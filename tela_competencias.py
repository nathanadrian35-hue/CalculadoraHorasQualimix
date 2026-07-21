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

import os
from tkinter import messagebox
from typing import Callable

import customtkinter as ctk

import competencias
from componentes import BotaoExportar, ColunaOrdenavel, TabelaPadrao
from config import Config
from constantes import StatusCompetencia, StatusSimplificado, nome_mes
from exportacao import caminho_exportacao, exportar_excel_simples
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

    def __init__(
        self, master,
        ao_abrir: Callable[[Competencia], None],
        ao_arquivar: Callable[[Competencia], None],
        ao_alternar_fechamento: Callable[[Competencia], None],
        ao_abrir_historico: Callable[[Competencia], None],
    ) -> None:
        super().__init__(master, corner_radius=10, border_width=1)
        self.competencia: Competencia | None = None
        self._ao_abrir = ao_abrir
        self._ao_arquivar = ao_arquivar
        self._ao_alternar_fechamento = ao_alternar_fechamento
        self._ao_abrir_historico = ao_abrir_historico

        self.grid_columnconfigure(0, weight=1)

        cabecalho = ctk.CTkFrame(self, fg_color="transparent")
        cabecalho.grid(row=0, column=0, sticky="ew", padx=15, pady=(12, 5))
        cabecalho.grid_columnconfigure(0, weight=1)

        self._rotulo_titulo = ctk.CTkLabel(
            cabecalho, font=ctk.CTkFont(size=16, weight="bold"), anchor="w")
        self._rotulo_titulo.grid(row=0, column=0, sticky="w")

        self._rotulo_status = ctk.CTkLabel(
            cabecalho, width=150, font=ctk.CTkFont(weight="bold"), anchor="w")
        self._rotulo_status.grid(row=0, column=1, padx=(0, 10))

        self._rotulo_selo = ctk.CTkLabel(
            cabecalho, width=170, font=ctk.CTkFont(weight="bold"), anchor="w")
        self._rotulo_selo.grid(row=0, column=2, padx=(0, 10))

        self._botao_fechar = ctk.CTkButton(
            cabecalho, width=90, fg_color="transparent", border_width=1,
            command=self._clicar_alternar_fechamento,
        )
        self._botao_fechar.grid(row=0, column=3, padx=(0, 10))

        self._botao_historico = ctk.CTkButton(
            cabecalho, text="Histórico", width=90, fg_color="transparent", border_width=1,
            command=self._clicar_historico,
        )
        self._botao_historico.grid(row=0, column=4, padx=(0, 10))

        self._botao_arquivar = ctk.CTkButton(
            cabecalho, text="Arquivar", width=100, fg_color="transparent", border_width=1,
            command=self._clicar_arquivar,
        )
        self._botao_arquivar.grid(row=0, column=5, padx=(0, 10))

        self._botao_abrir = ctk.CTkButton(
            cabecalho, text="Abrir", width=100, command=self._clicar_abrir)
        self._botao_abrir.grid(row=0, column=6)

        self._rotulo_info = ctk.CTkLabel(
            self, anchor="w", justify="left", wraplength=900,
            text_color=("gray60", "gray60"), font=ctk.CTkFont(size=12),
        )
        self._rotulo_info.grid(row=1, column=0, sticky="w", padx=15, pady=(0, 12))

    def vincular(self, competencia: Competencia) -> None:
        self.competencia = competencia

        self._rotulo_titulo.configure(text=f"{nome_mes(competencia.mes)}/{competencia.ano}")

        cor = _CORES_STATUS.get(competencia.status, ("gray50", "gray50"))
        self._rotulo_status.configure(text=competencia.status.value, text_color=cor)

        selo = competencias.status_simplificado(competencia)
        cor_selo = _CORES_SIMPLIFICADO.get(selo, ("gray50", "gray50"))
        self._rotulo_selo.configure(text=selo.value, text_color=cor_selo)

        self._botao_fechar.configure(text="Reabrir" if competencia.fechada else "Fechar")
        self._botao_arquivar.configure(
            state="disabled" if competencia.status == StatusCompetencia.ARQUIVADA else "normal")

        total_pendencias = len(competencia.resultado.pendencias)
        abertas = sum(1 for p in competencia.resultado.pendencias if not p.resolvida)
        resolvidas = total_pendencias - abertas
        self._rotulo_info.configure(text=(
            f"Data da importação: {competencia.data_importacao}    "
            f"Funcionários: {len(competencia.resultado.funcionarios_processados)}    "
            f"Importações: {competencia.quantidade_importacoes}    "
            f"Pendências: {total_pendencias} "
            f"({resolvidas} resolvida(s), {abertas} em aberto)    "
            f"Relatório gerado: {'Sim' if competencia.relatorio_gerado else 'Não'}"
        ))

    def _clicar_abrir(self) -> None:
        if self.competencia is not None:
            self._ao_abrir(self.competencia)

    def _clicar_arquivar(self) -> None:
        if self.competencia is not None:
            self._ao_arquivar(self.competencia)

    def _clicar_alternar_fechamento(self) -> None:
        if self.competencia is not None:
            self._ao_alternar_fechamento(self.competencia)

    def _clicar_historico(self) -> None:
        if self.competencia is not None:
            self._ao_abrir_historico(self.competencia)


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

        ctk.CTkButton(
            cabecalho, text="Imprimir", width=100, fg_color="transparent", border_width=1,
            command=self._imprimir,
        ).grid(row=0, column=2, padx=(0, 10))

        BotaoExportar(
            cabecalho, titulo="Competências", colunas=["Competência", "Status", "Pendências"],
            obter_registros=lambda: self._tabela.registros_filtrados(),
            montar_linha=lambda c: (
                f"{nome_mes(c.mes)}/{c.ano}", c.status.value,
                sum(1 for p in c.resultado.pendencias if not p.resolvida)),
            caminho_sugerido=lambda extensao: caminho_exportacao(
                self.config_app, "Competencias", "Competencias", extensao),
        ).grid(row=0, column=3, padx=(0, 15))

    def _montar_lista(self) -> None:
        self._tabela = TabelaPadrao(
            self,
            criar_linha=lambda m: _CardCompetencia(
                m, ao_abrir=self._abrir, ao_arquivar=self._arquivar,
                ao_alternar_fechamento=self._alternar_fechamento,
                ao_abrir_historico=self._abrir_historico,
            ),
            colunas=[
                ColunaOrdenavel("Competência", lambda c: (c.ano, c.mes)),
                ColunaOrdenavel(
                    "Pendências", lambda c: sum(
                        1 for p in c.resultado.pendencias if not p.resolvida)),
            ],
            campos_pesquisa=[lambda c: f"{nome_mes(c.mes)}/{c.ano}"],
            placeholder_pesquisa="Pesquisar competência (ex.: Julho, 2026)...",
            texto_vazio="Nenhuma competência importada ainda.",
        )
        self._tabela.grid(row=1, column=0, sticky="nsew", padx=30, pady=15)

    # -- Ciclo de vida ---------------------------------------------------------

    def ao_exibir(self) -> None:
        """Hook padrão (Sprint 1): recarrega a lista sempre que a tela é exibida."""
        self._carregar()

    def _carregar(self) -> None:
        self._competencias = competencias.listar()
        self._tabela.definir_registros(self._competencias)

    def _imprimir(self) -> None:
        """Impressão universal (Sprint 1): gera o Excel da lista e envia à impressora padrão."""
        registros = self._tabela.registros_filtrados()
        if not registros:
            messagebox.showinfo("Imprimir", "Não há competências para imprimir.")
            return
        caminho = caminho_exportacao(self.config_app, "Competencias", "Competencias", "xlsx")
        exportar_excel_simples(
            caminho, "Competências", ["Competência", "Status", "Pendências"],
            [(f"{nome_mes(c.mes)}/{c.ano}", c.status.value,
              sum(1 for p in c.resultado.pendencias if not p.resolvida)) for c in registros],
        )
        try:
            os.startfile(str(caminho), "print")  # type: ignore[attr-defined]
            self.controlador.definir_status(f"Enviado para impressão: {caminho.name}")
        except OSError as erro:
            log.error("Falha ao imprimir competências: %s", erro)
            messagebox.showerror(
                "Não foi possível imprimir",
                f"Não foi possível enviar para impressão automaticamente. "
                f"O arquivo foi gerado em:\n{caminho}",
            )

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
