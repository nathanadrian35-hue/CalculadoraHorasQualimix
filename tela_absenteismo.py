"""
tela_absenteismo.py
---------------------
Tela de Absenteísmo (v2.1 Sprint 2, Cap. 41-80) — Dashboard,
Indicadores, Ranking, Comparativo, Previsão, Simulador e Exportação
consolidados numa única tela (mais "Configurações", tela própria por
ser um workflow distinto — `tela_absenteismo_config.py`).

Consolidação deliberada dos 7 submenus da especificação (Dashboard/
Lançamentos/Indicadores/Relatórios/Configurações/Histórico/Simulador,
Cap. 43): "Lançamentos" não é uma tela de cadastro — o Absenteísmo não
lança dado nenhum, só lê o que Pendências/Justificativas (Cap. 9.6) já
registraram (Cap. 44); "Indicadores"/"Dashboard"/"Relatórios" são a
mesma visão sobre os mesmos dados; "Histórico" é satisfeito pela
versão da configuração vinculada a cada índice (Cap. 57/67), sem
precisar de uma tela de navegação própria nesta entrega.

Todo cálculo passa exclusivamente por `absenteismo.py` — nenhuma conta
é feita aqui (Cap. 61).
"""

from __future__ import annotations

import os
import tkinter as tk
from tkinter import messagebox
from typing import Callable

import customtkinter as ctk

import absenteismo
import competencias
from componentes import BotaoExportar, ColunaOrdenavel, TabelaPadrao
from config import Config
from constantes import formatar_minutos, nome_mes
from exportacao import caminho_exportacao, exportar_excel_simples
from logger import get_logger
from modelos import Competencia, ConfiguracaoAbsenteismo, IndicadorAbsenteismo

log = get_logger()

_CORES_CLASSIFICACAO: dict[str, tuple[str, str]] = {
    "verde": ("#1e8449", "#2ecc71"),
    "amarelo": ("#a04000", "#f39c12"),
    "vermelho": ("#c0392b", "#e74c3c"),
}


# ---------------------------------------------------------------------------
# Linha de um indicador (funcionário) na tabela principal
# ---------------------------------------------------------------------------

class _LinhaIndicador(ctk.CTkFrame):
    """Uma linha reaproveitável do pool de `TabelaPadrao` — o índice de um funcionário."""

    def __init__(
        self, master,
        obter_configuracao: Callable[[], ConfiguracaoAbsenteismo | None],
        ao_ver_memoria: Callable[[IndicadorAbsenteismo], None],
        ao_simular: Callable[[IndicadorAbsenteismo], None],
    ) -> None:
        super().__init__(master, corner_radius=8, border_width=1)
        self.indicador: IndicadorAbsenteismo | None = None
        self._obter_configuracao = obter_configuracao
        self._ao_ver_memoria = ao_ver_memoria
        self._ao_simular = ao_simular

        self.grid_columnconfigure(0, weight=2)
        self.grid_columnconfigure(1, weight=1)

        self._rotulo_nome = ctk.CTkLabel(
            self, anchor="w", font=ctk.CTkFont(weight="bold"))
        self._rotulo_nome.grid(row=0, column=0, sticky="w", padx=12, pady=10)

        self._rotulo_resultado = ctk.CTkLabel(self, anchor="w", width=90)
        self._rotulo_resultado.grid(row=0, column=1, padx=5)

        self._rotulo_dias = ctk.CTkLabel(self, anchor="w", width=70)
        self._rotulo_dias.grid(row=0, column=2, padx=5)

        self._rotulo_horas = ctk.CTkLabel(self, anchor="w", width=90)
        self._rotulo_horas.grid(row=0, column=3, padx=5)

        ctk.CTkButton(
            self, text="Memória de Cálculo", width=140, fg_color="transparent", border_width=1,
            command=self._clicar_memoria,
        ).grid(row=0, column=4, padx=5, pady=10)

        ctk.CTkButton(
            self, text="Simular", width=90, command=self._clicar_simular,
        ).grid(row=0, column=5, padx=(0, 12))

    def vincular(self, indicador: IndicadorAbsenteismo) -> None:
        self.indicador = indicador
        self._rotulo_nome.configure(text=indicador.nome)
        self._rotulo_resultado.configure(text=absenteismo.texto_resultado(indicador))
        self._rotulo_dias.configure(text=f"{indicador.dias_perdidos} dia(s)")
        self._rotulo_horas.configure(text=formatar_minutos(indicador.horas_perdidas_min))

        configuracao = self._obter_configuracao()
        if configuracao is not None:
            cor = absenteismo.classificar_cor(indicador, configuracao)
            self._rotulo_resultado.configure(
                text_color=_CORES_CLASSIFICACAO.get(cor, ("gray50", "gray50")))

    def _clicar_memoria(self) -> None:
        if self.indicador is not None:
            self._ao_ver_memoria(self.indicador)

    def _clicar_simular(self) -> None:
        if self.indicador is not None:
            self._ao_simular(self.indicador)


