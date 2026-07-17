"""
cadastro.py
------------
Orquestração entre a leitura da planilha (leitor_ponto.py), a validação
(validacao.py) e o motor de sugestão do Sprint 3/3.5 (modelos.py) — monta
a lista de SugestaoImportacao que alimenta o Painel de Revisão
(tela_funcionarios.iniciar_revisao_importacao) e a lista de
SetorNovoEncontrado que alimenta a tela de confirmação de Setores novos
(tela_funcionarios.iniciar_revisao_setores_novos, Cap. 5.17).

Responsabilidade única: orquestrar. Nenhuma lógica de matching/sugestão
é reimplementada aqui — apenas chamadas às funções já existentes
(sugerir_turno, sugerir_setor, departamentos_sem_setor,
grafia_amigavel_setor, localizar_funcionario_por_nome,
horario_entrada_predominante), reaproveitadas integralmente.

A importação acontece em duas etapas, com um ponto de pausa opcional no
meio (Cap. 5.17): `preparar_importacao()` lê e valida a planilha e
identifica os Setores novos; só depois de resolvidos (criados ou
ignorados) é que `montar_sugestoes_importacao()` deve ser chamada — ela
lê `config.setores` no momento em que roda, então já enxerga os Setores
recém-criados sem precisar de uma segunda importação.
"""

from __future__ import annotations

from pathlib import Path

import config as config_modulo
from config import Config
from constantes import SituacaoSugestao
from leitor_ponto import ler_planilha
from logger import get_logger
from modelos import (
    FuncionarioPlanilha,
    Pendencia,
    SetorNovoEncontrado,
    SugestaoImportacao,
    departamentos_sem_setor,
    grafia_amigavel_setor,
    horario_entrada_predominante,
    localizar_funcionario_por_id_planilha,
    localizar_funcionario_por_nome,
    normalizar_texto,
    sugerir_setor,
    sugerir_turno,
)
from validacao import validar_planilha

log = get_logger()


def preparar_importacao(
    caminho: Path, config: Config,
) -> tuple[
    list[FuncionarioPlanilha], list[Pendencia], list[SetorNovoEncontrado], tuple[int, int],
]:
    """
    Lê e valida a planilha (Cap. 3/9) e identifica os "Dep." que ainda
    não correspondem a nenhum Setor cadastrado (Cap. 5.17). Não monta
    as sugestões de importação ainda — isso só deve acontecer depois
    que os Setores novos forem resolvidos (criados ou ignorados), para
    que a sugestão de Setor já considere os recém-criados sem exigir
    uma segunda importação (ver `montar_sugestoes_importacao`).

    O último item retornado é a competência (mês, ano) da planilha —
    repassada adiante até o Motor de Cálculo (Cap. 6, `ContextoCalculo`).

    Pode levantar leitor_ponto.PlanilhaInvalidaError se o arquivo não
    puder ser lido ou não tiver competência localizável.
    """
    mes, ano, funcionarios_planilha = ler_planilha(caminho)
    pendencias = validar_planilha(funcionarios_planilha)
    setores_novos = _identificar_setores_novos(funcionarios_planilha, config)

    log.info(
        "Planilha lida: %d funcionário(s), %d pendência(s), %d setor(es) novo(s).",
        len(funcionarios_planilha), len(pendencias), len(setores_novos),
    )

    return funcionarios_planilha, pendencias, setores_novos, (mes, ano)


