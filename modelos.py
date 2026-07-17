"""
modelos.py
----------
Estruturas de dados internas do sistema (Cap. 16 da especificação).

Estas dataclasses formam o "contrato" de comunicação entre os módulos:
o leitor produz Funcionario/DiaTrabalho/Batida, o motor de cálculo preenche
ResultadoDia, e o relatório consome tudo. Nenhum módulo deve trafegar
dicionários soltos — sempre usar estes modelos.

Hierarquia:
    Empresa
      └── Funcionario
            └── DiaTrabalho
                  ├── Batida (lista)
                  └── ResultadoDia
    Pendencia (transversal, ligada a um funcionário/dia)
    ContextoCalculo / ResultadoProcessamento (Cap. 6, Motor de Cálculo)
"""

from __future__ import annotations

import unicodedata
import uuid
from dataclasses import dataclass, field
from datetime import date, datetime, time
from pathlib import Path
from typing import TYPE_CHECKING

from constantes import (
    GRAFIAS_SETOR_PADRAO,
    Situacao,
    SituacaoSugestao,
    StatusCompetencia,
    StatusFuncionario,
    TipoPendencia,
)

if TYPE_CHECKING:
    from config import Config


# ---------------------------------------------------------------------------
# Empresa
# ---------------------------------------------------------------------------

@dataclass
class Empresa:
    """Dados da empresa exibidos na interface e nos relatórios."""

    nome: str = ""
    logo_caminho: str = ""  # caminho relativo para assets/logo


# ---------------------------------------------------------------------------
# Turno
# ---------------------------------------------------------------------------

def diferenca_minutos(inicio: time, fim: time) -> int | None:
    """
    Retorna a diferença em minutos entre dois horários do mesmo dia
    (fim - início). Retorna None se `fim` não for posterior a `início`
    (turnos que cruzam a meia-noite não são suportados nesta versão).

    Usada por `JornadaDia.jornada_prevista_minutos()` e reaproveitada
    por `calculadora.py` (Cap. 6/10) para o mesmo cálculo de duração
    entre duas batidas — única fonte dessa conta em todo o sistema.
    """
    minutos_inicio = inicio.hour * 60 + inicio.minute
    minutos_fim = fim.hour * 60 + fim.minute
    if minutos_fim <= minutos_inicio:
        return None
    return minutos_fim - minutos_inicio


@dataclass
class JornadaDia:
    """
    Horários previstos para um tipo de dia (Segunda a Sexta, Sábado ou
    Domingo) dentro de um Turno (Cap. 4.6/6.4/6.5). O intervalo
    (almoço) é sempre opcional: quando início/fim do intervalo não
    estiverem preenchidos, o dia simplesmente não tem horário de
    almoço previsto — não é uma regra fixa do sistema.
    """

    entrada: time | None = None              # horário previsto de entrada
    saida: time | None = None                # horário previsto de saída
    inicio_intervalo: time | None = None     # início do intervalo (almoço), opcional
    fim_intervalo: time | None = None        # fim do intervalo (almoço), opcional

    def jornada_prevista_minutos(self) -> int | None:
        """
        Calcula automaticamente a jornada prevista deste dia, em minutos:
        (saída - entrada) descontando o intervalo (fim - início), quando
        ambos os horários do intervalo estiverem preenchidos.

        Retorna None se entrada/saída não estiverem definidos ou formarem
        um período inválido.
        """
        if self.entrada is None or self.saida is None:
            return None

        minutos_expediente = diferenca_minutos(self.entrada, self.saida)
        if minutos_expediente is None:
            return None

        minutos_intervalo = 0
        if self.inicio_intervalo is not None and self.fim_intervalo is not None:
            diferenca_intervalo = diferenca_minutos(self.inicio_intervalo, self.fim_intervalo)
            if diferenca_intervalo is not None:
                minutos_intervalo = diferenca_intervalo

        return minutos_expediente - minutos_intervalo


