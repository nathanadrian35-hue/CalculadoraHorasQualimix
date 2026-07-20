# QualiPonto

### Sistema de Controle de Jornada e Horas Extras

> Sistema desktop desenvolvido para automatizar o processamento da folha de ponto da Qualimix.

**Desenvolvido por:** Nathan Adrian

---

# Objetivo

O QualiPonto é um sistema desktop desenvolvido em Python para automatizar a leitura da planilha de ponto da empresa, identificar inconsistências, calcular horas trabalhadas, horas extras e gerar relatórios profissionais em Excel.

O sistema foi projetado para ser simples, rápido, confiável e de fácil manutenção.

A planilha original nunca será alterada.

---

# Tecnologias

- Python 3.13
- CustomTkinter
- Pandas
- OpenPyXL
- xlrd
- Pillow
- PyInstaller
- Git
- GitHub
- JSON (armazenamento das configurações)

---

# Estrutura do Projeto

```text
CalculadoraHorasQualimix/

assets/
    logo/
    icones/

dados/
    empresa.json
    configuracoes.json (inclui os Turnos cadastrados)
    funcionarios.json
    setores.json
    versao.json
    competencias/ (uma Competência por mês/ano — gerenciamento de múltiplas competências)

backup/

Historico/

Logs/

README.md
CLAUDE.md
ESPECIFICACAO.md
DESENVOLVIMENTO.md
TODO.md

main.py
interface.py

tela_principal.py
tela_configuracoes.py
tela_funcionarios.py
tela_setores.py
tela_pendencias.py
tela_relatorios.py
tela_competencias.py
tela_dashboard.py
tela_historico.py
tela_sobre.py

config.py
cadastro.py
validacao.py
leitor_ponto.py
calculadora.py
relatorio.py
competencias.py
modelos.py
constantes.py
logger.py

requirements.txt
```

# Funcionalidades

## Leitura da planilha

- Ler arquivos XLS
- Ler arquivos XLSX
- Detectar automaticamente:
  - Funcionários
  - Competência
  - Dias
  - Horários

---

## Cadastro Inteligente Assistido de Funcionários

A principal forma de cadastro é a importação da planilha do ponto: o sistema identifica os funcionários automaticamente, detecta o horário de entrada predominante e sugere o turno mais compatível, marcando cada sugestão como "✓ Confirmado" ou "⚠ Revisar" num painel de revisão antes de concluir. O cadastro manual continua existindo como complemento (antes da primeira importação, funcionários que ainda não aparecem na planilha, correções, temporários).

- Campos: Nome Completo (obrigatório), Nome utilizado na Planilha (opcional), Apelido, Matrícula, CPF, Cargo (obrigatório).
- Vínculo obrigatório com Turno e Setor, sempre por ID (nunca por nome).
- Adicionar, editar, ativar/inativar e excluir — manual ou em massa (selecionar vários/todos e aplicar Turno/Setor/Cargo/Status).
- O Painel de Revisão da importação também traz uma coluna de Status (Ativo/Inativo, já marcada conforme o cadastro atual): funcionários marcados como Inativo são cadastrados normalmente, mas não entram no Motor de Cálculo, não geram pendência e não aparecem no relatório daquela competência.
- Pesquisa em tempo real, ordenação alfabética, filtros e contadores (Total/Ativos/Inativos).
- **Importação parcial:** uma planilha pode representar toda a empresa, só um setor, só um período ou só alguns funcionários. Quem não aparecer na importação nunca é excluído, inativado ou perde vínculo — o sistema só atualiza quem foi encontrado e adiciona quem for novo.
- **Identificação por IDUsuário:** o identificador principal de um funcionário na planilha é o IDUsuário (não o nome), permitindo diferenciar corretamente dois funcionários reais com o mesmo nome (homônimos) — cada um chega ao Painel de Revisão como uma linha distinta, com o próprio IDUsuário visível como subtítulo. Cadastros anteriores a esta funcionalidade são migrados automaticamente, sem nenhuma tela ou rotina separada: na próxima importação em que o funcionário reaparecer, casado por nome, o sistema já grava o IDUsuário dele.
- Leitura real de arquivos XLS/XLSX (competência, funcionários, dias e batidas), alimentando o motor de sugestão de turno e o painel de revisão.
- Sugestão automática de Setor a partir do campo "Dep." da planilha, com comparação tolerante a maiúsculas/minúsculas, acentos e espaços extras.
- **Setores novos:** quando a planilha traz um "Dep." que ainda não tem Setor cadastrado, o sistema pergunta antes de continuar — o usuário escolhe quais criar automaticamente, e a importação segue sem precisar ser refeita.

---

## Cadastro de Setores

Permite organizar a empresa em setores (ex.: Produção, Expedição, Administrativo), para uso futuro no vínculo com funcionários, filtros, estatísticas, gráficos e relatórios.

