"""
tela_configuracoes.py
---------------------
Tela de Configurações (Cap. 4 / 12.5 / 13).

Sprint 2, Etapa 2.1: componentes visuais reutilizáveis da tela de
configurações — campo Empresa, campo Logo (com preview), painel de
Turnos, blocos de Tolerâncias e da Pasta do Histórico, e um contêiner de
seção padrão usado por todos eles.

Sprint 2, Etapa 2.2: validação em tempo real desses componentes — nome
da empresa, horários dos turnos (formato e sequência lógica Entrada <
Início do Intervalo < Fim do Intervalo < Saída, com recálculo automático
da jornada), minutos das tolerâncias, e pasta do histórico (via
config.pasta_historico_valida()). Cada componente exibe sua mensagem de
erro inline e atualiza um estado de validade agregado (`ao_validar` /
`esta_tudo_valido()`), servindo de infraestrutura para os botões
"Próximo"/"Salvar" que serão criados nas próximas etapas.

Sprint 2, Etapa 2.3: Wizard de primeira execução (Cap. 4), com 7 etapas
fixas — Boas-vindas, Empresa, Turnos, Tolerâncias, Histórico, Resumo e
Conclusão —, reaproveitando integralmente os componentes e a validação
das Etapas 2.1/2.2 (nenhuma lógica de campo é duplicada aqui). Somente
na etapa "Resumo", ao clicar em "Concluir Configuração", os dados são
persistidos com os métodos já existentes em config.py, a flag
primeira_execucao é marcada como concluída, e a Tela Principal é aberta
automaticamente.

Modo de edição (Cap. 12.5, fora da primeira execução): os mesmos
componentes do Wizard, já carregados com os valores atuais, numa única
página em vez de etapas sequenciais. A persistência é explícita — botão
"Salvar Alterações", habilitado apenas quando tudo é válido — nunca a
cada tecla digitada, para não gravar um Turno ou tolerância incompletos
no meio da edição. Turnos existentes preservam seu ID ao serem
editados (Cap. 5.13/21.4); podem ser adicionados ou removidos
livremente. Esta tela nunca toca em Funcionários ou Setores.

O cabeçalho (Voltar + título) herdado do Sprint 1 permanece. O corpo
mostra o Wizard quando `config.primeira_execucao` é True; caso
contrário, o modo de edição.
"""

from __future__ import annotations

import tkinter as tk
import uuid
from datetime import datetime, time
from pathlib import Path
from tkinter import filedialog, messagebox
from typing import Callable

import customtkinter as ctk

from config import (
    HISTORICO_DIR,
    Config,
    copiar_logo,
    pasta_historico_valida,
    turno_de_dict,
    turno_para_dict,
)
from constantes import APP_NOME, EXTENSOES_IMAGEM, formatar_minutos
from logger import get_logger
from modelos import JornadaDia, Turno, indices_com_nome_duplicado

log = get_logger()

try:
    from PIL import Image
    _PIL_OK = True
except ImportError:  # pragma: no cover - Pillow faz parte das dependências
    _PIL_OK = False


# ---------------------------------------------------------------------------
# Auxiliares de formatação/parsing (uso interno desta tela)
# ---------------------------------------------------------------------------


def _texto_para_horario(texto: str) -> time | None:
    """
    Converte um texto "HH:MM" em datetime.time. Retorna None se o texto
    estiver vazio ou não for um horário válido — sem gerar erro nem
    mensagem (a validação de fato fica para a próxima etapa).
    """
    texto = texto.strip()
    if not texto:
        return None
    try:
        return datetime.strptime(texto, "%H:%M").time()
    except ValueError:
        return None


def _horario_para_texto(horario: time | None) -> str:
    """Converte um datetime.time em texto "HH:MM" para exibição em campo."""
    return horario.strftime("%H:%M") if horario is not None else ""


# ---------------------------------------------------------------------------
# Bloco de jornada opcional (Sábado ou Domingo — componente reutilizável)
# ---------------------------------------------------------------------------

