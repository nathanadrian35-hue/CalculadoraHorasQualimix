"""
qualiassist.py
----------------
Motor do QualiAssist (v2.1 Sprint 3, Documento 3 Cap. 1-36) —
assistente inteligente offline.

Responsabilidade única: carregar/pesquisar a base de conhecimento,
manter histórico e favoritos, e sugerir ajuda contextual (por tela) ou
por mensagem de erro reconhecida. Nunca altera dados do sistema (Cap.
4): não grava em `funcionarios.json`/`configuracoes.json`/
competências, só nos seus dois próprios arquivos
(`qualiassist_base.json`, `qualiassist_historico.json`).

Busca tolerante (Cap. 9/33): ignora maiúsculas/minúsculas e acentos
(reaproveita `modelos.normalizar_texto`, já usado pela pesquisa da
Sprint 1 — nenhuma lógica de normalização nova), plural/singular
simples e um mapa de sinônimos por categoria — sem nenhuma biblioteca
de NLP (mantém o sistema leve e 100% offline, Cap. 2).
"""

from __future__ import annotations

import re
from datetime import datetime

from config import escrever_json, ler_json
from constantes import CategoriaQualiAssist
from logger import get_logger
from modelos import (
    ArtigoQualiAssist,
    BaseQualiAssist,
    RegistroHistoricoQualiAssist,
    normalizar_texto,
)

log = get_logger()

_MAXIMO_HISTORICO = 200
_MAXIMO_RELACIONADOS = 4


def _caminho_base():
    from config import DADOS_DIR
    return DADOS_DIR / "qualiassist_base.json"


def _caminho_historico():
    from config import DADOS_DIR
    return DADOS_DIR / "qualiassist_historico.json"


# ---------------------------------------------------------------------------
# Sinônimos e tela → categoria (Cap. 8/9/26/33)
# ---------------------------------------------------------------------------

_SINONIMOS: dict[str, set[str]] = {
    "importar": {"importacao", "planilha", "arquivo", "excel", "xls", "sincronizacao"},
    "planilha": {"importacao", "arquivo", "excel"},
    "excel": {"exportacao", "planilha"},
    "he": {"horas extras", "extra"},
    "extra": {"horas extras"},
    "saldo": {"banco de horas"},
    "banco": {"banco de horas"},
    "falta": {"absenteismo", "ausencia", "justificativa"},
    "ausencia": {"absenteismo", "falta"},
    "atraso": {"hora negativa", "absenteismo"},
    "corrigir": {"correcoes", "batida", "pendencia"},
    "batida": {"correcoes", "pendencia"},
    "pendencia": {"correcoes", "batida"},
    "turno": {"jornada", "horario"},
    "horario": {"jornada", "turno"},
    "setor": {"funcionarios", "departamento"},
    "departamento": {"setor", "funcionarios"},
    "grafico": {"dashboard", "indicadores"},
    "indicador": {"dashboard", "absenteismo"},
    "erro": {"problema", "falha"},
    "imprimir": {"exportacao", "impressao"},
    "csv": {"exportacao"},
    "pdf": {"exportacao"},
}

# Tela (chave usada em `interface.App._telas`) → categoria sugerida (Cap. 8).
_TELA_PARA_CATEGORIA: dict[str, CategoriaQualiAssist] = {
    "principal": CategoriaQualiAssist.IMPORTACAO,
    "funcionarios": CategoriaQualiAssist.FUNCIONARIOS,
    "setores": CategoriaQualiAssist.FUNCIONARIOS,
    "configuracoes": CategoriaQualiAssist.JORNADAS,
    "pendencias": CategoriaQualiAssist.CORRECOES,
    "competencias": CategoriaQualiAssist.COMPETENCIAS,
    "dashboard": CategoriaQualiAssist.DASHBOARD,
    "absenteismo": CategoriaQualiAssist.ABSENTEISMO,
    "absenteismo_config": CategoriaQualiAssist.ABSENTEISMO,
    "relatorios": CategoriaQualiAssist.RELATORIOS,
    "historico": CategoriaQualiAssist.EXPORTACOES,
    "qualiassist_admin": CategoriaQualiAssist.QUALIASSIST,
}


def categoria_da_tela(nome_tela: str) -> CategoriaQualiAssist | None:
    """Ajuda contextual (Cap. 8/26): sugere a categoria pela tela atualmente visível."""
    return _TELA_PARA_CATEGORIA.get(nome_tela)


# ---------------------------------------------------------------------------
# Erros conhecidos (Cap. 25) — reconhecimento por palavras da mensagem, não
# por trecho exato (as mensagens reais do sistema têm texto entre as
# palavras-chave, ex.: "arquivo... não está aberto...") — todas as palavras
# do gatilho precisam aparecer na mensagem, em qualquer ordem.
# ---------------------------------------------------------------------------

