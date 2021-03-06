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
ALTER TABLE leilao ADD CONSTRAINT leilao_fk3 FOREIGN KEY (vencedor_username) REFERENCES utilizador(username);
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

	-- verificar se cumpre os requesitos de ser > pre??o minimo e > licitacao atual
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

	IF v_inLeilao = 0 AND v_momento_fim > CURRENT_TIMESTAMP THEN
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
	v_id_leilao_geral INTEGER;
	v_username VARCHAR;
	v_creator_username VARCHAR;
	v_terminado BOOL;
	v_cancelled BOOL;
	v_admin BOOL;
BEGIN
	-- get versao do leilao
	SELECT id_leilao, versao, terminado, cancelled, creator_username
   	INTO v_id_leilao_geral, v_versao, v_terminado, v_cancelled, v_creator_username
   	FROM leilao
   	WHERE leilao.id_familia = v_id_leilao AND leilao.cancelled = false;

	IF v_terminado = true OR v_cancelled = true THEN
		RETURN false;
	END IF;

	-- get username from authcode
	SELECT username, admin
   	INTO v_username, v_admin
   	FROM utilizador
   	WHERE utilizador.authcode = v_authcode;

	IF v_username != v_creator_username AND v_admin != true THEN
		return false;
	END IF;

	-- atualizar versao
	v_versao := v_versao + 1;

	-- cancelar leilao anterior
	UPDATE leilao
	SET cancelled = true
	WHERE leilao.id_leilao = v_id_leilao_geral;


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

CREATE OR REPLACE FUNCTION notify_users_of_bid()
	RETURNS TRIGGER
	LANGUAGE plpgsql
	AS
$$
	DECLARE
		c1 cursor for SELECT DISTINCT utilizador_username from licitacao where leilao_id_leilao = (SELECT licitacao.leilao_id_leilao from licitacao where licitacao.id = (SELECT MAX(id) FROM licitacao));
		v_id_leilao INTEGER;
		v_last_bidder VARCHAR;
	BEGIN
	SELECT licitacao.leilao_id_leilao INTO v_id_leilao FROM licitacao where licitacao.id = (SELECT MAX(id) FROM licitacao);
	SELECT licitacao.utilizador_username INTO v_last_bidder  FROM licitacao WHERE licitacao.id = (SELECT MAX(id) FROM licitacao);
		for r in c1
		loop
			if (r.utilizador_username is distinct from v_last_bidder) then
				INSERT INTO notificacao VALUES(DEFAULT, CONCAT('Licitacao ultrapassada no leilao de id: ', CAST(v_id_leilao as VARCHAR(10))), r.utilizador_username, v_id_leilao);
			end if;
		end loop;
		RETURN NEW;
	END;
$$;

CREATE TRIGGER notify_users_of_bid_trigger
	AFTER INSERT
	ON licitacao
	FOR EACH STATEMENT
	EXECUTE PROCEDURE notify_users_of_bid();

	CREATE OR REPLACE FUNCTION random_portal_name()
	RETURNS varchar as $$
		begin
		    create temp sequence if not exists portal_names;
		    return 'portal$' || nextval('portal_names');
		end;
		$$ language plpgsql;




CREATE OR REPLACE FUNCTION invalidate_bids()
	RETURNS TRIGGER
	LANGUAGE plpgsql
	AS
	$$
		DECLARE
			c1 cursor for SELECT DISTINCT leilao_id_leilao from licitacao where licitacao.utilizador_username = NEW.utilizador_username;

			--c2 cursor(leilao_id integer, v_max_bid_c INTEGER) for SELECT DISTINCT utilizador_username from licitacao where (licitacao.valor > OLD.valor AND licitacao.valor < v_max_bid_c AND licitacao.leilao_id_leilao = leilao_id);

			v_max_bid licitacao.valor%type;
			v_cancelled_bid_value licitacao.valor%type;
			v_creator VARCHAR;
		BEGIN
			--SELECT valor INTO v_cancelled_bid_value FROM old.valor;
			--INSERT INTO v_cancelled_bid_value VALUES(OLD.valor);

			c1 := random_portal_name();
			for r in c1
			loop
				SELECT valor INTO v_max_bid FROM licitacao WHERE licitacao.valor = (SELECT MAX(valor) FROM licitacao WHERE licitacao.leilao_id_leilao = r.leilao_id_leilao);
				UPDATE licitacao SET cancelled = true WHERE (licitacao.valor > OLD.valor AND licitacao.valor < v_max_bid AND licitacao.leilao_id_leilao = r.leilao_id_leilao);
				
				--c2 := random_portal_name();
				--for r2 in c2(r.leilao_id_leilao, v_max_bid)
				--loop
				--	INSERT INTO notificacao VALUES(DEFAULT, 'A sua licita????o foi invalidada porque um utilizador foi banido.', r2.utilizador_username, r.leilao_id_leilao);
				--end loop;

				--UPDATE licitacao SET valor = OLD.valor WHERE licitacao.id = (SELECT id FROM licitacao WHERE licitacao.leilao_id_leilao = r.leilao_id_leilao AND licitacao.valor = v_max_bid);
				SELECT creator_username
				INTO v_creator
				FROM leilao
				WHERE id_leilao = r.leilao_id_leilao;

				INSERT INTO mensagem VALUES(DEFAULT, 'Foram invalidadas licita????es porque um utilizador foi banido da nossa plataforma. Pedimos desculpa pelo inc??modo.', v_creator, r.leilao_id_leilao);
			end loop;
			RETURN NEW;
		END;
	$$;




