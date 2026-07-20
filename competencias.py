"""
competencias.py
----------------
Persistência do gerenciamento de múltiplas competências.

Cada competência (mês/ano) importada e processada pelo Motor de
Cálculo (`calculadora.processar_todos()`) é gravada em um arquivo
JSON próprio dentro de `dados/competencias/`, para que fechar o
sistema no meio das pendências nunca perca nada. Nenhuma lógica de
cálculo mora aqui — este módulo só serializa/desserializa o que o
Motor já produziu, e decide (`avaliar_status`) qual `StatusCompetencia`
esses dados representam.

`listar()` é deliberadamente diferente de `relatorio.listar_competencias()`
— são conceitos distintos: aquele lê metadados de arquivos `.xlsx` já
exportados para o Histórico (Cap. 12.6/14); este lê o estado de
trabalho completo (funcionários, dias, pendências) de cada competência
ainda em gerenciamento.
"""

from __future__ import annotations

import getpass
import os
from dataclasses import dataclass
from datetime import date, datetime, time
from pathlib import Path
from typing import Any

import config
from calculadora import montar_resumo_mensal
from constantes import Situacao, StatusCompetencia, StatusSimplificado, TipoPendencia
from logger import get_logger
from modelos import (
    Batida,
    Competencia,
    DiaTrabalho,
    Funcionario,
    Pendencia,
    RegistroAuditoria,
    RegistroImportacao,
    ResultadoDia,
    ResultadoProcessamento,
    ResumoMensalFuncionario,
)

log = get_logger()


# ---------------------------------------------------------------------------
# Caminho e operações de arquivo
# ---------------------------------------------------------------------------

def _caminho(mes: int, ano: int) -> Path:
    """Caminho do arquivo JSON de uma competência: dados/competencias/{ano}-{mes:02d}.json."""
    return config.COMPETENCIAS_DIR / f"{ano}-{mes:02d}.json"


def existe(mes: int, ano: int) -> bool:
    """True se já existe uma competência persistida para este mês/ano."""
    return _caminho(mes, ano).exists()


def carregar_competencia(mes: int, ano: int) -> Competencia | None:
    """Carrega a competência do mês/ano informado, ou None se não existir."""
    caminho = _caminho(mes, ano)
    if not caminho.exists():
        return None
    dados = config.ler_json(caminho, padrao={})
    return _competencia_de_dict(dados)


def salvar_competencia(competencia: Competencia) -> None:
    """
    Persiste a competência (com backup automático da versão anterior,
    se houver — mesma rede de segurança do resto do app), e atualiza o
    índice leve (Cap. novo, v2.0 — Performance) usado por
    `listar_indice()`.
    """
    caminho = _caminho(competencia.mes, competencia.ano)
    dados = _competencia_para_dict(competencia)
    config.escrever_json(caminho, dados, com_backup=True)
    _atualizar_indice(competencia)
    log.info(
        "Competência %02d/%d salva (status=%s).",
        competencia.mes, competencia.ano, competencia.status.value,
    )


def listar() -> list[Competencia]:
    """
    Lista todas as competências persistidas, mais recente primeiro.
    Arquivos corrompidos/ilegíveis são ignorados (com log de erro),
    nunca derrubam a listagem inteira.
    """
    if not config.COMPETENCIAS_DIR.exists():
        return []

    competencias: list[Competencia] = []
    for arquivo in config.COMPETENCIAS_DIR.glob("*.json"):
        if arquivo.name.startswith("_"):
            continue  # arquivos internos (ex.: _indice.json), não são competências
        try:
            ano_texto, mes_texto = arquivo.stem.split("-")
            competencia = carregar_competencia(int(mes_texto), int(ano_texto))
        except (ValueError, OSError) as erro:
            log.error("Competência ilegível em %s (%s) — ignorada.", arquivo.name, erro)
            continue
        if competencia is not None:
            competencias.append(competencia)

    competencias.sort(key=lambda c: (c.ano, c.mes), reverse=True)
    return competencias


# ---------------------------------------------------------------------------
# Índice leve (Cap. novo, v2.0 — Performance): evita carregar o JSON
# completo (funcionários + dias + pendências) de cada competência só para
# mostrar contadores num seletor. Sempre reconstruível a partir dos
# arquivos completos — nunca a única fonte de verdade.
# ---------------------------------------------------------------------------

