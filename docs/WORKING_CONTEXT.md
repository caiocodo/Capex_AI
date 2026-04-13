# Contexto Canônico de Trabalho

Este é o documento canônico de contexto operacional, técnico e decisório do projeto
Capex_AI. Ele é a única documentação operacional e contextual que deve orientar
trabalho futuro no repositório. Deve ser lido antes de qualquer modificação futura e
atualizado ao final de cada rodada relevante que altere código, testes, scripts,
decisões de escopo, regras de negócio ou contexto operacional.

Uso esperado em futuras threads do Codex:
- iniciar pelo conteúdo deste documento, sem depender de longos prompts históricos;
- distinguir fatos confirmados, regras definidas, hipóteses, problemas em aberto e
  registros históricos;
- tratar registros históricos como contexto de auditoria, não como bloqueios
  automáticos para rodadas futuras;
- quando o prompt vigente conflitar com este documento, seguir o prompt vigente e
  atualizar este documento ao final da rodada se a decisão permanecer válida.

## 1. Objetivo do projeto

O projeto é uma base Python para carga, validação estrutural, modelagem relacional e
análise operacional de dados Capex a partir de um workbook Excel real.

Objetivos confirmados:
- organizar a fundação técnica do projeto;
- manter modelo relacional confiável, qualidade de dados e rastreabilidade;
- validar schema, tabelas, colunas e relações antes de análises de negócio;
- permitir operação por especialista via scripts CLI;
- manter a lógica principal no core reutilizável do pacote;
- usar scripts apenas como wrappers finos de entrada do usuário;
- evitar UI web, desktop ou similar nesta fase;
- trabalhar por prompts para o Codex atuar diretamente no repositório.

O projeto não deve ser tratado como uma aplicação de UI. O caminho esperado é uso local,
controlado, por CLI e testes automatizados.

## 2. Regras operacionais obrigatórias para qualquer trabalho futuro com Codex

Antes de qualquer mudança futura:
- ler este documento;
- verificar o estado atual do repositório;
- planejar antes de mudanças não triviais;
- separar fatos confirmados, regras já definidas, hipóteses e achados pendentes;
- preservar mudanças existentes de terceiros ou do usuário;
- não assumir histórico externo que não esteja presente no repositório ou no prompt vigente.

Durante qualquer mudança futura:
- não criar UI;
- manter mudanças pequenas, incrementais e auditáveis;
- reaproveitar o máximo possível do que já existe;
- não alterar regra de negócio silenciosamente;
- usar TDD para mudança funcional;
- só considerar algo pronto quando houver teste e execução real;
- validar relações e qualidade estrutural antes de análise de negócio;
- manter scripts como wrappers finos;
- manter lógica principal no core do projeto;
- tratar relações entre tabelas como fatos conhecidos do modelo de dados;
- lembrar que a existência de chaves relacionadas não implica match completo,
  cobertura completa ou correspondência total entre os dois lados.

Ao final de qualquer mudança futura:
- rodar lint e testes aplicáveis;
- registrar no documento o que mudou, quais decisões foram tomadas e quais dúvidas permanecem;
- não espalhar contexto operacional em novos documentos paralelos.

## 3. Arquitetura e princípios de engenharia já definidos

Stack esperada nesta fase:
- pandas;
- pytest;
- ruff.

Arquitetura operacional:
- `configs/schema.yaml` descreve tabelas, aliases, colunas e relações conhecidas;
- `src/capex_ai/` concentra o core reutilizável;
- `scripts/` contém pontos de entrada CLI;
- `tests/` contém a suíte automatizada;
- `tests/fixtures/Capex AI - Dados.xlsx` é o workbook real de validação.

Princípios consolidados:
- core primeiro, CLI fina depois;
- validação estrutural antes de análise de negócio;
- relações tratadas como fatos conhecidos do modelo, com qualidade e cobertura a validar;
- evitar refactor amplo sem necessidade;
- documentar dúvidas em vez de transformar hipótese em fato;
- usar o workbook real para validação de comportamento relevante.

Comandos operacionais consolidados do antigo `README.md`:

```bash
python -m pip install -e ".[dev]"
python scripts/preflight_check.py
pytest -rs
pytest -rs -m core
pytest -rs -m integration
ruff check src tests scripts
python scripts/load_workbook.py /caminho/para/workbook.xlsx
python scripts/validate_relations.py /caminho/para/workbook.xlsx
python scripts/materialize_views.py /caminho/para/workbook.xlsx
python scripts/analyze_orphans.py /caminho/para/workbook.xlsx
python scripts/summarize_costs_by_wo.py /caminho/para/workbook.xlsx
python scripts/run_analysis.py --list
python scripts/run_analysis.py --analysis-id orphan_records --excel-path /caminho/para/workbook.xlsx
```

Regras de execução:
- executar scripts a partir da raiz do repositório;
- usar `--help` para smoke de CLI quando não for necessário carregar workbook;
- antes de validar pipeline real, executar `python scripts/preflight_check.py`;
- dependências obrigatórias de runtime: `pandas`, `PyYAML` e `openpyxl`;
- testes core não devem passar por skip que mascare ausência de runtime;
- testes de integração/E2E são marcados com `integration`.

## 4. Workbook de validação e modelo de dados

Fato confirmado pelo prompt e pelo repositório:
- o workbook real de validação é `tests/fixtures/Capex AI - Dados.xlsx`;
- o arquivo existe no repositório;
- o schema canônico está em `configs/schema.yaml`;
- o projeto espera um único workbook Excel com 5 tabelas/abas canônicas.
- há mapeamento explícito entre nomes originais de tabela e aliases internos;
- as validações operacionais de ingestão incluem abas esperadas, colunas obrigatórias
  por aba e normalização leve de nomes de colunas, incluindo trim, comparação
  case-insensitive e tratamento de espaços.

Observação importante: este documento não substitui `configs/schema.yaml` como fonte técnica
de colunas e relações configuradas. O schema continua sendo a fonte executável. Este
documento registra o contexto operacional e decisório.

## 5. Tabelas, aliases e relações conhecidas

Tabelas e aliases internos:

| Tabela original | Alias interno |
| --- | --- |
| `admafecost` | `admafecost` |
| `INV-AFE` | `inv_afe` |
| `INVOICECOST` | `invoicecost` |
| `multiassetlocci` | `multiassetlocci` |
| `WO-AFES` | `wo_afes` |

Relações conhecidas do modelo de dados:

| Relação | Coluna esquerda | Coluna direita |
| --- | --- | --- |
| `WO-AFES` -> `admafecost` | `WO-AFES.wonum` | `admafecost.wonum` |
| `WO-AFES` -> `INV-AFE` | `WO-AFES.wonum` | `INV-AFE.refwo` |
| `WO-AFES` -> `multiassetlocci` | `WO-AFES.wonum` | `multiassetlocci.recordkey` |
| `INVOICECOST` -> `multiassetlocci` | `INVOICECOST.CHAVE_WO_CODE` | `multiassetlocci.CHAVE_WO_CODE` |

Regra de interpretação:
- essas relações são fatos conhecidos do modelo de dados do projeto;
- a existência das chaves relacionadas não implica match completo, cobertura completa
  ou correspondência total entre os dois lados;
- qualidade, cardinalidade e completude dos matches devem ser validadas antes de uso
  analítico;
- não inferir que todo registro de um lado terá correspondência no outro.

## 6. Funcionalidades já implementadas e consideradas parte do sistema final

Confirmado por arquivos presentes no repositório:
- `configs/schema.yaml`;
- loader do workbook em `src/capex_ai/io/excel_loader.py`;
- modelo tipado de schema em `src/capex_ai/models/schema.py`;
- validação relacional em `src/capex_ai/validation/relations.py`;
- join engine e visões base em `src/capex_ai/modeling/join_engine.py`;
- análises iniciais em `src/capex_ai/analysis/`;
- runner/registry em `src/capex_ai/analysis/runner.py` e `src/capex_ai/analysis/registry.py`;
- preflight de runtime em `scripts/preflight_check.py`;
- testes automatizados em `tests/`;
- scripts CLI em `scripts/`.

Funcionalidades de budget tratadas como parte do sistema final pelo prompt e com arquivos
presentes no repositório:
- consulta agregada de budget por `budgetcode` para um `wonum`;
- visão semanal por `budgetcode`.

