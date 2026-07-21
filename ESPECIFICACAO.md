ESPECIFICAÇÃO OFICIAL
QualiPonto — Sistema de Controle de Jornada e Horas Extras
Versão 2.0

Autor: Nathan Adrian

CAPÍTULO 1
VISÃO GERAL DO SISTEMA
1.1 Objetivo

O QualiPonto é um sistema desktop desenvolvido para automatizar completamente o processamento das folhas de ponto dos colaboradores da empresa.

O sistema deverá eliminar o trabalho manual atualmente realizado pelo setor responsável, reduzindo erros, aumentando a velocidade do processamento e padronizando a geração dos relatórios.

O processamento deverá ocorrer a partir da planilha exportada pelo sistema de ponto da empresa.

A planilha original nunca deverá ser alterada.

Todo o processamento ocorrerá em memória.

Ao final será gerado um novo arquivo Excel contendo os cálculos e informações necessárias.

1.2 Objetivos Específicos

O sistema deverá:

Ler automaticamente planilhas XLS e XLSX.
Identificar automaticamente o mês e o ano da competência.
Identificar automaticamente todos os funcionários.
Ler todas as batidas de ponto.
Detectar inconsistências.
Calcular automaticamente horas trabalhadas.
Calcular automaticamente horas extras.
Calcular automaticamente horas negativas.
Gerar relatório profissional.
Salvar histórico.
Registrar logs.
1.3 Público-alvo

O sistema será utilizado por:

Recursos Humanos
Administração
Gerência

Não exige conhecimento técnico.

1.4 Requisitos Gerais

O sistema deverá funcionar:

Offline.
Em Windows 10.
Em Windows 11.
Sem necessidade de banco de dados.
Sem necessidade de internet.

Todas as informações deverão permanecer armazenadas localmente.

1.5 Tecnologias

O projeto utilizará exclusivamente:

Python 3.13
CustomTkinter
Pandas
OpenPyXL
xlrd
Pillow
JSON
PyInstaller
Git
GitHub
CAPÍTULO 2
ARQUITETURA DO SISTEMA

O sistema será dividido em módulos independentes.

Cada módulo terá apenas uma responsabilidade.

A comunicação ocorrerá através de estruturas de dados padronizadas.

Nenhum módulo poderá acessar diretamente outro módulo sem utilizar sua interface pública.

Módulos
main.py

Responsável pela inicialização.

interface.py

Responsável pela interface gráfica.

config.py

Responsável pelas configurações.

leitor_ponto.py

Responsável pela leitura da planilha.

calculadora.py

Responsável pelos cálculos.

relatorio.py

Responsável pela geração do Excel.

Fluxo Geral
Usuário

↓

Seleciona a planilha

↓

Leitor da planilha

↓

Validação

↓

Cadastro Inteligente

↓

Pendências

↓

Correções

↓

Motor de cálculo

↓

Relatório Excel

↓

Salvar Histórico

↓

Fim
CAPÍTULO 3
ESTRUTURA DA PLANILHA
3.1 Formatos aceitos

O sistema deverá aceitar:

XLS
XLSX
3.2 Estrutura

Após análise da planilha oficial da Qualimix, foi identificado que cada funcionário ocupa um bloco composto por três linhas.
Linha 1

IDUsuário

Nome

↓

Linha 2

Dias do mês

↓

Linha 3

Batidas de ponto
Cada bloco deverá ser identificado automaticamente.
3.3 Identificação do Funcionário

Cada funcionário será identificado por:

IDUsuário
Nome

O nome será utilizado para exibição.

O ID será utilizado como identificador interno.

3.4 Dias

A segunda linha do bloco contém todos os dias do mês.

Exemplo: 1 2 3 4 5 6 7 ...
Esses valores deverão ser convertidos para datas completas utilizando o mês e o ano da competência.
3.5 Batidas

Cada célula poderá conter:

nenhuma batida;
uma batida;
duas batidas;
três batidas;
quatro batidas;
ou mais de quatro batidas.

As batidas estarão separadas por quebra de linha.

Exemplo:
 07:22

 13:47

 14:37

 17:14
 O sistema deverá separar automaticamente essas batidas em uma lista.
 3.6 Competência

O sistema deverá localizar automaticamente:

mês;
ano.

Com essas informações será possível montar a data completa de cada registro.

Exemplo:
Dia 15

↓

Julho

↓

2026

↓

15/07/2026
3.7 Calendário Inteligente

Após montar cada data, o sistema deverá calcular automaticamente o dia da semana.

Não será permitido informar isso manualmente.

Exemplo:
15/07/2026

↓

Quarta-feira
A partir disso serão aplicadas automaticamente todas as regras da jornada
3.8 Regras Automáticas

Segunda a sexta:

Esperado:

4 batidas.

Sábado e Domingo:

Não existe mais uma regra fixa de quantidade de batidas ou de hora
extra automática para estes dias. O que é esperado em cada um depende
exclusivamente da jornada configurada no Turno do funcionário
(Capítulo 4.6) — ver o detalhamento completo nos Capítulos 6.4
(Sábado), 6.5 (Domingo) e 7.3 (Duas Batidas).

Fim da Parte 1
# CAPÍTULO 4

# PRIMEIRA CONFIGURAÇÃO

## 4.1 Objetivo

Na primeira execução, o sistema deverá realizar uma configuração inicial guiada.

Essa configuração será executada apenas uma vez.

Todas as informações deverão ser armazenadas em arquivos JSON dentro da pasta "dados".

O usuário poderá alterar essas informações posteriormente através da tela Configurações.

---

## 4.2 Nome da Empresa

O sistema deverá solicitar:

Nome da empresa.

Exemplo:

Qualimix Pescados

Esse nome será utilizado:

- Tela principal.
- Relatórios.
- Sobre o sistema.

---

## 4.3 Logo da Empresa

O usuário poderá selecionar uma imagem.

Formatos aceitos:

- PNG
- JPG
- JPEG
- BMP
- WEBP

A logo será utilizada:

- Tela inicial.
- Tela Sobre.
- Relatórios.

A imagem será copiada automaticamente para:

assets/logo

Não será utilizada a imagem original.

---

## 4.4 Seleção da Primeira Planilha

Após informar os dados da empresa.

O sistema solicitará a primeira planilha.

Essa planilha será utilizada para:

- Identificar funcionários.
- Identificar a competência.
- Identificar os turnos.

---

## 4.5 Cadastro Inicial

Após ler a primeira planilha.

O sistema deverá cadastrar automaticamente todos os funcionários encontrados.

Nenhum cadastro será digitado manualmente.

---

## 4.6 Definição dos Turnos

Cada Turno cadastrado deverá ter jornada independente para três tipos
de dia: Segunda a Sexta, Sábado e Domingo — para que o motor de
cálculo (Capítulo 6) saiba exatamente o que é esperado em cada um,
sem depender de uma regra fixa igual para todos os turnos.

**Segunda a Sexta** — sempre obrigatória. Campos:

Entrada

Saída

Início do intervalo

Fim do intervalo

**Sábado** — opcional, controlado por um checkbox "Trabalha sábado":

Desmarcado: nenhum campo de horário é exibido nem validado — o turno
simplesmente não prevê trabalho aos sábados.

Marcado: exibe Entrada, Saída e um checkbox "Possui intervalo".
Entrada e Saída passam a ser obrigatórios. Se "Possui intervalo"
estiver marcado, exibe também Início e Fim do intervalo (também
obrigatórios); caso contrário, o sábado é tratado como um dia sem
horário de almoço.

**Domingo** — exatamente o mesmo comportamento do Sábado: checkbox
"Trabalha domingo", Entrada, Saída, checkbox "Possui intervalo" e
intervalo opcional.

Em qualquer um dos três tipos de dia, a jornada prevista (Capítulo
10.1) é calculada automaticamente a partir dos horários preenchidos,
sempre que algum deles for alterado. Exemplo de exibição:

Segunda a Sexta — Jornada: 8h00

Sábado — Jornada: 5h30

Domingo — Não trabalha

Ao selecionar um Turno na lista de funcionários (importação ou
cadastro manual, Capítulo 5), o vínculo continua sendo feito apenas
pelo Turno como um todo — nunca pelo dia da semana isoladamente.

---

## 4.7 Tolerâncias de Jornada

O sistema perguntará, para cada um dos quatro pontos da jornada —
**Entrada**, **Saída para o Almoço**, **Retorno do Almoço** e **Saída
Final** —, de forma totalmente independente:

Deseja utilizar tolerância para [ponto]?

○ Sim

○ Não

Caso Sim.

Informar quantidade de minutos.

Exemplo.

5 minutos.

Cada tolerância é opcional e configurável separadamente — ativar uma
não exige ativar as demais. Todas as quatro serão aplicadas
automaticamente durante os cálculos (Capítulo 8).

---

## 4.8 Finalização

Após concluir todas as etapas.

O sistema criará automaticamente:

dados/configuracoes.json

dados/funcionarios.json

A configuração inicial será considerada concluída.

Ela não deverá ser exibida novamente.

---

# CAPÍTULO 5

# CADASTRO INTELIGENTE ASSISTIDO DE FUNCIONÁRIOS

## 5.1 Objetivo

A principal forma de cadastrar funcionários é a importação da planilha
do ponto eletrônico. O sistema deverá identificar automaticamente os
funcionários encontrados, criar o cadastro básico de cada um, detectar
o horário de entrada predominante e sugerir automaticamente o turno
mais compatível.

O cadastro manual continua existindo, como complemento — nunca como
substituto da importação. É utilizado para:

Cadastrar funcionários antes da primeira importação.

Adicionar funcionários que ainda não aparecem na planilha.

Corrigir qualquer informação.

Cadastrar funcionários temporários.

Nesta fase (Sprint 3), a leitura definitiva de arquivos XLS/XLSX ainda
não é implementada (Sprint 3.5). Todo o mecanismo de identificação
automática, sugestão de turno e painel de revisão deverá ser construído
e testado com dados simulados, de forma que a leitura real da planilha
apenas alimente esse mecanismo já pronto, sem necessidade de
refatoração.

---

## 5.2 Primeira Importação

Quando o usuário importar a primeira planilha (Sprint 3.5), o sistema
deverá, para cada funcionário encontrado:

1. Identificar automaticamente o funcionário.

2. Criar automaticamente o cadastro básico (Nome utilizado na Planilha
   e, inicialmente, Nome Completo igual a ele).

3. Detectar o horário de entrada predominante do funcionário.

4. Comparar esse horário com todos os Turnos cadastrados (Capítulo
   4.6).

5. Sugerir automaticamente o turno mais compatível.

6. Marcar essa sugestão como:

✓ Confirmado — quando a identificação for suficientemente confiável.

⚠ Revisar — quando houver dúvida (nenhum turno compatível o suficiente,
ou mais de um turno igualmente compatível).

7. Preencher automaticamente todas as informações possíveis.

8. Deixar pendente apenas o que realmente precisa de decisão do
   usuário — no mínimo, Cargo e Setor, que não podem ser inferidos
   automaticamente.

---

## 5.3 Cadastro Assistido

Após a importação, o usuário apenas complementa:

Cargo.

Setor.

Demais informações administrativas (Apelido, Matrícula, CPF), quando
aplicável.

Todo o restante deverá já estar preenchido automaticamente sempre que
possível.

---

## 5.4 Painel de Revisão