def _caminho_indice() -> Path:
    return config.COMPETENCIAS_DIR / "_indice.json"


def _resumo_indice(competencia: Competencia) -> dict[str, Any]:
    return {
        "mes": competencia.mes,
        "ano": competencia.ano,
        "status": competencia.status.value,
        "fechada": competencia.fechada,
        "quantidade_funcionarios": competencia.quantidade_funcionarios,
        "quantidade_registros": competencia.quantidade_registros,
        "quantidade_pendencias": competencia.quantidade_pendencias,
        "quantidade_pendencias_abertas": competencia.quantidade_pendencias_abertas,
        "quantidade_importacoes": competencia.quantidade_importacoes,
        "relatorio_gerado": competencia.relatorio_gerado,
        "data_importacao": competencia.data_importacao,
    }


def _atualizar_indice(competencia: Competencia) -> None:
    """Atualiza (ou cria) a entrada desta competência no índice leve."""
    chave = f"{competencia.ano}-{competencia.mes:02d}"
    indice = config.ler_json(_caminho_indice(), padrao={})
    indice[chave] = _resumo_indice(competencia)
    config.escrever_json(_caminho_indice(), indice, com_backup=False)


def listar_indice() -> list[dict[str, Any]]:
    """
    Versão leve de `listar()` (Cap. novo, v2.0 — Performance): lê só o
    índice (contadores já prontos), sem carregar funcionários/dias/
    pendências de cada competência — usada por telas que só precisam
    mostrar um resumo (ex.: seletor do Dashboard). Se o índice estiver
    ausente ou não bater com os arquivos reais, é reconstruído na hora
    a partir de `listar()` — nunca é a única fonte de verdade.
    """
    if not config.COMPETENCIAS_DIR.exists():
        return []

    chaves_reais = {
        arquivo.stem for arquivo in config.COMPETENCIAS_DIR.glob("*.json")
        if not arquivo.name.startswith("_")
    }
    indice = config.ler_json(_caminho_indice(), padrao={})

    if set(indice.keys()) != chaves_reais:
        log.info("Índice de competências desatualizado — reconstruindo.")
        competencias_completas = listar()
        indice = {}
        for competencia in competencias_completas:
            chave = f"{competencia.ano}-{competencia.mes:02d}"
            indice[chave] = _resumo_indice(competencia)
        config.escrever_json(_caminho_indice(), indice, com_backup=False)

    resumos = list(indice.values())
    resumos.sort(key=lambda r: (r["ano"], r["mes"]), reverse=True)
    return resumos


# ---------------------------------------------------------------------------
# Máquina de estados do status (Cap. novo — ver ESPECIFICACAO.md)
# ---------------------------------------------------------------------------

def avaliar_status(
    resultado: ResultadoProcessamento, status_atual: StatusCompetencia | None,
) -> StatusCompetencia:
    """
    Reavalia o `StatusCompetencia` de uma competência a partir do estado
    atual de suas pendências — função pura, chamada após qualquer
    correção/justificativa na Tela de Pendências. `ARQUIVADA` só muda
    por ação manual do usuário (Tela Competências); `RELATORIO_GERADO`
    nunca regride automaticamente para `PRONTA_PARA_RELATORIO` (a
    geração do relatório é sempre atribuída diretamente por
    `tela_relatorios.py` após a exportação).
    """
    if status_atual == StatusCompetencia.ARQUIVADA:
        return status_atual

    abertas = sum(1 for p in resultado.pendencias if not p.resolvida)
    resolvidas = len(resultado.pendencias) - abertas

    if abertas == 0:
        if status_atual == StatusCompetencia.RELATORIO_GERADO:
            return status_atual
        return StatusCompetencia.PRONTA_PARA_RELATORIO
    if resolvidas > 0:
        return StatusCompetencia.EM_ANDAMENTO
    return StatusCompetencia.PENDENCIAS_ABERTAS


def status_simplificado(competencia: Competencia) -> StatusSimplificado:
    """
    Selo de 3 estados (Cap. novo, v2.0) para a Tela de Competências e o
    Dashboard — não substitui `StatusCompetencia` (que continua
    controlando o fluxo detalhado já existente), só resume: fechada
    manualmente prevalece sobre tudo; senão, qualquer pendência em
    aberto já é "aguardando"; senão, "em andamento".
    """
    if competencia.fechada:
        return StatusSimplificado.FECHADA
    if any(not p.resolvida for p in competencia.resultado.pendencias):
        return StatusSimplificado.AGUARDANDO_PENDENCIAS
    return StatusSimplificado.EM_ANDAMENTO


