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

Tela dedicada ("Relatórios"), acessível pela Tela Inicial, com filtros
por Funcionário, Setor, Turno, Cargo e Status, resumo superior
(Funcionários/Horas Extras/Horas Negativas/Pendências) e os botões
Visualizar, Exportar Excel e Imprimir.

A geração é bloqueada enquanto existir qualquer pendência em aberto.

Relatório Geral da Competência: um único arquivo Excel com 4 abas:

### Aba 1

Relatório Diário.

### Aba 2

Resumo Mensal.

### Aba 3

Pendências.

### Aba 4

Informações do Processamento (inclui Estatísticas da Competência).

Também é possível gerar um **Relatório Individual por Funcionário**
(cabeçalho + tabela diária + resumo do funcionário) e o **Resumo
Geral da Competência** é exibido tanto na tela quanto na Aba 4.

O Excel gerado é totalmente editável e tem formatação profissional
para conferência e impressão: cabeçalho em destaque, painel congelado,
bordas, largura de coluna ajustada ao conteúdo e layout em paisagem
pronto para impressão.

---

## Gerenciamento de Múltiplas Competências

Cada planilha importada cria uma **Competência** (mês/ano), persistida
em disco imediatamente após o Motor de Cálculo processar o lote —
funcionários, pendências, justificativas já preenchidas, resumo mensal,
estatísticas e status. Fechar o sistema a qualquer momento nunca perde
esse trabalho.

- Tela dedicada ("Competências"), com um card por competência: data da
  importação, quantidade de funcionários, quantidade de pendências
  (total e resolvidas), status e se já foi gerado relatório.
- **Retomar trabalho:** o botão "Abrir" leva direto às pendências
  restantes (justificativas já aplicadas preservadas) ou, se não
  houver mais nenhuma pendência em aberto, direto para a Tela de
  Relatórios.
- **Múltiplas competências coexistem** de forma totalmente
  independente — a Tela de Relatórios lista todas e gera o relatório
  de qualquer uma sem afetar as demais.
- **Arquivar:** muda o status manualmente; a competência continua
  disponível na Tela de Relatórios (sem ação de Desarquivar nesta
  versão).
- Reimportar uma competência já existente pergunta antes de
  substituir — nunca duplica.

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