# ---------------------------------------------------------------------------
# Tela de Absenteísmo
# ---------------------------------------------------------------------------

class TelaAbsenteismo(ctk.CTkFrame):
    """Dashboard/Indicadores/Ranking/Comparativo/Simulador de Absenteísmo (Cap. 41-80)."""

    def __init__(self, master, controlador, config: Config) -> None:
        super().__init__(master, corner_radius=0)
        self.controlador = controlador
        self.config_app = config
        self._competencias: list[Competencia] = []
        self._rotulos_competencia: dict[str, Competencia] = {}
        self._competencia_atual: Competencia | None = None
        self._configuracao: ConfiguracaoAbsenteismo | None = None
        self._indicadores: list[IndicadorAbsenteismo] = []

        self.grid_rowconfigure(3, weight=1)
        self.grid_columnconfigure(0, weight=1)

        self._montar_cabecalho()
        self._montar_cards()
        self._montar_alertas()
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
            cabecalho, text="Absenteísmo", font=ctk.CTkFont(size=20, weight="bold"),
        ).grid(row=0, column=1, sticky="w", padx=10)

        self._var_competencia = tk.StringVar(value="")
        self._menu_competencia = ctk.CTkOptionMenu(
            cabecalho, values=[""], variable=self._var_competencia, width=220,
            command=self._ao_selecionar_competencia,
        )
        self._menu_competencia.grid(row=0, column=2, padx=(0, 10))

        ctk.CTkButton(
            cabecalho, text="Configurações", width=120, fg_color="transparent", border_width=1,
            command=lambda: self.controlador.mostrar_tela("absenteismo_config"),
        ).grid(row=0, column=3, padx=(0, 10))

        ctk.CTkButton(
            cabecalho, text="Imprimir", width=90, fg_color="transparent", border_width=1,
            command=self._imprimir,
        ).grid(row=0, column=4, padx=(0, 10))

        BotaoExportar(
            cabecalho, titulo="Absenteísmo",
            colunas=["Funcionário", "Resultado", "Dias Perdidos", "Horas Perdidas"],
            obter_registros=lambda: self._tabela.registros_filtrados(),
            montar_linha=lambda i: (
                i.nome, absenteismo.texto_resultado(i), i.dias_perdidos,
                formatar_minutos(i.horas_perdidas_min)),
            caminho_sugerido=lambda extensao: caminho_exportacao(
                self.config_app, "Absenteismo", "Absenteismo", extensao),
        ).grid(row=0, column=5, padx=(0, 15))

    def _montar_cards(self) -> None:
        area = ctk.CTkFrame(self, fg_color="transparent")
        area.grid(row=1, column=0, sticky="ew", padx=30, pady=(15, 0))
        for coluna in range(5):
            area.grid_columnconfigure(coluna, weight=1)

        self._card_indice = self._montar_card(area, 0, "Índice Geral")
        self._card_horas_perdidas = self._montar_card(area, 1, "Horas Perdidas")
        self._card_dias_perdidos = self._montar_card(area, 2, "Dias Perdidos")
        self._card_funcionarios = self._montar_card(area, 3, "Funcionários")
        self._card_com_ocorrencia = self._montar_card(area, 4, "Com Ocorrência")

    def _montar_card(self, master, coluna: int, titulo: str) -> ctk.CTkLabel:
        card = ctk.CTkFrame(master, corner_radius=10)
        card.grid(row=0, column=coluna, sticky="ew", padx=8, pady=8)
        ctk.CTkLabel(
            card, text=titulo, font=ctk.CTkFont(size=12), text_color=("gray60", "gray60"),
        ).pack(anchor="w", padx=15, pady=(10, 0))
        rotulo_valor = ctk.CTkLabel(card, text="—", font=ctk.CTkFont(size=20, weight="bold"))
        rotulo_valor.pack(anchor="w", padx=15, pady=(0, 10))
        return rotulo_valor

    def _montar_alertas(self) -> None:
        linha = ctk.CTkFrame(self, fg_color="transparent")
        linha.grid(row=2, column=0, sticky="ew", padx=30, pady=(10, 0))
        linha.grid_columnconfigure(0, weight=1)

        self._rotulo_alertas = ctk.CTkLabel(
            linha, text="", anchor="w", justify="left", wraplength=700,
            text_color=("#a04000", "#f39c12"), font=ctk.CTkFont(size=12),
        )
        self._rotulo_alertas.grid(row=0, column=0, sticky="w")

        ctk.CTkLabel(linha, text="Comparar com").grid(row=0, column=1, padx=(10, 5))
        self._var_competencia_comparar = tk.StringVar(value="")
        self._menu_comparar = ctk.CTkOptionMenu(
            linha, values=[""], variable=self._var_competencia_comparar, width=160,
            command=lambda valor: self._atualizar_comparativo(),
        )
        self._menu_comparar.grid(row=0, column=2, padx=(0, 10))

        self._rotulo_comparativo = ctk.CTkLabel(
            linha, text="", anchor="e", font=ctk.CTkFont(size=12),
            text_color=("gray60", "gray60"),
        )
        self._rotulo_comparativo.grid(row=0, column=3, sticky="e")

    def _montar_lista(self) -> None:
        self._tabela = TabelaPadrao(
            self,
            criar_linha=lambda m: _LinhaIndicador(
                m, obter_configuracao=lambda: self._configuracao,
                ao_ver_memoria=self._ver_memoria_calculo, ao_simular=self._abrir_simulador,
            ),
            colunas=[
                ColunaOrdenavel("Funcionário", lambda i: i.nome.lower()),
                ColunaOrdenavel("Resultado", lambda i: i.resultado_no_metodo()),
                ColunaOrdenavel("Dias Perdidos", lambda i: i.dias_perdidos),
                ColunaOrdenavel("Horas Perdidas", lambda i: i.horas_perdidas_min),
            ],
            campos_pesquisa=[lambda i: i.nome],
            texto_vazio="Nenhum indicador calculado — importe/selecione uma competência.",
        )
        self._tabela.grid(row=3, column=0, sticky="nsew", padx=30, pady=15)

    # -- Ciclo de vida ---------------------------------------------------------

    def ao_exibir(self) -> None:
        """Hook padrão (Sprint 1): recarrega competências e recalcula os indicadores."""
        self._configuracao = absenteismo.carregar_configuracao()
        self._competencias = competencias.listar()
        self._rotulos_competencia = {
            f"{nome_mes(c.mes)}/{c.ano}": c for c in self._competencias
        }
        rotulos = list(self._rotulos_competencia.keys())
        self._menu_competencia.configure(values=rotulos or ["Nenhuma competência disponível"])
        if self._var_competencia.get() not in rotulos:
            self._var_competencia.set(rotulos[0] if rotulos else "Nenhuma competência disponível")
        self._menu_comparar.configure(values=[""] + rotulos)
        self._selecionar_competencia(self._var_competencia.get())

    def _ao_selecionar_competencia(self, rotulo: str) -> None:
        self._selecionar_competencia(rotulo)

    def _selecionar_competencia(self, rotulo: str) -> None:
        self._competencia_atual = self._rotulos_competencia.get(rotulo)
        if self._competencia_atual is None or self._configuracao is None:
            self._indicadores = []
        else:
            self._indicadores = absenteismo.calcular_indicadores(
                self._competencia_atual, self._configuracao)
        self._atualizar()
        self._atualizar_comparativo()

    def _atualizar_comparativo(self) -> None:
        """"Competência atual" × "Comparar com" (Cap. 56/74) — diferença de índice geral."""
        rotulo_b = self._var_competencia_comparar.get()
        competencia_b = self._rotulos_competencia.get(rotulo_b)
        if competencia_b is None or self._configuracao is None or not self._indicadores:
            self._rotulo_comparativo.configure(text="")
            return

        indicadores_b = absenteismo.calcular_indicadores(competencia_b, self._configuracao)
        resultado = absenteismo.comparar(self._indicadores, indicadores_b)
        unidade = "%" if self._configuracao.metodo.value == "Percentual" else (
            " dia(s)" if self._configuracao.metodo.value == "Dias" else " min")
        sinal = "+" if resultado["diferenca_absoluta"] >= 0 else ""
        self._rotulo_comparativo.configure(
            text=(
                f"{self._var_competencia.get()}: {resultado['indice_a']:.2f}{unidade}   "
                f"{rotulo_b}: {resultado['indice_b']:.2f}{unidade}   "
                f"Diferença: {sinal}{resultado['diferenca_absoluta']:.2f}{unidade}"
            )
        )

    def _atualizar(self) -> None:
        self._tabela.definir_registros(self._indicadores)

        if not self._indicadores or self._configuracao is None:
            for card in (
                self._card_indice, self._card_horas_perdidas, self._card_dias_perdidos,
                self._card_funcionarios, self._card_com_ocorrencia,
            ):
                card.configure(text="—")
            self._rotulo_alertas.configure(text="")
            return

        indice = absenteismo.indice_geral(self._indicadores)
        total_horas_perdidas = sum(i.horas_perdidas_min for i in self._indicadores)
        total_dias_perdidos = sum(i.dias_perdidos for i in self._indicadores)
        com_ocorrencia = sum(1 for i in self._indicadores if i.ocorrencias_consideradas)

        texto_indice = (
            f"{indice:.2f}%" if self._configuracao.metodo.value == "Percentual"
            else (f"{total_dias_perdidos} dia(s)" if self._configuracao.metodo.value == "Dias"
                  else formatar_minutos(total_horas_perdidas))
        )
        self._card_indice.configure(text=texto_indice)
        self._card_horas_perdidas.configure(text=formatar_minutos(total_horas_perdidas))
        self._card_dias_perdidos.configure(text=str(total_dias_perdidos))
        self._card_funcionarios.configure(text=str(len(self._indicadores)))
        self._card_com_ocorrencia.configure(text=str(com_ocorrencia))

        alertas = absenteismo.gerar_alertas(self._indicadores, self._configuracao)
        if alertas:
            self._rotulo_alertas.configure(text="⚠ " + "  |  ".join(alertas[:5]))
        else:
            self._rotulo_alertas.configure(text="")

    # -- Memória de Cálculo (Cap. 48/50/66) -------------------------------------

    def _ver_memoria_calculo(self, indicador: IndicadorAbsenteismo) -> None:
        janela = ctk.CTkToplevel(self)
        janela.title(f"Memória de Cálculo — {indicador.nome}")
        janela.geometry("560x480")
        janela.transient(self.winfo_toplevel())

        texto = ctk.CTkTextbox(janela, font=ctk.CTkFont(family="Consolas", size=12))
        texto.pack(fill="both", expand=True, padx=15, pady=15)
        texto.insert("1.0", absenteismo.montar_memoria_calculo(indicador))
        texto.configure(state="disabled")

    # -- Simulador (Cap. 51) — nunca altera dados reais -------------------------

    def _abrir_simulador(self, indicador: IndicadorAbsenteismo) -> None:
        janela = ctk.CTkToplevel(self)
        janela.title(f"Simular Absenteísmo — {indicador.nome}")
        janela.geometry("480x360")
        janela.transient(self.winfo_toplevel())
        janela.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(
            janela, text="SIMULAÇÃO — não altera nenhum dado real",
            text_color=("#a04000", "#f39c12"), font=ctk.CTkFont(weight="bold"),
        ).grid(row=0, column=0, sticky="w", padx=15, pady=(15, 5))

        ctk.CTkLabel(
            janela, text=f"Resultado atual: {absenteismo.texto_resultado(indicador)}", anchor="w",
        ).grid(row=1, column=0, sticky="w", padx=15)

        frame_dias = ctk.CTkFrame(janela, fg_color="transparent")
        frame_dias.grid(row=2, column=0, sticky="w", padx=15, pady=(15, 0))
        ctk.CTkLabel(frame_dias, text="Se faltar mais").pack(side="left", padx=(0, 5))
        entry_dias = ctk.CTkEntry(frame_dias, width=50)
        entry_dias.insert(0, "1")
        entry_dias.pack(side="left", padx=(0, 5))
        ctk.CTkLabel(frame_dias, text="dia(s)...").pack(side="left")

        rotulo_resultado_simulado = ctk.CTkLabel(
            janela, text="", anchor="w", font=ctk.CTkFont(weight="bold"))
        rotulo_resultado_simulado.grid(row=4, column=0, sticky="w", padx=15, pady=(15, 0))

        def _simular() -> None:
            try:
                dias_extras = int(entry_dias.get())
            except ValueError:
                messagebox.showerror("Valor inválido", "Informe um número inteiro de dias.")
                return
            simulado = absenteismo.simular_dias_extras(indicador, dias_extras)
            rotulo_resultado_simulado.configure(
                text=f"Resultado simulado: {absenteismo.texto_resultado(simulado)} "
                     f"(era {absenteismo.texto_resultado(indicador)})"
            )

        ctk.CTkButton(janela, text="Simular", command=_simular).grid(
            row=3, column=0, sticky="w", padx=15, pady=(10, 0))

    # -- Impressão (Sprint 1) ----------------------------------------------------

    def _imprimir(self) -> None:
        registros = self._tabela.registros_filtrados()
        if not registros:
            messagebox.showinfo("Imprimir", "Não há indicadores para imprimir.")
            return
        caminho = caminho_exportacao(self.config_app, "Absenteismo", "Absenteismo", "xlsx")
        exportar_excel_simples(
            caminho, "Absenteísmo",
            ["Funcionário", "Resultado", "Dias Perdidos", "Horas Perdidas"],
            [(i.nome, absenteismo.texto_resultado(i), i.dias_perdidos,
              formatar_minutos(i.horas_perdidas_min)) for i in registros],
        )
        try:
            os.startfile(str(caminho), "print")  # type: ignore[attr-defined]
            self.controlador.definir_status(f"Enviado para impressão: {caminho.name}")
        except OSError as erro:
            log.error("Falha ao imprimir absenteísmo: %s", erro)
            messagebox.showerror(
                "Não foi possível imprimir",
                f"Não foi possível enviar para impressão automaticamente. "
                f"O arquivo foi gerado em:\n{caminho}",
            )
