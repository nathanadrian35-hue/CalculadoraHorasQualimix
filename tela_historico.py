"""
tela_historico.py
-----------------
Tela de Histórico (Cap. 12.6).

Sprint 1: esqueleto navegável (título + botão Voltar). A navegação por
Ano/Mês e a abertura de relatórios serão implementadas no Sprint 6.
"""

from __future__ import annotations

import customtkinter as ctk

from config import Config


class TelaHistorico(ctk.CTkFrame):
    """Tela de histórico de relatórios (implementação no Sprint 6)."""

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
            cabecalho, text="Histórico",
            font=ctk.CTkFont(size=20, weight="bold"),
        ).grid(row=0, column=1, sticky="w", padx=10)

        ctk.CTkLabel(
            self,
            text="Módulo de Histórico — será implementado no Sprint 6.",
            font=ctk.CTkFont(size=14),
            text_color=("gray70", "gray70"),
        ).grid(row=1, column=0, sticky="n", pady=60)
