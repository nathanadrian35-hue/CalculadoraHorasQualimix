"""
tela_setores.py
----------------
Tela de Cadastro de Setores (Cap. 21).

Sprint 2.5: cadastro de setores da empresa — nome, cor (opcional, uso
futuro em gráficos/relatórios, escolhida via o seletor gráfico nativo
do Tkinter — tkinter.colorchooser) e status (Ativo/Inativo). Permite
adicionar, editar, ativar/inativar e excluir (com confirmação e
verificação de vínculo com funcionários, preparada para a Sprint 3).

Persistido em dados/setores.json através de config.py, reaproveitando
exatamente o mesmo padrão de leitura/escrita/backup automático já usado
pelas demais configurações do sistema — nenhuma lógica de persistência
nova é criada aqui.
"""

from __future__ import annotations

import os
import tkinter as tk
from tkinter import colorchooser, messagebox
from typing import Callable

import customtkinter as ctk

from componentes import BotaoExportar, ColunaOrdenavel, TabelaPadrao
from config import Config, setor_de_dict, setor_para_dict
from constantes import StatusFuncionario
from exportacao import caminho_exportacao, exportar_excel_simples
from logger import get_logger
from modelos import Setor, nome_duplicado

log = get_logger()


# ---------------------------------------------------------------------------
# Linha de um único setor (componente reaproveitável — Sprint 1, v2.1)
# ---------------------------------------------------------------------------

class _LinhaSetor(ctk.CTkFrame):
    """
    Uma linha reaproveitável do pool de `TabelaPadrao` (Sprint 1,
    v2.1): todos os widgets são criados uma única vez em `__init__` —
    `vincular()` só troca qual Setor esta linha exibe, sem recriar
    nada (mesmo padrão de `_LinhaPendencia`, tela_pendencias.py).
    """

    def __init__(
        self,
        master,
        ao_editar: Callable[[Setor], None],
        ao_alternar_status: Callable[[Setor], None],
        ao_excluir: Callable[[Setor], None],
    ) -> None:
        super().__init__(master, corner_radius=8, border_width=1)
        self.setor: Setor | None = None
        self._ao_editar = ao_editar
        self._ao_alternar_status = ao_alternar_status
        self._ao_excluir = ao_excluir

        self.grid_columnconfigure(1, weight=1)

        self._quadro_cor = ctk.CTkFrame(self, width=18, height=18, corner_radius=4)
        self._quadro_cor.grid(row=0, column=0, padx=(12, 0), pady=12)

        self._rotulo_nome = ctk.CTkLabel(
            self, font=ctk.CTkFont(size=14, weight="bold"), anchor="w")
        self._rotulo_nome.grid(row=0, column=1, sticky="w", padx=12, pady=12)

        self._rotulo_status = ctk.CTkLabel(self, font=ctk.CTkFont(size=12), width=70)
        self._rotulo_status.grid(row=0, column=2, padx=10)

        self._botao_editar = ctk.CTkButton(
            self, text="Editar", width=80, command=self._clicar_editar)
        self._botao_editar.grid(row=0, column=3, padx=(0, 8), pady=12)

        self._botao_alternar = ctk.CTkButton(
            self, text="", width=80, fg_color="transparent", border_width=1,
            command=self._clicar_alternar_status,
        )
        self._botao_alternar.grid(row=0, column=4, padx=(0, 8), pady=12)

        self._botao_excluir = ctk.CTkButton(
            self, text="Excluir", width=80, fg_color="#c0392b", hover_color="#992d22",
            command=self._clicar_excluir,
        )
        self._botao_excluir.grid(row=0, column=5, padx=(0, 12), pady=12)

    def _clicar_editar(self) -> None:
        if self.setor is not None:
            self._ao_editar(self.setor)

    def _clicar_alternar_status(self) -> None:
        if self.setor is not None:
            self._ao_alternar_status(self.setor)

    def _clicar_excluir(self) -> None:
        if self.setor is not None:
            self._ao_excluir(self.setor)

    def vincular(self, setor: Setor) -> None:
        self.setor = setor
        if setor.cor:
            self._aplicar_cor(setor.cor)
        else:
            self._quadro_cor.configure(fg_color="transparent")
        self._rotulo_nome.configure(text=setor.nome)

        ativo = setor.status == StatusFuncionario.ATIVO
        self._rotulo_status.configure(
            text=setor.status.value,
            text_color=("#1e8449", "#2ecc71") if ativo else ("gray50", "gray50"),
        )
        self._botao_alternar.configure(text="Inativar" if ativo else "Ativar")

    def _aplicar_cor(self, cor: str) -> None:
        """Aplica a cor informada ao indicador visual, ignorando valores inválidos."""
        try:
            self._quadro_cor.configure(fg_color=cor)
        except tk.TclError:
            self._quadro_cor.configure(fg_color="gray40")


