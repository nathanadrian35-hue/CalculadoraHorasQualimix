"""
tela_relatorios.py
-------------------
Tela de Relatórios (Cap. 12.8) — visualizar e exportar os relatórios
da competência processada (Cap. 11), com filtros e bloqueio por
pendências (Cap. 9.1/11.11).

Não calcula nada — consome exclusivamente `relatorio.py` (que por sua
vez só lê o que `calculadora.py`, Cap. 6, já produziu). Acessível pelo
botão "Relatórios" da Tela Inicial (Cap. 12.2), não só logo após um
processamento: um seletor lista TODAS as competências persistidas
(`competencias.listar()`, gerenciamento de múltiplas competências) —
cada uma gera seu relatório de forma independente, sem afetar as
demais.
"""

from __future__ import annotations

import os
import tkinter as tk
from datetime import date, datetime, timedelta
from pathlib import Path
from tkinter import messagebox

import customtkinter as ctk

import competencias
from config import Config
from constantes import Situacao, StatusCompetencia, StatusFuncionario, formatar_minutos, nome_mes
from logger import get_logger
from modelos import Competencia, Funcionario, ResultadoProcessamento
from relatorio import (
    MENSAGEM_BLOQUEIO,
    ExportadorExcel,
    RelatorioBloqueadoError,
    caminho_historico,
    existem_pendencias_abertas,
    filtrar_por_atributos,
    filtrar_por_periodo,
    filtrar_resultado,
    montar_dados_relatorio,
    montar_resumo_geral,
)

log = get_logger()

_TODOS = "Todos"
_PERIODO_MES_COMPLETO = "Mês completo"
_PERIODO_PERSONALIZADO = "Personalizado"
_COM_PENDENCIA = "Com pendência"
_SEM_PENDENCIA = "Sem pendência"
_COM_HORAS_EXTRAS = "Com horas extras"
_SEM_HORAS_EXTRAS = "Sem horas extras"
_BANCO_POSITIVO = "Positivo"
_BANCO_NEGATIVO = "Negativo"
_BANCO_ZERADO = "Zerado"


def _texto_para_data(texto: str) -> date | None:
    """Converte "DD/MM/AAAA" em `date`. Retorna None se vazio/inválido."""
    texto = texto.strip()
    if not texto:
        return None
    try:
        return datetime.strptime(texto, "%d/%m/%Y").date()
    except ValueError:
        return None


