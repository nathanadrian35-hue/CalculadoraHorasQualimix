"""
config.py
---------
Configurações e persistência local (Cap. 4 / 13 da especificação).

Responsabilidades:
    - Definir os caminhos padrão do projeto (pastas e arquivos JSON).
    - Criar automaticamente toda a estrutura de pastas.
    - Ler/salvar as configurações em arquivos JSON dentro de "dados/".
    - Fazer backup automático antes de sobrescrever qualquer arquivo.

Nenhuma informação de configuração fica gravada no código (Cap. 13.1):
tudo é lido/gravado em JSON. A jornada usada pelo Motor de Cálculo
(Cap. 6) pertence exclusivamente a cada Turno (Cap. 4.6), não existe
mais como configuração global aqui.
"""

from __future__ import annotations

import json
import os
import shutil
import sys
import uuid
from copy import deepcopy
from datetime import datetime, time
from pathlib import Path
from typing import Any

from constantes import EXTENSOES_IMAGEM, VERSAO, StatusFuncionario
from logger import get_logger
from modelos import Funcionario, JornadaDia, Setor, Turno

log = get_logger()


# ---------------------------------------------------------------------------
# Caminhos do projeto
# ---------------------------------------------------------------------------

# Executável empacotado (PyInstaller, Cap. 17): __file__ apontaria para a
# pasta temporária de extração (sys._MEIPASS), recriada do zero e
# descartada a cada execução — os dados do usuário (Cap. 13.1: "tudo
# armazenado localmente") devem ficar ao lado do .exe de verdade, nunca
# nessa pasta temporária.
BASE_DIR: Path = (
    Path(sys.executable).resolve().parent if getattr(sys, "frozen", False)
    else Path(__file__).resolve().parent
)

DADOS_DIR: Path = BASE_DIR / "dados"
ASSETS_DIR: Path = BASE_DIR / "assets"
LOGO_DIR: Path = ASSETS_DIR / "logo"
ICONES_DIR: Path = ASSETS_DIR / "icones"
HISTORICO_DIR: Path = BASE_DIR / "Historico"
LOGS_DIR: Path = BASE_DIR / "Logs"
BACKUP_DIR: Path = BASE_DIR / "backup"
COMPETENCIAS_DIR: Path = DADOS_DIR / "competencias"

# Arquivos JSON
ARQ_EMPRESA: Path = DADOS_DIR / "empresa.json"
ARQ_CONFIGURACOES: Path = DADOS_DIR / "configuracoes.json"
ARQ_FUNCIONARIOS: Path = DADOS_DIR / "funcionarios.json"
ARQ_SETORES: Path = DADOS_DIR / "setores.json"
ARQ_VERSAO: Path = DADOS_DIR / "versao.json"

# Todas as pastas que devem existir para o sistema funcionar
_PASTAS: tuple[Path, ...] = (
    DADOS_DIR,
    ASSETS_DIR,
    LOGO_DIR,
    ICONES_DIR,
    HISTORICO_DIR,
    LOGS_DIR,
    BACKUP_DIR,
    COMPETENCIAS_DIR,
)


# ---------------------------------------------------------------------------
# Valores padrão dos arquivos JSON
# ---------------------------------------------------------------------------

def _padrao_empresa() -> dict[str, Any]:
    return {"nome": "", "logo_caminho": ""}


def _padrao_configuracoes() -> dict[str, Any]:
    return {
        "turnos": [],  # lista de dicts — ver turno_para_dict()/turno_de_dict()
        "tolerancia_entrada": {"ativa": False, "minutos": 0},
        "tolerancia_almoco": {"ativa": False, "minutos": 0},
        "pasta_historico": str(HISTORICO_DIR),
        "tema": "dark",
        "primeira_execucao": True,
    }


def _padrao_funcionarios() -> dict[str, Any]:
    return {"funcionarios": []}


def _padrao_setores() -> dict[str, Any]:
    return {"setores": []}  # lista de dicts — ver setor_para_dict()/setor_de_dict()


def _padrao_versao() -> dict[str, Any]:
    return {"versao": VERSAO, "ultima_atualizacao": ""}


# ---------------------------------------------------------------------------
# Estrutura de pastas
# ---------------------------------------------------------------------------

def garantir_estrutura() -> None:
    """Cria automaticamente todas as pastas necessárias (idempotente)."""
    for pasta in _PASTAS:
        pasta.mkdir(parents=True, exist_ok=True)
    log.info("Estrutura de pastas verificada/criada.")


# ---------------------------------------------------------------------------
# Logo da empresa (Cap. 4.3)
# ---------------------------------------------------------------------------

