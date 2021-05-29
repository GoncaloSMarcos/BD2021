CREATE TABLE artigo (
	id	 SERIAL,
	nome	 VARCHAR(512) NOT NULL,
	descricao VARCHAR(512) NOT NULL,
	PRIMARY KEY(id)
);

CREATE TABLE leilao (
	id_leilao	 SERIAL,
	titulo	 VARCHAR(512) NOT NULL,
	momento_fim	 TIMESTAMP NOT NULL,
	preco_minimo DOUBLE PRECISION NOT NULL,
	descricao	 VARCHAR(1024) NOT NULL,
	versao	 INTEGER NOT NULL,
	id_familia	 INTEGER NOT NULL,
	cancelled	 BOOL NOT NULL,
	artigo_id	 INTEGER UNIQUE NOT NULL,
	PRIMARY KEY(id_leilao)
);

CREATE TABLE utilizador (
	username VARCHAR(512),
	email	 VARCHAR(512) UNIQUE NOT NULL,
	password VARCHAR(512) NOT NULL,
	banned	 BOOL NOT NULL DEFAULT false,
	admin	 BOOL NOT NULL DEFAULT false,
	authcode SERIAL UNIQUE NOT NULL,
	PRIMARY KEY(username)
);

CREATE TABLE licitacao (
	id			 SERIAL,
	valor		 DOUBLE PRECISION NOT NULL,
	leilao_id_leilao	 INTEGER NOT NULL,
	utilizador_username VARCHAR(512) NOT NULL,
	PRIMARY KEY(id)
);

CREATE TABLE mensagem (
	id			 SERIAL,
	conteudo		 VARCHAR(512) NOT NULL,
	utilizador_username VARCHAR(512),
	leilao_id_leilao	 INTEGER,
	PRIMARY KEY(id,utilizador_username,leilao_id_leilao)
);

CREATE TABLE notificacao (
	conteudo		 VARCHAR(512) NOT NULL,
	licitacao_id	 INTEGER UNIQUE NOT NULL,
	utilizador_username VARCHAR(512) UNIQUE NOT NULL,
	leilao_id_leilao	 INTEGER,
	PRIMARY KEY(leilao_id_leilao)
);

CREATE TABLE utilizador_leilao (
	utilizador_username VARCHAR(512),
	leilao_id_leilao	 INTEGER,
	PRIMARY KEY(utilizador_username,leilao_id_leilao)
);

ALTER TABLE leilao ADD CONSTRAINT leilao_fk1 FOREIGN KEY (artigo_id) REFERENCES artigo(id);
ALTER TABLE licitacao ADD CONSTRAINT licitacao_fk1 FOREIGN KEY (leilao_id_leilao) REFERENCES leilao(id_leilao);
ALTER TABLE licitacao ADD CONSTRAINT licitacao_fk2 FOREIGN KEY (utilizador_username) REFERENCES utilizador(username);
ALTER TABLE mensagem ADD CONSTRAINT mensagem_fk1 FOREIGN KEY (utilizador_username) REFERENCES utilizador(username);
ALTER TABLE mensagem ADD CONSTRAINT mensagem_fk2 FOREIGN KEY (leilao_id_leilao) REFERENCES leilao(id_leilao);
ALTER TABLE notificacao ADD CONSTRAINT notificacao_fk1 FOREIGN KEY (licitacao_id) REFERENCES licitacao(id);
ALTER TABLE notificacao ADD CONSTRAINT notificacao_fk2 FOREIGN KEY (utilizador_username) REFERENCES utilizador(username);
ALTER TABLE notificacao ADD CONSTRAINT notificacao_fk3 FOREIGN KEY (leilao_id_leilao) REFERENCES leilao(id_leilao);
ALTER TABLE utilizador_leilao ADD CONSTRAINT utilizador_leilao_fk1 FOREIGN KEY (utilizador_username) REFERENCES utilizador(username);
ALTER TABLE utilizador_leilao ADD CONSTRAINT utilizador_leilao_fk2 FOREIGN KEY (leilao_id_leilao) REFERENCES leilao(id_leilao);

CREATE OR REPLACE FUNCTION licitar(v_preco INTEGER, v_authcode INTEGER, v_leilao_id INTEGER)
RETURNS BOOL
LANGUAGE plpgsql
AS
$$
DECLARE
	v_username VARCHAR(512);
	v_preco_minimo INTEGER;
	v_licitacao_atual INTEGER;
	v_familia_id INTEGER;

BEGIN
 	-- get username from authcode
	SELECT username
   	INTO v_username
   	FROM utilizador
   	WHERE utilizador.authcode = v_authcode;

	-- get preco minimo e id da familia do leilao
	SELECT preco_minimo, id_familia
   	INTO v_preco_minimo, v_familia_id
   	FROM leilao
   	WHERE leilao.id_leilao = v_leilao_id;

	-- get licitacao atual
	SELECT coalesce(MAX(licitacao.valor), 0)
   	INTO v_licitacao_atual
   	FROM licitacao, leilao
   	WHERE licitacao.leilao_id_leilao = leilao.id_leilao AND leilao.id_familia = v_familia_id;

	-- verificar se cumpre os requesitos de ser > preço minimo e > licitacao atual
	IF v_preco >= v_preco_minimo AND v_preco > v_licitacao_atual THEN
    	INSERT INTO licitacao VALUES(DEFAULT, v_preco, v_leilao_id,v_username);
		RETURN true;
	ELSE
   	 	RETURN false;
	END IF;
END;
$$;

CREATE OR REPLACE FUNCTION edit_leilao(v_titulo VARCHAR, v_momento_fim TIMESTAMP, v_preco_minimo INTEGER, v_descricao VARCHAR, v_id_leilao INTEGER, v_artigo_id INTEGER)
RETURNS BOOL
LANGUAGE plpgsql
AS
$$
DECLARE
	v_versao INTEGER;
BEGIN
	-- get versao do leilao
	SELECT versao
   	INTO v_versao
   	FROM leilao
   	WHERE leilao.id_leilao = v_id_leilao;

	-- atualizar versao
	v_versao := v_versao + 1;

	INSERT INTO leilao (id_leilao, titulo, momento_fim, preco_minimo, descricao, versao, id_familia, cancelled, artigo_id)
	VALUES (DEFAULT, v_titulo, v_momento_fim, v_preco_minimo, v_descricao, v_versao, v_id_leilao, false, v_artigo_id);
	RETURN true;
END;
$$;