# ---------------------------------------------------------------------------
# Fechamento (Cap. novo, v2.0) — competência fechada não é alterada sem
# confirmação explícita de reabertura (Etapa 7)
# ---------------------------------------------------------------------------

def fechar_competencia(competencia: Competencia, usuario: str | None = None) -> None:
    """Fecha a competência (Cap. novo, v2.0) e persiste. Não valida nada — a
    confirmação é responsabilidade de quem chama (Tela de Competências)."""
    competencia.fechada = True
    competencia.data_fechamento = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
    registrar_auditoria(
        competencia, o_que="Competência fechada",
        valor_anterior="Aberta", valor_novo="Fechada", usuario=usuario,
    )
    salvar_competencia(competencia)


def reabrir_competencia(competencia: Competencia, usuario: str | None = None) -> None:
    """Reabre uma competência fechada (Cap. novo, v2.0) e persiste."""
    competencia.fechada = False
    competencia.data_fechamento = ""
    registrar_auditoria(
        competencia, o_que="Competência reaberta",
        valor_anterior="Fechada", valor_novo="Aberta", usuario=usuario,
    )
    salvar_competencia(competencia)


# ---------------------------------------------------------------------------
# Auditoria (Cap. novo, v2.0) — quem, quando, o quê, valor anterior/novo
# ---------------------------------------------------------------------------

def _usuario_atual() -> str:
    """Usuário do Windows logado — sem exigir login próprio no QualiPonto."""
    try:
        return os.getlogin()
    except OSError:
        return getpass.getuser()


def registrar_auditoria(
    competencia: Competencia, o_que: str, valor_anterior: str, valor_novo: str,
    usuario: str | None = None,
) -> None:
    """
    Acrescenta um evento ao log de auditoria da Competência (Cap. novo,
    v2.0) — a série só cresce, nunca reescreve entradas antigas. Não
    salva sozinho: quem chama decide quando persistir (várias chamadas
    podem compor uma única gravação).
    """
    competencia.auditoria.append(RegistroAuditoria(
        quando=datetime.now().strftime("%d/%m/%Y %H:%M:%S"),
        usuario=usuario or _usuario_atual(),
        o_que=o_que,
        valor_anterior=valor_anterior,
        valor_novo=valor_novo,
    ))


# ---------------------------------------------------------------------------
# Sincronização incremental (Cap. novo, v2.0) — importação semanal
# ---------------------------------------------------------------------------

@dataclass
class ResultadoSincronizacao:
    """Resumo de uma sincronização incremental — para o Histórico de Importações."""

    funcionarios_novos: int = 0
    registros_adicionados: int = 0
    registros_alterados: int = 0
    registros_mantidos: int = 0


def _dia_protegido(dia: DiaTrabalho) -> bool:
    """
    Um dia nunca é sobrescrito por uma nova importação quando o usuário
    já mexeu nele (Cap. novo, v2.0 — "jamais apagar pendências
    corrigidas sem confirmação"): pelo menos uma batida digitada
    manualmente (Cap. 9.4), ou a pendência já resolvida (corrigida ou
    justificada, Cap. 9.5/9.6).
    """
    if any(batida.manual for batida in dia.batidas):
        return True
    if dia.pendencia is not None and dia.pendencia.resolvida:
        return True
    return False


