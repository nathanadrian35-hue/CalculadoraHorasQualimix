"""
calculadora.py
---------------
Motor de Cálculo de Horas (Cap. 6/7/8/9/10).

Responsabilidade única (Cap. 18): todo cálculo do sistema acontece
exclusivamente aqui. Nenhuma outra tela ou módulo calcula horas —
apenas chamam as funções públicas abaixo e exibem o resultado já
pronto.

Todo o motor trabalha exclusivamente com minutos inteiros — nunca
float. Só a interface/relatório converte para "8h00"/"-0h35"
(`constantes.formatar_minutos`).

A regra de um único dia mora inteiramente em `recalcular_dia()` — uma
função pura e atômica, reaproveitada tanto pelo processamento completo
(`processar_todos`) quanto pelo reprocessamento incremental depois de
uma correção manual na Tela de Pendências (Cap. 10.7). Nenhuma cópia
dessa regra existe em nenhum outro lugar.
"""

from __future__ import annotations

from datetime import date, time

from config import Config
from constantes import JUSTIFICATIVAS_QUE_ELIMINAM_HORA_NEGATIVA, Situacao, TipoPendencia
from logger import get_logger
from modelos import (
    ContextoCalculo,
    DiaTrabalho,
    Funcionario,
    JornadaDia,
    Pendencia,
    ResultadoDia,
    ResultadoProcessamento,
    ResumoMensalFuncionario,
    Turno,
    diferenca_minutos,
)

log = get_logger()


# ---------------------------------------------------------------------------
# Ponto de entrada público: processamento completo
# ---------------------------------------------------------------------------

def processar_todos(
    funcionarios: list[Funcionario],
    turnos: list[Turno],
    config: Config,
    nome_empresa: str = "",
    competencia: tuple[int, int] | None = None,
) -> ResultadoProcessamento:
    """
    Processa todos os funcionários informados (Cap. 6.2): resolve o
    Turno de cada um, calcula todos os seus dias (`recalcular_dia`) e
    monta o resumo mensal. Funcionários sem Turno válido (`turno_id`
    vazio ou apontando para um Turno removido) não são calculados —
    geram uma única pendência TURNO_NAO_DEFINIDO e são pulados
    (Cap. 9.2).

    Retorna um `ResultadoProcessamento` consolidado, já preparado para
    alimentar Relatórios, Dashboard, Histórico e Exportação em sprints
    futuras.
    """
    turnos_por_id = {turno.id: turno for turno in turnos}
    resultado = ResultadoProcessamento(funcionarios_processados=list(funcionarios))
    dias_calculados = 0
    ultimo_dia_com_dados = _ultimo_dia_com_dados(funcionarios)

    for funcionario in funcionarios:
        turno = turnos_por_id.get(funcionario.turno_id) if funcionario.turno_id else None

        if turno is None:
            resultado.pendencias.append(Pendencia(
                tipo=TipoPendencia.TURNO_NAO_DEFINIDO,
                id_funcionario=funcionario.id,
                nome_funcionario=funcionario.nome_completo,
                descricao="Funcionário sem Turno válido — não é possível calcular.",
            ))
            log.warning(
                'Funcionário "%s" sem Turno válido — cálculo não realizado.',
                funcionario.nome_completo,
            )
            continue

        contexto = ContextoCalculo(
            config=config,
            turno=turno,
            funcionario_id=funcionario.id,
            nome_funcionario=funcionario.nome_completo,
            nome_empresa=nome_empresa,
            competencia=competencia,
            ultimo_dia_com_dados=ultimo_dia_com_dados,
        )
        for dia in funcionario.dias:
            recalcular_dia(dia, contexto)
            dias_calculados += 1
            if dia.pendencia is not None and not dia.pendencia.resolvida:
                resultado.pendencias.append(dia.pendencia)

        resultado.resumos_mensais.append(montar_resumo_mensal(funcionario))

    resultado.estatisticas = {
        "funcionarios_processados": len(funcionarios),
        "funcionarios_sem_turno": sum(
            1 for p in resultado.pendencias if p.tipo == TipoPendencia.TURNO_NAO_DEFINIDO
        ),
        "dias_calculados": dias_calculados,
        "pendencias": len(resultado.pendencias),
    }

    log.info(
        "Processamento concluído: %d funcionário(s), %d dia(s) calculado(s), %d pendência(s).",
        len(funcionarios), dias_calculados, len(resultado.pendencias),
    )

    return resultado