def copiar_logo(origem: Path) -> str:
    """
    Copia a imagem de logo escolhida pelo usuário para assets/logo/,
    nunca utilizando o arquivo original (Cap. 4.3). Substitui qualquer
    logo anterior.

    Retorna o caminho relativo ao projeto, para ser salvo em
    empresa["logo_caminho"].

    Levanta ValueError se a extensão do arquivo não for suportada.
    """
    extensao = origem.suffix.lower()
    if extensao not in EXTENSOES_IMAGEM:
        raise ValueError(f"Formato de imagem não suportado: {extensao or '(sem extensão)'}")

    LOGO_DIR.mkdir(parents=True, exist_ok=True)

    for logo_antiga in LOGO_DIR.glob("logo.*"):
        logo_antiga.unlink(missing_ok=True)

    destino = LOGO_DIR / f"logo{extensao}"
    shutil.copy2(origem, destino)
    log.info("Logo copiada para: %s", destino.name)

    return str(destino.relative_to(BASE_DIR))


# ---------------------------------------------------------------------------
# Conversão de horários (usado na serialização de Turno)
# ---------------------------------------------------------------------------

def _time_para_texto(horario: time | None) -> str | None:
    """Converte um datetime.time em texto "HH:MM", ou None."""
    return horario.strftime("%H:%M") if horario is not None else None


def _texto_para_time(texto: str | None) -> time | None:
    """Converte um texto "HH:MM" em datetime.time. Retorna None se inválido/vazio."""
    if not texto:
        return None
    try:
        return datetime.strptime(texto, "%H:%M").time()
    except ValueError:
        return None


# ---------------------------------------------------------------------------
# Serialização de Turno (Cap. 4.6 / 13.3)
# ---------------------------------------------------------------------------

def _jornada_para_dict(jornada: JornadaDia | None) -> dict[str, Any] | None:
    """Converte uma JornadaDia em um dict serializável em JSON, ou None."""
    if jornada is None:
        return None
    return {
        "entrada": _time_para_texto(jornada.entrada),
        "saida": _time_para_texto(jornada.saida),
        "inicio_intervalo": _time_para_texto(jornada.inicio_intervalo),
        "fim_intervalo": _time_para_texto(jornada.fim_intervalo),
    }


def _jornada_de_dict(dados: dict[str, Any] | None) -> JornadaDia | None:
    """Reconstrói uma JornadaDia a partir do dict lido do JSON, ou None."""
    if not dados:
        return None
    return JornadaDia(
        entrada=_texto_para_time(dados.get("entrada")),
        saida=_texto_para_time(dados.get("saida")),
        inicio_intervalo=_texto_para_time(dados.get("inicio_intervalo")),
        fim_intervalo=_texto_para_time(dados.get("fim_intervalo")),
    )


def turno_para_dict(turno: Turno) -> dict[str, Any]:
    """Converte um Turno em um dict serializável em JSON (Cap. 4.6)."""
    return {
        "id": turno.id,
        "nome": turno.nome,
        "segunda_a_sexta": _jornada_para_dict(turno.segunda_a_sexta),
        "sabado": _jornada_para_dict(turno.sabado),
        "domingo": _jornada_para_dict(turno.domingo),
    }


def turno_de_dict(dados: dict[str, Any]) -> Turno:
    """
    Reconstrói um Turno a partir do dict lido do JSON, já na estrutura
    atual (jornada por tipo de dia, Cap. 4.6) — turnos no formato
    antigo (Sprint 2/3) são convertidos por `_migrar_estrutura_turnos()`
    antes de chegar aqui, uma única vez ao carregar as configurações.

    Tolerante a turnos cadastrados antes do Sprint 3 (sem "id" salvo):
    nesse caso um novo id é gerado aqui, mas para permanecer estável
    entre execuções ele precisa ser persistido — ver
    `_migrar_ids_turnos()`, chamado no mesmo momento.
    """
    campos: dict[str, Any] = {
        "nome": dados.get("nome", ""),
        "segunda_a_sexta": _jornada_de_dict(dados.get("segunda_a_sexta")) or JornadaDia(),
        "sabado": _jornada_de_dict(dados.get("sabado")),
        "domingo": _jornada_de_dict(dados.get("domingo")),
    }
    id_existente = dados.get("id")
    if id_existente:
        campos["id"] = id_existente

    return Turno(**campos)