@dataclass
class Turno:
    """
    Um turno de trabalho cadastrado, com jornada independente por tipo
    de dia (Cap. 4.6): Segunda a Sexta (sempre presente), Sábado e
    Domingo (opcionais — Cap. 6.4/6.5).

    `sabado`/`domingo` valendo None significa que o turno não prevê
    trabalho naquele dia (equivalente ao checkbox "Trabalha sábado"/
    "Trabalha domingo" desmarcado); quando presentes, carregam os
    próprios horários daquele dia, independentes dos demais.

    O `id` é gerado automaticamente e nunca deve ser editado pelo
    usuário. O vínculo com funcionários deve sempre usar o `id`, nunca
    o `nome` (Cap. 5.13/21.4) — assim, renomear um turno não quebra os
    vínculos já existentes.
    """

    nome: str                                # rótulo exibido, ex.: "06:00 às 15:00"
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    segunda_a_sexta: JornadaDia = field(default_factory=JornadaDia)
    sabado: JornadaDia | None = None
    domingo: JornadaDia | None = None

    def jornada_do_dia(self, data: date) -> JornadaDia | None:
        """
        Retorna a jornada prevista deste Turno para o dia informado
        (Cap. 4.6/6.4/6.5), despachando por dia da semana: Segunda a
        Sexta é sempre retornada; Sábado/Domingo só se estiverem
        configurados (None caso contrário — dia sem jornada prevista).

        Despacho estrutural, não cálculo de horas — por isso vive aqui
        e não em calculadora.py (Cap. 18).
        """
        indice = data.weekday()  # 0=segunda ... 6=domingo
        if indice <= 4:
            return self.segunda_a_sexta
        if indice == 5:
            return self.sabado
        return self.domingo


# ---------------------------------------------------------------------------
# Setor
# ---------------------------------------------------------------------------

@dataclass
class Setor:
    """
    Um setor da empresa (Cap. 21), usado futuramente para vincular
    funcionários (Sprint 3).

    O `id` é gerado automaticamente e nunca deve ser editado pelo
    usuário. O vínculo com funcionários deve sempre usar o `id`, nunca
    o `nome` — assim, renomear um setor não quebra os vínculos já
    existentes.
    """

    nome: str
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    cor: str = ""                              # opcional, uso futuro em gráficos/relatórios
    status: StatusFuncionario = StatusFuncionario.ATIVO


# ---------------------------------------------------------------------------
# Funcionário
# ---------------------------------------------------------------------------

@dataclass
class Funcionario:
    """
    Funcionário (Cap. 5) — cadastrado principalmente pela importação da
    planilha, complementado por cadastro manual quando necessário.

    O `id` é gerado automaticamente e nunca editável. O vínculo com
    Turno e Setor é sempre por `turno_id`/`setor_id`, nunca por nome
    (Cap. 5.13 / 21.4) — renomear um Turno ou Setor nunca quebra o
    vínculo já existente.
    """

    nome_completo: str
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    nome_planilha: str = ""      # opcional; usado para localizar na planilha (Cap. 5.8)
    id_planilha: str = ""        # "IDUsuário" da planilha — identificador principal
    apelido: str = ""
    matricula: str = ""
    cpf: str = ""
    cargo: str = ""
    turno_id: str = ""           # vínculo por ID com Turno (Cap. 4.6); "" = sem turno
    setor_id: str = ""           # vínculo por ID com Setor (Cap. 21); "" = sem setor
    status: StatusFuncionario = StatusFuncionario.ATIVO
    data_cadastro: str = ""      # ISO (dd/mm/aaaa HH:MM:SS)
    ultima_atualizacao: str = ""  # ISO

    # Dados de processamento (preenchidos em memória, não persistidos no JSON)
    dias: list["DiaTrabalho"] = field(default_factory=list)

    def nome_para_localizacao(self) -> str:
        """
        Nome usado para localizar este funcionário numa planilha
        (Cap. 5.8): o Nome utilizado na Planilha, ou o Nome Completo se
        aquele estiver vazio.
        """
        return self.nome_planilha or self.nome_completo


