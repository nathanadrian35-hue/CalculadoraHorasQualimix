"""
main.py
-------
Ponto de entrada do sistema (inicialização).

Responsabilidade única: preparar o ambiente e subir a interface.
    1. Inicia o logger central.
    2. Cria automaticamente a estrutura de pastas.
    3. Carrega (ou cria) as configurações locais em JSON.
    4. Instancia e executa a janela principal.

Não contém lógica de interface, cálculo ou leitura de planilha.
"""

from __future__ import annotations

import sys

from config import Config, garantir_estrutura
from constantes import APP_NOME, VERSAO
from logger import get_logger


def iniciar() -> int:
    """Prepara o ambiente e executa a aplicação. Retorna o código de saída."""
    log = get_logger()
    log.info("=" * 60)
    log.info("Iniciando %s v%s", APP_NOME, VERSAO)

    try:
        # 1/2. Estrutura de pastas
        garantir_estrutura()

        # 3. Configurações locais
        config = Config()

        # 4. Interface (import tardio: só carrega CustomTkinter após o setup)
        from interface import App

        app = App(config)
        app.mainloop()

        log.info("Aplicação encerrada normalmente.")
        return 0

    except Exception as erro:  # captura qualquer falha de inicialização
        log.exception("Falha crítica na inicialização: %s", erro)
        return 1


if __name__ == "__main__":
    sys.exit(iniciar())
