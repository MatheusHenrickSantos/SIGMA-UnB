# Imagem do serviço `db`: a mesma base usada até aqui (postgres:16-alpine),
# acrescida da extensão pgvector, usada pela busca semântica (schema semantica).
#
# Por que compilar em vez de trocar para a imagem pgvector/pgvector:pg16?
# Aquela imagem é baseada em Debian (glibc); esta é Alpine (musl). As duas
# ordenam texto de forma diferente, e o volume pgdata de quem já subiu o
# projeto tem índices de texto (UNIQUE em material, almoxarifado, credor...)
# construídos com a ordenação do Alpine. Manter a mesma base preserva o volume.
FROM postgres:16-alpine

# Versão fixa: trocar só por decisão explícita (ver docs/semantica.md).
ARG PGVECTOR_VERSAO=v0.8.7

# OPTFLAGS="" evita -march=native, para a imagem rodar em qualquer CPU.
# with_llvm=no pula o bitcode de JIT, que exigiria o clang na mesma versão
# usada para compilar o PostgreSQL da imagem base.
RUN apk add --no-cache --virtual .deps-pgvector build-base git \
    && git clone --branch "${PGVECTOR_VERSAO}" --depth 1 \
       https://github.com/pgvector/pgvector.git /tmp/pgvector \
    && make -C /tmp/pgvector OPTFLAGS="" with_llvm=no \
    && make -C /tmp/pgvector install with_llvm=no \
    && rm -rf /tmp/pgvector \
    && apk del .deps-pgvector
