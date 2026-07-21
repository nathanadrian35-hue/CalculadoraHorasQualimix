"""
absenteismo.py
---------------
Motor de Absenteísmo (v2.1 Sprint 2, Cap. 41-80).

Responsabilidade única: calcular, configurar e simular índices de
absenteísmo — sempre em cima do que `calculadora.py` (Cap. 6) e as
Justificativas (Cap. 9.6) já produziram em cada `Competencia`
persistida. Nenhuma hora é recalculada aqui, nenhum dado de ponto é
lançado à parte (Cap. 44: "não deverá existir duplicação de dados").

Nenhuma tela deve calcular índice diretamente — todas (Dashboard,
relatórios, exportações) chamam as funções deste módulo, garantindo
que produzam exatamente o mesmo resultado (Cap. 12/61).

Configuração (`ConfiguracaoAbsenteismo`) é persistida separadamente de
`configuracoes.json`, versionada: cada `salvar_configuracao()`
incrementa a versão e registra um evento de auditoria — um
`IndicadorAbsenteismo` já calculado guarda a versão vigente no momento
do cálculo, então mudar a configuração depois nunca reescreve
silenciosamente um índice histórico (Cap. 57/67).
"""

from __future__ import annotations

from dataclasses import replace
from datetime import datetime

from config import escrever_json, ler_json
from constantes import (
    LIMIAR_ABSENTEISMO_ATENCAO_PADRAO,
    LIMIAR_ABSENTEISMO_CRITICO_PADRAO,
    Justificativa,
    MetodoCalculoAbsenteismo,
    formatar_minutos,
    nome_mes,
)
from logger import get_logger
from modelos import (
    Competencia,
    ConfiguracaoAbsenteismo,
    ConfiguracaoOcorrencia,
    Funcionario,
    IndicadorAbsenteismo,
    OcorrenciaAbsenteismo,
    RegistroAuditoria,
    usuario_atual,
)

log = get_logger()

# Ocorrências que já nascem marcadas para contar no índice (Cap. 46) — só o
# ponto de partida sugerido pela tabela-exemplo da especificação; 100%
# editável depois pelo administrador na Tela de Configurações.
_CONSIDERADAS_POR_PADRAO: frozenset[Justificativa] = frozenset({
    Justificativa.FALTA,
    Justificativa.FALTA_JUSTIFICADA,
    Justificativa.ATESTADO_MEDICO,
})


# ---------------------------------------------------------------------------
# Persistência da configuração (Cap. 46/67)
# ---------------------------------------------------------------------------

def _caminho_config():
    from config import DADOS_DIR
    return DADOS_DIR / "absenteismo_config.json"


def _padrao_configuracao_dict() -> dict:
    return {
        "metodo": MetodoCalculoAbsenteismo.PERCENTUAL.value,
        "ocorrencias": [
            {
                "justificativa": justificativa.value,
                "considerar_no_indice": justificativa in _CONSIDERADAS_POR_PADRAO,
                "cor": "#e74c3c" if justificativa in _CONSIDERADAS_POR_PADRAO else "#3498db",
                "icone": "📌",
                "ativa": True,
            }
            for justificativa in Justificativa
        ],
        "limiar_atencao": LIMIAR_ABSENTEISMO_ATENCAO_PADRAO,
        "limiar_critico": LIMIAR_ABSENTEISMO_CRITICO_PADRAO,
        "versao": 1,
        "atualizado_em": "",
        "auditoria": [],
    }


def _ocorrencia_de_dict(dados: dict) -> ConfiguracaoOcorrencia | None:
    try:
        justificativa = Justificativa(dados.get("justificativa", ""))
    except ValueError:
        return None
    return ConfiguracaoOcorrencia(
        justificativa=justificativa,
        considerar_no_indice=bool(dados.get("considerar_no_indice", False)),
        cor=dados.get("cor", "#3498db"),
        icone=dados.get("icone", "📌"),
        ativa=bool(dados.get("ativa", True)),
    )


