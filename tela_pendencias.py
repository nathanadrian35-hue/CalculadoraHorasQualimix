"""
tela_pendencias.py
-------------------
Tela de Pendências (Cap. 9.3/9.4/9.5/9.6) — última etapa do fluxo de
importação nesta sprint, alcançada automaticamente depois do Motor de
Cálculo (Cap. 6) processar os funcionários do lote.

Permite, por pendência: corrigir as batidas do dia (Cap. 9.4), escolher
uma Justificativa (Cap. 9.6) e registrar Observações — "Salvar"
recalcula imediatamente apenas aquele dia (Cap. 10.7, via
`calculadora.recalcular_dia`), nunca a planilha inteira. Nenhuma
lógica de cálculo é duplicada aqui — só chama o Motor de Cálculo já
existente.

Sprint 4.1 (homologação): a lista é paginada, pesquisável por nome e
filtrável por tipo, e usa um POOL FIXO de `_TAMANHO_PAGINA` linhas
(`_LinhaPendencia`) criadas uma única vez e reaproveitadas — nunca
destruídas/recriadas a cada troca de página/filtro/correção. Isso
resolve dois problemas observados com centenas de pendências: o limite
de menus nativos do Windows (cada linha tem um `CTkOptionMenu`) e o
custo real de criar/destruir widgets do CustomTkinter repetidamente
(medido em torno de vários segundos para 25 linhas). Puramente uma
mudança de interface — nenhuma regra de cálculo foi alterada.

Não é uma das telas fixas de navegação (Cap. 12): é alcançada apenas
programaticamente, via `App.iniciar_tela_pendencias()`, no mesmo
espírito do Painel de Revisão (Cap. 5.4).
"""

from __future__ import annotations

import tkinter as tk
from dataclasses import dataclass, field
from datetime import date, datetime
from tkinter import messagebox
from typing import Callable

import customtkinter as ctk

import competencias
from calculadora import recalcular_dia
from config import Config, turno_de_dict
from constantes import Justificativa, StatusFuncionario, TipoPendencia, formatar_minutos
from logger import get_logger
from modelos import (
    Batida,
    Competencia,
    ContextoCalculo,
    DiaTrabalho,
    Funcionario,
    Pendencia,
    ResultadoProcessamento,
)
from tela_configuracoes import _horario_para_texto, _texto_para_horario

log = get_logger()

_SEM_JUSTIFICATIVA = "— Nenhuma —"
_ROTULOS_HORARIO = ("Entrada", "Saída Almoço", "Retorno Almoço", "Saída")
_TODOS_OS_TIPOS = "Todos os tipos"

# Pendências cuja correção envolve digitar batidas (Cap. 9.4) — todas
# exceto a de Turno, que se resolve na tela Funcionários (Cap. 5.13).
_TIPOS_COM_CORRECAO_DE_BATIDA = frozenset({
    TipoPendencia.SEM_BATIDAS,
    TipoPendencia.UMA_BATIDA,
    TipoPendencia.DUAS_BATIDAS,
    TipoPendencia.TRES_BATIDAS,
    TipoPendencia.MAIS_DE_QUATRO,
    TipoPendencia.HORARIO_INCONSISTENTE,
})


# ---------------------------------------------------------------------------
# Linha de uma pendência (widget reaproveitável — Sprint 4.1)
# ---------------------------------------------------------------------------