class TelaRelatorios(ctk.CTkFrame):
    """Tela de Relatórios (Cap. 12.8)."""

    def __init__(self, master, controlador, config: Config) -> None:
        super().__init__(master, corner_radius=0)
        self.controlador = controlador
        self.config_app = config
        self._resultado: ResultadoProcessamento | None = None
        self._arquivo_original: str = ""
        self._competencia: tuple[int, int] | None = None
        self._competencias: list[Competencia] = []
        self._competencia_obj: Competencia | None = None
        self._rotulos_competencia: dict[str, Competencia] = {}
        self._exportador_excel = ExportadorExcel()

        self.grid_rowconfigure(4, weight=1)
        self.grid_columnconfigure(0, weight=1)

        self._montar_cabecalho()
        self._montar_resumo_superior()
        self._montar_periodo()
        self._montar_filtros()
        self._montar_area_principal()

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
            cabecalho, text="Relatórios", font=ctk.CTkFont(size=20, weight="bold"),
        ).grid(row=0, column=1, sticky="w", padx=10)

        # Seletor de competência (gerenciamento de múltiplas competências):
        # lista TODAS as competências persistidas, cada rótulo já indicando
        # o status (ex.: "Julho/2026 — Pendências abertas"). Uma competência
        # com pendência em aberto aparece normalmente na lista — o bloqueio
        # é comunicado pelo mecanismo já existente (`_atualizar()` abaixo),
        # nunca por um item "desabilitado" no próprio menu.
        self._var_competencia = tk.StringVar(value="")
        self._menu_competencia = ctk.CTkOptionMenu(
            cabecalho, values=[""], variable=self._var_competencia, width=260,
            command=self._ao_selecionar_competencia,
        )
        self._menu_competencia.grid(row=0, column=2, padx=15)

    def _montar_resumo_superior(self) -> None:
        """Resumo superior (Cap. 12.8): Funcionários/Horas Extras/Horas Negativas/Pendências."""
        resumo = ctk.CTkFrame(self)
        resumo.grid(row=1, column=0, sticky="ew", padx=30, pady=(15, 0))
        for coluna in range(4):
            resumo.grid_columnconfigure(coluna, weight=1)

        self._rotulo_card_funcionarios = self._montar_card(resumo, 0, "Funcionários")
        self._rotulo_card_extras = self._montar_card(resumo, 1, "Horas Extras")
        self._rotulo_card_negativas = self._montar_card(resumo, 2, "Horas Negativas")
        self._rotulo_card_pendencias = self._montar_card(resumo, 3, "Pendências")

    def _montar_card(self, master, coluna: int, titulo: str) -> ctk.CTkLabel:
        card = ctk.CTkFrame(master, corner_radius=10)
        card.grid(row=0, column=coluna, sticky="ew", padx=8, pady=12)
        ctk.CTkLabel(
            card, text=titulo, font=ctk.CTkFont(size=12), text_color=("gray60", "gray60"),
        ).pack(anchor="w", padx=15, pady=(10, 0))
        rotulo_valor = ctk.CTkLabel(card, text="—", font=ctk.CTkFont(size=20, weight="bold"))
        rotulo_valor.pack(anchor="w", padx=15, pady=(0, 10))
        return rotulo_valor

    def _montar_periodo(self) -> None:
        """
        Período do relatório (Etapa 8 v2.0): dia/semana/quinzena/intervalo
        personalizado/mês completo — independente do fechamento da
        competência. "Mês completo" (padrão) preserva o comportamento
        anterior ao v2.0 (nenhum filtro de data aplicado). Os três botões
        de atalho só preenchem os campos "De"/"Até" com um intervalo
        pronto; o filtro em si é sempre resolvido a partir desses dois
        campos quando o modo é "Personalizado" (ver `_intervalo_periodo_selecionado`).
        """
        barra = ctk.CTkFrame(self, fg_color="transparent")
        barra.grid(row=2, column=0, sticky="ew", padx=30, pady=(15, 0))

        ctk.CTkLabel(barra, text="Período").grid(row=0, column=0, sticky="w", padx=(0, 5))
        self._var_periodo = tk.StringVar(value=_PERIODO_MES_COMPLETO)
        self._menu_periodo = ctk.CTkOptionMenu(
            barra, values=[_PERIODO_MES_COMPLETO, _PERIODO_PERSONALIZADO],
            variable=self._var_periodo, width=150,
            command=lambda valor: self._ao_alterar_periodo(),
        )
        self._menu_periodo.grid(row=0, column=1, padx=(0, 15))

        ctk.CTkLabel(barra, text="De").grid(row=0, column=2, sticky="w", padx=(0, 5))
        self._entry_periodo_inicio = ctk.CTkEntry(barra, placeholder_text="DD/MM/AAAA", width=100)
        self._entry_periodo_inicio.grid(row=0, column=3, padx=(0, 15))
        self._entry_periodo_inicio.bind("<KeyRelease>", lambda evento: self._atualizar())

        ctk.CTkLabel(barra, text="Até").grid(row=0, column=4, sticky="w", padx=(0, 5))
        self._entry_periodo_fim = ctk.CTkEntry(barra, placeholder_text="DD/MM/AAAA", width=100)
        self._entry_periodo_fim.grid(row=0, column=5, padx=(0, 15))
        self._entry_periodo_fim.bind("<KeyRelease>", lambda evento: self._atualizar())

        ctk.CTkButton(
            barra, text="Hoje", width=70, command=lambda: self._definir_periodo_preset(0),
        ).grid(row=0, column=6, padx=(0, 8))
        ctk.CTkButton(
            barra, text="Esta Semana", width=100,
            command=lambda: self._definir_periodo_preset(6),
        ).grid(row=0, column=7, padx=(0, 8))
        ctk.CTkButton(
            barra, text="Quinzena", width=90, command=lambda: self._definir_periodo_preset(14),
        ).grid(row=0, column=8)

        # Estado inicial dos campos "De"/"Até" (desabilitados — "Mês
        # completo" é o padrão): configurado diretamente, sem passar por
        # `_ao_alterar_periodo()`/`_atualizar()`, porque neste ponto da
        # construção da tela `_montar_area_principal()` ainda não rodou
        # (widgets como `_rotulo_bloqueio` ainda não existem).
        self._entry_periodo_inicio.configure(state="disabled")
        self._entry_periodo_fim.configure(state="disabled")

    def _ao_alterar_periodo(self) -> None:
        personalizado = self._var_periodo.get() == _PERIODO_PERSONALIZADO
        estado = "normal" if personalizado else "disabled"
        self._entry_periodo_inicio.configure(state=estado)
        self._entry_periodo_fim.configure(state=estado)
        self._atualizar()

    def _definir_periodo_preset(self, dias_atras: int) -> None:
        fim = date.today()
        inicio = fim - timedelta(days=dias_atras)
        self._var_periodo.set(_PERIODO_PERSONALIZADO)
        self._entry_periodo_inicio.configure(state="normal")
        self._entry_periodo_fim.configure(state="normal")
        self._entry_periodo_inicio.delete(0, "end")
        self._entry_periodo_inicio.insert(0, inicio.strftime("%d/%m/%Y"))
        self._entry_periodo_fim.delete(0, "end")
        self._entry_periodo_fim.insert(0, fim.strftime("%d/%m/%Y"))
        self._atualizar()

    def _intervalo_periodo_selecionado(self) -> tuple[date, date] | None:
        """None = sem filtro de período ("Mês completo" — comportamento pré-v2.0)."""
        if self._var_periodo.get() != _PERIODO_PERSONALIZADO:
            return None
        inicio = _texto_para_data(self._entry_periodo_inicio.get())
        fim = _texto_para_data(self._entry_periodo_fim.get())
        if inicio is None or fim is None:
            return None
        if inicio > fim:
            inicio, fim = fim, inicio
        return inicio, fim

    def _montar_filtros(self) -> None:
        """
        Funcionário (Todos/Individual) + filtros de Setor/Turno/Cargo/Status
        (Cap. 12.8), mais os novos filtros de Situação/Pendências/Horas
        Extras/Banco de Horas (Etapa 9 v2.0) — 3 filtros por linha (em vez
        de 5 numa única linha) para que todos caibam na largura padrão da
        janela (1000px) sem ficar cortados fora da área visível.
        """
        barra = ctk.CTkFrame(self, fg_color="transparent")
        barra.grid(row=3, column=0, sticky="ew", padx=30, pady=(15, 0))

        def _rotulo(texto: str, coluna: int, linha: int) -> None:
            pady = (0, 0) if linha == 0 else (10, 0)
            ctk.CTkLabel(barra, text=texto).grid(
                row=linha, column=coluna, sticky="w", padx=(0, 5), pady=pady)

        ctk.CTkLabel(barra, text="Funcionário").grid(row=0, column=0, sticky="w", padx=(0, 5))
        self._var_funcionario = tk.StringVar(value=_TODOS)
        self._menu_funcionario = ctk.CTkOptionMenu(
            barra, values=[_TODOS], variable=self._var_funcionario, width=200,
            command=lambda valor: self._ao_alterar_modo(),
        )
        self._menu_funcionario.grid(row=0, column=1, padx=(0, 30))

        _rotulo("Setor", 2, 0)
        self._var_setor = tk.StringVar(value=_TODOS)
        self._menu_setor = ctk.CTkOptionMenu(
            barra, values=[_TODOS], variable=self._var_setor, width=200,
            command=lambda valor: self._atualizar(),
        )
        self._menu_setor.grid(row=0, column=3, padx=(0, 30))

        _rotulo("Turno", 4, 0)
        self._var_turno = tk.StringVar(value=_TODOS)
        self._menu_turno = ctk.CTkOptionMenu(
            barra, values=[_TODOS], variable=self._var_turno, width=200,
            command=lambda valor: self._atualizar(),
        )
        self._menu_turno.grid(row=0, column=5)

        _rotulo("Cargo", 0, 1)
        self._var_cargo = tk.StringVar(value=_TODOS)
        self._menu_cargo = ctk.CTkOptionMenu(
            barra, values=[_TODOS], variable=self._var_cargo, width=200,
            command=lambda valor: self._atualizar(),
        )
        self._menu_cargo.grid(row=1, column=1, padx=(0, 30), pady=(10, 0))

        _rotulo("Status", 2, 1)
        self._var_status = tk.StringVar(value=_TODOS)
        self._menu_status = ctk.CTkOptionMenu(
            barra, values=[_TODOS, StatusFuncionario.ATIVO.value, StatusFuncionario.INATIVO.value],
            variable=self._var_status, width=200,
            command=lambda valor: self._atualizar(),
        )
        self._menu_status.grid(row=1, column=3, padx=(0, 30), pady=(10, 0))

        _rotulo("Situação", 4, 1)
        self._var_situacao_filtro = tk.StringVar(value=_TODOS)
        self._menu_situacao_filtro = ctk.CTkOptionMenu(
            barra, values=[_TODOS] + [s.value for s in Situacao],
            variable=self._var_situacao_filtro, width=200,
            command=lambda valor: self._atualizar(),
        )
        self._menu_situacao_filtro.grid(row=1, column=5, pady=(10, 0))

        _rotulo("Pendências", 0, 2)
        self._var_pendencia_filtro = tk.StringVar(value=_TODOS)
        self._menu_pendencia_filtro = ctk.CTkOptionMenu(
            barra, values=[_TODOS, _COM_PENDENCIA, _SEM_PENDENCIA],
            variable=self._var_pendencia_filtro, width=200,
            command=lambda valor: self._atualizar(),
        )
        self._menu_pendencia_filtro.grid(row=2, column=1, padx=(0, 30), pady=(10, 0))

        _rotulo("Horas Extras", 2, 2)
        self._var_extras_filtro = tk.StringVar(value=_TODOS)
        self._menu_extras_filtro = ctk.CTkOptionMenu(
            barra, values=[_TODOS, _COM_HORAS_EXTRAS, _SEM_HORAS_EXTRAS],
            variable=self._var_extras_filtro, width=200,
            command=lambda valor: self._atualizar(),
        )
        self._menu_extras_filtro.grid(row=2, column=3, padx=(0, 30), pady=(10, 0))

        _rotulo("Banco de Horas", 4, 2)
        self._var_banco_filtro = tk.StringVar(value=_TODOS)
        self._menu_banco_filtro = ctk.CTkOptionMenu(
            barra, values=[_TODOS, _BANCO_POSITIVO, _BANCO_NEGATIVO, _BANCO_ZERADO],
            variable=self._var_banco_filtro, width=200,
            command=lambda valor: self._atualizar(),
        )
        self._menu_banco_filtro.grid(row=2, column=5, pady=(10, 0))

    def _montar_area_principal(self) -> None:
        area = ctk.CTkFrame(self, fg_color="transparent")
        area.grid(row=4, column=0, sticky="nsew", padx=30, pady=15)
        area.grid_rowconfigure(1, weight=1)
        area.grid_columnconfigure(0, weight=1)

        self._rotulo_bloqueio = ctk.CTkLabel(
            area, text="", text_color=("#c0392b", "#e74c3c"), anchor="w", wraplength=800,
        )
        self._rotulo_bloqueio.grid(row=0, column=0, sticky="w", pady=(0, 10))

        self._texto_visualizacao = ctk.CTkTextbox(area, state="disabled")
        self._texto_visualizacao.grid(row=1, column=0, sticky="nsew")

        linha_botoes = ctk.CTkFrame(area, fg_color="transparent")
        linha_botoes.grid(row=2, column=0, sticky="w", pady=(15, 0))

        self._botao_visualizar = ctk.CTkButton(
            linha_botoes, text="Visualizar", width=120, command=self._visualizar,
        )
        self._botao_visualizar.pack(side="left", padx=(0, 10))

        self._botao_exportar_excel = ctk.CTkButton(
            linha_botoes, text="Exportar Excel", width=140, command=self._exportar_excel,
        )
        self._botao_exportar_excel.pack(side="left", padx=(0, 10))

        self._botao_imprimir = ctk.CTkButton(
            linha_botoes, text="Imprimir", width=110, command=self._imprimir,
        )
        self._botao_imprimir.pack(side="left")

    # -- Ciclo de vida ---------------------------------------------------------

    def ao_exibir(self) -> None:
        """
        Hook padrão (Sprint 1): sempre que a tela é exibida, recarrega
        TODAS as competências persistidas (`competencias.listar()`) e
        repopula o seletor — a tela é acessível a qualquer momento pelo
        botão "Relatórios" (Cap. 12.2), não só logo após um
        processamento, e precisa refletir competências
        importadas/retomadas por outras telas nesta mesma sessão.
        """
        self._competencias = competencias.listar()
        self._rotulos_competencia = {self._rotulo_competencia(c): c for c in self._competencias}
        rotulos = list(self._rotulos_competencia.keys())
        self._menu_competencia.configure(values=rotulos or ["Nenhuma competência disponível"])
        self._var_competencia.set(self._rotulo_preferido(rotulos))
        self._selecionar_competencia(self._var_competencia.get())

    def _rotulo_competencia(self, competencia: Competencia) -> str:
        return f"{nome_mes(competencia.mes)}/{competencia.ano} — {competencia.status.value}"

    def _rotulo_preferido(self, rotulos: list[str]) -> str:
        """
        Mantém a competência já selecionada quando ainda existir na
        lista; senão prioriza a dica de pré-seleção do controlador
        (`App.competencia_atual` — a competência recém-importada ou
        retomada nesta sessão); por fim, cai para a primeira disponível.
        """
        if not rotulos:
            return "Nenhuma competência disponível"

        atual = self._var_competencia.get()
        if atual in rotulos:
            return atual

        dica = getattr(self.controlador, "competencia_atual", None)
        if dica is not None:
            rotulo_dica = self._rotulo_competencia(dica)
            if rotulo_dica in rotulos:
                return rotulo_dica

        return rotulos[0]

    def _ao_selecionar_competencia(self, rotulo: str) -> None:
        self._selecionar_competencia(rotulo)

    def selecionar_competencia(self, competencia: Competencia) -> None:
        """
        Seleção EXPLÍCITA (ao contrário da dica `App.competencia_atual`,
        que `ao_exibir()` só usa quando não há seleção anterior ainda
        válida): usada por `App._abrir()` para forçar qual competência
        aparece ao navegar para cá logo após um cálculo ou um "Abrir" na
        Tela Competências — sem isso, uma seleção anterior no dropdown
        (de uma visita anterior a esta tela) venceria a intenção de
        navegação atual.
        """
        self._competencias = competencias.listar()
        self._rotulos_competencia = {self._rotulo_competencia(c): c for c in self._competencias}
        rotulo = self._rotulo_competencia(competencia)
        self._rotulos_competencia.setdefault(rotulo, competencia)
        self._menu_competencia.configure(values=list(self._rotulos_competencia.keys()))
        self._var_competencia.set(rotulo)
        self._selecionar_competencia(rotulo)

    def _selecionar_competencia(self, rotulo: str) -> None:
        competencia_obj = self._rotulos_competencia.get(rotulo)
        self._competencia_obj = competencia_obj

        if competencia_obj is None:
            self._resultado = None
            self._arquivo_original = ""
            self._competencia = None
        else:
            self._resultado = competencia_obj.resultado
            self._arquivo_original = competencia_obj.arquivo_original
            self._competencia = (competencia_obj.mes, competencia_obj.ano)

        self._popular_filtros()
        self._atualizar()

    # -- Filtros -----------------------------------------------------------

    def _popular_filtros(self) -> None:
        if self._resultado is None:
            self._menu_funcionario.configure(values=[_TODOS])
            self._var_funcionario.set(_TODOS)
            for menu, var in (
                (self._menu_setor, self._var_setor),
                (self._menu_turno, self._var_turno),
                (self._menu_cargo, self._var_cargo),
            ):
                menu.configure(values=[_TODOS])
                var.set(_TODOS)
            return

        nomes_funcionarios = sorted(
            f.nome_completo for f in self._resultado.funcionarios_processados
        )
        self._menu_funcionario.configure(values=[_TODOS] + nomes_funcionarios)
        if self._var_funcionario.get() not in ([_TODOS] + nomes_funcionarios):
            self._var_funcionario.set(_TODOS)

        funcionarios = self._resultado.funcionarios_processados
        setores = self._nomes_unicos(self._nome_setor(f) for f in funcionarios)
        self._menu_setor.configure(values=[_TODOS] + setores)
        turnos = self._nomes_unicos(self._nome_turno(f) for f in funcionarios)
        self._menu_turno.configure(values=[_TODOS] + turnos)
        cargos = self._nomes_unicos(f.cargo for f in funcionarios if f.cargo)
        self._menu_cargo.configure(values=[_TODOS] + cargos)

    def _nomes_unicos(self, valores) -> list[str]:
        return sorted({v for v in valores if v and v != "—"})

    def _nome_setor(self, funcionario: Funcionario) -> str:
        setores = self.config_app.setores.get("setores", [])
        return next(
            (s.get("nome", "") for s in setores if s.get("id") == funcionario.setor_id), "—")

    def _nome_turno(self, funcionario: Funcionario) -> str:
        turnos = self.config_app.configuracoes.get("turnos", [])
        return next(
            (t.get("nome", "") for t in turnos if t.get("id") == funcionario.turno_id), "—")

    def _ao_alterar_modo(self) -> None:
        """Filtros de Setor/Turno/Cargo/Status só se aplicam ao modo "Todos" (Cap. 12.8)."""
        individual = self._var_funcionario.get() != _TODOS
        estado = "disabled" if individual else "normal"
        for menu in (self._menu_setor, self._menu_turno, self._menu_cargo, self._menu_status):
            menu.configure(state=estado)
        self._atualizar()

    def _resultado_filtrado(self) -> ResultadoProcessamento | None:
        """
        Compõe, em sequência, todos os filtros ativos da tela (Etapas 8/9
        v2.0): período → Funcionário individual OU Setor/Turno/Cargo/Status
        → Situação/Pendências/Horas Extras/Banco de Horas. Cada etapa parte
        do resultado da etapa anterior, então os filtros são sempre
        combináveis entre si (ex.: uma semana específica + só quem tem
        horas extras).
        """
        if self._resultado is None:
            return None

        resultado = self._resultado

        intervalo = self._intervalo_periodo_selecionado()
        if intervalo is not None:
            resultado = filtrar_por_periodo(resultado, intervalo[0], intervalo[1])

        if self._var_funcionario.get() != _TODOS:
            funcionario = next(
                (f for f in resultado.funcionarios_processados
                 if f.nome_completo == self._var_funcionario.get()),
                None,
            )
            if funcionario is not None:
                resultado = filtrar_resultado(resultado, funcionario_id=funcionario.id)
        else:
            setor_id = self._id_por_nome(
                self._var_setor.get(), self.config_app.setores.get("setores", []))
            turno_id = self._id_por_nome(
                self._var_turno.get(), self.config_app.configuracoes.get("turnos", []))
            cargo = None if self._var_cargo.get() == _TODOS else self._var_cargo.get()
            status = (
                None if self._var_status.get() == _TODOS
                else StatusFuncionario(self._var_status.get())
            )
            resultado = filtrar_resultado(
                resultado, setor_id=setor_id, turno_id=turno_id, cargo=cargo, status=status,
            )

        situacao = (
            None if self._var_situacao_filtro.get() == _TODOS
            else Situacao(self._var_situacao_filtro.get())
        )
        com_pendencia = {
            _TODOS: None, _COM_PENDENCIA: True, _SEM_PENDENCIA: False,
        }[self._var_pendencia_filtro.get()]
        com_horas_extras = {
            _TODOS: None, _COM_HORAS_EXTRAS: True, _SEM_HORAS_EXTRAS: False,
        }[self._var_extras_filtro.get()]
        banco_horas = {
            _TODOS: None, _BANCO_POSITIVO: "positivo",
            _BANCO_NEGATIVO: "negativo", _BANCO_ZERADO: "zerado",
        }[self._var_banco_filtro.get()]

        if (
            situacao is not None or com_pendencia is not None
            or com_horas_extras is not None or banco_horas is not None
        ):
            resultado = filtrar_por_atributos(
                resultado, situacao=situacao, com_pendencia=com_pendencia,
                com_horas_extras=com_horas_extras, banco_horas=banco_horas,
            )

        return resultado

    def _id_por_nome(self, nome: str, itens: list[dict]) -> str | None:
        if nome == _TODOS:
            return None
        return next((item.get("id") for item in itens if item.get("nome") == nome), None)

    # -- Atualização da tela -------------------------------------------------

    def _competencia_texto(self) -> str:
        if self._competencia is None:
            return "—"
        mes, ano = self._competencia
        return f"{nome_mes(mes)}/{ano}"

    def _atualizar(self) -> None:
        if self._resultado is None:
            self._rotulo_card_funcionarios.configure(text="—")
            self._rotulo_card_extras.configure(text="—")
            self._rotulo_card_negativas.configure(text="—")
            self._rotulo_card_pendencias.configure(text="—")
            self._rotulo_bloqueio.configure(
                text="Nenhuma competência disponível — importe uma planilha primeiro.")
            self._definir_acoes_habilitadas(False)
            return

        resultado_filtrado = self._resultado_filtrado() or self._resultado
        resumo_geral = montar_resumo_geral(resultado_filtrado, self._competencia_texto())
        self._rotulo_card_funcionarios.configure(text=str(resumo_geral.funcionarios_processados))
        self._rotulo_card_extras.configure(text=formatar_minutos(resumo_geral.horas_extras_min))
        self._rotulo_card_negativas.configure(
            text=formatar_minutos(resumo_geral.horas_negativas_min))
        self._rotulo_card_pendencias.configure(text=str(resumo_geral.total_pendencias))

        # Etapas 8/9 v2.0: o bloqueio por pendência considera apenas o
        # recorte selecionado (período/filtros), não a competência inteira
        # — relatório por período não depende do fechamento da competência.
        if existem_pendencias_abertas(resultado_filtrado):
            self._rotulo_bloqueio.configure(text=f"⚠ {MENSAGEM_BLOQUEIO}")
            self._definir_acoes_habilitadas(False)
        else:
            self._rotulo_bloqueio.configure(text="")
            self._definir_acoes_habilitadas(True)

    def _definir_acoes_habilitadas(self, habilitado: bool) -> None:
        estado = "normal" if habilitado else "disabled"
        self._botao_visualizar.configure(state=estado)
        self._botao_exportar_excel.configure(state=estado)
        self._botao_imprimir.configure(state=estado)

    # -- Ações -----------------------------------------------------------------

    def _dados_para_exportacao(self):
        resultado_filtrado = self._resultado_filtrado()
        if resultado_filtrado is None:
            return None, None
        dados = montar_dados_relatorio(
            resultado_filtrado, self.config_app, self._arquivo_original, self._competencia_texto(),
        )
        funcionario_individual = None
        if self._var_funcionario.get() != _TODOS:
            funcionario_individual = next(
                (f for f in resultado_filtrado.funcionarios_processados
                 if f.nome_completo == self._var_funcionario.get()),
                None,
            )
        return dados, funcionario_individual

    def _gerar_arquivo(self, exportador) -> Path | None:
        resultado_filtrado = self._resultado_filtrado()
        if resultado_filtrado is None or existem_pendencias_abertas(resultado_filtrado):
            messagebox.showwarning("Relatório bloqueado", MENSAGEM_BLOQUEIO)
            return None

        dados, funcionario_individual = self._dados_para_exportacao()
        if dados is None:
            return None

        nome_base = (
            f"Relatorio_Horas_{funcionario_individual.nome_completo}"
            if funcionario_individual is not None
            else "Relatorio_Horas"
        )
        caminho = caminho_historico(
            self.config_app, self._competencia or (0, 0), nome_base,
        )

        try:
            if funcionario_individual is not None:
                caminho_final = exportador.exportar_individual(
                    dados, funcionario_individual, caminho)
            else:
                caminho_final = exportador.exportar_geral(dados, caminho)
        except RelatorioBloqueadoError:
            # Defesa em profundidade (Cap. 9.1/11.11): a checagem já feita
            # acima cobre o caso comum; esta captura só protege contra uma
            # pendência que tenha surgido entre a checagem e a geração.
            messagebox.showwarning("Relatório bloqueado", MENSAGEM_BLOQUEIO)
            return None

        self._marcar_relatorio_gerado()
        return caminho_final

    def _marcar_relatorio_gerado(self) -> None:
        """
        Depois de qualquer exportação bem-sucedida (Visualizar, Exportar
        Excel ou Imprimir — as três passam por `_gerar_arquivo()`),
        marca a competência selecionada como `relatorio_gerado=True` e
        avança seu status para `RELATORIO_GERADO`, exceto se já estiver
        `ARQUIVADA` (arquivar não impede reemitir relatório, mas nunca
        desarquiva automaticamente — decisão confirmada com o usuário).
        """
        if self._competencia_obj is None:
            return
        self._competencia_obj.relatorio_gerado = True
        if self._competencia_obj.status != StatusCompetencia.ARQUIVADA:
            self._competencia_obj.status = StatusCompetencia.RELATORIO_GERADO
        competencias.salvar_competencia(self._competencia_obj)

        rotulos = list(self._rotulos_competencia.keys())
        self._rotulos_competencia = {self._rotulo_competencia(c): c for c in self._competencias}
        self._menu_competencia.configure(values=list(self._rotulos_competencia.keys()) or rotulos)
        self._var_competencia.set(self._rotulo_competencia(self._competencia_obj))

    def _visualizar(self) -> None:
        caminho = self._gerar_arquivo(self._exportador_excel)
        if caminho is None:
            return
        self._preencher_visualizacao(caminho)
        self.controlador.definir_status(f"Relatório visualizado: {caminho.name}")

    def _preencher_visualizacao(self, caminho: Path) -> None:
        """Resumo textual simples do relatório gerado, direto na tela (sem abrir outro programa)."""
        self._texto_visualizacao.configure(state="normal")
        self._texto_visualizacao.delete("1.0", "end")
        dados, funcionario_individual = self._dados_para_exportacao()
        if dados is not None:
            linhas = [f"Arquivo gerado: {caminho}", ""]
            if funcionario_individual is not None:
                linhas.append(f"Relatório Individual — {funcionario_individual.nome_completo}")
            else:
                resumo_geral = dados.resumo_geral
                linhas.append("Relatório Geral")
                linhas.append(f"Funcionários: {resumo_geral.funcionarios_processados}")
                linhas.append(
                    f"Horas Previstas: {formatar_minutos(resumo_geral.horas_previstas_min)}")
                linhas.append(
                    f"Horas Trabalhadas: {formatar_minutos(resumo_geral.horas_trabalhadas_min)}")
                linhas.append(
                    f"Horas Extras: {formatar_minutos(resumo_geral.horas_extras_min)}")
                linhas.append(
                    f"Horas Negativas: {formatar_minutos(resumo_geral.horas_negativas_min)}")
                linhas.append(
                    f"Saldo Geral: {formatar_minutos(resumo_geral.saldo_geral_min)}")
            self._texto_visualizacao.insert("1.0", "\n".join(linhas))
        self._texto_visualizacao.configure(state="disabled")

    def _exportar_excel(self) -> None:
        caminho = self._gerar_arquivo(self._exportador_excel)
        if caminho is None:
            return
        messagebox.showinfo("Relatório exportado", f"Relatório salvo em:\n{caminho}")
        self.controlador.definir_status(f"Relatório exportado: {caminho.name}")

    def _imprimir(self) -> None:
        caminho = self._gerar_arquivo(self._exportador_excel)
        if caminho is None:
            return
        try:
            os.startfile(str(caminho), "print")  # type: ignore[attr-defined]
            self.controlador.definir_status(f"Enviado para impressão: {caminho.name}")
        except OSError as erro:
            log.error("Falha ao imprimir relatório: %s", erro)
            messagebox.showerror(
                "Não foi possível imprimir",
                "Não foi possível enviar o relatório para impressão automaticamente. "
                f"O arquivo foi gerado em:\n{caminho}",
            )