def _ultimo_dia_com_dados(funcionarios: list[Funcionario]) -> date | None:
    """
    Maior `dia.data` com pelo menos 1 batida entre todos os
    funcionários (Cap. novo, v2.0): a planilha semanal do RH sempre
    representa o mês inteiro, mas só os dias já ocorridos vêm
    preenchidos — isso marca até onde os dados "realmente chegam"
    nesta importação, para `recalcular_dia()` não gerar pendência
    SEM_BATIDAS em dias futuros ainda vazios. `None` se nenhum dia de
    nenhum funcionário tiver batida nenhuma (planilha totalmente vazia
    — caso degenerado, mantém o comportamento anterior à v2.0).
    """
    datas: list[date] = [
        dia.data
        for funcionario in funcionarios
        for dia in funcionario.dias
        if dia.batidas
    ]
    return max(datas) if datas else None


# ---------------------------------------------------------------------------
# Ponto de entrada público: cálculo de um único dia (Cap. 6/10)
# ---------------------------------------------------------------------------

def recalcular_dia(dia: DiaTrabalho, contexto: ContextoCalculo) -> None:
    """
    Calcula (ou recalcula) um único dia, mutando `dia.resultado` e
    `dia.pendencia`. Função pura e atômica — é a única implementação
    da regra de cálculo diário em todo o sistema (Cap. 6.2):

    1. Determina a jornada esperada do dia (Segunda-Sexta/Sábado/
       Domingo do Turno, Cap. 4.6/6.4/6.5).
    2. Verifica feriado (Cap. 6.6) — reservado, sem lógica nesta
       versão (`contexto.feriados` sempre vazio).
    3. Se o dia está sem batida e é posterior ao último dia com dados
       da importação (Cap. novo, v2.0 — planilha semanal representando
       o mês inteiro, dias futuros vazios): não gera pendência, fica
       neutro. Caso contrário, classifica pendência de quantidade de
       batidas (Cap. 7), considerando se a jornada do dia tem
       intervalo (Cap. 7.3), ou detecta horário fora de ordem
       cronológica.
    4. Se pendente e **ainda sem Justificativa** (Cap. 9.1): zera o
       resultado do dia e para — a correção da batida (Cap. 9.4) ou
       uma Justificativa (Cap. 9.6) são o único jeito de destravá-lo.
       Se já houver Justificativa, o cálculo segue mesmo com a
       quantidade incorreta de batidas — é a Justificativa quem decide
       o efeito sobre a Hora Negativa (Cap. 9.7), não a quantidade.
    5. Aplica as tolerâncias de Entrada, Saída para o Almoço, Retorno
       do Almoço e Saída Final (Cap. 8) — cada uma independente,
       configurável e opcional.
    6. Calcula Horas Trabalhadas (Cap. 10.1).
    7. Calcula Saldo (Cap. 10.4) e deriva Extras/Negativas (Cap.
       10.2/10.3), considerando a Justificativa já informada (Cap. 9.7).
    8. Define a Situação do dia.
    """
    jornada = contexto.turno.jornada_do_dia(dia.data)

    if _eh_feriado(contexto, dia.data):
        pass  # reservado (Cap. 6.6) — nenhuma lógica de feriado nesta versão

    quantidade = len(dia.batidas)
    horarios = [batida.horario for batida in dia.batidas]  # ordem original da planilha
    justificativa = dia.pendencia.justificativa if dia.pendencia else ""

    if (
        quantidade == 0
        and dia.pendencia is None
        and contexto.ultimo_dia_com_dados is not None
        and dia.data > contexto.ultimo_dia_com_dados
    ):
        # Dia futuro ainda não ocorrido (Cap. novo, v2.0): a planilha
        # semanal do RH sempre representa o mês inteiro, mas só os dias
        # já ocorridos vêm com batidas — os futuros vêm vazios. Ao
        # contrário de "sem batidas" de um dia já ocorrido (pendência
        # real), aqui ainda não há nada a cobrar: nenhuma pendência é
        # criada, o dia fica neutro até a próxima importação trazer os
        # dados dele.
        dia.resultado = ResultadoDia(
            jornada_prevista_min=(jornada.jornada_prevista_minutos() if jornada else None) or 0,
            situacao=Situacao.SEM_REGISTRO,
        )
        return

    tipo_pendencia = _classificar_pendencia_quantidade(quantidade, jornada)
    if tipo_pendencia is None and len(horarios) > 1 and not _em_ordem_crescente(horarios):
        tipo_pendencia = TipoPendencia.HORARIO_INCONSISTENTE

    if tipo_pendencia is not None and not justificativa:
        _registrar_pendencia(dia, contexto, tipo_pendencia)
        dia.resultado = ResultadoDia(situacao=Situacao.PENDENCIA)
        return

    if tipo_pendencia is not None:
        _registrar_pendencia(dia, contexto, tipo_pendencia)

    if horarios:
        for indice, previsto, chave_tolerancia in _pontos_tolerancia(jornada, len(horarios)):
            ativa, minutos = _obter_tolerancia(contexto.config, chave_tolerancia)
            horarios[indice] = _aplicar_tolerancia(horarios[indice], previsto, minutos, ativa)

    trabalhadas_min = _calcular_horas_trabalhadas_min(horarios)
    prevista_min = (jornada.jornada_prevista_minutos() if jornada else None) or 0
    saldo_min = trabalhadas_min - prevista_min
    extras_min, negativas_min = _derivar_extras_negativas_min(saldo_min, justificativa)

    if dia.pendencia is not None:
        # Corrigida (batidas passaram a bater com o esperado) ou
        # justificada (Cap. 9.6/9.7) — em ambos os casos, tratada.
        # Mantém o registro (Cap. 9.5), só marca como resolvida.
        dia.pendencia.resolvida = True

    situacao = _definir_situacao(extras_min, negativas_min)
    if not horarios and extras_min == 0 and negativas_min == 0:
        situacao = Situacao.SEM_REGISTRO

    dia.resultado = ResultadoDia(
        horas_trabalhadas_min=trabalhadas_min,
        jornada_prevista_min=prevista_min,
        saldo_min=saldo_min,
        horas_extras_min=extras_min,
        horas_negativas_min=negativas_min,
        situacao=situacao,
    )


