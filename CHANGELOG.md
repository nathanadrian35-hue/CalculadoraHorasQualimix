# Changelog

Todas as mudanças notáveis do QualiPonto são documentadas neste arquivo.

## [2.1.0] - 2026-07-20

Modernização da interface, um novo módulo de Absenteísmo e o QualiAssist —
assistente de ajuda offline integrado a todo o sistema.

### Adicionado

- **Componentes reutilizáveis** (`componentes.py`): `TabelaPadrao` (pesquisa
  instantânea, ordenação por clique no cabeçalho, paginação 25/50/100/Todos)
  e `BotaoExportar` — usados agora por Funcionários, Setores, Histórico,
  Competências, Absenteísmo e pela Administração do QualiAssist.
- **Exportação universal** (`exportacao.py`): Excel, CSV e PDF (nova
  dependência `reportlab`, aprovada explicitamente) em qualquer tabela do
  sistema, mais o botão "Imprimir" já existente em Relatórios estendido às
  demais telas.
- **Atalhos de teclado globais**: F5 (Atualizar), Ctrl+F (Pesquisar),
  Ctrl+P (Imprimir).
- **Módulo de Absenteísmo** (`absenteismo.py`): índice configurável (Dias/
  Horas/Percentual), memória de cálculo transparente, ranking, índice
  geral, classificação por cor (limiares configuráveis), alertas
  automáticos, comparativo entre competências, previsão simples por média
  móvel e simulador que nunca altera dados reais. Configuração versionada
  — cada alteração salva incrementa a versão e registra auditoria; um
  índice já calculado nunca é recalculado retroativamente. Três novas
  Justificativas (Licença Maternidade, Licença Paternidade, Feriado).
- **QualiAssist** (`qualiassist.py`): assistente de ajuda 100% offline,
  com base de conhecimento própria (22 artigos cobrindo todo o sistema),
  busca tolerante a acento/caixa/plural/sinônimo, botão flutuante sempre
  visível, ajuda contextual por tela, "Explicar esta Tela", reconhecimento
  de mensagens de erro conhecidas, histórico e favoritos, e um painel
  administrativo para editar a base sem tocar em código.

### Alterado

- `Justificativa` (`constantes.py`) ganhou 3 novos valores, também
  incluídos em `JUSTIFICATIVAS_QUE_ELIMINAM_HORA_NEGATIVA` (mesma
  natureza das já existentes).
- `usuario_atual()` (auditoria) consolidado num único lugar
  (`modelos.py`) — antes existia uma cópia idêntica em `competencias.py`
  e outra em `absenteismo.py`.
- `tela_absenteismo.py` passa a popular o seletor de competências via
  `competencias.listar_indice()` (leve) em vez de `listar()` (carrega
  tudo), carregando a competência selecionada sob demanda.

### Compatibilidade

- **Retrocompatível.** Nenhuma regra de cálculo, tela ou relatório
  existente foi removida ou alterada — tudo que a v2.0 fazia continua
  fazendo exatamente da mesma forma. Absenteísmo e QualiAssist só leem
  dados já registrados pelos módulos existentes (Pendências/
  Justificativas); nenhum dos dois grava em `funcionarios.json`/
  `configuracoes.json`/competências.

## [2.0.0] - 2026-07-20

Evolução do sistema para o fluxo real do RH: a planilha é exportada
**semanalmente**, sempre com o layout do mês inteiro, mas só com os dias
já ocorridos preenchidos — o QualiPonto passa a **atualizar** a mesma
competência incrementalmente a cada importação, em vez de processar um
único arquivo isolado.

### Adicionado

- **Importação incremental por competência.** Reimportar um mês já
  existente não substitui mais nada: `competencias.sincronizar_competencia()`
  mescla a nova planilha dia a dia — dia com batida idêntica à já
  registrada não é tocado, dia novo é adicionado, dia diferente é
  atualizado, e nenhum funcionário/dia é removido, mesmo ausente do
  arquivo mais recente.
