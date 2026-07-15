"""
tela_sobre.py
-------------
Tela Sobre (Cap. 12.7).

Já funcional no Sprint 1, pois depende apenas de informações locais:
nome do sistema, versão, empresa, desenvolvedor, versão do Python e
data da última atualização (lida de versao.json).
"""

from __future__ import annotations

import platform

import customtkinter as ctk

from config import Config
from constantes import APP_NOME, DESENVOLVEDOR, VERSAO


class TelaSobre(ctk.CTkFrame):
    """Informações sobre o sistema."""

    def __init__(self, master, controlador, config: Config) -> None:
        super().__init__(master, corner_radius=0)

        self.controlador = controlador
        self.config_app = config

        self.grid_rowconfigure(1, weight=1)
        self.grid_columnconfigure(0, weight=1)

        cabecalho = ctk.CTkFrame(self, corner_radius=0, height=70)
        cabecalho.grid(row=0, column=0, sticky="ew")
        cabecalho.grid_columnconfigure(1, weight=1)

        ctk.CTkButton(
            cabecalho, text="← Voltar", width=90,
            command=lambda: self.controlador.mostrar_tela("principal"),
        ).grid(row=0, column=0, padx=15, pady=15)

        ctk.CTkLabel(
            cabecalho, text="Sobre",
            font=ctk.CTkFont(size=20, weight="bold"),
        ).grid(row=0, column=1, sticky="w", padx=10)

        self._corpo = ctk.CTkFrame(self, fg_color="transparent")
        self._corpo.grid(row=1, column=0, sticky="n", pady=40)
        self._preencher()

    def ao_exibir(self) -> None:
        """Recria as informações (empresa/atualização podem ter mudado)."""
        self._preencher()

    def _preencher(self) -> None:
        for widget in self._corpo.winfo_children():
            widget.destroy()

        info = [
            ("Sistema", APP_NOME),
            ("Versão", VERSAO),
            ("Empresa", self.config_app.nome_empresa or "—"),
            ("Desenvolvido por", DESENVOLVEDOR),
            ("Python", platform.python_version()),
            ("Última atualização", self.config_app.versao.get("ultima_atualizacao", "—") or "—"),
        ]

        for linha, (rotulo, valor) in enumerate(info):
            ctk.CTkLabel(
                self._corpo, text=f"{rotulo}:", anchor="e",
                font=ctk.CTkFont(size=14, weight="bold"), width=180,
            ).grid(row=linha, column=0, sticky="e", padx=(10, 15), pady=8)
            ctk.CTkLabel(
                self._corpo, text=valor, anchor="w",
                font=ctk.CTkFont(size=14), width=260,
            ).grid(row=linha, column=1, sticky="w", padx=10, pady=8)
