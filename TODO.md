# TODO - QualiPonto

**Projeto:** QualiPonto — Sistema de Controle de Jornada e Horas Extras

**Desenvolvedor:** Nathan Adrian

---

# STATUS DO PROJETO

🟢 Concluído

🟡 Em desenvolvimento

⚪ Não iniciado

---

# ETAPA 1 - DOCUMENTAÇÃO

| Status | Item |
|--------|------|
| 🟢 | Estrutura do Projeto |
| 🟢 | Git |
| 🟢 | GitHub |
| 🟢 | README.md |
| 🟢 | CLAUDE.md |
| 🟢 | ESPECIFICACAO.md |
| 🟢 | Revisão da Arquitetura |

---

# ETAPA 2 - ARQUITETURA

| Status | Item |
|--------|------|
| 🟢 | Arquitetura Geral |
| 🟢 | Fluxo dos Módulos |
| 🟢 | Estrutura Interna dos Dados |
| 🟢 | Comunicação entre Módulos |

---

# ETAPA 3 - INTERFACE

| Status | Item |
|--------|------|
| 🟢 | Tela Inicial |
| 🟢 | Tela Configurações (Wizard + modo de edição) |
| 🟢 | Tela Funcionários |
| 🟢 | Tela Histórico (listar/pesquisar competências, abrir e excluir relatórios) |
| 🟢 | Tela Sobre |
| 🟢 | Barra de Status |
| 🟢 | Tema Escuro |

---

# ETAPA 4 - CONFIGURAÇÕES

| Status | Item |
|--------|------|
| 🟢 | Configurações da Empresa (Wizard + edição) |
| 🟢 | Cadastro dos Turnos (adicionar/editar/remover, ID preservado) |
| 🟢 | Tolerâncias |
| 🟢 | Logo |
| 🟢 | Configurações JSON |

---

# ETAPA 4.5 - CADASTRO DE SETORES

| Status | Item |
|--------|------|
| 🟢 | Estrutura do Setor (nome, cor, status) |
| 🟢 | Adicionar Setor |
| 🟢 | Editar Setor |
| 🟢 | Ativar/Inativar Setor |
| 🟢 | Excluir Setor (com verificação de vínculo) |
| 🟢 | Persistência setores.json + Backup |
| 🟢 | Acesso pela Tela Principal |

---

# ETAPA 5 - LEITOR DA PLANILHA

| Status | Item |
|--------|------|
| 🟢 | Leitura XLS |
| 🟢 | Leitura XLSX |
| 🟢 | Identificar Competência |
| 🟢 | Identificar Funcionários |
| 🟢 | Identificar Dias |
| 🟢 | Identificar Batidas |
| 🟢 | Identificar Mês |
| 🟢 | Identificar Ano |
| 🟢 | Alimentar o Motor de Sugestão de Turno (Etapa 6) com os dados reais extraídos |
| 🟢 | Localizar Funcionário Cadastrado Automaticamente (Nome na Planilha / Nome Completo) |
| 🟢 | Identificar Campo "Dep." e Sugerir Setor Automaticamente (comparação tolerante) |
| 🟢 | Criação Automática de Setores Novos Encontrados na Planilha (com confirmação do usuário) |

---

# ETAPA 6 - CADASTRO INTELIGENTE ASSISTIDO DE FUNCIONÁRIOS

| Status | Item |
|--------|------|
| 🟢 | Estrutura do Cadastro (ID, Nome Completo, Nome na Planilha, Apelido, Matrícula, CPF, Cargo, Turno, Setor, Status) |
| 🟢 | Cadastro Manual: Adicionar Funcionário |
| 🟢 | Cadastro Manual: Editar Funcionário |
| 🟢 | Cadastro Manual: Excluir Funcionário |
| 🟢 | Cadastro Manual: Ativar/Inativar Funcionário |
| 🟢 | Motor de Sugestão de Turno (compara horário x turnos cadastrados) |
| 🟢 | Classificação de Confiança (✓ Confirmado / ⚠ Revisar) |
| 🟢 | Painel de Revisão (Funcionário / Horário / Turno Sugerido / Situação / Status) |
| 🟢 | Reconhecimento de Funcionário Já Cadastrado (evita duplicação) |
| 🟢 | Importação Parcial (ausentes nunca são excluídos/inativados/desvinculados) |
| 🟢 | Ações em Massa (Turno, Setor, Cargo, Ativar, Inativar) |
| 🟢 | Pesquisa em Tempo Real |
| 🟢 | Ordenação Alfabética |
| 🟢 | Filtros (Status/Setor/Turno) |
| 🟢 | Contadores (Total/Ativos/Inativos) |
| 🟢 | Vínculo com Turno por ID |
| 🟢 | Vínculo com Setor por ID |
| 🟢 | Persistência funcionarios.json + Backup |

---

# ETAPA 7 - MOTOR DE CÁLCULO

| Status | Item |
|--------|------|
| 🟢 | Determinar Jornada do Dia a partir do Turno (Segunda-Sexta/Sábado/Domingo) |
| 🟢 | Horas Trabalhadas |
| 🟢 | Horas Extras |
| 🟢 | Horas Negativas |
| 🟢 | Saldo |
| 🟢 | Sábados (jornada do Turno, sem regra fixa) |
| 🟢 | Domingos (jornada do Turno, sem regra fixa) |
| 🟢 | Aplicar Tolerâncias (faixa de aceitação) |
| 🟢 | Reprocessamento Incremental (recalcular só o dia editado) |
| 🟢 | Resumo Mensal por Funcionário |

