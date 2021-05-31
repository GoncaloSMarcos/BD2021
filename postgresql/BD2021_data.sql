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
	id					SERIAL UNIQUE NOT NULL,
	conteudo		 VARCHAR(512) NOT NULL,
	utilizador_username VARCHAR(512) NOT NULL,
	leilao_id_leilao	 INTEGER,
	PRIMARY KEY(id, leilao_id_leilao, utilizador_username)
);

CREATE TABLE utilizador_leilao (
	utilizador_username VARCHAR(512),
	leilao_id_leilao	 INTEGER,
	PRIMARY KEY(utilizador_username,leilao_id_leilao)
);

ALTER TABLE leilao ADD CONSTRAINT leilao_fk1 FOREIGN KEY (artigo_id) REFERENCES artigo(id);
ALTER TABLE leilao ADD CONSTRAINT leilao_fk2 FOREIGN KEY (creator_username) REFERENCES utilizador(username);
ALTER TABLE licitacao ADD CONSTRAINT licitacao_fk1 FOREIGN KEY (leilao_id_leilao) REFERENCES leilao(id_leilao);
ALTER TABLE licitacao ADD CONSTRAINT licitacao_fk2 FOREIGN KEY (utilizador_username) REFERENCES utilizador(username);
ALTER TABLE mensagem ADD CONSTRAINT mensagem_fk1 FOREIGN KEY (utilizador_username) REFERENCES utilizador(username);
ALTER TABLE mensagem ADD CONSTRAINT mensagem_fk2 FOREIGN KEY (leilao_id_leilao) REFERENCES leilao(id_leilao);
ALTER TABLE notificacao ADD CONSTRAINT notificacao_fk1 FOREIGN KEY (utilizador_username) REFERENCES utilizador(username);
ALTER TABLE notificacao ADD CONSTRAINT notificacao_fk2 FOREIGN KEY (leilao_id_leilao) REFERENCES leilao(id_leilao);
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
   	FROM licitacao
   	WHERE licitacao.leilao_id_familia = v_familia_id;

	-- verificar se cumpre os requesitos de ser > preço minimo e > licitacao atual
	IF v_preco >= v_preco_minimo AND v_preco > v_licitacao_atual THEN
    	INSERT INTO licitacao VALUES(DEFAULT, v_preco, v_leilao_id, v_familia_id, v_username);
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
		INSERT INTO leilao (id_leilao, titulo, momento_fim, preco_minimo, descricao, versao, id_familia, cancelled, artigo_id, creator_username)
    	VALUES (DEFAULT, v_titulo, v_momento_fim, v_preco_minimo, v_descricao, 1, DEFAULT, false, v_artigo_id, v_username)
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
BEGIN
	-- get versao do leilao
	SELECT versao
   	INTO v_versao
   	FROM leilao
   	WHERE leilao.id_leilao = v_id_leilao;

	-- atualizar versao
	v_versao := v_versao + 1;

	-- get username from authcode
	SELECT username
   	INTO v_username
   	FROM utilizador
   	WHERE utilizador.authcode = v_authcode;

	INSERT INTO leilao (id_leilao, titulo, momento_fim, preco_minimo, descricao, versao, id_familia, cancelled, artigo_id, creator_username)
	VALUES (DEFAULT, v_titulo, v_momento_fim, v_preco_minimo, v_descricao, v_versao, v_id_leilao, false, v_artigo_id, v_username);
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
BEGIN
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

	-- get leiloes criados ou leiloes nos quais o user participou DOES NOT WORK
	RETURN QUERY SELECT versao, titulo, descricao, preco_minimo, momento_fim
				 FROM leilao, licitacao
				 WHERE (leilao.creator_username = v_username OR licitacao.utilizador_username = v_username) AND licitacao.leilao_id_leilao = leilao.id_leilao;
END;
$$;



CREATE OR REPLACE FUNCTION mural(v_id_leilao INTEGER, v_authcode INTEGER)
RETURNS TABLE (
		v_username VARCHAR,
		v_conteudo VARCHAR
		)
LANGUAGE plpgsql
AS
$$
DECLARE
	v_aux_username VARCHAR;
BEGIN
  -- obter username atraves de authCode
	SELECT username
	INTO v_aux_username
	FROM utilizador
	WHERE utilizador.authcode = v_authcode;

	-- get leiloes criados ou leiloes nos quais o user participou DOES NOT WORK
	RETURN QUERY SELECT utilizador_username, conteudo
				 FROM mensagem
				 WHERE mensagem.leilao_id_leilao = v_id_leilao;
END;
$$;



CREATE OR REPLACE FUNCTION notify_users_of_messages()
	RETURNS TRIGGER
	LANGUAGE plpgsql
	AS
$$
	DECLARE
		--c1 cursor for SELECT * from mensagem where leilao_id_leilao = (SELECT mensagem.leilao_id_leilao from mensagem GROUP BY mensagem.id, mensagem.leilao_id_leilao HAVING mensagem.id = MAX(mensagem.id));
		c1 cursor for SELECT DISTINCT utilizador_username from mensagem where leilao_id_leilao = (SELECT mensagem.leilao_id_leilao from mensagem where mensagem.id = (SELECT MAX(id) FROM mensagem));
		v_id_leilao INTEGER;
		v_creator_username VARCHAR;
	BEGIN
	SELECT mensagem.leilao_id_leilao INTO v_id_leilao FROM mensagem where mensagem.id = (SELECT MAX(id) FROM mensagem);
		for r in c1
		loop
			INSERT INTO notificacao VALUES(DEFAULT, CONCAT('Mensagem recebida no leilao ', CAST(v_id_leilao as VARCHAR(10))), r.utilizador_username, v_id_leilao);
		end loop;
		--SELECT creator_username INTO v_creator_username FROM leilao, mensagem where leilao.id_leilao = mensagem.leilao_id_leilao;
		--INSERT INTO notificacao VALUES(CONCAT('Mensagem recebida no leilao ', CAST(v_id_leilao as VARCHAR(10))), v_creator_username, v_id_leilao);
		RETURN NEW;
	END;
$$;






	CREATE TRIGGER notify_users_of_messages_trigger
	  AFTER INSERT
	  ON mensagem
	  FOR EACH STATEMENT
		EXECUTE PROCEDURE notify_users_of_messages();