- Adicionar, editar, ativar/inativar e excluir setores.
- Cada setor possui nome, cor (opcional) e status.
- Exclusão só é permitida quando não há funcionários vinculados ao setor.
- Persistido em `dados/setores.json`, com backup automático.
- Também podem ser criados automaticamente durante a importação da planilha (ver Cadastro Inteligente Assistido de Funcionários) — sem distinção depois de criados, administrados normalmente por aqui.

---

## Configuração Inicial

Na primeira execução:

- Nome da empresa
- Logo
- Turnos
- Tolerâncias (Entrada, Saída para o Almoço, Retorno do Almoço, Saída Final — todas
  independentes, configuráveis e opcionais)
- Pasta do histórico

As configurações ficam salvas e podem ser alteradas posteriormente pela tela de Configurações.

---

## Processamento

Calcular automaticamente:

- Horas trabalhadas
- Horas extras
- Horas negativas
- Saldo diário

Aplicando todas as regras configuradas.

---

## Tratamento de Pendências

Detectar automaticamente:

- Funcionários sem batidas
- Batidas incompletas (uma, duas, três ou mais de quatro)
- Horários inconsistentes
- Turno não definido

Corrigir batida a batida, com justificativa e observações — ou usar
**Aplicar Justificativa por Período** para resolver vários dias de uma
vez (ex.: Férias, Licença, Atestado Médico): escolhe o funcionário, a
justificativa e o período, mostra um resumo antes de aplicar e trata
dias já justificados com outra coisa (substituir, manter ou perguntar
um a um). Quando a justificativa é **Desligamento**, o período restante
da competência é preenchido automaticamente e, ao confirmar, o sistema
pergunta se o funcionário deve ser marcado como Inativo.

Se, ao final do cálculo, não houver nenhuma pendência em aberto, a Tela
de Pendências é pulada automaticamente e o sistema vai direto para a
Tela de Relatórios.

---

## Relatórios

Tela dedicada ("Relatórios"), acessível pela Tela Inicial, com um
seletor de **período** (Mês completo ou intervalo personalizado, com
atalhos para Hoje/Esta Semana/Quinzena — v2.0), filtros por
Funcionário, Setor, Turno, Cargo e Status, e os novos filtros por
Situação, Pendências, Horas Extras e Banco de Horas (v2.0, todos
combináveis entre si), resumo superior
(Funcionários/Horas Extras/Horas Negativas/Pendências) e os botões
Visualizar, Exportar Excel e Imprimir.

A geração é bloqueada enquanto existir qualquer pendência em aberto no
recorte selecionado (não na competência inteira — v2.0).

Relatório Geral da Competência: um único arquivo Excel com 5 abas:

### Aba 1

Relatório Diário.

### Aba 2

Resumo Mensal.

### Aba 3

Pendências.

### Aba 4

Informações do Processamento (inclui Estatísticas da Competência).

### Aba 5 (v2.0)

Dashboard: indicadores gerais, ranking de horas extras e de horas
negativas por funcionário, distribuição do banco de horas e gráficos
nativos do Excel (sem nenhuma dependência nova).

Também é possível gerar um **Relatório Individual por Funcionário**
(cabeçalho + tabela diária + resumo do funcionário) e o **Resumo
Geral da Competência** é exibido tanto na tela quanto na Aba 4.

O Excel gerado é totalmente editável e tem formatação profissional
para conferência e impressão: cabeçalho em destaque, painel congelado,
bordas, largura de coluna ajustada ao conteúdo e layout em paisagem
pronto para impressão.

---

## Gerenciamento de Múltiplas Competências

Cada planilha importada cria (ou **atualiza incrementalmente**, v2.0)
uma **Competência** (mês/ano), persistida em disco imediatamente após
o Motor de Cálculo processar o lote — funcionários, pendências,
justificativas já preenchidas, resumo mensal, estatísticas e status.
Fechar o sistema a qualquer momento nunca perde esse trabalho.

- **Importação semanal incremental (v2.0):** o RH pode exportar a
  mesma planilha (com o layout do mês inteiro) toda semana — reimportar
  um mês já existente nunca substitui nem duplica nada: cada dia é
  comparado individualmente, dias iguais não são tocados, dias novos
  são adicionados, dias diferentes são atualizados. Um dia com batida
  corrigida manualmente ou pendência já resolvida/justificada nunca é
  sobrescrito por uma nova importação.
- Tela dedicada ("Competências"), com um card por competência: data da
  importação, quantidade de funcionários, quantidade de importações
  recebidas, quantidade de pendências (total e resolvidas), status
  detalhado, selo simplificado (🟢 Em andamento / 🟡 Aguardando
  pendências / 🔴 Fechada) e se já foi gerado relatório.
- **Retomar trabalho:** o botão "Abrir" leva direto às pendências
  restantes (justificativas já aplicadas preservadas) ou, se não
  houver mais nenhuma pendência em aberto, direto para a Tela de
  Relatórios.