def sincronizar_competencia(
    competencia_existente: Competencia, resultado_novo: ResultadoProcessamento,
) -> ResultadoSincronizacao:
    """
    Mescla `resultado_novo` (saída normal e já calculada de
    `calculadora.processar_todos()`, de uma nova importação semanal)
    DENTRO da competência já persistida, dia a dia — nunca substitui a
    competência inteira (Cap. novo, v2.0). Nenhum recálculo acontece
    aqui: `resultado_novo` já foi computado pelo Motor com as regras de
    sempre; esta função só decide, por dia, se o valor antigo ou o novo
    prevalece.

    Regras:
      - Funcionário novo (id inédito nesta competência): adicionado
        por inteiro.
      - Funcionário sem Turno válido nesta importação (Cap. 9.2): seus
        dias já calculados em importações anteriores NUNCA são
        tocados — só a pendência TURNO_NAO_DEFINIDO é atualizada.
      - Dia que não existia antes: adicionado.
      - Dia já protegido (`_dia_protegido`): nunca sobrescrito, mesmo
        que a planilha traga um valor diferente.
      - Dia com as MESMAS batidas (mesmos horários, mesma ordem): não é
        tocado — mantém o objeto (e a pendência) exatamente como
        estava.
      - Dia com batidas diferentes e ainda não protegido (ex.: era um
        dia futuro sem dados, a semana chegou): substituído pela nova
        versão já calculada.
      - Nenhum funcionário/dia é removido, mesmo ausente do novo
        arquivo.

    Ao final, `pendencias`/`resumos_mensais`/`estatisticas` da
    competência são recompostos sobre o estado já mesclado, reaproveitando
    a mesma agregação pura de `calculadora.montar_resumo_mensal()` —
    nenhuma fórmula nova.
    """
    resumo = ResultadoSincronizacao()
    resultado_existente = competencia_existente.resultado
    funcionarios_existentes = {f.id: f for f in resultado_existente.funcionarios_processados}

    ids_sem_turno_agora = {
        p.id_funcionario for p in resultado_novo.pendencias
        if p.tipo == TipoPendencia.TURNO_NAO_DEFINIDO
    }

    for funcionario_novo in resultado_novo.funcionarios_processados:
        if funcionario_novo.id in ids_sem_turno_agora:
            # Sem Turno válido nesta importação: não há .dias recalculados
            # de verdade a mesclar — só a pendência (tratada abaixo, na
            # composição final) reflete isso. Dias já existentes de uma
            # importação anterior (quando o Turno estava certo) ficam
            # intocados.
            continue

        funcionario_existente = funcionarios_existentes.get(funcionario_novo.id)

        if funcionario_existente is None:
            resultado_existente.funcionarios_processados.append(funcionario_novo)
            funcionarios_existentes[funcionario_novo.id] = funcionario_novo
            resumo.funcionarios_novos += 1
            resumo.registros_adicionados += sum(1 for d in funcionario_novo.dias if d.batidas)
            continue

        dias_existentes = {dia.data: dia for dia in funcionario_existente.dias}
        for dia_novo in funcionario_novo.dias:
            dia_existente = dias_existentes.get(dia_novo.data)

            if dia_existente is None:
                funcionario_existente.dias.append(dia_novo)
                if dia_novo.batidas:
                    resumo.registros_adicionados += 1
                continue

            if _dia_protegido(dia_existente):
                resumo.registros_mantidos += 1
                continue

            horarios_existente = [b.horario for b in dia_existente.batidas]
            horarios_novo = [b.horario for b in dia_novo.batidas]
            # Mesmo com as mesmas batidas (ou ambas vazias), o dia pode ter
            # deixado de ser "futuro" nesta nova importação — o último dia
            # com dados avançou, e um dia antes vazio agora é uma pendência
            # SEM_BATIDAS real (Cap. novo, v2.0). Sem checar isso, duas
            # listas de batidas vazias pareceriam "iguais" e a pendência
            # nova nunca seria adotada.
            pendencia_surgiu = dia_existente.pendencia is None and dia_novo.pendencia is not None
            if horarios_existente == horarios_novo and not pendencia_surgiu:
                resumo.registros_mantidos += 1
                continue

            indice = funcionario_existente.dias.index(dia_existente)
            funcionario_existente.dias[indice] = dia_novo
            if horarios_novo and not horarios_existente:
                resumo.registros_adicionados += 1
            elif horarios_existente != horarios_novo:
                resumo.registros_alterados += 1
            else:
                resumo.registros_mantidos += 1  # só a pendência mudou, não é bem um "registro" novo

    # Recompõe pendências/resumos/estatísticas sobre o estado final já
    # mesclado (mesma lógica de agregação de calculadora.processar_todos,
    # nunca duplicada — só reaproveitada aqui por cima dos dias já
    # calculados).
    ids_tocados_agora = {f.id for f in resultado_novo.funcionarios_processados}
    pendencias_finais: list[Pendencia] = [
        p for p in resultado_existente.pendencias
        if p.data is None and p.id_funcionario not in ids_tocados_agora
    ]
    pendencias_finais.extend(p for p in resultado_novo.pendencias if p.data is None)

    # Inclui TODAS as pendências ligadas a um dia — resolvidas ou não
    # (mesmo comportamento de `calculadora.processar_todos()`, que nunca
    # descarta uma pendência só porque já foi corrigida/justificada).
    # Excluir as resolvidas aqui apagaria, a cada nova importação, o
    # histórico de pendências já tratadas (contadores da Tela
    # Competências, estatísticas do Excel) — quem precisa só das
    # pendências em aberto já filtra por `.resolvida` separadamente
    # (`existem_pendencias_abertas`, `_pendencias_filtradas`).
    funcionarios_finais = resultado_existente.funcionarios_processados
    for funcionario in funcionarios_finais:
        for dia in funcionario.dias:
            if dia.pendencia is not None and dia.pendencia not in pendencias_finais:
                pendencias_finais.append(dia.pendencia)

    resultado_existente.pendencias = pendencias_finais
    resultado_existente.resumos_mensais = [
        montar_resumo_mensal(funcionario) for funcionario in funcionarios_finais
    ]
    resultado_existente.estatisticas = {
        "funcionarios_processados": len(funcionarios_finais),
        "funcionarios_sem_turno": sum(
            1 for p in pendencias_finais if p.tipo == TipoPendencia.TURNO_NAO_DEFINIDO
        ),
        "dias_calculados": sum(len(f.dias) for f in funcionarios_finais),
        "pendencias": len(pendencias_finais),
    }

    return resumo


