# ESPECIFICAÇÃO OFICIAL

# Calculadora de Horas Extras - Qualimix

Versão: 1.0

Desenvolvido por: Nathan Adrian

---

# 1. Objetivo

Desenvolver um sistema desktop para Windows capaz de ler automaticamente a planilha de ponto da empresa, calcular horas trabalhadas, horas extras, identificar pendências e gerar um relatório profissional em Excel.

O sistema deverá ser simples de utilizar, confiável, rápido e totalmente configurável sem necessidade de alterar o código.

A planilha original nunca será modificada.

---

# 2. Público-alvo

Departamento de Recursos Humanos.

Gerência.

Administração.

---

# 3. Entrada do Sistema

O sistema deverá aceitar:

- Arquivos XLS
- Arquivos XLSX

Exportados pelo sistema de ponto da empresa.

---

# 4. Saída

Gerar um único arquivo Excel (.xlsx).

O arquivo conterá duas abas.

Aba 1

Relatório Diário.

Aba 2

Resumo Mensal.

---

# 5. Fluxo Geral

Selecionar planilha

↓

Leitura automática

↓

Identificação dos funcionários

↓

Identificação da competência

↓

Validação

↓

Cadastro inteligente

↓

Pendências

↓

Correções

↓

Cálculo

↓

Geração do relatório

↓

Histórico

↓

Fim

---

# 6. Primeira Configuração

Na primeira execução o sistema deverá perguntar:

Nome da empresa.

Logo da empresa.

Turnos existentes.

Tolerância para entrada.

Tolerância para almoço.

Pasta do histórico.

Salvar todas as configurações.

Nunca perguntar novamente.

---

# 7. Cadastro Inteligente

Na primeira planilha.

O sistema deverá:

Ler automaticamente todos os funcionários.

Solicitar apenas o turno.

Salvar o cadastro.

Nas próximas planilhas.

Detectar automaticamente:

Funcionários novos.

Funcionários ausentes.

Funcionários inativos.

Solicitar apenas o turno dos novos funcionários.

---

# 8. Jornadas

Turno A

06:00 às 15:00

Turno B

07:30 às 16:30

Sábado

Duas batidas.

Domingo

Todo horário deverá ser considerado hora extra.

---

# 9. Batidas

Segunda a sexta.

Esperado:

4 horários.

Sábado.

Esperado:

2 horários.

---

# 10. Pendências

O sistema deverá identificar automaticamente:

Funcionário sem nenhuma batida.

Funcionário com batidas incompletas.

Horários inconsistentes.

Novo funcionário.

---

# 11. Justificativas

Ausência:

- Falta
- Falta Justificada
- Férias
- Folga
- Afastamento
- Licença
- Licença Maternidade
- Licença Paternidade
- Consulta Médica
- Atestado Médico
- Serviço Externo
- Treinamento
- Desligamento
- Outro

Batidas incompletas:

- Esqueceu de bater
- Ponto não registrou
- Entrada autorizada
- Saída autorizada
- Consulta Médica
- Serviço Externo
- Outro

Sempre permitir observação.

---

# 12. Cálculos

Calcular automaticamente:

Horas trabalhadas.

Horas extras.

Horas negativas.

Saldo diário.

Aplicar as tolerâncias configuradas.

---

# 13. Relatórios

Aba 1.

Uma linha por funcionário.

Mostrar:

Funcionário.

Data.

Dia da semana.

Turno.

Entrada.

Saída almoço.

Volta almoço.

Saída.

Horas trabalhadas.

Horas extras.

Horas negativas.

Saldo.

Situação.

Justificativa.

Observação.

---

Aba 2.

Resumo mensal.

Mostrar:

Dias trabalhados.

Horas trabalhadas.

Horas extras.

Horas negativas.

Faltas.

Férias.

Afastamentos.

Pendências.

---

# 14. Histórico

Salvar automaticamente.

Historico/

Ano/

Mês/

Nunca substituir arquivos.

---

# 15. Logs

Registrar:

Data.

Hora.

Arquivo utilizado.

Quantidade de funcionários.

Pendências.

Erros.

Relatório gerado.

---

# 16. Interface

Utilizar CustomTkinter.

Tema escuro.

Visual moderno.

Botões grandes.

Interface simples.

---

# 17. Configurações

Permitir alterar:

Empresa.

Logo.

Turnos.

Tolerâncias.

Funcionários.

Pasta do histórico.

Sem necessidade de alterar código.

---

# 18. Objetivo Final

Gerar automaticamente um relatório profissional da folha de ponto da Qualimix com o menor número possível de intervenções manuais.