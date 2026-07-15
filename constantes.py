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

APP_NOME: str = "Calculadora de Horas Extras Qualimix"
APP_NOME_CURTO: str = "Calculadora de Horas Extras"
VERSAO: str = "1.0.0"
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
    FUNCIONARIO_NOVO = "Funcionário novo"
    SEM_BATIDAS = "Nenhuma batida registrada"
    UMA_BATIDA = "Apenas uma batida"
    DUAS_BATIDAS = "Apenas duas batidas"
    TRES_BATIDAS = "Apenas três batidas"
    MAIS_DE_QUATRO = "Mais de quatro batidas"
    HORARIO_INCONSISTENTE = "Horário inconsistente"


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
# Situação diária (resultado do cálculo por dia)
# ---------------------------------------------------------------------------

class Situacao(str, Enum):
    NORMAL = "Normal"
    HORA_EXTRA = "Hora Extra"
    HORA_NEGATIVA = "Hora Negativa"
    PENDENCIA = "Pendência"
    SEM_REGISTRO = "Sem Registro"


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