- **Proteção de correções manuais.** Um dia com batida digitada
  manualmente (Cap. 9.4) ou com pendência já resolvida/justificada nunca
  é sobrescrito por uma nova importação, mesmo que a planilha traga um
  valor diferente para aquele dia.
- **Dia futuro não gera pendência falsa.** O Motor de Cálculo agora sabe
  distinguir "dia sem batida porque ainda não ocorreu" (depois do último
  dia com dado em qualquer funcionário do lote) de "dia sem batida que é
  uma pendência real" — planilhas com o layout do mês inteiro, mas só
  parcialmente preenchidas, não geram mais dezenas de pendências
  fantasmas para os dias futuros.
- **Histórico de importações e auditoria por competência.** Cada
  competência guarda quantas vezes foi importada (com data/hora, usuário
  do Windows, arquivo e quantidade de registros adicionados/alterados) e
  um log de auditoria (quem/quando/o quê/valor anterior/valor novo) para
  correções manuais de batida, justificativa e observações, além de
  aplicações de Justificativa por Período — consultável pelo botão
  "Histórico" da Tela Competências.
- **Fechamento de competência.** Uma competência pode ser marcada como
  Fechada (Tela Competências); reimportar sobre uma competência fechada
  exige confirmação explícita antes de sincronizar. Independente do
  status detalhado já existente, um selo simplificado de 3 estados
  (🟢 Em andamento / 🟡 Aguardando pendências / 🔴 Fechada) resume a
  situação de cada competência.
- **Relatórios por período.** A Tela de Relatórios ganha um seletor de
  período (Mês completo ou intervalo personalizado, com atalhos para
  Hoje/Esta Semana/Quinzena) e novos filtros de Situação, Pendências,
  Horas Extras e Banco de Horas — combináveis entre si e com os filtros
  já existentes (Funcionário/Setor/Turno/Cargo/Status). O bloqueio por
  pendência em aberto passa a considerar apenas o recorte selecionado,
  não a competência inteira.
- **Dashboard.** Nova tela com indicadores (funcionários, horas
  trabalhadas/extras/negativas, banco de horas, pendências, dias
  processados) e tabelas ordenadas (horas extras/negativas por
  funcionário, pendências por dia, horas extras por dia, rankings de
  horas extras e de atrasos, distribuição do banco de horas) para a
  competência selecionada. Uma 5ª aba "Dashboard" equivalente é
  adicionada ao Relatório Geral em Excel, com indicadores, rankings e
  gráficos nativos do Excel (`openpyxl.chart` — sem nenhuma dependência
  nova).
- "Banco de Horas" como sinônimo do Saldo já existente (`saldo_final_min`)
  em toda a interface nova — nenhuma regra de acúmulo entre competências
  diferentes foi criada.

### Compatibilidade

- **Retrocompatível.** Todas as regras de cálculo (jornadas, tolerâncias,
  horas extras, horas negativas), o formato dos relatórios Excel já
  existentes (as 4 abas originais permanecem exatamente como eram) e o
  fluxo de Pendências/Justificativa por Período continuam funcionando
  sem alteração. Competências e cadastros de instalações v1.x são lidos
  normalmente — os campos novos (`fechada`, `quantidade_importacoes`,
  `historico_importacoes`, `auditoria`) recebem valores padrão vazios na
  primeira leitura.
- Uma competência processada de uma única vez (fluxo antigo) produz
  exatamente o mesmo resultado de antes — a sincronização incremental só
  entra em ação ao reimportar um mês já existente.

## [1.1.1] - 2026-07-17

### Corrigido

