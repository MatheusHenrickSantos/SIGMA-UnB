-- V1: esquema inicial do SIGMA-UnB (sistema de origem / OLTP)
--
-- Regras seguidas (ver docs/adr/0001-modelagem-da-origem.md):
--   * cadastros (unidade, material, almoxarifado, natureza, credor) são CRUD:
--     a linha é atualizada no lugar e guarda atualizado_em;
--   * fatos que formam série no tempo (saldo de estoque, cotação) são
--     insert-only: cada carga acrescenta linhas, nada é sobrescrito;
--   * empenho, gasto e requisição são atualizados pela chave natural quando
--     o portal republica o registro (upsert), com atualizado_em.
--   * data_referencia / data_* = hora do evento no mundo real;
--     carregado_em = hora da ingestão no banco.

SET TIME ZONE 'America/Sao_Paulo';

-- ---------------------------------------------------------------------------
-- Controle das cargas
-- ---------------------------------------------------------------------------

CREATE TABLE carga_execucao (
    id_carga          BIGSERIAL PRIMARY KEY,
    dataset           TEXT        NOT NULL,
    arquivo           TEXT        NOT NULL,
    sha256            CHAR(64)    NOT NULL,
    linhas_lidas      INTEGER     NOT NULL DEFAULT 0 CHECK (linhas_lidas >= 0),
    linhas_gravadas   INTEGER     NOT NULL DEFAULT 0 CHECK (linhas_gravadas >= 0),
    linhas_rejeitadas INTEGER     NOT NULL DEFAULT 0 CHECK (linhas_rejeitadas >= 0),
    iniciado_em       TIMESTAMPTZ NOT NULL DEFAULT now(),
    finalizado_em     TIMESTAMPTZ,
    -- o mesmo conteúdo publicado duas vezes no portal só é carregado uma vez
    CONSTRAINT uq_carga_conteudo UNIQUE (dataset, sha256)
);

CREATE TABLE carga_rejeitado (
    id_rejeitado BIGSERIAL PRIMARY KEY,
    id_carga     BIGINT NOT NULL REFERENCES carga_execucao (id_carga) ON DELETE CASCADE,
    registro     JSONB  NOT NULL,
    motivo       TEXT   NOT NULL
);

-- ---------------------------------------------------------------------------
-- Cadastros
-- ---------------------------------------------------------------------------

CREATE TABLE unidade (
    id_unidade             INTEGER PRIMARY KEY,
    nome                   TEXT NOT NULL CHECK (btrim(nome) <> ''),
    sigla                  TEXT,
    sigla_academica        TEXT,
    tipo_organizacional    TEXT,
    tipo_academica         TEXT,
    id_unidade_responsavel INTEGER,
    id_unidade_gestora     INTEGER,
    id_gestora_academica   INTEGER,
    -- 'cadastro': veio do dataset Unidades Acadêmicas;
    -- 'referencia': só apareceu citada em gasto, empenho ou requisição
    --               (unidades administrativas não estão no cadastro do portal)
    fonte                  TEXT NOT NULL DEFAULT 'cadastro'
                           CHECK (fonte IN ('cadastro', 'referencia')),
    carregado_em           TIMESTAMPTZ NOT NULL DEFAULT now(),
    atualizado_em          TIMESTAMPTZ NOT NULL DEFAULT now(),
    -- a hierarquia aponta para a própria tabela; DEFERRABLE deixa carregar
    -- pai e filho na mesma transação sem se preocupar com a ordem
    CONSTRAINT fk_unidade_responsavel FOREIGN KEY (id_unidade_responsavel)
        REFERENCES unidade (id_unidade) DEFERRABLE INITIALLY DEFERRED,
    CONSTRAINT fk_unidade_gestora FOREIGN KEY (id_unidade_gestora)
        REFERENCES unidade (id_unidade) DEFERRABLE INITIALLY DEFERRED,
    CONSTRAINT fk_unidade_gestora_academica FOREIGN KEY (id_gestora_academica)
        REFERENCES unidade (id_unidade) DEFERRABLE INITIALLY DEFERRED
);

