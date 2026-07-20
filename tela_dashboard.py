"""
tela_dashboard.py
------------------
Tela Dashboard (Etapa 10, v2.0) — visão consolidada em cards e tabelas
da competência selecionada. Não calcula nada: consome exclusivamente
o que `calculadora.py` (Cap. 6) e `relatorio.montar_resumo_geral`
(Cap. 11.9) já produziram, na mesma competência persistida por
`competencias.py`.

Sem gráficos de imagem (decisão confirmada com o usuário — mantém o
instalador leve, sem nova dependência): os "gráficos" pedidos na
especificação (Horas extras por funcionário, Horas negativas,
Pendências por dia, Horas extras por dia, Ranking de horas extras,
Ranking de atrasos, Banco de horas) são apresentados como tabelas
numéricas ordenadas, dentro de uma `CTkScrollableFrame`.

"Ranking de atrasos" usa a única noção já existente de atraso no
sistema: dias cuja `Situacao` calculada é `HORA_NEGATIVA` (Cap. 10) —
nenhuma regra nova, só uma contagem sobre o que o Motor já classificou.
"""

from __future__ import annotations

import tkinter as tk

import customtkinter as ctk

import competencias
from config import Config
from constantes import Situacao, formatar_minutos, nome_mes
from logger import get_logger
from modelos import Competencia, ResultadoProcessamento
from relatorio import montar_resumo_geral

log = get_logger()

_TOPO_RANKING = 10


