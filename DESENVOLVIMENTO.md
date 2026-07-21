# DESENVOLVIMENTO

## QualiPonto — Sistema de Controle de Jornada e Horas Extras

**Desenvolvedor:** Nathan Adrian

---

# OBJETIVO

Este documento define a ordem oficial de desenvolvimento do sistema.

Todas as implementações deverão seguir exatamente esta sequência.

Nenhuma Sprint poderá iniciar antes da conclusão da anterior.

---

# SPRINT 1

## Objetivo

Criar a base da aplicação.

### Arquivos

- main.py
- config.py
- interface.py
- tela_principal.py

### Funcionalidades

- Inicialização do sistema
- Criação automática das pastas
- Criação automática dos arquivos JSON
- Carregamento das configurações
- Interface principal
- Barra de status
- Tema escuro
- Navegação entre telas

### Critério de conclusão

O sistema abre normalmente.

---

# SPRINT 2

## Objetivo

Criar o módulo de configurações.

### Funcionalidades

- Cadastro da empresa
- Cadastro da logo
- Cadastro dos turnos
- Tolerância de entrada
- Tolerância do almoço
- Salvamento em JSON
- Backup automático

### Critério de conclusão

Todas as configurações são salvas corretamente.

---

# SPRINT 2.5

## Objetivo

Implementar o Cadastro de Setores.

### Arquivos

- tela_setores.py
- config.py (extensão)

### Funcionalidades

- Cadastro de setores: nome, cor (opcional), status (Ativo/Inativo)
- Adicionar, editar, ativar/inativar e excluir setor
- Exclusão bloqueada quando houver funcionário vinculado (estrutura preparada para a Sprint 3)
- Persistência em dados/setores.json, com backup automático
- Acesso pela Tela Principal (botão Setores)

### Critério de conclusão

O usuário consegue cadastrar, editar, ativar/inativar e excluir setores, com os dados salvos corretamente.

---

# SPRINT 3

## Objetivo

Implementar o Cadastro Inteligente Assistido de Funcionários (Cap. 5):
cadastro manual completo (complementar) + motor de sugestão automática
de turno + painel de revisão + ações em massa, tudo construído e
testado com dados simulados. A leitura real de arquivos XLS/XLSX fica
para a Sprint 3.5 — esta sprint prepara a arquitetura para que a
leitura real apenas alimente o mecanismo já pronto, sem refatoração.

### Arquivos

- tela_funcionarios.py
- config.py (extensão)
- modelos.py (extensão: estrutura de sugestão de importação)

### Funcionalidades

- Cadastro completo: ID (UUID), Nome Completo, Nome utilizado na Planilha (opcional), Apelido, Matrícula, CPF, Cargo, Turno (vínculo por ID), Setor (vínculo por ID), Status
- Cadastro manual: adicionar, editar, excluir, ativar/inativar (complementar à importação)
- Motor de sugestão de turno: compara um horário de entrada com os turnos cadastrados e retorna a sugestão + confiança (✓ Confirmado / ⚠ Revisar) — testável com dados simulados, sem depender de leitura real de arquivo
- Painel de Revisão: tabela Funcionário / Horário Encontrado / Turno Sugerido / Situação; só exige ação do usuário nos casos "⚠ Revisar"
- Reconhecimento de funcionários já cadastrados (evita duplicação), usando Nome na Planilha / Nome Completo
- Importação parcial: funcionários ausentes de uma importação nunca são excluídos, inativados ou perdem vínculo — só os encontrados são atualizados, novos são adicionados
- Ações em massa: selecionar múltiplos (ou todos) e aplicar Turno, Setor, Cargo, Ativar ou Inativar
- Pesquisa em tempo real, ordenação alfabética, filtros e contadores (Total/Ativos/Inativos)
- Persistência em funcionarios.json, com backup automático

### Critério de conclusão