- **Múltiplas competências coexistem** de forma totalmente
  independente — a Tela de Relatórios lista todas e gera o relatório
  de qualquer uma sem afetar as demais.
- **Fechar/Reabrir (v2.0):** uma competência fechada exige confirmação
  extra antes de aceitar uma nova importação — protege competências já
  fechadas contra atualização acidental.
- **Arquivar:** muda o status manualmente; a competência continua
  disponível na Tela de Relatórios (sem ação de Desarquivar nesta
  versão) — conceito independente de Fechar/Reabrir.
- **Histórico e Auditoria (v2.0):** botão "Histórico" no card mostra
  todas as importações recebidas (data/hora, usuário, arquivo,
  registros adicionados/alterados) e o log de auditoria de correções
  manuais (quem — usuário do Windows —, quando, o quê, valor anterior e
  valor novo).

---

## Dashboard (v2.0)

Tela dedicada ("Dashboard"), acessível pela Tela Inicial, com a
competência selecionável e:

- Cards: Total de Funcionários, Horas Trabalhadas, Horas Extras, Horas
  Negativas, Banco de Horas, Pendências, Dias Processados e
  Competência.
- Tabelas ordenadas: Horas Extras por Funcionário, Horas Negativas por
  Funcionário, Pendências por Dia, Horas Extras por Dia, Ranking de
  Horas Extras (Top 10), Ranking de Atrasos (Top 10 — dias com
  Situação "Hora Negativa") e Banco de Horas (saldo por funcionário).

Sem gráficos de imagem — tabelas numéricas ordenadas, mantendo o
instalador leve e sem dependências novas. O mesmo conjunto de
indicadores/rankings/distribuição também está disponível na Aba 5
("Dashboard") do Relatório Geral em Excel, com gráficos nativos do
Excel.

---

## Histórico

Salvar automaticamente todos os relatórios organizados por:

```
Historico/
Ano/
Mês/
```

Nunca substituir arquivos existentes.

---

## Logs

Registrar automaticamente:

- Data
- Hora
- Arquivo processado
- Quantidade de funcionários
- Pendências
- Erros
- Relatório gerado

---

# Interface

Interface moderna utilizando CustomTkinter.

Menus:

- Selecionar Planilha
- Processar
- Funcionários
- Setores
- Competências
- Relatórios
- Configurações
- Histórico
- Sobre

---

# Fluxo do Sistema

```
Selecionar planilha

↓

Leitura automática

↓

Cadastro inteligente (Painel de Revisão, com Status Ativo/Inativo)

↓

Validação

↓

Cálculo

↓

Competência persistida em disco (dados/competencias/)

↓

Pendências (pulado automaticamente se não houver nenhuma)

↓

Relatório Excel

↓

Histórico

↓

Fim
```

---

# Objetivo da Versão 1.0

Implementar um sistema totalmente funcional para automatizar o processamento diário da folha de ponto da Qualimix.

---

# Objetivo da Versão 1.1

Completar as tolerâncias de jornada: além de Entrada e Retorno do Almoço (já existentes
desde a v1.0), implementadas também as tolerâncias de **Saída para o Almoço** e **Saída
Final** — todas independentes, configuráveis e opcionais, seguindo exatamente a mesma
regra de faixa de aceitação (Capítulo 8 da especificação). Nenhuma regra de negócio
anterior foi alterada; configurações antigas continuam funcionando normalmente (as duas
novas tolerâncias entram desativadas por padrão). Ver `CHANGELOG.md` para detalhes.

---

# Objetivo da Versão 1.1.1

Correção definitiva de um bug visual da Wizard de configuração inicial: a etapa de
Tolerâncias (introduzida na v1.1) ficava encoberta pela etapa anterior (Turnos) devido
ao uso de um container de rolagem incompatível com a navegação por `tkraise()` desta
tela. Corrigido usando o mesmo tipo de container das demais etapas — nenhuma regra de
cálculo, configuração ou persistência foi alterada. Ver `CHANGELOG.md` para detalhes.

---

# Objetivo da Versão 2.0

Evoluir o sistema para o fluxo real do RH da Qualimix: a planilha é exportada
**semanalmente**, sempre com o layout do mês inteiro, mas só com os dias já
ocorridos preenchidos. O QualiPonto passa a **atualizar** a mesma competência
incrementalmente a cada importação (nunca substituindo nada), com proteção
automática de correções manuais, histórico de importações, auditoria,
fechamento de competência, relatórios por período, novos filtros e um
Dashboard (in-app e no Excel). Nenhuma regra de cálculo, tela ou relatório
existente foi removida ou alterada — apenas estendida. Ver `CHANGELOG.md`
para detalhes.

---

# Futuras Versões

- Estatísticas avançadas / análises comparativas entre competências
- Banco de dados
- Integração com relógio de ponto
- Relatórios PDF

---

# Licença

Sistema interno da Qualimix.

Desenvolvimento:

Nathan Adrian.