Homologado na Sprint 4.1 contra a planilha real da Qualimix.

---

# ETAPA 8 - PENDÊNCIAS

| Status | Item |
|--------|------|
| 🟢 | Sem Batidas |
| 🟢 | Batidas Incompletas |
| 🟢 | Horários Inconsistentes |
| 🟢 | Turno Não Definido |
| 🟢 | Lista de Pendências (paginada e virtualizada, Sprint 4.1) |
| 🟢 | Corrigir Batida (Batida Esquecida) |
| 🟢 | Informar Justificativa |
| 🟢 | Justificativas que Eliminam Hora Negativa (lista central) |
| 🟢 | Observações |
| 🟢 | Aplicar Justificativa por Período (com tratamento de conflitos e confirmação inteligente) |
| 🟢 | Desligamento Inteligente (aplica o período restante e oferece inativar o funcionário) |
| 🟢 | Fluxo inteligente: sem pendência em aberto, pula direto para a Tela de Relatórios |

---

# ETAPA 9 - RELATÓRIO

| Status | Item |
|--------|------|
| 🟢 | Aba Relatório Diário |
| 🟢 | Aba Resumo Mensal |
| 🟢 | Aba Pendências |
| 🟢 | Aba Informações |
| 🟢 | Cabeçalho (com logo) |
| 🟢 | Rodapé |
| 🟢 | Relatório Individual por Funcionário |
| 🟢 | Resumo Geral da Competência |
| 🟢 | Estatísticas da Competência |
| 🟢 | Bloqueio por pendência em aberto |
| 🟢 | Tela de Relatórios (filtros, resumo superior, exportação Excel/Imprimir) |
| 🟢 | Formatação profissional do Excel (cabeçalho, bordas, painel congelado, impressão) |
| ⚪ | Exportação em PDF *(oficialmente fora da interface da v1.0; arquitetura interna reservada para versão futura)* |

---

# ETAPA 10 - HISTÓRICO

| Status | Item |
|--------|------|
| 🟢 | Organização por Ano |
| 🟢 | Organização por Mês |
| 🟢 | Cópia Automática (nomeação incremental, nunca sobrescreve) |
| 🟢 | Tela de Histórico (navegar/abrir relatórios já gerados pelo sistema) |

---

# ETAPA 11 - LOGS

| Status | Item |
|--------|------|
| 🟢 | Registro de Processamento |
| 🟢 | Registro de Erros |
| 🟢 | Registro de Pendências |

---

# ETAPA 11.5 - GERENCIAMENTO DE MÚLTIPLAS COMPETÊNCIAS + IDUSUÁRIO

| Status | Item |
|--------|------|
| 🟢 | Persistência de Competência (funcionários, dias, pendências, justificativas, status) em dados/competencias/ |
| 🟢 | Status da Competência com transição automática (Em andamento / Pendências abertas / Pronta para relatório / Relatório gerado) |
| 🟢 | Arquivar Competência (manual, sem Desarquivar nesta versão) |
| 🟢 | Tela Competências (cards com contadores, status, Abrir/Arquivar) |
| 🟢 | Retomar Trabalho (fechar/reabrir preserva pendências restantes e justificativas já aplicadas) |
| 🟢 | Múltiplas competências coexistindo de forma independente |
| 🟢 | Tela de Relatórios com seletor de competência (geração independente por competência) |
| 🟢 | Importação de competência já existente pergunta Substituir/Cancelar (nunca duplica) |
| 🟢 | Identificação de Funcionário por IDUsuário (identificador principal, diferencia homônimos) |
| 🟢 | Migração automática just-in-time do IDUsuário em cadastros antigos |
| 🟢 | Homologado com as duas planilhas reais (Julho/2026 e Abril/2026) |

---

# ETAPA 12 - FINALIZAÇÃO

| Status | Item |
|--------|------|
| 🟢 | Testes Gerais (homologação funcional completa, planilhas reais) |
| 🟢 | Correções (bugs da homologação corrigidos e retestados) |
| ⚪ | Otimizações |
| 🟢 | Gerar Executável (.exe) — PyInstaller (`--onedir`) + instalador Inno Setup (`QualiPonto_Setup_v1.0.exe`) |
| ⚪ | Teste em Outro Computador |
| ⚪ | Entrega para Empresa |

---

# OBSERVAÇÕES

- A planilha oficial do relógio de ponto nunca será alterada.
- Todo processamento será realizado apenas em memória.
- Todos os resultados serão gravados em um novo arquivo Excel.
- Toda configuração será salva em arquivos JSON.
- O sistema deverá funcionar totalmente offline.
- O projeto será mantido no GitHub desde a primeira versão.

---

# PROGRESSO

Documentação: ██████████ 100%

Desenvolvimento: ██████████ Aproximadamente 98% (falta apenas Exportação em PDF — reservada para versão futura — e testar em outro computador)

Testes: █████████░ Homologação funcional completa (planilhas reais) + regressão manual a cada Sprint, sem suíte automatizada persistente (scripts temporários por sessão)

Projeto: ██████████ Aproximadamente 98% — instalador oficial (QualiPonto_Setup_v1.0.exe) gerado e testado (instalação, atalhos, registro, desinstalação)