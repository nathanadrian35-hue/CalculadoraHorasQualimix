"""
tela_absenteismo_config.py
----------------------------
Tela de Configurações do Absenteísmo (v2.1 Sprint 2, Cap. 46/67).

Permite ao administrador escolher o método de cálculo (Dias/Horas/
Percentual), os limiares de alerta (Cap. 55/71) e, por Justificativa,
se ela conta ou não no índice, sua cor e se está ativa. Salvar sempre
incrementa a versão da configuração e registra auditoria
(`absenteismo.salvar_configuracao`) — nenhum índice já calculado é
recalculado retroativamente (Cap. 57/67).

Não lança nem edita Justificativas em si (isso continua sendo feito
via Pendências, Cap. 9.6) — só a configuração de como cada uma entra
(ou não) no índice de absenteísmo.
"""

from __future__ import annotations

import tkinter as tk
from tkinter import colorchooser, messagebox
from typing import Callable

import customtkinter as ctk

import absenteismo
from componentes import ColunaOrdenavel, TabelaPadrao
from config import Config
from constantes import MetodoCalculoAbsenteismo
from logger import get_logger
from modelos import ConfiguracaoAbsenteismo, ConfiguracaoOcorrencia

log = get_logger()


# ---------------------------------------------------------------------------
# Linha de uma ocorrência (Justificativa) configurável
# ---------------------------------------------------------------------------

class _LinhaOcorrencia(ctk.CTkFrame):
    """Uma linha reaproveitável do pool de `TabelaPadrao` — uma Justificativa configurável."""

    def __init__(self, master, ao_alterar: Callable[[], None]) -> None:
        super().__init__(master, corner_radius=8, border_width=1)
        self.ocorrencia: ConfiguracaoOcorrencia | None = None
        self._ao_alterar = ao_alterar

        self.grid_columnconfigure(0, weight=1)

        self._rotulo_nome = ctk.CTkLabel(
            self, anchor="w", font=ctk.CTkFont(weight="bold"))
        self._rotulo_nome.grid(row=0, column=0, sticky="w", padx=12, pady=10)

        self._var_considerar = tk.BooleanVar(value=False)
        ctk.CTkCheckBox(
            self, text="Considerar no índice", variable=self._var_considerar,
            command=self._alterar,
        ).grid(row=0, column=1, padx=10)

        self._quadro_cor = ctk.CTkFrame(self, width=20, height=20, corner_radius=4, border_width=1)
        self._quadro_cor.grid(row=0, column=2, padx=(10, 5))
        ctk.CTkButton(
            self, text="Cor", width=60, fg_color="transparent", border_width=1,
            command=self._escolher_cor,
        ).grid(row=0, column=3, padx=(0, 10))

        self._var_ativa = tk.BooleanVar(value=True)
        ctk.CTkCheckBox(
            self, text="Ativa", variable=self._var_ativa, command=self._alterar,
        ).grid(row=0, column=4, padx=(0, 12))

    def vincular(self, ocorrencia: ConfiguracaoOcorrencia) -> None:
        self.ocorrencia = ocorrencia
        self._rotulo_nome.configure(text=ocorrencia.justificativa.value)
        self._var_considerar.set(ocorrencia.considerar_no_indice)
        self._var_ativa.set(ocorrencia.ativa)
        self._aplicar_cor(ocorrencia.cor)

    def _alterar(self) -> None:
        if self.ocorrencia is None:
            return
        self.ocorrencia.considerar_no_indice = bool(self._var_considerar.get())
        self.ocorrencia.ativa = bool(self._var_ativa.get())
        self._ao_alterar()

    def _escolher_cor(self) -> None:
        if self.ocorrencia is None:
            return
        _rgb, cor_hex = colorchooser.askcolor(
            color=self.ocorrencia.cor, title="Cor da ocorrência")
        if cor_hex is None:
            return
        self.ocorrencia.cor = cor_hex
        self._aplicar_cor(cor_hex)
        self._ao_alterar()

    def _aplicar_cor(self, cor: str) -> None:
        try:
            self._quadro_cor.configure(fg_color=cor)
        except tk.TclError:
            self._quadro_cor.configure(fg_color="gray40")


# ---------------------------------------------------------------------------
# Tela de Configurações do Absenteísmo
# ---------------------------------------------------------------------------

