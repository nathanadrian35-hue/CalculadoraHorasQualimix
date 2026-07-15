"""
config.py
---------
Configurações e persistência local (Cap. 4 / 13 da especificação).

Responsabilidades:
    - Definir os caminhos padrão do projeto (pastas e arquivos JSON).
    - Criar automaticamente toda a estrutura de pastas.
    - Ler/salvar as configurações em arquivos JSON dentro de "dados/".
    - Fazer backup automático antes de sobrescrever qualquer arquivo.

Nenhuma informação de configuração fica gravada no código (Cap. 13.1):
tudo é lido/gravado em JSON. Os valores da jornada (usados pelo motor de
cálculo) ficam parametrizados aqui e serão definidos no Sprint 4.
"""

from __future__ import annotations

import json
import shutil
from copy import deepcopy
from datetime import datetime
from pathlib import Path
from typing import Any

from constantes import VERSAO
from logger import get_logger

log = get_logger()


# ---------------------------------------------------------------------------
# Caminhos do projeto
# ---------------------------------------------------------------------------

BASE_DIR: Path = Path(__file__).resolve().parent

DADOS_DIR: Path = BASE_DIR / "dados"
ASSETS_DIR: Path = BASE_DIR / "assets"
LOGO_DIR: Path = ASSETS_DIR / "logo"
ICONES_DIR: Path = ASSETS_DIR / "icones"
HISTORICO_DIR: Path = BASE_DIR / "Historico"
LOGS_DIR: Path = BASE_DIR / "Logs"
BACKUP_DIR: Path = BASE_DIR / "backup"

# Arquivos JSON
ARQ_EMPRESA: Path = DADOS_DIR / "empresa.json"
ARQ_CONFIGURACOES: Path = DADOS_DIR / "configuracoes.json"
ARQ_FUNCIONARIOS: Path = DADOS_DIR / "funcionarios.json"
ARQ_VERSAO: Path = DADOS_DIR / "versao.json"

# Todas as pastas que devem existir para o sistema funcionar
_PASTAS: tuple[Path, ...] = (
    DADOS_DIR,
    ASSETS_DIR,
    LOGO_DIR,
    ICONES_DIR,
    HISTORICO_DIR,
    LOGS_DIR,
    BACKUP_DIR,
)


# ---------------------------------------------------------------------------
# Valores padrão dos arquivos JSON
# ---------------------------------------------------------------------------

def _padrao_empresa() -> dict[str, Any]:
    return {"nome": "", "logo_caminho": ""}


def _padrao_configuracoes() -> dict[str, Any]:
    return {
        "turnos": [],  # [{"nome": "06:00 às 15:00", "entrada": "06:00", "saida": "15:00"}]
        "tolerancia_entrada": {"ativa": False, "minutos": 0},
        "tolerancia_almoco": {"ativa": False, "minutos": 0},
        "pasta_historico": str(HISTORICO_DIR),
        "tema": "dark",
        # Jornada parametrizável — regra numérica definida no Sprint 4 (não inventar).
        "jornada": {
            "minutos_diarios": None,       # jornada prevista dias úteis (minutos)
            "intervalo_almoco_min": None,  # intervalo padrão de almoço (minutos)
            "minutos_sabado": None,        # jornada prevista de sábado (minutos)
        },
        "primeira_execucao": True,
    }


def _padrao_funcionarios() -> dict[str, Any]:
    return {"funcionarios": []}


def _padrao_versao() -> dict[str, Any]:
    return {"versao": VERSAO, "ultima_atualizacao": ""}


# ---------------------------------------------------------------------------
# Estrutura de pastas
# ---------------------------------------------------------------------------

def garantir_estrutura() -> None:
    """Cria automaticamente todas as pastas necessárias (idempotente)."""
    for pasta in _PASTAS:
        pasta.mkdir(parents=True, exist_ok=True)
    log.info("Estrutura de pastas verificada/criada.")


# ---------------------------------------------------------------------------
# Leitura/escrita de JSON com backup
# ---------------------------------------------------------------------------

def _ler_json(caminho: Path, padrao: dict[str, Any]) -> dict[str, Any]:
    """
    Lê um JSON. Se o arquivo não existir, cria-o com os valores padrão.
    Se estiver corrompido, faz backup do arquivo e recria com o padrão.
    """
    if not caminho.exists():
        _escrever_json(caminho, padrao, com_backup=False)
        log.info("Arquivo criado com valores padrão: %s", caminho.name)
        return deepcopy(padrao)

    try:
        with caminho.open("r", encoding="utf-8") as arquivo:
            dados = json.load(arquivo)
        if not isinstance(dados, dict):
            raise ValueError(f"Conteúdo de {caminho.name} não é um objeto JSON.")
        # Completa chaves ausentes com o padrão (evita quebra ao evoluir o schema)
        return _mesclar_padrao(padrao, dados)
    except (json.JSONDecodeError, OSError, ValueError) as erro:
        log.error("Falha ao ler %s (%s). Recriando com padrão.", caminho.name, erro)
        _fazer_backup(caminho)
        _escrever_json(caminho, padrao, com_backup=False)
        return deepcopy(padrao)