class TelaDashboard(ctk.CTkFrame):
    """Tela Dashboard (Etapa 10, v2.0)."""

    def __init__(self, master, controlador, config: Config) -> None:
        super().__init__(master, corner_radius=0)
        self.controlador = controlador
        self.config_app = config
        self._resultado: ResultadoProcessamento | None = None
        self._competencia_obj: Competencia | None = None
        self._competencias: list[Competencia] = []
        self._rotulos_competencia: dict[str, Competencia] = {}

        self.grid_rowconfigure(2, weight=1)
        self.grid_columnconfigure(0, weight=1)

        self._montar_cabecalho()
        self._montar_cards()
        self._montar_area_tabelas()

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
            cabecalho, text="Dashboard", font=ctk.CTkFont(size=20, weight="bold"),
        ).grid(row=0, column=1, sticky="w", padx=10)

        self._var_competencia = tk.StringVar(value="")
        self._menu_competencia = ctk.CTkOptionMenu(
            cabecalho, values=[""], variable=self._var_competencia, width=260,
            command=self._ao_selecionar_competencia,
        )
        self._menu_competencia.grid(row=0, column=2, padx=15)

    def _montar_cards(self) -> None:
        area = ctk.CTkFrame(self, fg_color="transparent")
        area.grid(row=1, column=0, sticky="ew", padx=30, pady=(15, 0))
        for coluna in range(4):
            area.grid_columnconfigure(coluna, weight=1)

        self._card_funcionarios = self._montar_card(area, 0, 0, "Total Funcionários")
        self._card_horas_trabalhadas = self._montar_card(area, 0, 1, "Horas Trabalhadas")
        self._card_horas_extras = self._montar_card(area, 0, 2, "Horas Extras")
        self._card_horas_negativas = self._montar_card(area, 0, 3, "Horas Negativas")
        self._card_banco_horas = self._montar_card(area, 1, 0, "Banco de Horas")
        self._card_pendencias = self._montar_card(area, 1, 1, "Pendências")
        self._card_dias_processados = self._montar_card(area, 1, 2, "Dias Processados")
        self._card_competencia = self._montar_card(area, 1, 3, "Competência")

    def _montar_card(self, master, linha: int, coluna: int, titulo: str) -> ctk.CTkLabel:
        card = ctk.CTkFrame(master, corner_radius=10)
        card.grid(row=linha, column=coluna, sticky="ew", padx=8, pady=8)
        ctk.CTkLabel(
            card, text=titulo, font=ctk.CTkFont(size=12), text_color=("gray60", "gray60"),
        ).pack(anchor="w", padx=15, pady=(10, 0))
        rotulo_valor = ctk.CTkLabel(card, text="—", font=ctk.CTkFont(size=20, weight="bold"))
        rotulo_valor.pack(anchor="w", padx=15, pady=(0, 10))
        return rotulo_valor

    def _montar_area_tabelas(self) -> None:
        self._scroll = ctk.CTkScrollableFrame(self, fg_color="transparent")
        self._scroll.grid(row=2, column=0, sticky="nsew", padx=30, pady=15)
        self._scroll.grid_columnconfigure(0, weight=1)
        self._scroll.grid_columnconfigure(1, weight=1)

        self._rotulo_vazio = ctk.CTkLabel(
            self._scroll, text="Nenhuma competência disponível — importe uma planilha primeiro.",
            text_color=("gray60", "gray60"),
        )

    # -- Ciclo de vida -----------------------------------------------------------

    def ao_exibir(self) -> None:
        """Hook padrão: recarrega a lista de competências sempre que a tela é exibida."""
        self._competencias = competencias.listar()
        self._rotulos_competencia = {
            f"{nome_mes(c.mes)}/{c.ano} — {c.status.value}": c for c in self._competencias
        }
        rotulos = list(self._rotulos_competencia.keys())
        self._menu_competencia.configure(values=rotulos or ["Nenhuma competência disponível"])
        if self._var_competencia.get() not in rotulos:
            self._var_competencia.set(rotulos[0] if rotulos else "Nenhuma competência disponível")
        self._selecionar_competencia(self._var_competencia.get())

    def _ao_selecionar_competencia(self, rotulo: str) -> None:
        self._selecionar_competencia(rotulo)

    def _selecionar_competencia(self, rotulo: str) -> None:
        self._competencia_obj = self._rotulos_competencia.get(rotulo)
        self._resultado = self._competencia_obj.resultado if self._competencia_obj else None
        self._atualizar()

    # -- Atualização ---------------------------------------------------------------

    def _atualizar(self) -> None:
        for widget in self._scroll.winfo_children():
            if widget is not self._rotulo_vazio:
                widget.destroy()
        self._rotulo_vazio.grid_forget()

        if self._resultado is None or self._competencia_obj is None:
            for card in (
                self._card_funcionarios, self._card_horas_trabalhadas,
                self._card_horas_extras, self._card_horas_negativas,
                self._card_banco_horas, self._card_pendencias,
                self._card_dias_processados, self._card_competencia,
            ):
                card.configure(text="—")
            self._rotulo_vazio.grid(row=0, column=0, columnspan=2, pady=30)
            return

        competencia = self._competencia_obj
        resultado = self._resultado
        competencia_texto = f"{nome_mes(competencia.mes)}/{competencia.ano}"
        resumo_geral = montar_resumo_geral(resultado, competencia_texto)

        dias_processados = len({
            dia.data for funcionario in resultado.funcionarios_processados
            for dia in funcionario.dias
        })

        self._card_funcionarios.configure(text=str(resumo_geral.funcionarios_processados))
        self._card_horas_trabalhadas.configure(
            text=formatar_minutos(resumo_geral.horas_trabalhadas_min))
        self._card_horas_extras.configure(text=formatar_minutos(resumo_geral.horas_extras_min))
        self._card_horas_negativas.configure(
            text=formatar_minutos(resumo_geral.horas_negativas_min))
        self._card_banco_horas.configure(text=formatar_minutos(resumo_geral.saldo_geral_min))
        self._card_pendencias.configure(text=str(resumo_geral.total_pendencias))
        self._card_dias_processados.configure(text=str(dias_processados))
        self._card_competencia.configure(text=competencia_texto)

        self._montar_tabelas(resultado)

    # -- Tabelas (Etapa 10 — "gráficos" numéricos, sem imagens) ---------------------

    def _montar_tabelas(self, resultado: ResultadoProcessamento) -> None:
        resumos = resultado.resumos_mensais

        extras_por_funcionario = sorted(
            (r for r in resumos if r.horas_extras_min > 0),
            key=lambda r: r.horas_extras_min, reverse=True,
        )
        self._montar_tabela(
            0, 0, "Horas Extras por Funcionário", ["Funcionário", "Horas Extras"],
            [(r.nome, formatar_minutos(r.horas_extras_min)) for r in extras_por_funcionario],
        )

        negativas_por_funcionario = sorted(
            (r for r in resumos if r.horas_negativas_min > 0),
            key=lambda r: r.horas_negativas_min, reverse=True,
        )
        self._montar_tabela(
            0, 1, "Horas Negativas por Funcionário", ["Funcionário", "Horas Negativas"],
            [(r.nome, formatar_minutos(-r.horas_negativas_min))
             for r in negativas_por_funcionario],
        )

        pendencias_por_dia: dict[str, int] = {}
        for pendencia in resultado.pendencias:
            if pendencia.data is None:
                continue
            chave = pendencia.data.strftime("%d/%m/%Y")
            pendencias_por_dia[chave] = pendencias_por_dia.get(chave, 0) + 1
        self._montar_tabela(
            1, 0, "Pendências por Dia", ["Data", "Pendências"],
            sorted(pendencias_por_dia.items()),
        )

        extras_por_dia: dict[str, int] = {}
        for funcionario in resultado.funcionarios_processados:
            for dia in funcionario.dias:
                if dia.resultado.horas_extras_min > 0:
                    chave = dia.data.strftime("%d/%m/%Y")
                    extras_por_dia[chave] = (
                        extras_por_dia.get(chave, 0) + dia.resultado.horas_extras_min)
        self._montar_tabela(
            1, 1, "Horas Extras por Dia", ["Data", "Horas Extras"],
            [(data, formatar_minutos(minutos))
             for data, minutos in sorted(extras_por_dia.items())],
        )

        ranking_extras = extras_por_funcionario[:_TOPO_RANKING]
        self._montar_tabela(
            2, 0, f"Ranking de Horas Extras (Top {_TOPO_RANKING})",
            ["#", "Funcionário", "Horas Extras"],
            [(str(i + 1), r.nome, formatar_minutos(r.horas_extras_min))
             for i, r in enumerate(ranking_extras)],
        )

        atrasos_por_funcionario: dict[str, tuple[str, int]] = {}
        for funcionario in resultado.funcionarios_processados:
            quantidade = sum(
                1 for dia in funcionario.dias
                if dia.resultado.situacao == Situacao.HORA_NEGATIVA
            )
            if quantidade > 0:
                atrasos_por_funcionario[funcionario.id] = (funcionario.nome_completo, quantidade)
        ranking_atrasos = sorted(
            atrasos_por_funcionario.values(), key=lambda item: item[1], reverse=True,
        )[:_TOPO_RANKING]
        self._montar_tabela(
            2, 1, f"Ranking de Atrasos (Top {_TOPO_RANKING})",
            ["#", "Funcionário", "Dias com Hora Negativa"],
            [(str(i + 1), nome, str(quantidade))
             for i, (nome, quantidade) in enumerate(ranking_atrasos)],
        )

        banco_horas = sorted(resumos, key=lambda r: r.saldo_final_min, reverse=True)
        self._montar_tabela(
            3, 0, "Banco de Horas (Saldo por Funcionário)", ["Funcionário", "Saldo"],
            [(r.nome, formatar_minutos(r.saldo_final_min)) for r in banco_horas],
            colspan=2,
        )

    def _montar_tabela(
        self, linha: int, coluna: int, titulo: str, colunas: list[str],
        registros: list[tuple], colspan: int = 1,
    ) -> None:
        bloco = ctk.CTkFrame(self._scroll, corner_radius=10)
        bloco.grid(
            row=linha, column=coluna, columnspan=colspan, sticky="nsew", padx=8, pady=8)
        for c in range(len(colunas)):
            bloco.grid_columnconfigure(c, weight=1)

        ctk.CTkLabel(
            bloco, text=titulo, font=ctk.CTkFont(size=14, weight="bold"), anchor="w",
        ).grid(row=0, column=0, columnspan=len(colunas), sticky="w", padx=15, pady=(12, 5))

        for c, nome_coluna in enumerate(colunas):
            ctk.CTkLabel(
                bloco, text=nome_coluna, font=ctk.CTkFont(size=12, weight="bold"),
                text_color=("gray60", "gray60"), anchor="w",
            ).grid(row=1, column=c, sticky="w", padx=15, pady=(0, 5))

        if not registros:
            ctk.CTkLabel(
                bloco, text="Sem dados nesta competência.", text_color=("gray60", "gray60"),
                font=ctk.CTkFont(size=12),
            ).grid(row=2, column=0, columnspan=len(colunas), sticky="w", padx=15, pady=(0, 12))
            return

        for i, registro in enumerate(registros):
            for c, valor in enumerate(registro):
                ctk.CTkLabel(
                    bloco, text=str(valor), anchor="w", font=ctk.CTkFont(size=12),
                ).grid(row=2 + i, column=c, sticky="w", padx=15, pady=1)

        ctk.CTkLabel(bloco, text="").grid(row=2 + len(registros), column=0, pady=(0, 8))
