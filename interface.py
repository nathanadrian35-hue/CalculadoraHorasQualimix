"""
interface.py
------------
Janela raiz da aplicação e roteamento entre telas (Cap. 12).

Responsabilidade única: montar a janela principal CustomTkinter (tema
escuro), instanciar as telas e alternar entre elas. NÃO realiza cálculos
nem leitura de planilha — apenas apresentação e navegação.

Cada tela é um CTkFrame que recebe (master, controlador, config). O
controlador é esta própria janela (App), que expõe:
    - mostrar_tela(nome): traz uma tela para frente;
    - definir_status(texto): atualiza a barra de status da tela principal.
"""

from __future__ import annotations

from typing import Callable

import customtkinter as ctk

from config import ICONES_DIR, Config
from constantes import APP_NOME
from logger import get_logger
from modelos import (
    Competencia,
    Funcionario,
    FuncionarioPlanilha,
    SetorNovoEncontrado,
    SugestaoImportacao,
)
from qualiassist_ui import BotaoFlutuanteQualiAssist, PainelQualiAssist
from relatorio import existem_pendencias_abertas
from tela_absenteismo import TelaAbsenteismo
from tela_absenteismo_config import TelaAbsenteismoConfig
from tela_competencias import TelaCompetencias
from tela_configuracoes import TelaConfiguracoes
from tela_dashboard import TelaDashboard
from tela_funcionarios import TelaFuncionarios
from tela_historico import TelaHistorico
from tela_pendencias import TelaPendencias
from tela_principal import TelaPrincipal
from tela_qualiassist_admin import TelaQualiAssistAdmin
from tela_relatorios import TelaRelatorios
from tela_setores import TelaSetores
from tela_sobre import TelaSobre

log = get_logger()

# Aparência global (tema escuro conforme especificação)
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("dark-blue")


