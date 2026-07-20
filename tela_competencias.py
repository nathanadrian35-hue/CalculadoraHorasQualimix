"""
tela_competencias.py
---------------------
Tela Competências (gerenciamento de múltiplas competências).

Lista TODAS as competências persistidas (`competencias.listar()`) — cada
importação de planilha cria uma competência independente, totalmente
persistida (funcionários, dias, pendências, justificativas, status) logo
após o Motor de Cálculo processar o lote (Cap. 6, `tela_principal.py`).
Fechar o sistema no meio das pendências nunca perde nada: reabrir esta
tela e clicar "Abrir" retoma o trabalho exatamente de onde parou (mesma
decisão de destino de `App.iniciar_tela_pendencias()` — Pendências se
houver pendência em aberto, Relatórios caso contrário).

Nenhuma competência é excluída por esta tela — "Arquivar" só muda o
status (`StatusCompetencia.ARQUIVADA`); a competência continua acessível
normalmente pela Tela de Relatórios, sem ação de "Desarquivar" nesta
versão (decisão confirmada com o usuário).
"""

from __future__ import annotations

import functools
from tkinter import messagebox

import customtkinter as ctk

import competencias
from config import Config
from constantes import StatusCompetencia, StatusSimplificado, nome_mes
from logger import get_logger
from modelos import Competencia

log = get_logger()

_CORES_STATUS: dict[StatusCompetencia, tuple[str, str]] = {
    StatusCompetencia.IMPORTADA: ("gray50", "gray50"),
    StatusCompetencia.EM_ANDAMENTO: ("#a04000", "#f39c12"),
    StatusCompetencia.PENDENCIAS_ABERTAS: ("#c0392b", "#e74c3c"),
    StatusCompetencia.PRONTA_PARA_RELATORIO: ("#1f618d", "#3498db"),
    StatusCompetencia.RELATORIO_GERADO: ("#1e8449", "#2ecc71"),
    StatusCompetencia.ARQUIVADA: ("gray50", "gray50"),
}

_CORES_SIMPLIFICADO: dict[StatusSimplificado, tuple[str, str]] = {
    StatusSimplificado.EM_ANDAMENTO: ("#1e8449", "#2ecc71"),
    StatusSimplificado.AGUARDANDO_PENDENCIAS: ("#a04000", "#f39c12"),
    StatusSimplificado.FECHADA: ("#c0392b", "#e74c3c"),
}


# ---------------------------------------------------------------------------
# Card de uma competência
# ---------------------------------------------------------------------------

