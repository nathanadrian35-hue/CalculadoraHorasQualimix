# DESENVOLVIMENTO

## Calculadora de Horas Extras Qualimix

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

# SPRINT 3

## Objetivo

Implementar o leitor da planilha.

### Arquivos

- leitor_ponto.py
- validacao.py
- cadastro.py

### Funcionalidades

- Ler XLS
- Ler XLSX
- Identificar competência
- Identificar funcionários
- Ler dias
- Ler batidas
- Detectar novos funcionários
- Validar estrutura da planilha

### Critério de conclusão

O sistema consegue importar corretamente uma planilha da Qualimix.

---

# SPRINT 4

## Objetivo

Criar o motor de cálculo.

### Arquivo

- calculadora.py

### Funcionalidades

- Horas trabalhadas
- Horas extras
- Horas negativas
- Saldo
- Aplicação das tolerâncias
- Tratamento de sábado
- Tratamento de domingo

### Critério de conclusão

Todos os cálculos devem estar corretos.

---

# SPRINT 5

## Objetivo

Gerar os relatórios.

### Arquivo

- relatorio.py

### Funcionalidades

- Relatório Diário
- Resumo Mensal
- Pendências
- Informações do Processamento
- Cabeçalho
- Rodapé
- Logo da empresa

### Critério de conclusão

O Excel deverá ser gerado corretamente.

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

# REGRAS

- Seguir obrigatoriamente o README.md.
- Seguir obrigatoriamente o CLAUDE.md.
- Seguir obrigatoriamente o ESPECIFICACAO.md.
- Não implementar funcionalidades de outras Sprints.
- Cada módulo deve possuir apenas uma responsabilidade.
- O código deve ser limpo, organizado e documentado.
- Toda alteração deverá ser validada antes de iniciar a próxima Sprint.