class _LinhaPendencia(ctk.CTkFrame):
    """
    Uma linha reaproveitável do pool da Tela de Pendências (Sprint 4.1):
    todos os widgets são construídos uma única vez em `__init__` — os
    dois blocos possíveis (correção de batida vs. aviso de Turno) já
    existem sempre, alternados via `grid()`/`grid_remove()` (mesmo
    padrão de `_GrupoJornadaOpcional` em tela_configuracoes.py).
    `vincular()` é quem troca qual pendência esta linha exibe, sem
    recriar nada.
    """

    def __init__(
        self,
        master,
        ao_salvar: Callable[["_LinhaPendencia"], None],
        ao_ir_funcionarios: Callable[[], None],
    ) -> None:
        super().__init__(master, corner_radius=8, border_width=1)
        self.pendencia: Pendencia | None = None
        self.dia: DiaTrabalho | None = None
        self._ao_salvar = ao_salvar

        self.grid_columnconfigure(1, weight=1)

        self._rotulo_cabecalho = ctk.CTkLabel(
            self, text="", font=ctk.CTkFont(weight="bold"), anchor="w")
        self._rotulo_cabecalho.grid(
            row=0, column=0, columnspan=3, sticky="w", padx=12, pady=(10, 2))

        self._rotulo_descricao = ctk.CTkLabel(
            self, text="", anchor="w", text_color=("gray60", "gray60"))
        self._rotulo_descricao.grid(row=1, column=0, columnspan=3, sticky="w", padx=12, pady=(0, 8))

        # -- Bloco de correção de batida (Cap. 9.4) --
        self._frame_batidas = ctk.CTkFrame(self, fg_color="transparent")
        self._frame_batidas.grid(row=2, column=0, columnspan=3, sticky="w")
        self._entries_horario: list[ctk.CTkEntry] = []
        for indice, rotulo in enumerate(_ROTULOS_HORARIO):
            ctk.CTkLabel(self._frame_batidas, text=rotulo).grid(
                row=indice, column=0, sticky="w", padx=(12, 5), pady=2)
            entry = ctk.CTkEntry(self._frame_batidas, placeholder_text="HH:MM", width=90)
            entry.grid(row=indice, column=1, sticky="w", padx=(0, 12), pady=2)
            self._entries_horario.append(entry)

        # -- Bloco de aviso de Turno não definido (Cap. 5.13) --
        self._frame_turno = ctk.CTkFrame(self, fg_color="transparent")
        self._frame_turno.grid(row=2, column=0, columnspan=3, sticky="w")
        ctk.CTkLabel(
            self._frame_turno,
            text="Defina um Turno válido para este funcionário na tela Funcionários.",
            anchor="w",
        ).grid(row=0, column=0, sticky="w", padx=12)
        ctk.CTkButton(
            self._frame_turno, text="Ir para Funcionários", width=160,
            command=lambda: ao_ir_funcionarios(),
        ).grid(row=0, column=1, padx=12, pady=6)

        ctk.CTkLabel(self, text="Justificativa").grid(
            row=3, column=0, sticky="w", padx=(12, 5), pady=2)
        valores_justificativa = [_SEM_JUSTIFICATIVA] + [j.value for j in Justificativa]
        self._var_justificativa = tk.StringVar(value=_SEM_JUSTIFICATIVA)
        ctk.CTkOptionMenu(
            self, values=valores_justificativa, variable=self._var_justificativa, width=200,
        ).grid(row=3, column=1, sticky="w", padx=(0, 12), pady=2)

        ctk.CTkLabel(self, text="Observações").grid(
            row=4, column=0, sticky="w", padx=(12, 5), pady=2)
        self._entry_observacoes = ctk.CTkEntry(self, placeholder_text="Observações (opcional)")
        self._entry_observacoes.grid(
            row=4, column=1, columnspan=2, sticky="ew", padx=(0, 12), pady=2)

        self._rotulo_resultado = ctk.CTkLabel(self, text="", anchor="w")
        self._rotulo_resultado.grid(row=5, column=0, columnspan=3, sticky="w", padx=12, pady=(2, 4))

        self._botao_salvar = ctk.CTkButton(
            self, text="Salvar", width=100, command=lambda: self._ao_salvar(self))
        self._botao_salvar.grid(row=6, column=0, sticky="w", padx=12, pady=(4, 10))

    # -- Vínculo com uma pendência (Sprint 4.1: reaproveitamento) ------------

    def vincular(self, pendencia: Pendencia, dia: DiaTrabalho | None) -> None:
        """Rebind desta linha do pool para (possivelmente outra) pendência/dia."""
        self.pendencia = pendencia
        self.dia = dia

        cabecalho = pendencia.nome_funcionario
        if pendencia.data is not None:
            cabecalho += f" — {pendencia.data.strftime('%d/%m/%Y')}"
        self._rotulo_cabecalho.configure(text=cabecalho)
        self._rotulo_descricao.configure(text=f"{pendencia.tipo.value} — {pendencia.descricao}")

        tem_correcao_de_batida = pendencia.tipo in _TIPOS_COM_CORRECAO_DE_BATIDA
        if tem_correcao_de_batida:
            self._frame_turno.grid_remove()
            self._frame_batidas.grid()
            self._botao_salvar.grid()
            batidas_atuais = dia.batidas if dia is not None else []
            for indice, entry in enumerate(self._entries_horario):
                entry.delete(0, "end")
                if indice < len(batidas_atuais):
                    entry.insert(0, _horario_para_texto(batidas_atuais[indice].horario))
        else:
            self._frame_batidas.grid_remove()
            self._frame_turno.grid()
            self._botao_salvar.grid_remove()

        self._var_justificativa.set(pendencia.justificativa or _SEM_JUSTIFICATIVA)
        self._entry_observacoes.delete(0, "end")
        self._entry_observacoes.insert(0, pendencia.observacoes)

        self._atualizar_rotulo_resultado()

    # -- Acesso aos dados ------------------------------------------------

    def horarios_texto(self) -> list[str]:
        return [entry.get().strip() for entry in self._entries_horario]

    def justificativa_selecionada(self) -> str:
        valor = self._var_justificativa.get()
        return "" if valor == _SEM_JUSTIFICATIVA else valor

    def observacoes(self) -> str:
        return self._entry_observacoes.get().strip()

    def _atualizar_rotulo_resultado(self) -> None:
        if self.dia is None:
            self._rotulo_resultado.configure(text="")
            return
        resultado = self.dia.resultado
        self._rotulo_resultado.configure(text=(
            f"Trabalhadas: {formatar_minutos(resultado.horas_trabalhadas_min)}   "
            f"Saldo: {formatar_minutos(resultado.saldo_min)}   "
            f"Extras: {formatar_minutos(resultado.horas_extras_min)}   "
            f"Negativas: {formatar_minutos(resultado.horas_negativas_min)}"
        ))


# ---------------------------------------------------------------------------
# Aplicar Justificativa por Período (Cap. 9.8)
# ---------------------------------------------------------------------------

