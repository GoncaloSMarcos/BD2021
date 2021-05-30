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
	id_familia	 SERIAL NOT NULL,
	cancelled	 BOOL NOT NULL,
	terminado	 BOOL NOT NULL,
	vencedor_username	VARCHAR(512),
	artigo_id	 INTEGER NOT NULL,
	creator_username	VARCHAR(512) NOT NULL,
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
	leilao_id_familia	 INTEGER NOT NULL,
	utilizador_username VARCHAR(512) NOT NULL,
	cancelled	 BOOL NOT NULL,
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
ALTER TABLE leilao ADD CONSTRAINT leilao_fk2 FOREIGN KEY (creator_username) REFERENCES utilizador(username);
ALTER TABLE leilao ADD CONSTRAINT leilao_fk3 FOREIGN KEY (vencedor_username) REFERENCES utilizador(username);
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
	v_terminado BOOL;
	v_cancelled BOOL;
BEGIN
 	-- get username from authcode
	SELECT username
   	INTO v_username
   	FROM utilizador
   	WHERE utilizador.authcode = v_authcode;

	-- get preco minimo e id da familia do leilao
	SELECT preco_minimo, id_familia, terminado, cancelled
   	INTO v_preco_minimo, v_familia_id, v_terminado, v_cancelled
   	FROM leilao
   	WHERE leilao.id_leilao = v_leilao_id;

	IF v_terminado = true OR v_cancelled = true THEN
		RETURN false;
	END IF;

	-- get licitacao atual
	SELECT coalesce(MAX(licitacao.valor), 0)
   	INTO v_licitacao_atual
   	FROM licitacao
   	WHERE licitacao.leilao_id_familia = v_familia_id;

	-- verificar se cumpre os requesitos de ser > preço minimo e > licitacao atual
	IF v_preco >= v_preco_minimo AND v_preco > v_licitacao_atual THEN
    	INSERT INTO licitacao VALUES(DEFAULT, v_preco, v_leilao_id, v_familia_id, v_username, false);
		RETURN true;
	ELSE
   	 	RETURN false;
	END IF;
END;
$$;

CREATE OR REPLACE FUNCTION add_leilao(v_titulo VARCHAR, v_momento_fim TIMESTAMP, v_preco_minimo INTEGER, v_descricao VARCHAR, v_artigo_id INTEGER, v_authcode INTEGER)
RETURNS INTEGER
LANGUAGE plpgsql
AS
$$
DECLARE
	v_username VARCHAR;
	v_id INTEGER;
	v_inLeilao INTEGER;
BEGIN
	-- get username from authcode
	SELECT username
   	INTO v_username
   	FROM utilizador
   	WHERE utilizador.authcode = v_authcode;

	-- check if artigo is in a leilao
	SELECT count(*)
	INTO v_inLeilao
	FROM leilao 
	WHERE leilao.artigo_id = v_artigo_id;
	
	IF v_inLeilao = 0 THEN
		INSERT INTO leilao (id_leilao, titulo, momento_fim, preco_minimo, descricao, versao, id_familia, cancelled, artigo_id, creator_username, terminado)
    	VALUES (DEFAULT, v_titulo, v_momento_fim, v_preco_minimo, v_descricao, 1, DEFAULT, false, v_artigo_id, v_username, false)
		RETURNING id_leilao INTO v_id;

		RETURN v_id;
	ELSE
		RETURN 0;
	END IF;
END;
$$;

CREATE OR REPLACE FUNCTION edit_leilao(v_titulo VARCHAR, v_momento_fim TIMESTAMP, v_preco_minimo INTEGER, v_descricao VARCHAR, v_id_leilao INTEGER, v_artigo_id INTEGER, v_authcode INTEGER)
RETURNS BOOL
LANGUAGE plpgsql
AS
$$
DECLARE
	v_versao INTEGER;
	v_username VARCHAR;
	v_terminado BOOL;
	v_cancelled BOOL;
BEGIN
	-- get versao do leilao
	SELECT versao, terminado, cancelled
   	INTO v_versao, v_terminado, v_cancelled
   	FROM leilao
   	WHERE leilao.id_leilao = v_id_leilao;

	IF v_terminado = true OR v_cancelled = true THEN
		RETURN false;
	END IF;

	-- atualizar versao
	v_versao := v_versao + 1;

	-- cancelar leilao anterior
	UPDATE leilao 
	SET cancelled = true
	WHERE leilao.id_leilao = v_id_leilao;

	-- get username from authcode
	SELECT username
   	INTO v_username
   	FROM utilizador
   	WHERE utilizador.authcode = v_authcode;

	INSERT INTO leilao (id_leilao, titulo, momento_fim, preco_minimo, descricao, versao, id_familia, cancelled, artigo_id, creator_username, terminado)
	VALUES (DEFAULT, v_titulo, v_momento_fim, v_preco_minimo, v_descricao, v_versao, v_id_leilao, false, v_artigo_id, v_username, false);
	RETURN true;