O usuário consegue cadastrar funcionários manualmente, e o motor de
sugestão de turno + painel de revisão funcionam corretamente com dados
de teste simulados (sem leitura real de arquivo).

---

# SPRINT 3.5

## Objetivo

Implementar a leitura real da planilha (XLS/XLSX) e conectá-la ao
motor de sugestão de turno e ao painel de revisão já construídos na
Sprint 3, sem necessidade de refatoração. Emendada, ainda dentro desta
sprint (antes do commit), para também reconhecer o campo "Dep." da
planilha, sugerir Setor automaticamente (Cap. 5.16) e permitir a
criação automática de Setores ainda não cadastrados (Cap. 5.17/21.8).
Emendada uma segunda vez para evoluir o Turno: jornada independente
para Segunda–Sexta, Sábado e Domingo (Cap. 4.6/6.4/6.5), com migração
automática dos turnos cadastrados no formato antigo.

### Arquivos

- leitor_ponto.py
- validacao.py
- cadastro.py
- modelos.py (extensão: sugestão de Setor, normalização tolerante, JornadaDia/Turno por tipo de dia)
- tela_funcionarios.py (extensão: Setor no painel de revisão, tela "Novos Setores Encontrados")
- tela_principal.py / interface.py (ligação do botão Processar ao fluxo real)
- config.py (extensão: serialização e migração automática da nova estrutura do Turno)
- tela_configuracoes.py (extensão: painel de Turno com jornada por tipo de dia)

### Funcionalidades

- Ler XLS
- Ler XLSX
- Identificar competência (célula "Data de presença", com suporte a intervalos que cruzam meses)
- Identificar funcionários e horários de entrada na planilha
- Alimentar o motor de sugestão de turno (Sprint 3) com os dados reais extraídos
- Localizar automaticamente o funcionário cadastrado correspondente (Nome utilizado na Planilha, com Nome Completo como alternativa)
- Ler dias
- Ler batidas
- Identificar novos funcionários e possíveis conflitos, usando a infraestrutura já pronta
- Respeitar a Importação Parcial (Cap. 5.7): nunca excluir, inativar ou desvincular funcionários ausentes da planilha importada
- Validar estrutura da planilha
- Ler o campo "Dep." de cada funcionário e sugerir Setor automaticamente (Cap. 5.16), com comparação tolerante a maiúsculas/minúsculas, acentos e espaços extras
- Detectar "Dep." sem Setor cadastrado correspondente e, antes do painel de revisão, oferecer a criação automática dos Setores novos (Cap. 5.17), reaproveitando a persistência já existente de setores.json (Cap. 21.6)
- Considerar os Setores recém-criados na mesma importação, sem exigir reprocessamento
- Turno com jornada independente por tipo de dia (Cap. 4.6): Segunda–Sexta obrigatória; Sábado e Domingo opcionais, cada um com Entrada/Saída e intervalo também opcional ("Possui intervalo")
- Jornada de cada dia calculada e exibida automaticamente a partir dos horários preenchidos
- Migração automática, sem perda de dados, dos turnos cadastrados no formato antigo (um único horário + trabalha_sabado/trabalha_domingo booleanos) para a nova estrutura

### Critério de conclusão

O sistema consegue importar corretamente uma planilha real da Qualimix,
usando o motor de sugestão e o painel de revisão já construídos,
consegue criar automaticamente os Setores que a planilha trouxer sem
que já existam cadastrados, e o cadastro de Turnos suporta jornada
independente por tipo de dia, com os turnos já existentes migrados
automaticamente.

---

# SPRINT 4

## Objetivo

Criar o motor de cálculo (Cap. 6/7/8/9/10): uma única função pura por
dia (`recalcular_dia`), reaproveitada tanto no processamento completo
quanto no reprocessamento incremental após correções manuais (Cap.
10.7). Fecha a lacuna entre o Cadastro Inteligente e o cálculo — hoje
os dias/batidas lidos da planilha não chegam ao `Funcionario` que sai
do Painel de Revisão. Inclui a Tela de Pendências completa (Cap.
9.3/9.4/9.5/9.6): visualizar, corrigir batidas, informar justificativa
e observações, recalculando apenas o dia editado.

