"""
tela_funcionarios.py
---------------------
Tela de Cadastro Inteligente Assistido de Funcionários (Cap. 5 / 12.4).

A principal forma de cadastro é a importação da planilha do ponto
(leitor_ponto.py + cadastro.py, Cap. 3/5). Esta tela implementa:

    - Cadastro manual completo (adicionar/editar/excluir/ativar-inativar),
      usado antes da primeira importação, para funcionários que ainda
      não aparecem na planilha, correções e temporários (Cap. 5.8).
    - O motor de sugestão de turno (modelos.sugerir_turno) e o Painel de
      Revisão (Cap. 5.4), acessível pelo método público
      `iniciar_revisao_importacao()` — chamado por `tela_principal.py`
      com os dados reais extraídos da planilha.
    - Ações em massa (Cap. 5.9): selecionar vários funcionários e
      aplicar Turno/Setor/Cargo/Status de uma vez.
    - Importação Parcial (Cap. 5.7): concluir uma revisão só cria/atualiza
      os funcionários presentes no lote revisado — nenhum funcionário
      ausente é excluído, inativado ou perde vínculo.

Persistido em dados/funcionarios.json através de config.py, reaproveitando
o mesmo padrão de leitura/escrita/backup automático das demais telas.
"""

from __future__ import annotations

import os
import tkinter as tk
from datetime import datetime
from tkinter import messagebox
from typing import Callable

import customtkinter as ctk

from componentes import BotaoExportar, ColunaOrdenavel, TabelaPadrao
from config import Config, funcionario_de_dict, funcionario_para_dict, setor_para_dict
from constantes import SituacaoSugestao, StatusFuncionario
from exportacao import caminho_exportacao, exportar_excel_simples
from logger import get_logger
from modelos import (
    Funcionario,
    FuncionarioPlanilha,
    Setor,
    SetorNovoEncontrado,
    SugestaoImportacao,
)

log = get_logger()

_SEM_SELECAO = "— Selecione —"
_SEM_TURNO_SUGERIDO = "— Nenhum —"


def _agora_texto() -> str:
    """Data/hora atual formatada, para data_cadastro/ultima_atualizacao."""
    return datetime.now().strftime("%d/%m/%Y %H:%M:%S")


def _horario_texto(horario) -> str:
    """Formata um datetime.time (ou None) como texto "HH:MM" / "—"."""
    return horario.strftime("%H:%M") if horario is not None else "—"


# ---------------------------------------------------------------------------
# Linha de um funcionário na tabela
# ---------------------------------------------------------------------------

class _LinhaFuncionario(ctk.CTkFrame):
    """
    Uma linha reaproveitável do pool de `TabelaPadrao` (Sprint 1,
    v2.1): checkbox de seleção, Nome, Cargo, Setor, Turno (nomes
    resolvidos apenas para exibição — o vínculo interno continua por
    ID, Cap. 5.13/21.4), Status, e os botões
    Editar/Ativar-Inativar/Excluir. `vincular()` só troca qual
    funcionário esta linha exibe, sem recriar nada.
    """

    def __init__(
        self, master,
        nome_turno_de: Callable[[str], str],
        nome_setor_de: Callable[[str], str],
        esta_selecionado: Callable[[str], bool],
        ao_alternar_selecao: Callable[[str, bool], None],
        ao_editar: Callable[[Funcionario], None],
        ao_alternar_status: Callable[[Funcionario], None],
        ao_excluir: Callable[[Funcionario], None],
    ) -> None:
        super().__init__(master, corner_radius=8, border_width=1)
        self.funcionario: Funcionario | None = None
        self._nome_turno_de = nome_turno_de
        self._nome_setor_de = nome_setor_de
        self._esta_selecionado = esta_selecionado
        self._ao_alternar_selecao = ao_alternar_selecao

        self.grid_columnconfigure(1, weight=2)
        self.grid_columnconfigure(2, weight=1)
        self.grid_columnconfigure(3, weight=1)
        self.grid_columnconfigure(4, weight=1)

        self._var_selecionado = tk.BooleanVar(value=False)
        self._chk_selecionar = ctk.CTkCheckBox(
            self, text="", width=20, variable=self._var_selecionado,
            command=self._clicar_selecionar,
        )
        self._chk_selecionar.grid(row=0, column=0, padx=(12, 5), pady=10)

        self._rotulo_nome = ctk.CTkLabel(
            self, anchor="w", font=ctk.CTkFont(weight="bold"))
        self._rotulo_nome.grid(row=0, column=1, sticky="w", padx=5)

        self._rotulo_cargo = ctk.CTkLabel(self, anchor="w")
        self._rotulo_cargo.grid(row=0, column=2, sticky="w", padx=5)
        self._rotulo_setor = ctk.CTkLabel(self, anchor="w")
        self._rotulo_setor.grid(row=0, column=3, sticky="w", padx=5)
        self._rotulo_turno = ctk.CTkLabel(self, anchor="w")
        self._rotulo_turno.grid(row=0, column=4, sticky="w", padx=5)

        self._rotulo_status = ctk.CTkLabel(self, width=64)
        self._rotulo_status.grid(row=0, column=5, padx=5)

        self._botao_editar = ctk.CTkButton(
            self, text="Editar", width=70, command=lambda: self._chamar(ao_editar))
        self._botao_editar.grid(row=0, column=6, padx=(5, 5), pady=10)

        self._botao_alternar = ctk.CTkButton(
            self, text="", width=70, fg_color="transparent", border_width=1,
            command=lambda: self._chamar(ao_alternar_status),
        )
        self._botao_alternar.grid(row=0, column=7, padx=(0, 5), pady=10)

        self._botao_excluir = ctk.CTkButton(
            self, text="Excluir", width=70, fg_color="#c0392b", hover_color="#992d22",
            command=lambda: self._chamar(ao_excluir),
        )
        self._botao_excluir.grid(row=0, column=8, padx=(0, 12), pady=10)

    def vincular(self, funcionario: Funcionario) -> None:
        self.funcionario = funcionario

        self._var_selecionado.set(self._esta_selecionado(funcionario.id))
        self._rotulo_nome.configure(text=funcionario.nome_completo)
        self._rotulo_cargo.configure(text=funcionario.cargo or "—")
        self._rotulo_setor.configure(text=self._nome_setor_de(funcionario.setor_id))
        self._rotulo_turno.configure(text=self._nome_turno_de(funcionario.turno_id))

        ativo = funcionario.status == StatusFuncionario.ATIVO
        self._rotulo_status.configure(
            text=funcionario.status.value,
            text_color=("#1e8449", "#2ecc71") if ativo else ("gray50", "gray50"),
        )
        self._botao_alternar.configure(text="Inativar" if ativo else "Ativar")

    def _clicar_selecionar(self) -> None:
        if self.funcionario is not None:
            self._ao_alternar_selecao(self.funcionario.id, bool(self._var_selecionado.get()))

    def _chamar(self, callback: Callable[[Funcionario], None]) -> None:
        if self.funcionario is not None:
            callback(self.funcionario)