class _CardCompetencia(ctk.CTkFrame):
    """
    Card de uma competência (mês/ano) persistida: status detalhado
    (badge colorido, mesmo padrão de Ativo/Inativo já usado em
    tela_setores.py/tela_funcionarios.py) + selo simplificado de 3
    estados 🟢/🟡/🔴 (Etapa 7, v2.0, `competencias.status_simplificado`),
    contadores de funcionários/pendências (abertas x resolvidas) e de
    importações recebidas, indicação de relatório já gerado, e os
    botões "Abrir" (retomar trabalho), "Fechar"/"Reabrir" (Etapa 7,
    v2.0 — competência fechada exige confirmação extra para ser
    alterada por uma nova importação), "Histórico" (Etapas 6/13, v2.0
    — importações e auditoria) e "Arquivar".
    """

    def __init__(self, master, competencia: Competencia) -> None:
        super().__init__(master, corner_radius=10, border_width=1)
        self.competencia = competencia

        self.grid_columnconfigure(0, weight=1)

        cabecalho = ctk.CTkFrame(self, fg_color="transparent")
        cabecalho.grid(row=0, column=0, sticky="ew", padx=15, pady=(12, 5))
        cabecalho.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(
            cabecalho, text=f"{nome_mes(competencia.mes)}/{competencia.ano}",
            font=ctk.CTkFont(size=16, weight="bold"), anchor="w",
        ).grid(row=0, column=0, sticky="w")

        cor = _CORES_STATUS.get(competencia.status, ("gray50", "gray50"))
        ctk.CTkLabel(
            cabecalho, text=competencia.status.value, text_color=cor, width=150,
            font=ctk.CTkFont(weight="bold"), anchor="w",
        ).grid(row=0, column=1, padx=(0, 10))

        selo = competencias.status_simplificado(competencia)
        cor_selo = _CORES_SIMPLIFICADO.get(selo, ("gray50", "gray50"))
        ctk.CTkLabel(
            cabecalho, text=selo.value, text_color=cor_selo, width=170,
            font=ctk.CTkFont(weight="bold"), anchor="w",
        ).grid(row=0, column=2, padx=(0, 10))

        self._botao_fechar = ctk.CTkButton(
            cabecalho, text=("Reabrir" if competencia.fechada else "Fechar"),
            width=90, fg_color="transparent", border_width=1,
        )
        self._botao_fechar.grid(row=0, column=3, padx=(0, 10))

        self._botao_historico = ctk.CTkButton(
            cabecalho, text="Histórico", width=90, fg_color="transparent", border_width=1,
        )
        self._botao_historico.grid(row=0, column=4, padx=(0, 10))

        self._botao_arquivar = ctk.CTkButton(
            cabecalho, text="Arquivar", width=100, fg_color="transparent", border_width=1,
        )
        self._botao_arquivar.grid(row=0, column=5, padx=(0, 10))
        if competencia.status == StatusCompetencia.ARQUIVADA:
            self._botao_arquivar.configure(state="disabled")

        self._botao_abrir = ctk.CTkButton(cabecalho, text="Abrir", width=100)
        self._botao_abrir.grid(row=0, column=6)

        total_pendencias = len(competencia.resultado.pendencias)
        abertas = sum(1 for p in competencia.resultado.pendencias if not p.resolvida)
        resolvidas = total_pendencias - abertas
        info = (
            f"Data da importação: {competencia.data_importacao}    "
            f"Funcionários: {len(competencia.resultado.funcionarios_processados)}    "
            f"Importações: {competencia.quantidade_importacoes}    "
            f"Pendências: {total_pendencias} "
            f"({resolvidas} resolvida(s), {abertas} em aberto)    "
            f"Relatório gerado: {'Sim' if competencia.relatorio_gerado else 'Não'}"
        )
        ctk.CTkLabel(
            self, text=info, anchor="w", justify="left", wraplength=900,
            text_color=("gray60", "gray60"), font=ctk.CTkFont(size=12),
        ).grid(row=1, column=0, sticky="w", padx=15, pady=(0, 12))

    def definir_comando_abrir(self, comando) -> None:
        self._botao_abrir.configure(command=comando)

    def definir_comando_arquivar(self, comando) -> None:
        self._botao_arquivar.configure(command=comando)

    def definir_comando_fechar(self, comando) -> None:
        self._botao_fechar.configure(command=comando)

    def definir_comando_historico(self, comando) -> None:
        self._botao_historico.configure(command=comando)


# ---------------------------------------------------------------------------
# Tela Competências
# ---------------------------------------------------------------------------