### Arquivos

- calculadora.py (implementado pela primeira vez)
- tela_pendencias.py (novo)
- modelos.py (extensão: `Turno.jornada_do_dia()`, `ResumoMensalFuncionario`, `TipoPendencia.TURNO_NAO_DEFINIDO`)
- constantes.py (extensão: lista central de Justificativas que eliminam Hora Negativa)
- tela_funcionarios.py (extensão: `_concluir_revisao()` anexa `.dias` e devolve os funcionários processáveis)
- tela_principal.py / interface.py (orquestração: Painel de Revisão → Motor de Cálculo → Tela de Pendências)
- config.py (remoção do bloco `configuracoes["jornada"]`, morto desde a Sprint 3.5)

### Funcionalidades

- Horas trabalhadas, horas extras, horas negativas, saldo (Cap. 10)
- Determinação da jornada esperada por tipo de dia a partir do Turno (Cap. 4.6/6.4/6.5)
- Aplicação das tolerâncias como faixa de aceitação, com contagem integral a partir do previsto fora da faixa (Cap. 8)
- Classificação de pendências de quantidade de batidas, agora ciente do Turno (Cap. 7)
- Nova pendência "Turno não definido" — funcionário sem Turno válido não é calculado (Cap. 9.2)
- Justificativas com efeito centralizado sobre a Hora Negativa (Cap. 9.7)
- Tela de Pendências: visualizar, corrigir batidas, justificar, observar, recalcular só o dia editado (Cap. 9.3/9.4/9.5/10.7)
- Resumo mensal por funcionário, pronto para alimentar o relatório (Sprint 5) sem cálculo adicional

### Critério de conclusão

Todos os cálculos batem manualmente contra a planilha real da
Qualimix para os casos de semana, sábado (com e sem jornada
configurada), domingo (com e sem jornada configurada), tolerâncias,
pendências e justificativas — e o reprocessamento após uma correção
manual atualiza só o dia editado.

---

# SPRINT 4.1

## Objetivo

Homologar o Motor de Cálculo e a Tela de Pendências antes de iniciar a
Sprint 5: auditoria de pendências, homologação manual contra a
planilha real da Qualimix, e escalabilidade da Tela de Pendências para
grandes volumes (centenas de funcionários).

### Arquivos

- tela_pendencias.py (padrão de pool/virtualização de widgets: os
  mesmos ~25 widgets de linha são reaproveitados ao trocar de página,
  em vez de criar/destruir a cada troca)

### Funcionalidades

- Paginação da Tela de Pendências
- Virtualização de widgets (correção de lentidão identificada por
  benchmark com dataset sintético de 300 funcionários × 28 dias)
- Regressão completa do Motor de Cálculo contra dados reais

### Critério de conclusão

Motor de Cálculo homologado; Tela de Pendências abre e navega entre
páginas em menos de 1 segundo mesmo com centenas de pendências.

---

# SPRINT 5

## Objetivo

Transformar os resultados do Motor de Cálculo em relatórios
consultáveis pelo usuário — Relatório Individual por Funcionário,
Relatório Geral da Competência, Resumo Geral e Estatísticas —, com uma
Tela de Relatórios dedicada, exportação para Excel com formatação
profissional, e bloqueio da geração enquanto houver pendência em
aberto. Nenhuma regra do Motor de Cálculo é alterada ou reimplementada
— este módulo só agrega, formata e exporta o que o Motor já produziu.

### Arquivos