CREATE INDEX ix_unidade_responsavel ON unidade (id_unidade_responsavel);
CREATE INDEX ix_unidade_gestora     ON unidade (id_unidade_gestora);

CREATE TABLE almoxarifado (
    id_almoxarifado SERIAL PRIMARY KEY,
    nome            TEXT NOT NULL CHECK (btrim(nome) <> ''),
    id_unidade      INTEGER REFERENCES unidade (id_unidade),
    carregado_em    TIMESTAMPTZ NOT NULL DEFAULT now(),
    atualizado_em   TIMESTAMPTZ NOT NULL DEFAULT now(),
    CONSTRAINT uq_almoxarifado_nome UNIQUE (nome)
);

CREATE TABLE material (
    id_material   SERIAL PRIMARY KEY,
    descricao     TEXT NOT NULL CHECK (btrim(descricao) <> ''),
    termo_busca   TEXT,
    carregado_em  TIMESTAMPTZ NOT NULL DEFAULT now(),
    atualizado_em TIMESTAMPTZ NOT NULL DEFAULT now(),
    CONSTRAINT uq_material_descricao UNIQUE (descricao)
);

CREATE TABLE natureza_despesa (
    id_natureza   SERIAL PRIMARY KEY,
    descricao     TEXT NOT NULL CHECK (btrim(descricao) <> ''),
    carregado_em  TIMESTAMPTZ NOT NULL DEFAULT now(),
    CONSTRAINT uq_natureza_descricao UNIQUE (descricao)
);

-- Credor pode ser pessoa física (dado pessoal). Fica separado para facilitar
-- mascarar e restringir acesso (LGPD).
CREATE TABLE credor (
    id_credor     SERIAL PRIMARY KEY,
    nome          TEXT NOT NULL CHECK (btrim(nome) <> ''),
    carregado_em  TIMESTAMPTZ NOT NULL DEFAULT now(),
    CONSTRAINT uq_credor_nome UNIQUE (nome)
);

-- ---------------------------------------------------------------------------
-- Estoque (insert-only: uma foto do saldo por mês de referência)
-- ---------------------------------------------------------------------------

CREATE TABLE estoque_saldo (
    id_material     INTEGER       NOT NULL REFERENCES material (id_material),
    id_almoxarifado INTEGER       NOT NULL REFERENCES almoxarifado (id_almoxarifado),
    data_referencia DATE          NOT NULL,
    saldo           NUMERIC(14,3) NOT NULL,
    preco_unitario  NUMERIC(14,4) CHECK (preco_unitario >= 0),
    valor_total     NUMERIC(16,2),
    id_carga        BIGINT        NOT NULL REFERENCES carga_execucao (id_carga),
    carregado_em    TIMESTAMPTZ   NOT NULL DEFAULT now(),
    CONSTRAINT pk_estoque_saldo PRIMARY KEY (id_material, id_almoxarifado, data_referencia),
    CONSTRAINT ck_estoque_data_primeiro_dia
        CHECK (data_referencia = date_trunc('month', data_referencia)::date)
);

-- "saldo atual de um material": última data_referencia de um id_material
CREATE INDEX ix_estoque_material_data ON estoque_saldo (id_material, data_referencia DESC);
CREATE INDEX ix_estoque_data          ON estoque_saldo (data_referencia);

-- ---------------------------------------------------------------------------
-- Execução orçamentária
-- ---------------------------------------------------------------------------

CREATE TABLE gasto (
    id_gasto        BIGSERIAL     PRIMARY KEY,
    id_unidade      INTEGER       NOT NULL REFERENCES unidade (id_unidade),
    id_natureza     INTEGER       NOT NULL REFERENCES natureza_despesa (id_natureza),
    data_referencia DATE          NOT NULL,
    valor           NUMERIC(16,2) NOT NULL,
    id_carga        BIGINT        NOT NULL REFERENCES carga_execucao (id_carga),
    carregado_em    TIMESTAMPTZ   NOT NULL DEFAULT now(),
    atualizado_em   TIMESTAMPTZ   NOT NULL DEFAULT now(),
    CONSTRAINT uq_gasto UNIQUE (id_unidade, id_natureza, data_referencia),
    CONSTRAINT ck_gasto_data_primeiro_dia
        CHECK (data_referencia = date_trunc('month', data_referencia)::date)
);