def _identificar_setores_novos(
    funcionarios_planilha: list[FuncionarioPlanilha], config: Config,
) -> list[SetorNovoEncontrado]:
    """
    Reaproveita `departamentos_sem_setor()` para achar os "Dep." sem
    Setor correspondente e, para cada um, conta quantos funcionários da
    planilha pertencem a ele (mesma comparação tolerante) e normaliza o
    nome para a grafia amigável (Cap. 5.17) — sem duplicar nenhuma
    lógica de matching já existente em modelos.py.
    """
    setores = [
        config_modulo.setor_de_dict(dados) for dados in config.setores.get("setores", [])
    ]
    departamentos = [f.departamento for f in funcionarios_planilha if f.departamento]

    novos = departamentos_sem_setor(departamentos, setores)
    if not novos:
        return []

    log.info("Setores novos encontrados na planilha: %s", ", ".join(novos))

    setores_novos: list[SetorNovoEncontrado] = []
    for departamento_bruto in novos:
        chave = normalizar_texto(departamento_bruto)
        quantidade = sum(
            1 for f in funcionarios_planilha
            if f.departamento and normalizar_texto(f.departamento) == chave
        )
        setores_novos.append(SetorNovoEncontrado(
            nome=grafia_amigavel_setor(departamento_bruto),
            quantidade_funcionarios=quantidade,
        ))

    return setores_novos


def montar_sugestoes_importacao(
    funcionarios_planilha: list[FuncionarioPlanilha], config: Config,
) -> list[SugestaoImportacao]:
    """
    Para cada funcionário lido da planilha: detecta o horário
    predominante, localiza o cadastro existente (ou marca como novo),
    sugere turno e setor — reaproveitando integralmente o motor de
    sugestão do Sprint 3. Nenhuma lógica nova de matching é criada aqui.

    A localização do cadastro tenta primeiro `id_planilha` (IDUsuário —
    identificador principal, Cap. 5.8), e só recorre ao nome quando o
    cadastro ainda não tem `id_planilha` salvo — esse fallback por nome
    é justamente o que migra automaticamente cadastros antigos na
    primeira importação em que reaparecerem (migração just-in-time).
    """
    turnos = [
        config_modulo.turno_de_dict(dados) for dados in config.configuracoes.get("turnos", [])
    ]
    setores = [
        config_modulo.setor_de_dict(dados) for dados in config.setores.get("setores", [])
    ]
    funcionarios_cadastrados = [
        config_modulo.funcionario_de_dict(dados)
        for dados in config.funcionarios.get("funcionarios", [])
    ]

    sugestoes: list[SugestaoImportacao] = []

    for funcionario_planilha in funcionarios_planilha:
        horario = horario_entrada_predominante(funcionario_planilha.dias)

        encontrado = localizar_funcionario_por_id_planilha(
            funcionario_planilha.id_planilha, funcionarios_cadastrados)
        if encontrado is None:
            encontrado = localizar_funcionario_por_nome(
                funcionario_planilha.nome_planilha, funcionarios_cadastrados)
        if encontrado is None:
            log.info(
                "Nome não encontrado no cadastro (novo funcionário): \"%s\".",
                funcionario_planilha.nome_planilha,
            )

        if horario is not None:
            turno_sugerido, situacao_turno = sugerir_turno(horario, turnos)
        else:
            turno_sugerido, situacao_turno = None, SituacaoSugestao.REVISAR

        setor_sugerido, situacao_setor = sugerir_setor(
            funcionario_planilha.departamento, setores)
        if situacao_setor == SituacaoSugestao.REVISAR:
            log.info(
                'Setor não encontrado ("%s") para "%s" — marcado para revisão.',
                funcionario_planilha.departamento, funcionario_planilha.nome_planilha,
            )

        situacao_geral = (
            SituacaoSugestao.CONFIRMADO
            if situacao_turno == SituacaoSugestao.CONFIRMADO
            and situacao_setor == SituacaoSugestao.CONFIRMADO
            else SituacaoSugestao.REVISAR
        )

        sugestoes.append(SugestaoImportacao(
            nome_planilha=funcionario_planilha.nome_planilha,
            horario_entrada=horario,
            turno_sugerido_id=turno_sugerido.id if turno_sugerido else None,
            situacao=situacao_geral,
            funcionario_id=encontrado.id if encontrado else None,
            setor_sugerido_id=setor_sugerido.id if setor_sugerido else None,
            id_planilha=funcionario_planilha.id_planilha,
        ))

    return sugestoes