- relatorio.py (novo)
- tela_relatorios.py (novo)
- modelos.py (extensão: dataclasses de relatório — `ResumoIndividualRelatorio`, `ResumoGeralCompetencia`, `EstatisticasCompetencia`, `DadosRelatorio`)
- interface.py / tela_principal.py (registro da tela, controlador guarda o último `ResultadoProcessamento` da sessão)
- tela_configuracoes.py (implementação do modo de edição — Cap. 12.5, necessário para corrigir Turnos entre competências sem repetir o Wizard)

### Funcionalidades

- Relatório Geral (4 abas: Relatório Diário, Resumo Mensal, Pendências, Informações do Processamento)
- Relatório Individual por Funcionário
- Resumo Geral da Competência
- Estatísticas da Competência
- Bloqueio da geração enquanto houver pendência em aberto (Cap. 9.1/11.11)
- Tela de Relatórios: filtros por Funcionário/Setor/Turno/Cargo/Status, resumo superior, Visualizar/Exportar Excel/Imprimir
- Exportação Excel com formatação profissional (cabeçalho em destaque, painel congelado, bordas, largura de coluna ajustada, layout de impressão em paisagem)
- Histórico com nomeação incremental (nunca sobrescreve um relatório já exportado)
- Arquitetura de exportação pronta para múltiplos formatos (`ExportadorRelatorio`); exportação em PDF **não implementada nesta sprint** — reservada para versão futura, mesmo padrão do Cap. 6.6 (Feriados)

### Critério de conclusão

O Excel é gerado corretamente (Geral e Individual), com bloqueio
efetivo por pendência aberta, filtros funcionando, e regressão
completa (Wizard, Configurações, Cadastro, Importação, Setores,
Turnos, Motor de Cálculo, Tela de Pendências, Tela de Relatórios)
sem quebras.

---

# SPRINT 6

## Objetivo

Finalização do sistema.

### Funcionalidades

- Histórico
- Logs
- Testes
- Correções
- Geração do Executável (.exe)

### Critério de conclusão

Sistema pronto para utilização na empresa.

---

# SPRINT 6.5

## Objetivo

Última funcionalidade antes do empacotamento em .exe: transformar o
processamento de uma única competência em memória (perdida ao fechar o
sistema) em gerenciamento de múltiplas competências persistidas em
disco, cada uma com estado independente e retomável; e resolver a
limitação conhecida de identificação de funcionário só por nome,
passando a usar o IDUsuário da planilha como identificador principal,
com migração automática. Não altera o Motor de Cálculo, os relatórios
já existentes, nem o Histórico — reaproveita tudo que já existia.

### Arquivos

- competencias.py (novo — persistência da Competência, máquina de
  estados do status, invariante de referência da Pendência)
- tela_competencias.py (novo — cards com contadores, status, Abrir/
  Arquivar)
- constantes.py (extensão: `StatusCompetencia`)
- modelos.py (extensão: `Funcionario.id_planilha`,
  `SugestaoImportacao.id_planilha`,
  `localizar_funcionario_por_id_planilha`, dataclass `Competencia`)
- config.py (extensão: `ler_json`/`escrever_json` públicos, `id_planilha`
  em `funcionario_para_dict`/`funcionario_de_dict`, `COMPETENCIAS_DIR`)
- leitor_ponto.py (`_mesclar_repetidos` chaveado por `id_planilha`)
- cadastro.py (`montar_sugestoes_importacao` tenta `id_planilha`
  primeiro, cai para nome — migração just-in-time)
- tela_funcionarios.py (correção do casamento por posição, não por
  nome, em `_concluir_revisao`; subtítulo de IDUsuário no Painel de
  Revisão)
- tela_principal.py (checagem de competência já existente; persiste a
  Competência logo após o Motor de Cálculo rodar)
- interface.py (`iniciar_tela_pendencias`/`abrir_competencia` recebem
  `Competencia`; `competencia_atual` substitui os 3 atributos soltos
  anteriores)
- tela_pendencias.py (persistência incremental a cada correção/
  justificativa aplicada)
