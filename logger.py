"""
logger.py
---------
Sistema de logs central (Cap. 15 da especificação).

Registra todos os processamentos e erros em Logs/processamento.log.
Mantido dependência-livre (resolve o próprio caminho a partir de __file__)
para evitar importações circulares com config.py.

Uso:
    from logger import get_logger
    log = get_logger()
    log.info("Sistema iniciado")
"""

from __future__ import annotations

import logging
import sys
from pathlib import Path

# Diretório base do projeto (pasta onde este arquivo está). Em um
# executável empacotado (PyInstaller), __file__ apontaria para a pasta
# temporária de extração — descartada a cada execução — em vez da pasta
# real do .exe; mesma lógica de config.py, duplicada aqui de propósito
# para este módulo continuar dependência-livre.
BASE_DIR: Path = (
    Path(sys.executable).resolve().parent if getattr(sys, "frozen", False)
    else Path(__file__).resolve().parent
)
LOGS_DIR: Path = BASE_DIR / "Logs"
ARQUIVO_LOG: Path = LOGS_DIR / "processamento.log"

_LOGGER_NOME = "qualimix"


def get_logger() -> logging.Logger:
    """
    Retorna o logger central do sistema, configurando-o na primeira chamada.

    Escreve em arquivo (Logs/processamento.log) e também no console, com
    data, hora e nível de cada evento.
    """
    logger = logging.getLogger(_LOGGER_NOME)

    if logger.handlers:
        return logger

    logger.setLevel(logging.INFO)

    # Garante a pasta de logs
    LOGS_DIR.mkdir(parents=True, exist_ok=True)

    formato = logging.Formatter(
        fmt="%(asctime)s | %(levelname)-7s | %(message)s",
        datefmt="%d/%m/%Y %H:%M:%S",
    )

    # Handler de arquivo (append, UTF-8)
    handler_arquivo = logging.FileHandler(ARQUIVO_LOG, encoding="utf-8")
    handler_arquivo.setFormatter(formato)
    logger.addHandler(handler_arquivo)

    # Handler de console (útil durante o desenvolvimento)
    handler_console = logging.StreamHandler()
    handler_console.setFormatter(formato)
    logger.addHandler(handler_console)

    logger.propagate = False

    return logger
