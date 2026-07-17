"""
constantes.py
-------------
Constantes e enumerações centrais do sistema.

Centraliza todos os valores fixos (versão, textos, tipos de pendência,
justificativas, status, dias da semana) para evitar "strings mágicas"
espalhadas pelo código. Nenhum outro módulo deve redefinir esses valores.
"""

from __future__ import annotations

from enum import Enum


# ---------------------------------------------------------------------------
# Identificação do sistema
# ---------------------------------------------------------------------------

APP_NOME: str = "QualiPonto"
APP_NOME_CURTO: str = "Sistema de Controle de Jornada e Horas Extras"
VERSAO: str = "1.1.0"
DESENVOLVEDOR: str = "Nathan Adrian"


# ---------------------------------------------------------------------------
# Dias da semana (índice do date.weekday(): 0=segunda ... 6=domingo)
# ---------------------------------------------------------------------------

DIAS_SEMANA: dict[int, str] = {
    0: "Segunda-feira",
    1: "Terça-feira",
    2: "Quarta-feira",
    3: "Quinta-feira",
    4: "Sexta-feira",
    5: "Sábado",
    6: "Domingo",
}


def nome_dia_semana(indice: int) -> str:
    """Retorna o nome do dia da semana a partir do índice de date.weekday()."""
    return DIAS_SEMANA.get(indice, "")


# ---------------------------------------------------------------------------
# Status do funcionário (Cap. 5.8 / 12.4)
# ---------------------------------------------------------------------------

class StatusFuncionario(str, Enum):
    ATIVO = "Ativo"
    INATIVO = "Inativo"


# ---------------------------------------------------------------------------
# Tipos de pendência (Cap. 7 / 9.2 / 11 - Aba 3)
# ---------------------------------------------------------------------------

class TipoPendencia(str, Enum):
    SEM_BATIDAS = "Nenhuma batida registrada"
    UMA_BATIDA = "Apenas uma batida"
    DUAS_BATIDAS = "Apenas duas batidas"
    TRES_BATIDAS = "Apenas três batidas"
    MAIS_DE_QUATRO = "Mais de quatro batidas"
    HORARIO_INCONSISTENTE = "Horário inconsistente"
    TURNO_NAO_DEFINIDO = "Turno não definido"


# ---------------------------------------------------------------------------
# Justificativas disponíveis (Cap. 9.6)
# ---------------------------------------------------------------------------

class Justificativa(str, Enum):
    FALTA = "Falta"
    FALTA_JUSTIFICADA = "Falta Justificada"
    FERIAS = "Férias"
    FOLGA = "Folga"
    LICENCA = "Licença"
    AFASTAMENTO = "Afastamento"
    ATESTADO_MEDICO = "Atestado Médico"
    CONSULTA_MEDICA = "Consulta Médica"
    SERVICO_EXTERNO = "Serviço Externo"
    TREINAMENTO = "Treinamento"
    DESLIGAMENTO = "Desligamento"
    ESQUECEU_BATER = "Esqueceu de bater"
    PONTO_NAO_REGISTROU = "Ponto não registrou"
    OUTRO = "Outro"


# ---------------------------------------------------------------------------
# Justificativas que eliminam a Hora Negativa do dia (Cap. 9.7) — lista
# central e explícita: só uma justificativa presente aqui zera a hora
# negativa; qualquer outra (ou nenhuma) mantém a hora negativa normalmente.
# Futuras inclusões só precisam adicionar o valor aqui, sem tocar no motor
# de cálculo.
# ---------------------------------------------------------------------------

JUSTIFICATIVAS_QUE_ELIMINAM_HORA_NEGATIVA: frozenset[Justificativa] = frozenset({
    Justificativa.ATESTADO_MEDICO,
    Justificativa.FERIAS,
    Justificativa.FOLGA,
    Justificativa.LICENCA,
})


# ---------------------------------------------------------------------------
# Situação diária (resultado do cálculo por dia)
# ---------------------------------------------------------------------------

class Situacao(str, Enum):
    NORMAL = "Normal"
    HORA_EXTRA = "Hora Extra"
    HORA_NEGATIVA = "Hora Negativa"
    PENDENCIA = "Pendência"
    SEM_REGISTRO = "Sem Registro"


