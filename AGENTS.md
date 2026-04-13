# AGENTS.md

Instruções para agentes neste repositório (`/workspace/Capex_AI`).

## Princípios de trabalho
- `docs/WORKING_CONTEXT.md` é o documento canônico operacional: leia-o antes de qualquer modificação no projeto e atualize-o ao final de qualquer rodada relevante.
- Sempre planejar antes de mudanças não triviais.
- Manter mudanças pequenas, incrementais e auditáveis.
- Preservar compatibilidade com a estrutura atual do repositório sempre que não houver acoplamento ruim.
- Não criar UI (web, desktop ou similar) nesta fase do projeto.

## Escopo funcional atual
- Priorizar fundação técnica: carga, mapeamento de esquema, validações estruturais e documentação curta.
- Tratar relações entre tabelas como fatos do modelo, validando qualidade e cobertura antes de uso analítico.
- Validar relações e qualidade estrutural dos dados **antes** de qualquer análise de negócio.

## Qualidade mínima obrigatória
- Rodar lint e testes ao final de cada alteração relevante.
- Usar tipagem básica em funções públicas.
- Evitar mudanças grandes sem necessidade.

## Stack esperada nesta fase
- pandas
- pytest
- ruff
