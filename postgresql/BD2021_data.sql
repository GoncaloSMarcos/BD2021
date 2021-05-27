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
	valor		 DOUBLE PRECISION NOT NULL,
	utilizador_username VARCHAR(512),
	leilao_id_leilao	 INTEGER,
	PRIMARY KEY(utilizador_username,leilao_id_leilao)
);

CREATE TABLE mensagem (
	id			 SERIAL,
	conteudo		 VARCHAR(512) NOT NULL,
	utilizador_username VARCHAR(512),
	leilao_id_leilao	 INTEGER,
	PRIMARY KEY(id,utilizador_username,leilao_id_leilao)
);

CREATE TABLE notificacao (
	conteudo			 VARCHAR(512) NOT NULL,
	utilizador_username		 VARCHAR(512) UNIQUE NOT NULL,
	leilao_id_leilao		 INTEGER UNIQUE NOT NULL,
	licitacao_utilizador_username VARCHAR(512),
	licitacao_leilao_id_leilao	 INTEGER,
	PRIMARY KEY(licitacao_utilizador_username,licitacao_leilao_id_leilao)
);

CREATE TABLE utilizador_leilao (
	utilizador_username VARCHAR(512),
	leilao_id_leilao	 INTEGER,
	PRIMARY KEY(utilizador_username,leilao_id_leilao)
);

ALTER TABLE leilao ADD CONSTRAINT leilao_fk1 FOREIGN KEY (artigo_id) REFERENCES artigo(id);
ALTER TABLE licitacao ADD CONSTRAINT licitacao_fk1 FOREIGN KEY (utilizador_username) REFERENCES utilizador(username);
ALTER TABLE licitacao ADD CONSTRAINT licitacao_fk2 FOREIGN KEY (leilao_id_leilao) REFERENCES leilao(id_leilao);
ALTER TABLE mensagem ADD CONSTRAINT mensagem_fk1 FOREIGN KEY (utilizador_username) REFERENCES utilizador(username);
ALTER TABLE mensagem ADD CONSTRAINT mensagem_fk2 FOREIGN KEY (leilao_id_leilao) REFERENCES leilao(id_leilao);
ALTER TABLE notificacao ADD CONSTRAINT notificacao_fk1 FOREIGN KEY (utilizador_username) REFERENCES utilizador(username);
ALTER TABLE notificacao ADD CONSTRAINT notificacao_fk2 FOREIGN KEY (leilao_id_leilao) REFERENCES leilao(id_leilao);
ALTER TABLE notificacao ADD CONSTRAINT notificacao_fk3 FOREIGN KEY (licitacao_utilizador_username) REFERENCES licitacao(utilizador_username);
ALTER TABLE notificacao ADD CONSTRAINT notificacao_fk4 FOREIGN KEY (licitacao_leilao_id_leilao) REFERENCES licitacao(leilao_id_leilao);
ALTER TABLE utilizador_leilao ADD CONSTRAINT utilizador_leilao_fk1 FOREIGN KEY (utilizador_username) REFERENCES utilizador(username);
ALTER TABLE utilizador_leilao ADD CONSTRAINT utilizador_leilao_fk2 FOREIGN KEY (leilao_id_leilao) REFERENCES leilao(id_leilao);