def _migrar_ids_turnos(configuracoes: dict[str, Any]) -> bool:
    """
    Garante que todo turno em configuracoes["turnos"] tenha um "id"
    estável (Cap. 4.6/5.13). Turnos cadastrados antes do Sprint 3 não
    tinham esse campo; aqui cada um recebe um id novo, uma única vez.
    Retorna True se algum id foi atribuído (o chamador deve persistir).
    """
    algum_gerado = False
    for dados_turno in configuracoes.get("turnos", []):
        if not dados_turno.get("id"):
            dados_turno["id"] = str(uuid.uuid4())
            algum_gerado = True
    return algum_gerado


def _turno_tem_estrutura_antiga(dados_turno: dict[str, Any]) -> bool:
    """
    Um turno está no formato anterior (Sprint 2/3: um único horário no
    nível raiz + trabalha_sabado/trabalha_domingo booleanos) se não
    tiver a chave "segunda_a_sexta" introduzida no Cap. 4.6.
    """
    return "segunda_a_sexta" not in dados_turno


def _migrar_estrutura_turnos(configuracoes: dict[str, Any]) -> bool:
    """
    Converte turnos no formato antigo (Sprint 2/3: um único horário +
    trabalha_sabado/trabalha_domingo booleanos) para o formato com
    jornada independente por tipo de dia (Cap. 4.6/6.4/6.5), uma única
    vez, sem perda de dados:

    - O horário existente vira a jornada de "segunda_a_sexta".
    - "trabalha_sabado"/"trabalha_domingo" viravam uma jornada de
      Sábado/Domingo ativa, porém sem horário ainda (o usuário
      preenche na próxima edição), quando eram True; ou None (turno
      não trabalha naquele dia) quando eram False.

    Retorna True se algum turno foi convertido (o chamador deve
    persistir).
    """
    algum_migrado = False
    for dados_turno in configuracoes.get("turnos", []):
        if not _turno_tem_estrutura_antiga(dados_turno):
            continue

        dados_turno["segunda_a_sexta"] = {
            "entrada": dados_turno.pop("entrada", None),
            "saida": dados_turno.pop("saida", None),
            "inicio_intervalo": dados_turno.pop("inicio_intervalo", None),
            "fim_intervalo": dados_turno.pop("fim_intervalo", None),
        }

        jornada_vazia = {
            "entrada": None, "saida": None, "inicio_intervalo": None, "fim_intervalo": None,
        }
        dados_turno["sabado"] = (
            dict(jornada_vazia) if dados_turno.pop("trabalha_sabado", False) else None
        )
        dados_turno["domingo"] = (
            dict(jornada_vazia) if dados_turno.pop("trabalha_domingo", False) else None
        )
        algum_migrado = True

    return algum_migrado


# ---------------------------------------------------------------------------
# Serialização de Setor (Cap. 21)
# ---------------------------------------------------------------------------

def setor_para_dict(setor: Setor) -> dict[str, Any]:
    """Converte um Setor em um dict serializável em JSON."""
    return {
        "id": setor.id,
        "nome": setor.nome,
        "cor": setor.cor,
        "status": setor.status.value,
    }


def setor_de_dict(dados: dict[str, Any]) -> Setor:
    """
    Reconstrói um Setor a partir do dict lido do JSON. Tolerante a dados
    incompletos/corrompidos: sem "id" válido, um novo é gerado (via o
    próprio default de Setor); status desconhecido cai para Ativo.
    """
    try:
        status = StatusFuncionario(dados.get("status", StatusFuncionario.ATIVO.value))
    except ValueError:
        status = StatusFuncionario.ATIVO

    campos: dict[str, Any] = {
        "nome": dados.get("nome", ""),
        "cor": dados.get("cor", ""),
        "status": status,
    }
    id_existente = dados.get("id")
    if id_existente:
        campos["id"] = id_existente

    return Setor(**campos)


# ---------------------------------------------------------------------------
# Serialização de Funcionário (Cap. 5.14)
# ---------------------------------------------------------------------------

def funcionario_para_dict(funcionario: Funcionario) -> dict[str, Any]:
    """Converte um Funcionario em um dict serializável em JSON."""
    return {
        "id": funcionario.id,
        "nome_completo": funcionario.nome_completo,
        "nome_planilha": funcionario.nome_planilha,
        "id_planilha": funcionario.id_planilha,
        "apelido": funcionario.apelido,
        "matricula": funcionario.matricula,
        "cpf": funcionario.cpf,
        "cargo": funcionario.cargo,
        "turno_id": funcionario.turno_id,
        "setor_id": funcionario.setor_id,
        "status": funcionario.status.value,
        "data_cadastro": funcionario.data_cadastro,
        "ultima_atualizacao": funcionario.ultima_atualizacao,
    }