# ---------------------------------------------------------------------------
# Situação da sugestão de turno no Painel de Revisão (Cap. 5.2 / 5.4)
# ---------------------------------------------------------------------------

class SituacaoSugestao(str, Enum):
    CONFIRMADO = "✓ Confirmado"
    REVISAR = "⚠ Revisar"


# ---------------------------------------------------------------------------
# Status da Competência (gerenciamento de múltiplas competências)
# ---------------------------------------------------------------------------

class StatusCompetencia(str, Enum):
    """
    Status de uma Competência persistida (`competencias.py`). Só 4 valores
    têm transição automática no fluxo síncrono atual — `PENDENCIAS_ABERTAS`
    → `EM_ANDAMENTO` → `PRONTA_PARA_RELATORIO` → `RELATORIO_GERADO`, sempre
    reavaliados por `competencias.avaliar_status()`. `ARQUIVADA` só muda por
    ação manual do usuário. `IMPORTADA` fica reservada: a Competência só é
    criada depois que o Motor de Cálculo já rodou (Cap. 6), então esse
    estado nunca é alcançado automaticamente hoje — existe para documentar
    a lista completa pedida e para um futuro fluxo assíncrono, se algum dia
    a leitura/cálculo deixarem de ser síncronos.
    """

    IMPORTADA = "Importada"
    EM_ANDAMENTO = "Em andamento"
    PENDENCIAS_ABERTAS = "Pendências abertas"
    PRONTA_PARA_RELATORIO = "Pronta para relatório"
    RELATORIO_GERADO = "Relatório gerado"
    ARQUIVADA = "Arquivada"


# ---------------------------------------------------------------------------
# Grafia amigável de Setores conhecidos (Cap. 5.17) — usada para apresentar
# de forma padronizada um Setor criado automaticamente durante a
# importação, quando o "Dep." da planilha vier todo em maiúsculas,
# minúsculas ou sem acentuação. Chave: nome já normalizado (sem acento,
# minúsculo, espaços colapsados — ver modelos.normalizar_texto).
# ---------------------------------------------------------------------------

GRAFIAS_SETOR_PADRAO: dict[str, str] = {
    "producao": "Produção",
    "logistica": "Logística",
    "motoristas": "Motoristas",
    "adm": "ADM",
    "rh": "RH",
}


# ---------------------------------------------------------------------------
# Formatos de arquivo aceitos na leitura da planilha (Cap. 3.1)
# ---------------------------------------------------------------------------

EXTENSOES_PLANILHA: tuple[str, ...] = (".xls", ".xlsx")

# Formatos de imagem aceitos para a logo (Cap. 4.3)
EXTENSOES_IMAGEM: tuple[str, ...] = (".png", ".jpg", ".jpeg", ".bmp", ".webp")


# ---------------------------------------------------------------------------
# Nomes dos meses em português (para montar competência e nomes de pastas)
# ---------------------------------------------------------------------------

MESES: dict[int, str] = {
    1: "Janeiro",
    2: "Fevereiro",
    3: "Março",
    4: "Abril",
    5: "Maio",
    6: "Junho",
    7: "Julho",
    8: "Agosto",
    9: "Setembro",
    10: "Outubro",
    11: "Novembro",
    12: "Dezembro",
}


def nome_mes(numero: int) -> str:
    """Retorna o nome do mês em português a partir do número (1-12)."""
    return MESES.get(numero, "")


# ---------------------------------------------------------------------------
# Formatação de minutos para exibição (Cap. 6) — único lugar do sistema que
# converte minutos inteiros (usados em todo o motor de cálculo) para o
# formato "XhYY" exibido na interface e nos relatórios. Trata corretamente
# valores negativos (ex.: -35 -> "-0h35"), diferente de um divmod ingênuo.
# ---------------------------------------------------------------------------

def formatar_minutos(minutos: int) -> str:
    """
    Formata minutos (inteiros, podendo ser negativos) como "XhYY"
    (ex.: 480 -> "8h00", -35 -> "-0h35").
    """
    sinal = "-" if minutos < 0 else ""
    horas, resto = divmod(abs(minutos), 60)
    return f"{sinal}{horas}h{resto:02d}"
