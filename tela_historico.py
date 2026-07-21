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

import os
from pathlib import Path
from tkinter import messagebox
from typing import Callable

import customtkinter as ctk

from componentes import BotaoExportar, ColunaOrdenavel, TabelaPadrao
from config import Config
from exportacao import caminho_exportacao
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

    def __init__(self, master, ao_abrir: Callable[[Path], None]) -> None:
        super().__init__(master, fg_color="transparent")
        self.arquivo: ArquivoHistorico | None = None
        self._ao_abrir = ao_abrir

        self.grid_columnconfigure(0, weight=1)

        self._rotulo_nome = ctk.CTkLabel(self, anchor="w")
        self._rotulo_nome.grid(row=0, column=0, sticky="w", padx=(20, 10))
        self._rotulo_tamanho = ctk.CTkLabel(
            self, anchor="w", width=70,
            text_color=("gray60", "gray60"), font=ctk.CTkFont(size=12),
        )
        self._rotulo_tamanho.grid(row=0, column=1, padx=(0, 10))
        self._rotulo_data = ctk.CTkLabel(
            self, anchor="w", width=120,
            text_color=("gray60", "gray60"), font=ctk.CTkFont(size=12),
        )
        self._rotulo_data.grid(row=0, column=2, padx=(0, 10))

        self._botao_abrir = ctk.CTkButton(
            self, text="Abrir", width=80, command=self._clicar_abrir)
        self._botao_abrir.grid(row=0, column=3, padx=(0, 10), pady=3)

    def vincular(self, arquivo: ArquivoHistorico) -> None:
        self.arquivo = arquivo
        self._rotulo_nome.configure(text=arquivo.nome)
        self._rotulo_tamanho.configure(text=_tamanho_legivel(arquivo.tamanho_bytes))
        self._rotulo_data.configure(text=arquivo.modificado_em.strftime("%d/%m/%Y %H:%M"))

    def _clicar_abrir(self) -> None:
        if self.arquivo is not None:
            self._ao_abrir(self.arquivo.caminho)


# ---------------------------------------------------------------------------
# Card de uma competência (linha reaproveitável do pool — Sprint 1, v2.1)
# ---------------------------------------------------------------------------

class _CardCompetencia(ctk.CTkFrame):
    """
    Card de uma competência: informações básicas (lidas do relatório já
    exportado, nunca recalculadas), a lista de arquivos daquela
    competência e o botão "Excluir Histórico". A sublista de arquivos
    varia de tamanho por competência, então é reconstruída a cada
    `vincular()` — só o card em si é reaproveitado pelo pool de
    `TabelaPadrao` (o que importa para desempenho é não recriar os
    cards a cada rolagem/pesquisa, não a sublista interna, tipicamente
    pequena).
    """

    def __init__(
        self, master,
        ao_abrir_arquivo: Callable[[Path], None],
        ao_excluir: Callable[[CompetenciaHistorico], None],
    ) -> None:
        super().__init__(master, corner_radius=10, border_width=1)
        self.competencia: CompetenciaHistorico | None = None
        self._ao_abrir_arquivo = ao_abrir_arquivo
        self._ao_excluir = ao_excluir
        self._linhas_arquivo: list[_LinhaArquivoHistorico] = []

        self.grid_columnconfigure(0, weight=1)

        cabecalho = ctk.CTkFrame(self, fg_color="transparent")
        cabecalho.grid(row=0, column=0, sticky="ew", padx=15, pady=(12, 5))
        cabecalho.grid_columnconfigure(0, weight=1)

        self._rotulo_titulo = ctk.CTkLabel(
            cabecalho, font=ctk.CTkFont(size=16, weight="bold"), anchor="w")
        self._rotulo_titulo.grid(row=0, column=0, sticky="w")

        self._botao_excluir = ctk.CTkButton(
            cabecalho, text="Excluir Histórico", width=150,
            fg_color="#c0392b", hover_color="#992d22", command=self._clicar_excluir,
        )
        self._botao_excluir.grid(row=0, column=1, sticky="e")

        self._rotulo_info = ctk.CTkLabel(
            self, anchor="w", justify="left", wraplength=900,
            text_color=("gray60", "gray60"), font=ctk.CTkFont(size=12),
        )
        self._rotulo_info.grid(row=1, column=0, columnspan=2, sticky="w", padx=15, pady=(0, 10))

        self._frame_arquivos = ctk.CTkFrame(self, fg_color="transparent")
        self._frame_arquivos.grid(row=2, column=0, columnspan=2, sticky="ew", padx=5, pady=(0, 12))

    def vincular(self, competencia: CompetenciaHistorico) -> None:
        self.competencia = competencia
        self._rotulo_titulo.configure(text=competencia.competencia_texto)
        self._rotulo_info.configure(text=(
            f"Empresa: {competencia.nome_empresa or '—'}    "
            f"Funcionários processados: {competencia.quantidade_funcionarios}    "
            f"Pendências: {competencia.quantidade_pendencias}    "
            f"Processado em: {competencia.data_processamento} {competencia.hora_processamento}    "
            f"{len(competencia.arquivos)} relatório(s)"
        ))

        for linha in self._linhas_arquivo:
            linha.destroy()
        self._linhas_arquivo = []
        for arquivo in competencia.arquivos:
            linha = _LinhaArquivoHistorico(self._frame_arquivos, ao_abrir=self._ao_abrir_arquivo)
            linha.vincular(arquivo)
            linha.pack(fill="x", pady=2)
            self._linhas_arquivo.append(linha)

    def _clicar_excluir(self) -> None:
        if self.competencia is not None:
            self._ao_excluir(self.competencia)


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

        self.grid_rowconfigure(1, weight=1)
        self.grid_columnconfigure(0, weight=1)

        self._montar_cabecalho()
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

        BotaoExportar(
            cabecalho, titulo="Histórico", colunas=["Competência", "Empresa", "Relatórios"],
            obter_registros=lambda: self._tabela.registros_filtrados(),
            montar_linha=lambda c: (
                c.competencia_texto, c.nome_empresa or "—", len(c.arquivos)),
            caminho_sugerido=lambda extensao: caminho_exportacao(
                self.config_app, "Historico", "Historico", extensao),
        ).grid(row=0, column=2, padx=15)

    def _montar_lista(self) -> None:
        self._tabela = TabelaPadrao(
            self,
            criar_linha=lambda m: _CardCompetencia(
                m, ao_abrir_arquivo=self._abrir_arquivo, ao_excluir=self._excluir),
            colunas=[
                ColunaOrdenavel("Competência", lambda c: (c.ano, c.mes)),
                ColunaOrdenavel("Pendências", lambda c: c.quantidade_pendencias),
            ],
            campos_pesquisa=[lambda c: c.competencia_texto, lambda c: c.nome_empresa],
            placeholder_pesquisa="Pesquisar competência (ex.: Julho, 2026)...",
            texto_vazio="Nenhum histórico encontrado.",
        )
        self._tabela.grid(row=1, column=0, sticky="nsew", padx=30, pady=15)

    # -- Ciclo de vida ----------------------------------------------------------

    def ao_exibir(self) -> None:
        """Hook padrão (Sprint 1): recarrega a lista sempre que a tela é exibida."""
        self._carregar()

    def _carregar(self) -> None:
        self._competencias = listar_competencias(self.config_app)
        self._tabela.definir_registros(self._competencias)

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