Arquivos relacionados:
- `src/capex_ai/modeling/budget_views.py`;
- `scripts/get_budget_by_budgetcode.py`;
- `scripts/get_weekly_budget_view.py`;
- `tests/test_multiasset_budget.py`.

Observação de confiança: a presença de arquivos e testes confirma implementação no estado
atual do repositório. A validação funcional completa deve ser feita por testes e execução
real na rodada que alterar comportamento.

## 7. Regras de negócio consolidadas

### Consulta agregada de budget por budgetcode

Regras definidas:
- entrada: `wonum`;
- saída: `budgetcode` único;
- `budget` somado por `budgetcode`;
- ordenação por `budgetcode` crescente.

### Visão semanal por budgetcode

Regras definidas:
- a coluna temporal chama-se `ref_date`;
- `ref_date` deve ser um domingo;
- cada linha representa dados acumulados até o fim desse domingo;
- mostrar as 4 `ref_date` mais recentes com dados;
- `ref_date` em ordem decrescente;
- `budgetcode` em ordem crescente dentro de cada `ref_date`;
- `budget_sum` agregado por `budgetcode`;
- `linecost_sum` exibido deve ser acumulado até a `ref_date`;
- `remaining_budget_pct = ((budget_sum - cumulative_linecost_sum) / budget_sum) * 100`;
- `remaining_budget_pct` pode ser negativo;
- `remaining_budget_pct_delta_vs_prev_week` usa a `ref_date` anterior real do mesmo `budgetcode`;
- mesmo quando não há mudança de uma semana para outra, a linha deve continuar aparecendo;
- a única razão para ocultar uma linha é quando `budget_sum == 0` e `linecost_sum == 0` ao mesmo tempo;
- quando não existe semana anterior, usar a string `Primeira ocorrência`;
- no script, valores monetários devem ser formatados com `R$`;
- na saída CLI semanal, a visualização deve ser quebrada em 4 blocos/tabelas, uma por `ref_date`, com cabeçalho repetido.

### Projects overview

Intenção definida para a tabela:
- `wonum`;
- `budget_sum`;
- `cumulative_linecost_sum`;
- `remaining_budget_pct`;
- `targstartdate`;
- `targcompdate`;
- `extendedtargcompdate`;
- `status`.

Regras definidas:
- `targstartdate = WO-AFES.TARGSTARTDATE`;
- `targcompdate = WO-AFES.TARGCOMPDATE`;
- `extendedtargcompdate = WO-AFES.EXTENDEDTARGCOMPDATE`;
- status `Em andamento` usa `EXTENDEDTARGCOMPDATE` se existir; senão `TARGCOMPDATE`;
- a regra de `Em andamento` usa janela dos últimos 14 dias em relação a `ref_date`;
- excluir somente linhas em que `budget_sum == 0` e `cumulative_linecost_sum == 0` ao mesmo tempo;
- não excluir linhas só porque `budget == 0`;
- não excluir linhas só porque `cost == 0`;
- ordenar por `budget_sum` do maior para o menor;
- ordenação secundária por `cumulative_linecost_sum`, também do maior para o menor.

## 8. Problema em aberto: `projects_overview`

Problema em aberto:
- `projects_overview` ainda precisa de auditoria e eventual correção em rodada futura;
- este documento não declara que a implementação atual esteja correta ou final.

Fatos confirmados no repositório:
- existe implementação em `src/capex_ai/modeling/projects_overview.py`;
- existe wrapper CLI em `scripts/get_projects_overview.py`;
- existem testes em `tests/test_projects_overview.py`.

Classificação de confiança:
- a intenção e as regras acima são regras definidas;
- a implementação atual deve ser tratada como estado presente, não como validação final;
- resultados antigos sobre `projects_overview` não devem ser tratados como verdade sem reverificação;
- futuras alterações devem começar por teste ou reprodução concreta com o workbook real.

Ponto de cuidado:
- `BM9-176428` foi usado repetidamente como caso de teste;
- existe preocupação de contaminação de análises anteriores por esse foco;
- próximas auditorias devem diversificar casos e registrar método, dados e resultado.