class _GrupoJornadaOpcional(ctk.CTkFrame):
    """
    Bloco de horários opcional para Sábado ou Domingo (Cap. 4.6/6.4/6.5):
    um checkbox "Trabalha <dia>" que, quando marcado, revela Entrada e
    Saída e um checkbox "Possui intervalo" que por sua vez revela
    Início e Fim do intervalo. Sábado e Domingo têm exatamente o mesmo
    comportamento (Cap. 6.5) — este componente é reaproveitado duas
    vezes por `_PainelTurno`, sem duplicar nenhuma lógica entre os dois
    dias.
    """

    def __init__(self, master, rotulo_dia: str, ao_alterar: Callable[[], None]) -> None:
        super().__init__(master, fg_color="transparent")
        self._ao_alterar = ao_alterar

        self.grid_columnconfigure((1, 3), weight=1)

        self._chk_ativo = ctk.CTkCheckBox(
            self, text=f"Trabalha {rotulo_dia}", command=self._ao_alternar_ativo)
        self._chk_ativo.grid(row=0, column=0, columnspan=4, sticky="w", pady=(4, 2))

        self._rotulo_entrada = ctk.CTkLabel(self, text="Entrada")
        self._entry_entrada = ctk.CTkEntry(self, placeholder_text="HH:MM", width=90)
        self._rotulo_saida = ctk.CTkLabel(self, text="Saída")
        self._entry_saida = ctk.CTkEntry(self, placeholder_text="HH:MM", width=90)
        self._chk_possui_intervalo = ctk.CTkCheckBox(
            self, text="Possui intervalo", command=self._ao_alternar_intervalo)
        self._rotulo_inicio_intervalo = ctk.CTkLabel(self, text="Início intervalo")
        self._entry_inicio_intervalo = ctk.CTkEntry(self, placeholder_text="HH:MM", width=90)
        self._rotulo_fim_intervalo = ctk.CTkLabel(self, text="Fim intervalo")
        self._entry_fim_intervalo = ctk.CTkEntry(self, placeholder_text="HH:MM", width=90)
        self._rotulo_jornada = ctk.CTkLabel(
            self, text="Não trabalha", font=ctk.CTkFont(size=12),
            text_color=("gray60", "gray60"),
        )

        for entrada_horario in (
            self._entry_entrada, self._entry_saida,
            self._entry_inicio_intervalo, self._entry_fim_intervalo,
        ):
            entrada_horario.bind("<KeyRelease>", lambda evento: self._ao_alterar())

        self._rotulo_entrada.grid(row=1, column=0, sticky="w", padx=(20, 5), pady=2)
        self._entry_entrada.grid(row=1, column=1, sticky="w", pady=2)
        self._rotulo_saida.grid(row=1, column=2, sticky="w", padx=(10, 5), pady=2)
        self._entry_saida.grid(row=1, column=3, sticky="w", pady=2)

        self._chk_possui_intervalo.grid(
            row=2, column=0, columnspan=4, sticky="w", padx=(20, 0), pady=2)

        self._rotulo_inicio_intervalo.grid(row=3, column=0, sticky="w", padx=(20, 5), pady=2)
        self._entry_inicio_intervalo.grid(row=3, column=1, sticky="w", pady=2)
        self._rotulo_fim_intervalo.grid(row=3, column=2, sticky="w", padx=(10, 5), pady=2)
        self._entry_fim_intervalo.grid(row=3, column=3, sticky="w", pady=2)

        self._rotulo_jornada.grid(
            row=4, column=0, columnspan=4, sticky="w", padx=(20, 0), pady=(0, 4))

        self._atualizar_visibilidade()

    # -- Mostrar/esconder campos conforme os checkboxes (Cap. 4.6) -----------

    def _ao_alternar_ativo(self) -> None:
        self._atualizar_visibilidade()
        self._ao_alterar()

    def _ao_alternar_intervalo(self) -> None:
        self._atualizar_visibilidade()
        self._ao_alterar()

    def _atualizar_visibilidade(self) -> None:
        """
        Nada fica visível desnecessariamente (Cap. 4.6/8): Entrada/
        Saída só aparecem com o dia ativo; Início/Fim do intervalo só
        aparecem com "Possui intervalo" marcado.
        """
        ativo = bool(self._chk_ativo.get())
        for widget in (
            self._rotulo_entrada, self._entry_entrada,
            self._rotulo_saida, self._entry_saida, self._chk_possui_intervalo,
        ):
            widget.grid() if ativo else widget.grid_remove()

        possui_intervalo = ativo and bool(self._chk_possui_intervalo.get())
        for widget in (
            self._rotulo_inicio_intervalo, self._entry_inicio_intervalo,
            self._rotulo_fim_intervalo, self._entry_fim_intervalo,
        ):
            widget.grid() if possui_intervalo else widget.grid_remove()

    # -- Acesso aos dados ------------------------------------------------

    def obter_jornada(self) -> JornadaDia | None:
        """Retorna a JornadaDia deste dia, ou None se o checkbox estiver desmarcado."""
        if not self._chk_ativo.get():
            return None
        possui_intervalo = bool(self._chk_possui_intervalo.get())
        return JornadaDia(
            entrada=_texto_para_horario(self._entry_entrada.get()),
            saida=_texto_para_horario(self._entry_saida.get()),
            inicio_intervalo=(
                _texto_para_horario(self._entry_inicio_intervalo.get())
                if possui_intervalo else None
            ),
            fim_intervalo=(
                _texto_para_horario(self._entry_fim_intervalo.get())
                if possui_intervalo else None
            ),
        )

    def definir_jornada(self, jornada: JornadaDia | None) -> None:
        """Preenche os widgets a partir de uma JornadaDia — None = dia inativo."""
        for entry in (
            self._entry_entrada, self._entry_saida,
            self._entry_inicio_intervalo, self._entry_fim_intervalo,
        ):
            entry.delete(0, "end")

        if jornada is None:
            self._chk_ativo.deselect()
            self._chk_possui_intervalo.deselect()
        else:
            self._chk_ativo.select()
            self._entry_entrada.insert(0, _horario_para_texto(jornada.entrada))
            self._entry_saida.insert(0, _horario_para_texto(jornada.saida))
            possui_intervalo = (
                jornada.inicio_intervalo is not None and jornada.fim_intervalo is not None
            )
            if possui_intervalo:
                self._chk_possui_intervalo.select()
                self._entry_inicio_intervalo.insert(
                    0, _horario_para_texto(jornada.inicio_intervalo))
                self._entry_fim_intervalo.insert(0, _horario_para_texto(jornada.fim_intervalo))
            else:
                self._chk_possui_intervalo.deselect()

        self._atualizar_visibilidade()

    def jornada_prevista_minutos(self) -> int | None:
        jornada = self.obter_jornada()
        return jornada.jornada_prevista_minutos() if jornada is not None else None

    # -- Validação (Cap. 4.6/8) ------------------------------------------

    def validar(self) -> list[str]:
        """
        Quando o dia está inativo, não há nada a validar (Cap. 4.6:
        "não validar" quando desmarcado). Quando ativo, Entrada e
        Saída são obrigatórios; com "Possui intervalo" marcado,
        Início/Fim do intervalo também passam a ser obrigatórios, e a
        sequência lógica dos horários deve fazer sentido. Retorna a
        lista de mensagens de erro (vazia se válido).
        """
        if not self._chk_ativo.get():
            return []

        erros: list[str] = []
        texto_entrada = self._entry_entrada.get().strip()
        texto_saida = self._entry_saida.get().strip()
        entrada = _texto_para_horario(texto_entrada)
        saida = _texto_para_horario(texto_saida)

        if not texto_entrada:
            erros.append("Informe o horário de entrada.")
        elif entrada is None:
            erros.append("Entrada inválida (use HH:MM).")

        if not texto_saida:
            erros.append("Informe o horário de saída.")
        elif saida is None:
            erros.append("Saída inválida (use HH:MM).")

        if bool(self._chk_possui_intervalo.get()):
            texto_inicio = self._entry_inicio_intervalo.get().strip()
            texto_fim = self._entry_fim_intervalo.get().strip()
            inicio = _texto_para_horario(texto_inicio)
            fim = _texto_para_horario(texto_fim)

            if not texto_inicio:
                erros.append("Informe o início do intervalo.")
            elif inicio is None:
                erros.append("Início do intervalo inválido (use HH:MM).")

            if not texto_fim:
                erros.append("Informe o fim do intervalo.")
            elif fim is None:
                erros.append("Fim do intervalo inválido (use HH:MM).")

            if entrada is not None and saida is not None and inicio is not None and fim is not None:
                if not (entrada < inicio < fim < saida):
                    erros.append(
                        "Sequência inválida: Entrada < Início do Intervalo "
                        "< Fim do Intervalo < Saída."
                    )
        elif entrada is not None and saida is not None:
            if entrada >= saida:
                erros.append("A entrada deve ser anterior à saída.")

        return erros

    def atualizar_jornada(self) -> None:
        """Recalcula e exibe a jornada prevista deste dia, a partir dos campos atuais."""
        if not self._chk_ativo.get():
            self._rotulo_jornada.configure(text="Não trabalha")
            return
        minutos = self.jornada_prevista_minutos()
        texto = formatar_minutos(minutos) if minutos is not None else "—"
        self._rotulo_jornada.configure(text=f"Jornada: {texto}")


# ---------------------------------------------------------------------------
# Painel de um único turno (componente reutilizável)
# ---------------------------------------------------------------------------

