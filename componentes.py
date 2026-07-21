"""
componentes.py
---------------
Biblioteca de componentes reutilizáveis da interface (Sprint 1, v2.1).

Antes desta Sprint, cada tela com listagem (Funcionários, Setores,
Histórico, Pendências, Competências) reimplementava do zero: uma linha
por item (`_Linha*`), uma `CTkScrollableFrame`, pesquisa (quando
existia) e paginação (só existia em Pendências). Nenhuma tinha
ordenação por cabeçalho ou exportação/impressão.

Este módulo concentra esse padrão numa única classe (`TabelaPadrao`),
reaproveitando o desenho de "pool fixo de linhas" já validado por
`tela_pendencias.py` (Sprint 4.1) — criar N linhas uma única vez e só
trocar o conteúdo delas (`vincular()`) é sensivelmente mais rápido que
destruir/recriar widgets do CustomTkinter a cada atualização.

Cada tela continua responsável pelo LAYOUT de uma linha (o que exibir,
quais botões) — só entrega uma fábrica de linhas (`criar_linha`) que
devolve um widget com um método `vincular(registro)`, exatamente como
`_LinhaPendencia` já fazia. A tabela cuida de pesquisa, ordenação,
paginação e do rodapé.
"""

from __future__ import annotations

import tkinter as tk
from dataclasses import dataclass
from typing import Any, Callable, Protocol

import customtkinter as ctk

from modelos import normalizar_texto

_TAMANHOS_PAGINA = ("25", "50", "100", "Todos")


class LinhaTabela(Protocol):
    """Contrato mínimo de uma linha reaproveitável do pool de `TabelaPadrao`."""

    def vincular(self, registro: Any) -> None: ...

    def grid(self, **kwargs: Any) -> None: ...

    def grid_remove(self) -> None: ...


@dataclass(frozen=True)
class ColunaOrdenavel:
    """
    Uma coluna clicável no cabeçalho de `TabelaPadrao` (Cap. novo,
    v2.1, requisito "Ordenação Global"): `chave` extrai o valor de
    comparação de um registro (ex.: `lambda f: f.nome_completo`).
    """

    rotulo: str
    chave: Callable[[Any], Any]