Antes da conclusão da importação, o sistema deverá exibir um painel de
revisão com uma linha por funcionário identificado:

Funcionário — Horário encontrado — Turno sugerido — Situação — Status

Exemplo:

João — 07:29 — Produção — ✓ Confirmado — ☑ Ativo

Maria — 07:31 — Produção — ✓ Confirmado — ☑ Ativo

Carlos — 08:42 — Nenhum — ⚠ Revisar — ☑ Ativo

Pedro — 06:02 — Motoristas — ✓ Confirmado — ☐ Inativo

Somente os casos marcados como "⚠ Revisar" deverão exigir intervenção
do usuário antes de concluir a importação. Os casos "✓ Confirmado"
prosseguem automaticamente.

**Status (Ativo/Inativo)**: cada linha traz um checkbox de Status,
marcado como Ativo por padrão. Se o funcionário já existir no cadastro
como Inativo, a linha chega desmarcada (Inativo), refletindo o estado
atual — sem reativação automática (isso permanece uma decisão
manual). Ao concluir a importação (Capítulo 5.7):

Funcionários marcados como Ativo — cadastrados normalmente, enviados
ao Motor de Cálculo (Capítulo 6), podem gerar Pendências (Capítulo 9)
e aparecem nos Relatórios (Capítulo 11) desta competência.

Funcionários marcados como Inativo — cadastrados/atualizados
normalmente (permanecem no cadastro, com status = Inativo), mas NÃO
são enviados ao Motor de Cálculo, NÃO geram Pendências e NÃO aparecem
nos Relatórios desta competência.

---

## 5.5 Reconhecimento Automático de Turno

A planilha contém o horário de entrada de cada funcionário. O sistema
deverá comparar esse horário com o horário de entrada de cada Turno
cadastrado e sugerir automaticamente aquele cuja entrada estiver mais
próxima.

Exemplo:

Turno A tem entrada às 07:30.

Funcionário registrou entrada às 07:29.

Sugestão automática: Turno A (✓ Confirmado).

Caso o horário encontrado não esteja suficientemente próximo de nenhum
turno cadastrado, ou esteja igualmente próximo de mais de um, a
sugestão deverá ser marcada como "⚠ Revisar", sem turno pré-selecionado
automaticamente.

---

## 5.6 Importações Futuras

Em importações seguintes (após a primeira), o sistema deverá:

Reconhecer automaticamente os funcionários já cadastrados (Capítulo
5.8).

Reconhecer alterações no horário de entrada (podendo sugerir revisão
do turno, caso o padrão tenha mudado).

Identificar novos funcionários (ainda não cadastrados).

Identificar possíveis conflitos (ex.: nome da planilha correspondendo
a mais de um cadastro).

Nunca duplicar um funcionário já existente.

Respeitar em todos os casos a regra de Importação Parcial (Capítulo
5.7).

---

## 5.7 Importação Parcial

O sistema nunca deverá assumir que uma planilha importada contém todos
os funcionários da empresa.

Uma importação poderá representar:

Toda a empresa.

Apenas um setor.

Apenas um período.

Apenas alguns funcionários.

Portanto, em toda importação (primeira ou seguintes):

Funcionários que não aparecerem na planilha importada NÃO deverão ser
excluídos.

Funcionários que não aparecerem NÃO deverão ser inativados
automaticamente.

Funcionários que não aparecerem NÃO deverão perder seus vínculos com
Turnos ou Setores.

O sistema deverá atualizar apenas os funcionários encontrados na
importação.

Novos funcionários encontrados deverão ser adicionados normalmente
(Capítulo 5.2).

Alterações deverão ser aplicadas apenas aos funcionários presentes na
planilha importada.

Exemplo:

Cadastro atual: 150 funcionários.

Importação realizada: 30 funcionários.

Resultado esperado:

Atualizar os 30 encontrados.

Adicionar novos funcionários, caso existam.

Manter os outros 120 exatamente como estão.

Nunca interpretar ausência na planilha como desligamento.

Esta regra prevalece sobre qualquer outra leitura possível dos
Capítulos 5.2, 5.6 e 5.11 — a ausência de um funcionário numa
importação nunca é, por si só, motivo para alterar seu cadastro.

---

## 5.8 Localização Automática na Leitura da Planilha

Identificador principal: o **IDUsuário** lido de cada bloco da planilha
(Capítulo 3.3) — não o nome. Para localizar o funcionário correspondente
a uma linha da planilha, o sistema deverá utilizar, nesta ordem:

1. O IDUsuário, comparado com o campo "IDUsuário" salvo em cada
   funcionário cadastrado (Capítulo 5.14). Casamento exato — nunca
   casa dois IDUsuário vazios entre si.

2. Caso o cadastro correspondente ainda não tenha um IDUsuário salvo
   (cadastro anterior a esta funcionalidade, ou criado manualmente),
   cai para o casamento por nome de sempre: "Nome utilizado na
   Planilha", se preenchido, senão o "Nome Completo". Esse casamento
   por nome funciona como **migração automática**: assim que encontra
   o cadastro por nome, o sistema grava o IDUsuário daquela linha no
   cadastro — nas importações seguintes, esse funcionário já passa a
   ser localizado diretamente pelo IDUsuário, sem depender do nome
   novamente. Não existe tela ou rotina separada de migração; ela
   acontece sozinha, na primeira importação em que o funcionário
   reaparecer.

Se nenhum funcionário cadastrado corresponder (nem por IDUsuário, nem
por nome), ele deverá ser tratado como um novo funcionário (Capítulo
5.2), nunca como uma pendência silenciosa.

Isso é o que permite diferenciar corretamente dois funcionários reais
com exatamente o mesmo nome (homônimos): tendo IDUsuário diferente na
planilha, eles chegam ao Painel de Revisão (Capítulo 5.4) como duas
linhas distintas — cada uma mostrando o próprio IDUsuário como
subtítulo, para o usuário conseguir diferenciá-las visualmente — e
geram dois cadastros separados, cada um com seus próprios dias e
batidas, nunca misturados entre si.

---

## 5.9 Cadastro Manual

O cadastro manual continua disponível a qualquer momento, como
complemento à importação (Capítulo 5.1). Pela Tela de Funcionários, o
usuário poderá:

Adicionar funcionário.

Editar funcionário.

Excluir funcionário.

Ativar/Inativar funcionário.

Cadastrar funcionários antes da primeira importação.

Cadastrar funcionários temporários (que nunca aparecerão na planilha).

Corrigir qualquer informação, a qualquer momento.

---

## 5.10 Ações em Massa

A Tela de Funcionários deverá permitir selecionar múltiplos
funcionários (ou todos) simultaneamente, e aplicar em lote:

Alterar Turno.

Alterar Setor.

Alterar Cargo.

Ativar.

Inativar.

Ações em massa são sempre um comando explícito do usuário sobre os
funcionários selecionados — nunca um efeito colateral de uma
importação (Capítulo 5.7).

---

## 5.11 Funcionário sem Horários

Caso um funcionário apareça na planilha sem nenhuma batida.

O sistema deverá mostrar.

------------------------------------------------

Funcionário:

Arthur Lima

Nenhuma batida encontrada.

Selecione o motivo.

☐ Falta

☐ Falta Justificada

☐ Férias

☐ Folga

☐ Afastamento

☐ Licença

☐ Licença Médica

☐ Desligamento

☐ Outro

Observação:

__________________________

[ Confirmar ]

------------------------------------------------

Essa informação deverá ser gravada no relatório.

---

## 5.12 Funcionário Não Encontrado na Planilha

Caso um funcionário cadastrado deixe de aparecer na planilha importada.

Nenhuma alteração deverá ser realizada automaticamente — nem exclusão,
nem inativação, nem perda de vínculo com Turno ou Setor (Capítulo 5.7,
Importação Parcial).

O cadastro permanecerá exatamente como estava.

O sistema apenas registrará essa ocorrência nos logs.

---

## 5.13 Alteração de Turno ou Setor

A qualquer momento, pela Tela de Funcionários, o usuário poderá alterar
o Turno e/ou o Setor de um funcionário, sempre por seleção em lista —
nunca por texto digitado. O mesmo vale para alterações em massa
(Capítulo 5.10).

O vínculo é sempre por ID. Alterar o nome de um Turno ou de um Setor
nunca quebra o vínculo já existente com os funcionários (Capítulo 21.4).

---

## 5.14 Estrutura do Cadastro

Cada funcionário possuirá:

ID (UUID gerado automaticamente, nunca editável).

Nome Completo (obrigatório).

Nome utilizado na Planilha (opcional — se vazio, a localização
automática do Capítulo 5.8 utilizará o Nome Completo).

IDUsuário (identificador principal da planilha, Capítulo 5.8 — vazio
em cadastros anteriores a esta funcionalidade, até a migração
automática na próxima importação em que o funcionário reaparecer).

Apelido (opcional).

Matrícula (opcional).

CPF (opcional).

Cargo (obrigatório).

Turno (vínculo obrigatório por ID — Capítulo 4.6).

Setor (vínculo obrigatório por ID — Capítulo 21).

Status (Ativo/Inativo).

Data de Cadastro.

Última Atualização.

Não é permitido cadastrar dois funcionários com o mesmo Nome Completo.

Tudo armazenado em:

dados/funcionarios.json

---

## 5.15 Atualização Automática

Sempre que o sistema criar (via importação) ou o usuário adicionar ou
editar um funcionário.

O sistema deverá atualizar automaticamente a "Última Atualização".

Sem necessidade de nenhuma ação extra do usuário.

---

## 5.16 Reconhecimento Automático de Setor

Além do horário de entrada (Capítulo 5.5), a planilha do ponto também
traz o campo "Dep." (departamento) de cada funcionário.

O sistema deverá comparar esse valor com o nome de cada Setor já
cadastrado (Capítulo 21), de forma tolerante a diferenças de
maiúsculas/minúsculas, acentuação e espaços extras no início, no fim
ou entre palavras.

Exemplos considerados equivalentes:

"PRODUCAO" = "Produção"

" logistica " = "Logística"

"RH" = "rh"

Regras de sugestão:

Exatamente um Setor cadastrado corresponde ao "Dep." encontrado ->
sugestão automática desse Setor (✓ Confirmado).

Mais de um Setor cadastrado corresponde de forma equivalente
(ambiguidade) -> ⚠ Revisar, sem impedir o usuário de escolher
manualmente.

Nenhum Setor cadastrado corresponde -> ⚠ Revisar, sem Setor
pré-selecionado (ver também Capítulo 5.17).

O Painel de Revisão (Capítulo 5.4) deverá permitir corrigir
manualmente o Setor sugerido, da mesma forma que já permite corrigir
o Turno.

---

## 5.17 Criação Automática de Setores Não Cadastrados

Os Setores deixam de ser um pré-requisito obrigatório para a
importação. O sistema não deverá exigir que todos os Setores
existentes na planilha já estejam cadastrados antes de importar.

Durante o processamento de uma planilha, o sistema deverá:

1. Ler todos os valores distintos do campo "Dep." encontrados na
planilha.

2. Comparar cada um com os Setores já cadastrados, usando a mesma
comparação tolerante do Capítulo 5.16.

3. Identificar quais desses valores não correspondem a nenhum Setor
já cadastrado ("Setores novos").

Caso existam Setores novos, antes de exibir o Painel de Revisão
(Capítulo 5.4), o sistema deverá exibir uma tela informando:

"Foram encontrados novos setores na planilha."

Com uma lista de checkboxes, uma linha por Setor novo, todos
pré-marcados, mostrando também quantos funcionários da planilha
pertencem a cada um (para o usuário confirmar rapidamente se o
reconhecimento está correto). Exemplo:

☑ Produção (26 funcionários)

☑ Logística (8 funcionários)

☑ RH (4 funcionários)

☑ Motoristas (2 funcionários)

E dois botões:

[ Criar selecionados ] — cria automaticamente cada Setor novo que
permanecer marcado.

[ Ignorar ] — não cria nenhum Setor novo nesta importação; os "Dep."
correspondentes permanecem sem Setor cadastrado (⚠ Revisar).

Cada Setor criado por esta tela deverá seguir exatamente a estrutura
do Capítulo 21.2:

ID gerado automaticamente.

Nome = o valor do "Dep." encontrado na planilha, com a grafia
normalizada para uma apresentação amigável — nunca gravado tal como
foi digitado na planilha quando isso resultar em texto todo em
maiúsculas, todo em minúsculas ou sem acentuação. Exemplos:

"PRODUCAO" ou "producao" -> "Produção"

"LOGISTICA" ou "logistica" -> "Logística"

"MOTORISTAS" -> "Motoristas"

"RH" -> "RH" (siglas permanecem em maiúsculas)

O matching tolerante (Capítulo 5.16) continua funcionando normalmente
sobre o valor original lido da planilha — apenas a apresentação do
Setor salvo no cadastro é normalizada.

Cor = vazia (o usuário poderá definir depois, pela Tela de
Gerenciamento de Setores, Capítulo 21.3).

Status = Ativo.

Os Setores criados deverão ser persistidos imediatamente em
dados/setores.json (Capítulo 21.6), usando o mesmo mecanismo de
leitura/escrita/backup já existente — nenhum novo mecanismo de
persistência deverá ser criado.

Após criar os Setores selecionados (ou após "Ignorar"), a importação
deverá continuar automaticamente, sem exigir nenhuma ação adicional
do usuário.

A sugestão automática de Setor (Capítulo 5.16) desta mesma importação
deverá considerar também os Setores recém-criados — um "Dep." que
corresponda a um Setor recém-criado deverá aparecer no Painel de
Revisão já como ✓ Confirmado, sem exigir uma segunda importação.

Esta tela é exclusiva do fluxo de importação. A administração
completa de Setores (renomear, alterar cor, ativar/inativar, excluir)
continua sendo feita apenas pela Tela de Gerenciamento de Setores
(Capítulo 21.3).
# CAPÍTULO 6

# MOTOR DE CÁLCULO

## 6.1 Objetivo

O Motor de Cálculo é o núcleo do sistema.

Ele será responsável por analisar todas as batidas de ponto, aplicar as regras da empresa e gerar o saldo diário de cada funcionário.

Nenhum cálculo será realizado pela interface.

Toda regra deverá ficar centralizada neste módulo.

---

## 6.2 Ordem de Processamento

O sistema deverá seguir obrigatoriamente esta sequência.

Selecionar planilha

↓

Ler funcionários

↓

Ler dias

↓

Ler batidas

↓

Determinar o dia da semana

↓

Verificar pendências

↓

Aplicar tolerâncias

↓

Calcular jornada

↓

Calcular horas extras

↓

Calcular horas negativas

↓

Gerar saldo

↓

Enviar para o relatório

---

## 6.3 Segunda a Sexta

Para dias úteis o sistema espera:

4 batidas.

Entrada.

↓

Saída para almoço.

↓

Retorno do almoço.

↓

Saída.

Caso existam exatamente quatro batidas.

O cálculo deverá ocorrer normalmente.

---

## 6.4 Sábado

O sistema deverá identificar automaticamente os sábados pelo dia da
semana — isso nunca é configurado manualmente.

A jornada esperada do sábado passa a vir do Turno vinculado ao
funcionário (Capítulo 4.6), não mais de uma regra fixa igual para
todos:

Se o Turno do funcionário tiver jornada de Sábado configurada
(checkbox "Trabalha sábado" marcado): a jornada esperada é definida
pela Entrada/Saída (e, se houver, o Intervalo) daquele Turno —
inclusive a existência ou não de horário de almoço deixa de ser uma
regra fixa do sistema e passa a depender do checkbox "Possui
intervalo" de cada Turno.

Se o Turno do funcionário não tiver jornada de Sábado configurada: o
sábado é tratado como um dia sem jornada prevista.

O algoritmo exato de cálculo (Capítulo 10) a partir dessa jornada será
definido na implementação do Motor de Cálculo (Sprint 4) — este
capítulo só estabelece de onde vem o esperado do dia.

---

## 6.5 Domingo

O sistema deverá identificar automaticamente os domingos pelo dia da
semana — isso nunca é configurado manualmente.

A jornada esperada do domingo passa a vir do Turno vinculado ao
funcionário (Capítulo 4.6), da mesma forma que o Sábado (Capítulo
6.4):

Se o Turno do funcionário tiver jornada de Domingo configurada
(checkbox "Trabalha domingo" marcado): a jornada esperada é definida
pela Entrada/Saída (e, se houver, o Intervalo) daquele Turno.

Se o Turno do funcionário não tiver jornada de Domingo configurada:
todo horário registrado no domingo continua sendo considerado Hora
Extra, independentemente da quantidade de batidas — a regra original
deste capítulo permanece válida como comportamento padrão na ausência
de jornada de Domingo configurada.

O algoritmo exato de cálculo (Capítulo 10) para quando existe jornada
de Domingo configurada será definido na implementação do Motor de
Cálculo (Sprint 4).

---

## 6.6 Feriados

Nesta versão.

Os feriados não serão identificados automaticamente.

O tratamento será implementado em versões futuras.

---

# CAPÍTULO 7

# REGRAS DE BATIDAS

## 7.1 Quatro Batidas

Situação normal.

O sistema deverá calcular normalmente.

---

## 7.2 Três Batidas

O sistema deverá considerar como pendência.

O processamento continuará.

Será solicitado ao usuário informar a justificativa.

---

## 7.3 Duas Batidas

Segunda a sexta.

Pendência.

Sábado e Domingo.

Depende da jornada configurada no Turno do funcionário para aquele
dia (Capítulo 4.6/6.4/6.5): o critério exato de quando 2 batidas são
situação normal ou pendência para Sábado/Domingo será definido junto
com o Motor de Cálculo (Sprint 4).

---

## 7.4 Uma Batida

Sempre será considerada pendência.

---

## 7.5 Nenhuma Batida

O sistema abrirá automaticamente a janela de justificativa.

---

## 7.6 Mais de Quatro Batidas

Caso sejam encontradas cinco ou mais batidas.

O sistema deverá marcar como inconsistência.

O usuário decidirá como proceder.

---

# CAPÍTULO 8

# TOLERÂNCIAS

## 8.1 Entrada

Caso exista tolerância configurada, ela deverá ser aplicada
automaticamente como uma **faixa de aceitação** em torno do horário
previsto — tanto para atraso quanto para antecipação.

Exemplo:

Entrada prevista: 06:30

Tolerância: 5 minutos

Qualquer entrada registrada entre 06:25 e 06:35 (inclusive) deverá ser
considerada exatamente como 06:30 para efeito de cálculo — não apenas
"sem atraso", mas tratada como se tivesse batido exatamente no horário
previsto.

Fora da faixa de aceitação (ex.: 06:36, ou 06:24), o horário conta
**integralmente a partir do horário previsto** — nunca apenas o
excedente além da tolerância. Ou seja, uma entrada às 06:40 com
tolerância de 5 minutos gera 10 minutos de atraso (06:40 − 06:30), não
5 minutos (06:40 − 06:35).

---

## 8.2 Saída para o Almoço

A tolerância de saída para o almoço deverá funcionar exatamente da
mesma maneira (Capítulo 8.1), aplicada ao horário de saída para o
intervalo — faixa de aceitação em torno do horário previsto, e
contagem integral a partir do previsto quando fora da faixa. Só se
aplica em dias cuja jornada tenha intervalo definido (Capítulo 4.6).

Independente e configurável separadamente da tolerância de Entrada —
uma pode estar ativa sem a outra.

---

## 8.3 Retorno do Almoço

A tolerância de retorno do almoço deverá funcionar exatamente da mesma
maneira (Capítulo 8.1), aplicada ao horário de retorno do intervalo —
faixa de aceitação em torno do horário previsto, e contagem integral a
partir do previsto quando fora da faixa. Só se aplica em dias cuja
jornada tenha intervalo definido (Capítulo 4.6).

Independente e configurável separadamente das demais.

---

## 8.4 Saída Final

A tolerância de saída final deverá funcionar exatamente da mesma
maneira (Capítulo 8.1), aplicada ao horário de saída do dia — faixa de
aceitação em torno do horário previsto, e contagem integral a partir
do previsto quando fora da faixa. Aplica-se tanto a dias com intervalo
(a última das 4 batidas) quanto a dias sem intervalo (a última das 2
batidas).

Independente e configurável separadamente das demais.

---

## 8.5 Sem Tolerância

Caso a empresa não utilize tolerância.

O cálculo deverá utilizar exatamente os horários registrados.

---

# CAPÍTULO 9

# PENDÊNCIAS

## 9.1 Objetivo

O sistema nunca deverá parar o processamento.

Todas as pendências deverão ser resolvidas antes da geração do relatório.

---

## 9.2 Tipos

Pendências possíveis.

Funcionário novo.

Sem batidas.

Batidas incompletas.

Mais de quatro batidas.

Horário inconsistente.

Turno não definido — funcionário sem Turno vinculado (ou vinculado a
um Turno que não existe mais). Enquanto essa pendência não for
resolvida (Capítulo 5.13: sempre pela seleção de um Turno válido), o
Motor de Cálculo (Capítulo 6) não terá jornada prevista para calcular
nenhum dia desse funcionário.

---

## 9.3 Tela de Pendências

Antes do relatório.

O sistema exibirá uma tela contendo todas as pendências encontradas.

Cada pendência poderá ser resolvida individualmente, ou várias de uma
vez através de "Aplicar Justificativa por Período" (Capítulo 9.8).

**Fluxo inteligente**: se, ao final do Motor de Cálculo (Capítulo 6),
não existir nenhuma pendência em aberto, a Tela de Pendências é
desnecessária — o sistema vai direto para a Tela de Relatórios
(Capítulo 12.8). Só quando existir pelo menos uma pendência em aberto
a Tela de Pendências é exibida normalmente.

---

## 9.4 Batida Esquecida

Caso o usuário informe.

"Esqueceu de bater o ponto."

O sistema permitirá digitar manualmente o horário.

Exemplo.

Entrada

07:30

Saída almoço

12:00

Volta almoço

13:00

Saída

17:00

Após salvar.

O cálculo será atualizado automaticamente.

---

## 9.5 Alteração Manual

Toda alteração manual deverá ficar registrada.

No relatório.

Nos logs.

Com data e hora.

---

## 9.6 Justificativas

As justificativas disponíveis serão.

Falta.

Falta Justificada.

Férias.

Folga.

Licença.

Afastamento.

Atestado Médico.

Consulta Médica.

Serviço Externo.

Treinamento.

Desligamento.

Esqueceu de bater.

Ponto não registrou.

Outro.

Sempre permitir observações.

---