def funcionario_de_dict(dados: dict[str, Any]) -> Funcionario:
    """
    Reconstrói um Funcionario a partir do dict lido do JSON. Tolerante a
    dados incompletos/corrompidos: sem "id" válido, um novo é gerado
    (via o próprio default de Funcionario); status desconhecido cai
    para Ativo; sem "id_planilha" (cadastros anteriores à Sprint de
    Competências), cai para "" — a migração para IDUsuário é just-in-time,
    na próxima importação em que o funcionário reaparecer (Cap. 5.8).
    """
    try:
        status = StatusFuncionario(dados.get("status", StatusFuncionario.ATIVO.value))
    except ValueError:
        status = StatusFuncionario.ATIVO

    campos: dict[str, Any] = {
        "nome_completo": dados.get("nome_completo", ""),
        "nome_planilha": dados.get("nome_planilha", ""),
        "id_planilha": dados.get("id_planilha", ""),
        "apelido": dados.get("apelido", ""),
        "matricula": dados.get("matricula", ""),
        "cpf": dados.get("cpf", ""),
        "cargo": dados.get("cargo", ""),
        "turno_id": dados.get("turno_id", ""),
        "setor_id": dados.get("setor_id", ""),
        "status": status,
        "data_cadastro": dados.get("data_cadastro", ""),
        "ultima_atualizacao": dados.get("ultima_atualizacao", ""),
    }
    id_existente = dados.get("id")
    if id_existente:
        campos["id"] = id_existente

    return Funcionario(**campos)


# ---------------------------------------------------------------------------
# Pasta do Histórico (Cap. 4.1 / 12.5)
# ---------------------------------------------------------------------------

def pasta_historico_valida(caminho: Path) -> bool:
    """
    Verifica se a pasta informada é um diretório existente e gravável,
    apto a ser usado como pasta do histórico. Não cria a pasta — apenas
    valida (a criação, se necessária, é responsabilidade de quem chama).
    """
    return caminho.is_dir() and os.access(caminho, os.W_OK)


# ---------------------------------------------------------------------------
# Leitura/escrita de JSON com backup
# ---------------------------------------------------------------------------

def ler_json(caminho: Path, padrao: dict[str, Any]) -> dict[str, Any]:
    """
    Wrapper público de `_ler_json`, para reaproveitamento por outros módulos
    (ex.: `competencias.py`) sem duplicar a lógica de backup/merge aqui
    centralizada.
    """
    return _ler_json(caminho, padrao)


def escrever_json(caminho: Path, dados: dict[str, Any], com_backup: bool = True) -> None:
    """Wrapper público de `_escrever_json` — mesmo motivo de `ler_json` acima."""
    _escrever_json(caminho, dados, com_backup=com_backup)


def _ler_json(caminho: Path, padrao: dict[str, Any]) -> dict[str, Any]:
    """
    Lê um JSON. Se o arquivo não existir, cria-o com os valores padrão.
    Se estiver corrompido, faz backup do arquivo e recria com o padrão.
    """
    if not caminho.exists():
        _escrever_json(caminho, padrao, com_backup=False)
        log.info("Arquivo criado com valores padrão: %s", caminho.name)
        return deepcopy(padrao)

    try:
        with caminho.open("r", encoding="utf-8") as arquivo:
            dados = json.load(arquivo)
        if not isinstance(dados, dict):
            raise ValueError(f"Conteúdo de {caminho.name} não é um objeto JSON.")
        # Completa chaves ausentes com o padrão (evita quebra ao evoluir o schema)
        return _mesclar_padrao(padrao, dados)
    except (json.JSONDecodeError, OSError, ValueError) as erro:
        log.error("Falha ao ler %s (%s). Recriando com padrão.", caminho.name, erro)
        _fazer_backup(caminho)
        _escrever_json(caminho, padrao, com_backup=False)
        return deepcopy(padrao)


def _escrever_json(caminho: Path, dados: dict[str, Any], com_backup: bool = True) -> None:
    """Grava um JSON de forma legível (UTF-8), com backup opcional prévio."""
    if com_backup and caminho.exists():
        _fazer_backup(caminho)

    caminho.parent.mkdir(parents=True, exist_ok=True)
    with caminho.open("w", encoding="utf-8") as arquivo:
        json.dump(dados, arquivo, ensure_ascii=False, indent=4)