# ---------------------------------------------------------------------------
# Sugestão de importação (Painel de Revisão — Cap. 5.4)
# ---------------------------------------------------------------------------

@dataclass
class SugestaoImportacao:
    """
    Uma linha do Painel de Revisão: um funcionário identificado numa
    importação (real ou simulada), com o turno sugerido automaticamente
    e a confiança da sugestão.

    Transitória — não é persistida em funcionarios.json. Existe apenas
    durante a revisão de uma importação (Cap. 5.2/5.4).
    """

    nome_planilha: str
    horario_entrada: time | None
    turno_sugerido_id: str | None
    situacao: SituacaoSugestao
    funcionario_id: str | None = None   # preenchido se já existe cadastro correspondente
    setor_sugerido_id: str | None = None
    id_planilha: str = ""               # "IDUsuário" da planilha (Cap. 5.8)


# Diferença máxima (em minutos) entre o horário detectado e a entrada de um
# turno para a sugestão ser considerada confiável (Cap. 5.5). É um parâmetro
# de confiança do motor de sugestão, não uma regra de tolerância de cálculo
# (que continua sendo config.configuracoes["tolerancia_entrada"], Cap. 8).
LIMITE_CONFIANCA_MINUTOS: int = 15


@dataclass
class SetorNovoEncontrado:
    """
    Um "Dep." encontrado numa planilha que ainda não corresponde a
    nenhum Setor cadastrado (Cap. 5.17): o nome já na grafia amigável
    (`grafia_amigavel_setor`) e a quantidade de funcionários da
    planilha que pertencem a ele, exibida na tela de confirmação.

    Transitória — não é persistida. Só existe entre o processamento da
    planilha e a decisão do usuário de criar (ou não) o Setor.
    """

    nome: str
    quantidade_funcionarios: int


def sugerir_turno(
    horario_entrada: time, turnos: list[Turno],
) -> tuple[Turno | None, SituacaoSugestao]:
    """
    Motor de sugestão de turno (Cap. 5.5): compara o horário de entrada
    detectado (predominantemente de dias de semana, Cap. 5.2) com a
    entrada de Segunda a Sexta (Cap. 4.6) de cada turno cadastrado e
    sugere o mais próximo.

    Retorna (turno_sugerido, situacao):
        - Um único turno mais próximo, dentro de LIMITE_CONFIANCA_MINUTOS
          e sem empate -> (turno, CONFIRMADO).
        - Turno mais próximo, porém fora do limite de confiança ou
          empatado com outro -> (turno_mais_proximo_ou_None, REVISAR).
        - Nenhum turno com horário de entrada cadastrado -> (None, REVISAR).
    """
    minutos_alvo = horario_entrada.hour * 60 + horario_entrada.minute

    candidatos: list[tuple[int, Turno]] = []
    for turno in turnos:
        entrada_semana = turno.segunda_a_sexta.entrada
        if entrada_semana is None:
            continue
        minutos_turno = entrada_semana.hour * 60 + entrada_semana.minute
        candidatos.append((abs(minutos_turno - minutos_alvo), turno))

    if not candidatos:
        return None, SituacaoSugestao.REVISAR

    candidatos.sort(key=lambda item: item[0])
    menor_diferenca, turno_mais_proximo = candidatos[0]

    empatado = len(candidatos) > 1 and candidatos[1][0] == menor_diferenca
    confiavel = menor_diferenca <= LIMITE_CONFIANCA_MINUTOS and not empatado

    situacao = SituacaoSugestao.CONFIRMADO if confiavel else SituacaoSugestao.REVISAR
    return turno_mais_proximo, situacao


def localizar_funcionario_por_nome(
    nome: str, funcionarios: list[Funcionario],
) -> Funcionario | None:
    """
    Localiza, dentre os funcionários já cadastrados, aquele cujo nome de
    localização (Cap. 5.8: Nome na Planilha, ou Nome Completo se vazio)
    corresponde exatamente ao nome informado. Retorna None se nenhum
    corresponder — nesse caso, trata-se de um novo funcionário
    (Cap. 5.2), nunca uma pendência silenciosa.
    """
    nome_normalizado = nome.strip().lower()
    for funcionario in funcionarios:
        if funcionario.nome_para_localizacao().strip().lower() == nome_normalizado:
            return funcionario
    return None