def _ocorrencia_para_dict(ocorrencia: ConfiguracaoOcorrencia) -> dict:
    return {
        "justificativa": ocorrencia.justificativa.value,
        "considerar_no_indice": ocorrencia.considerar_no_indice,
        "cor": ocorrencia.cor,
        "icone": ocorrencia.icone,
        "ativa": ocorrencia.ativa,
    }


def _auditoria_de_dict(dados: dict) -> RegistroAuditoria:
    return RegistroAuditoria(
        quando=dados.get("quando", ""), usuario=dados.get("usuario", ""),
        o_que=dados.get("o_que", ""), valor_anterior=dados.get("valor_anterior", ""),
        valor_novo=dados.get("valor_novo", ""),
    )


def _auditoria_para_dict(evento: RegistroAuditoria) -> dict:
    return {
        "quando": evento.quando, "usuario": evento.usuario, "o_que": evento.o_que,
        "valor_anterior": evento.valor_anterior, "valor_novo": evento.valor_novo,
    }


def carregar_configuracao() -> ConfiguracaoAbsenteismo:
    """
    Carrega a configuração vigente (Cap. 46), criando-a com os
    valores padrão sugeridos na primeira execução. Tolerante a
    Justificativas desconhecidas no JSON (versão antiga) e a
    Justificativas novas no Enum sem entrada ainda no JSON (mescla
    automaticamente, Cap. 11-compatibilidade).
    """
    dados = ler_json(_caminho_config(), _padrao_configuracao_dict())

    ocorrencias: list[ConfiguracaoOcorrencia] = []
    justificativas_no_arquivo: set[Justificativa] = set()
    for item in dados.get("ocorrencias", []):
        ocorrencia = _ocorrencia_de_dict(item)
        if ocorrencia is not None:
            ocorrencias.append(ocorrencia)
            justificativas_no_arquivo.add(ocorrencia.justificativa)

    # Justificativa nova no Enum (ex.: adicionada em versão futura) que
    # ainda não tem entrada no JSON persistido — entra com o padrão
    # "não considerar", nunca inflando um índice já em uso sem aviso.
    for justificativa in Justificativa:
        if justificativa not in justificativas_no_arquivo:
            ocorrencias.append(ConfiguracaoOcorrencia(justificativa=justificativa))

    valor_metodo = dados.get("metodo", MetodoCalculoAbsenteismo.PERCENTUAL.value)
    try:
        metodo = MetodoCalculoAbsenteismo(valor_metodo)
    except ValueError:
        metodo = MetodoCalculoAbsenteismo.PERCENTUAL

    return ConfiguracaoAbsenteismo(
        metodo=metodo,
        ocorrencias=ocorrencias,
        limiar_atencao=float(dados.get("limiar_atencao", LIMIAR_ABSENTEISMO_ATENCAO_PADRAO)),
        limiar_critico=float(dados.get("limiar_critico", LIMIAR_ABSENTEISMO_CRITICO_PADRAO)),
        versao=int(dados.get("versao", 1)),
        atualizado_em=dados.get("atualizado_em", ""),
        auditoria=[_auditoria_de_dict(e) for e in dados.get("auditoria", [])],
    )


def salvar_configuracao(
    configuracao: ConfiguracaoAbsenteismo, o_que: str,
    valor_anterior: str, valor_novo: str, usuario: str | None = None,
) -> None:
    """
    Persiste a configuração incrementando a versão e registrando um
    evento de auditoria (Cap. 46/58/67) — nunca sobrescreve em
    silêncio. `o_que`/`valor_anterior`/`valor_novo` descrevem a
    alteração feita (ex.: "Método de cálculo", "Percentual", "Dias").
    """
    configuracao.versao += 1
    configuracao.atualizado_em = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
    configuracao.auditoria.append(RegistroAuditoria(
        quando=configuracao.atualizado_em, usuario=usuario or usuario_atual(),
        o_que=o_que, valor_anterior=valor_anterior, valor_novo=valor_novo,
    ))

    dados = {
        "metodo": configuracao.metodo.value,
        "ocorrencias": [_ocorrencia_para_dict(o) for o in configuracao.ocorrencias],
        "limiar_atencao": configuracao.limiar_atencao,
        "limiar_critico": configuracao.limiar_critico,
        "versao": configuracao.versao,
        "atualizado_em": configuracao.atualizado_em,
        "auditoria": [_auditoria_para_dict(e) for e in configuracao.auditoria],
    }
    escrever_json(_caminho_config(), dados, com_backup=True)
    log.info("Configuração de Absenteísmo salva (versão %d): %s", configuracao.versao, o_que)