def _texto_para_data(texto: str) -> date | None:
    """Converte "DD/MM/AAAA" em `date`. Retorna None se vazio/inválido."""
    texto = texto.strip()
    if not texto:
        return None
    try:
        return datetime.strptime(texto, "%d/%m/%Y").date()
    except ValueError:
        return None


@dataclass
class _AnaliseJustificativaPeriodo:
    """
    Resultado de analisar um período (Cap. 9.8) para um funcionário,
    antes de qualquer alteração — puramente uma classificação dos dias
    já calculados pelo Motor, nenhum valor é derivado de novo.
    """

    funcionario: Funcionario
    justificativa: str
    data_inicial: date
    data_final: date
    dias_no_periodo: list[DiaTrabalho] = field(default_factory=list)
    resolvidas: list[DiaTrabalho] = field(default_factory=list)
    mesma_justificativa: list[DiaTrabalho] = field(default_factory=list)
    conflitos: list[DiaTrabalho] = field(default_factory=list)
    sem_alteracao: list[DiaTrabalho] = field(default_factory=list)


class _DialogoJustificativaPeriodo(ctk.CTkToplevel):
    """
    "Aplicar Justificativa por Período" (Cap. 9.8): formulário →
    análise do período → tratamento de conflitos (Cap. 9.8.1) →
    confirmação inteligente (Cap. 9.8.2) → aplicação. Quando a
    Justificativa é "Desligamento", pergunta também sobre inativar o
    funcionário (Cap. 9.8.3). Toda alteração de dia reaproveita
    `calculadora.recalcular_dia` via `construir_contexto` (a mesma
    função que a correção individual da Tela de Pendências já usa) —
    nenhuma regra de cálculo nova.
    """

    def __init__(
        self,
        master,
        config: Config,
        funcionarios: list[Funcionario],
        construir_contexto: Callable[[Funcionario], ContextoCalculo | None],
        ao_confirmar: Callable[[Funcionario, str, list[DiaTrabalho]], None],
    ) -> None:
        super().__init__(master)
        self.title("Aplicar Justificativa por Período")
        self.geometry("540x560")
        self.transient(master)
        self.grab_set()

        self._config = config
        self._funcionarios = sorted(funcionarios, key=lambda f: f.nome_completo)
        self._construir_contexto = construir_contexto
        self._ao_confirmar = ao_confirmar
        self._analise: _AnaliseJustificativaPeriodo | None = None
        self._estrategia_conflito = tk.StringVar(value="substituir")

        self.grid_columnconfigure(0, weight=1)

        self._montar_formulario()
        self._frame_resultado = ctk.CTkFrame(self, fg_color="transparent")
        self._frame_resultado.grid(row=1, column=0, sticky="nsew", padx=20, pady=(10, 20))

    # -- Formulário (Cap. 9.8) ------------------------------------------------

    def _montar_formulario(self) -> None:
        formulario = ctk.CTkFrame(self, fg_color="transparent")
        formulario.grid(row=0, column=0, sticky="ew", padx=20, pady=(20, 0))
        formulario.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(formulario, text="Funcionário").grid(row=0, column=0, sticky="w", pady=4)
        nomes = [f.nome_completo for f in self._funcionarios]
        self._var_funcionario = tk.StringVar(value=nomes[0] if nomes else "")
        ctk.CTkOptionMenu(
            formulario, values=nomes or ["—"], variable=self._var_funcionario, width=280,
        ).grid(row=0, column=1, sticky="ew", pady=4)

        ctk.CTkLabel(formulario, text="Justificativa").grid(row=1, column=0, sticky="w", pady=4)
        valores_justificativa = [j.value for j in Justificativa]
        self._var_justificativa = tk.StringVar(value=valores_justificativa[0])
        ctk.CTkOptionMenu(
            formulario, values=valores_justificativa, variable=self._var_justificativa,
            width=280, command=self._ao_alterar_justificativa,
        ).grid(row=1, column=1, sticky="ew", pady=4)

        ctk.CTkLabel(formulario, text="Data Inicial").grid(row=2, column=0, sticky="w", pady=4)
        self._entry_data_inicial = ctk.CTkEntry(formulario, placeholder_text="DD/MM/AAAA")
        self._entry_data_inicial.grid(row=2, column=1, sticky="ew", pady=4)

        ctk.CTkLabel(formulario, text="Data Final").grid(row=3, column=0, sticky="w", pady=4)
        self._entry_data_final = ctk.CTkEntry(formulario, placeholder_text="DD/MM/AAAA")
        self._entry_data_final.grid(row=3, column=1, sticky="ew", pady=4)

        self._rotulo_erro = ctk.CTkLabel(
            formulario, text="", text_color=("#c0392b", "#e74c3c"), anchor="w")
        self._rotulo_erro.grid(row=4, column=0, columnspan=2, sticky="ew", pady=(4, 0))

        ctk.CTkButton(
            formulario, text="Analisar Período", command=self._analisar,
        ).grid(row=5, column=0, columnspan=2, sticky="w", pady=(10, 0))

    def _ao_alterar_justificativa(self, valor: str) -> None:
        """Desligamento Inteligente (Cap. 9.8.3): Data Final vira o último dia da competência."""
        if valor != Justificativa.DESLIGAMENTO.value:
            return
        funcionario = self._funcionario_selecionado()
        if funcionario is None or not funcionario.dias:
            return
        ultimo_dia = max(dia.data for dia in funcionario.dias)
        self._entry_data_final.delete(0, "end")
        self._entry_data_final.insert(0, ultimo_dia.strftime("%d/%m/%Y"))

    def _funcionario_selecionado(self) -> Funcionario | None:
        nome = self._var_funcionario.get()
        return next((f for f in self._funcionarios if f.nome_completo == nome), None)

    # -- Análise do período (Cap. 9.8) ----------------------------------------

    def _analisar(self) -> None:
        funcionario = self._funcionario_selecionado()
        justificativa = self._var_justificativa.get()
        data_inicial = _texto_para_data(self._entry_data_inicial.get())
        data_final = _texto_para_data(self._entry_data_final.get())

        erro = self._validar(funcionario, justificativa, data_inicial, data_final)
        if erro:
            self._rotulo_erro.configure(text=erro)
            return
        self._rotulo_erro.configure(text="")
        assert funcionario is not None and data_inicial is not None and data_final is not None

        dias_no_periodo = sorted(
            (dia for dia in funcionario.dias if data_inicial <= dia.data <= data_final),
            key=lambda d: d.data,
        )
        resolvidas, mesma_justificativa, conflitos, sem_alteracao = [], [], [], []
        for dia in dias_no_periodo:
            if dia.pendencia is None:
                sem_alteracao.append(dia)
            elif not dia.pendencia.justificativa and not dia.pendencia.resolvida:
                # Só entra aqui uma pendência REALMENTE em aberto (Cap. 9.1).
                # Um dia já corrigido por batida (resolvida=True) mas sem
                # justificativa preenchida não deve ser tocado — o registro
                # de pendência (Cap. 9.5) é mantido mesmo depois de
                # corrigido, então "tem pendência sem justificativa" sozinho
                # não distingue "ainda pendente" de "já corrigido".
                resolvidas.append(dia)
            elif not dia.pendencia.justificativa:
                sem_alteracao.append(dia)
            elif dia.pendencia.justificativa == justificativa:
                mesma_justificativa.append(dia)
            else:
                conflitos.append(dia)

        self._analise = _AnaliseJustificativaPeriodo(
            funcionario=funcionario, justificativa=justificativa,
            data_inicial=data_inicial, data_final=data_final,
            dias_no_periodo=dias_no_periodo, resolvidas=resolvidas,
            mesma_justificativa=mesma_justificativa, conflitos=conflitos,
            sem_alteracao=sem_alteracao,
        )
        self._exibir_resultado()

    def _validar(
        self, funcionario: Funcionario | None, justificativa: str,
        data_inicial: date | None, data_final: date | None,
    ) -> str:
        if funcionario is None:
            return "Selecione um funcionário."
        if not justificativa:
            return "Selecione uma justificativa."
        if data_inicial is None or data_final is None:
            return "Informe Data Inicial e Data Final válidas (DD/MM/AAAA)."
        if data_inicial > data_final:
            return "A Data Inicial deve ser anterior (ou igual) à Data Final."
        return ""

    # -- Tratamento de conflitos + Confirmação Inteligente (Cap. 9.8.1/9.8.2) --

    def _exibir_resultado(self) -> None:
        for widget in self._frame_resultado.winfo_children():
            widget.destroy()
        analise = self._analise
        if analise is None:
            return

        if analise.conflitos:
            ctk.CTkLabel(
                self._frame_resultado,
                text="Este período contém dias já justificados com outra justificativa.",
                text_color=("#a04000", "#f39c12"), anchor="w", justify="left", wraplength=480,
            ).pack(anchor="w", pady=(0, 5))
            for valor, texto in (
                ("substituir", "Substituir justificativas existentes"),
                ("manter", "Manter justificativas existentes"),
                ("perguntar", "Perguntar conflito por conflito"),
            ):
                ctk.CTkRadioButton(
                    self._frame_resultado, text=texto,
                    variable=self._estrategia_conflito, value=valor,
                ).pack(anchor="w", pady=2)

        inativar_texto = "—"
        if analise.justificativa == Justificativa.DESLIGAMENTO.value:
            inativar_texto = "Será perguntado ao confirmar"

        ctk.CTkLabel(
            self._frame_resultado, text="Resumo da operação",
            font=ctk.CTkFont(size=14, weight="bold"), anchor="w",
        ).pack(anchor="w", pady=(10, 4))

        resumo = (
            f"Funcionário: {analise.funcionario.nome_completo}\n"
            f"Justificativa: {analise.justificativa}\n"
            f"Período: {analise.data_inicial.strftime('%d/%m/%Y')} até "
            f"{analise.data_final.strftime('%d/%m/%Y')}\n\n"
            f"Dias analisados: {len(analise.dias_no_periodo)}\n"
            f"Pendências que serão resolvidas: {len(analise.resolvidas)}\n"
            f"Dias já justificados: {len(analise.mesma_justificativa) + len(analise.conflitos)}\n"
            f"Dias sem alteração: {len(analise.sem_alteracao)}\n"
            f"Conflitos encontrados: {len(analise.conflitos)}\n"
            f"Funcionário será inativado: {inativar_texto}"
        )
        ctk.CTkLabel(self._frame_resultado, text=resumo, anchor="w", justify="left").pack(
            anchor="w")

        linha_botoes = ctk.CTkFrame(self._frame_resultado, fg_color="transparent")
        linha_botoes.pack(anchor="w", pady=(15, 0))
        ctk.CTkButton(linha_botoes, text="Confirmar", command=self._confirmar).pack(
            side="left", padx=(0, 10))
        ctk.CTkButton(
            linha_botoes, text="Cancelar", fg_color="transparent", border_width=1,
            command=self.destroy,
        ).pack(side="left")

    # -- Aplicação (Cap. 9.8.2/9.8.3) -----------------------------------------

    def _confirmar(self) -> None:
        analise = self._analise
        if analise is None:
            return

        dias_para_aplicar = list(analise.resolvidas)
        estrategia = self._estrategia_conflito.get()
        if estrategia == "substituir":
            dias_para_aplicar += analise.conflitos
        elif estrategia == "perguntar":
            for dia in analise.conflitos:
                justificativa_atual = dia.pendencia.justificativa if dia.pendencia else ""
                pergunta = (
                    f'O dia {dia.data.strftime("%d/%m/%Y")} já está justificado como '
                    f'"{justificativa_atual}". Substituir por "{analise.justificativa}"?'
                )
                if messagebox.askyesno("Conflito encontrado", pergunta):
                    dias_para_aplicar.append(dia)
        # estrategia == "manter": os conflitos ficam de fora, nada a adicionar

        contexto = self._construir_contexto(analise.funcionario)
        for dia in dias_para_aplicar:
            if dia.pendencia is not None:
                dia.pendencia.justificativa = analise.justificativa
            if contexto is not None:
                recalcular_dia(dia, contexto)
        if dias_para_aplicar:
            log.info(
                'Justificativa "%s" aplicada por período a "%s": %d dia(s) entre %s e %s.',
                analise.justificativa, analise.funcionario.nome_completo,
                len(dias_para_aplicar), analise.data_inicial.strftime("%d/%m/%Y"),
                analise.data_final.strftime("%d/%m/%Y"),
            )

        if analise.justificativa == Justificativa.DESLIGAMENTO.value:
            inativar = messagebox.askyesno(
                "Funcionário desligado",
                "O funcionário será desligado.\n\nDeseja também marcá-lo como Inativo?",
            )
            if inativar:
                self._marcar_inativo(analise.funcionario)

        self.destroy()
        self._ao_confirmar(analise.funcionario, analise.justificativa, dias_para_aplicar)

    def _marcar_inativo(self, funcionario: Funcionario) -> None:
        """Desligamento Inteligente (Cap. 9.8.3): marca Status = Inativo e persiste no cadastro."""
        funcionario.status = StatusFuncionario.INATIVO
        for dados in self._config.funcionarios.get("funcionarios", []):
            if dados.get("id") == funcionario.id:
                dados["status"] = StatusFuncionario.INATIVO.value
                break
        self._config.salvar_funcionarios()
        log.info('Funcionário "%s" marcado como Inativo (Desligamento).', funcionario.nome_completo)