- tela_relatorios.py (seletor de competência; marca relatório gerado)

### Funcionalidades

- Persistência automática de cada Competência (funcionários, dias,
  pendências, justificativas, resumo mensal, estatísticas, status) em
  `dados/competencias/`, um arquivo por mês/ano
- Status da Competência com transição automática (Em andamento /
  Pendências abertas / Pronta para relatório / Relatório gerado) e
  Arquivada manual (sem Desarquivar nesta versão)
- Tela Competências: listar, Abrir (retomar trabalho exatamente de
  onde parou) e Arquivar
- Múltiplas competências coexistindo de forma totalmente independente
- Tela de Relatórios com seletor de competência, gerando o relatório
  de qualquer uma sem afetar as demais
- Reimportar uma competência já existente pergunta Substituir/
  Cancelar — nunca duplica
- Identificação de funcionário por IDUsuário (identificador principal),
  diferenciando corretamente homônimos; migração automática
  just-in-time de cadastros antigos sem `id_planilha`

### Critério de conclusão

Homologado com as duas planilhas reais da Qualimix (Julho/2026 e
Abril/2026): múltiplas competências coexistindo, retomada após fechar
o sistema com pendências/justificativas preservadas, geração de
relatório independente por competência, reimportação com
substituição/cancelamento, homônimos sintéticos corretamente
diferenciados (incluindo o caso de correspondência por posição em vez
de nome no Painel de Revisão), Histórico inalterado, análise estática
(pyflakes/pycodestyle/mypy) limpa em todos os arquivos.

---

# SPRINT 7 (v1.1)

## Objetivo

Completar as tolerâncias de jornada: a v1.0 só cobria Entrada e Retorno
do Almoço; faltavam Saída para o Almoço e Saída Final. Implementadas
as duas, reaproveitando integralmente a função `_aplicar_tolerancia()`
e a regra de faixa de aceitação já existentes (Cap. 8) — nenhuma
lógica de cálculo nova, apenas os dois pontos que faltavam. Motor
refatorado para uma estrutura orientada a dados (`_pontos_tolerancia()`)
para os 4 pontos não repetirem código entre si.

### Arquivos

- calculadora.py (`_pontos_tolerancia()` novo; `recalcular_dia()`
  aplica os 4 pontos num único laço, sem duplicar a leitura/aplicação
  de tolerância)
- config.py (`tolerancia_saida_almoco`/`tolerancia_saida` no padrão de
  `configuracoes.json` — retrocompatível via o mecanismo de merge já
  existente, nenhuma configuração antiga é apagada)
- tela_configuracoes.py (dois novos grupos "Saída para o Almoço" e
  "Saída Final" no Wizard e no modo de edição, reaproveitando
  `_montar_bloco_tolerancia()`; resumo do Wizard atualizado)
- ESPECIFICACAO.md (Cap. 4.7 consolidado em "Tolerâncias de Jornada";
  Cap. 8 com as 4 tolerâncias: 8.1 Entrada, 8.2 Saída Almoço, 8.3
  Retorno Almoço, 8.4 Saída Final)

### Funcionalidades

- Tolerância de Saída para o Almoço (faixa de aceitação em torno do
  horário previsto de saída para o intervalo)
- Tolerância de Saída Final (faixa de aceitação em torno do horário
  previsto de saída do dia, com ou sem intervalo)
- As quatro tolerâncias — Entrada, Saída Almoço, Retorno Almoço, Saída
  Final — totalmente independentes, configuráveis e opcionais
- Retrocompatibilidade automática: `configuracoes.json` de uma
  instalação v1.0 ganha as duas chaves novas (desativadas) na primeira
  leitura, sem apagar nada

### Critério de conclusão