CREATE TRIGGER invalidate_bids_trigger
	AFTER UPDATE
	ON licitacao
	FOR EACH ROW
	EXECUTE PROCEDURE invalidate_bids();




CREATE OR REPLACE FUNCTION get_top10_criadores()
	RETURNS TABLE (
				t_username VARCHAR,
				t_count BIGINT
			)
	LANGUAGE plpgsql
	AS
	$$
	DECLARE
		c1 CURSOR for SELECT DISTINCT creator_username FROM leilao WHERE cancelled = false;
		v_username VARCHAR;
		v_count BIGINT;
	BEGIN

		CREATE TEMPORARY TABLE temp(
									temp_user VARCHAR,
									temp_count BIGINT
									);
		
		for r in c1
		loop
			SELECT creator_username, count(*)
			INTO v_username, v_count
			FROM leilao
			GROUP BY creator_username, cancelled
			HAVING creator_username = r.creator_username AND cancelled = false;
			INSERT INTO temp VALUES(v_username, v_count);
		end loop;

		RETURN QUERY SELECT * 
					 FROM temp
					 ORDER BY temp_count DESC
					 LIMIT 10;
	END;
$$;

CREATE OR REPLACE FUNCTION get_top10_vencedores()
	RETURNS TABLE (
			t_username VARCHAR,
			t_count BIGINT
	)
	LANGUAGE plpgsql
	AS
	$$
	DECLARE
		c1 CURSOR for SELECT DISTINCT vencedor_username FROM leilao WHERE vencedor_username IS NOT NULL AND cancelled = false;
		v_username VARCHAR;
		v_count BIGINT;
	BEGIN

		CREATE TEMPORARY TABLE temp(
									temp_user VARCHAR,
									temp_count BIGINT
									);
		
		for r in c1
		loop
			SELECT vencedor_username, count(*)
			INTO v_username, v_count
			FROM leilao
			GROUP BY vencedor_username, cancelled
			HAVING vencedor_username = r.vencedor_username AND cancelled = false;
			INSERT INTO temp VALUES(v_username, v_count);
		end loop;

		RETURN QUERY SELECT * 
					 FROM temp
					 ORDER BY temp_count DESC
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

CREATE OR REPLACE FUNCTION get_notificacoes(v_authcode INTEGER)
RETURNS TABLE (
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
	RETURN QUERY SELECT conteudo
				 FROM notificacao
				 WHERE notificacao.utilizador_username = v_aux_username;
END;
$$;





CREATE OR REPLACE FUNCTION notify_cancelled(v_id_leilao INTEGER)
RETURNS BOOL
LANGUAGE plpgsql
AS
$$
DECLARE
		--Devolve todos os users associados ao leilao (mandaram mensagem, licitaram ou criaram o leilao)
		c1 cursor for (SELECT DISTINCT utilizador_username from licitacao where (licitacao.leilao_id_leilao = v_id_leilao) UNION SELECT DISTINCT utilizador_username from mensagem where (mensagem.leilao_id_leilao = v_id_leilao) UNION SELECT creator_username FROM leilao where id_leilao = v_id_leilao);
	BEGIN
		--SELECT licitacao.leilao_id_leilao INTO v_id_leilao FROM licitacao where licitacao.id = (SELECT MAX(id) FROM licitacao);
		--SELECT licitacao.utilizador_username INTO v_last_bidder  FROM licitacao WHERE licitacao.id = (SELECT MAX(id) FROM licitacao);
		for r in c1
		loop
			INSERT INTO notificacao VALUES(DEFAULT, CONCAT('Leilao cancelado! id: ', CAST(v_id_leilao as VARCHAR(10))), r.utilizador_username, v_id_leilao);
		end loop;
		RETURN true;
	END;
$$;