def registrar_criacao(competencia: Competencia, usuario: str | None = None) -> None:
    """
    Primeira importação de uma Competência nova (Cap. novo, v2.0):
    registra a primeira entrada do histórico de importações e o
    primeiro evento de auditoria. Não persiste — quem chama decide
    quando salvar (normalmente logo em seguida, via `salvar_competencia`).
    """
    usuario_efetivo = usuario or _usuario_atual()
    competencia.historico_importacoes.append(RegistroImportacao(
        data_hora=competencia.data_importacao,
        usuario=usuario_efetivo,
        arquivo_original=competencia.arquivo_original,
        quantidade_registros=competencia.quantidade_registros,
        registros_adicionados=competencia.quantidade_registros,
        registros_alterados=0,
    ))
    registrar_auditoria(
        competencia, o_que=f"Competência criada ({competencia.arquivo_original})",
        valor_anterior="—",
        valor_novo=f"{competencia.quantidade_funcionarios} funcionário(s), "
                   f"{competencia.quantidade_registros} registro(s)",
        usuario=usuario_efetivo,
    )


def registrar_importacao(
    competencia_existente: Competencia, resultado_novo: ResultadoProcessamento,
    arquivo_original: str, usuario: str | None = None,
) -> ResultadoSincronizacao:
    """
    Ponto de entrada único para atualizar incrementalmente uma
    Competência já existente com uma nova importação semanal (Cap.
    novo, v2.0): mescla (`sincronizar_competencia`), reavalia o status,
    registra a entrada no histórico de importações e persiste — tudo
    em uma chamada, para `tela_principal.py` nunca duplicar essa
    sequência. O backup automático da versão anterior acontece dentro
    de `salvar_competencia()` (Cap. 13.1, já existente), então toda
    sincronização já é protegida por um backup, sem código adicional.
    """
    usuario_efetivo = usuario or _usuario_atual()
    resumo = sincronizar_competencia(competencia_existente, resultado_novo)

    agora = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
    competencia_existente.data_importacao = agora
    competencia_existente.quantidade_importacoes += 1
    competencia_existente.arquivo_original = arquivo_original
    competencia_existente.status = avaliar_status(
        competencia_existente.resultado, competencia_existente.status)

    competencia_existente.historico_importacoes.append(RegistroImportacao(
        data_hora=agora,
        usuario=usuario_efetivo,
        arquivo_original=arquivo_original,
        quantidade_registros=competencia_existente.quantidade_registros,
        registros_adicionados=resumo.registros_adicionados,
        registros_alterados=resumo.registros_alterados,
    ))
    registrar_auditoria(
        competencia_existente, o_que=f"Importação sincronizada ({arquivo_original})",
        valor_anterior="—",
        valor_novo=f"{resumo.registros_adicionados} adicionado(s), "
                   f"{resumo.registros_alterados} alterado(s), "
                   f"{resumo.registros_mantidos} mantido(s), "
                   f"{resumo.funcionarios_novos} funcionário(s) novo(s)",
        usuario=usuario_efetivo,
    )

    salvar_competencia(competencia_existente)
    log.info(
        "Competência %02d/%d sincronizada: %d adicionado(s), %d alterado(s), "
        "%d mantido(s), %d funcionário(s) novo(s).",
        competencia_existente.mes, competencia_existente.ano,
        resumo.registros_adicionados, resumo.registros_alterados,
        resumo.registros_mantidos, resumo.funcionarios_novos,
    )
    return resumo


