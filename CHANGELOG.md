# Changelog

Todas as mudanças notáveis do QualiPonto são documentadas neste arquivo.

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
