CREATE TABLE artigo (
	id	 INTEGER,
	nome	 VARCHAR(512) NOT NULL,
	descricao VARCHAR(512) NOT NULL,
	PRIMARY KEY(id)
);

CREATE TABLE leilao (
	id_versao	 INTEGER,
	titulo	 VARCHAR(512) NOT NULL,
	momento_fim	 TIMESTAMP NOT NULL,
	preco_minimo DOUBLE PRECISION NOT NULL,
	descricao	 VARCHAR(1024) NOT NULL,
	versao	 INTEGER NOT NULL,
	id_leilao	 INTEGER NOT NULL,
	cancelled	 BOOL NOT NULL,
	artigo_id	 INTEGER UNIQUE NOT NULL,
	PRIMARY KEY(id_versao)
);

CREATE TABLE utilizador (
	username VARCHAR(512),
	email	 VARCHAR(512) UNIQUE NOT NULL,
	password VARCHAR(512) NOT NULL,
	banned	 BOOL NOT NULL DEFAULT false,
	admin	 BOOL NOT NULL DEFAULT false,
	PRIMARY KEY(username)
);

CREATE TABLE licitacao (
	valor		 DOUBLE PRECISION NOT NULL,
	utilizador_username	 VARCHAR(512),
	leilao_id_versao INTEGER,
	PRIMARY KEY(utilizador_username,leilao_id_versao)
);

CREATE TABLE mensagem (
	id		 INTEGER,
	conteudo	 VARCHAR(512) NOT NULL,
	utilizador_username	 VARCHAR(512),
	leilao_id_versao INTEGER,
	PRIMARY KEY(id,utilizador_username,leilao_id_versao)
);

CREATE TABLE notificacao (
	id		 INTEGER,
	conteudo	 VARCHAR(512) NOT NULL,
	utilizador_username VARCHAR(512),
	PRIMARY KEY(id,utilizador_username)
);

CREATE TABLE utilizador_leilao (
	utilizador_username	 VARCHAR(512),
	leilao_id_versao INTEGER,
	PRIMARY KEY(utilizador_username,leilao_id_versao)
);

ALTER TABLE leilao ADD CONSTRAINT leilao_fk1 FOREIGN KEY (artigo_id) REFERENCES artigo(id);
ALTER TABLE licitacao ADD CONSTRAINT licitacao_fk1 FOREIGN KEY (utilizador_username) REFERENCES utilizador(username);
ALTER TABLE licitacao ADD CONSTRAINT licitacao_fk2 FOREIGN KEY (leilao_id_versao) REFERENCES leilao(id_versao);
ALTER TABLE mensagem ADD CONSTRAINT mensagem_fk1 FOREIGN KEY (utilizador_username) REFERENCES utilizador(username);
ALTER TABLE mensagem ADD CONSTRAINT mensagem_fk2 FOREIGN KEY (leilao_id_versao) REFERENCES leilao(id_versao);
ALTER TABLE notificacao ADD CONSTRAINT notificacao_fk1 FOREIGN KEY (utilizador_username) REFERENCES utilizador(username);
ALTER TABLE utilizador_leilao ADD CONSTRAINT utilizador_leilao_fk1 FOREIGN KEY (utilizador_username) REFERENCES utilizador(username);
ALTER TABLE utilizador_leilao ADD CONSTRAINT utilizador_leilao_fk2 FOREIGN KEY (leilao_id_versao) REFERENCES leilao(id_versao);

INSERT INTO utilizador VALUES('Jorge Sampaio', 'tijorgesamp@gmail.com', 'password123', false, false);