# ---------------------------------------------------------------------------
# Linha do Painel de Revisão
# ---------------------------------------------------------------------------

class _LinhaRevisao(ctk.CTkFrame):
    """
    Uma linha do Painel de Revisão (Cap. 5.4): nome encontrado, horário
    detectado, turno sugerido e setor sugerido (Cap. 5.5-Setor) — ambos
    corrigíveis via seleção em lista —, e a situação combinada
    (✓ Confirmado apenas se turno e setor estiverem confirmados;
    ⚠ Revisar caso qualquer um dos dois precise de atenção).
    """

    def __init__(
        self,
        master,
        sugestao: SugestaoImportacao,
        opcoes_turno: list[tuple[str, str]],
        opcoes_setor: list[tuple[str, str]],
        status_inicial: StatusFuncionario = StatusFuncionario.ATIVO,
    ) -> None:
        super().__init__(master, corner_radius=8, border_width=1)
        self.sugestao = sugestao

        self._mapa_nome_id_turno = {nome: id_turno for id_turno, nome in opcoes_turno}
        self._mapa_id_nome_turno = {id_turno: nome for id_turno, nome in opcoes_turno}
        self._mapa_nome_id_setor = {nome: id_setor for id_setor, nome in opcoes_setor}
        self._mapa_id_nome_setor = {id_setor: nome for id_setor, nome in opcoes_setor}

        self.grid_columnconfigure(0, weight=2)
        self.grid_columnconfigure(2, weight=1)
        self.grid_columnconfigure(3, weight=1)

        # Subtítulo com o IDUsuário sempre visível (não só quando há
        # duplicata) — sem ele, duas linhas "João Silva" (homônimos, cada
        # um com seu próprio IDUsuário) ficariam indistinguíveis para
        # quem está revisando (Cap. 5.8).
        frame_nome = ctk.CTkFrame(self, fg_color="transparent")
        frame_nome.grid(row=0, column=0, sticky="w", padx=(12, 5), pady=10)
        ctk.CTkLabel(
            frame_nome, text=sugestao.nome_planilha, anchor="w", font=ctk.CTkFont(weight="bold"),
        ).pack(anchor="w")
        ctk.CTkLabel(
            frame_nome, text=f"IDUsuário: {sugestao.id_planilha or '—'}", anchor="w",
            font=ctk.CTkFont(size=11), text_color=("gray60", "gray60"),
        ).pack(anchor="w")

        ctk.CTkLabel(self, text=_horario_texto(sugestao.horario_entrada), width=60).grid(
            row=0, column=1, padx=5)

        valores_turno = [_SEM_TURNO_SUGERIDO] + [nome for _, nome in opcoes_turno]
        valor_inicial_turno = self._mapa_id_nome_turno.get(
            sugestao.turno_sugerido_id or "", _SEM_TURNO_SUGERIDO)
        self._var_turno = tk.StringVar(value=valor_inicial_turno)
        ctk.CTkOptionMenu(self, values=valores_turno, variable=self._var_turno, width=160).grid(
            row=0, column=2, sticky="ew", padx=5)

        valores_setor = [_SEM_TURNO_SUGERIDO] + [nome for _, nome in opcoes_setor]
        valor_inicial_setor = self._mapa_id_nome_setor.get(
            sugestao.setor_sugerido_id or "", _SEM_TURNO_SUGERIDO)
        self._var_setor = tk.StringVar(value=valor_inicial_setor)
        ctk.CTkOptionMenu(self, values=valores_setor, variable=self._var_setor, width=160).grid(
            row=0, column=3, sticky="ew", padx=5)

        confirmado = sugestao.situacao == SituacaoSugestao.CONFIRMADO
        ctk.CTkLabel(
            self, text=sugestao.situacao.value, width=110,
            text_color=("#1e8449", "#2ecc71") if confirmado else ("#a04000", "#f39c12"),
        ).grid(row=0, column=4, padx=(5, 12))

        # Status (Melhoria 1): funcionário já Inativo no cadastro chega
        # aqui desmarcado; um funcionário novo chega marcado (Ativo,
        # padrão). Quem decide o valor inicial é quem cria a linha
        # (iniciar_revisao_importacao), que já sabe o status atual.
        self._var_ativo = tk.BooleanVar(value=status_inicial != StatusFuncionario.INATIVO)
        ctk.CTkCheckBox(
            self, text="Ativo", variable=self._var_ativo, width=70,
        ).grid(row=0, column=5, padx=(5, 12))

    def turno_id_selecionado(self) -> str | None:
        """Retorna o id do turno atualmente escolhido nesta linha, ou None."""
        return self._mapa_nome_id_turno.get(self._var_turno.get())

    def setor_id_selecionado(self) -> str | None:
        """Retorna o id do setor atualmente escolhido nesta linha, ou None."""
        return self._mapa_nome_id_setor.get(self._var_setor.get())

    def status_selecionado(self) -> StatusFuncionario:
        """Status escolhido nesta linha (Melhoria 1) — Ativo por padrão."""
        return StatusFuncionario.ATIVO if self._var_ativo.get() else StatusFuncionario.INATIVO


# ---------------------------------------------------------------------------
# Linha da tela "Foram encontrados novos setores na planilha" (Cap. 5.17)
# ---------------------------------------------------------------------------

class _LinhaSetorNovo(ctk.CTkFrame):
    """
    Uma linha da tela de confirmação de Setores novos (Cap. 5.17): um
    checkbox pré-marcado com o nome do Setor (já na grafia amigável,
    Cap. 5.17) e a quantidade de funcionários da planilha que
    pertencem a ele — não persiste nada, apenas exibe o
    SetorNovoEncontrado recebido.
    """

    def __init__(self, master, setor_novo: SetorNovoEncontrado) -> None:
        super().__init__(master, corner_radius=8, border_width=1)
        self.nome = setor_novo.nome

        quantidade = setor_novo.quantidade_funcionarios
        sufixo = "funcionário" if quantidade == 1 else "funcionários"
        texto = f"{setor_novo.nome} ({quantidade} {sufixo})"

        self._var_selecionado = tk.BooleanVar(value=True)
        ctk.CTkCheckBox(
            self, text=texto, variable=self._var_selecionado,
            font=ctk.CTkFont(weight="bold"),
        ).pack(anchor="w", padx=12, pady=10)

    def selecionado(self) -> bool:
        return bool(self._var_selecionado.get())


# ---------------------------------------------------------------------------
# Tela de Funcionários
# ---------------------------------------------------------------------------