# ---------------------------------------------------------------------------
# Ponto de entrada público: resumo mensal (Cap. 11.4, Aba 2)
# ---------------------------------------------------------------------------

def montar_resumo_mensal(funcionario: Funcionario) -> ResumoMensalFuncionario:
    """
    Agrega os dias já calculados de um funcionário (Cap. 11.4, Aba 2).
    Agregação pura — nenhum cálculo novo, só soma o que
    `recalcular_dia()` já produziu.
    """
    dias_trabalhados = sum(
        1 for dia in funcionario.dias if dia.resultado.horas_trabalhadas_min > 0
    )
    quantidade_pendencias = sum(
        1 for dia in funcionario.dias
        if dia.pendencia is not None and not dia.pendencia.resolvida
    )

    return ResumoMensalFuncionario(
        funcionario_id=funcionario.id,
        nome=funcionario.nome_completo,
        dias_trabalhados=dias_trabalhados,
        horas_trabalhadas_min=sum(d.resultado.horas_trabalhadas_min for d in funcionario.dias),
        horas_extras_min=sum(d.resultado.horas_extras_min for d in funcionario.dias),
        horas_negativas_min=sum(d.resultado.horas_negativas_min for d in funcionario.dias),
        saldo_final_min=sum(d.resultado.saldo_min for d in funcionario.dias),
        quantidade_pendencias=quantidade_pendencias,
    )


# ---------------------------------------------------------------------------
# Feriados (Cap. 6.6) — placeholder reservado
# ---------------------------------------------------------------------------

def _eh_feriado(contexto: ContextoCalculo, data: date) -> bool:
    """
    Verifica se `data` é um feriado (Cap. 6.6). Sempre False nesta
    versão — `contexto.feriados` nunca é populado ainda. Existe como
    ponto reservado na ordem do algoritmo (entre jornada e tolerâncias)
    para que uma futura sprint de Feriados não precise reordenar nada
    aqui, só preencher `contexto.feriados` e decidir o efeito.
    """
    return data in contexto.feriados


