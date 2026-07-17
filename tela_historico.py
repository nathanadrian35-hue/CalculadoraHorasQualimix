"""
tela_historico.py
-----------------
Tela de Histórico (Cap. 12.6/14) — Sprint 6.

Lista as competências já processadas (Ano/Mês), com as informações
básicas de cada uma lidas diretamente do relatório geral já exportado
(Cap. 11.4, Aba 4 — Informações do Processamento). Nenhuma competência
já fechada é recalculada aqui — `relatorio.listar_competencias()` só
lê o que já está gravado em disco.

Permite pesquisar por competência, abrir qualquer relatório (.xlsx) já
gerado diretamente no Excel, e excluir o histórico de uma competência
inteira mediante confirmação explícita.
"""

from __future__ import annotations

import functools
import os
from pathlib import Path
from tkinter import messagebox

import customtkinter as ctk

from config import Config
from logger import get_logger
from modelos import ArquivoHistorico, CompetenciaHistorico
from relatorio import excluir_historico, listar_competencias

log = get_logger()


def _tamanho_legivel(tamanho_bytes: int) -> str:
    """Formata um tamanho em bytes como "KB" (ou "B" para arquivos muito pequenos)."""
    if tamanho_bytes < 1024:
        return f"{tamanho_bytes} B"
    return f"{tamanho_bytes / 1024:.0f} KB"


# ---------------------------------------------------------------------------
# Linha de um arquivo dentro do card de uma competência
# ---------------------------------------------------------------------------

class _LinhaArquivoHistorico(ctk.CTkFrame):
    """Uma linha de arquivo já exportado: nome, tamanho e o botão "Abrir"."""

    def __init__(self, master, arquivo: ArquivoHistorico) -> None:
        super().__init__(master, fg_color="transparent")
        self.arquivo = arquivo

        self.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(self, text=arquivo.nome, anchor="w").grid(
            row=0, column=0, sticky="w", padx=(20, 10))
        ctk.CTkLabel(
            self, text=_tamanho_legivel(arquivo.tamanho_bytes), anchor="w", width=70,
            text_color=("gray60", "gray60"), font=ctk.CTkFont(size=12),
        ).grid(row=0, column=1, padx=(0, 10))
        ctk.CTkLabel(
            self, text=arquivo.modificado_em.strftime("%d/%m/%Y %H:%M"), anchor="w", width=120,
            text_color=("gray60", "gray60"), font=ctk.CTkFont(size=12),
        ).grid(row=0, column=2, padx=(0, 10))

        self._botao_abrir = ctk.CTkButton(self, text="Abrir", width=80)
        self._botao_abrir.grid(row=0, column=3, padx=(0, 10), pady=3)

    def definir_comando_abrir(self, comando) -> None:
        self._botao_abrir.configure(command=comando)


# ---------------------------------------------------------------------------
# Card de uma competência
# ---------------------------------------------------------------------------

class _CardCompetencia(ctk.CTkFrame):
    """
    Card de uma competência: informações básicas (lidas do relatório já
    exportado, nunca recalculadas), a lista de arquivos daquela
    competência e o botão "Excluir Histórico".
    """

    def __init__(self, master, competencia: CompetenciaHistorico) -> None:
        super().__init__(master, corner_radius=10, border_width=1)
        self.competencia = competencia
        self._linhas_arquivo: list[_LinhaArquivoHistorico] = []

        self.grid_columnconfigure(0, weight=1)

        cabecalho = ctk.CTkFrame(self, fg_color="transparent")
        cabecalho.grid(row=0, column=0, sticky="ew", padx=15, pady=(12, 5))
        cabecalho.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(
            cabecalho, text=competencia.competencia_texto,
            font=ctk.CTkFont(size=16, weight="bold"), anchor="w",
        ).grid(row=0, column=0, sticky="w")

        self._botao_excluir = ctk.CTkButton(
            cabecalho, text="Excluir Histórico", width=150,
            fg_color="#c0392b", hover_color="#992d22",
        )
        self._botao_excluir.grid(row=0, column=1, sticky="e")

        info = (
            f"Empresa: {competencia.nome_empresa or '—'}    "
            f"Funcionários processados: {competencia.quantidade_funcionarios}    "
            f"Pendências: {competencia.quantidade_pendencias}    "
            f"Processado em: {competencia.data_processamento} {competencia.hora_processamento}    "
            f"{len(competencia.arquivos)} relatório(s)"
        )
        ctk.CTkLabel(
            self, text=info, anchor="w", justify="left", wraplength=900,
            text_color=("gray60", "gray60"), font=ctk.CTkFont(size=12),
        ).grid(row=1, column=0, columnspan=2, sticky="w", padx=15, pady=(0, 10))

        frame_arquivos = ctk.CTkFrame(self, fg_color="transparent")
        frame_arquivos.grid(row=2, column=0, columnspan=2, sticky="ew", padx=5, pady=(0, 12))
        for arquivo in competencia.arquivos:
            linha = _LinhaArquivoHistorico(frame_arquivos, arquivo)
            linha.pack(fill="x", pady=2)
            self._linhas_arquivo.append(linha)

    def definir_comando_excluir(self, comando) -> None:
        self._botao_excluir.configure(command=comando)

    def linhas_arquivo(self) -> list[_LinhaArquivoHistorico]:
        return self._linhas_arquivo