class TelaFuncionarios(ctk.CTkFrame):
    """Tela de Cadastro Inteligente Assistido de Funcionários (Cap. 5)."""

    def __init__(self, master, controlador, config: Config) -> None:
        super().__init__(master, corner_radius=0)

        self.controlador = controlador
        self.config_app = config

        self._selecionados: set[str] = set()
        self._funcionario_em_edicao_id: str | None = None
        self._linhas_revisao: list[_LinhaRevisao] = []
        self._funcionarios_planilha_pendente: list[FuncionarioPlanilha] = []
        self._ao_concluir_calculo: Callable[[list[Funcionario]], None] | None = None
        self._linhas_setores_novos: list[_LinhaSetorNovo] = []
        self._ao_concluir_setores_novos: Callable[[], None] | None = None

        self.grid_rowconfigure(4, weight=1)
        self.grid_columnconfigure(0, weight=1)

        self._montar_cabecalho()
        self._montar_barra_ferramentas()
        self._montar_barra_massa()
        self._montar_formulario()
        self._montar_lista()
        self._montar_painel_revisao()
        self._montar_painel_setores_novos()

        self._carregar_lista()

    # -- Cabeçalho (mesmo padrão das demais telas) ----------------------------

    def _montar_cabecalho(self) -> None:
        cabecalho = ctk.CTkFrame(self, corner_radius=0, height=70)
        cabecalho.grid(row=0, column=0, sticky="ew")
        cabecalho.grid_columnconfigure(1, weight=1)

        ctk.CTkButton(
            cabecalho, text="← Voltar", width=90,
            command=lambda: self.controlador.mostrar_tela("principal"),
        ).grid(row=0, column=0, padx=15, pady=15)

        ctk.CTkLabel(
            cabecalho, text="Funcionários",
            font=ctk.CTkFont(size=20, weight="bold"),
        ).grid(row=0, column=1, sticky="w", padx=10)

        self._rotulo_contadores = ctk.CTkLabel(
            cabecalho, text="", font=ctk.CTkFont(size=13),
            text_color=("gray60", "gray60"),
        )
        self._rotulo_contadores.grid(row=0, column=2, padx=15)

    # -- Barra de ferramentas: filtro, adicionar, exportar, imprimir -----------

    def _montar_barra_ferramentas(self) -> None:
        barra = ctk.CTkFrame(self, fg_color="transparent")
        barra.grid(row=1, column=0, sticky="ew", padx=30, pady=(15, 0))
        barra.grid_columnconfigure(3, weight=1)

        ctk.CTkLabel(barra, text="Status").grid(row=0, column=0, padx=(0, 5))
        self._var_filtro_status = tk.StringVar(value="Todos")
        ctk.CTkOptionMenu(
            barra, values=["Todos", StatusFuncionario.ATIVO.value, StatusFuncionario.INATIVO.value],
            variable=self._var_filtro_status, width=110,
            command=lambda valor: self._carregar_lista(),
        ).grid(row=0, column=1, padx=(0, 10))

        ctk.CTkButton(
            barra, text="+ Adicionar Funcionário", height=40,
            font=ctk.CTkFont(weight="bold"),
            command=lambda: self._mostrar_formulario(),
        ).grid(row=0, column=2)

        ctk.CTkButton(
            barra, text="Imprimir", width=100, fg_color="transparent", border_width=1,
            command=self._imprimir,
        ).grid(row=0, column=4, padx=(10, 0))

        BotaoExportar(
            barra, titulo="Funcionários", colunas=["Nome", "Cargo", "Setor", "Turno", "Status"],
            obter_registros=lambda: self._tabela.registros_filtrados(),
            montar_linha=lambda f: (
                f.nome_completo, f.cargo or "—", self._nome_setor(f.setor_id),
                self._nome_turno(f.turno_id), f.status.value),
            caminho_sugerido=lambda extensao: caminho_exportacao(
                self.config_app, "Funcionarios", "Funcionarios", extensao),
        ).grid(row=0, column=5, padx=(10, 0))

    # -- Barra de ações em massa (Cap. 5.9) -------------------------------------

    def _montar_barra_massa(self) -> None:
        self._barra_massa = ctk.CTkFrame(self, corner_radius=10)
        self._barra_massa.grid_columnconfigure(6, weight=1)
        # Não posicionada aqui — só aparece quando há seleção (_atualizar_barra_massa)

        self._rotulo_selecionados = ctk.CTkLabel(
            self._barra_massa, text="", font=ctk.CTkFont(weight="bold"),
        )
        self._rotulo_selecionados.grid(row=0, column=0, padx=(15, 15), pady=12)

        self._var_massa_turno = tk.StringVar(value=_SEM_SELECAO)
        self._menu_massa_turno = ctk.CTkOptionMenu(
            self._barra_massa, values=[_SEM_SELECAO], variable=self._var_massa_turno, width=150,
        )
        self._menu_massa_turno.grid(row=0, column=1, padx=5)
        ctk.CTkButton(
            self._barra_massa, text="Aplicar Turno", width=110,
            command=self._aplicar_turno_massa,
        ).grid(row=0, column=2, padx=(0, 10))

        self._var_massa_setor = tk.StringVar(value=_SEM_SELECAO)
        self._menu_massa_setor = ctk.CTkOptionMenu(
            self._barra_massa, values=[_SEM_SELECAO], variable=self._var_massa_setor, width=150,
        )
        self._menu_massa_setor.grid(row=0, column=3, padx=5)
        ctk.CTkButton(
            self._barra_massa, text="Aplicar Setor", width=110,
            command=self._aplicar_setor_massa,
        ).grid(row=0, column=4, padx=(0, 10))

        self._entry_massa_cargo = ctk.CTkEntry(
            self._barra_massa, placeholder_text="Cargo", width=130)
        self._entry_massa_cargo.grid(row=0, column=5, padx=5)
        ctk.CTkButton(
            self._barra_massa, text="Aplicar Cargo", width=110,
            command=self._aplicar_cargo_massa,
        ).grid(row=0, column=6, padx=(0, 10), sticky="w")

        ctk.CTkButton(
            self._barra_massa, text="Ativar", width=80, command=self._ativar_massa,
        ).grid(row=0, column=7, padx=5)
        ctk.CTkButton(
            self._barra_massa, text="Inativar", width=80, fg_color="transparent",
            border_width=1, command=self._inativar_massa,
        ).grid(row=0, column=8, padx=(0, 15))

    def _atualizar_barra_massa(self) -> None:
        """Mostra a barra de ações em massa somente quando há seleção."""
        if self._selecionados:
            self._rotulo_selecionados.configure(text=f"{len(self._selecionados)} selecionado(s)")
            self._menu_massa_turno.configure(values=[_SEM_SELECAO] + self._nomes_turnos())
            self._menu_massa_setor.configure(values=[_SEM_SELECAO] + self._nomes_setores())
            self._barra_massa.grid(row=2, column=0, sticky="ew", padx=30, pady=(10, 0))
        else:
            self._barra_massa.grid_remove()

    def _aplicar_turno_massa(self) -> None:
        nome = self._var_massa_turno.get()
        turno_id = self._id_turno_por_nome(nome)
        if not turno_id:
            return
        quantidade = self._atualizar_selecionados(lambda f: setattr(f, "turno_id", turno_id))
        self._notificar_massa(f'Turno "{nome}" aplicado a {quantidade} funcionário(s).')

    def _aplicar_setor_massa(self) -> None:
        nome = self._var_massa_setor.get()
        setor_id = self._id_setor_por_nome(nome)
        if not setor_id:
            return
        quantidade = self._atualizar_selecionados(lambda f: setattr(f, "setor_id", setor_id))
        self._notificar_massa(f'Setor "{nome}" aplicado a {quantidade} funcionário(s).')

    def _aplicar_cargo_massa(self) -> None:
        cargo = self._entry_massa_cargo.get().strip()
        if not cargo:
            return
        quantidade = self._atualizar_selecionados(lambda f: setattr(f, "cargo", cargo))
        self._notificar_massa(f'Cargo "{cargo}" aplicado a {quantidade} funcionário(s).')

    def _ativar_massa(self) -> None:
        quantidade = self._atualizar_selecionados(
            lambda f: setattr(f, "status", StatusFuncionario.ATIVO))
        self._notificar_massa(f"{quantidade} funcionário(s) ativado(s).")

    def _inativar_massa(self) -> None:
        """Inativação em massa pede confirmação (Cap. 12.4) — afeta vários cadastros de uma vez."""
        quantidade_selecionada = len(self._selecionados)
        if quantidade_selecionada == 0:
            return
        confirmar = messagebox.askyesno(
            "Confirmar inativação",
            f"Inativar {quantidade_selecionada} funcionário(s) selecionado(s)?",
        )
        if not confirmar:
            return
        quantidade = self._atualizar_selecionados(
            lambda f: setattr(f, "status", StatusFuncionario.INATIVO))
        self._notificar_massa(f"{quantidade} funcionário(s) inativado(s).")

    def _notificar_massa(self, mensagem: str) -> None:
        """Feedback visual consistente (Cap. 12.2) após uma ação em massa."""
        if hasattr(self.controlador, "definir_status"):
            self.controlador.definir_status(mensagem)

    def _atualizar_selecionados(self, alteracao: Callable[[Funcionario], None]) -> int:
        """
        Aplica `alteracao` a cada funcionário atualmente selecionado, e
        somente a eles — os demais permanecem intocados (mesmo espírito
        da Importação Parcial, Cap. 5.7, aplicado a ações em massa).
        Retorna a quantidade de funcionários efetivamente alterados.
        """
        if not self._selecionados:
            return 0

        dados_lista = self.config_app.funcionarios.get("funcionarios", [])
        agora = _agora_texto()
        quantidade = 0
        for dados in dados_lista:
            if dados.get("id") in self._selecionados:
                funcionario = funcionario_de_dict(dados)
                alteracao(funcionario)
                funcionario.ultima_atualizacao = agora
                dados.clear()
                dados.update(funcionario_para_dict(funcionario))
                quantidade += 1

        self.config_app.salvar_funcionarios()
        self._carregar_lista()
        return quantidade

    # -- Formulário (reaproveitado para adicionar e editar) --------------------

    def _montar_formulario(self) -> None:
        self._frame_formulario = ctk.CTkFrame(self, corner_radius=10)
        self._frame_formulario.grid_columnconfigure((1, 3), weight=1)

        self._rotulo_titulo_formulario = ctk.CTkLabel(
            self._frame_formulario, text="Novo Funcionário",
            font=ctk.CTkFont(size=16, weight="bold"), anchor="w",
        )
        self._rotulo_titulo_formulario.grid(
            row=0, column=0, columnspan=4, sticky="w", padx=15, pady=(15, 10))

        def _rotulo(texto: str, linha: int, coluna: int) -> None:
            ctk.CTkLabel(self._frame_formulario, text=texto).grid(
                row=linha, column=coluna, sticky="w", padx=(15 if coluna == 0 else 5, 5),
                pady=(6, 0))

        _rotulo("Nome Completo *", 1, 0)
        self._entry_nome_completo = ctk.CTkEntry(self._frame_formulario)
        self._entry_nome_completo.grid(
            row=1, column=1, columnspan=3, sticky="ew", padx=(0, 15), pady=(6, 0))

        _rotulo("Nome na Planilha", 2, 0)
        self._entry_nome_planilha = ctk.CTkEntry(
            self._frame_formulario, placeholder_text="Se vazio, usa o Nome Completo")
        self._entry_nome_planilha.grid(row=2, column=1, sticky="ew", padx=(0, 15), pady=(6, 0))

        _rotulo("Apelido", 2, 2)
        self._entry_apelido = ctk.CTkEntry(self._frame_formulario)
        self._entry_apelido.grid(row=2, column=3, sticky="ew", padx=(0, 15), pady=(6, 0))

        _rotulo("Matrícula", 3, 0)
        self._entry_matricula = ctk.CTkEntry(self._frame_formulario)
        self._entry_matricula.grid(row=3, column=1, sticky="ew", padx=(0, 15), pady=(6, 0))

        _rotulo("CPF", 3, 2)
        self._entry_cpf = ctk.CTkEntry(self._frame_formulario)
        self._entry_cpf.grid(row=3, column=3, sticky="ew", padx=(0, 15), pady=(6, 0))

        _rotulo("Cargo *", 4, 0)
        self._entry_cargo = ctk.CTkEntry(self._frame_formulario)
        self._entry_cargo.grid(row=4, column=1, sticky="ew", padx=(0, 15), pady=(6, 0))

        _rotulo("Status", 4, 2)
        self._var_status_form = tk.StringVar(value=StatusFuncionario.ATIVO.value)
        ctk.CTkOptionMenu(
            self._frame_formulario,
            values=[StatusFuncionario.ATIVO.value, StatusFuncionario.INATIVO.value],
            variable=self._var_status_form,
        ).grid(row=4, column=3, sticky="ew", padx=(0, 15), pady=(6, 0))

        _rotulo("Turno *", 5, 0)
        self._var_turno_form = tk.StringVar(value=_SEM_SELECAO)
        self._menu_turno_form = ctk.CTkOptionMenu(
            self._frame_formulario, values=[_SEM_SELECAO], variable=self._var_turno_form,
        )
        self._menu_turno_form.grid(row=5, column=1, sticky="ew", padx=(0, 15), pady=(6, 0))

        _rotulo("Setor *", 5, 2)
        self._var_setor_form = tk.StringVar(value=_SEM_SELECAO)
        self._menu_setor_form = ctk.CTkOptionMenu(
            self._frame_formulario, values=[_SEM_SELECAO], variable=self._var_setor_form,
        )
        self._menu_setor_form.grid(row=5, column=3, sticky="ew", padx=(0, 15), pady=(6, 0))

        self._rotulo_erro_formulario = ctk.CTkLabel(
            self._frame_formulario, text="", text_color=("#c0392b", "#e74c3c"), anchor="w",
        )
        self._rotulo_erro_formulario.grid(
            row=6, column=0, columnspan=4, sticky="ew", padx=15, pady=(8, 0))

        linha_botoes = ctk.CTkFrame(self._frame_formulario, fg_color="transparent")
        linha_botoes.grid(row=7, column=0, columnspan=4, sticky="w", padx=15, pady=(8, 15))
        ctk.CTkButton(
            linha_botoes, text="Salvar", command=self._salvar_formulario,
        ).pack(side="left", padx=(0, 10))
        ctk.CTkButton(
            linha_botoes, text="Cancelar", fg_color="transparent", border_width=1,
            command=self._ocultar_formulario,
        ).pack(side="left")

    def _mostrar_formulario(self, funcionario: Funcionario | None = None) -> None:
        """Exibe o formulário em modo "novo" (funcionario=None) ou "editar"."""
        self._funcionario_em_edicao_id = funcionario.id if funcionario is not None else None
        self._rotulo_titulo_formulario.configure(
            text="Editar Funcionário" if funcionario is not None else "Novo Funcionário"
        )

        self._menu_turno_form.configure(values=[_SEM_SELECAO] + self._nomes_turnos())
        self._menu_setor_form.configure(values=[_SEM_SELECAO] + self._nomes_setores())

        campos_texto = {
            self._entry_nome_completo: funcionario.nome_completo if funcionario else "",
            self._entry_nome_planilha: funcionario.nome_planilha if funcionario else "",
            self._entry_apelido: funcionario.apelido if funcionario else "",
            self._entry_matricula: funcionario.matricula if funcionario else "",
            self._entry_cpf: funcionario.cpf if funcionario else "",
            self._entry_cargo: funcionario.cargo if funcionario else "",
        }
        for entrada, valor in campos_texto.items():
            entrada.delete(0, "end")
            entrada.insert(0, valor)

        self._var_status_form.set(
            funcionario.status.value if funcionario else StatusFuncionario.ATIVO.value
        )
        self._var_turno_form.set(
            self._nome_turno(funcionario.turno_id) if funcionario and funcionario.turno_id
            else _SEM_SELECAO
        )
        self._var_setor_form.set(
            self._nome_setor(funcionario.setor_id) if funcionario and funcionario.setor_id
            else _SEM_SELECAO
        )
        self._rotulo_erro_formulario.configure(text="")

        self._frame_formulario.grid(row=3, column=0, sticky="ew", padx=30, pady=(15, 0))

    def _ocultar_formulario(self) -> None:
        self._frame_formulario.grid_remove()
        self._funcionario_em_edicao_id = None

    def _validar_formulario(self) -> bool:
        """
        Valida os campos obrigatórios (Cap. 5.14/12.4): Nome Completo,
        Cargo, Turno, Setor e Status; e a unicidade do Nome Completo.
        """
        nome = self._entry_nome_completo.get().strip()
        cargo = self._entry_cargo.get().strip()
        turno_selecionado = self._var_turno_form.get()
        setor_selecionado = self._var_setor_form.get()

        erro = ""
        if not nome:
            erro = "Informe o Nome Completo."
        elif not cargo:
            erro = "Informe o Cargo."
        elif turno_selecionado == _SEM_SELECAO:
            erro = "Selecione o Turno."
        elif setor_selecionado == _SEM_SELECAO:
            erro = "Selecione o Setor."
        elif self._nome_completo_duplicado(nome):
            erro = "Já existe um funcionário cadastrado com este Nome Completo."

        self._rotulo_erro_formulario.configure(text=erro)
        return not erro

    def _nome_completo_duplicado(self, nome: str) -> bool:
        """
        Verifica se já existe outro funcionário com exatamente o mesmo
        Nome Completo (Cap. 5.14), ignorando o próprio registro quando
        em modo de edição.
        """
        for dados in self.config_app.funcionarios.get("funcionarios", []):
            if dados.get("id") == self._funcionario_em_edicao_id:
                continue
            if dados.get("nome_completo", "") == nome:
                return True
        return False

    def _salvar_formulario(self) -> None:
        """
        Cria um novo funcionário ou atualiza um existente — um único
        método para os dois fluxos, evitando lógica duplicada entre
        "adicionar" e "editar" (Cap. 5.8).
        """
        if not self._validar_formulario():
            return

        agora = _agora_texto()
        funcionarios = self.config_app.funcionarios.setdefault("funcionarios", [])

        if self._funcionario_em_edicao_id is not None:
            for indice, dados in enumerate(funcionarios):
                if dados.get("id") == self._funcionario_em_edicao_id:
                    funcionario = funcionario_de_dict(dados)
                    self._preencher_funcionario_do_formulario(funcionario)
                    funcionario.ultima_atualizacao = agora
                    funcionarios[indice] = funcionario_para_dict(funcionario)
                    break
        else:
            novo = Funcionario(nome_completo="")
            self._preencher_funcionario_do_formulario(novo)
            novo.data_cadastro = agora
            novo.ultima_atualizacao = agora
            funcionarios.append(funcionario_para_dict(novo))

        self.config_app.salvar_funcionarios()
        self._ocultar_formulario()
        self._carregar_lista()

    def _preencher_funcionario_do_formulario(self, funcionario: Funcionario) -> None:
        """Copia os valores atuais do formulário para `funcionario` (in-place)."""
        funcionario.nome_completo = self._entry_nome_completo.get().strip()
        funcionario.nome_planilha = self._entry_nome_planilha.get().strip()
        funcionario.apelido = self._entry_apelido.get().strip()
        funcionario.matricula = self._entry_matricula.get().strip()
        funcionario.cpf = self._entry_cpf.get().strip()
        funcionario.cargo = self._entry_cargo.get().strip()
        funcionario.turno_id = self._id_turno_por_nome(self._var_turno_form.get()) or ""
        funcionario.setor_id = self._id_setor_por_nome(self._var_setor_form.get()) or ""
        funcionario.status = StatusFuncionario(self._var_status_form.get())

    # -- Lista de funcionários ---------------------------------------------------

    def _montar_lista(self) -> None:
        self._tabela = TabelaPadrao(
            self,
            criar_linha=lambda m: _LinhaFuncionario(
                m, nome_turno_de=self._nome_turno, nome_setor_de=self._nome_setor,
                esta_selecionado=lambda fid: fid in self._selecionados,
                ao_alternar_selecao=self._alternar_selecao,
                ao_editar=self._mostrar_formulario,
                ao_alternar_status=self._alternar_status,
                ao_excluir=self._excluir_funcionario,
            ),
            colunas=[
                ColunaOrdenavel("Nome", lambda f: f.nome_completo.lower()),
                ColunaOrdenavel("Cargo", lambda f: (f.cargo or "").lower()),
                ColunaOrdenavel("Setor", lambda f: self._nome_setor(f.setor_id).lower()),
                ColunaOrdenavel("Turno", lambda f: self._nome_turno(f.turno_id).lower()),
                ColunaOrdenavel("Status", lambda f: f.status.value),
            ],
            campos_pesquisa=[lambda f: f.nome_completo, lambda f: f.matricula, lambda f: f.cpf],
            placeholder_pesquisa="Pesquisar por nome, matrícula ou CPF...",
            texto_vazio="Nenhum funcionário cadastrado ainda.",
        )
        self._tabela.grid(row=4, column=0, sticky="nsew", padx=30, pady=15)

    def ao_exibir(self) -> None:
        """Recarrega a lista sempre que a tela é exibida (hook padrão do Sprint 1)."""
        self._carregar_lista()

    def _carregar_lista(self) -> None:
        """
        (Re)carrega a lista de funcionários a partir de config.funcionarios,
        aplicando o filtro de status (pesquisa e ordenação já ficam por
        conta de `TabelaPadrao`). Os contadores (Total/Ativos/Inativos)
        refletem sempre o cadastro completo, independentemente do
        filtro/pesquisa atuais.
        """
        dados_todos = self.config_app.funcionarios.get("funcionarios", [])
        todos = [funcionario_de_dict(d) for d in dados_todos]
        self._atualizar_contadores(todos)

        filtro_status = self._var_filtro_status.get()
        visiveis = todos
        if filtro_status != "Todos":
            visiveis = [f for f in visiveis if f.status.value == filtro_status]

        ids_validos = {f.id for f in todos}
        self._selecionados &= ids_validos  # remove seleção de itens excluídos

        self._tabela.definir_registros(visiveis)
        self._atualizar_barra_massa()

    def _atualizar_contadores(self, funcionarios: list[Funcionario]) -> None:
        total = len(funcionarios)
        ativos = sum(1 for f in funcionarios if f.status == StatusFuncionario.ATIVO)
        inativos = total - ativos
        self._rotulo_contadores.configure(
            text=f"Total: {total}   Ativos: {ativos}   Inativos: {inativos}"
        )

    def _alternar_selecao(self, funcionario_id: str, selecionado: bool) -> None:
        if selecionado:
            self._selecionados.add(funcionario_id)
        else:
            self._selecionados.discard(funcionario_id)
        self._atualizar_barra_massa()

    def _imprimir(self) -> None:
        """Impressão universal (Sprint 1): gera o Excel da lista e envia à impressora padrão."""
        registros = self._tabela.registros_filtrados()
        if not registros:
            messagebox.showinfo("Imprimir", "Não há funcionários para imprimir.")
            return
        caminho = caminho_exportacao(self.config_app, "Funcionarios", "Funcionarios", "xlsx")
        exportar_excel_simples(
            caminho, "Funcionários", ["Nome", "Cargo", "Setor", "Turno", "Status"],
            [(f.nome_completo, f.cargo or "—", self._nome_setor(f.setor_id),
              self._nome_turno(f.turno_id), f.status.value) for f in registros],
        )
        try:
            os.startfile(str(caminho), "print")  # type: ignore[attr-defined]
            self.controlador.definir_status(f"Enviado para impressão: {caminho.name}")
        except OSError as erro:
            log.error("Falha ao imprimir funcionários: %s", erro)
            messagebox.showerror(
                "Não foi possível imprimir",
                f"Não foi possível enviar para impressão automaticamente. "
                f"O arquivo foi gerado em:\n{caminho}",
            )

    # -- Ações individuais -----------------------------------------------------

    def _alternar_status(self, funcionario: Funcionario) -> None:
        """Ativa/Inativa um único funcionário imediatamente."""
        for dados in self.config_app.funcionarios.get("funcionarios", []):
            if dados.get("id") == funcionario.id:
                atual = funcionario_de_dict(dados)
                atual.status = (
                    StatusFuncionario.INATIVO if atual.status == StatusFuncionario.ATIVO
                    else StatusFuncionario.ATIVO
                )
                atual.ultima_atualizacao = _agora_texto()
                dados.clear()
                dados.update(funcionario_para_dict(atual))
                break

        self.config_app.salvar_funcionarios()
        self._carregar_lista()

    def _excluir_funcionario(self, funcionario: Funcionario) -> None:
        """Exclui um funcionário, com confirmação obrigatória."""
        confirmar = messagebox.askyesno(
            "Confirmar exclusão",
            f'Excluir o funcionário "{funcionario.nome_completo}"? '
            "Esta ação não pode ser desfeita.",
        )
        if not confirmar:
            return

        funcionarios = self.config_app.funcionarios.get("funcionarios", [])
        self.config_app.funcionarios["funcionarios"] = [
            dados for dados in funcionarios if dados.get("id") != funcionario.id
        ]
        self._selecionados.discard(funcionario.id)
        self.config_app.salvar_funcionarios()
        self._carregar_lista()

    # -- Resolução de Turno/Setor (nomes só para exibição — vínculo por ID) ----

    def _turnos(self) -> list[dict]:
        return self.config_app.configuracoes.get("turnos", [])

    def _setores(self) -> list[dict]:
        return self.config_app.setores.get("setores", [])

    def _nomes_turnos(self) -> list[str]:
        return [t.get("nome", "") for t in self._turnos()]

    def _nomes_setores(self) -> list[str]:
        return [s.get("nome", "") for s in self._setores()]

    def _nome_turno(self, turno_id: str) -> str:
        if not turno_id:
            return "—"
        for turno in self._turnos():
            if turno.get("id") == turno_id:
                return turno.get("nome", "—")
        return "(turno removido)"

    def _nome_setor(self, setor_id: str) -> str:
        if not setor_id:
            return "—"
        for setor in self._setores():
            if setor.get("id") == setor_id:
                return setor.get("nome", "—")
        return "(setor removido)"

    def _id_turno_por_nome(self, nome: str) -> str | None:
        for turno in self._turnos():
            if turno.get("nome") == nome:
                return turno.get("id")
        return None

    def _id_setor_por_nome(self, nome: str) -> str | None:
        for setor in self._setores():
            if setor.get("nome") == nome:
                return setor.get("id")
        return None

    def _opcoes_turno(self) -> list[tuple[str, str]]:
        """Lista de (id, nome) de todos os turnos cadastrados."""
        return [(t.get("id", ""), t.get("nome", "")) for t in self._turnos() if t.get("id")]

    def _opcoes_setor(self) -> list[tuple[str, str]]:
        """Lista de (id, nome) de todos os setores cadastrados."""
        return [(s.get("id", ""), s.get("nome", "")) for s in self._setores() if s.get("id")]

    # -- Painel de Revisão (Cap. 5.4) --------------------------------------------

    def _montar_painel_revisao(self) -> None:
        self._frame_revisao = ctk.CTkFrame(self, fg_color="transparent")
        # Não posicionado aqui — só aparece via iniciar_revisao_importacao()

        ctk.CTkLabel(
            self._frame_revisao, text="Revisão da Importação",
            font=ctk.CTkFont(size=18, weight="bold"),
        ).pack(anchor="w", pady=(0, 5))

        ctk.CTkLabel(
            self._frame_revisao,
            text=(
                "Confira as sugestões abaixo. Casos \"⚠ Revisar\" podem ter o "
                "turno e/ou o setor corrigidos manualmente antes de concluir."
            ),
            text_color=("gray60", "gray60"),
        ).pack(anchor="w", pady=(0, 10))

        self._scroll_revisao = ctk.CTkScrollableFrame(self._frame_revisao, height=300)
        self._scroll_revisao.pack(fill="both", expand=True)

        linha_botoes = ctk.CTkFrame(self._frame_revisao, fg_color="transparent")
        linha_botoes.pack(fill="x", pady=(15, 0))
        ctk.CTkButton(
            linha_botoes, text="Concluir Importação", command=self._concluir_revisao,
        ).pack(side="left", padx=(0, 10))
        ctk.CTkButton(
            linha_botoes, text="Cancelar", fg_color="transparent", border_width=1,
            command=self._cancelar_revisao,
        ).pack(side="left")

    def iniciar_revisao_importacao(
        self,
        sugestoes: list[SugestaoImportacao],
        funcionarios_planilha: list[FuncionarioPlanilha],
        ao_concluir_calculo: Callable[[list[Funcionario]], None],
    ) -> None:
        """
        Ponto de entrada público do Painel de Revisão (Cap. 5.4). Recebe
        as sugestões, os `FuncionarioPlanilha` originais (para anexar
        `.dias` aos funcionários ao concluir — Cap. 6) e um callback
        chamado ao final de `_concluir_revisao()` com os funcionários já
        processáveis pelo Motor de Cálculo. Não persiste nada até
        "Concluir Importação" ser clicado.
        """
        # A barra de ações em massa (Cap. 5.9) pertence à lista normal de
        # funcionários, que fica escondida durante a revisão — mas ela não
        # é trocada por tkraise(), só por grid_remove(), então continuaria
        # visível/funcional por trás do Painel de Revisão se uma seleção
        # anterior não fosse limpa aqui. Sem isso, uma ação em massa
        # aplicada por engano durante a revisão gravaria funcionarios.json
        # e, ao concluir, `_concluir_revisao()` sobrescreveria esse valor
        # com o que a linha de revisão (com o status capturado antes)
        # decidir — revertendo a ação em massa silenciosamente.
        self._selecionados.clear()
        self._atualizar_barra_massa()

        for widget in self._scroll_revisao.winfo_children():
            widget.destroy()
        self._linhas_revisao = []
        self._funcionarios_planilha_pendente = funcionarios_planilha
        self._ao_concluir_calculo = ao_concluir_calculo

        existentes_por_id = {
            dados.get("id"): dados for dados in self.config_app.funcionarios.get("funcionarios", [])
        }

        opcoes_turno = self._opcoes_turno()
        opcoes_setor = self._opcoes_setor()
        for sugestao in sugestoes:
            dados_existente = (
                existentes_por_id.get(sugestao.funcionario_id) if sugestao.funcionario_id else None
            )
            status_inicial = (
                funcionario_de_dict(dados_existente).status
                if dados_existente is not None else StatusFuncionario.ATIVO
            )
            linha = _LinhaRevisao(
                self._scroll_revisao, sugestao, opcoes_turno, opcoes_setor, status_inicial)
            linha.pack(fill="x", pady=4)
            self._linhas_revisao.append(linha)

        self._ocultar_formulario()
        self._scroll_funcionarios.grid_remove()
        self._frame_revisao.grid(row=4, column=0, sticky="nsew", padx=30, pady=15)

    def _cancelar_revisao(self) -> None:
        """Fecha o Painel de Revisão sem persistir nada."""
        self._frame_revisao.grid_remove()
        self._scroll_funcionarios.grid(row=4, column=0, sticky="nsew", padx=30, pady=15)

    def _concluir_revisao(self) -> None:
        """
        Cria ou atualiza APENAS os funcionários presentes no lote
        revisado (Importação Parcial, Cap. 5.7) — funcionários ausentes
        desta importação nunca são excluídos, inativados ou perdem
        vínculo, pois nem são tocados por este método.

        Reconhece funcionários já cadastrados pelo `funcionario_id` que
        `montar_sugestoes_importacao()` (cadastro.py) já resolveu por
        `id_planilha`/nome (Cap. 5.6/5.8/5.13-Competências) — esse
        casamento só acontece uma vez, lá; aqui é sempre por ID,
        evitando refazer a mesma busca duas vezes. Para cada
        funcionário do lote, anexa os dias/batidas do
        `FuncionarioPlanilha` correspondente (em memória, nunca
        persistido em funcionarios.json — Cap. 16) e, ao final, entrega
        a lista ao callback de conclusão para o Motor de Cálculo
        (Cap. 6) processar, sem exigir uma segunda importação.

        `self._linhas_revisao` e `self._funcionarios_planilha_pendente`
        correspondem 1:1 por POSIÇÃO (montados por iteração posicional
        simples em `montar_sugestoes_importacao()`/`iniciar_revisao_importacao()`,
        sem reordenar/filtrar em nenhum passo) — por isso o pareamento é
        feito com `zip()`, nunca por busca de nome. Localizar por nome
        aqui quebraria silenciosamente assim que dois funcionários reais
        homônimos (mesmo nome, `id_planilha` diferente) aparecessem na
        mesma importação: a busca por nome sempre devolveria o primeiro
        para os dois, misturando os `.dias` de pessoas diferentes.

        Funcionários marcados como Inativo na coluna Status (Melhoria
        1) são cadastrados/atualizados normalmente, mas NÃO entram em
        `funcionarios_processaveis` — não são calculados, não geram
        pendência e não aparecem nos relatórios desta competência.
        """
        funcionarios_dict = self.config_app.funcionarios.setdefault("funcionarios", [])
        existentes = [funcionario_de_dict(d) for d in funcionarios_dict]
        existentes_por_id = {f.id: f for f in existentes}
        agora = _agora_texto()
        funcionarios_processaveis: list[Funcionario] = []
        ids_ja_processados: set[str] = set()

        for linha, funcionario_planilha in zip(
            self._linhas_revisao, self._funcionarios_planilha_pendente,
        ):
            sugestao = linha.sugestao
            turno_id = linha.turno_id_selecionado() or ""
            setor_id = linha.setor_id_selecionado() or ""
            status_selecionado = linha.status_selecionado()
            encontrado = (
                existentes_por_id.get(sugestao.funcionario_id)
                if sugestao.funcionario_id else None
            )

            # Guarda contra IDUsuário reaproveitado por engano na origem:
            # duas linhas resolvendo para o MESMO cadastro sobrescreveriam
            # uma a dias/turno/setor da outra silenciosamente. Caso raro,
            # mas barato de detectar — a segunda linha é ignorada e fica
            # registrada em log para investigação manual.
            if encontrado is not None and encontrado.id in ids_ja_processados:
                log.error(
                    'Duas linhas da revisão resolveram para o mesmo cadastro "%s" '
                    "(IDUsuário duplicado na planilha?) — a segunda foi ignorada.",
                    encontrado.nome_completo,
                )
                continue

            if encontrado is not None:
                encontrado.nome_planilha = sugestao.nome_planilha
                encontrado.id_planilha = sugestao.id_planilha
                if turno_id:
                    encontrado.turno_id = turno_id
                if setor_id:
                    encontrado.setor_id = setor_id
                encontrado.status = status_selecionado
                encontrado.ultima_atualizacao = agora
                for indice, dados in enumerate(funcionarios_dict):
                    if dados.get("id") == encontrado.id:
                        funcionarios_dict[indice] = funcionario_para_dict(encontrado)
                        break
                funcionario_atual = encontrado
                ids_ja_processados.add(encontrado.id)
            else:
                novo = Funcionario(
                    nome_completo=sugestao.nome_planilha,
                    nome_planilha=sugestao.nome_planilha,
                    id_planilha=sugestao.id_planilha,
                    turno_id=turno_id,
                    setor_id=setor_id,
                    status=status_selecionado,
                    data_cadastro=agora,
                    ultima_atualizacao=agora,
                )
                funcionarios_dict.append(funcionario_para_dict(novo))
                existentes.append(novo)
                funcionario_atual = novo
                ids_ja_processados.add(novo.id)

            if status_selecionado == StatusFuncionario.ATIVO:
                funcionario_atual.dias = funcionario_planilha.dias
                funcionarios_processaveis.append(funcionario_atual)

        self.config_app.salvar_funcionarios()
        self._frame_revisao.grid_remove()
        self._scroll_funcionarios.grid(row=4, column=0, sticky="nsew", padx=30, pady=15)
        self._carregar_lista()

        ao_concluir_calculo = self._ao_concluir_calculo
        self._ao_concluir_calculo = None
        if ao_concluir_calculo is not None:
            ao_concluir_calculo(funcionarios_processaveis)

    # -- Tela "Foram encontrados novos setores na planilha" (Cap. 5.17) --------

    def _montar_painel_setores_novos(self) -> None:
        self._frame_setores_novos = ctk.CTkFrame(self, fg_color="transparent")
        # Não posicionado aqui — só aparece via iniciar_revisao_setores_novos()

        ctk.CTkLabel(
            self._frame_setores_novos, text="Foram encontrados novos setores na planilha.",
            font=ctk.CTkFont(size=18, weight="bold"),
        ).pack(anchor="w", pady=(0, 5))

        ctk.CTkLabel(
            self._frame_setores_novos,
            text=(
                "Selecione quais deverão ser criados automaticamente antes de "
                "continuar a importação."
            ),
            text_color=("gray60", "gray60"),
        ).pack(anchor="w", pady=(0, 10))

        self._scroll_setores_novos = ctk.CTkScrollableFrame(
            self._frame_setores_novos, height=260)
        self._scroll_setores_novos.pack(fill="both", expand=True)

        linha_botoes = ctk.CTkFrame(self._frame_setores_novos, fg_color="transparent")
        linha_botoes.pack(fill="x", pady=(15, 0))
        ctk.CTkButton(
            linha_botoes, text="Criar selecionados", command=self._confirmar_setores_novos,
        ).pack(side="left", padx=(0, 10))
        ctk.CTkButton(
            linha_botoes, text="Ignorar", fg_color="transparent", border_width=1,
            command=self._ignorar_setores_novos,
        ).pack(side="left")

    def iniciar_revisao_setores_novos(
        self, setores_novos: list[SetorNovoEncontrado], ao_concluir: Callable[[], None],
    ) -> None:
        """
        Ponto de entrada público (Cap. 5.17). Recebe os "Dep." da
        planilha que ainda não têm Setor cadastrado correspondente e
        exibe a tela de confirmação antes de continuar a importação.

        `ao_concluir` é chamado assim que o usuário decidir (criando os
        Setores selecionados ou ignorando) — é assim que a importação
        retoma exatamente de onde parou, sem exigir uma segunda
        importação (quem chama, tela_principal.py, é quem sabe como
        continuar montando as sugestões).
        """
        # Mesmo motivo do Painel de Revisão (ver iniciar_revisao_importacao):
        # a barra de ações em massa não é trocada por tkraise(), então uma
        # seleção anterior continuaria visível/funcional por trás desta tela.
        self._selecionados.clear()
        self._atualizar_barra_massa()

        for widget in self._scroll_setores_novos.winfo_children():
            widget.destroy()
        self._linhas_setores_novos = [
            _LinhaSetorNovo(self._scroll_setores_novos, setor_novo)
            for setor_novo in setores_novos
        ]
        for linha in self._linhas_setores_novos:
            linha.pack(fill="x", pady=4)

        self._ao_concluir_setores_novos = ao_concluir

        self._ocultar_formulario()
        self._scroll_funcionarios.grid_remove()
        self._frame_setores_novos.grid(row=4, column=0, sticky="nsew", padx=30, pady=15)

    def _confirmar_setores_novos(self) -> None:
        """
        Cria cada Setor selecionado (Cap. 5.17/21.8), reaproveitando
        integralmente Setor, setor_para_dict() e Config.salvar_setores()
        — o mesmo mecanismo já usado pelo cadastro manual de Setores
        (tela_setores.py). Nenhuma persistência nova é criada aqui.
        """
        nomes_selecionados = [
            linha.nome for linha in self._linhas_setores_novos if linha.selecionado()
        ]
        if nomes_selecionados:
            setores_dict = self.config_app.setores.setdefault("setores", [])
            for nome in nomes_selecionados:
                setores_dict.append(setor_para_dict(Setor(nome=nome)))
            self.config_app.salvar_setores()
            log.info(
                "Setor(es) criado(s) automaticamente durante a importação: %s.",
                ", ".join(nomes_selecionados),
            )

        self._concluir_setores_novos()

    def _ignorar_setores_novos(self) -> None:
        """Não cria nenhum Setor novo — os "Dep." correspondentes permanecem ⚠ Revisar."""
        self._concluir_setores_novos()

    def _concluir_setores_novos(self) -> None:
        """Esconde a tela de confirmação e retoma a importação de onde parou."""
        self._frame_setores_novos.grid_remove()
        ao_concluir = self._ao_concluir_setores_novos
        self._ao_concluir_setores_novos = None
        if ao_concluir is not None:
            ao_concluir()