_ERROS_CONHECIDOS: list[tuple[frozenset[str], str]] = [
    (frozenset({"arquivo", "aberto"}), "excel"),
    (frozenset({"nao", "possivel", "abrir"}), "excel"),
    (frozenset({"nao", "possivel", "exportar"}), "excel"),
    (frozenset({"nao", "possivel", "imprimir"}), "impressao"),
    (frozenset({"turno", "nao", "definido"}), "turno nao definido"),
    (frozenset({"competencia", "existe"}), "competencia ja existe"),
    (frozenset({"esta", "fechada", "reabri"}), "competencia fechada"),
    (frozenset({"pendencia", "aberto"}), "pendencias em aberto"),
    (frozenset({"formato", "invalido"}), "formato de planilha invalido"),
    (frozenset({"campos", "invalidos"}), "campos invalidos wizard"),
]


def sugerir_por_erro(mensagem_erro: str) -> str | None:
    """
    Erros inteligentes (Cap. 25): reconhece uma mensagem de erro já
    conhecida (todas as palavras do gatilho presentes, em qualquer
    ordem) e devolve o termo de busca correspondente na base — a tela
    chamadora decide o que fazer com isso (ex.: já abrir o QualiAssist
    com essa pesquisa pronta). Não intercepta automaticamente todo
    `messagebox.showerror` do sistema (mudaria dezenas de pontos e
    arriscaria regressão) — é uma capacidade que qualquer tela pode
    chamar deliberadamente.
    """
    palavras = set(re.findall(r"\w+", normalizar_texto(mensagem_erro)))
    for gatilho, termo_busca in _ERROS_CONHECIDOS:
        if gatilho <= palavras:
            return termo_busca
    return None


# ---------------------------------------------------------------------------
# Persistência da base (Cap. 10/29)
# ---------------------------------------------------------------------------

def artigo_para_dict(artigo: ArtigoQualiAssist) -> dict:
    return {
        "id": artigo.id, "titulo": artigo.titulo, "categoria": artigo.categoria.value,
        "resposta": artigo.resposta, "palavras_chave": artigo.palavras_chave,
        "perguntas": artigo.perguntas, "links_internos": artigo.links_internos,
        "relacionados": artigo.relacionados, "atualizado_em": artigo.atualizado_em,
        "ativo": artigo.ativo,
    }


def artigo_de_dict(dados: dict) -> ArtigoQualiAssist | None:
    try:
        categoria = CategoriaQualiAssist(dados.get("categoria", ""))
    except ValueError:
        return None
    return ArtigoQualiAssist(
        id=dados.get("id") or "", titulo=dados.get("titulo", ""), categoria=categoria,
        resposta=dados.get("resposta", ""),
        palavras_chave=list(dados.get("palavras_chave", [])),
        perguntas=list(dados.get("perguntas", [])),
        links_internos=list(dados.get("links_internos", [])),
        relacionados=list(dados.get("relacionados", [])),
        atualizado_em=dados.get("atualizado_em", ""),
        ativo=bool(dados.get("ativo", True)),
    )


def _padrao_base_dict() -> dict:
    from qualiassist_base_inicial import artigos_iniciais

    agora = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
    artigos = artigos_iniciais()
    for artigo in artigos:
        artigo.atualizado_em = agora
    return {
        "artigos": [artigo_para_dict(a) for a in artigos],
        "versao": 1,
        "atualizado_em": agora,
    }


def carregar_base() -> BaseQualiAssist:
    """Carrega a base de conhecimento, criando-a com o conteúdo inicial na primeira execução."""
    dados = ler_json(_caminho_base(), _padrao_base_dict())
    artigos = [a for a in (artigo_de_dict(item) for item in dados.get("artigos", [])) if a]
    return BaseQualiAssist(
        artigos=artigos, versao=int(dados.get("versao", 1)),
        atualizado_em=dados.get("atualizado_em", ""),
    )


def salvar_base(base: BaseQualiAssist) -> None:
    """Persiste a base incrementando a versão (Cap. 29) — sempre com backup automático."""
    base.versao += 1
    base.atualizado_em = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
    dados = {
        "artigos": [artigo_para_dict(a) for a in base.artigos],
        "versao": base.versao,
        "atualizado_em": base.atualizado_em,
    }
    escrever_json(_caminho_base(), dados, com_backup=True)
    log.info("Base do QualiAssist salva (versão %d, %d artigo(s)).", base.versao, len(base.artigos))


# ---------------------------------------------------------------------------
# Busca tolerante (Cap. 9/33)
# ---------------------------------------------------------------------------

def _expandir_termos(consulta: str) -> set[str]:
    normalizado = normalizar_texto(consulta)
    tokens = re.findall(r"\w+", normalizado)
    termos: set[str] = set(tokens)
    # plural/singular simples (Cap. 9): "relatorios" também casa com "relatorio"
    termos |= {t[:-1] for t in tokens if len(t) > 3 and t.endswith("s")}
    for token in list(termos):
        termos |= _SINONIMOS.get(token, set())
    return termos


