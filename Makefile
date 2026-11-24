# Atalhos para o dia a dia (Linux e macOS; no Windows use os comandos `docker compose` do README).
# `make` sem argumento lista os comandos.

COMPOSE ?= docker compose
ARQ_DECISOES ?= semantica/decisoes/decisoes_agentes.csv

.DEFAULT_GOAL := ajuda
.PHONY: ajuda setup carga ouro compras decisoes exportar painel testes status parar

ajuda:  ## lista os comandos
	@grep -E '^[a-z_]+:.*## ' $(MAKEFILE_LIST) | awk -F':.*## ' '{printf "  make %-10s %s\n", $$1, $$2}'

setup:  ## cria o .env com senhas aleatórias (não sobrescreve um .env existente)
	@if [ -f .env ]; then echo ".env já existe: nada a fazer."; else \
	  cp .env.example .env && chmod 600 .env && \
	  for v in SENHA_DO_BANCO SENHA_DO_PAINEL SENHA_DE_ACESSO_DO_PAINEL; do \
	    s=$$(head -c 18 /dev/urandom | od -An -tx1 | tr -d ' \n'); \
	    if grep -q "^$$v=" .env; then sed -i "s/^$$v=.*/$$v=$$s/" .env; else echo "$$v=$$s" >> .env; fi; \
	  done; \
	  echo ".env criado com senhas aleatórias. Vale para um banco novo: um volume já existente mantém a senha antiga."; fi

carga:  ## sobe tudo do zero: banco, ingestão, dbt, busca, compras, ouro, exportação e painel
	$(COMPOSE) up --build -d

ouro:  ## refaz só o dbt de compras/ouro e a exportação (depois de mudar decisões ou métricas)
	$(COMPOSE) run --build --rm --no-deps transformar_ouro
	$(COMPOSE) run --build --rm --no-deps exportar

compras:  ## baixa as compras que faltam (retoma de onde parou) e refaz ouro e exportação
	$(COMPOSE) run --build --rm --no-deps compras
	$(MAKE) ouro

decisoes:  ## reimporta o CSV de decisões e refaz ouro, SEM refazer a busca (minutos, não dezenas de minutos)
	$(COMPOSE) run --build --rm --no-deps semantica sh -c "python -m semantica importar --arquivo $(ARQ_DECISOES) --revisor agente --tipo-revisor agente && python -m semantica validar"
	$(MAKE) compras

exportar:  ## regrava o CSV de alertas em dados/saida
	$(COMPOSE) run --build --rm --no-deps exportar

painel:  ## sobe só o painel e mostra o endereço
	$(COMPOSE) up -d --build painel
	@echo "Painel em http://localhost:$$(grep -s '^PORTA_DO_PAINEL=' .env | cut -d= -f2 | grep . || echo 8501)"

testes:  ## roda os testes Python num Postgres descartável (não toca no banco do projeto)
	@$(COMPOSE) build -q semantica
	@docker network create sigma-testes >/dev/null 2>&1 || true
	@docker run -d --rm --name sigma-pgtestes --network sigma-testes -e POSTGRES_USER=sigma -e POSTGRES_PASSWORD=sigma sigma-unb/postgres-pgvector:16 >/dev/null
	@until docker exec sigma-pgtestes pg_isready -U sigma -q; do sleep 1; done
	@docker run --rm --network sigma-testes -v "$(CURDIR)":/projeto -v /dev/null:/projeto/.env:ro -w /projeto \
	  -e SIGMA_TESTES_BANCO="host=sigma-pgtestes port=5432 user=sigma password=sigma dbname=postgres" \
	  $$($(COMPOSE) config --images | grep semantica) \
	  sh -c "pip install -q pytest python-dotenv requests >/dev/null 2>&1; python -m pytest testes -q --no-header -p no:cacheprovider"; \
	  rc=$$?; docker stop sigma-pgtestes >/dev/null; exit $$rc

status:  ## mostra o estado de cada serviço
	$(COMPOSE) ps -a --format 'table {{.Service}}\t{{.State}}\t{{.Status}}'

parar:  ## para os serviços (os dados ficam nos volumes)
	$(COMPOSE) stop