## 9. Hipóteses, achados anteriores e nível de confiança

| Item | Classificação | Confiança | Observação |
| --- | --- | --- | --- |
| `configs/schema.yaml` lista 5 tabelas, aliases e relações | Fato confirmado por arquivo | Alta | Confirmado por leitura do arquivo. |
| Workbook real em `tests/fixtures/Capex AI - Dados.xlsx` | Fato confirmado por arquivo e prompt | Alta | Arquivo presente no repositório. |
| Relações entre tabelas fazem parte do modelo conhecido | Fato confirmado/regra definida | Alta | Estão no prompt, no schema e nesta documentação canônica. |
| Relações têm match completo, cobertura completa ou correspondência total entre lados | Hipótese não provada | Baixa | Não assumir completude sem validação relacional. |
| Budget por `budgetcode` e visão semanal fazem parte do sistema final | Regra definida pelo prompt, com arquivos presentes | Alta | Não implica ausência de bugs futuros. |
| `projects_overview` está resolvido | Achado não confirmado | Baixa | O prompt define que o problema ainda está aberto. |
| Resultados antigos de investigações | Achados a reverificar | Baixa | Não há base suficiente neste documento para tratá-los como fatos. |
| Uso recorrente de `BM9-176428` pode ter contaminado conclusões | Risco registrado | Média | Preocupação explícita do prompt; exige auditoria futura. |
| `UDD-918308` é o valor correto, não `BM9-918308` | Correção definida pelo prompt | Alta | Usar `UDD-918308` em futuras auditorias. |
| Exports JSON antigos em `dev_utils/print_json_for_llm_help/` representam estado atual | Item obsoleto removido | Alta | Eram snapshots antigos para LLM e não eram fonte de verdade. |

## 10. Lista de wonums relevantes para futuras auditorias

Usar esta lista como conjunto inicial de auditoria futura, sem tratar qualquer resultado
anterior como verdade automática:
- `BM9-132818`;
- `BM9-132814`;
- `BM9-176552`;
- `UDD-918308`;
- `BM9-186541`;
- `BM9-176428`.

Correção obrigatória:
- `UDD-918308` corrige o valor anteriormente citado como `BM9-918308`;
- não usar `BM9-918308` sem confirmação independente no workbook.

## 11. Limites permanentes e problemas em aberto

Limites permanentes do projeto nesta fase:
- não criar UI web, desktop ou similar;
- manter scripts como entrada CLI fina;
- preservar lógica principal no core reutilizável;
- validar estrutura e relações antes de análise de negócio;
- não alterar regra de negócio silenciosamente.

Problemas em aberto:
- `projects_overview` requer auditoria em rodada futura;
- achados antigos e resultados de investigações anteriores precisam de reverificação antes
  de virar fato;
- cobertura e qualidade de matches das relações devem ser medidas com dados reais antes
  de sustentar análise de negócio.

## 12. Próximos passos recomendados, sem executá-los agora

Próximos passos sugeridos para rodadas futuras:
- auditar `projects_overview` com o workbook real e lista diversificada de wonums;
- transformar comportamento esperado de `projects_overview` em testes antes de alterar
  implementação;
- validar regras de cálculo de `projects_overview` contra dados reais e decisões
  explícitas, sem assumir origem de campos por inferência;
- registrar método, entradas, resultados e dúvidas da auditoria;
- rodar `python scripts/preflight_check.py` antes de validação real;
- rodar testes e ruff ao final de qualquer alteração funcional;
- atualizar este documento com decisões, comandos executados e resultado.

Esses passos são recomendações. Devem ser executados apenas quando forem escopo do
prompt vigente.

## 13. Atualização contínua e registro histórico de rodadas

Esta seção registra decisões e restrições de rodadas passadas. Ela serve como trilha de
auditoria e não limita automaticamente trabalhos futuros. Regras permanentes ficam nas
seções anteriores; restrições temporárias valem apenas para a rodada em que foram
registradas, salvo se forem promovidas explicitamente a regra permanente.

