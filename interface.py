"""
interface.py
------------
Janela raiz da aplicação e roteamento entre telas (Cap. 12).

Responsabilidade única: montar a janela principal CustomTkinter (tema
escuro), instanciar as telas e alternar entre elas. NÃO realiza cálculos
nem leitura de planilha — apenas apresentação e navegação.

Cada tela é um CTkFrame que recebe (master, controlador, config). O
controlador é esta própria janela (App), que expõe:
    - mostrar_tela(nome): traz uma tela para frente;
    - definir_status(texto): atualiza a barra de status da tela principal.
"""

from __future__ import annotations

import customtkinter as ctk

from config import Config
from constantes import APP_NOME
from logger import get_logger
from tela_configuracoes import TelaConfiguracoes
from tela_funcionarios import TelaFuncionarios
from tela_historico import TelaHistorico
from tela_principal import TelaPrincipal
from tela_sobre import TelaSobre

log = get_logger()

# Aparência global (tema escuro conforme especificação)
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("dark-blue")


class App(ctk.CTk):
    """Janela principal do sistema — controladora da navegação."""

    LARGURA = 1000
    ALTURA = 640

    def __init__(self, config: Config) -> None:
        super().__init__()

        self.config_app = config

        self.title(APP_NOME)
        self.geometry(f"{self.LARGURA}x{self.ALTURA}")
        self.minsize(900, 600)
        self._centralizar()

        # Container único onde todas as telas são empilhadas
        self.container = ctk.CTkFrame(self, corner_radius=0)
        self.container.pack(fill="both", expand=True)
        self.container.grid_rowconfigure(0, weight=1)
        self.container.grid_columnconfigure(0, weight=1)

        # Instancia todas as telas uma única vez
        self._telas: dict[str, ctk.CTkFrame] = {}
        for nome, Classe in (
            ("principal", TelaPrincipal),
            ("configuracoes", TelaConfiguracoes),
            ("funcionarios", TelaFuncionarios),
            ("historico", TelaHistorico),
            ("sobre", TelaSobre),
        ):
            tela = Classe(self.container, controlador=self, config=config)
            tela.grid(row=0, column=0, sticky="nsew")
            self._telas[nome] = tela

        self.mostrar_tela("principal")
        log.info("Interface iniciada.")

    # -- Navegação -----------------------------------------------------------

    def mostrar_tela(self, nome: str) -> None:
        """Traz a tela indicada para frente e a atualiza, se aplicável."""
        tela = self._telas.get(nome)
        if tela is None:
            log.error("Tela inexistente solicitada: %s", nome)
            return

        # Se a tela souber se atualizar ao aparecer, faz isso
        if hasattr(tela, "ao_exibir"):
            tela.ao_exibir()

        tela.tkraise()

    def definir_status(self, texto: str) -> None:
        """Atualiza a barra de status (exibida na tela principal)."""
        principal = self._telas.get("principal")
        if principal is not None and hasattr(principal, "definir_status"):
            principal.definir_status(texto)

    # -- Utilidades ----------------------------------------------------------

    def _centralizar(self) -> None:
        """Centraliza a janela na tela."""
        self.update_idletasks()
        largura_tela = self.winfo_screenwidth()
        altura_tela = self.winfo_screenheight()
        pos_x = (largura_tela - self.LARGURA) // 2
        pos_y = (altura_tela - self.ALTURA) // 2
        self.geometry(f"{self.LARGURA}x{self.ALTURA}+{pos_x}+{pos_y}")
