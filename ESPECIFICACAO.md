ESPECIFICAÇÃO OFICIAL
Calculadora de Horas Extras Qualimix
Versão 2.0

Autor: Nathan Adrian

CAPÍTULO 1
VISÃO GERAL DO SISTEMA
1.1 Objetivo

A Calculadora de Horas Extras Qualimix é um sistema desktop desenvolvido para automatizar completamente o processamento das folhas de ponto dos colaboradores da empresa.

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

Sábado:

Esperado:

2 batidas.

Domingo:

Todo horário registrado será considerado hora extra.

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

Após identificar todos os funcionários.

O sistema exibirá uma lista.

Exemplo.

João Silva

○ Turno 06:00 às 15:00

○ Turno 07:30 às 16:30

Maria

○ Turno 06:00 às 15:00

○ Turno 07:30 às 16:30

O usuário apenas marcará o turno.

Depois clicar em:

Salvar.

---

## 4.7 Tolerância de Entrada

O sistema perguntará:

Deseja utilizar tolerância para entrada?

○ Sim

○ Não

Caso Sim.

Informar quantidade de minutos.

Exemplo.

5 minutos.

Essa tolerância será aplicada automaticamente durante os cálculos.

---

## 4.8 Tolerância do Almoço

O sistema perguntará.

Deseja utilizar tolerância para retorno do almoço?

○ Sim

○ Não

Caso Sim.

Informar quantidade de minutos.

Essa tolerância será aplicada automaticamente.

---

## 4.9 Finalização

Após concluir todas as etapas.

O sistema criará automaticamente:

dados/configuracoes.json

dados/funcionarios.json

A configuração inicial será considerada concluída.

Ela não deverá ser exibida novamente.

---

# CAPÍTULO 5

# CADASTRO INTELIGENTE

## 5.1 Objetivo

Eliminar completamente o cadastro manual de funcionários.

Toda manutenção deverá ocorrer automaticamente através da leitura das planilhas.

---

## 5.2 Primeira Importação

Na primeira planilha.

O sistema deverá:

Ler todos os funcionários.

Cadastrar automaticamente.

Solicitar apenas o turno.

Salvar o cadastro.

---

## 5.3 Próximas Importações

Sempre que uma nova planilha for aberta.

O sistema comparará:

Funcionários cadastrados.

↓

Funcionários encontrados.

---

## 5.4 Novo Funcionário

Caso um funcionário novo seja encontrado.

O sistema deverá exibir.

------------------------------------------------

Novo funcionário encontrado.

Nome:

Carlos Eduardo

Selecione o turno.

○ 06:00 às 15:00

○ 07:30 às 16:30

[ Salvar ]

------------------------------------------------

Após salvar.

O funcionário será incluído automaticamente no cadastro.

---

## 5.5 Funcionário sem Horários

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

## 5.6 Funcionário Não Encontrado

Caso um funcionário cadastrado deixe de aparecer na planilha.

Nenhuma alteração deverá ser realizada automaticamente.

O cadastro permanecerá ativo.

O sistema apenas registrará essa ocorrência nos logs.

---

## 5.7 Alteração de Turno

A qualquer momento.

O usuário poderá abrir.

Funcionários.

↓

Selecionar funcionário.

↓

Alterar turno.

↓

Salvar.

Nenhum código deverá ser alterado.

---

## 5.8 Estrutura do Cadastro

Cada funcionário possuirá.

ID.

Nome.

Turno.

Status.

Data de Cadastro.

Última Atualização.

Tudo armazenado em:

dados/funcionarios.json

---

## 5.9 Atualização Automática

Sempre que uma nova planilha for processada.

O sistema deverá:

Atualizar automaticamente.

Última competência processada.

Última data de processamento.

Sem necessidade de intervenção do usuário.
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

O sistema deverá identificar automaticamente os sábados.

Não será permitido configurar isso manualmente.

Para sábados.

Esperado:

2 batidas.

Entrada.

↓

Saída.

Não existe horário de almoço.

---

## 6.5 Domingo

O sistema deverá identificar automaticamente os domingos.

Todo horário registrado no domingo deverá ser considerado Hora Extra.

Independentemente da quantidade de batidas.

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

Sábado.

Situação normal.

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

Caso exista tolerância configurada.

Ela deverá ser aplicada automaticamente.

Exemplo.

Entrada prevista.

07:30

Entrada registrada.

07:34

Tolerância.

5 minutos.

Resultado.

Sem atraso.

---

## 8.2 Almoço

A tolerância do almoço deverá funcionar da mesma maneira.

---

## 8.3 Sem Tolerância

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

---

## 9.3 Tela de Pendências

Antes do relatório.

O sistema exibirá uma tela contendo todas as pendências encontradas.

Cada pendência poderá ser resolvida individualmente.

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

Todo saldo positivo será Hora Extra.

---

## 10.6 Sábado

Será utilizada a jornada cadastrada para sábado.

---

## 10.7 Reprocessamento

Sempre que o usuário alterar qualquer horário.

O sistema deverá recalcular automaticamente.

Sem necessidade de processar novamente toda a planilha.
# CAPÍTULO 11

# GERAÇÃO DO RELATÓRIO

## 11.1 Objetivo

A Calculadora de Horas Extras Qualimix nunca alterará a planilha oficial exportada pelo relógio de ponto.

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

• Entrada

• Saída para Almoço

• Retorno do Almoço

• Saída

• Horas Trabalhadas

• Horas Extras

• Horas Negativas

• Saldo

• Situação

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

Calculadora de Horas Extras Qualimix

Nome da empresa

Competência

Data do processamento

Hora do processamento

Logo da empresa

---

## 11.6 Rodapé

No rodapé deverá ser exibido:

"Este relatório foi gerado automaticamente pela Calculadora de Horas Extras Qualimix."

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

Nesta tela será possível visualizar todos os funcionários cadastrados.

Mostrar:

• Nome

• ID

• Turno

• Status

• Última competência processada

Permitir:

Alterar turno.

Ativar funcionário.

Inativar funcionário.

Nunca alterar o nome ou o ID importado da planilha.

---

## 12.5 Tela Configurações

Permitir alterar:

• Nome da empresa

• Logo

• Turnos

• Tolerância Entrada

• Tolerância Almoço

• Pasta do Histórico

Todas as alterações deverão ser salvas automaticamente.

---

## 12.6 Tela Histórico

Mostrar todos os relatórios gerados.

Organizados por:

Ano

↓

Mês

↓

Relatório

Permitir abrir diretamente pelo sistema.

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

Resultado

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

Horas Trabalhadas

Horas Extras

Horas Negativas

Saldo

Situação

Pendência

Essa estrutura será utilizada por todos os módulos do sistema.

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

# FIM DA ESPECIFICAÇÃO