class TabelaPadrao(ctk.CTkFrame):
    """
    Tabela padronizada (Sprint 1, v2.1): pesquisa instantânea +
    cabeçalho ordenável (1º clique = crescente, 2º = decrescente, 3º =
    volta à ordem original) + paginação (25/50/100/Todos) + rodapé com
    contagem — tudo sobre um pool fixo de linhas reaproveitadas.

    Uso:
        tabela = TabelaPadrao(
            master, criar_linha=lambda m: _LinhaSetor(m, ...),
            colunas=[ColunaOrdenavel("Nome", lambda s: s.nome)],
            campos_pesquisa=[lambda s: s.nome],
        )
        tabela.grid(...)
        tabela.definir_registros(setores)
    """

    def __init__(
        self,
        master: Any,
        *,
        criar_linha: Callable[[Any], LinhaTabela],
        colunas: list[ColunaOrdenavel] | None = None,
        campos_pesquisa: list[Callable[[Any], str]] | None = None,
        tamanho_pagina_padrao: int = 25,
        texto_vazio: str = "Nenhum registro encontrado.",
        placeholder_pesquisa: str = "Pesquisar...",
        altura_lista: int | None = None,
        **kwargs: Any,
    ) -> None:
        super().__init__(master, fg_color="transparent", **kwargs)
        self._criar_linha = criar_linha
        self._colunas = colunas or []
        self._campos_pesquisa = campos_pesquisa or []
        self._texto_vazio = texto_vazio
        self._tamanho_pagina_padrao = tamanho_pagina_padrao

        self._registros: list[Any] = []
        self._pagina_atual = 0
        self._coluna_ordenacao: ColunaOrdenavel | None = None
        self._ordem_decrescente = False
        self._pool: list[LinhaTabela] = []

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(2, weight=1)

        self._montar_barra_superior()
        if self._colunas:
            self._montar_cabecalho()
        self._montar_lista(altura_lista)
        self._montar_rodape()

    # -- Construção da UI -----------------------------------------------------

    def _montar_barra_superior(self) -> None:
        barra = ctk.CTkFrame(self, fg_color="transparent")
        barra.grid(row=0, column=0, sticky="ew", pady=(0, 10))
        barra.grid_columnconfigure(0, weight=1)

        self._entry_pesquisa = ctk.CTkEntry(
            barra, placeholder_text=self._placeholder_pesquisa_texto())
        self._entry_pesquisa.grid(row=0, column=0, sticky="ew", padx=(0, 10))
        self._entry_pesquisa.bind("<KeyRelease>", lambda evento: self._reprocessar())

        ctk.CTkLabel(barra, text="Por página").grid(row=0, column=1, padx=(0, 5))
        self._var_tamanho_pagina = tk.StringVar(value=str(self._tamanho_pagina_padrao))
        ctk.CTkOptionMenu(
            barra, values=list(_TAMANHOS_PAGINA), variable=self._var_tamanho_pagina,
            width=90, command=lambda valor: self._ao_alterar_tamanho_pagina(),
        ).grid(row=0, column=2)

    def _placeholder_pesquisa_texto(self) -> str:
        return "Pesquisar..."

    def _montar_cabecalho(self) -> None:
        self._cabecalho = ctk.CTkFrame(self, fg_color="transparent")
        self._cabecalho.grid(row=1, column=0, sticky="ew", padx=4)
        self._rotulos_coluna: dict[str, ctk.CTkLabel] = {}
        for indice, coluna in enumerate(self._colunas):
            self._cabecalho.grid_columnconfigure(indice, weight=1)
            rotulo = ctk.CTkLabel(
                self._cabecalho, text=self._texto_coluna(coluna), anchor="w",
                font=ctk.CTkFont(weight="bold"), text_color=("gray50", "gray60"),
                cursor="hand2",
            )
            rotulo.grid(row=0, column=indice, sticky="w", padx=5, pady=(0, 4))
            rotulo.bind("<Button-1>", lambda evento, c=coluna: self._ordenar_por(c))
            self._rotulos_coluna[coluna.rotulo] = rotulo

    def _texto_coluna(self, coluna: ColunaOrdenavel) -> str:
        if self._coluna_ordenacao is not coluna:
            return f"{coluna.rotulo}  ↕"
        return f"{coluna.rotulo}  {'▼' if self._ordem_decrescente else '▲'}"

    def _montar_lista(self, altura: int | None) -> None:
        self._scroll = ctk.CTkScrollableFrame(
            self, fg_color="transparent",
            **({"height": altura} if altura is not None else {}),
        )
        self._scroll.grid(row=2, column=0, sticky="nsew")
        self._rotulo_vazio = ctk.CTkLabel(
            self._scroll, text=self._texto_vazio, text_color=("gray60", "gray60"))

    def _montar_rodape(self) -> None:
        rodape = ctk.CTkFrame(self, fg_color="transparent")
        rodape.grid(row=3, column=0, sticky="ew", pady=(8, 0))
        rodape.grid_columnconfigure(1, weight=1)

        self._botao_pagina_anterior = ctk.CTkButton(
            rodape, text="◀ Anterior", width=100, fg_color="transparent", border_width=1,
            command=self._pagina_anterior,
        )
        self._botao_pagina_anterior.grid(row=0, column=0, sticky="w")

        self._rotulo_contagem = ctk.CTkLabel(
            rodape, text="", font=ctk.CTkFont(size=12), text_color=("gray60", "gray60"))
        self._rotulo_contagem.grid(row=0, column=1)

        self._botao_pagina_proxima = ctk.CTkButton(
            rodape, text="Próxima ▶", width=100, fg_color="transparent", border_width=1,
            command=self._pagina_proxima,
        )
        self._botao_pagina_proxima.grid(row=0, column=2, sticky="e")

    # -- API pública -------------------------------------------------------------

    def definir_registros(self, registros: list[Any]) -> None:
        """Substitui a lista completa e reprocessa pesquisa/ordenação/paginação."""
        self._registros = registros
        self._pagina_atual = 0
        self._reprocessar()

    def registros_filtrados(self) -> list[Any]:
        """Registros após pesquisa + ordenação, sem recortar pela página (para exportação)."""
        return self._aplicar_pesquisa_e_ordenacao()

    def termo_pesquisa(self) -> str:
        return self._entry_pesquisa.get().strip()

    # -- Pesquisa, ordenação e paginação -----------------------------------------

    def _ao_alterar_tamanho_pagina(self) -> None:
        self._pagina_atual = 0
        self._reprocessar()

    def _ordenar_por(self, coluna: ColunaOrdenavel) -> None:
        """1º clique = crescente, 2º = decrescente, 3º = volta à ordem original."""
        if self._coluna_ordenacao is not coluna:
            self._coluna_ordenacao = coluna
            self._ordem_decrescente = False
        elif not self._ordem_decrescente:
            self._ordem_decrescente = True
        else:
            self._coluna_ordenacao = None
            self._ordem_decrescente = False

        for outra in self._colunas:
            self._rotulos_coluna[outra.rotulo].configure(text=self._texto_coluna(outra))
        self._pagina_atual = 0
        self._reprocessar()

    def _pagina_anterior(self) -> None:
        if self._pagina_atual > 0:
            self._pagina_atual -= 1
            self._reprocessar()

    def _pagina_proxima(self) -> None:
        self._pagina_atual += 1
        self._reprocessar()

    def _aplicar_pesquisa_e_ordenacao(self) -> list[Any]:
        registros = self._registros
        termo = normalizar_texto(self._entry_pesquisa.get().strip())
        if termo and self._campos_pesquisa:
            registros = [
                registro for registro in registros
                if any(termo in normalizar_texto(str(campo(registro))) for campo in
                       self._campos_pesquisa)
            ]
        if self._coluna_ordenacao is not None:
            registros = sorted(
                registros, key=self._coluna_ordenacao.chave, reverse=self._ordem_decrescente)
        return registros

    def _tamanho_pagina(self) -> int | None:
        valor = self._var_tamanho_pagina.get()
        return None if valor == "Todos" else int(valor)

    # -- Renderização (reaproveita o pool, nunca recria) --------------------------

    def _reprocessar(self) -> None:
        filtrados = self._aplicar_pesquisa_e_ordenacao()
        total = len(filtrados)
        tamanho_pagina = self._tamanho_pagina()

        if tamanho_pagina is None:
            total_paginas = 1
            pagina = filtrados
        else:
            total_paginas = max(1, -(-total // tamanho_pagina))
            self._pagina_atual = max(0, min(self._pagina_atual, total_paginas - 1))
            inicio = self._pagina_atual * tamanho_pagina
            pagina = filtrados[inicio:inicio + tamanho_pagina]

        self._garantir_pool(len(pagina))

        for linha in self._pool:
            linha.grid_remove()
        self._rotulo_vazio.grid_forget()

        if not pagina:
            self._rotulo_vazio.grid(row=0, column=0, pady=20)
        else:
            for indice, (linha, registro) in enumerate(zip(self._pool, pagina)):
                linha.vincular(registro)
                linha.grid(row=indice, column=0, sticky="ew", pady=4)

        if total == len(self._registros):
            self._rotulo_contagem.configure(text=f"{total} registro(s)")
        else:
            self._rotulo_contagem.configure(
                text=f"{total} de {len(self._registros)} registro(s) (filtrados)")
        if tamanho_pagina is not None:
            self._rotulo_contagem.configure(
                text=self._rotulo_contagem.cget("text") +
                f"    Página {self._pagina_atual + 1} de {total_paginas}")

        self._botao_pagina_anterior.configure(
            state="normal" if self._pagina_atual > 0 else "disabled")
        self._botao_pagina_proxima.configure(
            state="normal" if tamanho_pagina is not None and
            self._pagina_atual < total_paginas - 1 else "disabled")

    def _garantir_pool(self, quantidade_visivel: int) -> None:
        """Cresce o pool sob demanda (nunca encolhe — widgets já criados são baratos de ocultar)."""
        while len(self._pool) < quantidade_visivel:
            self._pool.append(self._criar_linha(self._scroll))


# ---------------------------------------------------------------------------
# Botão de exportação universal (Cap. novo, v2.1)
# ---------------------------------------------------------------------------

class BotaoExportar(ctk.CTkFrame):
    """
    Botão único com menu Excel/CSV/PDF (requisito "Exportação
    Universal", Sprint 1 v2.1). Recebe uma função `obter_registros`
    (chamada só no momento do clique, para sempre exportar o estado
    atual — já filtrado/ordenado) e uma função `montar_linha` que
    converte um registro numa tupla de valores de exibição.
    """

    def __init__(
        self,
        master: Any,
        *,
        titulo: str,
        colunas: list[str],
        obter_registros: Callable[[], list[Any]],
        montar_linha: Callable[[Any], tuple],
        caminho_sugerido: Callable[[str], "Any"],
        **kwargs: Any,
    ) -> None:
        super().__init__(master, fg_color="transparent", **kwargs)
        self._titulo = titulo
        self._colunas = colunas
        self._obter_registros = obter_registros
        self._montar_linha = montar_linha
        self._caminho_sugerido = caminho_sugerido

        self._var_formato = tk.StringVar(value="Excel")
        ctk.CTkOptionMenu(
            self, values=["Excel", "CSV", "PDF"], variable=self._var_formato, width=90,
        ).grid(row=0, column=0, padx=(0, 8))
        ctk.CTkButton(self, text="Exportar", width=100, command=self._exportar).grid(
            row=0, column=1)

    def _exportar(self) -> None:
        from tkinter import messagebox

        from exportacao import exportar_csv, exportar_excel_simples, exportar_pdf_simples

        registros = self._obter_registros()
        if not registros:
            messagebox.showinfo("Exportar", "Não há registros para exportar.")
            return

        linhas = [self._montar_linha(registro) for registro in registros]
        formato = self._var_formato.get()
        caminho = self._caminho_sugerido(formato.lower())

        try:
            if formato == "Excel":
                exportar_excel_simples(caminho, self._titulo, self._colunas, linhas)
            elif formato == "CSV":
                exportar_csv(caminho, self._colunas, linhas)
            else:
                exportar_pdf_simples(caminho, self._titulo, self._colunas, linhas)
        except OSError as erro:
            messagebox.showerror(
                "Não foi possível exportar",
                f"Verifique se o arquivo não está aberto em outro programa.\n\n{erro}")
            return

        messagebox.showinfo("Exportado", f"Arquivo salvo em:\n{caminho}")