# ---------------------------------------------------------------------------
# Pendências de quantidade/ordem de batidas (Cap. 7)
# ---------------------------------------------------------------------------

def _classificar_pendencia_quantidade(
    quantidade: int, jornada: JornadaDia | None,
) -> TipoPendencia | None:
    """
    Classifica a quantidade de batidas de um dia (Cap. 7), ciente da
    jornada esperada (Cap. 7.3): sem jornada configurada (Sábado/
    Domingo fora do Turno), qualquer quantidade é aceita — não há
    "esperado" para comparar (Cap. 6.4/6.5). Com jornada configurada,
    o esperado é 4 batidas quando ela tem intervalo, ou 2 quando não
    tem; qualquer outra quantidade é pendência.
    """
    if jornada is None:
        return None

    esperado = 4 if jornada.inicio_intervalo is not None else 2
    if quantidade == esperado:
        return None
    if quantidade == 0:
        return TipoPendencia.SEM_BATIDAS
    if quantidade == 1:
        return TipoPendencia.UMA_BATIDA
    if quantidade == 2:
        return TipoPendencia.DUAS_BATIDAS
    if quantidade == 3:
        return TipoPendencia.TRES_BATIDAS
    return TipoPendencia.MAIS_DE_QUATRO


def _em_ordem_crescente(horarios: list[time]) -> bool:
    """Confere se os horários estão em ordem cronológica estritamente crescente."""
    return all(horarios[i] < horarios[i + 1] for i in range(len(horarios) - 1))


def _registrar_pendencia(dia: DiaTrabalho, contexto: ContextoCalculo, tipo: TipoPendencia) -> None:
    """
    Cria a pendência do dia (na primeira vez) ou apenas atualiza seu
    tipo/descrição quando ela já existir — nunca troca o objeto por um
    novo. Isso preserva justificativa, observações e o status de
    resolvida já existentes (Cap. 9.5: uma reclassificação nunca apaga
    o histórico de uma correção anterior) e, principalmente, mantém
    válida a referência que `processar_todos()` já colocou em
    `ResultadoProcessamento.pendencias` — trocar o objeto deixaria essa
    entrada "fantasma", presa em resolvida=False mesmo depois do dia
    ser corrigido.
    """
    descricao = f"{tipo.value} em {dia.data.strftime('%d/%m/%Y')}."

    if dia.pendencia is None:
        dia.pendencia = Pendencia(
            tipo=tipo,
            id_funcionario=contexto.funcionario_id,
            nome_funcionario=contexto.nome_funcionario,
            data=dia.data,
            descricao=descricao,
        )
        return

    dia.pendencia.tipo = tipo
    dia.pendencia.descricao = descricao


# ---------------------------------------------------------------------------
# Tolerâncias (Cap. 8)
# ---------------------------------------------------------------------------

def _obter_tolerancia(config: Config, chave: str) -> tuple[bool, int]:
    """Lê (ativa, minutos) de configuracoes["tolerancia_<chave>"] (Cap. 8)."""
    dados = config.configuracoes.get(f"tolerancia_{chave}", {})
    return bool(dados.get("ativa", False)), int(dados.get("minutos") or 0)


def _aplicar_tolerancia(
    horario_real: time, horario_previsto: time | None, minutos: int, ativa: bool,
) -> time:
    """
    Aplica a tolerância como faixa de aceitação (Cap. 8.1-8.4, um dos
    quatro pontos — Entrada, Saída Almoço, Retorno Almoço ou Saída
    Final, decididos por `_pontos_tolerancia()`): dentro da faixa, o
    horário é tratado exatamente como o previsto. Fora da faixa
    (incluindo quando não há tolerância ativa/configurada, ou quando
    não há horário previsto), o horário real é usado sem alteração — a
    contagem integral a partir do previsto acontece naturalmente na
    subtração de Horas Trabalhadas/Saldo, sem lógica extra aqui.
    """
    if not ativa or horario_previsto is None:
        return horario_real

    minutos_real = horario_real.hour * 60 + horario_real.minute
    minutos_previsto = horario_previsto.hour * 60 + horario_previsto.minute
    if abs(minutos_real - minutos_previsto) <= minutos:
        return horario_previsto
    return horario_real