def _escrever_json(caminho: Path, dados: dict[str, Any], com_backup: bool = True) -> None:
    """Grava um JSON de forma legível (UTF-8), com backup opcional prévio."""
    if com_backup and caminho.exists():
        _fazer_backup(caminho)

    caminho.parent.mkdir(parents=True, exist_ok=True)
    with caminho.open("w", encoding="utf-8") as arquivo:
        json.dump(dados, arquivo, ensure_ascii=False, indent=4)


def _fazer_backup(caminho: Path) -> None:
    """Copia o arquivo atual para backup/ com carimbo de data/hora."""
    try:
        BACKUP_DIR.mkdir(parents=True, exist_ok=True)
        carimbo = datetime.now().strftime("%Y%m%d_%H%M%S")
        destino = BACKUP_DIR / f"{caminho.stem}_{carimbo}{caminho.suffix}"
        shutil.copy2(caminho, destino)
        log.info("Backup criado: %s", destino.name)
    except OSError as erro:
        log.error("Não foi possível fazer backup de %s: %s", caminho.name, erro)


def _mesclar_padrao(padrao: dict[str, Any], dados: dict[str, Any]) -> dict[str, Any]:
    """Retorna 'dados' garantindo que todas as chaves de 'padrao' existam."""
    resultado = deepcopy(padrao)
    for chave, valor in dados.items():
        if isinstance(valor, dict) and isinstance(resultado.get(chave), dict):
            resultado[chave] = _mesclar_padrao(resultado[chave], valor)
        else:
            resultado[chave] = valor
    return resultado


# ---------------------------------------------------------------------------
# Gerenciador de configuração
# ---------------------------------------------------------------------------

class Config:
    """
    Ponto único de acesso às configurações persistidas.

    Instanciado uma vez em main.py e repassado às telas (injeção de
    dependência), evitando estado global espalhado. Cada 'salvar_*' grava
    o respectivo JSON, fazendo backup automático do arquivo anterior.
    """

    def __init__(self) -> None:
        self.empresa: dict[str, Any] = {}
        self.configuracoes: dict[str, Any] = {}
        self.funcionarios: dict[str, Any] = {}
        self.versao: dict[str, Any] = {}
        self.carregar_tudo()

    # -- Carregamento --------------------------------------------------------

    def carregar_tudo(self) -> None:
        """Carrega (ou cria) todos os arquivos JSON de configuração."""
        self.empresa = _ler_json(ARQ_EMPRESA, _padrao_empresa())
        self.configuracoes = _ler_json(ARQ_CONFIGURACOES, _padrao_configuracoes())
        self.funcionarios = _ler_json(ARQ_FUNCIONARIOS, _padrao_funcionarios())
        self.versao = _ler_json(ARQ_VERSAO, _padrao_versao())

        # Mantém a versão do sistema sempre atualizada no arquivo
        if self.versao.get("versao") != VERSAO:
            self.versao["versao"] = VERSAO
            self.salvar_versao()

    # -- Salvamento ----------------------------------------------------------

    def salvar_empresa(self) -> None:
        _escrever_json(ARQ_EMPRESA, self.empresa)
        log.info("Configuração da empresa salva.")

    def salvar_configuracoes(self) -> None:
        _escrever_json(ARQ_CONFIGURACOES, self.configuracoes)
        log.info("Configurações gerais salvas.")

    def salvar_funcionarios(self) -> None:
        _escrever_json(ARQ_FUNCIONARIOS, self.funcionarios)
        log.info("Cadastro de funcionários salvo.")

    def salvar_versao(self) -> None:
        self.versao["ultima_atualizacao"] = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
        _escrever_json(ARQ_VERSAO, self.versao)

    # -- Conveniências -------------------------------------------------------

    @property
    def primeira_execucao(self) -> bool:
        """True enquanto a configuração inicial guiada não foi concluída."""
        return bool(self.configuracoes.get("primeira_execucao", True))

    def concluir_primeira_execucao(self) -> None:
        self.configuracoes["primeira_execucao"] = False
        self.salvar_configuracoes()

    @property
    def nome_empresa(self) -> str:
        return self.empresa.get("nome", "") or ""

    @property
    def tema(self) -> str:
        return self.configuracoes.get("tema", "dark") or "dark"