def localizar_funcionario_por_id_planilha(
    id_planilha: str, funcionarios: list[Funcionario],
) -> Funcionario | None:
    """
    Localiza, dentre os funcionários já cadastrados, aquele cujo
    `id_planilha` ("IDUsuário" do relógio de ponto) corresponde
    exatamente ao informado — identificador principal (Cap. 5.8),
    permitindo diferenciar corretamente funcionários com o mesmo nome
    (homônimos). `localizar_funcionario_por_nome()` continua existindo
    como fallback: usado quando um cadastro ainda não tem `id_planilha`
    salvo (migração automática — Cap. 5.8).

    Recusa `id_planilha` vazio de propósito: cadastros ainda não
    migrados têm `id_planilha == ""`, e casar dois vazios por acidente
    atropelaria o fallback por nome que a migração depende.
    """
    id_normalizado = id_planilha.strip()
    if not id_normalizado:
        return None
    for funcionario in funcionarios:
        if funcionario.id_planilha.strip() == id_normalizado:
            return funcionario
    return None


def indices_com_nome_duplicado(nomes: list[str]) -> set[int]:
    """
    Índices de `nomes` cujo valor (sem espaços nas pontas, sem
    diferenciar maiúsculas/minúsculas) se repete em outra posição da
    lista — usada pela validação de nome único de Turnos (Cap. 4.6),
    junto com `nome_duplicado()` abaixo (Setores, Cap. 21.2), para não
    duplicar a mesma regra de comparação em cada tela.
    """
    normalizados = [nome.strip().casefold() for nome in nomes]
    return {
        indice for indice, nome in enumerate(normalizados)
        if nome and normalizados.count(nome) > 1
    }


def nome_duplicado(nome: str, nomes_existentes: list[str]) -> bool:
    """True se `nome` já aparece em `nomes_existentes` (Cap. 21.2), ignorando espaços/caixa."""
    alvo = nome.strip().casefold()
    return any(existente.strip().casefold() == alvo for existente in nomes_existentes)


def normalizar_texto(texto: str) -> str:
    """
    Normaliza um texto para comparação tolerante: remove acentos,
    colapsa espaços duplicados, remove espaços nas pontas e converte
    para minúsculas (ex.: " Logística " e "LOGISTICA" -> "logistica").

    Usada por `sugerir_setor()` (Cap. 5.5-Setor) e pelo leitor da
    planilha para reconhecer rótulos de cabeçalho independentemente de
    variações de acentuação/caixa na fonte de dados. Não é usada por
    `localizar_funcionario_por_nome()`, que mantém sua própria regra
    (Cap. 5.8) desde o Sprint 3.
    """
    sem_acento = unicodedata.normalize("NFKD", texto)
    sem_acento = "".join(c for c in sem_acento if not unicodedata.combining(c))
    return " ".join(sem_acento.split()).lower()


def _setores_correspondentes(departamento: str, setores: list[Setor]) -> list[Setor]:
    """
    Lista os Setores cadastrados cujo nome normalizado (via
    `normalizar_texto`) é igual ao do `departamento` informado — a
    comparação tolerante a maiúsculas/minúsculas, acentos e espaços
    extras que serve de base tanto para `sugerir_setor()` quanto para
    `departamentos_sem_setor()` (Cap. 5.16/5.17). Única fonte da regra
    de comparação, para não duplicá-la entre as duas funções.
    """
    alvo = normalizar_texto(departamento) if departamento else ""
    if not alvo:
        return []
    return [s for s in setores if normalizar_texto(s.nome) == alvo]