## 9.7 Justificativas e Horas Negativas

Quando a pendência de um dia for resolvida com uma Justificativa
(Capítulo 9.6), o efeito dessa justificativa sobre a Hora Negativa do
dia (Capítulo 10.3) depende de uma lista central e explícita —
elimina a hora negativa somente quando a justificativa está nessa
lista; qualquer justificativa fora dela mantém a hora negativa
normalmente. Isso evita que cada nova regra futura precise mexer no
motor de cálculo: basta incluir a justificativa na lista.

**Elimina a Hora Negativa do dia:**

Atestado Médico

Férias

Folga

Licença

**Não elimina a Hora Negativa do dia** (lista não-exaustiva —
qualquer justificativa não listada acima também não elimina):

Falta

Falta Justificada

Afastamento

Consulta Médica

Serviço Externo

Treinamento

Desligamento

Esqueceu de bater

Ponto não registrou

Outro

Um dia sem nenhuma justificativa informada (pendência ainda não
resolvida) também não elimina a Hora Negativa.

---

## 9.8 Aplicar Justificativa por Período

Ação disponível na Tela de Pendências (Capítulo 9.3) para aplicar a
mesma Justificativa (Capítulo 9.6) a vários dias de um funcionário de
uma só vez, em vez de repetir a correção dia a dia. Funciona para
qualquer Justificativa já existente (Capítulo 9.6) — não introduz
nenhuma justificativa nova; "Licença Maternidade"/"Licença
Paternidade" e equivalentes usam a Justificativa "Licença" já
existente.

**Campos**: Funcionário, Justificativa, Data Inicial, Data Final.

**Ao analisar o período**, cada dia do funcionário dentro do intervalo
é classificado, sem que nenhum valor seja alterado ainda:

Pendência sem Justificativa — será resolvida com a nova Justificativa.

Já justificado com a mesma Justificativa — sem alteração necessária.

Já justificado com outra Justificativa — conflito (Capítulo 9.8.1).

Sem pendência (dia já calculado normalmente) — sem alteração; a
Justificativa só pode ser aplicada a um dia que tenha uma pendência
associada (Capítulo 9.1), pelo mesmo mecanismo já usado na correção
individual (Capítulo 9.6).

### 9.8.1 Tratamento de Conflitos

Se algum dia do período já tiver outra Justificativa, o sistema
pergunta como proceder, antes de aplicar qualquer coisa:

Substituir as justificativas existentes desses dias pela nova.

Manter as justificativas existentes (esses dias ficam de fora da
aplicação).

Perguntar conflito por conflito (uma confirmação por dia conflitante).

### 9.8.2 Confirmação Inteligente

Antes de aplicar qualquer alteração, o sistema mostra um resumo
completo da operação: Funcionário, Justificativa, Período, Dias
analisados, Pendências que serão resolvidas, Dias já justificados,
Dias sem alteração, Conflitos encontrados e, quando a Justificativa
for "Desligamento" (Capítulo 9.8.3), se o funcionário será inativado.
Só depois de "Confirmar" a alteração é aplicada — "Cancelar" não
altera nada.

Cada dia efetivamente alterado é recalculado imediatamente (Capítulo
10.7), reaproveitando exatamente o mesmo mecanismo já usado na
correção individual de uma pendência — nenhuma regra de cálculo nova.

### 9.8.3 Desligamento Inteligente

Quando a Justificativa escolhida for "Desligamento": a Data Final é
preenchida automaticamente com o último dia da competência do
funcionário (o período restante), sem impedir o usuário de ajustá-la.
Depois de confirmar a aplicação, o sistema pergunta:

"O funcionário será desligado. Deseja também marcá-lo como Inativo?"

Se "Sim": o funcionário passa para Status = Inativo (Capítulo 5.4),
permanece cadastrado e não participa das próximas importações
enquanto permanecer Inativo — sem reativação automática (Capítulo
5.4).

---

# CAPÍTULO 10

# REGRAS DE CÁLCULO

## 10.1 Horas Trabalhadas

O sistema calculará automaticamente.

Entrada

↓

Saída Almoço

↓

Retorno

↓

Saída

Descontando automaticamente o intervalo.

---

## 10.2 Horas Extras

Todo tempo superior à jornada prevista será considerado Hora Extra.

---

## 10.3 Horas Negativas

Todo tempo inferior à jornada prevista será considerado Hora Negativa.

---

## 10.4 Saldo

Saldo = Horas Trabalhadas - Jornada Prevista

---

## 10.5 Domingo

Segue a mesma fórmula do Capítulo 10.4 (Saldo = Trabalhadas − Jornada
Prevista), usando a jornada de Domingo do Turno do funcionário
(Capítulo 6.5) como Jornada Prevista.

Quando o Turno não tiver jornada de Domingo configurada, a Jornada
Prevista é 0 — nesse caso o Saldo é sempre igual às Horas Trabalhadas
(nunca negativo) e, portanto, sempre Hora Extra (Capítulo 10.2), sem
necessidade de nenhuma regra especial além da fórmula do Capítulo
10.4.

Quando o Turno tiver jornada de Domingo configurada, o dia é calculado
normalmente como qualquer outro (podendo gerar Hora Extra ou Hora
Negativa, conforme o Saldo).

---

## 10.6 Sábado

Segue exatamente a mesma lógica do Domingo (Capítulo 10.5): a Jornada
Prevista vem da jornada de Sábado do Turno do funcionário (Capítulo
6.4). Sem jornada de Sábado configurada, a Jornada Prevista é 0 e o
dia é tratado como um dia sem jornada prevista (Capítulo 6.4) — não
gera Hora Negativa. Com jornada de Sábado configurada, o dia é
calculado normalmente.

---

## 10.7 Reprocessamento

Sempre que o usuário alterar qualquer horário.

O sistema deverá recalcular automaticamente.

Sem necessidade de processar novamente toda a planilha.
# CAPÍTULO 11

# GERAÇÃO DO RELATÓRIO

## 11.1 Objetivo

O QualiPonto nunca alterará a planilha oficial exportada pelo relógio de ponto.

A planilha original será utilizada exclusivamente para leitura dos dados.

Todo o resultado do processamento será gravado em um novo arquivo Excel, preservando a integridade do documento oficial.

---

## 11.2 Planilha Original

A planilha exportada pelo relógio de ponto é considerada um documento oficial da empresa.

Portanto:

• Nunca poderá ser alterada.

• Nunca poderá receber observações.

• Nunca poderá receber cálculos.

• Nunca poderá receber justificativas.

• Nunca poderá ser sobrescrita pelo sistema.

O sistema terá acesso somente para leitura.

---

## 11.3 Relatório Gerado

Após concluir o processamento, o sistema criará automaticamente um novo arquivo Excel.

Exemplo:

RegistroPresenca_Julho_2026.xls

↓

Relatorio_Horas_Julho_2026.xlsx

Este novo arquivo pertencerá exclusivamente ao sistema.

Todas as informações adicionais serão registradas nele.

---

## 11.4 Estrutura do Relatório

O relatório será composto por quatro abas.

---

### Aba 1

## Relatório Diário

Uma linha para cada funcionário.

Deverá conter:

• Funcionário

• Data

• Dia da Semana

• Turno

• Batidas (todos os horários registrados no dia, na ordem em que ocorreram)

• Jornada Prevista

• Horas Trabalhadas

• Horas Extras

• Horas Negativas

• Saldo

• Situação

• Justificativa (quando existir)

• Observações

---

### Aba 2

## Resumo Mensal

Uma linha para cada funcionário.

Mostrar:

• Dias Trabalhados

• Horas Trabalhadas

• Horas Extras

• Horas Negativas

• Saldo Final

• Quantidade de Pendências

---

### Aba 3

## Pendências

Esta aba servirá para conferência do RH.

Mostrar:

• Funcionário

• Data

• Tipo da Pendência

• Descrição

• Status

• Observações

Exemplos de pendências:

- Nenhuma batida registrada

- Apenas uma batida

- Apenas duas batidas

- Apenas três batidas

- Mais de quatro batidas

- Funcionário novo

- Horário inconsistente

- Turno não definido

---

### Aba 4

## Informações do Processamento

Registrar automaticamente:

Nome da empresa

Competência

Arquivo original utilizado

Quantidade de funcionários

Quantidade de dias processados

Quantidade de pendências

Data do processamento

Hora do processamento

Versão do sistema

Desenvolvedor

Nathan Adrian

---

## 11.5 Cabeçalho do Relatório

No topo do relatório deverá constar:

QualiPonto

Nome da empresa

Competência

Data do processamento

Hora do processamento

Logo da empresa

---

## 11.6 Rodapé

No rodapé deverá ser exibido:

"Este relatório foi gerado automaticamente pelo QualiPonto."

"A planilha oficial exportada pelo relógio de ponto não foi modificada."

"Desenvolvido por Nathan Adrian."

---

## 11.7 Histórico

Após gerar o relatório.

O sistema salvará automaticamente uma cópia em:

Historico/

↓

Ano

↓

Mês

↓

Relatorio_Horas.xlsx

Nunca substituir arquivos existentes.

Caso já exista um relatório com o mesmo nome.

O sistema deverá acrescentar automaticamente:

Relatorio_Horas_Julho_2026_001.xlsx

Relatorio_Horas_Julho_2026_002.xlsx

Relatorio_Horas_Julho_2026_003.xlsx

Garantindo que nenhum relatório seja perdido.

---

## 11.8 Relatório Individual

Além do relatório geral (Capítulo 11.4, todos os funcionários), o
sistema deverá ser capaz de gerar um relatório focado em um único
funcionário — usado pela Tela de Relatórios (Capítulo 12.8) quando o
usuário escolhe "Individual" em vez de "Todos".

Cabeçalho do funcionário:

• Nome

• Cargo

• Setor

• Turno

• Competência

Tabela diária (mesmos dias do relatório geral, Capítulo 11.4 Aba 1,
recortados para este funcionário):

• Data

• Dia da Semana

• Batidas

• Jornada Prevista

• Horas Trabalhadas

• Saldo

• Horas Extras

• Horas Negativas

• Situação

• Justificativa (quando existir)

• Observação (quando existir)

Resumo do funcionário, ao final:

• Horas Previstas (soma da Jornada Prevista de todos os dias)

• Horas Trabalhadas

• Horas Extras

• Horas Negativas

• Saldo Final

• Quantidade de Pendências Resolvidas

• Quantidade de Pendências Existentes (ainda em aberto)

Todos os valores vêm diretamente do que o Motor de Cálculo (Capítulo
6) já produziu para aquele funcionário — nenhum cálculo é refeito
aqui, apenas agrupado e formatado para exibição.

---

## 11.9 Resumo Geral da Competência

Um resumo único, cobrindo todos os funcionários processados na
competência atual:

• Competência

• Funcionários Processados

• Funcionários com Pendência

• Total de Pendências

• Horas Previstas

• Horas Trabalhadas

• Horas Extras

• Horas Negativas

• Saldo Geral

Assim como o Relatório Individual (Capítulo 11.8), é uma agregação
sobre o que o Motor de Cálculo já calculou — não uma nova regra de
cálculo.

---

## 11.10 Estatísticas da Competência

Gerado automaticamente a partir do resultado do processamento
(Capítulo 6):

• Quantidade de funcionários ativos (Capítulo 5.8)

• Quantidade de funcionários processados nesta competência

• Quantidade de funcionários sem nenhuma batida no período