Testes unitários dos 4 pontos de tolerância com os valores exatos
pedidos (janelas de 6 horários por ponto, incluindo a borda que sai da
faixa), homologação com a planilha real de Julho/2026 (comparação
manual entre a batida original da planilha e o Relatório Diário
exportado, confirmando batidas reais preservadas e horas ajustadas
corretas), reprocessamento via Tela de Pendências, Dashboard/
Competências/Histórico sem alteração estrutural, regressão com
tolerâncias desativadas reproduzindo exatamente o comportamento do
v1.0, análise estática (pyflakes/pycodestyle/mypy) limpa em todos os
arquivos.

---

# SPRINT 7.1 (v1.1.1) — Correção da Wizard

## Objetivo

Corrigir um bug visual encontrado após a publicação da v1.1: na Wizard
de primeira execução, a etapa de Tolerâncias (Cap. 4.7) ficava
encoberta pela etapa anterior (Turnos) ao clicar em "Próximo" — o
índice interno avançava corretamente ("Etapa 4 de 7"), mas o conteúdo
exibido continuava sendo o de Turnos. Depois de concluir a Wizard, a
tela Configurações sempre mostrou as tolerâncias normalmente, por usar
um container diferente.

## Causa raiz

`_montar_etapa_wizard_tolerancias()` usava `ctk.CTkScrollableFrame`
como o próprio container da página, para caber os quatro grupos de
tolerância. Nesta tela, as 7 etapas da Wizard ficam todas empilhadas
na mesma célula do grid e são alternadas por `tkraise()` — um
`CTkScrollableFrame` usado como página não respeita esse `tkraise()`
(a página anterior permanece visível por cima), ao contrário de um
`CTkFrame` comum, usado por todas as outras 6 etapas.

### Arquivos

- tela_configuracoes.py (`_montar_etapa_wizard_tolerancias` volta a
  usar `ctk.CTkFrame`, o mesmo container de todas as demais etapas)
- CHANGELOG.md / README.md (registro da correção)

### Funcionalidades

Nenhuma nova — correção pontual de exibição. As quatro tolerâncias
continuam funcionando exatamente como na v1.1 (motor de cálculo e
`configuracoes.json` intocados).

### Critério de conclusão

Bug reproduzido com automação real de mouse (clique físico simulado +
captura de tela, não apenas chamadas programáticas — que não
reproduziam o problema), e a correção confirmada da mesma forma.
Testes unitários dos 4 pontos de tolerância, homologação com planilha
real, reprocessamento, Dashboard/Competências/Histórico e regressão
completa reexecutados e aprovados. Análise estática
(pyflakes/pycodestyle/mypy) limpa em todos os arquivos.

---

# SPRINT 8 (v2.0) — Competência Incremental, Importação Semanal e Dashboard

## Objetivo

Evoluir o sistema para o fluxo real do RH: a planilha é exportada
semanalmente, sempre com o layout do mês inteiro, mas só com os dias já
ocorridos preenchidos. Passar a atualizar a mesma competência
incrementalmente a cada importação, sem remover nenhuma funcionalidade
existente e sem alterar nenhum resultado de cálculo já produzido.

### Arquivos

- calculadora.py (dia futuro sem batida não gera pendência — nova
  função `_ultimo_dia_com_dados`, novo ramo em `recalcular_dia`)
- constantes.py (`StatusSimplificado`, `VERSAO = "2.0.0"`)
- modelos.py (`RegistroImportacao`, `RegistroAuditoria`, `Competencia`
  estendida: `fechada`, `data_fechamento`, `quantidade_importacoes`,
  `historico_importacoes`, `auditoria`; `ContextoCalculo.ultimo_dia_com_dados`)
- competencias.py (sincronização incremental, proteção de dia corrigido,
  índice leve para performance, fechar/reabrir, auditoria, histórico de
  importações)
- tela_principal.py (importação passa a sincronizar em vez de
  substituir; confirmação extra para competência fechada)
- tela_pendencias.py (hooks de auditoria em correção manual e
  Justificativa por Período)