class _PainelTurno(ctk.CTkFrame):
    """
    Painel com os campos de um único turno (Cap. 4.6): nome, jornada
    de Segunda a Sexta (obrigatória), jornada de Sábado e de Domingo
    (opcionais, via `_GrupoJornadaOpcional`), e a jornada de cada dia
    calculada automaticamente a partir dos horários preenchidos.

    Componente reutilizável e sem persistência própria — `obter_turno()`
    e `definir_turno()` dão acesso ao valor atual, mantido em memória.
    """

    def __init__(self, master, turno: Turno | None = None) -> None:
        super().__init__(master, corner_radius=8, border_width=1)

        # Id estável do turno (Cap. 5.13/21.4): preservado entre chamadas
        # de obter_turno(), para que o vínculo por ID com funcionários
        # nunca mude enquanto o painel existir.
        self._id: str = turno.id if turno is not None else str(uuid.uuid4())

        self.grid_columnconfigure((1, 3), weight=1)

        self._entry_nome = ctk.CTkEntry(self, placeholder_text="Ex.: 06:00 às 15:00")
        self._entry_entrada = ctk.CTkEntry(self, placeholder_text="HH:MM", width=90)
        self._entry_saida = ctk.CTkEntry(self, placeholder_text="HH:MM", width=90)
        self._entry_inicio_intervalo = ctk.CTkEntry(self, placeholder_text="HH:MM", width=90)
        self._entry_fim_intervalo = ctk.CTkEntry(self, placeholder_text="HH:MM", width=90)
        self._rotulo_jornada_semana = ctk.CTkLabel(
            self, text="Jornada: —", font=ctk.CTkFont(weight="bold")
        )

        self._comando_alterar: Callable[[], None] | None = None
        self._grupo_sabado = _GrupoJornadaOpcional(self, "sábado", self._ao_alterar_campo)
        self._grupo_domingo = _GrupoJornadaOpcional(self, "domingo", self._ao_alterar_campo)

        self._botao_remover = ctk.CTkButton(
            self, text="Remover", width=90, fg_color="transparent", border_width=1,
        )
        self._rotulo_erro = ctk.CTkLabel(
            self, text="", text_color=("#c0392b", "#e74c3c"), anchor="w",
        )

        for entrada_horario in (
            self._entry_nome, self._entry_entrada, self._entry_saida,
            self._entry_inicio_intervalo, self._entry_fim_intervalo,
        ):
            entrada_horario.bind("<KeyRelease>", lambda evento: self._ao_alterar_campo())

        ctk.CTkLabel(self, text="Nome do turno").grid(
            row=0, column=0, sticky="w", padx=10, pady=(10, 2))
        self._entry_nome.grid(row=0, column=1, columnspan=3, sticky="ew", padx=10, pady=(10, 2))

        ctk.CTkLabel(self, text="Segunda a Sexta", font=ctk.CTkFont(weight="bold")).grid(
            row=1, column=0, columnspan=4, sticky="w", padx=10, pady=(10, 0))

        ctk.CTkLabel(self, text="Entrada").grid(row=2, column=0, sticky="w", padx=10, pady=2)
        self._entry_entrada.grid(row=2, column=1, sticky="w", padx=10, pady=2)
        ctk.CTkLabel(self, text="Saída").grid(row=2, column=2, sticky="w", padx=10, pady=2)
        self._entry_saida.grid(row=2, column=3, sticky="w", padx=10, pady=2)

        ctk.CTkLabel(self, text="Início intervalo").grid(
            row=3, column=0, sticky="w", padx=10, pady=2)
        self._entry_inicio_intervalo.grid(row=3, column=1, sticky="w", padx=10, pady=2)
        ctk.CTkLabel(self, text="Fim intervalo").grid(row=3, column=2, sticky="w", padx=10, pady=2)
        self._entry_fim_intervalo.grid(row=3, column=3, sticky="w", padx=10, pady=2)

        self._rotulo_jornada_semana.grid(
            row=4, column=0, columnspan=4, sticky="w", padx=10, pady=(2, 8))

        ctk.CTkLabel(self, text="Sábado", font=ctk.CTkFont(weight="bold")).grid(
            row=5, column=0, columnspan=4, sticky="w", padx=10, pady=(2, 0))
        self._grupo_sabado.grid(row=6, column=0, columnspan=4, sticky="ew", padx=10)

        ctk.CTkLabel(self, text="Domingo", font=ctk.CTkFont(weight="bold")).grid(
            row=7, column=0, columnspan=4, sticky="w", padx=10, pady=(10, 0))
        self._grupo_domingo.grid(row=8, column=0, columnspan=4, sticky="ew", padx=10)

        self._botao_remover.grid(row=9, column=2, columnspan=2, sticky="e", padx=10, pady=(10, 2))
        self._rotulo_erro.grid(row=10, column=0, columnspan=4, sticky="ew", padx=10, pady=(0, 10))

        if turno is not None:
            self.definir_turno(turno)

        self.validar()

    # -- Acesso aos dados ------------------------------------------------

    def obter_turno(self) -> Turno:
        """Lê os widgets atuais e retorna o Turno correspondente."""
        return Turno(
            id=self._id,
            nome=self._entry_nome.get().strip(),
            segunda_a_sexta=JornadaDia(
                entrada=_texto_para_horario(self._entry_entrada.get()),
                saida=_texto_para_horario(self._entry_saida.get()),
                inicio_intervalo=_texto_para_horario(self._entry_inicio_intervalo.get()),
                fim_intervalo=_texto_para_horario(self._entry_fim_intervalo.get()),
            ),
            sabado=self._grupo_sabado.obter_jornada(),
            domingo=self._grupo_domingo.obter_jornada(),
        )

    def definir_turno(self, turno: Turno) -> None:
        """Preenche os widgets a partir de um Turno existente."""
        self._id = turno.id
        self._entry_nome.delete(0, "end")
        self._entry_nome.insert(0, turno.nome)
        self._entry_entrada.delete(0, "end")
        self._entry_entrada.insert(0, _horario_para_texto(turno.segunda_a_sexta.entrada))
        self._entry_saida.delete(0, "end")
        self._entry_saida.insert(0, _horario_para_texto(turno.segunda_a_sexta.saida))
        self._entry_inicio_intervalo.delete(0, "end")
        self._entry_inicio_intervalo.insert(
            0, _horario_para_texto(turno.segunda_a_sexta.inicio_intervalo))
        self._entry_fim_intervalo.delete(0, "end")
        self._entry_fim_intervalo.insert(
            0, _horario_para_texto(turno.segunda_a_sexta.fim_intervalo))

        self._grupo_sabado.definir_jornada(turno.sabado)
        self._grupo_domingo.definir_jornada(turno.domingo)

    def atualizar_jornada(self) -> None:
        """Recalcula e exibe a jornada prevista de cada tipo de dia (Cap. 4.6)."""
        minutos = self.obter_turno().segunda_a_sexta.jornada_prevista_minutos()
        texto = formatar_minutos(minutos) if minutos is not None else "—"
        self._rotulo_jornada_semana.configure(text=f"Jornada: {texto}")
        self._grupo_sabado.atualizar_jornada()
        self._grupo_domingo.atualizar_jornada()

    def definir_comando_remover(self, comando: Callable[[], None]) -> None:
        """
        Define a ação executada ao clicar em "Remover". Atribuída pelo
        container (que sabe como retirar este painel específico da lista).
        """
        self._botao_remover.configure(command=comando)

    def definir_comando_alterar(self, comando: Callable[[], None]) -> None:
        """
        Define a ação executada sempre que algum campo deste painel for
        alterado. Usada pelo container para revalidar o conjunto de
        turnos como um todo.
        """
        self._comando_alterar = comando

    # -- Validação em tempo real ------------------------------------------

    def _ao_alterar_campo(self) -> None:
        """Chamado a cada alteração de campo: revalida e notifica o container."""
        self.validar()
        if self._comando_alterar is not None:
            self._comando_alterar()

    def validar(self) -> bool:
        """
        Valida nome, os horários de Segunda a Sexta (sempre obrigatórios)
        e delega a validação de Sábado/Domingo aos respectivos
        `_GrupoJornadaOpcional` (só validados quando ativos, Cap. 4.6).
        Também recalcula as três jornadas. Atualiza a mensagem de erro
        inline (a primeira encontrada) e retorna se o turno está válido.
        """
        erros: list[str] = []

        if not self._entry_nome.get().strip():
            erros.append("Informe o nome do turno.")

        texto_entrada = self._entry_entrada.get().strip()
        texto_saida = self._entry_saida.get().strip()
        texto_inicio = self._entry_inicio_intervalo.get().strip()
        texto_fim = self._entry_fim_intervalo.get().strip()

        entrada = _texto_para_horario(texto_entrada)
        saida = _texto_para_horario(texto_saida)
        inicio = _texto_para_horario(texto_inicio)
        fim = _texto_para_horario(texto_fim)

        if not texto_entrada:
            erros.append("Informe o horário de entrada (Segunda a Sexta).")
        elif entrada is None:
            erros.append("Entrada inválida (Segunda a Sexta, use HH:MM).")

        if not texto_saida:
            erros.append("Informe o horário de saída (Segunda a Sexta).")
        elif saida is None:
            erros.append("Saída inválida (Segunda a Sexta, use HH:MM).")

        if texto_inicio and inicio is None:
            erros.append("Início do intervalo inválido (Segunda a Sexta, use HH:MM).")
        if texto_fim and fim is None:
            erros.append("Fim do intervalo inválido (Segunda a Sexta, use HH:MM).")

        if bool(texto_inicio) != bool(texto_fim):
            erros.append(
                "Preencha início e fim do intervalo (Segunda a Sexta), ou deixe ambos em branco."
            )

        if entrada is not None and saida is not None and inicio is not None and fim is not None:
            if not (entrada < inicio < fim < saida):
                erros.append(
                    "Sequência inválida (Segunda a Sexta): Entrada < Início do Intervalo "
                    "< Fim do Intervalo < Saída."
                )
        elif entrada is not None and saida is not None and inicio is None and fim is None:
            if entrada >= saida:
                erros.append("A entrada deve ser anterior à saída (Segunda a Sexta).")

        erros.extend(f"Sábado: {erro}" for erro in self._grupo_sabado.validar())
        erros.extend(f"Domingo: {erro}" for erro in self._grupo_domingo.validar())

        valido = not erros
        self._rotulo_erro.configure(text=erros[0] if erros else "")
        self.atualizar_jornada()
        return valido

    def marcar_duplicado(self, duplicado: bool) -> None:
        """
        Exibe (ou limpa) o aviso de nome duplicado — checado pelo
        container (`TelaConfiguracoes._revalidar_turnos`), que é quem
        enxerga todos os turnos ao mesmo tempo; este painel não sabe
        nada sobre os demais. Só substitui a mensagem de erro quando
        não há nenhum outro erro de campo já sendo exibido, para não
        mascarar um problema mais específico (ex.: horário inválido).
        """
        if duplicado and not self._rotulo_erro.cget("text"):
            self._rotulo_erro.configure(text="Já existe um turno com esse nome.")