# ---------------------------------------------------------------------------
# Motor de cálculo (Cap. 47/61/62) — agregação pura sobre dias já calculados
# ---------------------------------------------------------------------------

def calcular_indicadores(
    competencia: Competencia, configuracao: ConfiguracaoAbsenteismo,
) -> list[IndicadorAbsenteismo]:
    """
    Calcula o índice de absenteísmo de cada funcionário processado na
    competência (Cap. 47/62) — sempre por competência isolada, nunca
    misturando dados de competências diferentes (Cap. 62).
    """
    justificativas_consideradas = configuracao.justificativas_consideradas()
    competencia_texto = f"{nome_mes(competencia.mes)}/{competencia.ano}"
    return [
        _calcular_indicador_funcionario(
            funcionario, competencia_texto, configuracao, justificativas_consideradas)
        for funcionario in competencia.resultado.funcionarios_processados
    ]


def _calcular_indicador_funcionario(
    funcionario: Funcionario, competencia_texto: str,
    configuracao: ConfiguracaoAbsenteismo, justificativas_consideradas: frozenset[Justificativa],
) -> IndicadorAbsenteismo:
    dias_previstos = 0
    horas_previstas_min = 0
    horas_trabalhadas_min = 0
    horas_perdidas_min = 0
    dias_perdidos = 0
    ocorrencias: list[OcorrenciaAbsenteismo] = []

    for dia in funcionario.dias:
        jornada_prevista = dia.resultado.jornada_prevista_min
        if jornada_prevista <= 0:
            continue  # sem jornada prevista (folga/fim de semana sem turno) — fora da base

        dias_previstos += 1
        horas_previstas_min += jornada_prevista
        horas_trabalhadas_min += dia.resultado.horas_trabalhadas_min

        texto_justificativa = dia.pendencia.justificativa if dia.pendencia is not None else ""
        if not texto_justificativa:
            continue
        try:
            justificativa = Justificativa(texto_justificativa)
        except ValueError:
            continue

        considerada = justificativa in justificativas_consideradas
        ocorrencias.append(OcorrenciaAbsenteismo(
            data=dia.data, justificativa=justificativa, considerada=considerada))
        if considerada:
            dias_perdidos += 1
            horas_perdidas_min += max(0, jornada_prevista - dia.resultado.horas_trabalhadas_min)

    return IndicadorAbsenteismo(
        funcionario_id=funcionario.id, nome=funcionario.nome_completo,
        competencia_texto=competencia_texto,
        dias_previstos=dias_previstos, dias_perdidos=dias_perdidos,
        horas_previstas_min=horas_previstas_min, horas_trabalhadas_min=horas_trabalhadas_min,
        horas_perdidas_min=horas_perdidas_min, ocorrencias=ocorrencias,
        metodo=configuracao.metodo, configuracao_versao=configuracao.versao,
    )


# ---------------------------------------------------------------------------
# Memória de cálculo (Cap. 48/50/66) — a fórmula nunca fica escondida
# ---------------------------------------------------------------------------

