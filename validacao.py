"""
validacao.py
-------------
Validação estrutural dos dados extraídos da planilha (Cap. 9).

Responsabilidade única: examinar os FuncionarioPlanilha já lidos por
leitor_ponto.py e produzir uma lista de Pendencia (Cap. 16) — nunca
interrompe o processamento (Cap. 9.1), apenas sinaliza. Não lê arquivo,
não conhece Config, não faz matching com o cadastro.
"""

from __future__ import annotations

from constantes import TipoPendencia
from logger import get_logger
from modelos import FuncionarioPlanilha, Pendencia

log = get_logger()

# Quantidade de batidas esperada num dia normal (Cap. 6.3/7.1)
_QUANTIDADE_NORMAL_BATIDAS = 4


def validar_planilha(funcionarios: list[FuncionarioPlanilha]) -> list[Pendencia]:
    """
    Valida a estrutura já extraída (Cap. 9.2): funcionário sem nenhuma
    batida no período, dias com quantidade incomum de batidas. Retorna
    todas as pendências encontradas — nunca bloqueia o processamento.
    """
    pendencias: list[Pendencia] = []
    for funcionario in funcionarios:
        pendencias.extend(_validar_funcionario(funcionario))
    return pendencias


def _validar_funcionario(funcionario: FuncionarioPlanilha) -> list[Pendencia]:
    """Valida um único funcionário: sem batidas no período, ou dia a dia."""
    if not funcionario.dias or all(not dia.batidas for dia in funcionario.dias):
        log.info(
            "Sem batidas em todo o período: %s (id planilha %s).",
            funcionario.nome_planilha, funcionario.id_planilha,
        )
        return [Pendencia(
            tipo=TipoPendencia.SEM_BATIDAS,
            id_funcionario=funcionario.id_planilha,
            nome_funcionario=funcionario.nome_planilha,
            descricao="Nenhuma batida registrada em todo o período.",
        )]

    pendencias: list[Pendencia] = []
    for dia in funcionario.dias:
        tipo = _tipo_pendencia_por_quantidade(len(dia.batidas))
        if tipo is None:
            continue
        pendencias.append(Pendencia(
            tipo=tipo,
            id_funcionario=funcionario.id_planilha,
            nome_funcionario=funcionario.nome_planilha,
            data=dia.data,
            descricao=f"{len(dia.batidas)} batida(s) em {dia.data.strftime('%d/%m/%Y')}.",
        ))

    return pendencias


def _tipo_pendencia_por_quantidade(quantidade: int) -> TipoPendencia | None:
    """
    Classifica a quantidade de batidas de um dia (Cap. 7): 0 batidas
    (dia sem registro) não gera pendência aqui — é normal (folga, falta
    ainda não justificada, fim de semana) e será tratado pelo motor de
    cálculo (Sprint 4). 4 batidas é a situação normal (Cap. 7.1).
    """
    if quantidade in (0, _QUANTIDADE_NORMAL_BATIDAS):
        return None
    if quantidade == 1:
        return TipoPendencia.UMA_BATIDA
    if quantidade == 2:
        return TipoPendencia.DUAS_BATIDAS
    if quantidade == 3:
        return TipoPendencia.TRES_BATIDAS
    return TipoPendencia.MAIS_DE_QUATRO
