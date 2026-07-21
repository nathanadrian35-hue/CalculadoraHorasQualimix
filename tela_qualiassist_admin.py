"""
tela_qualiassist_admin.py
----------------------------
Painel Administrativo do QualiAssist (v2.1 Sprint 3, Cap. 28) —
cadastrar/editar/ativar-desativar artigos da base de conhecimento,
importar/exportar a base, com versionamento automático
(`qualiassist.salvar_base`, Cap. 29).

Categorias são um Enum fixo (Cap. 7 — mesmo agrupamento do menu do
sistema), não editável por aqui: criar uma categoria nova exigiria
código (`constantes.CategoriaQualiAssist`), não é um dado de
configuração solto.
"""

from __future__ import annotations

import json
from pathlib import Path
from tkinter import filedialog, messagebox
from typing import Callable

import customtkinter as ctk

import qualiassist
from componentes import ColunaOrdenavel, TabelaPadrao
from config import Config
from constantes import CategoriaQualiAssist
from logger import get_logger
from modelos import ArtigoQualiAssist, BaseQualiAssist

log = get_logger()


# ---------------------------------------------------------------------------
# Linha de um artigo
# ---------------------------------------------------------------------------

class _LinhaArtigo(ctk.CTkFrame):
    """Uma linha reaproveitável do pool de `TabelaPadrao` — um artigo da base."""

    def __init__(
        self, master,
        ao_editar: Callable[[ArtigoQualiAssist], None],
        ao_alternar_ativo: Callable[[ArtigoQualiAssist], None],
    ) -> None:
        super().__init__(master, corner_radius=8, border_width=1)
        self.artigo: ArtigoQualiAssist | None = None

        self.grid_columnconfigure(0, weight=2)
        self.grid_columnconfigure(1, weight=1)

        self._rotulo_titulo = ctk.CTkLabel(
            self, anchor="w", font=ctk.CTkFont(weight="bold"))
        self._rotulo_titulo.grid(row=0, column=0, sticky="w", padx=12, pady=10)

        self._rotulo_categoria = ctk.CTkLabel(self, anchor="w", width=150)
        self._rotulo_categoria.grid(row=0, column=1, padx=5)

        self._rotulo_status = ctk.CTkLabel(self, width=60)
        self._rotulo_status.grid(row=0, column=2, padx=5)

        ctk.CTkButton(
            self, text="Editar", width=80, command=lambda: self._chamar(ao_editar),
        ).grid(row=0, column=3, padx=(5, 5), pady=10)
        ctk.CTkButton(
            self, text="", width=90, fg_color="transparent", border_width=1,
            command=lambda: self._chamar(ao_alternar_ativo),
        ).grid(row=0, column=4, padx=(0, 12))
        self._botao_alternar = self.grid_slaves(row=0, column=4)[0]

    def vincular(self, artigo: ArtigoQualiAssist) -> None:
        self.artigo = artigo
        self._rotulo_titulo.configure(text=artigo.titulo)
        self._rotulo_categoria.configure(text=artigo.categoria.value)
        self._rotulo_status.configure(
            text="Ativo" if artigo.ativo else "Inativo",
            text_color=("#1e8449", "#2ecc71") if artigo.ativo else ("gray50", "gray50"),
        )
        self._botao_alternar.configure(text="Inativar" if artigo.ativo else "Ativar")

    def _chamar(self, callback: Callable[[ArtigoQualiAssist], None]) -> None:
        if self.artigo is not None:
            callback(self.artigo)


# ---------------------------------------------------------------------------
# Formulário de artigo (novo/editar)
# ---------------------------------------------------------------------------