# ---------------------------------------------------------------------------
# Conversão de horários/datas (uso local — mesmo padrão de config.py)
# ---------------------------------------------------------------------------

def _time_para_texto(horario: time) -> str:
    return horario.strftime("%H:%M")


def _texto_para_time(texto: str) -> time:
    return datetime.strptime(texto, "%H:%M").time()


def _data_para_texto(data: date | None) -> str | None:
    return data.isoformat() if data is not None else None


def _texto_para_data(texto: str | None) -> date | None:
    return date.fromisoformat(texto) if texto else None


# ---------------------------------------------------------------------------
# Serialização de Batida / ResultadoDia / DiaTrabalho
# ---------------------------------------------------------------------------

def _batida_para_dict(batida: Batida) -> dict[str, Any]:
    return {"horario": _time_para_texto(batida.horario), "manual": batida.manual}


def _batida_de_dict(dados: dict[str, Any]) -> Batida:
    return Batida(
        horario=_texto_para_time(dados["horario"]),
        manual=bool(dados.get("manual", False)),
    )


def _resultado_dia_para_dict(resultado: ResultadoDia) -> dict[str, Any]:
    return {
        "horas_trabalhadas_min": resultado.horas_trabalhadas_min,
        "jornada_prevista_min": resultado.jornada_prevista_min,
        "saldo_min": resultado.saldo_min,
        "horas_extras_min": resultado.horas_extras_min,
        "horas_negativas_min": resultado.horas_negativas_min,
        "situacao": resultado.situacao.value,
    }


def _resultado_dia_de_dict(dados: dict[str, Any]) -> ResultadoDia:
    try:
        situacao = Situacao(dados.get("situacao", Situacao.NORMAL.value))
    except ValueError:
        situacao = Situacao.NORMAL
    return ResultadoDia(
        horas_trabalhadas_min=int(dados.get("horas_trabalhadas_min", 0)),
        jornada_prevista_min=int(dados.get("jornada_prevista_min", 0)),
        saldo_min=int(dados.get("saldo_min", 0)),
        horas_extras_min=int(dados.get("horas_extras_min", 0)),
        horas_negativas_min=int(dados.get("horas_negativas_min", 0)),
        situacao=situacao,
    )


def _dia_trabalho_para_dict(dia: DiaTrabalho) -> dict[str, Any]:
    """
    Serializa um DiaTrabalho SEM campo de pendência — a pendência (se
    houver) já está na lista `pendencias` de nível superior e é
    religada a este dia na desserialização, para preservar a
    invariante de que `dia.pendencia` e a entrada correspondente em
    `ResultadoProcessamento.pendencias` são o MESMO objeto Python
    (`calculadora._registrar_pendencia` depende disso).
    """
    return {
        "data": _data_para_texto(dia.data),
        "dia_semana": dia.dia_semana,
        "batidas": [_batida_para_dict(b) for b in dia.batidas],
        "resultado": _resultado_dia_para_dict(dia.resultado),
        "observacoes": dia.observacoes,
    }


def _dia_trabalho_de_dict(dados: dict[str, Any]) -> DiaTrabalho:
    return DiaTrabalho(
        data=_texto_para_data(dados.get("data")) or date.today(),
        dia_semana=dados.get("dia_semana", ""),
        batidas=[_batida_de_dict(b) for b in dados.get("batidas", [])],
        resultado=_resultado_dia_de_dict(dados.get("resultado", {})),
        observacoes=dados.get("observacoes", ""),
    )


# ---------------------------------------------------------------------------
# Serialização de Pendencia
# ---------------------------------------------------------------------------

