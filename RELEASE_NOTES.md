# Notas de versão — SIGMA-UnB

## [E2] — DD/MM/AAAA

### Adicionado
- [ex.: ADR 0002 — mecanismo de ingestão e formato aberto]
- [ex.: coleta de cotações de mercado no banco]

### Alterado
- [..]

### Corrigido
- [..]

### Migrações
- `V2__[descricao].sql` — [o que faz]

---

## [E1] — DD/MM/AAAA

### Adicionado
- Banco PostgreSQL 16 em Docker Compose
- Migrações versionadas com Flyway (`V1__esquema_inicial.sql`)
- Download automatizado dos 5 datasets do dados.unb.br, com `manifesto.json`
- Carga idempotente no banco, com registro de linhas rejeitadas
- ADR 1 — modelagem da origem
- Site da documentação (Docsify): modelagem, dicionário de dados, DER, modelo relacional