# ---------------------------------------------------------------------------
# Tela de Pendências
# ---------------------------------------------------------------------------

class TelaPendencias(ctk.CTkFrame):
    """
    Tela de Pendências (Cap. 9.3) — visualizar, corrigir, justificar e
    recalcular. Escalável (Sprint 4.1): pool fixo de `_TAMANHO_PAGINA`
    linhas reaproveitadas, paginação, pesquisa por nome e filtro por
    tipo — nunca cria/destrói widgets a cada troca de página.
    """

    _TAMANHO_PAGINA = 25

    def __init__(self, master, controlador, config: Config) -> None:
        super().__init__(master, corner_radius=0)
        self.controlador = controlador
        self.config_app = config
        self._competencia: Competencia | None = None
        self._resultado: ResultadoProcessamento | None = None
        self._funcionarios_por_id: dict[str, Funcionario] = {}
        self._pagina_atual = 0
        self._pool: list[_LinhaPendencia] = []

        self.grid_rowconfigure(2, weight=1)
        self.grid_columnconfigure(0, weight=1)

        self._montar_cabecalho()
        self._montar_barra_ferramentas()
        self._montar_lista()
        self._montar_rodape_paginacao()

    def _montar_cabecalho(self) -> None:
        cabecalho = ctk.CTkFrame(self, corner_radius=0, height=70)
        cabecalho.grid(row=0, column=0, sticky="ew")
        cabecalho.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(
            cabecalho, text="Pendências", font=ctk.CTkFont(size=20, weight="bold"),
        ).grid(row=0, column=0, sticky="w", padx=15, pady=15)

        self._rotulo_contador = ctk.CTkLabel(
            cabecalho, text="", font=ctk.CTkFont(size=13), text_color=("gray60", "gray60"),
        )
        self._rotulo_contador.grid(row=0, column=1, sticky="w", padx=15)

        ctk.CTkButton(
            cabecalho, text="Concluir", width=110, command=self._concluir,
        ).grid(row=0, column=2, padx=15, pady=15)

    def _montar_barra_ferramentas(self) -> None:
        """Pesquisa por nome + filtro por tipo (Sprint 4.1) — reduzem a lista antes de paginar."""
        barra = ctk.CTkFrame(self, fg_color="transparent")
        barra.grid(row=1, column=0, sticky="ew", padx=30, pady=(15, 0))
        barra.grid_columnconfigure(0, weight=1)

        self._entry_busca = ctk.CTkEntry(barra, placeholder_text="Pesquisar por funcionário...")
        self._entry_busca.grid(row=0, column=0, sticky="ew", padx=(0, 10))
        self._entry_busca.bind("<KeyRelease>", lambda evento: self._ao_alterar_filtro())

        valores_tipo = [_TODOS_OS_TIPOS] + [tipo.value for tipo in TipoPendencia]
        self._var_filtro_tipo = tk.StringVar(value=_TODOS_OS_TIPOS)
        ctk.CTkOptionMenu(
            barra, values=valores_tipo, variable=self._var_filtro_tipo, width=220,
            command=lambda valor: self._ao_alterar_filtro(),
        ).grid(row=0, column=1, padx=(0, 10))

        ctk.CTkButton(
            barra, text="Aplicar Justificativa por Período", width=230,
            command=self._abrir_dialogo_justificativa_periodo,
        ).grid(row=0, column=2)

    def _montar_lista(self) -> None:
        """
        Cria o pool fixo de `_TAMANHO_PAGINA` linhas UMA ÚNICA VEZ
        (Sprint 4.1) — `_atualizar_lista()` só troca o conteúdo de cada
        uma via `vincular()`, nunca cria/destrói widgets depois disso.
        """
        self._scroll_pendencias = ctk.CTkScrollableFrame(self, fg_color="transparent")
        self._scroll_pendencias.grid(row=2, column=0, sticky="nsew", padx=30, pady=15)

        self._rotulo_vazio = ctk.CTkLabel(
            self._scroll_pendencias, text="", text_color=("gray60", "gray60"))

        self._pool = [
            _LinhaPendencia(
                self._scroll_pendencias,
                ao_salvar=self._salvar_correcao,
                ao_ir_funcionarios=self._ir_para_funcionarios,
            )
            for _ in range(self._TAMANHO_PAGINA)
        ]

    def _montar_rodape_paginacao(self) -> None:
        rodape = ctk.CTkFrame(self, fg_color="transparent")
        rodape.grid(row=3, column=0, sticky="ew", padx=30, pady=(0, 15))
        rodape.grid_columnconfigure(1, weight=1)

        self._botao_pagina_anterior = ctk.CTkButton(
            rodape, text="◀ Anterior", width=110, fg_color="transparent", border_width=1,
            command=self._pagina_anterior,
        )
        self._botao_pagina_anterior.grid(row=0, column=0, sticky="w")

        self._rotulo_pagina = ctk.CTkLabel(
            rodape, text="", font=ctk.CTkFont(size=12), text_color=("gray60", "gray60"),
        )
        self._rotulo_pagina.grid(row=0, column=1)

        self._botao_pagina_proxima = ctk.CTkButton(
            rodape, text="Próxima ▶", width=110, fg_color="transparent", border_width=1,
            command=self._pagina_proxima,
        )
        self._botao_pagina_proxima.grid(row=0, column=2, sticky="e")

    # -- Ponto de entrada público ------------------------------------------

    def iniciar(self, competencia: Competencia) -> None:
        """
        Recebe a Competência (gerenciamento de múltiplas competências —
        já persistida, com o resultado do Motor de Cálculo, Cap. 6) e
        exibe a lista de pendências. Cada correção salva daqui em diante
        persiste imediatamente de volta na mesma Competência
        (`_persistir()`), para que fechar o sistema no meio das
        pendências nunca perca o que já foi corrigido/justificado.
        """
        self._competencia = competencia
        self._resultado = competencia.resultado
        self._funcionarios_por_id = {
            f.id: f for f in competencia.resultado.funcionarios_processados
        }
        self._entry_busca.delete(0, "end")
        self._var_filtro_tipo.set(_TODOS_OS_TIPOS)
        self._pagina_atual = 0
        self._atualizar_lista()

    def ao_exibir(self) -> None:
        """Hook padrão (Sprint 1): mantém a lista em dia se a tela for revisitada."""
        self._atualizar_lista()

    # -- Pesquisa, filtro e paginação (Sprint 4.1) ---------------------------

    def _pendencias_filtradas(self) -> list[Pendencia]:
        """Aplica pesquisa por nome + filtro por tipo sobre as pendências ainda em aberto."""
        if self._resultado is None:
            return []

        termo = self._entry_busca.get().strip().lower()
        tipo_selecionado = self._var_filtro_tipo.get()

        pendencias = [p for p in self._resultado.pendencias if not p.resolvida]
        if termo:
            pendencias = [p for p in pendencias if termo in p.nome_funcionario.lower()]
        if tipo_selecionado != _TODOS_OS_TIPOS:
            pendencias = [p for p in pendencias if p.tipo.value == tipo_selecionado]
        return pendencias

    def _ao_alterar_filtro(self) -> None:
        self._pagina_atual = 0
        self._atualizar_lista()

    def _pagina_anterior(self) -> None:
        if self._pagina_atual > 0:
            self._pagina_atual -= 1
            self._atualizar_lista()

    def _pagina_proxima(self) -> None:
        self._pagina_atual += 1
        self._atualizar_lista()

    # -- Lista de pendências (reaproveita o pool, nunca recria) -------------

    def _atualizar_lista(self) -> None:
        if self._resultado is None:
            self._rotulo_contador.configure(text="")
            self._rotulo_pagina.configure(text="")
            self._botao_pagina_anterior.configure(state="disabled")
            self._botao_pagina_proxima.configure(state="disabled")
            for linha in self._pool:
                linha.pack_forget()
            self._rotulo_vazio.pack_forget()
            return

        total_abertas = sum(1 for p in self._resultado.pendencias if not p.resolvida)
        filtradas = self._pendencias_filtradas()
        total_filtradas = len(filtradas)

        total_paginas = max(1, -(-total_filtradas // self._TAMANHO_PAGINA))  # ceil
        self._pagina_atual = max(0, min(self._pagina_atual, total_paginas - 1))

        inicio = self._pagina_atual * self._TAMANHO_PAGINA
        pagina = filtradas[inicio:inicio + self._TAMANHO_PAGINA]

        if total_filtradas == total_abertas:
            self._rotulo_contador.configure(text=f"{total_abertas} pendência(s) em aberto")
        else:
            self._rotulo_contador.configure(
                text=f"{total_filtradas} de {total_abertas} pendência(s) em aberto (filtradas)")

        self._rotulo_pagina.configure(text=f"Página {self._pagina_atual + 1} de {total_paginas}")
        self._botao_pagina_anterior.configure(
            state="normal" if self._pagina_atual > 0 else "disabled")
        self._botao_pagina_proxima.configure(
            state="normal" if self._pagina_atual < total_paginas - 1 else "disabled")

        # Reordena sempre do zero (forget + pack, nunca destroy/create) —
        # barato, e garante a ordem correta mesmo trocando de página/filtro.
        for linha in self._pool:
            linha.pack_forget()
        self._rotulo_vazio.pack_forget()

        if not pagina:
            self._rotulo_vazio.configure(
                text="Nenhuma pendência em aberto." if total_abertas == 0
                else "Nenhuma pendência encontrada com esse filtro."
            )
            self._rotulo_vazio.pack(pady=20)
            return

        for linha, pendencia in zip(self._pool, pagina):
            funcionario = self._funcionarios_por_id.get(pendencia.id_funcionario)
            dia = self._localizar_dia(funcionario, pendencia.data)
            linha.vincular(pendencia, dia)
            linha.pack(fill="x", pady=4)

    def _localizar_dia(
        self, funcionario: Funcionario | None, data: date | None,
    ) -> DiaTrabalho | None:
        if funcionario is None or data is None:
            return None
        return next((dia for dia in funcionario.dias if dia.data == data), None)

    def _ir_para_funcionarios(self) -> None:
        self.controlador.mostrar_tela("funcionarios")

    # -- Correção e recálculo incremental (Cap. 9.4/9.5/9.6/10.7) -----------

    def _construir_contexto(self, funcionario: Funcionario) -> ContextoCalculo | None:
        """
        Monta o `ContextoCalculo` do Turno do funcionário (Cap. 6) —
        reaproveitado por qualquer recálculo desta tela (correção
        individual e Aplicar Justificativa por Período, Cap. 9.8),
        para não duplicar a busca do Turno em cada lugar que precisa
        chamar `calculadora.recalcular_dia`.
        """
        turnos = [
            turno_de_dict(dados) for dados in self.config_app.configuracoes.get("turnos", [])
        ]
        turno = next((t for t in turnos if t.id == funcionario.turno_id), None)
        if turno is None:
            return None
        return ContextoCalculo(
            config=self.config_app,
            turno=turno,
            funcionario_id=funcionario.id,
            nome_funcionario=funcionario.nome_completo,
            nome_empresa=self.config_app.nome_empresa,
        )

    def _salvar_correcao(self, linha: _LinhaPendencia) -> None:
        """
        Aplica a correção de uma única pendência e recalcula
        imediatamente apenas aquele dia (Cap. 10.7), reaproveitando
        `calculadora.recalcular_dia` — nenhuma lógica de cálculo nova
        é criada aqui.
        """
        if linha.pendencia is None or linha.dia is None:
            return
        funcionario = self._funcionarios_por_id.get(linha.pendencia.id_funcionario)
        if funcionario is None:
            return

        dia = linha.dia
        batidas_antes = self._texto_batidas(dia)
        justificativa_antes = dia.pendencia.justificativa if dia.pendencia is not None else ""
        observacoes_antes = dia.pendencia.observacoes if dia.pendencia is not None else ""

        novas_batidas = [
            Batida(horario=horario, manual=True)
            for texto in linha.horarios_texto()
            if (horario := _texto_para_horario(texto)) is not None
        ]
        if novas_batidas:
            dia.batidas = novas_batidas

        if dia.pendencia is not None:
            dia.pendencia.justificativa = linha.justificativa_selecionada()
            dia.pendencia.observacoes = linha.observacoes()

        contexto = self._construir_contexto(funcionario)
        if contexto is not None:
            recalcular_dia(dia, contexto)
            log.info(
                'Pendência recalculada: "%s" em %s.',
                funcionario.nome_completo, dia.data.strftime("%d/%m/%Y"),
            )

        self._registrar_auditoria_correcao(
            funcionario, dia, batidas_antes, justificativa_antes, observacoes_antes)

        self._atualizar_lista()
        self._persistir()

    def _texto_batidas(self, dia: DiaTrabalho) -> str:
        return ", ".join(_horario_para_texto(batida.horario) for batida in dia.batidas)

    def _registrar_auditoria_correcao(
        self, funcionario: Funcionario, dia: DiaTrabalho,
        batidas_antes: str, justificativa_antes: str, observacoes_antes: str,
    ) -> None:
        """
        Auditoria (Etapa 13, v2.0): registra quem/quando/o quê/valor
        anterior/valor novo para cada campo efetivamente alterado por
        uma correção manual — nunca grava um evento para um campo que
        não mudou. Fica em memória em `Competencia.auditoria`, gravado
        junto com `_persistir()` logo em seguida.
        """
        if self._competencia is None:
            return
        quando = dia.data.strftime("%d/%m/%Y")

        batidas_depois = self._texto_batidas(dia)
        if batidas_depois != batidas_antes:
            competencias.registrar_auditoria(
                self._competencia,
                o_que=f"Batidas corrigidas — {funcionario.nome_completo} em {quando}",
                valor_anterior=batidas_antes or "—", valor_novo=batidas_depois or "—",
            )

        justificativa_depois = dia.pendencia.justificativa if dia.pendencia is not None else ""
        if justificativa_depois != justificativa_antes:
            competencias.registrar_auditoria(
                self._competencia,
                o_que=f"Justificativa alterada — {funcionario.nome_completo} em {quando}",
                valor_anterior=justificativa_antes or "—", valor_novo=justificativa_depois or "—",
            )

        observacoes_depois = dia.pendencia.observacoes if dia.pendencia is not None else ""
        if observacoes_depois != observacoes_antes:
            competencias.registrar_auditoria(
                self._competencia,
                o_que=f"Observações alteradas — {funcionario.nome_completo} em {quando}",
                valor_anterior=observacoes_antes or "—", valor_novo=observacoes_depois or "—",
            )

    # -- Persistência incremental (gerenciamento de múltiplas competências) --

    def _persistir(self) -> None:
        """
        Reavalia o status da Competência atual a partir do estado
        corrente de suas pendências e persiste imediatamente
        (`competencias.salvar_competencia`) — chamada depois de
        qualquer correção/justificativa, para que fechar o sistema no
        meio das pendências nunca perca nada.
        """
        if self._competencia is None or self._resultado is None:
            return
        self._competencia.status = competencias.avaliar_status(
            self._resultado, self._competencia.status)
        competencias.salvar_competencia(self._competencia)

    # -- Aplicar Justificativa por Período (Cap. 9.8) -------------------------

    def _abrir_dialogo_justificativa_periodo(self) -> None:
        if self._resultado is None or not self._resultado.funcionarios_processados:
            messagebox.showinfo(
                "Aplicar Justificativa por Período",
                "Não há funcionários processados nesta competência.",
            )
            return
        _DialogoJustificativaPeriodo(
            self,
            self.config_app,
            self._resultado.funcionarios_processados,
            construir_contexto=self._construir_contexto,
            ao_confirmar=self._ao_confirmar_justificativa_periodo,
        )

    def _ao_confirmar_justificativa_periodo(
        self, funcionario: Funcionario, justificativa: str, dias: list[DiaTrabalho],
    ) -> None:
        """
        Callback de `_DialogoJustificativaPeriodo`: audita (Etapa 13, v2.0
        — um único evento agregado para a operação em lote, no mesmo
        espírito de `competencias.registrar_importacao`), atualiza a
        lista e persiste.
        """
        if self._competencia is not None and dias:
            datas = sorted(dia.data for dia in dias)
            competencias.registrar_auditoria(
                self._competencia,
                o_que=(
                    f"Justificativa por período aplicada — {funcionario.nome_completo} "
                    f"({datas[0].strftime('%d/%m/%Y')} a {datas[-1].strftime('%d/%m/%Y')})"
                ),
                valor_anterior=f"{len(dias)} dia(s) sem esta justificativa",
                valor_novo=f'"{justificativa}" aplicada a {len(dias)} dia(s)',
            )
        self._atualizar_lista()
        self._persistir()

    def _concluir(self) -> None:
        """
        Fecha a Tela de Pendências e volta à Principal. O bloqueio da
        geração do relatório enquanto houver pendência em aberto (Cap.
        9.1) é responsabilidade de relatorio.py
        (`existem_pendencias_abertas`/`RelatorioBloqueadoError`), não
        desta tela.
        """
        pendencias_abertas = (
            [p for p in self._resultado.pendencias if not p.resolvida] if self._resultado else []
        )
        self.controlador.definir_status(
            f"Cálculo concluído — {len(pendencias_abertas)} pendência(s) ainda em aberto."
        )
        self.controlador.mostrar_tela("principal")