def montar_memoria_calculo(indicador: IndicadorAbsenteismo) -> str:
    """Texto explicando exatamente como o índice foi obtido (Cap. 48/50) — nunca "caixa-preta"."""
    linhas = [
        f"Funcionário: {indicador.nome}",
        f"Competência: {indicador.competencia_texto}",
        f"Dias previstos: {indicador.dias_previstos}",
        f"Horas previstas: {formatar_minutos(indicador.horas_previstas_min)}",
        f"Horas trabalhadas: {formatar_minutos(indicador.horas_trabalhadas_min)}",
        f"Horas perdidas: {formatar_minutos(indicador.horas_perdidas_min)}",
        "",
        "Ocorrências consideradas no índice:",
    ]
    if indicador.ocorrencias_consideradas:
        linhas.extend(
            f"  {oc.data.strftime('%d/%m/%Y')} — {oc.justificativa.value}"
            for oc in indicador.ocorrencias_consideradas
        )
    else:
        linhas.append("  Nenhuma")

    linhas.append("")
    linhas.append("Ocorrências ignoradas (não contam no índice):")
    if indicador.ocorrencias_ignoradas:
        linhas.extend(
            f"  {oc.data.strftime('%d/%m/%Y')} — {oc.justificativa.value}"
            for oc in indicador.ocorrencias_ignoradas
        )
    else:
        linhas.append("  Nenhuma")

    linhas += [
        "",
        f"Configuração aplicada: versão {indicador.configuracao_versao}",
        f"Método: {indicador.metodo.value}",
        "",
        "Fórmula:",
        f"  {_texto_formula(indicador)}",
        "",
        f"Resultado final: {texto_resultado(indicador)}",
    ]
    return "\n".join(linhas)


def _texto_formula(indicador: IndicadorAbsenteismo) -> str:
    if indicador.metodo == MetodoCalculoAbsenteismo.PERCENTUAL:
        return (
            f"Horas perdidas ÷ Horas previstas × 100 = "
            f"{formatar_minutos(indicador.horas_perdidas_min)} ÷ "
            f"{formatar_minutos(indicador.horas_previstas_min)} × 100 = "
            f"{indicador.resultado_percentual:.2f}%"
        )
    if indicador.metodo == MetodoCalculoAbsenteismo.DIAS:
        return f"Dias perdidos = {indicador.dias_perdidos}"
    return f"Horas perdidas = {formatar_minutos(indicador.horas_perdidas_min)}"


def texto_resultado(indicador: IndicadorAbsenteismo) -> str:
    """Resultado final já formatado no método configurado (Cap. 47/49)."""
    if indicador.metodo == MetodoCalculoAbsenteismo.PERCENTUAL:
        return f"{indicador.resultado_percentual:.2f}%"
    if indicador.metodo == MetodoCalculoAbsenteismo.DIAS:
        return f"{indicador.dias_perdidos} dia(s)"
    return formatar_minutos(indicador.horas_perdidas_min)


# ---------------------------------------------------------------------------
# Índice geral, rankings, classificação por cor e alertas (Cap. 52/55/69/70/71)
# ---------------------------------------------------------------------------

def indice_geral(indicadores: list[IndicadorAbsenteismo]) -> float:
    """Índice consolidado de todos os funcionários (Cap. 52/70), no método vigente."""
    if not indicadores:
        return 0.0
    metodo = indicadores[0].metodo
    total_previstas = sum(i.horas_previstas_min for i in indicadores)
    total_perdidas = sum(i.horas_perdidas_min for i in indicadores)
    total_dias_perdidos = sum(i.dias_perdidos for i in indicadores)

    if metodo == MetodoCalculoAbsenteismo.DIAS:
        return float(total_dias_perdidos)
    if metodo == MetodoCalculoAbsenteismo.HORAS:
        return float(total_perdidas)
    if total_previstas <= 0:
        return 0.0
    return round((total_perdidas / total_previstas) * 100, 2)


def ranking(indicadores: list[IndicadorAbsenteismo], top: int = 10) -> list[IndicadorAbsenteismo]:
    """Ranking decrescente pelo resultado no método vigente (Cap. 52/69)."""
    return sorted(indicadores, key=lambda i: i.resultado_no_metodo(), reverse=True)[:top]


def classificar_cor(indicador: IndicadorAbsenteismo, configuracao: ConfiguracaoAbsenteismo) -> str:
    """Verde/Amarelo/Vermelho segundo os limiares configuráveis (Cap. 55) — sempre em percentual."""
    valor = indicador.resultado_percentual
    if valor >= configuracao.limiar_critico:
        return "vermelho"
    if valor >= configuracao.limiar_atencao:
        return "amarelo"
    return "verde"


