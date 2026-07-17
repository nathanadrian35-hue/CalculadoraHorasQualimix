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

from datetime import date, datetime, time
from pathlib import Path
from typing import Any

import config
from constantes import Situacao, StatusCompetencia, TipoPendencia
from logger import get_logger
from modelos import (
    Batida,
    Competencia,
    DiaTrabalho,
    Funcionario,
    Pendencia,
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
    se houver — mesma rede de segurança do resto do app).
    """
    caminho = _caminho(competencia.mes, competencia.ano)
    dados = _competencia_para_dict(competencia)
    config.escrever_json(caminho, dados, com_backup=True)
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
    )