END;
$$;

CREATE OR REPLACE FUNCTION add_message(v_id_leilao INTEGER, v_conteudo VARCHAR, v_authcode INTEGER)
RETURNS BOOL
LANGUAGE plpgsql
AS
$$
DECLARE
	v_username VARCHAR;
	v_terminado BOOL;
	v_cancelled BOOL;
BEGIN

	-- get versao do leilao
	SELECT terminado, cancelled
   	INTO v_terminado, v_cancelled
   	FROM leilao
   	WHERE leilao.id_leilao = v_id_leilao;

	IF v_terminado = true OR v_cancelled = true THEN
		RETURN false;
	END IF;

  	-- obter username atraves de authCode
	SELECT username
	INTO v_username
	FROM utilizador
	WHERE utilizador.authcode = v_authcode;

	-- inserir mensagem no mural do leilao
	INSERT into mensagem VALUES(DEFAULT, v_conteudo, v_username, v_id_leilao);
	RETURN true;
END;
$$;

CREATE OR REPLACE FUNCTION get_atividade(v_authcode INTEGER)
RETURNS TABLE (
		v_versao INTEGER,
		v_titulo VARCHAR,
		v_descricao VARCHAR,
		v_preco_minimo DOUBLE PRECISION,
		v_momento_fim TIMESTAMP
		) 
LANGUAGE plpgsql
AS
$$
DECLARE
	v_username VARCHAR;
BEGIN
  	-- obter username atraves de authCode
	SELECT username
	INTO v_username
	FROM utilizador
	WHERE utilizador.authcode = v_authcode;

	-- get leiloes criados ou leiloes nos quais o user participou 
	RETURN QUERY SELECT versao, titulo, descricao, preco_minimo, momento_fim 
				 FROM leilao 
				 WHERE leilao.creator_username = v_username
				 UNION
				 SELECT versao, titulo, descricao, preco_minimo, momento_fim 
				 FROM leilao, licitacao 
				 WHERE licitacao.utilizador_username = v_username AND licitacao.leilao_id_familia = leilao.id_familia AND leilao.cancelled = false;
END;
$$;

CREATE OR REPLACE FUNCTION get_top10_criadores(v_authcode INTEGER)
RETURNS TABLE (
		t_username VARCHAR,
		t_count BIGINT
		) 
LANGUAGE plpgsql
AS
$$
DECLARE
	v_username VARCHAR;
BEGIN
	-- obter username atraves de authCode
	SELECT username
	INTO v_username
	FROM utilizador
	WHERE utilizador.authcode = v_authcode;

	RETURN QUERY SELECT creator_username, count(leilao.creator_username = v_username)
				 FROM leilao
				 GROUP BY creator_username
				 HAVING cancelled = false
			 	 ORDER BY count(leilao.creator_username = v_username) DESC
			 	 LIMIT 10;
END;
$$;

CREATE OR REPLACE FUNCTION get_top10_vencedores(v_authcode INTEGER)
RETURNS TABLE (
		t_username VARCHAR,
		t_count BIGINT
		) 
LANGUAGE plpgsql
AS
$$
DECLARE
	v_username VARCHAR;
BEGIN
	-- obter username atraves de authCode
	SELECT username
	INTO v_username
	FROM utilizador
	WHERE utilizador.authcode = v_authcode;

	RETURN QUERY SELECT creator_username, count(leilao.vencedor_username = v_username)
				 FROM leilao
				 GROUP BY creator_username
				 HAVING cancelled = false
			 	 ORDER BY count(leilao.vencedor_username = v_username) DESC
			 	 LIMIT 10;
END;
$$;

CREATE OR REPLACE FUNCTION get_leiloes_10dias()
RETURNS BIGINT 
LANGUAGE plpgsql
AS
$$
DECLARE
	total BIGINT;
BEGIN
	SELECT count(*) 
	INTO total
	FROM leilao
	WHERE leilao.momento_fim >= current_date - INTEGER '10' AND leilao.momento_fim <= current_date AND leilao.cancelled = false;

	RETURN total;
END;
$$;