• Quantidade de pendências por tipo (Capítulo 9.2)

• Distribuição das Justificativas utilizadas (Capítulo 9.6)

• Total de dias processados

---

## 11.11 Bloqueio por Pendências

Reforça a regra já estabelecida no Capítulo 9.1: enquanto existir
qualquer pendência em aberto (não resolvida), o sistema não deverá
permitir gerar o relatório final (geral ou individual).

A Tela de Relatórios (Capítulo 12.8) deverá exibir uma mensagem clara
ao usuário nessa situação, por exemplo:

"Existem pendências que precisam ser resolvidas antes da emissão do
relatório."

Somente depois que todas as pendências estiverem resolvidas (Capítulo
9.3), os botões de gerar/exportar relatório deverão ficar disponíveis.

---

## 11.12 Exportação

Excel (.xlsx) — único formato de exportação da versão 1.0, já descrito
nos Capítulos 11.1 a 11.9. Totalmente editável, com formatação
profissional (cabeçalho em destaque, painel congelado, bordas e
largura de coluna ajustada) para conferência e impressão direta a
partir do próprio Excel. A impressão (Capítulo 12.8) usa esse mesmo
Excel gerado.

A exportação em PDF foi oficialmente retirada da versão 1.0 e não
aparece na interface (Capítulo 12.8) — nenhum botão, menu ou mensagem
sobre PDF é exibido ao usuário. A arquitetura interna permanece
preparada para um formato adicional (mesma interface comum a
qualquer exportador, no padrão do Capítulo 6.6/Feriados), reservada
para uma versão futura, mas isso é um detalhe de implementação
invisível ao usuário.

# CAPÍTULO 12

# INTERFACE DO SISTEMA

## 12.1 Objetivo

A interface deverá ser moderna, intuitiva e simples de utilizar.

O usuário deverá conseguir processar uma planilha completa com poucos cliques.

O sistema será desenvolvido utilizando CustomTkinter.

---

## 12.2 Tela Inicial

A tela inicial deverá conter:

• Logo da empresa

• Nome da empresa

• Nome do sistema

• Competência da planilha selecionada

• Nome do arquivo selecionado

• Botão Selecionar Planilha

• Botão Processar

• Botão Funcionários

• Botão Setores (Capítulo 21)

• Botão Competências (Capítulo 22)

• Botão Relatórios (Capítulo 12.8)

• Botão Configurações

• Botão Histórico

• Botão Sobre

• Barra de status

---

## 12.3 Barra de Status

A barra inferior deverá informar:

Sistema iniciado

↓

Planilha carregada

↓

Processando...

↓

Gerando relatório...

↓

Relatório concluído.

Sempre mostrando ao usuário o que está acontecendo.

---

## 12.4 Tela Funcionários

Nesta tela será possível visualizar, cadastrar, editar, ativar/inativar
e excluir funcionários (Capítulo 5), tanto os criados pela importação
da planilha quanto os cadastrados manualmente.

Mostrar, em formato de tabela:

• Nome

• Cargo

• Setor

• Turno

• Status

Permitir:

Adicionar funcionário.

Editar funcionário.

Ativar/Inativar funcionário.

Excluir funcionário.

Pesquisar por nome em tempo real.

Ordenar a lista em ordem alfabética.

Filtrar a lista (ex.: por Status, Setor ou Turno).

Selecionar múltiplos funcionários (ou todos) e aplicar ações em massa
(Capítulo 5.10): alterar Turno, alterar Setor, alterar Cargo, ativar ou
inativar.

Exibir contadores de Total, Ativos e Inativos.

O ID é gerado automaticamente e nunca pode ser editado.

Não é permitido cadastrar dois funcionários com o mesmo Nome Completo.

---

## 12.5 Tela Configurações

Permitir alterar:

• Nome da empresa

• Logo

• Turnos

• Tolerância Entrada

• Tolerância Almoço

• Pasta do Histórico