def gerar_alertas(
    indicadores: list[IndicadorAbsenteismo], configuracao: ConfiguracaoAbsenteismo,
) -> list[str]:
    """Alertas em texto simples (Cap. 71) para quem ultrapassou os limiares configurados."""
    alertas: list[str] = []
    for indicador in indicadores:
        cor = classificar_cor(indicador, configuracao)
        if cor == "vermelho":
            alertas.append(
                f"{indicador.nome}: índice de {indicador.resultado_percentual:.2f}% "
                f"ultrapassou o limite crítico ({configuracao.limiar_critico:.1f}%)."
            )
        elif cor == "amarelo":
            alertas.append(
                f"{indicador.nome}: índice de {indicador.resultado_percentual:.2f}% "
                f"está em atenção (limite: {configuracao.limiar_atencao:.1f}%)."
            )
    return alertas


# ---------------------------------------------------------------------------
# Comparativo entre períodos (Cap. 56/74) e previsão simples (Cap. 75)
# ---------------------------------------------------------------------------

def comparar(
    indicadores_a: list[IndicadorAbsenteismo], indicadores_b: list[IndicadorAbsenteismo],
) -> dict[str, float]:
    """Compara o índice geral de dois conjuntos (ex.: duas competências, Cap. 56/74)."""
    indice_a = indice_geral(indicadores_a)
    indice_b = indice_geral(indicadores_b)
    diferenca_absoluta = round(indice_b - indice_a, 2)
    diferenca_percentual = round((diferenca_absoluta / indice_a * 100), 2) if indice_a else 0.0
    return {
        "indice_a": indice_a, "indice_b": indice_b,
        "diferenca_absoluta": diferenca_absoluta, "diferenca_percentual": diferenca_percentual,
    }


def prever_proximo_indice(indices_historicos: list[float]) -> float | None:
    """
    Estimativa simples (Cap. 75) do índice do próximo mês: média móvel
    dos até 3 últimos índices históricos. Deliberadamente simples e
    transparente (sem "caixa-preta" estatística) — sempre exibida como
    "Estimativa" na interface, nunca substitui um índice real.
    """
    if not indices_historicos:
        return None
    ultimos = indices_historicos[-3:]
    return round(sum(ultimos) / len(ultimos), 2)


# ---------------------------------------------------------------------------
# Simulador (Cap. 51) — nunca altera dados reais, só devolve uma cópia
# hipotética do indicador já calculado
# ---------------------------------------------------------------------------

def simular_dias_extras(
    indicador: IndicadorAbsenteismo, dias_extras_perdidos: int,
) -> IndicadorAbsenteismo:
    """"Se esse funcionário faltar mais N dias" (Cap. 51) — cópia hipotética, dado real intocado."""
    media_jornada_min = (
        indicador.horas_previstas_min // indicador.dias_previstos
        if indicador.dias_previstos else 0
    )
    return replace(
        indicador,
        dias_perdidos=indicador.dias_perdidos + dias_extras_perdidos,
        horas_perdidas_min=indicador.horas_perdidas_min + media_jornada_min * dias_extras_perdidos,
    )


def simular_remover_ocorrencia(
    indicador: IndicadorAbsenteismo, ocorrencia: OcorrenciaAbsenteismo,
) -> IndicadorAbsenteismo:
    """"Se remover essa ocorrência" (Cap. 51) — cópia hipotética, dado real intocado."""
    if not ocorrencia.considerada:
        return indicador
    media_jornada_min = (
        indicador.horas_previstas_min // indicador.dias_previstos
        if indicador.dias_previstos else 0
    )
    return replace(
        indicador,
        dias_perdidos=max(0, indicador.dias_perdidos - 1),
        horas_perdidas_min=max(0, indicador.horas_perdidas_min - media_jornada_min),
        ocorrencias=[o for o in indicador.ocorrencias if o is not ocorrencia],
    )