# ---------------------------------------------------------------------------
# Tela de Setores
# ---------------------------------------------------------------------------

class TelaSetores(ctk.CTkFrame):
    """Tela de gerenciamento de setores (Cap. 21)."""

    def __init__(self, master, controlador, config: Config) -> None:
        super().__init__(master, corner_radius=0)

        self.controlador = controlador
        self.config_app = config
        self._setor_em_edicao_id: str | None = None
        self._cor_selecionada: str = ""

        self.grid_rowconfigure(3, weight=1)
        self.grid_columnconfigure(0, weight=1)

        self._montar_cabecalho()
        self._montar_botao_adicionar()
        self._montar_formulario()
        self._montar_lista()

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
            cabecalho, text="Setores",
            font=ctk.CTkFont(size=20, weight="bold"),
        ).grid(row=0, column=1, sticky="w", padx=10)

    def _montar_botao_adicionar(self) -> None:
        barra = ctk.CTkFrame(self, fg_color="transparent")
        barra.grid(row=1, column=0, sticky="ew", padx=30, pady=(15, 0))

        ctk.CTkButton(
            barra, text="+ Adicionar Setor", height=44,
            font=ctk.CTkFont(size=14, weight="bold"), corner_radius=10,
            command=lambda: self._mostrar_formulario(),
        ).pack(side="left")

        ctk.CTkButton(
            barra, text="Imprimir", width=100, fg_color="transparent", border_width=1,
            command=self._imprimir,
        ).pack(side="right")

        BotaoExportar(
            barra, titulo="Setores", colunas=["Nome", "Cor", "Status"],
            obter_registros=lambda: self._tabela.registros_filtrados(),
            montar_linha=lambda s: (s.nome, s.cor or "—", s.status.value),
            caminho_sugerido=lambda extensao: caminho_exportacao(
                self.config_app, "Setores", "Setores", extensao),
        ).pack(side="right", padx=(0, 10))

    # -- Formulário (reaproveitado para adicionar e editar) --------------------

    def _montar_formulario(self) -> None:
        """
        Formulário único usado tanto para adicionar quanto para editar —
        evita duplicar campos/validação entre os dois fluxos. Fica
        oculto (não posicionado) até `_mostrar_formulario()` ser chamado.
        """
        self._frame_formulario = ctk.CTkFrame(self, corner_radius=10)
        self._frame_formulario.grid_columnconfigure(1, weight=1)

        self._rotulo_titulo_formulario = ctk.CTkLabel(
            self._frame_formulario, text="Novo Setor",
            font=ctk.CTkFont(size=16, weight="bold"), anchor="w",
        )
        self._rotulo_titulo_formulario.grid(
            row=0, column=0, columnspan=4, sticky="w", padx=15, pady=(15, 10))

        ctk.CTkLabel(self._frame_formulario, text="Nome").grid(
            row=1, column=0, sticky="w", padx=(15, 5))
        self._entry_nome_setor = ctk.CTkEntry(
            self._frame_formulario, placeholder_text="Nome do setor")
        self._entry_nome_setor.grid(row=1, column=1, columnspan=3, sticky="ew", padx=(0, 15))
        self._entry_nome_setor.bind(
            "<KeyRelease>", lambda evento: self._validar_formulario())

        ctk.CTkLabel(self._frame_formulario, text="Cor (opcional)").grid(
            row=2, column=0, sticky="w", padx=(15, 5), pady=(10, 0))

        linha_cor = ctk.CTkFrame(self._frame_formulario, fg_color="transparent")
        linha_cor.grid(row=2, column=1, columnspan=3, sticky="w", pady=(10, 0))

        self._quadro_preview_cor = ctk.CTkFrame(
            linha_cor, width=22, height=22, corner_radius=4, border_width=1,
        )
        self._quadro_preview_cor.pack(side="left", padx=(0, 8))

        self._rotulo_cor_selecionada = ctk.CTkLabel(
            linha_cor, text="Nenhuma cor selecionada", anchor="w",
            text_color=("gray50", "gray50"),
        )
        self._rotulo_cor_selecionada.pack(side="left", padx=(0, 12))

        ctk.CTkButton(
            linha_cor, text="🎨 Escolher Cor", width=140, command=self._escolher_cor,
        ).pack(side="left")

        self._rotulo_erro_formulario = ctk.CTkLabel(
            self._frame_formulario, text="", text_color=("#c0392b", "#e74c3c"), anchor="w",
        )
        self._rotulo_erro_formulario.grid(
            row=3, column=0, columnspan=4, sticky="ew", padx=15, pady=(10, 0))

        linha_botoes = ctk.CTkFrame(self._frame_formulario, fg_color="transparent")
        linha_botoes.grid(row=4, column=0, columnspan=4, sticky="w", padx=15, pady=(10, 15))
        ctk.CTkButton(
            linha_botoes, text="Salvar", command=self._salvar_formulario,
        ).pack(side="left", padx=(0, 10))
        ctk.CTkButton(
            linha_botoes, text="Cancelar", fg_color="transparent", border_width=1,
            command=self._ocultar_formulario,
        ).pack(side="left")

    def _mostrar_formulario(self, setor: Setor | None = None) -> None:
        """Exibe o formulário em modo "novo" (setor=None) ou "editar"."""
        self._setor_em_edicao_id = setor.id if setor is not None else None
        self._rotulo_titulo_formulario.configure(
            text="Editar Setor" if setor is not None else "Novo Setor"
        )

        self._entry_nome_setor.delete(0, "end")
        self._entry_nome_setor.insert(0, setor.nome if setor is not None else "")
        self._definir_cor_selecionada(setor.cor if setor is not None else "")
        self._rotulo_erro_formulario.configure(text="")

        self._frame_formulario.grid(row=2, column=0, sticky="ew", padx=30, pady=(15, 0))

    def _ocultar_formulario(self) -> None:
        self._frame_formulario.grid_remove()
        self._setor_em_edicao_id = None

    def _validar_formulario(self) -> bool:
        """Valida em tempo real: nome obrigatório e único entre os setores (Cap. 21.2)."""
        nome = self._entry_nome_setor.get().strip()
        if not nome:
            self._rotulo_erro_formulario.configure(text="Informe o nome do setor.")
            return False
        if self._nome_duplicado(nome):
            self._rotulo_erro_formulario.configure(
                text=f'Já existe um setor chamado "{nome}".')
            return False
        self._rotulo_erro_formulario.configure(text="")
        return True

    def _nome_duplicado(self, nome: str) -> bool:
        """True se outro setor (diferente do que está sendo editado) já usa esse nome."""
        outros_nomes = [
            dados.get("nome", "")
            for dados in self.config_app.setores.get("setores", [])
            if dados.get("id") != self._setor_em_edicao_id
        ]
        return nome_duplicado(nome, outros_nomes)

    # -- Seletor de cor gráfico (Cap. 21.2) -------------------------------------

    def _escolher_cor(self) -> None:
        """
        Abre o seletor de cores nativo do Tkinter. Se o usuário cancelar,
        a cor anterior é mantida — nada é alterado.
        """
        cor_inicial = self._cor_selecionada or None
        _rgb, cor_hex = colorchooser.askcolor(
            color=cor_inicial, title="Escolher cor do setor",
        )
        if cor_hex is None:
            return
        self._definir_cor_selecionada(cor_hex)

    def _definir_cor_selecionada(self, cor: str) -> None:
        """Atualiza a cor atual do formulário: preview e texto HEX exibido."""
        self._cor_selecionada = cor or ""
        if self._cor_selecionada:
            self._aplicar_cor_preview(self._cor_selecionada)
            self._rotulo_cor_selecionada.configure(
                text=self._cor_selecionada, text_color=("gray10", "gray90"),
            )
        else:
            self._quadro_preview_cor.configure(fg_color="transparent")
            self._rotulo_cor_selecionada.configure(
                text="Nenhuma cor selecionada", text_color=("gray50", "gray50"),
            )

    def _aplicar_cor_preview(self, cor: str) -> None:
        """Aplica a cor ao quadro de preview, ignorando valores inválidos."""
        try:
            self._quadro_preview_cor.configure(fg_color=cor)
        except tk.TclError:
            self._quadro_preview_cor.configure(fg_color="gray40")

    def _salvar_formulario(self) -> None:
        """
        Cria um novo setor ou atualiza um existente — um único método
        para os dois fluxos, evitando lógica duplicada entre "adicionar"
        e "editar".
        """
        if not self._validar_formulario():
            return

        nome = self._entry_nome_setor.get().strip()
        cor = self._cor_selecionada
        setores = self.config_app.setores.setdefault("setores", [])

        if self._setor_em_edicao_id is not None:
            for indice, dados in enumerate(setores):
                if dados.get("id") == self._setor_em_edicao_id:
                    setor_existente = setor_de_dict(dados)
                    setor_atualizado = Setor(
                        id=setor_existente.id, nome=nome, cor=cor,
                        status=setor_existente.status,
                    )
                    setores[indice] = setor_para_dict(setor_atualizado)
                    break
        else:
            setores.append(setor_para_dict(Setor(nome=nome, cor=cor)))

        self.config_app.salvar_setores()
        self._ocultar_formulario()
        self._carregar_lista()

    # -- Lista de setores --------------------------------------------------------

    def _montar_lista(self) -> None:
        self._tabela = TabelaPadrao(
            self,
            criar_linha=lambda m: _LinhaSetor(
                m, ao_editar=self._mostrar_formulario,
                ao_alternar_status=self._alternar_status,
                ao_excluir=self._excluir_setor,
            ),
            colunas=[
                ColunaOrdenavel("Nome", lambda s: s.nome),
                ColunaOrdenavel("Status", lambda s: s.status.value),
            ],
            campos_pesquisa=[lambda s: s.nome],
            texto_vazio="Nenhum setor cadastrado ainda.",
        )
        self._tabela.grid(row=3, column=0, sticky="nsew", padx=30, pady=15)

    def ao_exibir(self) -> None:
        """Recarrega a lista sempre que a tela é exibida (Sprint 1: hook padrão)."""
        self._carregar_lista()

    def _carregar_lista(self) -> None:
        """(Re)carrega a lista de setores a partir de config.setores."""
        setores = [setor_de_dict(dados) for dados in self.config_app.setores.get("setores", [])]
        self._tabela.definir_registros(setores)

    # -- Ações -----------------------------------------------------------------

    def _alternar_status(self, setor: Setor) -> None:
        """Ativa/Inativa o setor imediatamente (Cap. 21.3)."""
        for dados in self.config_app.setores.get("setores", []):
            if dados.get("id") == setor.id:
                novo_status = (
                    StatusFuncionario.INATIVO if setor.status == StatusFuncionario.ATIVO
                    else StatusFuncionario.ATIVO
                )
                dados["status"] = novo_status.value
                break

        self.config_app.salvar_setores()
        self._carregar_lista()

    def _excluir_setor(self, setor: Setor) -> None:
        """
        Exclui um setor, com confirmação obrigatória (Cap. 21.3) e
        verificação de vínculo com funcionários (Cap. 21.5).
        """
        if self._setor_possui_vinculo(setor.id):
            messagebox.showerror(
                "Não é possível excluir",
                f'O setor "{setor.nome}" possui funcionários vinculados e não pode ser excluído.',
            )
            return

        confirmar = messagebox.askyesno(
            "Confirmar exclusão",
            f'Excluir o setor "{setor.nome}"? Esta ação não pode ser desfeita.',
        )
        if not confirmar:
            return

        setores = self.config_app.setores.get("setores", [])
        self.config_app.setores["setores"] = [
            dados for dados in setores if dados.get("id") != setor.id
        ]
        self.config_app.salvar_setores()
        self._carregar_lista()

    def _imprimir(self) -> None:
        """Impressão universal (Sprint 1): gera o Excel da lista e envia à impressora padrão."""
        registros = self._tabela.registros_filtrados()
        if not registros:
            messagebox.showinfo("Imprimir", "Não há registros para imprimir.")
            return
        caminho = caminho_exportacao(self.config_app, "Setores", "Setores", "xlsx")
        exportar_excel_simples(
            caminho, "Setores", ["Nome", "Cor", "Status"],
            [(s.nome, s.cor or "—", s.status.value) for s in registros],
        )
        try:
            os.startfile(str(caminho), "print")  # type: ignore[attr-defined]
            self.controlador.definir_status(f"Enviado para impressão: {caminho.name}")
        except OSError as erro:
            log.error("Falha ao imprimir setores: %s", erro)
            messagebox.showerror(
                "Não foi possível imprimir",
                f"Não foi possível enviar para impressão automaticamente. "
                f"O arquivo foi gerado em:\n{caminho}",
            )

    def _setor_possui_vinculo(self, setor_id: str) -> bool:
        """Verifica se existe algum funcionário vinculado a este setor (Cap. 21.5)."""
        funcionarios = self.config_app.funcionarios.get("funcionarios", [])
        return any(f.get("setor_id") == setor_id for f in funcionarios)