class _DialogoArtigo(ctk.CTkToplevel):
    """Formulário de criação/edição de um artigo (Cap. 28)."""

    def __init__(
        self, master, artigo: ArtigoQualiAssist | None, ao_salvar: Callable[[dict], None],
    ) -> None:
        super().__init__(master)
        self.title("Editar Artigo" if artigo is not None else "Novo Artigo")
        self.geometry("520x600")
        self.transient(master)
        self.grab_set()
        self._ao_salvar = ao_salvar
        self.grid_columnconfigure(0, weight=1)

        def _rotulo(texto: str) -> None:
            ctk.CTkLabel(self, text=texto, anchor="w").pack(
                anchor="w", padx=20, pady=(10, 2))

        _rotulo("Título")
        self._entry_titulo = ctk.CTkEntry(self)
        self._entry_titulo.pack(fill="x", padx=20)
        self._entry_titulo.insert(0, artigo.titulo if artigo else "")

        _rotulo("Categoria")
        self._var_categoria = ctk.StringVar(
            value=(artigo.categoria.value if artigo else list(CategoriaQualiAssist)[0].value))
        ctk.CTkOptionMenu(
            self, values=[c.value for c in CategoriaQualiAssist], variable=self._var_categoria,
        ).pack(anchor="w", padx=20)

        _rotulo("Palavras-chave (separadas por vírgula)")
        self._entry_palavras = ctk.CTkEntry(self)
        self._entry_palavras.pack(fill="x", padx=20)
        self._entry_palavras.insert(0, ", ".join(artigo.palavras_chave if artigo else []))

        _rotulo("Perguntas relacionadas (uma por linha)")
        self._texto_perguntas = ctk.CTkTextbox(self, height=60)
        self._texto_perguntas.pack(fill="x", padx=20)
        self._texto_perguntas.insert("1.0", "\n".join(artigo.perguntas if artigo else []))

        _rotulo("Resposta")
        self._texto_resposta = ctk.CTkTextbox(self, height=160)
        self._texto_resposta.pack(fill="both", expand=True, padx=20)
        self._texto_resposta.insert("1.0", artigo.resposta if artigo else "")

        _rotulo("Links internos (nomes de tela, separados por vírgula)")
        self._entry_links = ctk.CTkEntry(self)
        self._entry_links.pack(fill="x", padx=20)
        self._entry_links.insert(0, ", ".join(artigo.links_internos if artigo else []))

        linha_botoes = ctk.CTkFrame(self, fg_color="transparent")
        linha_botoes.pack(fill="x", padx=20, pady=15)
        ctk.CTkButton(linha_botoes, text="Salvar", command=self._salvar).pack(
            side="left", padx=(0, 10))
        ctk.CTkButton(
            linha_botoes, text="Cancelar", fg_color="transparent", border_width=1,
            command=self.destroy,
        ).pack(side="left")

    def _salvar(self) -> None:
        titulo = self._entry_titulo.get().strip()
        resposta = self._texto_resposta.get("1.0", "end").strip()
        if not titulo or not resposta:
            messagebox.showerror("Campos obrigatórios", "Título e Resposta são obrigatórios.")
            return

        dados = {
            "titulo": titulo,
            "categoria": self._var_categoria.get(),
            "palavras_chave": [
                p.strip() for p in self._entry_palavras.get().split(",") if p.strip()],
            "perguntas": [
                p.strip() for p in self._texto_perguntas.get("1.0", "end").splitlines()
                if p.strip()
            ],
            "resposta": resposta,
            "links_internos": [
                link.strip() for link in self._entry_links.get().split(",") if link.strip()],
        }
        self.destroy()
        self._ao_salvar(dados)


# ---------------------------------------------------------------------------
# Tela administrativa
# ---------------------------------------------------------------------------

