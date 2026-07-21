"""
qualiassist_base_inicial.py
------------------------------
Conteúdo inicial da base de conhecimento do QualiAssist (v2.1 Sprint
3) — só usado por `qualiassist._padrao_base_dict()` na primeira
execução (nunca lido depois disso; a partir daí a base vem sempre do
JSON persistido, editável pelo painel administrativo, Cap. 28).

Cada artigo reflete exatamente o que o sistema já faz — nenhuma
funcionalidade é inventada aqui; é só documentação do que já existe,
escrita para responder às perguntas frequentes da especificação
(Cap. 12).
"""

from __future__ import annotations

from constantes import CategoriaQualiAssist
from modelos import ArtigoQualiAssist

_C = CategoriaQualiAssist


def artigos_iniciais() -> list[ArtigoQualiAssist]:
    return [
        ArtigoQualiAssist(
            id="imp-01", titulo="Como importar uma planilha",
            categoria=_C.IMPORTACAO,
            palavras_chave=["importar", "importação", "planilha", "arquivo", "xls"],
            perguntas=["Como importar uma planilha?", "Como faço para importar o ponto?"],
            resposta=(
                "1. Na Tela Inicial, clique em \"Selecionar Planilha\" e escolha o "
                "arquivo .xls/.xlsx exportado pelo relógio de ponto.\n"
                "2. Clique em \"Processar\".\n"
                "3. Se a planilha trouxer um \"Dep.\" sem Setor cadastrado, revise "
                "os setores novos antes de continuar.\n"
                "4. Revise o Painel de Funcionários identificados (turno/setor "
                "sugeridos) e confirme.\n"
                "5. O Motor de Cálculo processa o lote e abre a Tela de Pendências, "
                "se houver alguma.\n"
                "6. Sem pendência em aberto, o sistema já vai direto para Relatórios."
            ),
            links_internos=["principal", "funcionarios"], relacionados=["imp-02", "corr-01"],
        ),
        ArtigoQualiAssist(
            id="imp-02", titulo="Importação semanal incremental",
            categoria=_C.IMPORTACAO,
            palavras_chave=["semanal", "sincronização", "reimportar", "incremental"],
            perguntas=[
                "Posso importar a planilha toda semana?",
                "O que acontece se eu importar a mesma competência de novo?",
            ],
            resposta=(
                "Sim. A planilha do RH normalmente traz o layout do mês inteiro, mas "
                "só os dias já ocorridos vêm preenchidos. Reimportar um mês já "
                "existente nunca substitui nada: cada dia é comparado individualmente "
                "— dias iguais não são tocados, dias novos são adicionados, dias "
                "diferentes são atualizados. Um dia já corrigido manualmente ou com "
                "pendência resolvida nunca é sobrescrito por uma nova importação."
            ),
            links_internos=["principal", "competencias"], relacionados=["comp-01"],
        ),
        ArtigoQualiAssist(
            id="func-01", titulo="Como cadastrar um funcionário",
            categoria=_C.FUNCIONARIOS,
            palavras_chave=["cadastrar", "funcionário", "novo funcionário", "adicionar"],
            perguntas=["Como cadastrar um funcionário?", "Como adiciono um novo colaborador?"],
            resposta=(
                "1. Abra a tela \"Funcionários\".\n"
                "2. Clique em \"+ Adicionar Funcionário\".\n"
                "3. Preencha nome completo (obrigatório), matrícula, cargo, turno e "
                "setor.\n"
                "4. Clique em Salvar.\n\n"
                "A forma mais comum de cadastro, porém, é automática: ao importar a "
                "planilha, o sistema já sugere turno e setor para cada nome "
                "encontrado."
            ),
            links_internos=["funcionarios"], relacionados=["func-02"],
        ),
        ArtigoQualiAssist(
            id="func-02", titulo="Pesquisa, ordenação e ações em massa",
            categoria=_C.FUNCIONARIOS,
            palavras_chave=["pesquisar", "ordenar", "filtro", "massa", "selecionar vários"],
            perguntas=[
                "Como pesquiso um funcionário?", "Como aplico turno para vários de uma vez?"],
            resposta=(
                "Digite no campo de pesquisa para filtrar em tempo real (ignora "
                "acento e maiúsculas). Clique no cabeçalho de qualquer coluna para "
                "ordenar. Marque o checkbox de vários funcionários para liberar a "
                "barra de ações em massa (Turno, Setor, Cargo, Ativar, Inativar)."
            ),
            links_internos=["funcionarios"], relacionados=["func-01"],
        ),
        ArtigoQualiAssist(
            id="jor-01", titulo="Como criar um turno",
            categoria=_C.JORNADAS,
            palavras_chave=["turno", "jornada", "horário", "criar turno"],
            perguntas=["Como cadastro um turno?", "Como defino o horário de um turno?"],
            resposta=(
                "Na tela Configurações, seção Turnos, defina o horário de Segunda a "
                "Sexta (obrigatório) e, se aplicável, Sábado e Domingo (opcionais). "
                "O intervalo de almoço também é opcional — sem ele, o sistema não "
                "descontará nenhum intervalo da jornada."
            ),
            links_internos=["configuracoes"], relacionados=["jor-02"],
        ),
        ArtigoQualiAssist(
            id="jor-02", titulo="Tolerâncias de jornada",
            categoria=_C.JORNADAS,
            palavras_chave=["tolerância", "atraso permitido", "faixa de aceitação"],
            perguntas=["O que são as tolerâncias?", "Como configuro a tolerância de entrada?"],
            resposta=(
                "As tolerâncias definem uma faixa de minutos, em torno do horário "
                "previsto, dentro da qual uma batida é tratada como pontual (Entrada, "
                "Saída Almoço, Retorno Almoço, Saída Final — cada uma independente). "
                "Fora da faixa, a diferença inteira conta normalmente como hora extra "
                "ou negativa. A planilha original e o horário batido nunca são "
                "alterados — só o cálculo interno considera a tolerância."
            ),
            links_internos=["configuracoes"], relacionados=["jor-01"],
        ),
        ArtigoQualiAssist(
            id="comp-01", titulo="O que é uma competência",
            categoria=_C.COMPETENCIAS,
            palavras_chave=["competência", "mês", "ano", "período de apuração"],
            perguntas=["O que é uma competência?", "Posso ter vários meses ao mesmo tempo?"],
            resposta=(
                "Cada mês/ano processado vira uma Competência independente, "
                "persistida em disco — fechar o sistema no meio das pendências nunca "
                "perde o trabalho já feito. Várias competências coexistem "
                "livremente; nenhum cálculo mistura dados de competências "
                "diferentes."
            ),
            links_internos=["competencias"], relacionados=["comp-02", "imp-02"],
        ),
        ArtigoQualiAssist(
            id="comp-02", titulo="Fechar e reabrir uma competência",
            categoria=_C.COMPETENCIAS,
            palavras_chave=["fechar competência", "reabrir", "travar"],
            perguntas=["Como fecho uma competência?", "Posso reabrir uma competência fechada?"],
            resposta=(
                "Na tela Competências, o botão \"Fechar\" marca a competência como "
                "encerrada — a partir daí, reimportar uma planilha para o mesmo mês "
                "pede confirmação extra antes de sincronizar. \"Reabrir\" remove essa "
                "proteção. Isso é diferente de \"Arquivar\", que só muda o status "
                "visual e não tem ação de desarquivar."
            ),
            links_internos=["competencias"], relacionados=["comp-01"],
        ),
        ArtigoQualiAssist(
            id="bh-01", titulo="Como funciona o Banco de Horas",
            categoria=_C.BANCO_DE_HORAS,
            palavras_chave=["banco de horas", "saldo", "saldo final"],
            perguntas=["O que é o Banco de Horas?", "Como o saldo é calculado?"],
            resposta=(
                "\"Banco de Horas\" é o mesmo Saldo já calculado por dia e "
                "consolidado por competência (horas trabalhadas menos jornada "
                "prevista, com tolerâncias já aplicadas) — não existe acúmulo entre "
                "competências diferentes. Pode ser consultado no Dashboard, na Tela "
                "de Relatórios (filtro \"Banco de Horas\": positivo/negativo/zerado) "
                "e no Dashboard de Absenteísmo."
            ),
            links_internos=["dashboard", "relatorios"], relacionados=["he-01", "hn-01"],
        ),
        ArtigoQualiAssist(
            id="he-01", titulo="Como são calculadas as Horas Extras",
            categoria=_C.HORAS_EXTRAS,
            palavras_chave=["hora extra", "horas extras", "he"],
            perguntas=["Como são calculadas as horas extras?"],
            resposta=(
                "Toda vez que a batida sai da faixa de tolerância configurada e o "
                "funcionário trabalhou mais do que a jornada prevista naquele dia, a "
                "diferença vira Hora Extra. O detalhamento (dia a dia) fica no "
                "Relatório Diário e no Dashboard (ranking de Horas Extras por "
                "funcionário)."
            ),
            links_internos=["dashboard", "relatorios"], relacionados=["bh-01", "jor-02"],
        ),
        ArtigoQualiAssist(
            id="hn-01", titulo="Como são calculadas as Horas Negativas",
            categoria=_C.HORAS_NEGATIVAS,
            palavras_chave=["hora negativa", "atraso", "falta de horas"],
            perguntas=["Como são calculadas as horas negativas?", "O que zera a hora negativa?"],
            resposta=(
                "Quando o funcionário trabalha menos que a jornada prevista (fora da "
                "tolerância), a diferença vira Hora Negativa. Aplicar uma "
                "justificativa que \"elimina hora negativa\" (ex.: Atestado Médico, "
                "Férias, Folga, Licença) zera a hora negativa daquele dia — a "
                "correção é feita na Tela de Pendências."
            ),
            links_internos=["pendencias", "dashboard"], relacionados=["corr-01", "bh-01"],
        ),
        ArtigoQualiAssist(
            id="corr-01", titulo="Como corrigir uma batida",
            categoria=_C.CORRECOES,
            palavras_chave=["corrigir batida", "batida esquecida", "pendência"],
            perguntas=["Como corrijo uma batida?", "O que fazer com uma pendência?"],
            resposta=(
                "Na Tela de Pendências, cada pendência mostra os campos de Entrada, "
                "Saída Almoço, Retorno Almoço e Saída — digite o horário correto e "
                "clique em Salvar. O dia é recalculado imediatamente (nunca a "
                "planilha inteira). Você também pode escolher uma Justificativa e "
                "adicionar Observações, mesmo sem alterar as batidas."
            ),
            links_internos=["pendencias"], relacionados=["corr-02", "hn-01"],
        ),
        ArtigoQualiAssist(
            id="corr-02", titulo="Aplicar Justificativa por Período",
            categoria=_C.CORRECOES,
            palavras_chave=["justificativa por período", "férias", "licença", "vários dias"],
            perguntas=[
                "Como justifico vários dias de uma vez?",
                "Como lanço férias de um funcionário?",
            ],
            resposta=(
                "Na Tela de Pendências, clique em \"Aplicar Justificativa por "
                "Período\", escolha o funcionário, a justificativa e o intervalo de "
                "datas. O sistema mostra um resumo antes de aplicar e pergunta como "
                "tratar dias que já têm outra justificativa (substituir, manter ou "
                "decidir um a um)."
            ),
            links_internos=["pendencias"], relacionados=["corr-01"],
        ),
        ArtigoQualiAssist(
            id="abs-01", titulo="O que é o índice de Absenteísmo",
            categoria=_C.ABSENTEISMO,
            palavras_chave=["absenteísmo", "índice", "faltas"],
            perguntas=["O que é o índice de absenteísmo?", "Como o absenteísmo é calculado?"],
            resposta=(
                "O índice de absenteísmo mede quanto uma ausência (Falta, Falta "
                "Justificada, Atestado Médico, por padrão) pesa sobre a jornada "
                "prevista de cada funcionário, na competência selecionada — sem "
                "nenhum dado novo: usa exatamente o que já foi registrado via "
                "Pendências/Justificativas. Pode ser expresso em Dias, Horas ou "
                "Percentual. Todo índice tem um botão \"Memória de Cálculo\" que "
                "mostra a fórmula exata usada."
            ),
            links_internos=["absenteismo"], relacionados=["abs-02", "abs-03"],
        ),
        ArtigoQualiAssist(
            id="abs-02", titulo="Como configurar o Absenteísmo",
            categoria=_C.ABSENTEISMO,
            palavras_chave=["configurar absenteísmo", "considerar no índice", "método de cálculo"],
            perguntas=[
                "Como escolho quais faltas contam no índice?",
                "Como mudo o método de cálculo?",
            ],
            resposta=(
                "Na tela \"Absenteísmo → Configurações\", escolha o método (Dias, "
                "Horas ou Percentual) e marque, para cada Justificativa, se ela deve "
                "\"considerar no índice\". Toda alteração salva cria uma nova versão "
                "— índices já calculados antes da mudança não são recalculados "
                "retroativamente."
            ),
            links_internos=["absenteismo_config"], relacionados=["abs-01"],
        ),
        ArtigoQualiAssist(
            id="abs-03", titulo="Simulador de Absenteísmo",
            categoria=_C.ABSENTEISMO,
            palavras_chave=["simular", "simulador", "e se faltar mais"],
            perguntas=["Como simulo um cenário de absenteísmo?", "O simulador altera dados reais?"],
            resposta=(
                "Na linha de cada funcionário, o botão \"Simular\" permite testar "
                "\"e se esse funcionário faltar mais N dias\" e ver o resultado "
                "hipotético — nada é gravado; é só uma projeção que desaparece ao "
                "fechar a janela."
            ),
            links_internos=["absenteismo"], relacionados=["abs-01"],
        ),
        ArtigoQualiAssist(
            id="rel-01", titulo="Como gerar um relatório",
            categoria=_C.RELATORIOS,
            palavras_chave=["gerar relatório", "relatório geral", "relatório individual"],
            perguntas=["Como gero o relatório da competência?", "Como exporto para Excel?"],
            resposta=(
                "Na Tela de Relatórios, selecione a competência, ajuste os filtros "
                "se quiser, e clique em Visualizar, Exportar Excel ou Imprimir. A "
                "geração fica bloqueada enquanto existir pendência em aberto no "
                "recorte selecionado."
            ),
            links_internos=["relatorios"], relacionados=["rel-02", "exp-01"],
        ),
        ArtigoQualiAssist(
            id="rel-02", titulo="Relatórios por período e filtros",
            categoria=_C.RELATORIOS,
            palavras_chave=["período", "filtro", "semana", "quinzena"],
            perguntas=[
                "Como gero um relatório só de uma semana?",
                "Quais filtros existem em Relatórios?",
            ],
            resposta=(
                "O seletor \"Período\" permite Mês completo ou um intervalo "
                "personalizado (com atalhos para Hoje/Esta Semana/Quinzena). Além "
                "dos filtros de Funcionário/Setor/Turno/Cargo/Status, também há "
                "Situação, Pendências, Horas Extras e Banco de Horas — todos "
                "combináveis."
            ),
            links_internos=["relatorios"], relacionados=["rel-01"],
        ),
        ArtigoQualiAssist(
            id="dash-01", titulo="O que mostra o Dashboard",
            categoria=_C.DASHBOARD,
            palavras_chave=["dashboard", "indicadores", "ranking"],
            perguntas=["O que o Dashboard mostra?", "Onde vejo o ranking de horas extras?"],
            resposta=(
                "O Dashboard resume a competência selecionada: total de "
                "funcionários, horas trabalhadas/extras/negativas, banco de horas, "
                "pendências e dias processados, além de tabelas ordenadas (horas "
                "extras/negativas por funcionário, pendências por dia, rankings). A "
                "mesma visão também existe como uma 5ª aba no Relatório Excel, com "
                "gráficos nativos."
            ),
            links_internos=["dashboard"], relacionados=["he-01", "bh-01"],
        ),
        ArtigoQualiAssist(
            id="cfg-01", titulo="Onde alterar dados da empresa",
            categoria=_C.CONFIGURACOES,
            palavras_chave=["configurações", "empresa", "logo", "wizard"],
            perguntas=["Como altero o nome da empresa?", "Como troco a logo do sistema?"],
            resposta=(
                "Na tela Configurações: nome da empresa, logo, turnos, tolerâncias e "
                "pasta do Histórico. Na primeira execução, esse mesmo conteúdo "
                "aparece como um assistente passo a passo (Wizard)."
            ),
            links_internos=["configuracoes"], relacionados=["jor-01"],
        ),
        ArtigoQualiAssist(
            id="exp-01", titulo="Exportar para Excel, CSV ou PDF",
            categoria=_C.EXPORTACOES,
            palavras_chave=["exportar", "excel", "csv", "pdf"],
            perguntas=["Posso exportar em PDF?", "Como exporto uma lista para CSV?"],
            resposta=(
                "Praticamente toda tabela do sistema (Funcionários, Setores, "
                "Pendências, Competências, Histórico, Absenteísmo, Relatórios) tem "
                "um botão \"Exportar\" com Excel, CSV e PDF — sempre respeitando a "
                "pesquisa/ordenação/filtro atuais da tela. Há também um botão "
                "\"Imprimir\" que gera o Excel e já envia para a impressora padrão."
            ),
            links_internos=["relatorios"], relacionados=["rel-01"],
        ),
        ArtigoQualiAssist(
            id="qa-01", titulo="Como usar o QualiAssist",
            categoria=_C.QUALIASSIST,
            palavras_chave=["qualiassist", "ajuda", "assistente"],
            perguntas=["Como uso o QualiAssist?", "O QualiAssist altera meus dados?"],
            resposta=(
                "Clique no botão flutuante no canto da tela para abrir o painel. "
                "Digite sua dúvida ou escolha uma categoria — a busca ignora acento "
                "e maiúsculas, e entende sinônimos comuns (ex.: \"HE\" encontra "
                "\"Horas Extras\"). O QualiAssist só explica e orienta: nunca altera, "
                "exclui ou recalcula nada no sistema."
            ),
            links_internos=[], relacionados=[],
        ),
    ]