Instruções permanentes de atualização contínua:
- ao iniciar trabalho futuro, ler este documento;
- ao terminar trabalho futuro relevante, acrescentar uma entrada curta nesta seção;
- registrar decisões de negócio separadas de achados técnicos;
- registrar dúvidas explicitamente;
- se um arquivo documental novo parecer necessário, preferir incorporar seu conteúdo aqui;
- se outro documento divergir deste, tratar este documento como canônico até que seja atualizado deliberadamente.

### Registro histórico

2026-04-13, consolidação canônica inicial:
- `docs/WORKING_CONTEXT.md` passa a ser a única documentação canônica operacional,
  contextual e decisória do projeto;
- `AGENTS.md` é mantido como instrução operacional mínima para agentes e aponta para
  este documento;
- conteúdo útil e ainda válido do antigo `README.md` foi incorporado aqui: foco do
  projeto, escopo de ingestão, validações operacionais, comandos, caminho oficial de
  execução e critério mínimo de aceite;
- conteúdo útil do antigo `docs/README.md` já está incorporado aqui pela descrição da
  fundação técnica do projeto;
- `README.md`, `docs/README.md`, prompt genérico em `dev_utils/` e snapshots JSON antigos
  foram removidos para evitar fontes paralelas, redundantes ou enganosas;
- arquivos de cache, logs de execução e metadados gerados podem ser removidos por não serem fonte confiável;
- `projects_overview` permanece aberto e não foi corrigido nesta rodada.

Inventário documental dessa consolidação:

| Item | Classificação | Decisão |
| --- | --- | --- |
| `docs/WORKING_CONTEXT.md` | Manter como canônico | Documento único de trabalho futuro. |
| `AGENTS.md` | Exceção operacional obrigatória | Preservado; instrução mínima para ler e atualizar este documento. |
| `README.md` | Útil e ainda válido, mas redundante após consolidação | Conteúdo incorporado; arquivo removido. |
| `docs/README.md` | Redundante | Conteúdo já incorporado; arquivo removido. |
| `dev_utils/_prompt para usar com JSON.txt` | Temporário e não confiável como contexto do projeto | Arquivo removido. |
| `dev_utils/print_json_for_llm_help/*.json` | Obsoleto e potencialmente enganoso | Snapshots antigos removidos. |
| `requirements.txt` | Arquivo funcional de dependências, não documentação | Preservado. |
| `pyproject.toml` | Configuração funcional do pacote, não documentação | Preservado. |
| `configs/schema.yaml` | Configuração executável do modelo de dados, não documentação paralela | Preservado. |
| `main.py`, `project.py`, `shared_vars.py`, `dev_utils/*.py` | Código ou utilitários, não documentação canônica | Preservados sem alteração. |
| `scripts/`, `src/`, `tests/`, `tests/fixtures/` | Código, testes, scripts e fixture real | Preservados sem alteração nesta rodada. |

2026-04-13, saneamento documental:
- criada consolidação canônica em `docs/WORKING_CONTEXT.md`;
- registrada separação entre fatos, regras, hipóteses e achados a reverificar;
- registrado que `projects_overview` segue aberto;
- registrado que `UDD-918308` corrige `BM9-918308`;
- registrado inventário documental e plano de saneamento seguro de artefatos temporários.

2026-04-13, rodada de limpeza documental final:
- incorporado conteúdo útil de `README.md` e `docs/README.md` neste documento;
- reforçado que `docs/WORKING_CONTEXT.md` é a única documentação operacional canônica;
- removidos `README.md`, `docs/README.md`, prompt genérico em `dev_utils/` e snapshots JSON antigos;
- preservados `AGENTS.md`, arquivos de configuração funcional, código, scripts, testes e fixtures;
- nenhuma feature, bugfix, investigação de `projects_overview` ou expansão de testes foi realizada.

2026-04-13, refinamento para uso em futuras threads:
- removida do corpo normativo a linguagem de restrições temporárias de rodadas passadas;
- reforçada a separação entre fatos confirmados, regras definidas, hipóteses, problemas em aberto e histórico;
- reescrita a descrição das relações como fatos conhecidos do modelo que não garantem
  match completo, cobertura completa ou correspondência total;
- revisados próximos passos para recomendar auditoria, TDD e validação concreta sem
  sugerir origem de campos por inferência;
- nenhum código, teste, script, schema ou comportamento funcional foi alterado.