class TelaAbsenteismoConfig(ctk.CTkFrame):
    """Configuração do módulo de Absenteísmo (Cap. 46/67)."""

    def __init__(self, master, controlador, config: Config) -> None:
        super().__init__(master, corner_radius=0)
        self.controlador = controlador
        self.config_app = config
        self._configuracao: ConfiguracaoAbsenteismo | None = None
        self._alterado = False
        self._considerar_original: dict[str, bool] = {}

        self.grid_rowconfigure(3, weight=1)
        self.grid_columnconfigure(0, weight=1)

        self._montar_cabecalho()
        self._montar_parametros()
        self._montar_lista()

    # -- Construção da UI -----------------------------------------------------

    def _montar_cabecalho(self) -> None:
        cabecalho = ctk.CTkFrame(self, corner_radius=0, height=70)
        cabecalho.grid(row=0, column=0, sticky="ew")
        cabecalho.grid_columnconfigure(1, weight=1)

        ctk.CTkButton(
            cabecalho, text="← Voltar", width=90,
            command=lambda: self.controlador.mostrar_tela("absenteismo"),
        ).grid(row=0, column=0, padx=15, pady=15)

        ctk.CTkLabel(
            cabecalho, text="Absenteísmo — Configurações",
            font=ctk.CTkFont(size=20, weight="bold"),
        ).grid(row=0, column=1, sticky="w", padx=10)

        self._botao_salvar = ctk.CTkButton(
            cabecalho, text="Salvar", width=110, command=self._salvar)
        self._botao_salvar.grid(row=0, column=2, padx=15)

    def _montar_parametros(self) -> None:
        barra = ctk.CTkFrame(self)
        barra.grid(row=1, column=0, sticky="ew", padx=30, pady=(15, 0))

        ctk.CTkLabel(barra, text="Método de cálculo").grid(
            row=0, column=0, sticky="w", padx=(15, 5), pady=12)
        self._var_metodo = tk.StringVar(value=MetodoCalculoAbsenteismo.PERCENTUAL.value)
        ctk.CTkOptionMenu(
            barra, values=[m.value for m in MetodoCalculoAbsenteismo],
            variable=self._var_metodo, width=140, command=lambda valor: self._marcar_alterado(),
        ).grid(row=0, column=1, padx=(0, 20), pady=12)

        ctk.CTkLabel(barra, text="Limite Atenção (%)").grid(
            row=0, column=2, sticky="w", padx=(0, 5))
        self._entry_atencao = ctk.CTkEntry(barra, width=70)
        self._entry_atencao.grid(row=0, column=3, padx=(0, 20))
        self._entry_atencao.bind("<KeyRelease>", lambda evento: self._marcar_alterado())

        ctk.CTkLabel(barra, text="Limite Crítico (%)").grid(
            row=0, column=4, sticky="w", padx=(0, 5))
        self._entry_critico = ctk.CTkEntry(barra, width=70)
        self._entry_critico.grid(row=0, column=5, padx=(0, 15))
        self._entry_critico.bind("<KeyRelease>", lambda evento: self._marcar_alterado())

    def _montar_lista(self) -> None:
        ctk.CTkLabel(
            self, text="Ocorrências consideradas no índice", anchor="w",
            font=ctk.CTkFont(size=14, weight="bold"),
        ).grid(row=2, column=0, sticky="w", padx=30, pady=(15, 0))

        self._tabela = TabelaPadrao(
            self,
            criar_linha=lambda m: _LinhaOcorrencia(m, ao_alterar=self._marcar_alterado),
            colunas=[
                ColunaOrdenavel("Justificativa", lambda o: o.justificativa.value),
                ColunaOrdenavel("Considerada", lambda o: o.considerar_no_indice),
            ],
            campos_pesquisa=[lambda o: o.justificativa.value],
            texto_vazio="Nenhuma ocorrência configurada.",
            tamanho_pagina_padrao=50,
        )
        self._tabela.grid(row=3, column=0, sticky="nsew", padx=30, pady=15)

    # -- Ciclo de vida -----------------------------------------------------------

    def ao_exibir(self) -> None:
        """Sempre recarrega do disco (hook padrão) — nunca reaproveita edição não salva."""
        self._configuracao = absenteismo.carregar_configuracao()
        self._alterado = False
        self._considerar_original = {
            oc.justificativa.value: oc.considerar_no_indice
            for oc in self._configuracao.ocorrencias
        }
        self._var_metodo.set(self._configuracao.metodo.value)
        self._entry_atencao.delete(0, "end")
        self._entry_atencao.insert(0, f"{self._configuracao.limiar_atencao:g}")
        self._entry_critico.delete(0, "end")
        self._entry_critico.insert(0, f"{self._configuracao.limiar_critico:g}")
        self._tabela.definir_registros(list(self._configuracao.ocorrencias))

    def _marcar_alterado(self) -> None:
        self._alterado = True

    # -- Ações -----------------------------------------------------------------

    def _salvar(self) -> None:
        if self._configuracao is None:
            return

        metodo_anterior = self._configuracao.metodo
        try:
            metodo_novo = MetodoCalculoAbsenteismo(self._var_metodo.get())
        except ValueError:
            metodo_novo = metodo_anterior

        try:
            limiar_atencao = float(self._entry_atencao.get().replace(",", "."))
            limiar_critico = float(self._entry_critico.get().replace(",", "."))
        except ValueError:
            messagebox.showerror(
                "Valor inválido", "Os limites de Atenção e Crítico devem ser números.")
            return
        if limiar_atencao < 0 or limiar_critico < 0 or limiar_atencao > limiar_critico:
            messagebox.showerror(
                "Valor inválido",
                "O limite de Atenção deve ser menor ou igual ao Crítico, e ambos não negativos.",
            )
            return

        quantidade_ocorrencias_alteradas = sum(
            1 for oc in self._configuracao.ocorrencias
            if oc.considerar_no_indice != self._considerar_original.get(
                oc.justificativa.value, oc.considerar_no_indice)
        )

        self._configuracao.metodo = metodo_novo
        self._configuracao.limiar_atencao = limiar_atencao
        self._configuracao.limiar_critico = limiar_critico

        absenteismo.salvar_configuracao(
            self._configuracao,
            o_que="Configuração de Absenteísmo atualizada",
            valor_anterior=f"Método: {metodo_anterior.value}",
            valor_novo=(
                f"Método: {metodo_novo.value}; Atenção: {limiar_atencao:g}%; "
                f"Crítico: {limiar_critico:g}%; "
                f"{quantidade_ocorrencias_alteradas} ocorrência(s) reconfigurada(s)"
            ),
        )
        self._alterado = False
        self._considerar_original = {
            oc.justificativa.value: oc.considerar_no_indice
            for oc in self._configuracao.ocorrencias
        }
        self.controlador.definir_status("Configuração de Absenteísmo salva.")
        messagebox.showinfo(
            "Configuração salva",
            f"Configuração salva (versão {self._configuracao.versao}). Índices já calculados "
            "não são alterados retroativamente.",
        )