- tela_competencias.py (selo simplificado, Fechar/Reabrir, Histórico)
- tela_relatorios.py (período, novos filtros, bloqueio por pendência
  restrito ao recorte selecionado)
- tela_dashboard.py (novo — Dashboard in-app)
- relatorio.py (`filtrar_por_periodo`, `filtrar_por_atributos`, nova
  aba "Dashboard" no Excel com gráficos nativos)
- interface.py (registro da tela Dashboard)

### Funcionalidades

- Importação semanal incremental por competência, com proteção de
  correções manuais e justificativas já resolvidas
- Dia futuro (sem batida, após o último dia com dado do lote) não gera
  mais pendência falsa
- Histórico de importações e auditoria (usuário do Windows,
  quando/o quê/valor anterior/valor novo) por competência
- Fechamento/reabertura de competência, com confirmação extra ao
  reimportar sobre uma competência fechada
- Relatórios por período (mês completo ou intervalo personalizado) e
  novos filtros (Situação, Pendências, Horas Extras, Banco de Horas)
- Dashboard in-app e aba "Dashboard" no Excel (gráficos nativos
  openpyxl, sem dependência nova)
- "Banco de Horas" como sinônimo do Saldo já existente — nenhuma regra
  de acúmulo nova

### Critério de conclusão

Convergência confirmada entre 4 importações incrementais sequenciais e
o processamento completo de uma só vez, usando as duas planilhas reais
do projeto (Julho/2026 e Abril/2026): mesmo conjunto de dias, mesmos
valores calculados. Proteção de dia corrigido manualmente confirmada
sobrevivendo a uma reimportação completa subsequente. Regressão
confirmando que os filtros padrão da Tela de Relatórios (sem tocar nos
novos controles) reproduzem exatamente o comportamento anterior ao
v2.0, e que as 4 abas originais do Excel permanecem inalteradas.
Auditoria testada ponta a ponta (correção individual, reaplicação
idempotente, Justificativa por Período em lote). Análise estática
(pyflakes/pycodestyle/mypy) limpa em todos os arquivos.

---

# SPRINT 9.1 (v2.1) — Modernização de Interface

## Objetivo

Padronizar pesquisa instantânea, ordenação por clique no cabeçalho,
paginação e exportação universal (Excel/CSV/PDF) em todas as telas com
listagem, mais atalhos de teclado globais — sem alterar nenhuma regra
de negócio ou formato de dado persistido.

### Arquivos

- componentes.py (novo — `TabelaPadrao`, `BotaoExportar`,
  `ColunaOrdenavel`, Protocol `LinhaTabela`)
- exportacao.py (novo — `exportar_excel_simples`, `exportar_csv`,
  `exportar_pdf_simples`, `caminho_exportacao`)
- requirements.txt (nova dependência `reportlab`, aprovada
  explicitamente antes de ser adicionada)
- tela_funcionarios.py, tela_setores.py, tela_historico.py,
  tela_competencias.py (migração para `TabelaPadrao`/`BotaoExportar`)
- tela_pendencias.py (ordenação, paginação, exportação e impressão
  mantendo o pool especializado próprio — Cap. 24.4)
- interface.py (`_configurar_atalhos`: F5/Ctrl+F/Ctrl+P)

### Funcionalidades

- Pesquisa instantânea insensível a acento/caixa/plural em todas as
  listagens
- Ordenação por clique no cabeçalho (3 estados: crescente/
  decrescente/original)
- Paginação 25/50/100/Todos, com reciclagem de widgets
- Exportação universal (Excel/CSV/PDF) e impressão em qualquer tabela
- Atalhos de teclado globais: F5, Ctrl+F, Ctrl+P

### Critério de conclusão

Todas as telas com listagem oferecem pesquisa, ordenação, paginação e
exportação de forma padronizada, sem regressão em nenhuma
funcionalidade anterior. Análise estática (pyflakes/pycodestyle/mypy)
limpa em todos os arquivos.

