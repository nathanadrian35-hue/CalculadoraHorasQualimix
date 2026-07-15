"""
modelos.py
----------
Estruturas de dados internas do sistema (Cap. 16 da especificação).

Estas dataclasses formam o "contrato" de comunicação entre os módulos:
o leitor produz Funcionario/DiaTrabalho/Batida, o motor de cálculo preenche
Resultado, e o relatório consome tudo. Nenhum módulo deve trafegar
dicionários soltos — sempre usar estes modelos.

Hierarquia:
    Empresa
      └── Funcionario
            └── DiaTrabalho
                  ├── Batida (lista)
                  └── Resultado
    Pendencia (transversal, ligada a um funcionário/dia)
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, time

from constantes import Situacao, StatusFuncionario, TipoPendencia


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

@dataclass
class Turno:
    """Um turno de trabalho cadastrado (ex.: 06:00 às 15:00)."""

    nome: str                       # rótulo exibido, ex.: "06:00 às 15:00"
    entrada: time | None = None     # horário previsto de entrada
    saida: time | None = None       # horário previsto de saída


# ---------------------------------------------------------------------------
# Funcionário
# ---------------------------------------------------------------------------

@dataclass
class Funcionario:
    """
    Funcionário identificado na planilha e persistido em funcionarios.json.

    O `id_usuario` e o `nome` vêm da planilha e NUNCA são editados
    manualmente (Cap. 12.4). Apenas turno e status podem ser alterados.
    """

    id_usuario: str
    nome: str
    turno: str = ""                                     # nome do turno escolhido
    status: StatusFuncionario = StatusFuncionario.ATIVO
    data_cadastro: str = ""                             # ISO (YYYY-MM-DD HH:MM:SS)
    ultima_atualizacao: str = ""                        # ISO
    ultima_competencia: str = ""                        # ex.: "Julho/2026"

    # Dados de processamento (preenchidos em memória, não persistidos no JSON)
    dias: list["DiaTrabalho"] = field(default_factory=list)


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
# Resultado do cálculo diário
# ---------------------------------------------------------------------------

@dataclass
class Resultado:
    """Resultado dos cálculos de um único dia (preenchido pela calculadora)."""

    horas_trabalhadas: float = 0.0   # em horas decimais
    horas_extras: float = 0.0
    horas_negativas: float = 0.0
    saldo: float = 0.0               # trabalhadas - jornada prevista
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
    resultado: Resultado = field(default_factory=Resultado)
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