def _pendencia_para_dict(pendencia: Pendencia) -> dict[str, Any]:
    return {
        "tipo": pendencia.tipo.value,
        "id_funcionario": pendencia.id_funcionario,
        "nome_funcionario": pendencia.nome_funcionario,
        "data": _data_para_texto(pendencia.data),
        "descricao": pendencia.descricao,
        "justificativa": pendencia.justificativa,
        "observacoes": pendencia.observacoes,
        "resolvida": pendencia.resolvida,
    }


def _pendencia_de_dict(dados: dict[str, Any]) -> Pendencia:
    try:
        tipo = TipoPendencia(dados["tipo"])
    except (KeyError, ValueError):
        tipo = TipoPendencia.HORARIO_INCONSISTENTE
    return Pendencia(
        tipo=tipo,
        id_funcionario=dados.get("id_funcionario", ""),
        nome_funcionario=dados.get("nome_funcionario", ""),
        data=_texto_para_data(dados.get("data")),
        descricao=dados.get("descricao", ""),
        justificativa=dados.get("justificativa", ""),
        observacoes=dados.get("observacoes", ""),
        resolvida=bool(dados.get("resolvida", False)),
    )


# ---------------------------------------------------------------------------
# Serialização de Funcionario processado (reaproveita config.funcionario_*_dict
# como base, só acrescentando .dias por cima)
# ---------------------------------------------------------------------------

def _funcionario_processado_para_dict(funcionario: Funcionario) -> dict[str, Any]:
    dados = config.funcionario_para_dict(funcionario)
    dados["dias"] = [_dia_trabalho_para_dict(dia) for dia in funcionario.dias]
    return dados


def _funcionario_processado_de_dict(
    dados: dict[str, Any], pendencias_por_chave: dict[tuple[str, date | None], Pendencia],
) -> Funcionario:
    funcionario = config.funcionario_de_dict(dados)
    dias = [_dia_trabalho_de_dict(d) for d in dados.get("dias", [])]
    for dia in dias:
        dia.pendencia = pendencias_por_chave.get((funcionario.id, dia.data))
    funcionario.dias = dias
    return funcionario


# ---------------------------------------------------------------------------
# Serialização de ResumoMensalFuncionario
# ---------------------------------------------------------------------------

def _resumo_mensal_para_dict(resumo: ResumoMensalFuncionario) -> dict[str, Any]:
    return {
        "funcionario_id": resumo.funcionario_id,
        "nome": resumo.nome,
        "dias_trabalhados": resumo.dias_trabalhados,
        "horas_trabalhadas_min": resumo.horas_trabalhadas_min,
        "horas_extras_min": resumo.horas_extras_min,
        "horas_negativas_min": resumo.horas_negativas_min,
        "saldo_final_min": resumo.saldo_final_min,
        "quantidade_pendencias": resumo.quantidade_pendencias,
    }


def _resumo_mensal_de_dict(dados: dict[str, Any]) -> ResumoMensalFuncionario:
    return ResumoMensalFuncionario(
        funcionario_id=dados.get("funcionario_id", ""),
        nome=dados.get("nome", ""),
        dias_trabalhados=int(dados.get("dias_trabalhados", 0)),
        horas_trabalhadas_min=int(dados.get("horas_trabalhadas_min", 0)),
        horas_extras_min=int(dados.get("horas_extras_min", 0)),
        horas_negativas_min=int(dados.get("horas_negativas_min", 0)),
        saldo_final_min=int(dados.get("saldo_final_min", 0)),
        quantidade_pendencias=int(dados.get("quantidade_pendencias", 0)),
    )


# ---------------------------------------------------------------------------
# Serialização de RegistroImportacao / RegistroAuditoria (Cap. novo, v2.0)
# ---------------------------------------------------------------------------

def _registro_importacao_para_dict(registro: RegistroImportacao) -> dict[str, Any]:
    return {
        "data_hora": registro.data_hora,
        "usuario": registro.usuario,
        "arquivo_original": registro.arquivo_original,
        "quantidade_registros": registro.quantidade_registros,
        "registros_adicionados": registro.registros_adicionados,
        "registros_alterados": registro.registros_alterados,
    }


def _registro_importacao_de_dict(dados: dict[str, Any]) -> RegistroImportacao:
    return RegistroImportacao(
        data_hora=dados.get("data_hora", ""),
        usuario=dados.get("usuario", ""),
        arquivo_original=dados.get("arquivo_original", ""),
        quantidade_registros=int(dados.get("quantidade_registros", 0)),
        registros_adicionados=int(dados.get("registros_adicionados", 0)),
        registros_alterados=int(dados.get("registros_alterados", 0)),
    )


