"""
tela_principal.py
-----------------
Tela inicial do sistema (Cap. 12.2 / 12.3).

Exibe logo, nome da empresa/sistema, competência e arquivo selecionado,
os botões grandes de navegação/ação e a barra de status inferior.

Esta tela NÃO processa nem calcula nada: apenas coleta a seleção da
planilha e delega a navegação ao controlador. A leitura (Sprint 3) e o
processamento (Sprint 4+) serão ligados aos botões nas próximas sprints.
"""

from __future__ import annotations

import functools
from datetime import datetime
from pathlib import Path
from tkinter import filedialog, messagebox

import customtkinter as ctk

import competencias
from cadastro import montar_sugestoes_importacao, preparar_importacao
from calculadora import processar_todos
from config import BASE_DIR, Config, turno_de_dict
from constantes import APP_NOME_CURTO, EXTENSOES_PLANILHA, VERSAO, nome_mes
from leitor_ponto import PlanilhaInvalidaError
from logger import get_logger
from modelos import Competencia, Funcionario, FuncionarioPlanilha, Pendencia

log = get_logger()

try:
    from PIL import Image
    _PIL_OK = True
except ImportError:  # pragma: no cover - Pillow faz parte das dependências
    _PIL_OK = False


class TelaPrincipal(ctk.CTkFrame):
    """Tela inicial com navegação, seleção de planilha e barra de status."""

    def __init__(self, master, controlador, config: Config) -> None:
        super().__init__(master, corner_radius=0)

        self.controlador = controlador
        self.config_app = config
        self.caminho_planilha: Path | None = None

        self.grid_rowconfigure(1, weight=1)
        self.grid_columnconfigure(0, weight=1)

        self._montar_cabecalho()
        self._montar_corpo()
        self._montar_barra_status()

    # -- Construção da UI ----------------------------------------------------

    def _montar_cabecalho(self) -> None:
        cabecalho = ctk.CTkFrame(self, corner_radius=0, height=110)
        cabecalho.grid(row=0, column=0, sticky="ew", padx=0, pady=0)
        cabecalho.grid_columnconfigure(1, weight=1)

        # Logo (opcional)
        self.rotulo_logo = ctk.CTkLabel(cabecalho, text="", width=90)
        self.rotulo_logo.grid(row=0, column=0, rowspan=2, padx=20, pady=15)
        self._carregar_logo()

        self.rotulo_empresa = ctk.CTkLabel(
            cabecalho,
            text=self._texto_empresa(),
            font=ctk.CTkFont(size=22, weight="bold"),
            anchor="w",
        )
        self.rotulo_empresa.grid(row=0, column=1, sticky="sw", padx=10, pady=(20, 0))

        ctk.CTkLabel(
            cabecalho,
            text=APP_NOME_CURTO,
            font=ctk.CTkFont(size=14),
            text_color=("gray70", "gray70"),
            anchor="w",
        ).grid(row=1, column=1, sticky="nw", padx=10, pady=(0, 20))

    def _montar_corpo(self) -> None:
        corpo = ctk.CTkFrame(self, fg_color="transparent")
        corpo.grid(row=1, column=0, sticky="nsew", padx=30, pady=20)
        corpo.grid_columnconfigure(0, weight=1)
        corpo.grid_columnconfigure(1, weight=1)

        # --- Painel de informações da planilha ---
        painel = ctk.CTkFrame(corpo)
        painel.grid(row=0, column=0, columnspan=2, sticky="ew", pady=(0, 20))
        painel.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(painel, text="Competência:", anchor="w",
                     font=ctk.CTkFont(weight="bold")).grid(
            row=0, column=0, sticky="w", padx=15, pady=(15, 5))
        self.rotulo_competencia = ctk.CTkLabel(painel, text="—", anchor="w")
        self.rotulo_competencia.grid(row=0, column=1, sticky="w", padx=10, pady=(15, 5))

        ctk.CTkLabel(painel, text="Arquivo:", anchor="w",
                     font=ctk.CTkFont(weight="bold")).grid(
            row=1, column=0, sticky="w", padx=15, pady=(5, 15))
        self.rotulo_arquivo = ctk.CTkLabel(
            painel, text="Nenhum arquivo selecionado", anchor="w")
        self.rotulo_arquivo.grid(row=1, column=1, sticky="w", padx=10, pady=(5, 15))

        # --- Botões grandes ---
        botoes = [
            ("Selecionar Planilha", self._selecionar_planilha),
            ("Processar", self._processar),
            ("Funcionários", lambda: self.controlador.mostrar_tela("funcionarios")),
            ("Setores", lambda: self.controlador.mostrar_tela("setores")),
            ("Competências", lambda: self.controlador.mostrar_tela("competencias")),
            ("Relatórios", lambda: self.controlador.mostrar_tela("relatorios")),
            ("Configurações", lambda: self.controlador.mostrar_tela("configuracoes")),
            ("Histórico", lambda: self.controlador.mostrar_tela("historico")),
            ("Sobre", lambda: self.controlador.mostrar_tela("sobre")),
        ]

        for indice, (texto, comando) in enumerate(botoes):
            linha = 1 + indice // 2
            coluna = indice % 2
            ctk.CTkButton(
                corpo,
                text=texto,
                command=comando,
                height=64,
                font=ctk.CTkFont(size=16, weight="bold"),
                corner_radius=10,
            ).grid(row=linha, column=coluna, sticky="ew", padx=10, pady=10)

    def _montar_barra_status(self) -> None:
        barra = ctk.CTkFrame(self, corner_radius=0, height=32)
        barra.grid(row=2, column=0, sticky="ew")
        barra.grid_columnconfigure(0, weight=1)

        self.rotulo_status = ctk.CTkLabel(
            barra, text="Sistema iniciado.", anchor="w",
            font=ctk.CTkFont(size=12))
        self.rotulo_status.grid(row=0, column=0, sticky="w", padx=15, pady=4)

        ctk.CTkLabel(
            barra, text=f"v{VERSAO}", anchor="e",
            font=ctk.CTkFont(size=12), text_color=("gray60", "gray60")).grid(
            row=0, column=1, sticky="e", padx=15, pady=4)

    # -- Ações ---------------------------------------------------------------

    def _selecionar_planilha(self) -> None:
        """Abre o seletor de arquivos e registra a planilha escolhida."""
        tipos = [("Planilhas do relógio de ponto", "*.xls *.xlsx"), ("Todos", "*.*")]
        caminho = filedialog.askopenfilename(title="Selecionar planilha", filetypes=tipos)
        if not caminho:
            return

        arquivo = Path(caminho)
        if arquivo.suffix.lower() not in EXTENSOES_PLANILHA:
            self.definir_status("Formato inválido. Selecione um arquivo .xls ou .xlsx.")
            return

        self.caminho_planilha = arquivo
        self.rotulo_arquivo.configure(text=arquivo.name)
        self.definir_status(f"Planilha carregada: {arquivo.name}")
        log.info("Planilha selecionada: %s", arquivo)

    def _processar(self) -> None:
        """
        Lê a planilha selecionada (Sprint 3.5) e abre o Painel de Revisão
        com as sugestões de importação. Caso a planilha traga "Dep."
        sem Setor cadastrado correspondente (Cap. 5.17), a importação
        pausa antes disso na tela "Foram encontrados novos setores na
        planilha" — `_concluir_leitura` é quem retoma o fluxo depois,
        sem exigir uma segunda importação. Depois do Painel de Revisão
        concluído, o Motor de Cálculo (Cap. 6) processa os funcionários
        do lote e a Tela de Pendências (Cap. 9.3) é aberta.
        """
        if self.caminho_planilha is None:
            self.definir_status("Selecione uma planilha antes de processar.")
            return

        self.definir_status(f"Processando {self.caminho_planilha.name}...")
        self.update_idletasks()

        try:
            funcionarios_planilha, pendencias, setores_novos, competencia = preparar_importacao(
                self.caminho_planilha, self.config_app)
        except PlanilhaInvalidaError as erro:
            log.error("Falha ao processar planilha: %s", erro)
            self.definir_status(f"Não foi possível processar a planilha: {erro}")
            return

        mes, ano = competencia
        if competencias.existe(mes, ano) and not self._confirmar_substituicao(mes, ano):
            return

        self.rotulo_competencia.configure(text=f"{nome_mes(mes)}/{ano}")

        continuar = functools.partial(
            self._concluir_leitura, funcionarios_planilha, pendencias, competencia)

        if setores_novos:
            self.definir_status(
                f"{len(setores_novos)} novo(s) setor(es) encontrado(s) na planilha — "
                "revise antes de continuar."
            )
            self.controlador.iniciar_revisao_setores_novos(setores_novos, continuar)
        else:
            continuar()

    def _confirmar_substituicao(self, mes: int, ano: int) -> bool:
        """
        Pergunta antes de reimportar uma competência já existente
        (gerenciamento de múltiplas competências): a importação nunca
        duplica uma competência silenciosamente — sempre pede
        confirmação explícita antes de sobrescrever o que já foi
        processado (com backup automático da versão anterior, feito por
        `competencias.salvar_competencia`).
        """
        substituir = messagebox.askyesno(
            "Competência já existe",
            f"Já existe uma competência importada para {nome_mes(mes)}/{ano}.\n\n"
            "Deseja substituir a competência existente? Esta ação não pode ser desfeita.",
        )
        if not substituir:
            self.definir_status(f"Importação cancelada — {nome_mes(mes)}/{ano} já existe.")
        return substituir

    def _concluir_leitura(
        self,
        funcionarios_planilha: list[FuncionarioPlanilha],
        pendencias: list[Pendencia],
        competencia: tuple[int, int],
    ) -> None:
        """
        Monta as sugestões de importação e abre o Painel de Revisão —
        chamado diretamente por `_processar()` quando não há Setores
        novos a resolver, ou como continuação da tela de Setores Novos
        (Cap. 5.17) depois que o usuário decide criar ou ignorar.
        """
        sugestoes = montar_sugestoes_importacao(funcionarios_planilha, self.config_app)
        self.definir_status(
            f"{len(sugestoes)} funcionário(s) identificado(s), "
            f"{len(pendencias)} pendência(s) — revise antes de confirmar."
        )
        ao_concluir_calculo = functools.partial(
            self._processar_calculo, competencia)
        self.controlador.iniciar_revisao_funcionarios(
            sugestoes, funcionarios_planilha, ao_concluir_calculo)

    def _processar_calculo(
        self, competencia: tuple[int, int], funcionarios_processaveis: list[Funcionario],
    ) -> None:
        """
        Motor de Cálculo (Cap. 6): roda depois que o Painel de Revisão é
        concluído, sobre os funcionários do lote já com `.dias`
        anexados. O resultado é imediatamente persistido como uma
        Competência (gerenciamento de múltiplas competências) — fechar o
        sistema a partir daqui nunca perde nada — e a Tela de Pendências
        (Cap. 9.3) é aberta em seguida.
        """
        turnos = [
            turno_de_dict(dados) for dados in self.config_app.configuracoes.get("turnos", [])
        ]
        resultado = processar_todos(
            funcionarios_processaveis, turnos, self.config_app,
            nome_empresa=self.config_app.nome_empresa, competencia=competencia,
        )
        self.definir_status(
            f"Cálculo concluído: {len(funcionarios_processaveis)} funcionário(s), "
            f"{len(resultado.pendencias)} pendência(s) para revisar."
        )

        mes, ano = competencia
        arquivo_original = self.caminho_planilha.name if self.caminho_planilha else ""
        competencia_obj = Competencia(
            mes=mes,
            ano=ano,
            status=competencias.avaliar_status(resultado, None),
            data_importacao=datetime.now().strftime("%d/%m/%Y %H:%M:%S"),
            arquivo_original=arquivo_original,
            resultado=resultado,
        )
        competencias.salvar_competencia(competencia_obj)

        self.controlador.iniciar_tela_pendencias(competencia_obj)

    # -- Integração com o controlador ---------------------------------------

    def ao_exibir(self) -> None:
        """Atualiza dados que podem ter mudado (ex.: nome/logo da empresa)."""
        self.rotulo_empresa.configure(text=self._texto_empresa())
        self._carregar_logo()

    def definir_status(self, texto: str) -> None:
        self.rotulo_status.configure(text=texto)

    # -- Auxiliares ----------------------------------------------------------

    def _texto_empresa(self) -> str:
        return self.config_app.nome_empresa or "Empresa não configurada"

    def _carregar_logo(self) -> None:
        """Carrega a logo da empresa, se existir e o Pillow estiver disponível."""
        caminho_rel = self.config_app.empresa.get("logo_caminho", "")
        if not caminho_rel or not _PIL_OK:
            self.rotulo_logo.configure(image=None, text="")
            return

        caminho = Path(caminho_rel)
        if not caminho.is_absolute():
            caminho = BASE_DIR / caminho_rel

        if not caminho.exists():
            self.rotulo_logo.configure(image=None, text="")
            return

        try:
            imagem = Image.open(caminho)
            ctk_img = ctk.CTkImage(light_image=imagem, dark_image=imagem, size=(80, 80))
            self.rotulo_logo.configure(image=ctk_img, text="")
            # Mantém referência para o garbage collector não descartar a imagem
            self.rotulo_logo.imagem = ctk_img
        except Exception as erro:  # pragma: no cover - proteção contra imagem inválida
            log.error("Falha ao carregar logo: %s", erro)
            self.rotulo_logo.configure(image=None, text="")