def _fazer_backup(caminho: Path) -> None:
    """Copia o arquivo atual para backup/ com carimbo de data/hora."""
    try:
        BACKUP_DIR.mkdir(parents=True, exist_ok=True)
        carimbo = datetime.now().strftime("%Y%m%d_%H%M%S")
        destino = BACKUP_DIR / f"{caminho.stem}_{carimbo}{caminho.suffix}"
        shutil.copy2(caminho, destino)
        log.info("Backup criado: %s", destino.name)
    except OSError as erro:
        log.error("Não foi possível fazer backup de %s: %s", caminho.name, erro)


def _mesclar_padrao(padrao: dict[str, Any], dados: dict[str, Any]) -> dict[str, Any]:
    """Retorna 'dados' garantindo que todas as chaves de 'padrao' existam."""
    resultado = deepcopy(padrao)
    for chave, valor in dados.items():
        if isinstance(valor, dict) and isinstance(resultado.get(chave), dict):
            resultado[chave] = _mesclar_padrao(resultado[chave], valor)
        else:
            resultado[chave] = valor
    return resultado


# ---------------------------------------------------------------------------
# Gerenciador de configuração
# ---------------------------------------------------------------------------

class Config:
    """
    Ponto único de acesso às configurações persistidas.

    Instanciado uma vez em main.py e repassado às telas (injeção de
    dependência), evitando estado global espalhado. Cada 'salvar_*' grava
    o respectivo JSON, fazendo backup automático do arquivo anterior.
    """

    def __init__(self) -> None:
        self.empresa: dict[str, Any] = {}
        self.configuracoes: dict[str, Any] = {}
        self.funcionarios: dict[str, Any] = {}
        self.setores: dict[str, Any] = {}
        self.versao: dict[str, Any] = {}
        self.carregar_tudo()

    # -- Carregamento --------------------------------------------------------

    def carregar_tudo(self) -> None:
        """Carrega (ou cria) todos os arquivos JSON de configuração."""
        self.empresa = _ler_json(ARQ_EMPRESA, _padrao_empresa())
        self.configuracoes = _ler_json(ARQ_CONFIGURACOES, _padrao_configuracoes())
        self.funcionarios = _ler_json(ARQ_FUNCIONARIOS, _padrao_funcionarios())
        self.setores = _ler_json(ARQ_SETORES, _padrao_setores())
        self.versao = _ler_json(ARQ_VERSAO, _padrao_versao())

        # Mantém a versão do sistema sempre atualizada no arquivo
        if self.versao.get("versao") != VERSAO:
            self.versao["versao"] = VERSAO
            self.salvar_versao()

        # Migração única: turnos cadastrados antes do Sprint 3 não tinham
        # "id" — atribui um id estável e persiste, para o vínculo por ID
        # (Cap. 5.13) funcionar com turnos já existentes.
        if _migrar_ids_turnos(self.configuracoes):
            self.salvar_configuracoes()
            log.info("IDs de turnos legados migrados e salvos.")

        # Migração única: turnos cadastrados antes desta melhoria tinham um
        # único horário + trabalha_sabado/trabalha_domingo booleanos —
        # converte para jornada independente por tipo de dia (Cap. 4.6).
        if _migrar_estrutura_turnos(self.configuracoes):
            self.salvar_configuracoes()
            log.info("Estrutura de jornada por tipo de dia migrada e salva (Cap. 4.6).")

    # -- Salvamento ----------------------------------------------------------

    def salvar_empresa(self) -> None:
        _escrever_json(ARQ_EMPRESA, self.empresa)
        log.info("Configuração da empresa salva.")

    def salvar_configuracoes(self) -> None:
        _escrever_json(ARQ_CONFIGURACOES, self.configuracoes)
        log.info("Configurações gerais salvas.")

    def salvar_funcionarios(self) -> None:
        _escrever_json(ARQ_FUNCIONARIOS, self.funcionarios)
        log.info("Cadastro de funcionários salvo.")

    def salvar_setores(self) -> None:
        _escrever_json(ARQ_SETORES, self.setores)
        log.info("Cadastro de setores salvo.")

    def salvar_versao(self) -> None:
        self.versao["ultima_atualizacao"] = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
        _escrever_json(ARQ_VERSAO, self.versao)

    # -- Conveniências -------------------------------------------------------

    @property
    def primeira_execucao(self) -> bool:
        """True enquanto a configuração inicial guiada não foi concluída."""
        return bool(self.configuracoes.get("primeira_execucao", True))

    def concluir_primeira_execucao(self) -> None:
        self.configuracoes["primeira_execucao"] = False
        self.salvar_configuracoes()

    @property
    def nome_empresa(self) -> str:
        return self.empresa.get("nome", "") or ""

    @property
    def tema(self) -> str:
        return self.configuracoes.get("tema", "dark") or "dark"
