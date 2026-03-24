# Capex_AI (fundação)

Projeto Python para fundação de monitoramento e análise de gastos de projetos, com foco em:
- modelo relacional confiável;
- qualidade de dados;
- rastreabilidade.

## Escopo desta rodada
- Carga de dados a partir de **um único arquivo Excel** com 5 abas.
- Mapeamento explícito entre nomes originais de tabela e aliases internos.
- Estrutura inicial de validação de relações como hipóteses operacionais.
- Base de testes/lint (`pytest` e `ruff`).

## Estrutura principal
- `configs/schema.yaml`: definição de tabelas, aliases, colunas e relações conhecidas.
- `src/capex_ai/io/excel_loader.py`: carregamento das abas do Excel.
- `src/capex_ai/models/schema.py`: modelo tipado do schema.
- `src/capex_ai/validation/relations.py`: validação estrutural mínima das relações.
- `tests/`: testes iniciais.

## Comandos
```bash
python -m pip install -e ".[dev]"
pytest
ruff check .
```