# ---------------------------------------------------------------------------
# Tela de Histórico
# ---------------------------------------------------------------------------

class TelaHistorico(ctk.CTkFrame):
    """Tela de Histórico (Cap. 12.6/14)."""

    def __init__(self, master, controlador, config: Config) -> None:
        super().__init__(master, corner_radius=0)

        self.controlador = controlador
        self.config_app = config
        self._competencias: list[CompetenciaHistorico] = []
        self._cards: list[_CardCompetencia] = []

        self.grid_rowconfigure(2, weight=1)
        self.grid_columnconfigure(0, weight=1)

        self._montar_cabecalho()
        self._montar_pesquisa()
        self._montar_lista()

    # -- Construção da UI -----------------------------------------------------

    def _montar_cabecalho(self) -> None:
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

    def _montar_pesquisa(self) -> None:
        barra = ctk.CTkFrame(self, fg_color="transparent")
        barra.grid(row=1, column=0, sticky="ew", padx=30, pady=(15, 0))
        barra.grid_columnconfigure(0, weight=1)

        self._entry_pesquisa = ctk.CTkEntry(
            barra, placeholder_text="Pesquisar competência (ex.: Julho, 2026)...",
        )
        self._entry_pesquisa.grid(row=0, column=0, sticky="ew")
        self._entry_pesquisa.bind("<KeyRelease>", lambda evento: self._filtrar())

    def _montar_lista(self) -> None:
        self._scroll = ctk.CTkScrollableFrame(self, fg_color="transparent")
        self._scroll.grid(row=2, column=0, sticky="nsew", padx=30, pady=15)

        self._rotulo_vazio = ctk.CTkLabel(
            self._scroll, text="Nenhum histórico encontrado.",
            text_color=("gray60", "gray60"),
        )

    # -- Ciclo de vida ----------------------------------------------------------

    def ao_exibir(self) -> None:
        """Hook padrão (Sprint 1): recarrega a lista sempre que a tela é exibida."""
        self._carregar()

    def _carregar(self) -> None:
        self._competencias = listar_competencias(self.config_app)
        self._entry_pesquisa.delete(0, "end")
        self._renderizar(self._competencias)

    # -- Pesquisa (Cap. 12.6) ----------------------------------------------------

    def _filtrar(self) -> None:
        termo = self._entry_pesquisa.get().strip().casefold()
        if not termo:
            self._renderizar(self._competencias)
            return
        filtradas = [c for c in self._competencias if termo in c.competencia_texto.casefold()]
        self._renderizar(filtradas)

    # -- Renderização -------------------------------------------------------------

    def _renderizar(self, competencias: list[CompetenciaHistorico]) -> None:
        for card in self._cards:
            card.destroy()
        self._cards = []
        self._rotulo_vazio.pack_forget()

        if not competencias:
            self._rotulo_vazio.pack(pady=30)
            return

        for competencia in competencias:
            card = _CardCompetencia(self._scroll, competencia)
            for linha in card.linhas_arquivo():
                linha.definir_comando_abrir(
                    functools.partial(self._abrir_arquivo, linha.arquivo.caminho))
            card.definir_comando_excluir(functools.partial(self._excluir, competencia))
            card.pack(fill="x", pady=6)
            self._cards.append(card)

    # -- Ações --------------------------------------------------------------------

    def _abrir_arquivo(self, caminho: Path) -> None:
        """Abre o relatório diretamente no Excel (Cap. 12.6: "abrir diretamente pelo sistema")."""
        try:
            os.startfile(str(caminho))  # type: ignore[attr-defined]
            self.controlador.definir_status(f"Abrindo: {caminho.name}")
        except OSError as erro:
            log.error("Falha ao abrir relatório do histórico: %s", erro)
            messagebox.showerror(
                "Não foi possível abrir",
                f"Não foi possível abrir o arquivo automaticamente.\nCaminho: {caminho}",
            )

    def _excluir(self, competencia: CompetenciaHistorico) -> None:
        """Exclui todos os relatórios de uma competência, mediante confirmação (Cap. 12.6)."""
        confirmar = messagebox.askyesno(
            "Excluir histórico",
            f"Excluir TODOS os {len(competencia.arquivos)} relatório(s) de "
            f"{competencia.competencia_texto}?\n\nEsta ação não pode ser desfeita.",
        )
        if not confirmar:
            return

        try:
            excluir_historico(self.config_app, competencia)
        except (ValueError, OSError) as erro:
            log.error("Falha ao excluir histórico: %s", erro)
            messagebox.showerror("Não foi possível excluir", str(erro))
            return

        self.controlador.definir_status(f"Histórico de {competencia.competencia_texto} excluído.")
        self._carregar()
