# Testes e validação

## Estratégia

[Que tipos de verificação a squad faz: testes unitários das funções de limpeza, testes de carga, checagens de qualidade no banco.]

## Como rodar

```bash
docker compose run --rm ingest pytest        # [ajuste se usar outra ferramenta]
```

## Testes automatizados

| Arquivo | O que testa | Status |
|---|---|---|
| `tests/test_normalizar.py` | Funções de `normalizar.py` (texto, números, datas) | [✅/⏳] |
| [..] | [..] | [..] |

## Checagens de qualidade dos dados

| Checagem | Consulta / regra | Resultado esperado | Resultado obtido |
|---|---|---|---|
| Sem duplicatas em [tabela] | `SELECT .. GROUP BY .. HAVING count(*) > 1` | 0 linhas | |
| Chaves estrangeiras válidas | [..] | 0 órfãos | |
| Preço unitário > 0 | [..] | 0 linhas | |
| Carga idempotente | Rodar `ingest` 2x e comparar contagens | Contagens iguais | |
| Sobe do zero | `docker compose down -v && docker compose up --build` | Exited (0) | |

## Última execução

**Data:** DD/MM/AAAA — **Commit:** `[hash]` — **Resultado:** [..]