Fora da primeira execução (Capítulo 4.1: "O usuário poderá alterar essas
informações posteriormente através da tela Configurações"), esta tela
exibe o modo de edição: os mesmos campos e a mesma validação do Wizard
(Capítulo 4.2 a 4.8), numa única página já carregada com os valores
atuais em vez das etapas sequenciais da primeira execução. Nenhum campo
é salvo isoladamente a cada tecla digitada — a persistência acontece de
uma só vez, ao clicar em "Salvar Alterações", e só quando todos os
campos estão válidos (mesma regra de validação do Resumo do Wizard,
Capítulo 4.9). Isso evita gravar um Turno com horário incompleto ou
uma tolerância inconsistente no meio da edição.

Turnos podem ser adicionados, editados ou removidos livremente nesta
tela. Um Turno já existente mantém seu ID (Capítulo 5.13/21.4) ao ser
editado — o vínculo por ID dos funcionários que o usam não se
rompe. Editar Configurações nunca apaga ou altera Funcionários ou
Setores — mudanças aqui ficam restritas a `configuracoes.json` e
`empresa.json`.

---

## 12.6 Tela Histórico

Mostrar todas as competências já processadas (Capítulo 14), organizadas
por:

Ano

↓

Mês

↓

Relatório(s) daquela competência

Deverá conter:

• Campo de pesquisa por competência (ex.: "Julho", "2026").

• Para cada competência: informações básicas lidas do próprio
relatório já gerado (Capítulo 11.4, Aba 4 — Informações do
Processamento) — Empresa, quantidade de funcionários processados,
quantidade de pendências, data/hora do processamento e quantidade de
relatórios (arquivos) disponíveis para aquela competência. Nenhuma
competência já fechada é recalculada para montar essa lista — os
valores exibidos são sempre os que já estão gravados no `.xlsx`.

• Para cada relatório (arquivo `.xlsx`) de uma competência: abrir
diretamente pelo sistema operacional (a "planilha Excel correspondente"
é o próprio arquivo do relatório, já em formato Excel — não existe uma
cópia da planilha original do relógio de ponto guardada em lugar
nenhum, conforme Capítulo 11.1/11.2).

• Excluir um histórico (todos os relatórios de uma competência),
mediante confirmação explícita — ação irreversível, avisada como tal.

---

## 12.7 Tela Sobre

Mostrar:

Nome do Sistema

Versão

Empresa

Desenvolvido por Nathan Adrian

Versão do Python

Última atualização

---

## 12.8 Tela de Relatórios

Tela dedicada para visualizar e exportar os relatórios de uma
competência (Capítulo 11), acessível pelo botão "Relatórios" da Tela
Inicial (Capítulo 12.2) — a qualquer momento, não só logo após um
processamento.

Deverá conter:

• Seletor de Competência: lista TODAS as competências já persistidas
(Capítulo 22), cada uma mostrando o próprio status (ex.: "Julho/2026 —
Pendências abertas"). Trocar a seleção troca o relatório exibido/
gerado, sem afetar as demais competências. Uma competência com
pendência em aberto aparece normalmente na lista — apenas o bloqueio
de geração (abaixo) fica ativo enquanto ela estiver selecionada. Uma
competência Arquivada (Capítulo 22.3) continua aparecendo
normalmente e pode gerar relatório de novo a qualquer momento.

• Seleção de Funcionário: "Todos" (Relatório Geral, Capítulo 11.4) ou
um funcionário específico (Relatório Individual, Capítulo 11.8).

Filtros (aplicáveis apenas ao modo "Todos"):

• Setor

• Turno

• Cargo

• Status

Botões:

• Visualizar

• Exportar Excel

• Imprimir (usa o Excel gerado — Capítulo 11.12)

A exportação em PDF não faz parte da interface da versão 1.0 (Capítulo
11.12) — nenhum botão, menu ou mensagem sobre PDF é exibido nesta tela.

Resumo superior, sempre visível:

• Funcionários

• Horas Extras

• Horas Negativas

• Pendências

Enquanto existir qualquer pendência em aberto, os botões de exportar/
imprimir deverão permanecer desabilitados, exibindo a mensagem do
Capítulo 9.1/11.11.

---

# CAPÍTULO 13

# CONFIGURAÇÕES

## 13.1 Objetivo

Todas as configurações deverão ficar armazenadas localmente.

Nenhuma informação ficará gravada no código.

---

## 13.2 Arquivo

Todas as configurações ficarão em:

dados/configuracoes.json

---

## 13.3 Configurações

Empresa

Logo

Turnos

Tolerância Entrada

Tolerância Almoço

Pasta Histórico

Tema

Versão

---

## 13.4 Funcionários

Todos os funcionários ficarão em:

dados/funcionarios.json

Cada funcionário possuirá:

ID

Nome

Turno

Status

Data Cadastro

Última Atualização

---

# CAPÍTULO 14

# HISTÓRICO

Todo relatório gerado será salvo automaticamente.

Estrutura:

Historico/

↓

2026/

↓

Julho/

↓

Relatorio_Horas_Julho_2026.xlsx

Nunca substituir arquivos.

Caso já exista.

Criar:

Relatorio_Horas_Julho_2026_001.xlsx

Relatorio_Horas_Julho_2026_002.xlsx

---

# CAPÍTULO 15

# LOGS

Todos os processamentos deverão ser registrados.

Arquivo:

Logs/processamento.log

Registrar:

Data

Hora

Arquivo utilizado

Competência

Funcionários processados

Pendências

Tempo de processamento

Relatório gerado

Possíveis erros

---

# CAPÍTULO 16

# ESTRUTURA INTERNA DOS DADOS

O sistema trabalhará internamente com objetos.

Empresa

↓

Funcionários

↓

Funcionário

↓

Dias

↓

Batidas

↓

ResultadoDia

↓

Relatório

Cada funcionário deverá possuir internamente:

ID

Nome

Turno

Dias

Cada dia deverá possuir:

Data

Dia da Semana

Batidas

Jornada Prevista

Horas Trabalhadas

Horas Extras

Horas Negativas

Saldo

Situação

Pendência

Essa estrutura será utilizada por todos os módulos do sistema.

---

## 16.1 Contrato do Motor de Cálculo

Além da estrutura por funcionário/dia acima, o Motor de Cálculo
(Capítulo 6) trabalha com mais dois objetos, usados exclusivamente
entre `calculadora.py` e quem o chama — nunca persistidos:

**ContextoCalculo** — tudo que o cálculo de um dia precisa além do
próprio dia (Configurações, Turno, nome da empresa, competência,
feriados). Criado uma vez por funcionário.

**ResultadoProcessamento** — o resultado consolidado de processar
todos os funcionários de uma competência: a lista de funcionários
processados, a lista de pendências, o resumo mensal de cada
funcionário e estatísticas gerais. É este objeto que alimenta o
Relatório (Capítulo 11) — nenhum módulo além de `calculadora.py`
deverá recalcular qualquer um desses valores; apenas ler, agrupar e
formatar.

**Competencia** — o `ResultadoProcessamento` acima, embrulhado junto
com mês, ano, status (Capítulo 22), data de importação, arquivo
original e se já foi gerado relatório. É a diferença entre um
resultado transitório (perdido ao fechar o sistema) e um resultado
persistido em disco (Capítulo 22) — nenhum dos dois objetos recalcula
nada; só o Motor de Cálculo (Capítulo 6) produz valores novos.

---

# CAPÍTULO 17

# REQUISITOS TÉCNICOS

O sistema deverá funcionar:

✓ Offline

✓ Windows 10

✓ Windows 11

✓ Sem internet

✓ Sem banco de dados

✓ Sem instalação de Python

O executável deverá ser gerado utilizando PyInstaller.

---

# CAPÍTULO 18

# REGRAS DE DESENVOLVIMENTO

Todos os módulos deverão possuir apenas uma responsabilidade.

Nenhum arquivo deverá ultrapassar aproximadamente 500 linhas de código.

O código deverá ser limpo, organizado e documentado.

Todo cálculo deverá ocorrer exclusivamente no módulo calculadora.py.

A interface nunca deverá realizar cálculos.

O leitor da planilha nunca deverá gerar relatórios.

Cada módulo deverá executar apenas sua função.

---

# CAPÍTULO 19

# VERSÃO 1.0

A primeira versão deverá entregar:

✓ Leitura da planilha

✓ Cadastro Inteligente

✓ Configurações

✓ Processamento

✓ Cálculo das horas

✓ Relatório Excel

✓ Histórico

✓ Logs

✓ Executável (.exe)

Esta versão deverá ser totalmente funcional para utilização diária na empresa.

---

# CAPÍTULO 20

# ARQUITETURA DE COMUNICAÇÃO

O QualiPonto será composto por módulos independentes.

Cada módulo terá apenas uma responsabilidade.

A comunicação ocorrerá sempre através de estruturas de dados padronizadas.

Fluxo Geral

main.py

↓

interface.py

↓

tela_principal.py

↓

config.py

↓

leitor_ponto.py

↓

validacao.py

↓

cadastro.py

↓

calculadora.py

↓

relatorio.py

↓

Historico

↓

Logs
# CAPÍTULO 21

# CADASTRO DE SETORES

## 21.1 Objetivo

O sistema deverá permitir o cadastro de Setores da empresa (ex.: Produção, Expedição, Administrativo), para uso futuro no vínculo com funcionários, filtros, estatísticas, gráficos e relatórios.

Este cadastro é independente do Cadastro Inteligente de Funcionários (Capítulo 5) e não depende da leitura de planilha.

---

## 21.2 Estrutura do Setor

Cada setor possuirá:

ID (identificador interno, gerado automaticamente, nunca editável)

Nome

Cor (opcional — reservada para uso futuro em gráficos e relatórios)

Status (Ativo/Inativo)

---

## 21.3 Tela de Gerenciamento de Setores

Deverá permitir:

Adicionar setor.

Editar setor (nome e cor).

Ativar/Inativar setor.

Excluir setor — apenas se não houver nenhum funcionário vinculado a ele.

Confirmação obrigatória antes de qualquer exclusão.

---

## 21.4 Vínculo com Funcionários

Quando o Cadastro de Funcionários existir (Capítulo 5), cada funcionário deverá ser vinculado a um setor por seleção em lista, nunca por texto digitado.

O vínculo deverá ser feito pelo ID do setor, nunca pelo nome.

Se um setor for renomeado, todos os funcionários vinculados a ele deverão permanecer associados automaticamente, sem nenhuma ação manual.

---

## 21.5 Exclusão de Setor

Um setor só poderá ser excluído se não existir nenhum funcionário vinculado a ele.

Enquanto o Cadastro de Funcionários não existir, essa verificação não terá funcionários para checar; a estrutura de validação deverá, ainda assim, estar preparada para ser usada assim que o Cadastro de Funcionários (Capítulo 5) for implementado.

---

## 21.6 Persistência

Os setores serão armazenados em:

dados/setores.json

Seguindo o mesmo padrão de leitura, escrita e backup automático já utilizado pelas demais configurações do sistema (Capítulo 13).

---

## 21.7 Interface

Tela de Setores, seguindo o mesmo padrão visual do restante do sistema (tema escuro, botões grandes, interface limpa).

Deverá conter:

Lista dos setores cadastrados.

Botão para adicionar novo setor.

---

## 21.8 Criação Automática Durante a Importação

Além do cadastro manual (Capítulo 21.3), Setores também poderão ser
criados automaticamente durante a importação de uma planilha, quando
o campo "Dep." de algum funcionário não corresponder a nenhum Setor
já cadastrado (Capítulo 5.17).

Setores criados dessa forma seguem exatamente a mesma estrutura
(Capítulo 21.2) e a mesma persistência (Capítulo 21.6) dos Setores
cadastrados manualmente — não existe distinção de origem no restante
do sistema. Após criados, são administrados normalmente pela Tela de
Gerenciamento de Setores (Capítulo 21.3): podem ser renomeados, ter
cor definida, ser ativados/inativados ou excluídos (respeitando a
mesma regra de exclusão do Capítulo 21.5).

Ação de editar por setor.

Ação de ativar/inativar por setor.

Ação de excluir por setor, com confirmação.

---

# CAPÍTULO 22

# GERENCIAMENTO DE MÚLTIPLAS COMPETÊNCIAS

## 22.1 Objetivo

Antes desta funcionalidade, o sistema processava uma única competência
por vez, inteiramente em memória — fechar o sistema sem exportar para
o Histórico (Capítulo 12.6) perdia todo o trabalho, incluindo
pendências já corrigidas e justificativas já preenchidas.

A partir desta funcionalidade, cada planilha importada cria uma
**Competência** (mês/ano) persistida em disco imediatamente após o
Motor de Cálculo (Capítulo 6) processar o lote — funcionários,
pendências, justificativas já preenchidas, resumo mensal, estatísticas
e status. Várias competências coexistem simultaneamente, cada uma
totalmente independente das demais.

---

## 22.2 O que é uma Competência

Uma Competência agrupa, para um mês/ano:

• Todos os funcionários processados naquela importação (com seus dias
e batidas).

• Todas as pendências geradas (Capítulo 9), resolvidas ou não.

• O resumo mensal e as estatísticas (Capítulo 11.9/11.10).

• Status (Capítulo 22.4), data da importação, nome do arquivo
original e se já foi gerado algum relatório.

Persistida em `dados/competencias/`, um arquivo por competência —
nunca um único arquivo compartilhado. Isso é o que permite fechar o
sistema no meio das pendências, a qualquer momento, sem perder nada.

---

## 22.3 Tela Competências

Nova tela, acessível pelo botão "Competências" da Tela Inicial
(Capítulo 12.2), mostrando um card por competência já importada:

• Competência (Mês/Ano).

• Data da importação.

• Quantidade de funcionários.

• Quantidade de pendências.

• Quantidade de pendências já resolvidas.

• Status (Capítulo 22.4).

• Relatório gerado (Sim/Não).

• Botão "Abrir" — retoma o trabalho daquela competência (Capítulo
22.5).

• Botão "Arquivar" — muda o status para Arquivada (Capítulo 22.4).
Não existe ação de "Desarquivar" nesta versão: uma competência
arquivada continua acessível normalmente pela Tela de Relatórios
(Capítulo 12.8, podendo gerar relatório de novo a qualquer momento),
apenas não pode voltar a um status anterior por esta tela.

Nenhuma competência é excluída por esta tela.

---

## 22.4 Status da Competência

Cada competência tem um dos seguintes status, reavaliado
automaticamente a cada correção/justificativa aplicada na Tela de
Pendências (Capítulo 9.3):

• **Em andamento** — parte das pendências já foi resolvida, ainda há
pendência em aberto.

• **Pendências abertas** — nenhuma pendência foi resolvida ainda.

• **Pronta para relatório** — todas as pendências foram resolvidas,
relatório ainda não foi gerado.

• **Relatório gerado** — pelo menos um relatório já foi exportado
para esta competência, sem nenhuma pendência em aberto no momento da
exportação. Não regride automaticamente para "Pronta para relatório".

• **Arquivada** — só muda por ação manual do usuário (Capítulo 22.3);
nenhuma reavaliação automática altera este status.

("Importada" existe como valor reservado, mas não é alcançado
automaticamente no fluxo atual: uma Competência só passa a existir
depois que o Motor de Cálculo já processou o lote.)

---

## 22.5 Retomar Trabalho

Ao clicar "Abrir" numa competência (Tela Competências, Capítulo 22.3):

Se ainda existir pendência em aberto: abre a Tela de Pendências
(Capítulo 9.3) exatamente com as pendências restantes — as já
resolvidas e as justificativas já aplicadas permanecem exatamente como
estavam antes de fechar o sistema.

Se não existir mais nenhuma pendência em aberto: vai direto para a
Tela de Relatórios (Capítulo 12.8), com esta competência já
selecionada — mesmo comportamento do fluxo inteligente já existente
(Capítulo 9.3) logo após um processamento.

---

## 22.6 Importação e Competência Já Existente

**Alterado na v2.0 — ver Capítulo 23.3.** Até a v1.1.1, importar uma
planilha cujo mês/ano já correspondia a uma competência existente
perguntava se deveria **substituir por inteiro** a competência
(destrutivo). A partir da v2.0, a nova planilha é **sincronizada
incrementalmente** com a competência já existente — nada é substituído
por inteiro, e nenhuma pendência já corrigida/justificada é perdida. A
única confirmação que permanece é para reimportar sobre uma competência
**Fechada** (Capítulo 23.4). Nunca existem duas competências para o
mesmo mês/ano ao mesmo tempo.

---

## 22.7 Relatórios Multi-Competência

A Tela de Relatórios (Capítulo 12.8) passa a listar todas as
competências persistidas, gerando o relatório de qualquer uma delas
de forma independente — exportar o relatório de uma competência nunca
afeta as demais. O bloqueio por pendência em aberto (Capítulo 9.1/
11.11) se aplica normalmente à competência selecionada no momento.

---

## 22.8 Histórico

O Histórico (Capítulo 12.6) continua funcionando exatamente como
antes, sem nenhuma alteração: continua lendo apenas os arquivos
`.xlsx` já exportados, sem nenhuma referência às competências geridas
por este capítulo. Uma competência não é removida do gerenciamento
(Capítulo 22.3) depois que um relatório é gerado.

---

# CAPÍTULO 23

# COMPETÊNCIA INCREMENTAL, IMPORTAÇÃO SEMANAL E DASHBOARD (v2.0)

## 23.1 Objetivo

O RH da Qualimix exporta a planilha de ponto **semanalmente**. O
arquivo sempre tem o layout do mês inteiro (todos os dias do mês
aparecem), mas só os dias já ocorridos até o momento da exportação têm
batida preenchida — os dias futuros aparecem em branco.

Até a v1.1.1, reimportar essa planilha sobre um mês já existente
substituía a competência inteira (Capítulo 22.6, versão anterior),
descartando qualquer correção manual ou justificativa já aplicada. A
partir da v2.0, cada nova importação **atualiza** a mesma competência
incrementalmente: nenhum dado corrigido é perdido, e a competência
cresce dia a dia até o mês fechar.

---

## 23.2 Sincronização Incremental

Ao reimportar uma planilha cujo mês/ano já corresponde a uma
competência existente, o sistema:

• Processa a planilha nova por inteiro através do Motor de Cálculo
(Capítulo 6), exatamente como sempre — nenhuma regra de cálculo muda.

• Compara o resultado novo com a competência já persistida,
funcionário a funcionário e dia a dia:

  — Funcionário que ainda não existia na competência: adicionado por
  inteiro.

  — Funcionário sem Turno válido nesta importação (Capítulo 9.2): seus
  dias já calculados em importações anteriores nunca são tocados — só
  a pendência de Turno Não Definido é atualizada.

  — Dia que não existia antes: adicionado.

  — Dia protegido (Capítulo 23.3): nunca sobrescrito, mesmo que a
  planilha traga um valor diferente para aquele dia.

  — Dia com as mesmas batidas (mesmos horários, mesma ordem) e sem
  nenhuma pendência nova surgindo (Capítulo 23.6): não é tocado.

  — Dia com batidas diferentes e ainda não protegido: substituído pela
  versão nova já calculada.

• Nenhum funcionário ou dia é removido, mesmo que esteja ausente do
arquivo mais recente.

• Pendências, resumo mensal e estatísticas da competência são
recompostos sobre o estado final já mesclado — mesma agregação pura já
usada pelo Motor de Cálculo, nenhuma fórmula nova.

O usuário só vê uma mensagem informativa ("competência já existe — os
novos registros serão sincronizados, sem apagar nada do que já foi
feito"), nunca mais uma pergunta de Substituir/Cancelar destrutiva
(exceto para competência Fechada, Capítulo 23.4).

---

## 23.3 Proteção de Dia Corrigido

Um dia nunca é sobrescrito por uma nova importação quando o usuário já
mexeu nele:

• Pelo menos uma batida daquele dia foi digitada manualmente (correção
de batida, Capítulo 9.4); ou

• A pendência daquele dia já está resolvida (corrigida ou justificada,
Capítulo 9.5/9.6).

Essa é a garantia central da importação semanal: corrigir um dia na
Tela de Pendências é definitivo — nenhuma importação futura da mesma
competência pode desfazer essa correção sem uma ação explícita do
usuário (edição manual de novo).

---

## 23.4 Fechamento de Competência

Uma competência pode ser marcada como **Fechada** pela Tela
Competências (Capítulo 22.3), independente do Status detalhado
(Capítulo 22.4) e do conceito já existente de Arquivar (Capítulo 22.3):
Fechar/Reabrir e Arquivar são ações independentes uma da outra.

Reimportar uma planilha sobre uma competência Fechada pergunta antes
de prosseguir: "Esta competência está fechada. Deseja reabri-la para
sincronizar esta nova importação?" — Cancelar interrompe a importação
sem alterar nada; confirmar reabre a competência (Fechada → aberta) e
prossegue com a sincronização incremental normal (Capítulo 23.2).

Um selo simplificado de 3 estados resume a situação de cada
competência, calculado automaticamente (nunca persistido por si só) e
exibido junto ao Status detalhado já existente:

• 🟢 **Em andamento** — não fechada, sem pendência em aberto.

• 🟡 **Aguardando pendências** — não fechada, com pelo menos uma
pendência em aberto.

• 🔴 **Fechada** — fechada manualmente (prevalece sobre os dois
anteriores).

---

## 23.5 Histórico de Importações e Auditoria

Cada competência guarda um registro de cada importação recebida: data
e hora, usuário do Windows que executou a importação, nome do arquivo
original e quantidade de registros no arquivo/adicionados/alterados.

Além disso, um log de auditoria registra eventos de alteração manual —
quem (usuário do Windows, capturado automaticamente, sem exigir tela
de login), quando, o quê foi alterado, valor anterior e valor novo —
para: correção manual de batida, alteração de justificativa, alteração
de observações (Tela de Pendências, evento por dia alterado) e
Aplicar Justificativa por Período (Capítulo 9.8, um único evento
agregado por operação em lote). Fechar/Reabrir uma competência também
gera um evento de auditoria.

Ambos os registros são consultáveis pelo botão "Histórico" de cada
card na Tela Competências (Capítulo 22.3).

---

## 23.6 Dia Futuro Sem Pendência Falsa

Como a planilha semanal sempre tem o layout do mês inteiro, os dias
que ainda não ocorreram aparecem sem nenhuma batida — exatamente como
um dia com pendência real de "Nenhuma batida registrada" (Capítulo
9.1). Sem distinguir os dois casos, toda importação semanal geraria
dezenas de pendências falsas para os dias futuros do mês.

O Motor de Cálculo determina, a cada processamento, o último dia com
pelo menos uma batida registrada entre todos os funcionários do lote.
Um dia sem nenhuma batida que seja **posterior** a esse último dia com
dado é tratado como "ainda não ocorrido": não gera pendência, fica com
Situação "Sem Registro", neutro para o resumo mensal. Um dia sem
batida **anterior ou igual** a esse último dia com dado continua
gerando a pendência de "Nenhuma batida registrada" normalmente — é uma
ausência real, não um dia futuro.

Se uma nova importação avança o último dia com dado (a semana seguinte
chegou), um dia antes tratado como futuro pode passar a ser uma
ausência real — a sincronização incremental (Capítulo 23.2) reconhece
essa transição e adota a pendência nova, mesmo que as batidas de
ambas as versões estivessem igualmente vazias.

---

## 23.7 Relatórios por Período

A Tela de Relatórios (Capítulo 12.8) ganha um seletor de período,
independente do fechamento da competência (Capítulo 23.4):

• **Mês completo** (padrão) — nenhum filtro de data, mesmo
comportamento de antes da v2.0.

• **Personalizado** — intervalo de datas "De"/"Até", preenchido
manualmente ou por um dos atalhos: Hoje, Esta Semana (últimos 7 dias)
e Quinzena (últimos 15 dias) — cada atalho só preenche os campos "De"/
"Até"; o filtro em si sempre usa esses dois campos.

O bloqueio por pendência em aberto (Capítulo 9.1/11.11) passa a
considerar apenas o recorte selecionado (período + demais filtros),
não a competência inteira — um relatório de uma semana sem nenhuma
pendência em aberto não é bloqueado por uma pendência de outro dia do
mesmo mês fora do recorte.

---

## 23.8 Novos Filtros de Relatório

Além dos filtros já existentes (Funcionário/Setor/Turno/Cargo/Status,
Capítulo 12.8), quatro novos filtros, todos combináveis entre si e com
os já existentes:

• **Situação** — mantém quem tem pelo menos um dia, no período
considerado, com a Situação escolhida (Normal/Hora Extra/Hora
Negativa/Pendência/Sem Registro, Capítulo 10).

• **Pendências** — Com pendência / Sem pendência.

• **Horas Extras** — Com horas extras / Sem horas extras.

• **Banco de Horas** — Positivo / Negativo / Zerado (Capítulo 23.11).

---

## 23.9 Dashboard (in-app)

Nova tela, acessível pelo botão "Dashboard" da Tela Inicial (Capítulo
12.2), com a competência selecionável (mesmo seletor usado na Tela de
Relatórios) e:

• Cards: Total de Funcionários, Horas Trabalhadas, Horas Extras, Horas
Negativas, Banco de Horas, Pendências, Dias Processados e Competência.

• Tabelas ordenadas: Horas Extras por Funcionário, Horas Negativas por
Funcionário, Pendências por Dia, Horas Extras por Dia, Ranking de
Horas Extras (10 primeiros), Ranking de Atrasos (10 primeiros — contagem
de dias com Situação "Hora Negativa" por funcionário) e Banco de Horas
(saldo por funcionário, Capítulo 23.11).

Sem gráficos de imagem — decisão confirmada: tabelas numéricas
ordenadas, mantendo o instalador leve e sem nenhuma dependência nova.

---

## 23.10 Dashboard no Relatório Excel

O Relatório Geral em Excel (Capítulo 11.4) ganha uma 5ª aba,
"Dashboard", com o mesmo conjunto de indicadores/ranking/distribuição
da Tela Dashboard (Capítulo 23.9), mais gráficos nativos do Excel
(`openpyxl.chart` — nenhuma dependência nova): gráfico de barras para
Horas Extras por Funcionário, gráfico de barras para Horas Negativas
por Funcionário e gráfico de pizza para a distribuição do Banco de
Horas (Positivo/Negativo/Zerado). As 4 abas já existentes (Relatório
Diário, Resumo Mensal, Pendências, Informações do Processamento)
permanecem exatamente como eram, em conteúdo e formatação.

---

## 23.11 Banco de Horas

"Banco de Horas" é um **sinônimo** do Saldo já existente
(`saldo_final_min`, Capítulo 10) — não é um conceito novo nem uma nova
regra de cálculo. Não há acúmulo entre competências diferentes: o
Banco de Horas exibido é sempre o saldo da competência selecionada,
igual ao que já era mostrado como "Saldo" antes da v2.0.

---

## 23.12 Compatibilidade

Nenhuma regra de cálculo (jornadas, tolerâncias, horas extras, horas
negativas, Capítulos 6 a 10), nenhuma tela existente e nenhum relatório
já gerado é alterado por este capítulo. Uma competência processada uma
única vez (fluxo anterior à v2.0, sem reimportação) produz exatamente
o mesmo resultado de antes — a sincronização incremental só entra em
ação ao reimportar um mês já existente. Competências e cadastros
persistidos por instalações v1.x são lidos normalmente: os campos
novos (`fechada`, `quantidade_importacoes`, `historico_importacoes`,
`auditoria`) recebem valores padrão vazios na primeira leitura.

---

# FIM DO CAPÍTULO 23

---

# CAPÍTULO 24 — Modernização de Interface (v2.1 Sprint 1)

## 24.1 Objetivo

Padronizar em todas as telas com listagem (Funcionários, Setores,
Histórico, Competências, Pendências e, a partir do Capítulo 25,
Absenteísmo) o mesmo conjunto de recursos de navegação e exportação,
sem duplicar essa lógica em cada tela.

---

## 24.2 Componentes reutilizáveis (`componentes.py`)

`TabelaPadrao` (`ctk.CTkFrame`) concentra, para qualquer lista de
registros:

• Pesquisa instantânea — insensível a acento, caixa e (de forma
simples) plural, usando a mesma normalização já usada pelo motor de
importação (`modelos.normalizar_texto`).

• Ordenação por clique no cabeçalho da coluna, com 3 estados por
coluna: crescente → decrescente → ordem original (nenhuma seta).
Clicar em outra coluna reinicia esse ciclo para a coluna nova.

• Paginação configurável (25 / 50 / 100 / Todos), com rodapé mostrando
a contagem de registros exibidos/total.

Cada tela fornece à `TabelaPadrao` apenas uma função `criar_linha` que
sabe construir o widget de UMA linha daquela tela específica — o
componente não impõe layout de linha, só o contrato mínimo de a linha
saber se vincular a um registro novo (`vincular`) e se mostrar/ocultar
(`grid`/`grid_remove`). Isso permite que cada tela mantenha o layout de
linha que já tinha, só ganhando pesquisa/ordenação/paginação de graça.

Por desempenho, as linhas são recicladas: ao trocar de página ou
filtrar, os widgets já existentes são reaproveitados e revinculados a
outro registro, em vez de destruídos e recriados — importante em
listas grandes (ex.: Histórico com muitas competências).

`BotaoExportar` (`ctk.CTkFrame`) — combina um seletor de formato
(Excel / CSV / PDF) com um botão "Exportar"; ao clicar, gera o arquivo
com o formato do momento (Excel via `openpyxl`, CSV com separador `;`
e codificação UTF-8 com BOM para abrir corretamente no Excel em
português, PDF via `reportlab`) usando exatamente os registros
visíveis na tabela no momento do clique (respeitando pesquisa e
ordenação ativas). O arquivo é salvo em
`Historico/Exportações/<categoria>/`, com sufixo incremental se já
existir um arquivo com o mesmo nome no mesmo dia (mesmo padrão já
usado pelo Histórico de relatórios, Capítulo 12).

---

## 24.3 Atalhos de teclado globais

Válidos em qualquer tela do sistema:

• **F5** — atualiza a tela atual (reexecuta o carregamento de dados),
quando a tela suporta atualização.

• **Ctrl+F** — leva o foco ao campo de pesquisa da tela atual, quando
existir.

• **Ctrl+P** — aciona a impressão da tela atual, quando a tela
suportar impressão.

Não há atalho global para Ctrl+N/Ctrl+S/Esc: o alvo desses comandos
depende de qual diálogo está aberto no momento, o que tornaria o
atalho ambíguo ou perigoso (ex.: Esc fechando um diálogo de
confirmação sem querer).

---

## 24.4 Exceção deliberada — Tela de Pendências

A Tela de Pendências (Capítulo 9) não foi migrada para `TabelaPadrao`
porque cada linha ali é um mini-formulário (campos de batida,
combobox de Justificativa, observações), não uma linha de exibição
compacta — o contrato de `TabelaPadrao` não se encaixa bem nesse caso.
A tela manteve seu próprio pool especializado de linhas (já existente
desde a Sprint de Justificativa por Período) e ganhou, à parte,
ordenação (Nome/Data/Tipo, crescente/decrescente), paginação
(25/50/100/Todos, com o mesmo princípio de reciclagem de widgets),
exportação (`BotaoExportar`) e impressão — mesma experiência de uso
das demais telas, sem forçar uma reestruturação que pioraria a tela.

---

## 24.5 Compatibilidade

Nenhuma regra de negócio, cálculo, ou formato de dado persistido foi
alterada por este capítulo — é puramente uma camada de apresentação
sobre listas que já existiam. Nenhuma tela perdeu funcionalidade
anterior.

---

# FIM DO CAPÍTULO 24

---

# CAPÍTULO 25 — Absenteísmo (v2.1 Sprint 2)

## 25.1 Objetivo

Medir e acompanhar o absenteísmo dos funcionários a partir de dados já
existentes no sistema — sem introduzir nenhuma nova fonte de dado nem
recalcular o motor de horas.

---

## 25.2 Fonte dos dados — motor de agregação, não de cálculo

O módulo de Absenteísmo (`absenteismo.py`) NUNCA recalcula horas
trabalhadas, extras ou negativas — ele apenas agrega o que o Motor de
Cálculo (Capítulo 6) e as Pendências/Justificativas (Capítulo 9) já
produziram para uma competência.

Um dia só entra como possível ocorrência de absenteísmo se:

1. O dia tem jornada prevista (dias sem jornada prevista, ex.: folga
   de escala, são ignorados — não é ausência se não havia expectativa
   de trabalho); e

2. O dia tem uma Pendência com uma Justificativa válida preenchida
   (Capítulo 9.6).

Dias com pendência SEM justificativa preenchida (ainda não resolvida)
não entram nem como ocorrência considerada nem como ignorada — ficam
de fora do índice até serem resolvidos, para não presumir que
pendência em aberto seja automaticamente falta.

---

## 25.3 Justificativas consideradas no índice (configurável)

Cada Justificativa (Capítulo 9.6) tem uma configuração própria,
versionada (25.6), indicando se ela conta para o índice de
absenteísmo (`considerar_no_indice`), além de cor e ícone de exibição.

Três novas Justificativas foram adicionadas para esta sprint —
**Licença Maternidade**, **Licença Paternidade** e **Feriado** —,
incluídas também em `JUSTIFICATIVAS_QUE_ELIMINAM_HORA_NEGATIVA`
(Capítulo 9.7), pela mesma natureza de ausência legalmente amparada
das justificativas que já estavam nessa lista.

Por padrão, apenas três Justificativas já existentes vêm marcadas como
consideradas no índice — **Falta**, **Falta Justificada** e **Atestado
Médico** —, por corresponderem diretamente a ausência do funcionário.
As demais (incluindo as 3 novas) vêm desmarcadas por padrão; o
administrador pode ativar outras conforme a realidade da empresa, sem
que o sistema precise "adivinhar" uma equivalência que a especificação
não definiu.

---

## 25.4 Método de cálculo (configurável)

O índice de absenteísmo pode ser expresso, à escolha do administrador,
em:

• **Dias** — quantidade de dias com ocorrência considerada.

• **Horas** — soma de `jornada_prevista_min - horas_trabalhadas_min`
(nunca negativo) dos dias com ocorrência considerada.

• **Percentual** — dias/horas perdidos sobre o total de dias/horas
previstos no período, expresso em %.

A mudança do método de cálculo não recalcula índices já apurados
(25.6) — só afeta cálculos feitos depois da mudança.

---

## 25.5 Memória de cálculo (nunca "caixa-preta")

Todo índice apurado pode ser aberto numa tela de "Memória de Cálculo"
mostrando, por extenso: quais dias entraram como ocorrência
considerada (com funcionário, data e Justificativa), quais ocorrências
existiam mas foram ignoradas (Justificativa presente, mas não marcada
para considerar no índice) e a fórmula exata aplicada para chegar ao
número final. Nenhum resultado é apresentado sem que o usuário consiga
ver de onde ele veio.

---

## 25.6 Configuração versionada

Cada alteração salva na configuração de Absenteísmo (quais
Justificativas contam, método de cálculo, limiares de cor) incrementa
um número de versão e registra uma entrada de auditoria (quem, quando,
o que mudou, valor anterior, valor novo — mesmo mecanismo de auditoria
do Capítulo 13). Um índice já calculado guarda a versão da configuração
usada naquele cálculo — mudar a configuração depois NUNCA altera
retroativamente um índice já apurado; apenas competências recalculadas
depois da mudança usam a configuração nova.

---

## 25.7 Classificação por cor e alertas

Cada índice apurado é classificado por cor (verde / amarelo / vermelho)
a partir de dois limiares configuráveis pelo administrador — "Atenção"
(padrão 2,0) e "Crítico" (padrão 5,0), na mesma unidade do método de
cálculo escolhido (25.4). A Tela de Absenteísmo gera alertas
automáticos para funcionários/competências que cruzam esses limiares.

---

## 25.8 Ranking, comparativo e previsão

• **Ranking** — os funcionários com maior índice de absenteísmo numa
competência, do maior para o menor.

• **Comparativo** — coloca lado a lado os índices de duas
competências (mesmo funcionário ou visão geral), mostrando a variação.

• **Previsão** — uma estimativa simples do próximo índice, por média
móvel dos índices já apurados anteriormente — não é um modelo
estatístico sofisticado, é uma projeção simples e explicável.

---

## 25.9 Simulador

Permite ao usuário testar hipóteses ("e se este funcionário tivesse
mais N dias de falta?", "e se esta ocorrência específica fosse
removida?") e ver o índice resultante, **sem gravar nenhuma alteração**
nos dados reais — o simulador opera sobre uma cópia em memória do
indicador já calculado e nunca chama `salvar_competencia` nem qualquer
outra função de persistência.

---

## 25.10 Tela e navegação

A Tela de Absenteísmo (menu principal) reúne dashboard/indicadores/
ranking/comparativo/alertas num único lugar (não como submenus
separados, já que são visões da mesma competência selecionada), com
uma tela própria de Configuração (Justificativas consideradas, método
de cálculo, limiares). O histórico de configuração fica acessível a
partir de cada índice já calculado, através da versão de configuração
que ele guarda (25.6) — não há uma tela de "Histórico" separada, pois
o vínculo índice→versão já cumpre esse papel sem duplicar informação.

---

## 25.11 Compatibilidade

Absenteísmo é somente leitura sobre dados já existentes — não grava em
`funcionarios.json`, em `configuracoes.json` nem em nenhuma
competência. Nenhuma regra de cálculo de horas (Capítulos 6 a 10) foi
alterada.

---

# FIM DO CAPÍTULO 25

---

# CAPÍTULO 26 — QualiAssist (v2.1 Sprint 3)

## 26.1 Objetivo

Um assistente de ajuda **100% offline**, integrado a todo o sistema,
para reduzir dependência de suporte externo — sem nunca alterar dados
do sistema.

---

## 26.2 Botão flutuante e painel

Um botão flutuante fica sempre visível sobre a janela principal,
independente da tela atual, e abre o Painel do QualiAssist ao ser
clicado. O painel oferece pesquisa livre, navegação por categoria
(mesmo agrupamento do menu principal — Importação, Funcionários,
Jornadas, Competências, Banco de Horas, Horas Extras, Horas Negativas,
Correções, Absenteísmo, Relatórios, Dashboard, Configurações,
Exportações, QualiAssist), histórico de consultas recentes e artigos
favoritados.

---

## 26.3 Base de conhecimento

Os artigos de ajuda ficam numa base própria (`qualiassist_base.json`),
separada do código-fonte — o conteúdo pode ser editado (26.6) sem
alterar nenhum arquivo `.py`. Cada artigo tem categoria, título,
palavras-chave, perguntas relacionadas (para casar frases naturais do
usuário), corpo da resposta e links para artigos relacionados.

---

## 26.4 Busca tolerante

A pesquisa ignora acento, caixa, plural simples (removendo o "s" final
de palavras com mais de 3 letras) e reconhece um pequeno conjunto de
sinônimos do vocabulário do sistema (ex.: "HE" para "Horas Extras").
Os resultados são ordenados por relevância: presença dos termos no
título pesa mais do que nas palavras-chave, que pesa mais do que nas
perguntas relacionadas, que pesa mais do que no corpo da resposta.

---

## 26.5 Ajuda contextual

Ao abrir o painel a partir de uma tela específica, o QualiAssist já
sugere a categoria correspondente àquela tela automaticamente. Duas
ações adicionais ficam disponíveis a partir de qualquer tela: "Explicar
esta Tela" (abre o artigo que descreve a tela atual, se existir) e
"Explicar este Botão" (mesma ideia, por elemento).

Quando uma mensagem de erro conhecida aparece no sistema, o QualiAssist
consegue sugerir o artigo relacionado automaticamente, reconhecendo o
conjunto de palavras-chave da mensagem (não é necessário que a
mensagem seja idêntica a um texto fixo — a correspondência é por
conjunto de palavras presentes, tolerando variações de frase).

---

## 26.6 Painel administrativo

Uma tela administrativa permite criar, editar e ativar/inativar artigos
da base de conhecimento sem editar o JSON manualmente, além de
exportar/importar a base inteira em JSON (para backup ou transferência
entre instalações). Toda alteração na base incrementa uma versão e
registra auditoria, no mesmo padrão do Capítulo 25.6.

---

## 26.7 Escopo desta versão

Ficam fora desta versão, deliberadamente: tooltip contextual por botão
individual (todos os botões, um a um) e tour guiado de primeiro acesso
— citados no documento de origem como possibilidades, mas não
implementados nesta sprint; ver `README.md`, seção "Futuras Versões".

---

## 26.8 Compatibilidade

O QualiAssist é somente leitura sobre os dados operacionais do sistema
(nunca grava em `funcionarios.json`, competências, ou configurações de
cálculo) — sua própria base de conhecimento e histórico de consultas
são os únicos arquivos que ele grava (`qualiassist_base.json`,
`qualiassist_historico.json`). Nenhuma tela, cálculo ou relatório
existente foi alterado por este capítulo.

---

# FIM DO CAPÍTULO 26

# FIM DA ESPECIFICAÇÃO