def sugerir_setor(
    departamento: str, setores: list[Setor],
) -> tuple[Setor | None, SituacaoSugestao]:
    """
    Motor de sugestão de setor (Cap. 5.5-Setor): compara o "Dep."
    encontrado na planilha com o nome de cada Setor cadastrado, de
    forma tolerante a maiúsculas/minúsculas, acentos e espaços extras
    (via `_setores_correspondentes`).

    Retorna (setor_sugerido, situacao):
        - Exatamente um Setor com nome normalizado igual ao
          departamento -> (setor, CONFIRMADO).
        - Mais de um Setor com o mesmo nome normalizado (ambíguo) ->
          (primeiro_encontrado, REVISAR).
        - Nenhuma correspondência, ou departamento vazio ->
          (None, REVISAR).
    """
    correspondentes = _setores_correspondentes(departamento, setores)

    if len(correspondentes) == 1:
        return correspondentes[0], SituacaoSugestao.CONFIRMADO
    if len(correspondentes) > 1:
        return correspondentes[0], SituacaoSugestao.REVISAR

    return None, SituacaoSugestao.REVISAR


def departamentos_sem_setor(departamentos: list[str], setores: list[Setor]) -> list[str]:
    """
    A partir dos valores de "Dep." lidos de uma planilha, retorna os
    que não correspondem a nenhum Setor já cadastrado (Cap. 5.17) —
    "Setores novos". Deduplicado por nome normalizado (via
    `_setores_correspondentes`, a mesma regra de `sugerir_setor()`),
    preservando a grafia da primeira ocorrência e a ordem em que
    apareceram na planilha. Departamentos vazios são ignorados.
    """
    vistos: set[str] = set()
    resultado: list[str] = []
    for departamento in departamentos:
        dep = departamento.strip() if departamento else ""
        if not dep:
            continue
        chave = normalizar_texto(dep)
        if chave in vistos:
            continue
        vistos.add(chave)
        if not _setores_correspondentes(dep, setores):
            resultado.append(dep)
    return resultado


def _capitalizar_amigavel(texto: str) -> str:
    """
    Capitalização "Título Case" usada como último recurso por
    `grafia_amigavel_setor()`, quando não há grafia padrão conhecida
    para o nome (Cap. 5.17): primeira letra de cada palavra em
    maiúscula, restante em minúscula. Palavras de até 3 letras são
    tratadas como sigla e mantidas totalmente em maiúsculas (mesmo
    critério aplicado a "RH"/"ADM" em GRAFIAS_SETOR_PADRAO). Não
    restaura acentos ausentes — isso só é possível para os nomes
    listados em GRAFIAS_SETOR_PADRAO.
    """
    palavras = texto.split()
    return " ".join(
        palavra.upper() if len(palavra) <= 3 else palavra.capitalize()
        for palavra in palavras
    )


def grafia_amigavel_setor(nome: str) -> str:
    """
    Normaliza a apresentação de um nome de Setor criado automaticamente
    durante a importação (Cap. 5.17), para não gravar no cadastro um
    "Dep." digitado todo em maiúsculas, minúsculas ou sem acentuação.

    Usa a grafia padrão conhecida (GRAFIAS_SETOR_PADRAO) quando o nome
    (comparado via `normalizar_texto`) estiver nela; caso contrário,
    aplica capitalização amigável como melhor esforço — o matching
    tolerante (`sugerir_setor`/`departamentos_sem_setor`) continua
    funcionando normalmente independentemente da grafia escolhida aqui.
    """
    nome = nome.strip()
    if not nome:
        return nome
    chave = normalizar_texto(nome)
    if chave in GRAFIAS_SETOR_PADRAO:
        return GRAFIAS_SETOR_PADRAO[chave]
    return _capitalizar_amigavel(nome)


# ---------------------------------------------------------------------------
# Funcionário conforme extraído da planilha (Sprint 3.5 — Cap. 3.2/3.3)
# ---------------------------------------------------------------------------