def _pontuar(artigo: ArtigoQualiAssist, termos: set[str]) -> int:
    pontos = 0
    titulo_normalizado = normalizar_texto(artigo.titulo)
    if any(termo in titulo_normalizado for termo in termos):
        pontos += 5
    for palavra_chave in artigo.palavras_chave:
        palavra_normalizada = normalizar_texto(palavra_chave)
        if any(termo in palavra_normalizada or palavra_normalizada in termo for termo in termos):
            pontos += 3
    for pergunta in artigo.perguntas:
        pergunta_normalizada = normalizar_texto(pergunta)
        if any(termo in pergunta_normalizada for termo in termos):
            pontos += 2
    resposta_normalizada = normalizar_texto(artigo.resposta)
    if any(termo in resposta_normalizada for termo in termos):
        pontos += 1
    return pontos


def buscar(
    base: BaseQualiAssist, consulta: str, categoria: CategoriaQualiAssist | None = None,
) -> list[ArtigoQualiAssist]:
    """
    Pesquisa avançada (Cap. 33): por título, categoria, pergunta,
    palavra-chave, sinônimo e resposta — ordenada por relevância
    (título > palavra-chave > pergunta > resposta). `consulta` vazia
    devolve todos os artigos ativos da categoria (ou de todas).
    """
    candidatos = [
        artigo for artigo in base.artigos
        if artigo.ativo and (categoria is None or artigo.categoria == categoria)
    ]
    if not consulta.strip():
        return candidatos

    termos = _expandir_termos(consulta)
    pontuados = [(_pontuar(artigo, termos), artigo) for artigo in candidatos]
    pontuados = [(pontos, artigo) for pontos, artigo in pontuados if pontos > 0]
    pontuados.sort(key=lambda par: par[0], reverse=True)
    return [artigo for _, artigo in pontuados]


def respostas_relacionadas(
    base: BaseQualiAssist, artigo: ArtigoQualiAssist,
) -> list[ArtigoQualiAssist]:
    """"Talvez você também queira saber" (Cap. 34) — pelos ids declarados no artigo."""
    por_id = {a.id: a for a in base.artigos if a.ativo}
    return [por_id[id_] for id_ in artigo.relacionados if id_ in por_id][:_MAXIMO_RELACIONADOS]


# ---------------------------------------------------------------------------
# Histórico e favoritos (Cap. 15/16/27)
# ---------------------------------------------------------------------------

def _registro_para_dict(registro: RegistroHistoricoQualiAssist) -> dict:
    return {
        "pergunta": registro.pergunta, "quando": registro.quando, "tela": registro.tela,
        "artigo_id": registro.artigo_id, "favorito": registro.favorito,
    }


def _registro_de_dict(dados: dict) -> RegistroHistoricoQualiAssist:
    return RegistroHistoricoQualiAssist(
        pergunta=dados.get("pergunta", ""), quando=dados.get("quando", ""),
        tela=dados.get("tela", ""), artigo_id=dados.get("artigo_id"),
        favorito=bool(dados.get("favorito", False)),
    )


def carregar_historico() -> list[RegistroHistoricoQualiAssist]:
    dados = ler_json(_caminho_historico(), {"registros": []})
    return [_registro_de_dict(item) for item in dados.get("registros", [])]


def salvar_historico(historico: list[RegistroHistoricoQualiAssist]) -> None:
    """Persiste o histórico, mantendo os favoritos mesmo além do limite de tamanho."""
    favoritos = [r for r in historico if r.favorito]
    recentes = historico[-_MAXIMO_HISTORICO:]
    combinados = favoritos + [r for r in recentes if not r.favorito]
    dados = {"registros": [_registro_para_dict(r) for r in combinados]}
    escrever_json(_caminho_historico(), dados, com_backup=False)


def registrar_pergunta(
    historico: list[RegistroHistoricoQualiAssist], pergunta: str, tela: str,
    artigo: ArtigoQualiAssist | None,
) -> RegistroHistoricoQualiAssist:
    """Registra uma pergunta feita (Cap. 15/27) e devolve o registro criado, já salvo."""
    registro = RegistroHistoricoQualiAssist(
        pergunta=pergunta, quando=datetime.now().strftime("%d/%m/%Y %H:%M:%S"),
        tela=tela, artigo_id=artigo.id if artigo is not None else None,
    )
    historico.append(registro)
    salvar_historico(historico)
    return registro


def alternar_favorito(
    historico: list[RegistroHistoricoQualiAssist], registro: RegistroHistoricoQualiAssist,
) -> None:
    """Favoritar/desfavoritar (Cap. 16) — persiste imediatamente."""
    registro.favorito = not registro.favorito
    salvar_historico(historico)


def limpar_historico(
    historico: list[RegistroHistoricoQualiAssist],
) -> list[RegistroHistoricoQualiAssist]:
    """Limpa o histórico (Cap. 5), preservando os favoritos."""
    restantes = [r for r in historico if r.favorito]
    salvar_historico(restantes)
    return restantes