class App(ctk.CTk):
    """Janela principal do sistema — controladora da navegação."""

    LARGURA = 1000
    ALTURA = 640

    def __init__(self, config: Config) -> None:
        super().__init__()

        self.config_app = config

        # Competência mais recentemente aberta nesta sessão (importada
        # agora ou retomada pela Tela Competências) — usada só como dica
        # de pré-seleção pela Tela de Relatórios (Cap. 12.8), nunca como
        # fonte de dados: a fonte é sempre `competencias.listar()`/
        # `competencias.carregar_competencia()`.
        self.competencia_atual: Competencia | None = None

        self.title(APP_NOME)
        self.geometry(f"{self.LARGURA}x{self.ALTURA}")
        self.minsize(900, 600)
        self._definir_icone()
        self._centralizar()

        # Container único onde todas as telas são empilhadas
        self.container = ctk.CTkFrame(self, corner_radius=0)
        self.container.pack(fill="both", expand=True)
        self.container.grid_rowconfigure(0, weight=1)
        self.container.grid_columnconfigure(0, weight=1)

        # Instancia todas as telas uma única vez
        self._telas: dict[str, ctk.CTkFrame] = {}
        for nome, Classe in (
            ("principal", TelaPrincipal),
            ("configuracoes", TelaConfiguracoes),
            ("funcionarios", TelaFuncionarios),
            ("setores", TelaSetores),
            ("pendencias", TelaPendencias),
            ("relatorios", TelaRelatorios),
            ("competencias", TelaCompetencias),
            ("dashboard", TelaDashboard),
            ("absenteismo", TelaAbsenteismo),
            ("absenteismo_config", TelaAbsenteismoConfig),
            ("historico", TelaHistorico),
            ("qualiassist_admin", TelaQualiAssistAdmin),
            ("sobre", TelaSobre),
        ):
            tela = Classe(self.container, controlador=self, config=config)
            tela.grid(row=0, column=0, sticky="nsew")
            self._telas[nome] = tela

        self._tela_atual: str = ""

        # Primeira execução: abre o Wizard de configuração inicial (Cap. 4)
        # em vez da tela principal. Nas próximas execuções, abre direto.
        tela_inicial = "configuracoes" if config.primeira_execucao else "principal"
        self.mostrar_tela(tela_inicial)
        self._configurar_atalhos()

        # QualiAssist (Sprint 3, v2.1): painel único reaproveitado por toda a
        # sessão + botão flutuante sempre visível (Cap. 5) — nenhum dos dois
        # é uma "tela" navegável do container principal.
        self._painel_qualiassist = PainelQualiAssist(self, self)
        self._botao_qualiassist = BotaoFlutuanteQualiAssist(
            self, ao_clicar=lambda: self.abrir_qualiassist())

        log.info("Interface iniciada.")

    # -- QualiAssist (Sprint 3, v2.1) ------------------------------------------

    def abrir_qualiassist(self, consulta_inicial: str = "") -> None:
        """
        Abre o painel do QualiAssist (Cap. 5) — qualquer tela pode
        chamar isso, opcionalmente com uma pesquisa já pronta (ex.:
        `qualiassist.sugerir_por_erro()` reconhecendo uma mensagem).
        """
        self._painel_qualiassist.abrir(consulta_inicial)

    # -- Navegação -----------------------------------------------------------

    def mostrar_tela(self, nome: str) -> None:
        """Traz a tela indicada para frente e a atualiza, se aplicável."""
        tela = self._telas.get(nome)
        if tela is None:
            log.error("Tela inexistente solicitada: %s", nome)
            return

        # Se a tela souber se atualizar ao aparecer, faz isso
        if hasattr(tela, "ao_exibir"):
            tela.ao_exibir()

        tela.tkraise()
        self._tela_atual = nome

    # -- Atalhos de teclado globais (Sprint 1, v2.1) --------------------------

    def _configurar_atalhos(self) -> None:
        """
        Cada tecla despacha para a tela atualmente visível através de
        hooks opcionais (`hasattr`) — uma tela que não implementa um
        atalho específico simplesmente o ignora, sem erro. `Ctrl+N`/
        `Ctrl+S`/`Esc` ficaram de fora desta primeira leva: o alvo
        "certo" depende de qual formulário/diálogo está aberto no
        momento (ex.: Esc fechando um Toplevel vs. voltando de tela),
        e um despacho genérico arriscaria fechar a coisa errada.
        """
        self.bind_all("<F5>", lambda evento: self._atalho_atualizar())
        self.bind_all("<Control-f>", lambda evento: self._atalho_pesquisar())
        self.bind_all("<Control-F>", lambda evento: self._atalho_pesquisar())
        self.bind_all("<Control-p>", lambda evento: self._atalho_imprimir())
        self.bind_all("<Control-P>", lambda evento: self._atalho_imprimir())

    def _tela_ativa(self) -> ctk.CTkFrame | None:
        return self._telas.get(self._tela_atual)

    def _atalho_atualizar(self) -> None:
        """F5 — Atualizar: reaproveita o mesmo hook `ao_exibir()` já usado ao trocar de tela."""
        tela = self._tela_ativa()
        if tela is not None and hasattr(tela, "ao_exibir"):
            tela.ao_exibir()

    def _atalho_pesquisar(self) -> None:
        """Ctrl+F — Pesquisar: foca o campo de busca da tela atual, se houver."""
        tela = self._tela_ativa()
        if tela is None:
            return
        tabela = getattr(tela, "_tabela", None)
        if tabela is not None and hasattr(tabela, "_entry_pesquisa"):
            tabela._entry_pesquisa.focus_set()
            return
        entry_busca = getattr(tela, "_entry_busca", None)
        if entry_busca is not None:
            entry_busca.focus_set()

    def _atalho_imprimir(self) -> None:
        """Ctrl+P — Imprimir: dispara o mesmo botão "Imprimir" da tela atual, se houver."""
        tela = self._tela_ativa()
        if tela is not None and hasattr(tela, "_imprimir"):
            tela._imprimir()

    def definir_status(self, texto: str) -> None:
        """Atualiza a barra de status (exibida na tela principal)."""
        principal = self._telas.get("principal")
        if principal is not None and hasattr(principal, "definir_status"):
            principal.definir_status(texto)

    def iniciar_revisao_funcionarios(
        self,
        sugestoes: list[SugestaoImportacao],
        funcionarios_planilha: list[FuncionarioPlanilha],
        ao_concluir_calculo: Callable[[list[Funcionario]], None],
    ) -> None:
        """
        Abre o Painel de Revisão (Cap. 5.4) na tela de Funcionários com as
        sugestões de uma importação de planilha recém-processada.
        `ao_concluir_calculo` é chamado ao final da revisão com os
        funcionários já prontos para o Motor de Cálculo (Cap. 6).
        """
        tela_funcionarios = self._telas.get("funcionarios")
        if tela_funcionarios is None:
            log.error("Tela de funcionários não encontrada para iniciar a revisão.")
            return
        tela_funcionarios.iniciar_revisao_importacao(
            sugestoes, funcionarios_planilha, ao_concluir_calculo)
        self.mostrar_tela("funcionarios")

    def iniciar_revisao_setores_novos(
        self, setores_novos: list[SetorNovoEncontrado], ao_concluir: Callable[[], None],
    ) -> None:
        """
        Abre a tela "Foram encontrados novos setores na planilha"
        (Cap. 5.17) na tela de Funcionários, antes do Painel de Revisão.
        """
        tela_funcionarios = self._telas.get("funcionarios")
        if tela_funcionarios is None:
            log.error("Tela de funcionários não encontrada para revisar setores novos.")
            return
        tela_funcionarios.iniciar_revisao_setores_novos(setores_novos, ao_concluir)
        self.mostrar_tela("funcionarios")

    def iniciar_tela_pendencias(self, competencia: Competencia) -> None:
        """
        Ponto de entrada chamado logo após o Motor de Cálculo (Cap. 6)
        processar o lote e a Competência já ter sido persistida
        (`competencias.salvar_competencia`, em `tela_principal.py`).
        Mesmo destino de `abrir_competencia()` abaixo.
        """
        self._abrir(competencia)

    def abrir_competencia(self, competencia: Competencia) -> None:
        """
        Retoma o trabalho de uma competência já persistida (Tela
        Competências, botão "Abrir" — "Retomar trabalho"): mesma decisão
        de destino de `iniciar_tela_pendencias()`, reaproveitada aqui
        para os dois pontos de entrada nunca divergirem.
        """
        self._abrir(competencia)

    def _abrir(self, competencia: Competencia) -> None:
        """
        Decide o destino de uma Competência — Pendências ou Relatórios —
        e a guarda como `competencia_atual` (dica de pré-seleção da Tela
        de Relatórios).

        Fluxo inteligente (melhoria da v1.0): se não houver nenhuma
        pendência em aberto, a Tela de Pendências é desnecessária — vai
        direto para a Tela de Relatórios. Reaproveita
        `relatorio.existem_pendencias_abertas`, a mesma checagem que já
        bloqueia a geração do relatório (Cap. 9.1/11.11), sem duplicar
        a regra.
        """
        self.competencia_atual = competencia

        if not existem_pendencias_abertas(competencia.resultado):
            self.definir_status("Sem pendências em aberto.")
            tela_relatorios = self._telas.get("relatorios")
            if tela_relatorios is not None:
                tela_relatorios.selecionar_competencia(competencia)
            self.mostrar_tela("relatorios")
            return

        tela_pendencias = self._telas.get("pendencias")
        if tela_pendencias is None:
            log.error("Tela de pendências não encontrada.")
            return
        tela_pendencias.iniciar(competencia)
        self.mostrar_tela("pendencias")

    # -- Utilidades ----------------------------------------------------------

    def _definir_icone(self) -> None:
        """
        Ícone da janela/taskbar (Cap. 17: empacotamento), a partir de
        assets/icones/app.ico — silenciosamente ignorado se ausente
        (mesmo espírito tolerante do carregamento da logo, Cap. 4.3),
        nunca impede a janela de abrir.
        """
        caminho_icone = ICONES_DIR / "app.ico"
        if not caminho_icone.exists():
            return
        try:
            self.iconbitmap(str(caminho_icone))
        except Exception as erro:  # pragma: no cover - proteção contra ambiente sem suporte a .ico
            log.error("Falha ao aplicar o ícone da janela: %s", erro)

    def _centralizar(self) -> None:
        """Centraliza a janela na tela."""
        self.update_idletasks()
        largura_tela = self.winfo_screenwidth()
        altura_tela = self.winfo_screenheight()
        pos_x = (largura_tela - self.LARGURA) // 2
        pos_y = (altura_tela - self.ALTURA) // 2
        self.geometry(f"{self.LARGURA}x{self.ALTURA}+{pos_x}+{pos_y}")