@dataclass
class FuncionarioPlanilha:
    """
    Um funcionário conforme extraído diretamente da planilha (Cap. 3.2/
    3.3), antes de qualquer casamento com o cadastro (Funcionario) ou
    sugestão de turno/setor. Puramente estrutural — nunca é persistida.

    `id_planilha` é o "IDUsuário" da planilha: uso apenas informativo/
    log — a localização do funcionário cadastrado usa o nome
    (`localizar_funcionario_por_nome`), nunca este id (Cap. 5.7/5.8).
    """

    id_planilha: str
    nome_planilha: str
    departamento: str = ""
    dias: list["DiaTrabalho"] = field(default_factory=list)


# Tamanho do agrupamento (em minutos) usado para detectar o horário de
# entrada "predominante" a partir de horários próximos, mas não idênticos
# (Cap. 5.2). Parâmetro do motor de sugestão, ajustável — não uma regra
# de cálculo de horas.
TAMANHO_BUCKET_MINUTOS: int = 5


def horario_entrada_predominante(dias: list["DiaTrabalho"]) -> time | None:
    """
    Detecta o horário de entrada predominante de um funcionário
    (Cap. 5.2), a partir dos dias lidos da planilha: a primeira batida
    de cada dia é considerada a entrada daquele dia. Entre todas essas
    entradas, agrupa por proximidade (blocos de TAMANHO_BUCKET_MINUTOS)
    e retorna o horário médio do grupo mais frequente — robusto a dias
    isolados com entrada atípica (ex.: batida da manhã esquecida).

    Retorna None se não houver nenhuma batida em nenhum dia.
    """
    entradas_minutos: list[int] = []
    for dia in dias:
        if not dia.batidas:
            continue
        primeira = min(dia.batidas, key=lambda b: (b.horario.hour, b.horario.minute))
        entradas_minutos.append(primeira.horario.hour * 60 + primeira.horario.minute)

    if not entradas_minutos:
        return None

    buckets: dict[int, list[int]] = {}
    for minutos in entradas_minutos:
        bucket = minutos // TAMANHO_BUCKET_MINUTOS
        buckets.setdefault(bucket, []).append(minutos)

    maior_bucket = max(buckets.values(), key=len)
    media_minutos = round(sum(maior_bucket) / len(maior_bucket))
    return time(hour=media_minutos // 60, minute=media_minutos % 60)


# ---------------------------------------------------------------------------
# Batida
# ---------------------------------------------------------------------------

@dataclass
class Batida:
    """
    Uma marcação de ponto individual.

    `horario` é o valor efetivo usado no cálculo. `manual` indica que a
    batida foi digitada pelo usuário na tela de pendências (Cap. 9.4/9.5),
    o que deve ser registrado no relatório e nos logs.
    """

    horario: time
    manual: bool = False


# ---------------------------------------------------------------------------
# Resultado do cálculo diário (Cap. 6/10)
# ---------------------------------------------------------------------------

@dataclass
class ResultadoDia:
    """
    Resultado completo do cálculo de um único dia (Cap. 10), sempre
    produzido por inteiro por `calculadora.recalcular_dia()` — nunca em
    etapas parciais, para não deixar o dia num estado inconsistente.

    Todos os valores são em minutos inteiros (nunca float, Cap. 6): só
    a interface/relatório converte para "8h00"/"-0h35"
    (`constantes.formatar_minutos`).
    """

    horas_trabalhadas_min: int = 0
    jornada_prevista_min: int = 0
    saldo_min: int = 0               # horas_trabalhadas_min - jornada_prevista_min
    horas_extras_min: int = 0
    horas_negativas_min: int = 0
    situacao: Situacao = Situacao.NORMAL


# ---------------------------------------------------------------------------
# Dia de trabalho
# ---------------------------------------------------------------------------

@dataclass
class DiaTrabalho:
    """Um dia do funcionário: data, dia da semana, batidas e resultado."""

    data: date
    dia_semana: str = ""                                 # ex.: "Quarta-feira"
    batidas: list[Batida] = field(default_factory=list)
    resultado: ResultadoDia = field(default_factory=ResultadoDia)
    observacoes: str = ""
    pendencia: "Pendencia | None" = None


# ---------------------------------------------------------------------------
# Pendência
# ---------------------------------------------------------------------------

@dataclass
class Pendencia:
    """
    Uma pendência detectada durante o processamento (Cap. 9 / 11 - Aba 3).

    Fica associada a um funcionário e (quando aplicável) a uma data.
    O status muda para "Resolvida" após justificativa/correção do usuário.
    """

    tipo: TipoPendencia
    id_funcionario: str
    nome_funcionario: str
    data: date | None = None
    descricao: str = ""
    justificativa: str = ""
    observacoes: str = ""
    resolvida: bool = False


# ---------------------------------------------------------------------------
# Contexto e resultado do processamento (Cap. 6) — Motor de Cálculo
# ---------------------------------------------------------------------------

@dataclass
class ContextoCalculo:
    """
    Agrupa tudo que `calculadora.recalcular_dia()` precisa além do
    próprio dia (Cap. 6), para a assinatura da função não crescer a
    cada nova regra. Criado uma vez por funcionário (com o Turno já
    resolvido) e reaproveitado para todos os dias dele — os demais
    campos são fixos para toda a competência sendo processada.

    `feriados` é um ponto reservado para uma futura sprint de Feriados
    (Cap. 6.6): sempre vazio nesta versão — nenhuma lógica de feriado
    está implementada ainda, só o lugar na ordem de cálculo.
    """

    config: "Config"
    turno: Turno
    funcionario_id: str = ""
    nome_funcionario: str = ""
    nome_empresa: str = ""
    competencia: tuple[int, int] | None = None  # (mês, ano)
    feriados: frozenset[date] = field(default_factory=frozenset)


@dataclass
class ResumoMensalFuncionario:
    """
    Resumo mensal de um funcionário (Cap. 11.4, Aba 2) — agregação
    pura sobre os dias já calculados por `recalcular_dia()`, sem
    nenhum cálculo novo. Transitório, não persistido.
    """

    funcionario_id: str
    nome: str
    dias_trabalhados: int = 0
    horas_trabalhadas_min: int = 0
    horas_extras_min: int = 0
    horas_negativas_min: int = 0
    saldo_final_min: int = 0
    quantidade_pendencias: int = 0


@dataclass
class ResultadoProcessamento:
    """
    Resultado consolidado de `calculadora.processar_todos()` (Cap. 6) —
    pronto para alimentar Relatórios, Dashboard, Histórico e
    Exportação. Em memória, é transitório; quando embrulhado numa
    `Competencia` (abaixo) e passado para `competencias.salvar_competencia()`,
    passa a ser persistido — mas nenhuma dessas duas classes recalcula
    nada, é sempre o que o Motor já produziu.
    """

    funcionarios_processados: list[Funcionario] = field(default_factory=list)
    pendencias: list[Pendencia] = field(default_factory=list)
    resumos_mensais: list[ResumoMensalFuncionario] = field(default_factory=list)
    estatisticas: dict[str, int] = field(default_factory=dict)


# ---------------------------------------------------------------------------
# Competência (gerenciamento de múltiplas competências)
#
# Uma Competência é o estado de trabalho completo de um mês/ano
# processado: os mesmos objetos que `calculadora.processar_todos()` já
# produziu, mais status e alguns metadados de importação — nada
# recalculado aqui. Persistida por `competencias.py`, um arquivo por
# competência, para que fechar o sistema no meio das pendências nunca
# perca nada (Cap. novo — ver ESPECIFICACAO.md).
# ---------------------------------------------------------------------------

@dataclass
class Competencia:
    """
    Uma competência (mês/ano) importada e processada, com estado
    independente de qualquer outra. `resultado` é o mesmo
    `ResultadoProcessamento` que a Tela de Pendências e a Tela de
    Relatórios já consomem hoje — nada muda na forma como é lido,
    só passa a vir de `competencias.carregar_competencia()` além de
    vir direto do Motor.
    """

    mes: int
    ano: int
    status: StatusCompetencia
    data_importacao: str
    arquivo_original: str
    resultado: ResultadoProcessamento
    relatorio_gerado: bool = False


# ---------------------------------------------------------------------------
# Relatório (Cap. 11) — Sprint 5
#
# Estas dataclasses são consumidas exclusivamente por relatorio.py. Nenhuma
# delas recalcula nada do Motor (Cap. 6/18): são agregações/formatações do
# que `ResultadoProcessamento`/`ResumoMensalFuncionario`/`DiaTrabalho.resultado`
# já contêm — os campos que faltam nos objetos do Motor para montar o
# relatório (ex.: Horas Previstas, o desdobramento de pendências
# resolvidas/existentes) são somas/contagens sobre valores já calculados,
# nunca uma nova regra de negócio.
# ---------------------------------------------------------------------------

@dataclass
class ResumoIndividualRelatorio:
    """Resumo de um funcionário para o Relatório Individual (Cap. 11.8)."""

    funcionario_id: str
    nome: str
    cargo: str
    setor_nome: str
    turno_nome: str
    horas_previstas_min: int = 0
    horas_trabalhadas_min: int = 0
    horas_extras_min: int = 0
    horas_negativas_min: int = 0
    saldo_final_min: int = 0
    quantidade_pendencias_resolvidas: int = 0
    quantidade_pendencias_existentes: int = 0


@dataclass
class ResumoGeralCompetencia:
    """
    Resumo geral da competência (Cap. 11.9) — agregação sobre todos
    os funcionários processados.
    """

    competencia_texto: str
    funcionarios_processados: int = 0
    funcionarios_com_pendencia: int = 0
    total_pendencias: int = 0
    horas_previstas_min: int = 0
    horas_trabalhadas_min: int = 0
    horas_extras_min: int = 0
    horas_negativas_min: int = 0
    saldo_geral_min: int = 0


@dataclass
class EstatisticasCompetencia:
    """Estatísticas da competência (Cap. 11.10)."""

    funcionarios_ativos: int = 0
    funcionarios_processados: int = 0
    funcionarios_sem_batidas: int = 0
    pendencias_por_tipo: dict[TipoPendencia, int] = field(default_factory=dict)
    distribuicao_justificativas: dict[str, int] = field(default_factory=dict)
    total_dias_processados: int = 0


@dataclass
class DadosRelatorio:
    """
    Tudo que um exportador (Cap. 11.12) precisa para montar o
    relatório — já pronto a partir do Motor (Cap. 6) e da Config
    (Cap. 13), sem nenhum cálculo novo. Transitório, não persistido.
    """

    resultado: "ResultadoProcessamento"
    resumo_geral: ResumoGeralCompetencia
    estatisticas: EstatisticasCompetencia
    nome_empresa: str
    logo_caminho: str
    competencia_texto: str
    arquivo_original: str
    data_processamento: str
    hora_processamento: str
    setores: list["Setor"] = field(default_factory=list)
    turnos: list[Turno] = field(default_factory=list)


# ---------------------------------------------------------------------------
# Histórico (Cap. 12.6/14) — Sprint 6
#
# Construídas só a partir do que já está gravado em disco (pastas
# Ano/Mês e o conteúdo já exportado da aba "Informações do
# Processamento" de cada relatório) — nenhuma competência já fechada é
# recalculada para montar estas estruturas.
# ---------------------------------------------------------------------------

@dataclass
class ArquivoHistorico:
    """Um arquivo `.xlsx` já exportado dentro de uma competência (Cap. 12.6/14)."""

    caminho: Path
    nome: str
    tamanho_bytes: int
    modificado_em: datetime


@dataclass
class CompetenciaHistorico:
    """Uma competência (Ano/Mês) já processada, encontrada na pasta de Histórico (Cap. 12.6/14)."""

    ano: int
    mes: int
    competencia_texto: str
    pasta: Path
    arquivos: list[ArquivoHistorico] = field(default_factory=list)
    nome_empresa: str = ""
    quantidade_funcionarios: str = "—"
    quantidade_pendencias: str = "—"
    data_processamento: str = "—"
    hora_processamento: str = "—"