class TelaQualiAssistAdmin(ctk.CTkFrame):
    """Painel Administrativo do QualiAssist (Cap. 28)."""

    def __init__(self, master, controlador, config: Config) -> None:
        super().__init__(master, corner_radius=0)
        self.controlador = controlador
        self.config_app = config
        self._base: BaseQualiAssist | None = None

        self.grid_rowconfigure(2, weight=1)
        self.grid_columnconfigure(0, weight=1)

        self._montar_cabecalho()
        self._montar_barra()
        self._montar_lista()

    def _montar_cabecalho(self) -> None:
        cabecalho = ctk.CTkFrame(self, corner_radius=0, height=70)
        cabecalho.grid(row=0, column=0, sticky="ew")
        cabecalho.grid_columnconfigure(1, weight=1)

        ctk.CTkButton(
            cabecalho, text="← Voltar", width=90,
            command=lambda: self.controlador.mostrar_tela("principal"),
        ).grid(row=0, column=0, padx=15, pady=15)

        ctk.CTkLabel(
            cabecalho, text="QualiAssist — Administração",
            font=ctk.CTkFont(size=20, weight="bold"),
        ).grid(row=0, column=1, sticky="w", padx=10)

        self._rotulo_versao = ctk.CTkLabel(
            cabecalho, text="", text_color=("gray60", "gray60"))
        self._rotulo_versao.grid(row=0, column=2, padx=15)

    def _montar_barra(self) -> None:
        barra = ctk.CTkFrame(self, fg_color="transparent")
        barra.grid(row=1, column=0, sticky="ew", padx=30, pady=(15, 0))

        ctk.CTkButton(
            barra, text="+ Novo Artigo", height=40, font=ctk.CTkFont(weight="bold"),
            command=lambda: self._abrir_formulario(None),
        ).pack(side="left")
        ctk.CTkButton(
            barra, text="Exportar Base (JSON)", fg_color="transparent", border_width=1,
            command=self._exportar_base,
        ).pack(side="left", padx=(10, 0))
        ctk.CTkButton(
            barra, text="Importar Base (JSON)", fg_color="transparent", border_width=1,
            command=self._importar_base,
        ).pack(side="left", padx=(10, 0))

    def _montar_lista(self) -> None:
        self._tabela = TabelaPadrao(
            self,
            criar_linha=lambda m: _LinhaArtigo(
                m, ao_editar=self._abrir_formulario, ao_alternar_ativo=self._alternar_ativo),
            colunas=[
                ColunaOrdenavel("Título", lambda a: a.titulo.lower()),
                ColunaOrdenavel("Categoria", lambda a: a.categoria.value),
            ],
            campos_pesquisa=[lambda a: a.titulo, lambda a: " ".join(a.palavras_chave)],
            texto_vazio="Nenhum artigo cadastrado.",
        )
        self._tabela.grid(row=2, column=0, sticky="nsew", padx=30, pady=15)

    # -- Ciclo de vida ---------------------------------------------------------

    def ao_exibir(self) -> None:
        self._base = qualiassist.carregar_base()
        self._rotulo_versao.configure(
            text=f"Versão {self._base.versao} — {len(self._base.artigos)} artigo(s)")
        self._tabela.definir_registros(self._base.artigos)

    # -- Ações -----------------------------------------------------------------

    def _abrir_formulario(self, artigo: ArtigoQualiAssist | None) -> None:
        _DialogoArtigo(self, artigo, ao_salvar=lambda dados: self._salvar_artigo(artigo, dados))

    def _salvar_artigo(self, artigo_existente: ArtigoQualiAssist | None, dados: dict) -> None:
        if self._base is None:
            return
        categoria = CategoriaQualiAssist(dados["categoria"])
        if artigo_existente is not None:
            artigo_existente.titulo = dados["titulo"]
            artigo_existente.categoria = categoria
            artigo_existente.palavras_chave = dados["palavras_chave"]
            artigo_existente.perguntas = dados["perguntas"]
            artigo_existente.resposta = dados["resposta"]
            artigo_existente.links_internos = dados["links_internos"]
        else:
            novo = ArtigoQualiAssist(
                titulo=dados["titulo"], categoria=categoria, resposta=dados["resposta"],
                palavras_chave=dados["palavras_chave"], perguntas=dados["perguntas"],
                links_internos=dados["links_internos"],
            )
            self._base.artigos.append(novo)

        qualiassist.salvar_base(self._base)
        self.controlador.definir_status("Base do QualiAssist atualizada.")
        self.ao_exibir()

    def _alternar_ativo(self, artigo: ArtigoQualiAssist) -> None:
        if self._base is None:
            return
        artigo.ativo = not artigo.ativo
        qualiassist.salvar_base(self._base)
        self.ao_exibir()

    def _exportar_base(self) -> None:
        if self._base is None:
            return
        caminho_texto = filedialog.asksaveasfilename(
            title="Exportar base do QualiAssist", defaultextension=".json",
            filetypes=[("JSON", "*.json")],
        )
        if not caminho_texto:
            return
        dados = {
            "artigos": [qualiassist.artigo_para_dict(a) for a in self._base.artigos],
            "versao": self._base.versao, "atualizado_em": self._base.atualizado_em,
        }
        Path(caminho_texto).write_text(
            json.dumps(dados, ensure_ascii=False, indent=4), encoding="utf-8")
        messagebox.showinfo("Exportado", f"Base exportada para:\n{caminho_texto}")

    def _importar_base(self) -> None:
        caminho_texto = filedialog.askopenfilename(
            title="Importar base do QualiAssist", filetypes=[("JSON", "*.json")])
        if not caminho_texto:
            return
        confirmar = messagebox.askyesno(
            "Importar base",
            "Importar substituirá TODOS os artigos atuais pelos do arquivo escolhido. Continuar?",
        )
        if not confirmar:
            return
        try:
            dados = json.loads(Path(caminho_texto).read_text(encoding="utf-8"))
            artigos = [
                a for a in (qualiassist.artigo_de_dict(item) for item in dados.get("artigos", []))
                if a is not None
            ]
        except (OSError, ValueError, json.JSONDecodeError) as erro:
            messagebox.showerror("Não foi possível importar", str(erro))
            return

        self._base = BaseQualiAssist(artigos=artigos, versao=self._base.versao if self._base else 1)
        qualiassist.salvar_base(self._base)
        self.controlador.definir_status("Base do QualiAssist importada.")
        self.ao_exibir()