def _registro_auditoria_para_dict(registro: RegistroAuditoria) -> dict[str, Any]:
    return {
        "quando": registro.quando,
        "usuario": registro.usuario,
        "o_que": registro.o_que,
        "valor_anterior": registro.valor_anterior,
        "valor_novo": registro.valor_novo,
    }


def _registro_auditoria_de_dict(dados: dict[str, Any]) -> RegistroAuditoria:
    return RegistroAuditoria(
        quando=dados.get("quando", ""),
        usuario=dados.get("usuario", ""),
        o_que=dados.get("o_que", ""),
        valor_anterior=dados.get("valor_anterior", ""),
        valor_novo=dados.get("valor_novo", ""),
    )


# ---------------------------------------------------------------------------
# Serialização de Competencia (nível superior)
# ---------------------------------------------------------------------------

def _competencia_para_dict(competencia: Competencia) -> dict[str, Any]:
    resultado = competencia.resultado
    return {
        "mes": competencia.mes,
        "ano": competencia.ano,
        "status": competencia.status.value,
        "data_importacao": competencia.data_importacao,
        "arquivo_original": competencia.arquivo_original,
        "relatorio_gerado": competencia.relatorio_gerado,
        "data_criacao": competencia.data_criacao,
        "quantidade_importacoes": competencia.quantidade_importacoes,
        "fechada": competencia.fechada,
        "data_fechamento": competencia.data_fechamento,
        "historico_importacoes": [
            _registro_importacao_para_dict(r) for r in competencia.historico_importacoes
        ],
        "auditoria": [_registro_auditoria_para_dict(r) for r in competencia.auditoria],
        "pendencias": [_pendencia_para_dict(p) for p in resultado.pendencias],
        "funcionarios": [
            _funcionario_processado_para_dict(f) for f in resultado.funcionarios_processados
        ],
        "resumos_mensais": [_resumo_mensal_para_dict(r) for r in resultado.resumos_mensais],
        "estatisticas": dict(resultado.estatisticas),
    }


def _competencia_de_dict(dados: dict[str, Any]) -> Competencia | None:
    try:
        mes = int(dados["mes"])
        ano = int(dados["ano"])
    except (KeyError, TypeError, ValueError):
        log.error("Competência sem mês/ano válidos — ignorada.")
        return None

    try:
        status = StatusCompetencia(dados.get("status", ""))
    except ValueError:
        status = StatusCompetencia.EM_ANDAMENTO

    # Pendências são desserializadas UMA vez aqui (fonte única) e religadas
    # aos dias correspondentes por (id_funcionario, data) — nunca recriadas
    # por funcionário, para preservar a invariante de referência que o
    # Motor de Cálculo depende (ver _dia_trabalho_para_dict).
    pendencias = [_pendencia_de_dict(p) for p in dados.get("pendencias", [])]
    pendencias_por_chave = {(p.id_funcionario, p.data): p for p in pendencias}

    funcionarios = [
        _funcionario_processado_de_dict(f, pendencias_por_chave)
        for f in dados.get("funcionarios", [])
    ]

    resumos_mensais = [_resumo_mensal_de_dict(r) for r in dados.get("resumos_mensais", [])]

    resultado = ResultadoProcessamento(
        funcionarios_processados=funcionarios,
        pendencias=pendencias,
        resumos_mensais=resumos_mensais,
        estatisticas=dict(dados.get("estatisticas", {})),
    )

    return Competencia(
        mes=mes,
        ano=ano,
        status=status,
        data_importacao=dados.get("data_importacao", ""),
        arquivo_original=dados.get("arquivo_original", ""),
        resultado=resultado,
        relatorio_gerado=bool(dados.get("relatorio_gerado", False)),
        data_criacao=dados.get("data_criacao", ""),
        quantidade_importacoes=int(dados.get("quantidade_importacoes", 1)),
        fechada=bool(dados.get("fechada", False)),
        data_fechamento=dados.get("data_fechamento", ""),
        historico_importacoes=[
            _registro_importacao_de_dict(r) for r in dados.get("historico_importacoes", [])
        ],
        auditoria=[_registro_auditoria_de_dict(r) for r in dados.get("auditoria", [])],
    )
