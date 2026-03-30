# Capex_AI (fundação)

Projeto Python para fundação de monitoramento e análise de gastos de projetos, com foco em:
- modelo relacional confiável;
- qualidade de dados;
- rastreabilidade.

## Escopo atual
- Carga de dados a partir de **um único arquivo Excel** com 5 abas canônicas.
- Mapeamento explícito entre nomes originais de tabela e aliases internos.
- Validações operacionais de ingestão:
  - abas esperadas
  - colunas obrigatórias por aba
  - normalização leve de nomes de colunas (trim, case-insensitive, espaços)

## Estrutura principal
- `configs/schema.yaml`: fonte da verdade de tabelas/colunas/relações conhecidas.
- `src/capex_ai/io/excel_loader.py`: API de ingestão do workbook.
- `src/capex_ai/models/schema.py`: modelo tipado do schema.
- `src/capex_ai/validation/relations.py`: validação relacional mínima já existente.
- `scripts/load_workbook.py`: script operacional de carga.
- `tests/`: testes automatizados.

## Comandos
```bash
python -m pip install -e ".[dev]"
pytest
ruff check src tests
python scripts/load_workbook.py /caminho/para/workbook.xlsx
python scripts/validate_relations.py /caminho/para/workbook.xlsx
python scripts/materialize_views.py /caminho/para/workbook.xlsx
python scripts/analyze_orphans.py /caminho/para/workbook.xlsx
python scripts/summarize_costs_by_wo.py /caminho/para/workbook.xlsx
python scripts/run_analysis.py --list
python scripts/run_analysis.py --analysis-id orphan_records --excel-path /caminho/para/workbook.xlsx
```


## Caminho oficial de execução
1. Instalar em modo editable: `python -m pip install -e ".[dev]"`
2. Executar scripts a partir da raiz do repositório.
3. Para smoke de CLI: use `--help` (não depende de workbook).