def _pontos_tolerancia(
    jornada: JornadaDia | None, quantidade_batidas: int,
) -> list[tuple[int, time | None, str]]:
    """
    Decide quais pontos de tolerância (Cap. 8) se aplicam a este dia, e
    a qual horário previsto/chave de configuração (`tolerancia_<chave>`)
    cada um corresponde — Entrada, Saída para o Almoço, Retorno do
    Almoço e Saída Final, todas independentes, configuráveis e
    opcionais (Cap. 8.1-8.4). Estrutura escalável e sem repetição: cada
    ponto vira uma entrada (índice na lista de horários, horário
    previsto, chave de config), e `recalcular_dia()` aplica todos com
    o mesmo laço, chamando sempre a mesma `_aplicar_tolerancia()`.

    Entrada (índice 0) é tentada sempre que há pelo menos 1 batida —
    preserva exatamente o comportamento de antes desta refatoração.
    Saída para o Almoço/Retorno do Almoço (índices 1/2) só fazem
    sentido num dia de 4 batidas (jornada com intervalo) — mesma
    condição exata que o Retorno do Almoço já usava antes. Saída Final
    é a última batida esperada: índice 3 num dia de 4 batidas, ou
    índice 1 num dia de 2 batidas (jornada sem intervalo) — nunca as
    duas ao mesmo tempo. Dias com uma quantidade de batidas diferente
    de 2 ou 4 (só alcançam aqui quando já justificados, Cap. 9.7) não
    ganham nenhum ponto além da Entrada — mesmo comportamento de antes.
    """
    pontos: list[tuple[int, time | None, str]] = [
        (0, jornada.entrada if jornada else None, "entrada"),
    ]

    if quantidade_batidas == 4:
        pontos.append((1, jornada.inicio_intervalo if jornada else None, "saida_almoco"))
        pontos.append((2, jornada.fim_intervalo if jornada else None, "almoco"))
        pontos.append((3, jornada.saida if jornada else None, "saida"))
    elif quantidade_batidas == 2:
        pontos.append((1, jornada.saida if jornada else None, "saida"))

    return pontos


# ---------------------------------------------------------------------------
# Horas trabalhadas, saldo, extras/negativas, situação (Cap. 10)
# ---------------------------------------------------------------------------

def _calcular_horas_trabalhadas_min(horarios: list[time]) -> int:
    """
    Soma os minutos trabalhados entre pares consecutivos de horários
    (Cap. 10.1): (1º, 2º), (3º, 4º), etc. — funciona igualmente para os
    2 horários de um dia sem intervalo (Entrada/Saída) e para os 4 de
    um dia com intervalo (Entrada/Saída Almoço/Retorno/Saída), sem
    precisar de dois algoritmos diferentes. Um horário final sem par
    (jornada sem quantidade esperada, Cap. 6.4/6.5) é ignorado.
    """
    total_min = 0
    for indice in range(0, len(horarios) - 1, 2):
        diferenca = diferenca_minutos(horarios[indice], horarios[indice + 1])
        if diferenca is not None:
            total_min += diferenca
    return total_min


def _derivar_extras_negativas_min(saldo_min: int, justificativa: str) -> tuple[int, int]:
    """
    Deriva Horas Extras/Negativas a partir do Saldo (Cap. 10.2/10.3):
    saldo positivo é sempre extra; saldo negativo é negativa, a menos
    que a Justificativa do dia esteja na lista central que elimina a
    Hora Negativa (Cap. 9.7).
    """
    if saldo_min > 0:
        return saldo_min, 0
    if saldo_min == 0:
        return 0, 0
    if justificativa in JUSTIFICATIVAS_QUE_ELIMINAM_HORA_NEGATIVA:
        return 0, 0
    return 0, -saldo_min


def _definir_situacao(extras_min: int, negativas_min: int) -> Situacao:
    """Define a Situação final do dia a partir de Extras/Negativas já calculados."""
    if extras_min > 0:
        return Situacao.HORA_EXTRA
    if negativas_min > 0:
        return Situacao.HORA_NEGATIVA
    return Situacao.NORMAL
