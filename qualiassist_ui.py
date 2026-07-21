"""
qualiassist_ui.py
-------------------
Painel do QualiAssist (v2.1 Sprint 3, Documento 3 Cap. 5-6/9/15-19/33-34)
— um `CTkToplevel` único, reaproveitado (nunca recriado) por toda a
sessão, aberto pelo botão flutuante (`qualiassist_flutuante.py`).

Não altera nenhum dado do sistema (Cap. 4) — só lê/pesquisa a base de
conhecimento e grava seu próprio histórico/favoritos
(`qualiassist.py`).
"""

from __future__ import annotations

import tkinter as tk
from pathlib import Path
from tkinter import messagebox

import customtkinter as ctk

import qualiassist
from constantes import APP_NOME, CategoriaQualiAssist
from exportacao import exportar_pdf_simples
from modelos import ArtigoQualiAssist, RegistroHistoricoQualiAssist

_TODAS_CATEGORIAS = "Todas as categorias"
_SAUDACAO = (
    f"Olá! Sou o QualiAssist.\n\n"
    f"Estou aqui para ajudar você a utilizar o {APP_NOME}.\n"
    "Digite sua dúvida ou escolha uma categoria abaixo."
)


class PainelQualiAssist(ctk.CTkToplevel):
    """
    Painel lateral do QualiAssist — pesquisa, categorias, histórico e
    favoritos (Cap. 5). Fechar (X ou "Fechar") só esconde a janela —
    ela é criada uma única vez e reaproveitada, nunca destruída/
    recriada a cada abertura.
    """

    def __init__(self, master, controlador) -> None:
        super().__init__(master)
        self.controlador = controlador
        self.title("QualiAssist")
        self.geometry("420x620")
        self.minsize(360, 480)
        self.protocol("WM_DELETE_WINDOW", self.withdraw)

        self._base = qualiassist.carregar_base()
        self._historico = qualiassist.carregar_historico()
        self._artigo_aberto: ArtigoQualiAssist | None = None
        self._aba_atual = "Buscar"

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(3, weight=1)

        self._montar_cabecalho()
        self._montar_busca()
        self._montar_abas()
        self._montar_area_respostas()
        self._montar_rodape()

        self.withdraw()

    # -- Construção da UI -----------------------------------------------------

    def _montar_cabecalho(self) -> None:
        cabecalho = ctk.CTkFrame(self, corner_radius=0, height=48)
        cabecalho.grid(row=0, column=0, sticky="ew")
        cabecalho.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(
            cabecalho, text="🤖 QualiAssist", font=ctk.CTkFont(size=16, weight="bold"),
        ).grid(row=0, column=0, sticky="w", padx=15, pady=10)

        ctk.CTkButton(
            cabecalho, text="⚙", width=32, fg_color="transparent",
            command=self._abrir_administracao,
        ).grid(row=0, column=1, padx=(0, 5))

        ctk.CTkButton(
            cabecalho, text="✕", width=32, fg_color="transparent", command=self.withdraw,
        ).grid(row=0, column=2, padx=(0, 10))

    def _montar_busca(self) -> None:
        barra = ctk.CTkFrame(self, fg_color="transparent")
        barra.grid(row=1, column=0, sticky="ew", padx=15, pady=(10, 0))
        barra.grid_columnconfigure(0, weight=1)

        self._entry_busca = ctk.CTkEntry(barra, placeholder_text="Digite sua dúvida...")
        self._entry_busca.grid(row=0, column=0, sticky="ew", padx=(0, 8))
        self._entry_busca.bind("<Return>", lambda evento: self._buscar())
        self._entry_busca.bind("<KeyRelease>", lambda evento: self._buscar())

        self._var_categoria = tk.StringVar(value=_TODAS_CATEGORIAS)
        ctk.CTkOptionMenu(
            barra, values=[_TODAS_CATEGORIAS] + [c.value for c in CategoriaQualiAssist],
            variable=self._var_categoria, width=150,
            command=lambda valor: self._buscar(),
        ).grid(row=0, column=1)

    def _montar_abas(self) -> None:
        self._abas = ctk.CTkSegmentedButton(
            self, values=["Buscar", "Histórico", "Favoritos"], command=self._trocar_aba,
        )
        self._abas.set("Buscar")
        self._abas.grid(row=2, column=0, sticky="ew", padx=15, pady=(10, 0))

    def _montar_area_respostas(self) -> None:
        self._scroll = ctk.CTkScrollableFrame(self, fg_color="transparent")
        self._scroll.grid(row=3, column=0, sticky="nsew", padx=15, pady=10)
        self._scroll.grid_columnconfigure(0, weight=1)

    def _montar_rodape(self) -> None:
        rodape = ctk.CTkFrame(self, fg_color="transparent")
        rodape.grid(row=4, column=0, sticky="ew", padx=15, pady=(0, 15))

        ctk.CTkButton(
            rodape, text="Limpar histórico", width=110, fg_color="transparent", border_width=1,
            command=self._limpar_historico,
        ).pack(side="left", padx=(0, 8))
        ctk.CTkButton(
            rodape, text="Explicar esta Tela", width=140, command=self._explicar_tela_atual,
        ).pack(side="left")

    def _abrir_administracao(self) -> None:
        """Painel Administrativo (Cap. 28) — tela própria, navegável no container principal."""
        if hasattr(self.controlador, "mostrar_tela"):
            self.controlador.mostrar_tela("qualiassist_admin")
        self.withdraw()

    # -- Abrir/fechar -----------------------------------------------------------

    def abrir(self, consulta_inicial: str = "") -> None:
        """
        Abre o painel (Cap. 5) — quando chamado com ajuda contextual
        (Cap. 8), já sugere a categoria da tela atualmente visível e,
        se `consulta_inicial` vier preenchida (ex.: erro reconhecido,
        Cap. 25), já dispara a busca.
        """
        self.deiconify()
        self.lift()
        self.focus_force()

        self._base = qualiassist.carregar_base()
        self._historico = qualiassist.carregar_historico()

        categoria = qualiassist.categoria_da_tela(getattr(self.controlador, "_tela_atual", ""))
        if categoria is not None and not consulta_inicial:
            self._var_categoria.set(categoria.value)

        if consulta_inicial:
            self._entry_busca.delete(0, "end")
            self._entry_busca.insert(0, consulta_inicial)

        if self._entry_busca.get().strip() == "":
            self._mostrar_saudacao()
        else:
            self._buscar()

    # -- Abas ---------------------------------------------------------------------

    def _trocar_aba(self, valor: str) -> None:
        self._aba_atual = valor
        self._artigo_aberto = None
        if valor == "Buscar":
            self._buscar()
        elif valor == "Histórico":
            self._exibir_historico(somente_favoritos=False)
        else:
            self._exibir_historico(somente_favoritos=True)

    def _limpar_scroll(self) -> None:
        for widget in self._scroll.winfo_children():
            widget.destroy()

    def _mostrar_saudacao(self) -> None:
        self._limpar_scroll()
        ctk.CTkLabel(
            self._scroll, text=_SAUDACAO, anchor="w", justify="left", wraplength=360,
        ).grid(row=0, column=0, sticky="w", pady=10)
        self._montar_categorias_rapidas(linha_inicial=1)

    def _montar_categorias_rapidas(self, linha_inicial: int) -> None:
        ctk.CTkLabel(
            self._scroll, text="Categorias", font=ctk.CTkFont(weight="bold"), anchor="w",
        ).grid(row=linha_inicial, column=0, sticky="w", pady=(10, 5))
        frame = ctk.CTkFrame(self._scroll, fg_color="transparent")
        frame.grid(row=linha_inicial + 1, column=0, sticky="ew")
        for indice, categoria in enumerate(CategoriaQualiAssist):
            ctk.CTkButton(
                frame, text=categoria.value, height=28, fg_color="transparent", border_width=1,
                command=lambda c=categoria: self._selecionar_categoria(c),
            ).grid(row=indice // 2, column=indice % 2, sticky="ew", padx=3, pady=3)
        frame.grid_columnconfigure((0, 1), weight=1)

    def _selecionar_categoria(self, categoria: CategoriaQualiAssist) -> None:
        self._var_categoria.set(categoria.value)
        self._entry_busca.delete(0, "end")
        self._buscar()

    # -- Busca e listagem de resultados ------------------------------------------

    def _categoria_selecionada(self) -> CategoriaQualiAssist | None:
        valor = self._var_categoria.get()
        if valor == _TODAS_CATEGORIAS:
            return None
        try:
            return CategoriaQualiAssist(valor)
        except ValueError:
            return None

    def _buscar(self) -> None:
        self._artigo_aberto = None
        consulta = self._entry_busca.get().strip()
        if not consulta:
            self._mostrar_saudacao()
            return

        resultados = qualiassist.buscar(self._base, consulta, self._categoria_selecionada())
        self._limpar_scroll()

        if not resultados:
            ctk.CTkLabel(
                self._scroll, text="Nenhum artigo encontrado para essa pesquisa.",
                text_color=("gray60", "gray60"),
            ).grid(row=0, column=0, sticky="w", pady=10)
            qualiassist.registrar_pergunta(self._historico, consulta, self._tela_atual(), None)
            return

        for indice, artigo in enumerate(resultados[:15]):
            self._montar_card_resultado(artigo, indice)

        qualiassist.registrar_pergunta(self._historico, consulta, self._tela_atual(), resultados[0])

    def _tela_atual(self) -> str:
        return getattr(self.controlador, "_tela_atual", "")

    def _montar_card_resultado(self, artigo: ArtigoQualiAssist, linha: int) -> None:
        card = ctk.CTkFrame(self._scroll, corner_radius=8, border_width=1)
        card.grid(row=linha, column=0, sticky="ew", pady=4)
        card.grid_columnconfigure(0, weight=1)

        botao = ctk.CTkButton(
            card, text=artigo.titulo, anchor="w", fg_color="transparent",
            font=ctk.CTkFont(weight="bold"), command=lambda: self._abrir_artigo(artigo),
        )
        botao.grid(row=0, column=0, sticky="ew", padx=10, pady=(8, 2))
        ctk.CTkLabel(
            card, text=artigo.categoria.value, text_color=("gray60", "gray60"),
            font=ctk.CTkFont(size=11), anchor="w",
        ).grid(row=1, column=0, sticky="w", padx=10, pady=(0, 8))

    # -- Exibição de um artigo -----------------------------------------------------

    def _abrir_artigo(self, artigo: ArtigoQualiAssist) -> None:
        self._artigo_aberto = artigo
        self._limpar_scroll()

        ctk.CTkButton(
            self._scroll, text="← Resultados", width=110, fg_color="transparent", border_width=1,
            command=self._buscar,
        ).grid(row=0, column=0, sticky="w", pady=(0, 10))

        ctk.CTkLabel(
            self._scroll, text=artigo.titulo, font=ctk.CTkFont(size=15, weight="bold"),
            anchor="w", justify="left", wraplength=360,
        ).grid(row=1, column=0, sticky="w")
        ctk.CTkLabel(
            self._scroll, text=artigo.categoria.value, text_color=("gray60", "gray60"),
            anchor="w",
        ).grid(row=2, column=0, sticky="w", pady=(0, 10))

        ctk.CTkLabel(
            self._scroll, text=artigo.resposta, anchor="w", justify="left", wraplength=360,
        ).grid(row=3, column=0, sticky="w", pady=(0, 15))

        if artigo.links_internos:
            frame_links = ctk.CTkFrame(self._scroll, fg_color="transparent")
            frame_links.grid(row=4, column=0, sticky="ew", pady=(0, 10))
            for nome_tela in artigo.links_internos:
                ctk.CTkButton(
                    frame_links, text=f"Ir para: {nome_tela.replace('_', ' ').title()}",
                    height=28, command=lambda n=nome_tela: self._ir_para_tela(n),
                ).pack(anchor="w", pady=2)

        linha_botoes = ctk.CTkFrame(self._scroll, fg_color="transparent")
        linha_botoes.grid(row=5, column=0, sticky="ew", pady=(0, 15))
        ctk.CTkButton(
            linha_botoes, text="Copiar", width=80, command=lambda: self._copiar(artigo),
        ).pack(side="left", padx=(0, 8))
        ctk.CTkButton(
            linha_botoes, text="Imprimir", width=90, fg_color="transparent", border_width=1,
            command=lambda: self._imprimir(artigo),
        ).pack(side="left", padx=(0, 8))
        ctk.CTkButton(
            linha_botoes, text="Exportar", width=90, fg_color="transparent", border_width=1,
            command=lambda: self._exportar(artigo),
        ).pack(side="left", padx=(0, 8))
        ctk.CTkButton(
            linha_botoes, text="☆ Favoritar", width=110, fg_color="transparent", border_width=1,
            command=lambda: self._favoritar(artigo),
        ).pack(side="left")

        relacionados = qualiassist.respostas_relacionadas(self._base, artigo)
        if relacionados:
            ctk.CTkLabel(
                self._scroll, text="Talvez você também queira saber:",
                font=ctk.CTkFont(weight="bold"), anchor="w",
            ).grid(row=6, column=0, sticky="w", pady=(5, 5))
            for indice, relacionado in enumerate(relacionados):
                ctk.CTkButton(
                    self._scroll, text=f"• {relacionado.titulo}", anchor="w",
                    fg_color="transparent", command=lambda a=relacionado: self._abrir_artigo(a),
                ).grid(row=7 + indice, column=0, sticky="ew", pady=1)

    def _ir_para_tela(self, nome_tela: str) -> None:
        if hasattr(self.controlador, "mostrar_tela"):
            self.controlador.mostrar_tela(nome_tela)

    # -- Ações sobre a resposta (Cap. 17/18/19) -------------------------------------

    def _copiar(self, artigo: ArtigoQualiAssist) -> None:
        self.clipboard_clear()
        self.clipboard_append(f"{artigo.titulo}\n\n{artigo.resposta}")
        messagebox.showinfo("Copiado", "Resposta copiada para a área de transferência.")

    def _imprimir(self, artigo: ArtigoQualiAssist) -> None:
        import os
        caminho = self._exportar_para_arquivo(artigo, "pdf")
        if caminho is None:
            return
        try:
            os.startfile(str(caminho), "print")  # type: ignore[attr-defined]
        except OSError as erro:
            messagebox.showerror("Não foi possível imprimir", str(erro))

    def _exportar(self, artigo: ArtigoQualiAssist) -> None:
        caminho = self._exportar_para_arquivo(artigo, "pdf")
        if caminho is not None:
            messagebox.showinfo("Exportado", f"Arquivo salvo em:\n{caminho}")

    def _exportar_para_arquivo(self, artigo: ArtigoQualiAssist, formato: str) -> Path | None:
        from exportacao import caminho_exportacao

        config_app = getattr(self.controlador, "config_app", None)
        if config_app is None:
            return None
        caminho = caminho_exportacao(config_app, "QualiAssist", artigo.titulo[:40], formato)
        if formato == "pdf":
            exportar_pdf_simples(
                caminho, artigo.titulo, ["Pergunta", "Resposta"],
                [(p, "") for p in artigo.perguntas] or [("", artigo.resposta)],
            )
        return caminho

    def _favoritar(self, artigo: ArtigoQualiAssist) -> None:
        registro = next(
            (r for r in reversed(self._historico) if r.artigo_id == artigo.id), None)
        if registro is None:
            registro = qualiassist.registrar_pergunta(
                self._historico, artigo.titulo, self._tela_atual(), artigo)
        qualiassist.alternar_favorito(self._historico, registro)
        messagebox.showinfo(
            "Favoritos", "Adicionado aos favoritos." if registro.favorito
            else "Removido dos favoritos.")

    # -- Histórico e Favoritos (Cap. 15/16/27) --------------------------------------

    def _exibir_historico(self, somente_favoritos: bool) -> None:
        self._limpar_scroll()
        registros = [r for r in self._historico if (r.favorito or not somente_favoritos)]
        registros = list(reversed(registros))
        if not registros:
            texto = "Nenhum favorito ainda." if somente_favoritos else "Nenhuma pergunta ainda."
            ctk.CTkLabel(self._scroll, text=texto, text_color=("gray60", "gray60")).grid(
                row=0, column=0, sticky="w", pady=10)
            return

        for indice, registro in enumerate(registros[:50]):
            self._montar_card_historico(registro, indice)

    def _montar_card_historico(self, registro: RegistroHistoricoQualiAssist, linha: int) -> None:
        card = ctk.CTkFrame(self._scroll, corner_radius=8, border_width=1)
        card.grid(row=linha, column=0, sticky="ew", pady=4)
        card.grid_columnconfigure(0, weight=1)

        estrela = "★" if registro.favorito else "☆"
        ctk.CTkButton(
            card, text=f"{estrela} {registro.pergunta}", anchor="w", fg_color="transparent",
            command=lambda: self._reutilizar_pergunta(registro),
        ).grid(row=0, column=0, sticky="ew", padx=10, pady=(8, 2))
        ctk.CTkLabel(
            card, text=registro.quando, text_color=("gray60", "gray60"),
            font=ctk.CTkFont(size=11), anchor="w",
        ).grid(row=1, column=0, sticky="w", padx=10, pady=(0, 8))

    def _reutilizar_pergunta(self, registro: RegistroHistoricoQualiAssist) -> None:
        self._abas.set("Buscar")
        self._aba_atual = "Buscar"
        self._entry_busca.delete(0, "end")
        self._entry_busca.insert(0, registro.pergunta)
        self._buscar()

    def _limpar_historico(self) -> None:
        confirmar = messagebox.askyesno(
            "Limpar histórico",
            "Limpar o histórico de perguntas? Os favoritos são preservados.")
        if not confirmar:
            return
        self._historico = qualiassist.limpar_historico(self._historico)
        if self._aba_atual != "Buscar":
            self._trocar_aba(self._aba_atual)

    # -- Explicar esta Tela (Cap. 21) -----------------------------------------------

    def _explicar_tela_atual(self) -> None:
        categoria = qualiassist.categoria_da_tela(self._tela_atual())
        if categoria is None:
            messagebox.showinfo(
                "Explicar esta Tela", "Não há ajuda contextual cadastrada para esta tela ainda.")
            return
        self._abas.set("Buscar")
        self._aba_atual = "Buscar"
        self._var_categoria.set(categoria.value)
        self._entry_busca.delete(0, "end")
        self._buscar()


# ---------------------------------------------------------------------------
# Botão flutuante fixo (Cap. 5) — sempre visível, em qualquer tela
# ---------------------------------------------------------------------------

class BotaoFlutuanteQualiAssist(ctk.CTkToplevel):
    """
    Botão flutuante sem decoração de janela, ancorado no canto
    inferior direito da janela principal e sempre por cima (Cap. 5) —
    reposiciona automaticamente ao mover/redimensionar a janela
    principal (`<Configure>`).
    """

    def __init__(self, master, ao_clicar) -> None:
        super().__init__(master)
        self._master_principal = master
        self.overrideredirect(True)
        self.attributes("-topmost", True)
        self.geometry("56x56")

        ctk.CTkButton(
            self, text="🤖", width=56, height=56, corner_radius=28,
            font=ctk.CTkFont(size=22), command=ao_clicar,
        ).pack()

        master.bind("<Configure>", self._reposicionar, add="+")
        self.after(50, self._reposicionar)

    def _reposicionar(self, evento=None) -> None:
        try:
            x = self._master_principal.winfo_x() + self._master_principal.winfo_width() - 76
            y = self._master_principal.winfo_y() + self._master_principal.winfo_height() - 86
            self.geometry(f"+{max(x, 0)}+{max(y, 0)}")
        except tk.TclError:
            pass
