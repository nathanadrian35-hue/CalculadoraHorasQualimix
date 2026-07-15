# Calculadora de Horas Extras - Qualimix

> Sistema desktop desenvolvido para automatizar o processamento da folha de ponto da Qualimix.

**Desenvolvido por:** Nathan Adrian

---

# Objetivo

A Calculadora de Horas Extras da Qualimix é um sistema desktop desenvolvido em Python para automatizar a leitura da planilha de ponto da empresa, identificar inconsistências, calcular horas trabalhadas, horas extras e gerar relatórios profissionais em Excel.

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
    configuracoes.json
    funcionarios.json
    turnos.json
    versao.json

backup/

Historico/

Logs/

README.md
CLAUDE.md
ESPECIFICACAO.md
TODO.md

main.py
interface.py

tela_principal.py
tela_configuracoes.py
tela_funcionarios.py
tela_historico.py
tela_sobre.py

config.py
cadastro.py
validacao.py
leitor_ponto.py
calculadora.py
relatorio.py

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

## Cadastro Inteligente

Na primeira utilização:

- Ler todos os funcionários automaticamente.
- Solicitar apenas o turno de trabalho.
- Salvar cadastro.

Nas próximas importações:

- Detectar novos funcionários.
- Solicitar somente o turno.
- Atualizar cadastro automaticamente.

---

## Configuração Inicial

Na primeira execução:

- Nome da empresa
- Logo
- Turnos
- Tolerâncias
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
- Batidas incompletas
- Novos funcionários
- Horários inconsistentes

Permitir justificativas antes da geração do relatório.

---

## Relatórios

Gerar um único arquivo Excel contendo:

### Aba 1

Relatório Diário.

### Aba 2

Resumo Mensal.

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
- Gerar Relatório
- Funcionários
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

Cadastro inteligente

↓

Validação

↓

Pendências

↓

Correções

↓

Cálculo

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

# Futuras Versões

- Dashboard
- Estatísticas
- Gráficos
- Banco de dados
- Integração com relógio de ponto
- Relatórios PDF

---

# Licença

Sistema interno da Qualimix.

Desenvolvimento:

Nathan Adrian.