class TelaCompetencias(ctk.CTkFrame):
    """Tela Competências — gerenciamento de múltiplas competências persistidas."""

    def __init__(self, master, controlador, config: Config) -> None:
        super().__init__(master, corner_radius=0)

        self.controlador = controlador
        self.config_app = config
        self._competencias: list[Competencia] = []
        self._cards: list[_CardCompetencia] = []

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
            cabecalho, text="Competências",
            font=ctk.CTkFont(size=20, weight="bold"),
        ).grid(row=0, column=1, sticky="w", padx=10)

    def _montar_lista(self) -> None:
        self._scroll = ctk.CTkScrollableFrame(self, fg_color="transparent")
        self._scroll.grid(row=1, column=0, sticky="nsew", padx=30, pady=15)

        self._rotulo_vazio = ctk.CTkLabel(
            self._scroll, text="Nenhuma competência importada ainda.",
            text_color=("gray60", "gray60"),
        )

    # -- Ciclo de vida ---------------------------------------------------------

    def ao_exibir(self) -> None:
        """Hook padrão (Sprint 1): recarrega a lista sempre que a tela é exibida."""
        self._carregar()

    def _carregar(self) -> None:
        self._competencias = competencias.listar()
        self._renderizar()

    # -- Renderização -----------------------------------------------------------

    def _renderizar(self) -> None:
        for card in self._cards:
            card.destroy()
        self._cards = []
        self._rotulo_vazio.pack_forget()

        if not self._competencias:
            self._rotulo_vazio.pack(pady=30)
            return

        for competencia in self._competencias:
            card = _CardCompetencia(self._scroll, competencia)
            card.definir_comando_abrir(functools.partial(self._abrir, competencia))
            card.definir_comando_arquivar(functools.partial(self._arquivar, competencia))
            card.definir_comando_fechar(functools.partial(self._alternar_fechamento, competencia))
            card.definir_comando_historico(functools.partial(self._abrir_historico, competencia))
            card.pack(fill="x", pady=6)
            self._cards.append(card)

    # -- Ações --------------------------------------------------------------------

    def _abrir(self, competencia: Competencia) -> None:
        """Retomar trabalho: mesma decisão de destino de `App.iniciar_tela_pendencias()`."""
        self.controlador.abrir_competencia(competencia)

    def _arquivar(self, competencia: Competencia) -> None:
        """
        Arquiva a competência mediante confirmação — sem ação de
        "Desarquivar" nesta versão (decisão confirmada com o usuário).
        A competência continua aparecendo normalmente na Tela de
        Relatórios, podendo gerar relatório novamente a qualquer
        momento.
        """
        confirmar = messagebox.askyesno(
            "Arquivar competência",
            f"Arquivar {nome_mes(competencia.mes)}/{competencia.ano}?\n\n"
            "A competência continuará disponível na Tela de Relatórios, mas "
            "não há como desarquivá-la nesta versão.",
        )
        if not confirmar:
            return

        competencia.status = StatusCompetencia.ARQUIVADA
        competencias.salvar_competencia(competencia)
        self.controlador.definir_status(
            f"{nome_mes(competencia.mes)}/{competencia.ano} arquivada.")
        self._carregar()

    def _alternar_fechamento(self, competencia: Competencia) -> None:
        """
        Fecha ou reabre a competência (Etapa 7, v2.0). Fechar exige
        confirmação porque, a partir daí, uma nova importação para o
        mesmo mês/ano só é aceita mediante confirmação extra em
        `tela_principal.py`; reabrir também é confirmado, já que
        remove essa proteção.
        """
        if competencia.fechada:
            confirmar = messagebox.askyesno(
                "Reabrir competência",
                f"Reabrir {nome_mes(competencia.mes)}/{competencia.ano}?\n\n"
                "A competência voltará a aceitar novas importações e correções "
                "sem confirmação extra.",
            )
            if not confirmar:
                return
            competencias.reabrir_competencia(competencia)
            mensagem = f"{nome_mes(competencia.mes)}/{competencia.ano} reaberta."
        else:
            confirmar = messagebox.askyesno(
                "Fechar competência",
                f"Fechar {nome_mes(competencia.mes)}/{competencia.ano}?\n\n"
                "Competências fechadas continuam disponíveis para relatório, "
                "mas passam a exigir confirmação extra antes de aceitar uma "
                "nova importação.",
            )
            if not confirmar:
                return
            competencias.fechar_competencia(competencia)
            mensagem = f"{nome_mes(competencia.mes)}/{competencia.ano} fechada."

        self.controlador.definir_status(mensagem)
        self._carregar()

    def _abrir_historico(self, competencia: Competencia) -> None:
        """
        Histórico de importações (Etapa 6) e auditoria (Etapa 13) da
        competência, v2.0 — leitura simples, sem ação nenhuma além de
        fechar a janela.
        """
        janela = ctk.CTkToplevel(self)
        janela.title(f"Histórico — {nome_mes(competencia.mes)}/{competencia.ano}")
        janela.geometry("720x480")
        janela.transient(self.winfo_toplevel())

        texto = ctk.CTkTextbox(janela, font=ctk.CTkFont(family="Consolas", size=12))
        texto.pack(fill="both", expand=True, padx=15, pady=15)

        linhas = ["IMPORTAÇÕES", "-" * 70]
        if competencia.historico_importacoes:
            for registro in competencia.historico_importacoes:
                linhas.append(
                    f"{registro.data_hora}  usuário: {registro.usuario}  "
                    f"arquivo: {registro.arquivo_original}"
                )
                linhas.append(
                    f"    registros no arquivo: {registro.quantidade_registros}    "
                    f"adicionados: {registro.registros_adicionados}    "
                    f"alterados: {registro.registros_alterados}"
                )
        else:
            linhas.append("Nenhum registro de importação.")

        linhas += ["", "AUDITORIA", "-" * 70]
        if competencia.auditoria:
            for evento in competencia.auditoria:
                linhas.append(
                    f"{evento.quando}  usuário: {evento.usuario}  {evento.o_que}: "
                    f"'{evento.valor_anterior}' → '{evento.valor_novo}'"
                )
        else:
            linhas.append("Nenhum registro de auditoria.")

        texto.insert("1.0", "\n".join(linhas))
        texto.configure(state="disabled")