# ---------------------------------------------------------------------------
# Tela de Configurações
# ---------------------------------------------------------------------------

class TelaConfiguracoes(ctk.CTkFrame):
    """Tela de configurações do sistema (Cap. 4 / 12.5)."""

    def __init__(self, master, controlador, config: Config) -> None:
        super().__init__(master, corner_radius=0)

        self.controlador = controlador
        self.config_app = config

        self._paineis_turno: list[_PainelTurno] = []
        self._logo_caminho_atual: str | None = None
        self._logo_selecionada: Path | None = None
        self._tolerancias: dict[str, tuple[ctk.CTkCheckBox, ctk.CTkEntry, ctk.CTkLabel]] = {}

        self._estado_validacao: dict[str, bool] = {}
        self.ao_validar: Callable[[], None] | None = None

        self.grid_rowconfigure(1, weight=1)
        self.grid_columnconfigure(0, weight=1)

        cabecalho = ctk.CTkFrame(self, corner_radius=0, height=70)
        cabecalho.grid(row=0, column=0, sticky="ew")
        cabecalho.grid_columnconfigure(1, weight=1)

        ctk.CTkButton(
            cabecalho, text="← Voltar", width=90,
            command=lambda: self.controlador.mostrar_tela("principal"),
        ).grid(row=0, column=0, padx=15, pady=15)

        ctk.CTkLabel(
            cabecalho, text="Configurações",
            font=ctk.CTkFont(size=20, weight="bold"),
        ).grid(row=0, column=1, sticky="w", padx=10)

        if config.primeira_execucao:
            self._montar_wizard()
        else:
            self._montar_edicao()

    # -- Infraestrutura de validação -------------------------------------------

    def _definir_validade(self, chave: str, valido: bool) -> None:
        """
        Atualiza o estado de validade de um componente e notifica o
        observador externo, se houver. Infraestrutura para as próximas
        etapas habilitarem/desabilitarem os botões "Próximo"/"Salvar" —
        nenhum botão é criado aqui.
        """
        self._estado_validacao[chave] = valido
        if self.ao_validar is not None:
            self.ao_validar()

    def esta_tudo_valido(self) -> bool:
        """True se todos os componentes atualmente registrados estão válidos."""
        return all(self._estado_validacao.values())

    # -- Estrutura visual reutilizável ----------------------------------------

    def _montar_secao(self, master, titulo: str) -> ctk.CTkFrame:
        """
        Contêiner visual padrão de uma seção de configuração (título +
        corpo), reaproveitado tanto pelo Wizard quanto pelo modo de edição.
        """
        secao = ctk.CTkFrame(master, corner_radius=10)
        ctk.CTkLabel(
            secao, text=titulo, font=ctk.CTkFont(size=16, weight="bold"), anchor="w",
        ).pack(fill="x", padx=15, pady=(15, 5))
        return secao

    # -- Campo Empresa (Cap. 4.2) ----------------------------------------------

    def _montar_campo_empresa(self, master, nome_inicial: str = "") -> ctk.CTkFrame:
        """Componente: nome da empresa."""
        secao = self._montar_secao(master, "Empresa")

        self._entry_nome_empresa = ctk.CTkEntry(secao, placeholder_text="Nome da empresa")
        self._entry_nome_empresa.insert(0, nome_inicial)
        self._entry_nome_empresa.pack(fill="x", padx=15, pady=(0, 5))
        self._entry_nome_empresa.bind(
            "<KeyRelease>", lambda evento: self._validar_nome_empresa()
        )

        self._rotulo_erro_empresa = ctk.CTkLabel(
            secao, text="", text_color=("#c0392b", "#e74c3c"), anchor="w",
        )
        self._rotulo_erro_empresa.pack(fill="x", padx=15, pady=(0, 15))

        self._validar_nome_empresa()

        return secao

    def obter_nome_empresa(self) -> str:
        """Lê o nome da empresa atualmente digitado."""
        return self._entry_nome_empresa.get().strip()

    def _validar_nome_empresa(self) -> bool:
        """Valida se o nome da empresa foi preenchido (Cap. 4.2)."""
        valido = bool(self.obter_nome_empresa())
        self._rotulo_erro_empresa.configure(
            text="" if valido else "Informe o nome da empresa."
        )
        self._definir_validade("empresa", valido)
        return valido

    # -- Campo Logo com preview (Cap. 4.3) -------------------------------------

    def _montar_campo_logo(self, master, caminho_inicial: str | None = None) -> ctk.CTkFrame:
        """Componente: seleção da logo, com preview."""
        secao = self._montar_secao(master, "Logo da Empresa")
        self._logo_caminho_atual = caminho_inicial
        self._logo_selecionada = None

        corpo = ctk.CTkFrame(secao, fg_color="transparent")
        corpo.pack(fill="x", padx=15, pady=(0, 15))

        self._rotulo_preview_logo = ctk.CTkLabel(corpo, text="Sem logo selecionada", width=90)
        self._rotulo_preview_logo.pack(side="left", padx=(0, 15))

        ctk.CTkButton(
            corpo, text="Selecionar Logo", command=self._selecionar_logo,
        ).pack(side="left")

        if caminho_inicial:
            self._exibir_preview_logo(Path(caminho_inicial))

        return secao

    def _selecionar_logo(self) -> None:
        """
        Abre o seletor de imagem e atualiza apenas o preview em memória.
        Não copia o arquivo nem grava nada — isso fica para a etapa de
        salvamento (Cap. 4.3: o arquivo original nunca é usado direto).
        """
        tipos = [
            ("Imagens", " ".join(f"*{ext}" for ext in EXTENSOES_IMAGEM)),
            ("Todos", "*.*"),
        ]
        caminho = filedialog.askopenfilename(title="Selecionar logo", filetypes=tipos)
        if not caminho:
            return

        arquivo = Path(caminho)
        if arquivo.suffix.lower() not in EXTENSOES_IMAGEM:
            log.warning("Formato de imagem não suportado selecionado: %s", arquivo.suffix)
            return

        self._logo_selecionada = arquivo
        self._exibir_preview_logo(arquivo)

    def _exibir_preview_logo(self, caminho: Path) -> None:
        """Carrega e exibe uma prévia da imagem informada, se possível."""
        if not _PIL_OK or not caminho.exists():
            return
        try:
            imagem = Image.open(caminho)
            preview = ctk.CTkImage(light_image=imagem, dark_image=imagem, size=(80, 80))
            self._rotulo_preview_logo.configure(image=preview, text="")
            self._rotulo_preview_logo.imagem = preview
        except Exception as erro:  # pragma: no cover - proteção contra imagem inválida
            log.error("Falha ao carregar preview da logo: %s", erro)

    def obter_logo_selecionada(self) -> Path | None:
        """Retorna o novo arquivo de logo escolhido nesta sessão (ainda não
        copiado para assets/logo), ou None se nada foi trocado."""
        return self._logo_selecionada

    # -- Painel de Turnos (Cap. 4.6) --------------------------------------------

    def _montar_lista_turnos(
        self, master, turnos_iniciais: list[Turno] | None = None,
    ) -> ctk.CTkFrame:
        """Componente: lista de turnos cadastrados, com adicionar/remover."""
        secao = self._montar_secao(master, "Turnos")

        self._scroll_turnos = ctk.CTkScrollableFrame(secao, height=220, fg_color="transparent")
        self._scroll_turnos.pack(fill="both", expand=True, padx=15, pady=(0, 10))

        ctk.CTkButton(
            secao, text="+ Adicionar Turno", command=lambda: self._adicionar_painel_turno(),
        ).pack(anchor="w", padx=15, pady=(0, 5))

        self._rotulo_erro_turnos = ctk.CTkLabel(
            secao, text="", text_color=("#c0392b", "#e74c3c"), anchor="w",
        )
        self._rotulo_erro_turnos.pack(fill="x", padx=15, pady=(0, 15))

        self._paineis_turno = []
        for turno in (turnos_iniciais or []):
            self._adicionar_painel_turno(turno)
        self._revalidar_turnos()

        return secao

    def _adicionar_painel_turno(self, turno: Turno | None = None) -> _PainelTurno:
        """Cria e adiciona um novo painel de turno à lista."""
        painel = _PainelTurno(self._scroll_turnos, turno=turno)
        painel.definir_comando_remover(lambda: self._remover_painel_turno(painel))
        painel.definir_comando_alterar(self._revalidar_turnos)
        painel.pack(fill="x", padx=5, pady=6)
        self._paineis_turno.append(painel)
        self._revalidar_turnos()
        return painel

    def _remover_painel_turno(self, painel: _PainelTurno) -> None:
        """
        Remove um painel de turno da lista. Se o Turno já estiver em
        uso por algum funcionário cadastrado, pede confirmação antes
        de remover (Cap. 12.5) — o Motor de Cálculo (Cap. 9.2) já
        trata graciosamente um funcionário sem Turno válido (gera uma
        pendência "Turno não definido"), mas essa é uma decisão que o
        usuário deve tomar conscientemente, não por engano.
        """
        turno_id = painel.obter_turno().id
        funcionarios_vinculados = [
            f.get("nome_completo", "—")
            for f in self.config_app.funcionarios.get("funcionarios", [])
            if f.get("turno_id") == turno_id
        ]
        if funcionarios_vinculados:
            quantidade = len(funcionarios_vinculados)
            exemplos = ", ".join(funcionarios_vinculados[:5])
            if quantidade > 5:
                exemplos += f" e mais {quantidade - 5}"
            confirmar = messagebox.askyesno(
                "Turno em uso",
                f"Este turno está vinculado a {quantidade} funcionário(s) "
                f"({exemplos}). Removê-lo deixará esses funcionários sem "
                "turno válido até que sejam reatribuídos a outro turno. "
                "Deseja continuar?",
            )
            if not confirmar:
                return

        if painel in self._paineis_turno:
            self._paineis_turno.remove(painel)
        painel.destroy()
        self._revalidar_turnos()

    def obter_turnos(self) -> list[Turno]:
        """Lê todos os painéis de turno atualmente na lista."""
        return [painel.obter_turno() for painel in self._paineis_turno]

    def _revalidar_turnos(self) -> None:
        """
        Revalida todos os painéis de turno (campos + nomes duplicados
        entre si) e exige pelo menos 1 turno cadastrado — sem isso,
        nenhum funcionário pode ser corretamente vinculado a um Turno
        (Cap. 4.6/5.13). Atualiza o estado agregado de validade.
        """
        campos_validos = [painel.validar() for painel in self._paineis_turno]

        nomes = [painel.obter_turno().nome for painel in self._paineis_turno]
        indices_duplicados = indices_com_nome_duplicado(nomes)
        for indice, painel in enumerate(self._paineis_turno):
            painel.marcar_duplicado(indice in indices_duplicados)

        self._rotulo_erro_turnos.configure(
            text="É necessário cadastrar pelo menos 1 turno." if not self._paineis_turno else ""
        )

        valido = (
            all(campos_validos)
            and not indices_duplicados
            and len(self._paineis_turno) >= 1
        )
        self._definir_validade("turnos", valido)

    # -- Bloco de Tolerâncias (Cap. 8) ------------------------------------------

    def _montar_bloco_tolerancia(
        self,
        master,
        chave: str,
        titulo: str,
        ativa_inicial: bool = False,
        minutos_inicial: int = 0,
    ) -> ctk.CTkFrame:
        """
        Componente reutilizável de tolerância: checkbox ativar/desativar +
        campo de minutos, habilitado apenas quando ativo. `chave` identifica
        esta tolerância (ex.: "entrada", "almoco") para leitura posterior
        via obter_tolerancia(chave).
        """
        secao = self._montar_secao(master, titulo)

        corpo = ctk.CTkFrame(secao, fg_color="transparent")
        corpo.pack(fill="x", padx=15, pady=(0, 5))

        entry_minutos = ctk.CTkEntry(corpo, width=80, placeholder_text="min")
        entry_minutos.insert(0, str(minutos_inicial))

        def _alternar_estado() -> None:
            entry_minutos.configure(state="normal" if chk_ativa.get() else "disabled")
            self._validar_tolerancia(chave)

        chk_ativa = ctk.CTkCheckBox(corpo, text="Ativar tolerância", command=_alternar_estado)
        if ativa_inicial:
            chk_ativa.select()
        chk_ativa.pack(side="left")

        ctk.CTkLabel(corpo, text="Minutos:").pack(side="left", padx=(20, 5))
        entry_minutos.pack(side="left")
        entry_minutos.bind("<KeyRelease>", lambda evento: self._validar_tolerancia(chave))

        rotulo_erro = ctk.CTkLabel(
            secao, text="", text_color=("#c0392b", "#e74c3c"), anchor="w",
        )
        rotulo_erro.pack(fill="x", padx=15, pady=(0, 15))

        self._tolerancias[chave] = (chk_ativa, entry_minutos, rotulo_erro)
        _alternar_estado()

        return secao

    def obter_tolerancia(self, chave: str) -> tuple[bool, int]:
        """Retorna (ativa, minutos) para a tolerância identificada por `chave`."""
        chk_ativa, entry_minutos, _rotulo_erro = self._tolerancias[chave]
        ativa = bool(chk_ativa.get())
        try:
            minutos = int(entry_minutos.get().strip() or 0)
        except ValueError:
            minutos = 0
        return ativa, minutos

    def _validar_tolerancia(self, chave: str) -> bool:
        """
        Valida os minutos de uma tolerância quando está ativa (Cap. 8):
        devem ser um número inteiro não-negativo.
        """
        chk_ativa, entry_minutos, rotulo_erro = self._tolerancias[chave]
        ativa = bool(chk_ativa.get())
        texto = entry_minutos.get().strip()

        valido = True
        mensagem = ""
        if ativa:
            if not texto:
                valido = False
                mensagem = "Informe os minutos de tolerância."
            else:
                try:
                    minutos = int(texto)
                except ValueError:
                    valido = False
                    mensagem = "Minutos deve ser um número inteiro."
                else:
                    if minutos < 0:
                        valido = False
                        mensagem = "Os minutos não podem ser negativos."

        rotulo_erro.configure(text=mensagem)
        self._definir_validade(f"tolerancia_{chave}", valido)
        return valido

    # -- Bloco da Pasta do Histórico (Cap. 4.1) ---------------------------------

    def _montar_bloco_historico(
        self, master, pasta_inicial: str = "", usar_padrao_inicial: bool = True,
    ) -> ctk.CTkFrame:
        """Componente: pasta padrão do sistema ou pasta personalizada."""
        secao = self._montar_secao(master, "Pasta do Histórico")

        self._var_historico_opcao = tk.StringVar(
            value="padrao" if usar_padrao_inicial else "personalizada"
        )

        def _alternar_estado() -> None:
            estado = "normal" if self._var_historico_opcao.get() == "personalizada" else "disabled"
            self._entry_historico_pasta.configure(state=estado)
            self._validar_pasta_historico()

        ctk.CTkRadioButton(
            secao, text="Usar pasta padrão", variable=self._var_historico_opcao,
            value="padrao", command=_alternar_estado,
        ).pack(anchor="w", padx=15, pady=(0, 5))

        ctk.CTkRadioButton(
            secao, text="Escolher pasta personalizada", variable=self._var_historico_opcao,
            value="personalizada", command=_alternar_estado,
        ).pack(anchor="w", padx=15, pady=(0, 5))

        linha_pasta = ctk.CTkFrame(secao, fg_color="transparent")
        linha_pasta.pack(fill="x", padx=15, pady=(0, 5))

        self._entry_historico_pasta = ctk.CTkEntry(linha_pasta, placeholder_text="Caminho da pasta")
        self._entry_historico_pasta.insert(0, pasta_inicial)
        self._entry_historico_pasta.pack(side="left", fill="x", expand=True, padx=(0, 10))
        self._entry_historico_pasta.bind(
            "<KeyRelease>", lambda evento: self._validar_pasta_historico()
        )

        ctk.CTkButton(
            linha_pasta, text="Procurar...", width=100,
            command=self._selecionar_pasta_historico,
        ).pack(side="left")

        self._rotulo_erro_historico = ctk.CTkLabel(
            secao, text="", text_color=("#c0392b", "#e74c3c"), anchor="w",
        )
        self._rotulo_erro_historico.pack(fill="x", padx=15, pady=(0, 15))

        _alternar_estado()

        return secao

    def _selecionar_pasta_historico(self) -> None:
        """Abre o seletor de pasta e atualiza o campo (sem salvar ainda)."""
        caminho = filedialog.askdirectory(title="Selecionar pasta do histórico")
        if not caminho:
            return
        self._entry_historico_pasta.delete(0, "end")
        self._entry_historico_pasta.insert(0, caminho)
        self._validar_pasta_historico()

    def obter_pasta_historico(self) -> tuple[bool, str]:
        """Retorna (usar_padrao, caminho_personalizado_digitado)."""
        usar_padrao = self._var_historico_opcao.get() == "padrao"
        return usar_padrao, self._entry_historico_pasta.get().strip()

    def _validar_pasta_historico(self) -> bool:
        """
        Valida a pasta do histórico usando config.pasta_historico_valida()
        quando a opção "personalizada" está selecionada (Cap. 4.1). A
        opção "padrão" é sempre válida (a pasta é criada por
        garantir_estrutura() na inicialização do sistema).
        """
        usar_padrao, pasta_texto = self.obter_pasta_historico()

        valido = True
        mensagem = ""
        if not usar_padrao:
            if not pasta_texto:
                valido = False
                mensagem = "Informe o caminho da pasta personalizada."
            elif not pasta_historico_valida(Path(pasta_texto)):
                valido = False
                mensagem = "Pasta inválida: verifique se ela existe e é gravável."

        self._rotulo_erro_historico.configure(text=mensagem)
        self._definir_validade("historico", valido)
        return valido

    # -- Wizard de Primeira Execução (Cap. 4) -----------------------------------
    #
    # Monta 7 etapas fixas reaproveitando exclusivamente os componentes e a
    # validação já construídos acima. Nenhum campo/lógica é duplicado aqui —
    # cada etapa apenas chama os `_montar_*`/`obter_*` já existentes.

    def _montar_wizard(self) -> None:
        """Monta o Wizard completo e exibe a primeira etapa (Boas-vindas)."""
        self._wizard_indice = 0

        self._frame_wizard = ctk.CTkFrame(self, fg_color="transparent")
        self._frame_wizard.grid(row=1, column=0, sticky="nsew", padx=30, pady=15)
        self._frame_wizard.grid_rowconfigure(0, weight=1)
        self._frame_wizard.grid_columnconfigure(0, weight=1)

        area_etapas = ctk.CTkFrame(self._frame_wizard, fg_color="transparent")
        area_etapas.grid(row=0, column=0, sticky="nsew")
        area_etapas.grid_rowconfigure(0, weight=1)
        area_etapas.grid_columnconfigure(0, weight=1)

        self._wizard_etapas: list[ctk.CTkFrame] = [
            self._montar_etapa_boas_vindas(area_etapas),
            self._montar_etapa_wizard_empresa(area_etapas),
            self._montar_etapa_wizard_turnos(area_etapas),
            self._montar_etapa_wizard_tolerancias(area_etapas),
            self._montar_etapa_wizard_historico(area_etapas),
            self._montar_etapa_resumo(area_etapas),
            self._montar_etapa_conclusao(area_etapas),
        ]
        for etapa in self._wizard_etapas:
            etapa.grid(row=0, column=0, sticky="nsew")

        self._montar_rodape_wizard(self._frame_wizard)

        self.ao_validar = self._atualizar_botao_proximo
        self._exibir_etapa_wizard(0)

    def _montar_rodape_wizard(self, master) -> None:
        """Rodapé fixo do Wizard: indicador de etapa + navegação."""
        rodape = ctk.CTkFrame(master, fg_color="transparent")
        rodape.grid(row=1, column=0, sticky="ew", pady=(15, 0))
        rodape.grid_columnconfigure(1, weight=1)

        self._rotulo_progresso_wizard = ctk.CTkLabel(
            rodape, text="", font=ctk.CTkFont(size=12),
            text_color=("gray60", "gray60"),
        )
        self._rotulo_progresso_wizard.grid(row=0, column=0, sticky="w")

        self._botao_wizard_voltar = ctk.CTkButton(
            rodape, text="Voltar", width=110, fg_color="transparent", border_width=1,
            command=self._wizard_etapa_anterior,
        )
        self._botao_wizard_voltar.grid(row=0, column=2, padx=(0, 10))

        self._botao_wizard_proximo = ctk.CTkButton(
            rodape, text="Próximo", width=160, command=self._wizard_proxima_etapa,
        )
        self._botao_wizard_proximo.grid(row=0, column=3)

    # -- Navegação entre etapas --------------------------------------------------

    def _wizard_proxima_etapa(self) -> None:
        """Avança para a próxima etapa do Wizard."""
        if self._wizard_indice < len(self._wizard_etapas) - 1:
            self._exibir_etapa_wizard(self._wizard_indice + 1)

    def _wizard_etapa_anterior(self) -> None:
        """Volta para a etapa anterior do Wizard."""
        if self._wizard_indice > 0:
            self._exibir_etapa_wizard(self._wizard_indice - 1)

    def _exibir_etapa_wizard(self, indice: int) -> None:
        """Exibe a etapa do Wizard pelo índice e atualiza rodapé/navegação."""
        self._wizard_indice = indice
        self._wizard_etapas[indice].tkraise()

        total = len(self._wizard_etapas)
        self._rotulo_progresso_wizard.configure(text=f"Etapa {indice + 1} de {total}")

        if indice == 0:
            self._botao_wizard_voltar.grid_remove()
        else:
            self._botao_wizard_voltar.grid()

        if indice == total - 1:
            # Etapa 7 - Conclusão: sem botões, encerra e segue automaticamente.
            self._botao_wizard_proximo.grid_remove()
            self._botao_wizard_voltar.grid_remove()
            self.after(1500, self._wizard_ir_para_principal)
        elif indice == total - 2:
            # Etapa 6 - Resumo: só "Voltar" e "Concluir Configuração".
            self._atualizar_resumo()
            self._botao_wizard_proximo.grid()
            self._botao_wizard_proximo.configure(
                text="Concluir Configuração", command=self._wizard_concluir,
            )
        elif indice == 0:
            self._botao_wizard_proximo.grid()
            self._botao_wizard_proximo.configure(text="Começar", command=self._wizard_proxima_etapa)
        else:
            self._botao_wizard_proximo.grid()
            self._botao_wizard_proximo.configure(text="Próximo", command=self._wizard_proxima_etapa)

        self._atualizar_botao_proximo()

    def _atualizar_botao_proximo(self) -> None:
        """
        Habilita/desabilita o botão de avanço conforme a validade dos
        componentes da etapa atual do Wizard. Também serve como
        observador (`ao_validar`) chamado a cada mudança de validade em
        qualquer componente. Boas-vindas, Resumo e Conclusão não têm
        campo próprio a validar aqui — "Resumo" valida tudo ao clicar em
        "Concluir Configuração" (ver `_wizard_concluir`).
        """
        if not hasattr(self, "_wizard_etapas"):
            return

        chaves_por_etapa: dict[int, list[str]] = {
            1: ["empresa"],
            2: ["turnos"],
            3: ["tolerancia_entrada", "tolerancia_almoco"],
            4: ["historico"],
        }
        chaves = chaves_por_etapa.get(self._wizard_indice)
        if chaves is None:
            self._botao_wizard_proximo.configure(state="normal")
            return

        valido = all(self._estado_validacao.get(chave, True) for chave in chaves)
        self._botao_wizard_proximo.configure(state="normal" if valido else "disabled")

    # -- Etapa 1: Boas-vindas -----------------------------------------------------

    def _montar_etapa_boas_vindas(self, master) -> ctk.CTkFrame:
        """Etapa 1: apresentação do sistema (Cap. 4.1)."""
        etapa = ctk.CTkFrame(master, fg_color="transparent")
        ctk.CTkLabel(
            etapa, text=f"Bem-vindo(a) ao {APP_NOME}",
            font=ctk.CTkFont(size=22, weight="bold"),
        ).pack(pady=(60, 15))
        ctk.CTkLabel(
            etapa,
            text=(
                "Antes de começar, vamos configurar rapidamente o sistema:\n"
                "nome da empresa, logo, turnos, tolerâncias e pasta do histórico.\n\n"
                "Essa configuração é feita apenas uma vez."
            ),
            font=ctk.CTkFont(size=14),
            text_color=("gray70", "gray70"),
            justify="center",
        ).pack()
        return etapa

    # -- Etapa 2: Empresa (reaproveita Etapa 2.1/2.2) -----------------------------

    def _montar_etapa_wizard_empresa(self, master) -> ctk.CTkFrame:
        """Etapa 2: nome da empresa e logo (Cap. 4.2/4.3)."""
        etapa = ctk.CTkFrame(master, fg_color="transparent")
        self._montar_campo_empresa(
            etapa, nome_inicial=self.config_app.nome_empresa,
        ).pack(fill="x", pady=(0, 15))
        self._montar_campo_logo(
            etapa, caminho_inicial=self.config_app.empresa.get("logo_caminho") or None,
        ).pack(fill="x")
        return etapa

    # -- Etapa 3: Turnos (reaproveita Etapa 2.1/2.2) ------------------------------

    def _montar_etapa_wizard_turnos(self, master) -> ctk.CTkFrame:
        """Etapa 3: cadastro de turnos (Cap. 4.6)."""
        etapa = ctk.CTkFrame(master, fg_color="transparent")
        self._montar_lista_turnos(etapa).pack(fill="both", expand=True)
        return etapa

    # -- Etapa 4: Tolerâncias (reaproveita Etapa 2.1/2.2) -------------------------

    def _montar_etapa_wizard_tolerancias(self, master) -> ctk.CTkFrame:
        """Etapa 4: tolerâncias de entrada e de intervalo (Cap. 4.7/4.8)."""
        etapa = ctk.CTkFrame(master, fg_color="transparent")
        self._montar_bloco_tolerancia(
            etapa, chave="entrada", titulo="Tolerância de Entrada",
        ).pack(fill="x", pady=(0, 15))
        self._montar_bloco_tolerancia(
            etapa, chave="almoco", titulo="Tolerância do Intervalo",
        ).pack(fill="x")
        return etapa

    # -- Etapa 5: Histórico (reaproveita Etapa 2.1/2.2) ---------------------------

    def _montar_etapa_wizard_historico(self, master) -> ctk.CTkFrame:
        """Etapa 5: pasta do histórico (Cap. 4.1)."""
        etapa = ctk.CTkFrame(master, fg_color="transparent")
        self._montar_bloco_historico(etapa).pack(fill="x")
        return etapa

    # -- Etapa 6: Resumo -----------------------------------------------------------

    def _montar_etapa_resumo(self, master) -> ctk.CTkFrame:
        """
        Etapa 6: resumo de conferência. Não salva nada — os valores são
        lidos (via os mesmos `obter_*`) e exibidos toda vez que esta
        etapa é exibida, através de `_atualizar_resumo()`.
        """
        etapa = ctk.CTkFrame(master, fg_color="transparent")
        ctk.CTkLabel(
            etapa, text="Resumo e Confirmação",
            font=ctk.CTkFont(size=18, weight="bold"),
        ).pack(anchor="w", pady=(0, 15))

        self._frame_resumo_linhas = ctk.CTkFrame(etapa, fg_color="transparent")
        self._frame_resumo_linhas.pack(fill="x")

        self._rotulo_erro_resumo = ctk.CTkLabel(
            etapa, text="", text_color=("#c0392b", "#e74c3c"), anchor="w",
        )
        self._rotulo_erro_resumo.pack(fill="x", pady=(15, 0))

        return etapa

    def _atualizar_resumo(self) -> None:
        """Preenche o resumo com os valores atuais coletados no Wizard."""
        self._rotulo_erro_resumo.configure(text="")

        for widget in self._frame_resumo_linhas.winfo_children():
            widget.destroy()

        tem_logo = self.obter_logo_selecionada() is not None or bool(self._logo_caminho_atual)
        turnos = self.obter_turnos()
        ativa_entrada, minutos_entrada = self.obter_tolerancia("entrada")
        ativa_almoco, minutos_almoco = self.obter_tolerancia("almoco")
        usar_padrao, pasta_personalizada = self.obter_pasta_historico()

        linhas = [
            ("Empresa", self.obter_nome_empresa() or "—"),
            ("Logo", "✔ Selecionada" if tem_logo else "Nenhuma"),
            ("Turnos", f"{len(turnos)} cadastrado(s)"),
            (
                "Tolerância Entrada",
                f"{minutos_entrada} minutos" if ativa_entrada else "Desativada",
            ),
            (
                "Tolerância Intervalo",
                f"{minutos_almoco} minutos" if ativa_almoco else "Desativada",
            ),
            (
                "Histórico",
                "Pasta padrão" if usar_padrao
                else f"Pasta personalizada: {pasta_personalizada or '—'}",
            ),
        ]

        for indice, (rotulo, valor) in enumerate(linhas):
            ctk.CTkLabel(
                self._frame_resumo_linhas, text=rotulo, anchor="w", width=180,
                font=ctk.CTkFont(weight="bold"),
            ).grid(row=indice, column=0, sticky="w", pady=4)
            ctk.CTkLabel(
                self._frame_resumo_linhas, text=valor, anchor="w",
            ).grid(row=indice, column=1, sticky="w", padx=(15, 0), pady=4)

    def _wizard_concluir(self) -> None:
        """
        Ação do botão "Concluir Configuração" (Etapa 6): valida tudo; se
        houver erro, informa e não avança. Se estiver tudo correto,
        persiste os dados (Cap. 4.9) e segue para a etapa de Conclusão.
        """
        if not self.esta_tudo_valido():
            self._rotulo_erro_resumo.configure(
                text=(
                    "Existem campos inválidos. Volte às etapas anteriores "
                    "e corrija-os antes de concluir."
                )
            )
            return

        self._rotulo_erro_resumo.configure(text="")
        self._salvar_configuracao_inicial()
        self._exibir_etapa_wizard(len(self._wizard_etapas) - 1)

    def _persistir_configuracoes_gerais(self) -> None:
        """
        Persiste Empresa/Logo/Turnos/Tolerâncias/Histórico usando
        exclusivamente os métodos e funções já existentes em config.py
        (Cap. 4.9/12.5) — reaproveitado tanto pela conclusão do Wizard
        quanto pelo modo de edição, sem duplicar a lógica de
        persistência entre os dois. Não decide nada sobre
        primeira_execucao nem sobre navegação; isso é responsabilidade
        de quem chama.
        """
        self.config_app.empresa["nome"] = self.obter_nome_empresa()

        logo_nova = self.obter_logo_selecionada()
        if logo_nova is not None:
            self.config_app.empresa["logo_caminho"] = copiar_logo(logo_nova)
        self.config_app.salvar_empresa()

        self.config_app.configuracoes["turnos"] = [
            turno_para_dict(turno) for turno in self.obter_turnos()
        ]

        ativa_entrada, minutos_entrada = self.obter_tolerancia("entrada")
        self.config_app.configuracoes["tolerancia_entrada"] = {
            "ativa": ativa_entrada, "minutos": minutos_entrada,
        }

        ativa_almoco, minutos_almoco = self.obter_tolerancia("almoco")
        self.config_app.configuracoes["tolerancia_almoco"] = {
            "ativa": ativa_almoco, "minutos": minutos_almoco,
        }

        usar_padrao, pasta_personalizada = self.obter_pasta_historico()
        self.config_app.configuracoes["pasta_historico"] = (
            str(HISTORICO_DIR) if usar_padrao else pasta_personalizada
        )

    def _salvar_configuracao_inicial(self) -> None:
        """
        Ação do botão "Concluir Configuração" do Wizard (Cap. 4.9):
        persiste os dados coletados e marca primeira_execucao como
        concluída (concluir_primeira_execucao() já grava
        configuracoes.json).
        """
        self._persistir_configuracoes_gerais()
        self.config_app.concluir_primeira_execucao()

    # -- Etapa 7: Conclusão ---------------------------------------------------------

    def _montar_etapa_conclusao(self, master) -> ctk.CTkFrame:
        """Etapa 7: confirmação final antes de abrir a Tela Principal."""
        etapa = ctk.CTkFrame(master, fg_color="transparent")
        ctk.CTkLabel(
            etapa, text="✔ Configuração concluída!",
            font=ctk.CTkFont(size=22, weight="bold"),
        ).pack(pady=(60, 10))
        ctk.CTkLabel(
            etapa,
            text="Tudo pronto. Você já pode começar a usar o sistema.",
            font=ctk.CTkFont(size=14),
            text_color=("gray70", "gray70"),
        ).pack()
        return etapa

    def _wizard_ir_para_principal(self) -> None:
        """Encerra o Wizard e abre a Tela Principal (Cap. 4.9)."""
        self.controlador.mostrar_tela("principal")

    # -- Modo de Edição (Cap. 12.5) -----------------------------------------------
    #
    # Reaproveita integralmente os mesmos componentes/validação do Wizard
    # acima — a única diferença é que tudo fica numa única página, já
    # carregada com os valores atuais, e a persistência é explícita
    # (botão "Salvar Alterações"), em vez das etapas sequenciais e do
    # "Concluir Configuração" da primeira execução.

    def _montar_edicao(self) -> None:
        """
        Monta o modo de edição: os mesmos campos do Wizard (Empresa,
        Logo, Turnos, Tolerâncias, Histórico) em uma única página
        rolável, pré-carregados com os valores de `self.config_app`.
        Turnos existentes mantêm seu ID (Cap. 5.13/21.4) porque
        `_montar_lista_turnos` os repassa para `_PainelTurno`, que só
        gera um ID novo quando criado sem Turno (Cap. 4.6).
        """
        corpo = ctk.CTkScrollableFrame(self, fg_color="transparent")
        corpo.grid(row=1, column=0, sticky="nsew", padx=30, pady=(15, 0))

        turnos_existentes = [
            turno_de_dict(dados) for dados in self.config_app.configuracoes.get("turnos", [])
        ]
        tolerancia_entrada = self.config_app.configuracoes.get("tolerancia_entrada", {})
        tolerancia_almoco = self.config_app.configuracoes.get("tolerancia_almoco", {})
        pasta_historico_atual = (
            self.config_app.configuracoes.get("pasta_historico") or str(HISTORICO_DIR)
        )
        usar_padrao_inicial = Path(pasta_historico_atual) == HISTORICO_DIR

        self._montar_campo_empresa(
            corpo, nome_inicial=self.config_app.nome_empresa,
        ).pack(fill="x", pady=(0, 15))
        self._montar_campo_logo(
            corpo, caminho_inicial=self.config_app.empresa.get("logo_caminho") or None,
        ).pack(fill="x", pady=(0, 15))
        self._montar_lista_turnos(corpo, turnos_existentes).pack(fill="both", pady=(0, 15))
        self._montar_bloco_tolerancia(
            corpo, chave="entrada", titulo="Tolerância de Entrada",
            ativa_inicial=bool(tolerancia_entrada.get("ativa", False)),
            minutos_inicial=int(tolerancia_entrada.get("minutos") or 0),
        ).pack(fill="x", pady=(0, 15))
        self._montar_bloco_tolerancia(
            corpo, chave="almoco", titulo="Tolerância do Intervalo",
            ativa_inicial=bool(tolerancia_almoco.get("ativa", False)),
            minutos_inicial=int(tolerancia_almoco.get("minutos") or 0),
        ).pack(fill="x", pady=(0, 15))
        self._montar_bloco_historico(
            corpo, pasta_inicial=pasta_historico_atual, usar_padrao_inicial=usar_padrao_inicial,
        ).pack(fill="x", pady=(0, 15))

        rodape = ctk.CTkFrame(self, fg_color="transparent")
        rodape.grid(row=2, column=0, sticky="ew", padx=30, pady=15)
        rodape.grid_columnconfigure(0, weight=1)

        self._rotulo_status_edicao = ctk.CTkLabel(
            rodape, text="", anchor="w", font=ctk.CTkFont(size=12),
        )
        self._rotulo_status_edicao.grid(row=0, column=0, sticky="w")

        self._botao_salvar_edicao = ctk.CTkButton(
            rodape, text="Salvar Alterações", width=180, command=self._salvar_edicao,
        )
        self._botao_salvar_edicao.grid(row=0, column=1, sticky="e")

        self.ao_validar = self._atualizar_botao_salvar_edicao
        self._atualizar_botao_salvar_edicao()

    def _atualizar_botao_salvar_edicao(self) -> None:
        """Habilita "Salvar Alterações" somente quando todos os campos são válidos."""
        self._botao_salvar_edicao.configure(
            state="normal" if self.esta_tudo_valido() else "disabled"
        )

    def _salvar_edicao(self) -> None:
        """
        Ação do botão "Salvar Alterações" (Cap. 12.5): persiste tudo de
        uma vez, com os mesmos métodos já usados pelo Wizard (Cap. 4.9),
        sem alterar primeira_execucao e sem sair da tela — o usuário
        pode continuar editando ou fechar quando quiser.
        """
        if not self.esta_tudo_valido():
            self._rotulo_status_edicao.configure(
                text="Existem campos inválidos. Corrija-os antes de salvar.",
                text_color=("#c0392b", "#e74c3c"),
            )
            return

        self._persistir_configuracoes_gerais()
        self.config_app.salvar_configuracoes()

        self._rotulo_status_edicao.configure(
            text=f"Alterações salvas às {datetime.now().strftime('%H:%M:%S')}.",
            text_color=("gray60", "gray60"),
        )
        log.info("Configurações atualizadas pelo modo de edição (Cap. 12.5).")