---

# SPRINT 9.2 (v2.1) — Absenteísmo

## Objetivo

Medir e acompanhar o absenteísmo agregando dados já produzidos pelo
Motor de Cálculo e pelas Pendências/Justificativas — sem recalcular
horas e sem inventar regras de negócio não presentes na especificação.

### Arquivos

- absenteismo.py (novo — motor completo: configuração versionada,
  cálculo de indicadores, memória de cálculo, ranking, comparativo,
  previsão, simulador)
- tela_absenteismo.py (novo — dashboard/indicadores/ranking/alertas/
  comparativo)
- tela_absenteismo_config.py (novo — Justificativas consideradas,
  método de cálculo, limiares de cor)
- constantes.py (3 novas Justificativas — Licença Maternidade,
  Licença Paternidade, Feriado —, `MetodoCalculoAbsenteismo`, limiares
  padrão)
- modelos.py (`ConfiguracaoOcorrencia`, `ConfiguracaoAbsenteismo`,
  `OcorrenciaAbsenteismo`, `IndicadorAbsenteismo`, `usuario_atual()`
  consolidado)
- tela_principal.py (botão Absenteísmo)
- interface.py (registro das telas)

### Funcionalidades

- Índice configurável (Dias/Horas/Percentual)
- Configuração de quais Justificativas contam no índice, versionada
  (nunca recalcula histórico retroativamente)
- Memória de cálculo sempre visível (nunca "caixa-preta")
- Ranking, classificação por cor, alertas automáticos, comparativo
  entre competências, previsão por média móvel
- Simulador que nunca altera dados reais

### Critério de conclusão

Índices calculados batem manualmente contra pendências/justificativas
de competências reais; mudança de configuração comprovadamente não
altera índices já apurados; simulador comprovadamente não grava nada.
Análise estática limpa em todos os arquivos.

---

# SPRINT 9.3 (v2.1) — QualiAssist

## Objetivo

Assistente de ajuda 100% offline integrado a todo o sistema, com base
de conhecimento própria e editável, sem nunca alterar dados
operacionais do sistema.

### Arquivos

- qualiassist.py (novo — motor: persistência versionada, busca
  tolerante, ajuda contextual por tela, reconhecimento de erros
  conhecidos)
- qualiassist_base_inicial.py (novo — 22 artigos cobrindo as 14
  categorias)
- qualiassist_ui.py (novo — `PainelQualiAssist`, `BotaoFlutuanteQualiAssist`)
- tela_qualiassist_admin.py (novo — CRUD de artigos, exportar/importar
  base JSON)
- interface.py (botão flutuante e painel instanciados uma única vez;
  `abrir_qualiassist()`)

### Funcionalidades

- Botão flutuante sempre visível e painel com pesquisa/categorias/
  histórico/favoritos
- Busca tolerante a acento/caixa/plural/sinônimo
- Ajuda contextual por tela, "Explicar esta Tela"
- Reconhecimento de mensagens de erro conhecidas (por conjunto de
  palavras, não substring exata)
- Painel administrativo com versionamento e auditoria

### Critério de conclusão

Painel/botão flutuante funcionam em todas as telas sem interferir em
nenhuma funcionalidade existente; busca encontra os artigos esperados
para consultas de teste (incluindo variações de acento/plural/
sinônimo); reconhecimento de erro testado contra mensagens reais do
sistema. Análise estática limpa em todos os arquivos.

---

# REGRAS

- Seguir obrigatoriamente o README.md.
- Seguir obrigatoriamente o CLAUDE.md.
- Seguir obrigatoriamente o ESPECIFICACAO.md.
- Não implementar funcionalidades de outras Sprints.
- Cada módulo deve possuir apenas uma responsabilidade.
- O código deve ser limpo, organizado e documentado.
- Toda alteração deverá ser validada antes de iniciar a próxima Sprint.