CREATE INDEX ix_gasto_data ON gasto (data_referencia);

-- O número do empenho só é único dentro da unidade gestora e do ano.
CREATE TABLE empenho (
    id_unidade_gestora         INTEGER       NOT NULL REFERENCES unidade (id_unidade),
    ano                        SMALLINT      NOT NULL CHECK (ano BETWEEN 2000 AND 2100),
    cod_empenho                INTEGER       NOT NULL CHECK (cod_empenho > 0),
    data_emissao               DATE,
    modalidade                 TEXT,
    id_natureza                INTEGER       REFERENCES natureza_despesa (id_natureza),
    id_credor                  INTEGER       REFERENCES credor (id_credor),
    valor_empenho              NUMERIC(16,2),
    valor_reforcado            NUMERIC(16,2),
    valor_anulado              NUMERIC(16,2),
    valor_cancelado            NUMERIC(16,2),
    saldo_empenho              NUMERIC(16,2),
    fonte_recurso              TEXT,
    programa_trabalho_resumido TEXT,
    plano_interno              TEXT,
    esfera                     TEXT,
    processo                   TEXT,
    documento_associado        TEXT,
    licitacao                  TEXT,
    convenio                   TEXT,
    observacoes                TEXT,
    id_carga                   BIGINT        NOT NULL REFERENCES carga_execucao (id_carga),
    carregado_em               TIMESTAMPTZ   NOT NULL DEFAULT now(),
    atualizado_em              TIMESTAMPTZ   NOT NULL DEFAULT now(),
    CONSTRAINT pk_empenho PRIMARY KEY (id_unidade_gestora, ano, cod_empenho)
);

CREATE INDEX ix_empenho_credor   ON empenho (id_credor);
CREATE INDEX ix_empenho_natureza ON empenho (id_natureza);
CREATE INDEX ix_empenho_data     ON empenho (data_emissao);

CREATE TABLE requisicao_servico (
    numero                  INTEGER     NOT NULL CHECK (numero > 0),
    ano                     SMALLINT    NOT NULL CHECK (ano BETWEEN 2000 AND 2100),
    tipo                    TEXT,
    id_unidade_requisitante INTEGER     REFERENCES unidade (id_unidade),
    id_unidade_custo        INTEGER     REFERENCES unidade (id_unidade),
    data_envio              DATE,
    data_autorizacao_chefe  DATE,
    status                  TEXT,
    observacoes             TEXT,
    id_carga                BIGINT      NOT NULL REFERENCES carga_execucao (id_carga),
    carregado_em            TIMESTAMPTZ NOT NULL DEFAULT now(),
    atualizado_em           TIMESTAMPTZ NOT NULL DEFAULT now(),
    CONSTRAINT pk_requisicao PRIMARY KEY (ano, numero),
    CONSTRAINT ck_requisicao_datas
        CHECK (data_autorizacao_chefe IS NULL OR data_envio IS NULL
               OR data_autorizacao_chefe >= data_envio)
);

CREATE INDEX ix_requisicao_unidade ON requisicao_servico (id_unidade_requisitante, ano);

-- ---------------------------------------------------------------------------
-- Cotações de mercado (geradas pelo próprio SIGMA, insert-only)
-- ---------------------------------------------------------------------------

CREATE TABLE cotacao_online (
    id_cotacao   BIGSERIAL     PRIMARY KEY,
    id_material  INTEGER       NOT NULL REFERENCES material (id_material),
    loja         TEXT          NOT NULL,
    titulo       TEXT,
    preco        NUMERIC(14,2) NOT NULL CHECK (preco > 0),
    url          TEXT,
    data_coleta  TIMESTAMPTZ   NOT NULL,
    carregado_em TIMESTAMPTZ   NOT NULL DEFAULT now()
);

CREATE INDEX ix_cotacao_material_data ON cotacao_online (id_material, data_coleta DESC);