- **Wizard de configuração inicial pulava visualmente a etapa de Tolerâncias.**
  Ao clicar em "Próximo" na etapa de Turnos, a Wizard avançava corretamente seu
  índice interno (o rótulo "Etapa 4 de 7" já aparecia certo), mas a tela
  continuava mostrando o conteúdo da etapa anterior (Turnos) por cima — os
  quatro grupos de tolerância existiam e tinham valores padrão corretos, mas
  ficavam inacessíveis visualmente durante a primeira execução. Depois de
  concluir a Wizard, a tela Configurações (modo de edição) sempre mostrou tudo
  normalmente, porque usa um container diferente do da Wizard.
  **Causa raiz:** a etapa de Tolerâncias havia sido implementada em `1.1.0`
  usando `CTkScrollableFrame` como o próprio container da página, para caber
  os quatro grupos. Nesta tela, todas as 7 etapas da Wizard ficam empilhadas
  na mesma célula do layout e são alternadas por `tkraise()`; um
  `CTkScrollableFrame` usado dessa forma não respeita esse `tkraise()` (a
  página anterior permanece visível por cima), diferente de um `CTkFrame`
  comum — usado por todas as outras 6 etapas.
  **Correção:** a etapa de Tolerâncias volta a usar um `CTkFrame` comum,
  exatamente o mesmo padrão das demais etapas da Wizard e do modo de edição.
  Nenhuma lógica de configuração, cálculo ou persistência foi alterada — o
  bug era puramente de exibição durante a Wizard.

## [1.1.0] - 2026-07-17

### Adicionado

- Tolerâncias de **Saída para o Almoço** e **Saída Final**, completando as quatro
  tolerâncias de jornada (Entrada, Saída Almoço, Retorno Almoço, Saída Final) — todas
  independentes, configuráveis e opcionais, cada uma com seu próprio checkbox
  "Ativar" e campo de minutos, seguindo a mesma faixa de aceitação já usada por
  Entrada/Retorno do Almoço desde a v1.0 (`abs(real - previsto) <= minutos`).
- Novos grupos "Saída para o Almoço" e "Saída Final" na tela de Configurações
  (Wizard de primeira execução e modo de edição), reaproveitando integralmente o
  componente visual já existente.
- `CHANGELOG.md` (este arquivo).

### Alterado

- `calculadora.py`: a aplicação de tolerâncias foi refatorada para uma estrutura
  orientada a dados (`_pontos_tolerancia()`), eliminando repetição de código ao
  escalar de 2 para 4 pontos de tolerância. A função `_aplicar_tolerancia()` e a
  regra de cálculo (`abs(real - previsto) <= minutos`, faixa de aceitação, contagem
  integral fora da faixa) permanecem exatamente as mesmas — nenhuma lógica de
  cálculo foi alterada, apenas reorganizada.
- `config.py`: `configuracoes.json` passa a ter as chaves `tolerancia_saida_almoco`
  e `tolerancia_saida` (mesmo formato `{"ativa": bool, "minutos": int}` das já
  existentes).

### Compatibilidade

- **Retrocompatível.** Um `configuracoes.json` de uma instalação v1.0 (sem as duas
  chaves novas) recebe automaticamente `tolerancia_saida_almoco` e
  `tolerancia_saida` desativadas (`ativa: false, minutos: 0`) na primeira leitura,
  através do mecanismo de merge já existente — nenhuma configuração anterior é
  apagada ou alterada, e o comportamento de cálculo permanece idêntico ao v1.0
  enquanto as duas novas tolerâncias não forem ativadas manualmente.
- Relatórios Excel, Histórico, Competências, Dashboard e Pendências: nenhuma
  alteração estrutural ou de layout — os relatórios continuam exibindo as batidas
  reais originais; apenas o cálculo das horas passa a considerar as tolerâncias
  adicionais quando configuradas.

## [1.0.0] - 2026-07-17

Primeira versão oficial do QualiPonto. Importação inteligente de planilhas,
cadastro de funcionários/setores/cargos/turnos, gerenciamento de múltiplas
competências, revisão de importação, motor de cálculo de horas, tratamento de
pendências, relatórios Excel, histórico, backup automático e instalador
profissional para Windows.
