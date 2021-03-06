from os import replace
from flask import Flask, jsonify, request
import logging, psycopg2, time

app = Flask(__name__)

@app.route('/')
def hello():

    return """

    Hello World!  <br/>
    <br/>
    Check the sources for instructions on how to use the endpoints!<br/>
    <br/>
    BD 2021 Team<br/>
    <br/>
    """

##########################################################
## GETS
##########################################################

#GET ALL USERS
@app.route("/dbproj/user/", methods=['GET'])
def get_all_users():

    logger.info("###              GET /dbproj/user/              ###")
    payload = request.get_json()

    if not isAdmin(payload):
        return jsonify({"authError": "Please log in with an admin user before executing this"})

    conn = db_connection()
    cur = conn.cursor()

    cur.execute("SELECT * FROM utilizador")
    rows = cur.fetchall()

    payload = []

    for row in rows:
        content = {'username': row[0], 'email': row[1], 'banned': row[3], 'admin': row[4], 'authcode': row[5]}
        payload.append(content) # appending to the payload to be returned

    conn.close()
    return jsonify(payload)

#GET USER BY USERNAME
@app.route("/dbproj/user/<username>", methods=['GET'])
def get_user(username):

    logger.info("###              GET /user/<username>              ###");
    payload = request.get_json()

    if not isLoggedIn(payload):
        return jsonify({"authError": "Please log in before executing this"})

    conn = db_connection()
    cur = conn.cursor()

    try:
        statement = "SELECT username, email FROM utilizador WHERE utilizador.username = %s"
        values = [username]
        cur.execute(statement, values)
        rows = cur.fetchall()
        logger.info(rows);

        output = []
        for row in rows:
            content = {'username': row[0], 'email': row[1]}
            output.append(content)

        conn.close ()
        if output == []:
            return jsonify('ERROR: User missing from database!')
        else:
            return jsonify(output)

    except (Exception) as error:
        logger.error(error)
        logger.error(type(error))

        return jsonify('ERROR: User missing from database!')

#GET ALL LEILOES
@app.route("/dbproj/leiloes/", methods=['GET'])
def get_all_leiloes():

    logger.info("###              GET /dbproj/leiloes/              ###")
    payload = request.get_json()

    if not isLoggedIn(payload):
        return jsonify({"authError": "Please log in before executing this"})

    conn = db_connection()
    cur = conn.cursor()

    cur.execute("SELECT id_leilao, titulo, descricao, preco_minimo, momento_fim, id_familia, versao, creator_username, artigo_id, cancelled FROM leilao")
    rows = cur.fetchall()

    payload = []

    for row in rows:
        aux = getHighestBidder(row[0])
        if aux[0] != None:
            content = {'id_leilao': row[0], 'titulo': row[1], 'descricao': row[2], 'preco_minimo': row[3], 'momento_fim': row[4], 'id_familia': row[5], 'versao': row[6], 'creator_username': row[7], 'artigo_id': int(row[8]), 'cancelled': row[9], 'highestBid': aux[0][0][1], 'highestBidder': aux[1][0][0]}
        else:
            content = {'id_leilao': row[0], 'titulo': row[1], 'descricao': row[2], 'preco_minimo': row[3], 'momento_fim': row[4], 'id_familia': row[5], 'versao': row[6], 'creator_username': row[7], 'artigo_id': int(row[8]), 'cancelled': row[9], 'highestBid': aux[0], 'highestBidder': aux[1]}
        payload.append(content) # appending to the payload to be returned

    conn.close()
    return jsonify(payload)

#GET LEILAO BY ID
@app.route("/dbproj/leilao/<id_leilao>", methods=['GET'])
def get_leilao(id_leilao):

    logger.info("###              GET /leilao/<id_leilao>              ###");
    payload = request.get_json()

    if not isLoggedIn(payload):
        return jsonify({"authError": "Please log in before executing this"})

    conn = db_connection()
    cur = conn.cursor()

    try:
        cur.execute("""SELECT id_leilao, titulo, descricao, preco_minimo, momento_fim, id_familia, versao, creator_username, artigo_id, cancelled, vencedor_username
                    FROM leilao
                    WHERE leilao.id_leilao = %s""", (id_leilao,) )
        rows = cur.fetchall()
        row = rows[0]

        aux = getHighestBidder(row[0])
        if aux[0] != None:
            content = {'id_leilao': row[0], 'titulo': row[1], 'descricao': row[2], 'preco_minimo': row[3], 'momento_fim': row[4], 'id_familia': row[5], 'versao': row[6], 'creator_username': row[7], 'artigo_id': int(row[8]), 'cancelled': row[9], 'highestBid': aux[0][0][1], 'highestBidder': aux[1][0][0], 'vencedorUsername': row[10]}
        else:
            content = {'id_leilao': row[0], 'titulo': row[1], 'descricao': row[2], 'preco_minimo': row[3], 'momento_fim': row[4], 'id_familia': row[5], 'versao': row[6], 'creator_username': row[7], 'artigo_id': int(row[8]), 'cancelled': row[9], 'highestBid': None, 'highestBidder': None}

        cur.execute("""SELECT utilizador_username, valor
                    FROM licitacao
                    WHERE licitacao.leilao_id_leilao = %s""", (id_leilao,) )
        rows = cur.fetchall()
        logger.info(rows)
        content['licitacoes'] = rows

        cur.execute("""SELECT utilizador_username, conteudo
                    FROM mensagem
                    WHERE mensagem.leilao_id_leilao = %s""", (id_leilao,) )
        rows = cur.fetchall()
        logger.info(rows)
        content['mensagens'] = rows


        conn.close ()
        return jsonify(content)

    except (Exception) as error:
        logger.error(error)
        logger.error(type(error))

        return jsonify('ERROR: Leilao missing from database!')

#GET ALL ARTIGOS
@app.route("/dbproj/artigo/", methods=['GET'])
def get_all_artigos():

    logger.info("###              GET /dbproj/artigo/              ###")
    payload = request.get_json()

    if not isLoggedIn(payload):
        return jsonify({"authError": "Please log in before executing this"})

    conn = db_connection()
    cur = conn.cursor()

    cur.execute("SELECT * FROM artigo")
    rows = cur.fetchall()

    payload = []

    for row in rows:
        content = {'id': row[0], 'nome': row[1], 'descricao': row[2]}
        payload.append(content) # appending to the payload to be returned

    conn.close()
    return jsonify(payload)

#GET LEILAO BY KEYWORD
@app.route("/dbproj/leiloes/<keyword>", methods=['GET'])
def get_leilao_keyword(keyword):

    logger.info("###              GET /leiloes/<keyword>              ###");
    payload = request.get_json()

    if not isLoggedIn(payload):
        return jsonify({"authError": "Please log in before executing this"})

    conn = db_connection()
    cur = conn.cursor()

    try:
        cur.execute(f"SELECT id_leilao, titulo, descricao, preco_minimo, momento_fim, id_familia, versao, creator_username, artigo_id, cancelled FROM leilao WHERE (CAST(id_leilao as VARCHAR(10)) = '{keyword}' OR descricao LIKE '%{keyword}%') AND leilao.cancelled = false")      #id_leilao*1 = id_leilao significa se e numerico
        rows = cur.fetchall()

        output = []

        for row in rows:
            aux = getHighestBidder(row[0])
            if aux[0] != None:
                content = {'id_leilao': row[0], 'titulo': row[1], 'descricao': row[2], 'preco_minimo': row[3], 'momento_fim': row[4], 'id_familia': row[5], 'versao': row[6], 'creator_username': row[7], 'artigo_id': int(row[8]), 'cancelled': row[9], 'highestBid': aux[0][0][1], 'highestBidder': aux[1][0][0]}
            else:
                content = {'id_leilao': row[0], 'titulo': row[1], 'descricao': row[2], 'preco_minimo': row[3], 'momento_fim': row[4], 'id_familia': row[5], 'versao': row[6], 'creator_username': row[7], 'artigo_id': int(row[8]), 'cancelled': row[9], 'highestBid': aux[0], 'highestBidder': aux[1]}
            output.append(content)

        conn.close ()
        return jsonify(output)

    except (Exception) as error:
        logger.error(error)
        logger.error(type(error))

        return jsonify('ERROR: Leilao missing from database!')

#GET HISTORICO
@app.route("/dbproj/historico/<id_leilao>", methods=['GET'])
def get_historico(id_leilao):

    logger.info("###              GET /historico/<id_leilao>             ###");
    payload = request.get_json()

    if not isLoggedIn(payload):
        return jsonify({"authError": "Please log in before executing this"})

    conn = db_connection()
    cur = conn.cursor()

    try:
        cur.execute(f"""SELECT id_leilao, titulo, descricao, preco_minimo, momento_fim, id_familia, versao, artigo_id
                        FROM leilao
                        WHERE leilao.id_familia = (SELECT id_familia
                                                   FROM leilao
                                                   WHERE leilao.id_leilao = {id_leilao})
                        ORDER BY versao DESC""")
        rows = cur.fetchall()

        output = []

        for row in rows:
            content = {'id_leilao': int(row[0]), 'titulo': row[1], 'descricao': row[2], 'preco_minimo': row[3], 'momento_fim': row[4], 'id_familia': row[5], 'versao': row[6], 'artigo_id': row[7]}
            output.append(content)

        conn.close ()
        return jsonify(output)

    except (Exception) as error:
        logger.error(error)
        logger.error(type(error))

        return jsonify('ERROR: Leilao missing from database!')

#GET ATIVIDADE
@app.route("/dbproj/atividade", methods=['GET'])
def get_atividade():

    logger.info("###              GET /atividade             ###");
    payload = request.get_json()

    if not isLoggedIn(payload):
        return jsonify({"authError": "Please log in before executing this"})

    conn = db_connection()
    cur = conn.cursor()

    try:
        cur.execute("SELECT * FROM get_atividade(%s);", (payload["authcode"],))
        rows = cur.fetchall()

        output = []

        for row in rows:
            content = {'versao': int(row[0]), 'titulo': row[1], 'descricao': row[2], 'preco_minimo': row[3], 'momento_fim': row[4]}
            output.append(content)

        conn.close()
        return jsonify(output)

    except (Exception) as error:
        logger.error(error)
        logger.error(type(error))

        return jsonify('Erro: Por favor tente outra vez.')

#EFETUAR LICITACAO
@app.route("/dbproj/licitar/<leilaoId>/<licitacao>", methods=['GET'])
def licitar(leilaoId, licitacao):

    logger.info("###              GET /dbproj/licitar/<leilaoId>/<licitacao>              ###");

    payload = request.get_json()

    if not isLoggedIn(payload):
        return jsonify({"authError": "Please log in before executing this"})

    conn = db_connection()
    cur = conn.cursor()

    cur.execute("BEGIN TRANSACTION")
    cur.execute("LOCK TABLE licitacao")

    cur.execute("SELECT licitar(%s, %s, %s);", (licitacao, payload["authcode"], leilaoId))
    sucessful = cur.fetchall()

    if sucessful[0][0]:
        cur.execute("commit")
        result = 'Licita????o realizada com sucesso!'
    else:
        cur.execute("rollback")
        result = 'Erro! Verifique se est?? a licitar um valor superior ao atual e ao pre??o m??nimo.'

    conn.close()
    return jsonify(result)

#LISTAR CRIADORES
@app.route("/dbproj/estatisticas/criadores", methods=['GET'])
def get_criadores():

    logger.info("###              GET /dbproj/estatisticas/criadores             ###");

    payload = request.get_json()

    if not isAdmin(payload):
        return jsonify({"authError": "Please log in with an admin user before executing this"})

    conn = db_connection()
    cur = conn.cursor()

    cur.execute("SELECT * FROM get_top10_criadores();")
    rows = cur.fetchall()

    output = []

    for row in rows:
        content = {'username': row[0], 'n leiloes criados': row[1]}
        output.append(content)

    conn.close()
    return jsonify(output)

#LISTAR VENCEDORES
@app.route("/dbproj/estatisticas/vencedores", methods=['GET'])
def get_vencedores():

    logger.info("###              GET /dbproj/estatisticas/vencedores              ###");

    payload = request.get_json()

    if not isAdmin(payload):
        return jsonify({"authError": "Please log in with an admin user before executing this"})

    conn = db_connection()
    cur = conn.cursor()

    cur.execute("SELECT * FROM get_top10_vencedores();")
    rows = cur.fetchall()
    
    output = []

    for row in rows:
        content = {'username': row[0], 'n leiloes ganhos': row[1]}
        output.append(content)

    conn.close()
    return jsonify(output)

#LISTAR LEILOES 10 DIAS
@app.route("/dbproj/estatisticas/total", methods=['GET'])
def get_leiloes_10dias():

    logger.info("###              GET /dbproj/estatisticas/total              ###");

    payload = request.get_json()

    if not isAdmin(payload):
        return jsonify({"authError": "Please log in with an admin user before executing this"})

    conn = db_connection()
    cur = conn.cursor()

    cur.execute("SELECT get_leiloes_10dias();")
    total = cur.fetchall()

    content = {'Total de leil??es nos ??ltimos 10 dias': total[0][0]}

    conn.close()
    return jsonify(content)


#ENDPOINT PARA MENSAGENS (RECEBE ID DO LEILAO)
@app.route("/dbproj/leilao/mural/<leilaoId>", methods=['GET'])
def get_mural_leilao(leilaoId):

    logger.info("###              GET /dbproj/leilao/mural/<leilaoId>              ###");

    payload = request.get_json()

    if not isLoggedIn(payload):
        return jsonify({"authError": "Please log in before executing this"})

    conn = db_connection()
    cur = conn.cursor()

    try:
        cur.execute("SELECT * from mural(%s, %s);", (leilaoId, payload["authcode"]))
        logger.info("###        Executed Mural         ###");
        rows = cur.fetchall()
        logger.debug(rows)

        output = []

        for row in rows:
            content = {'conteudo':row[1],'utilizador':row[0]}
            #content = {'utilizador':row["v_username"]}

            output.append(content)

        conn.close ()
        return jsonify(output)


    except (Exception) as error:
        logger.error(error)
        logger.error(type(error))

        return jsonify('ERROR: Erro a obter mural do leilao!')




@app.route("/dbproj/user/notificacoes", methods=['GET'])
def get_notificacoes_user():

    logger.info("###              GET /dbproj/leilao/mural/<leilaoId>              ###");

    payload = request.get_json()

    if not isLoggedIn(payload):
        return jsonify({"authError": "Please log in before executing this"})

    conn = db_connection()
    cur = conn.cursor()

    try:
        cur.execute("SELECT * from get_notificacoes(%s);", (payload["authcode"]))
        logger.info("###        Retrieving Notifications         ###");
        rows = cur.fetchall()
        logger.debug(rows)

        output = []

        for row in rows:
            content = {'Conteudo':row[0]}
            #content = {'utilizador':row["v_username"]}

            output.append(content)

        conn.close ()
        return jsonify(output)


    except (Exception) as error:
        logger.error(error)
        logger.error(type(error))

        return jsonify('ERROR: Erro a obter mural do leilao!')


##########################################################
## POSTS
##########################################################

#ADD USER
@app.route("/dbproj/user/", methods=['POST'])
def add_utilizador():

    logger.info("###              POST /dbproj/user/              ###")
    payload = request.get_json()

    conn = db_connection()
    cur = conn.cursor()

    logger.info("---- novo utilizador  ----")

    cur.execute("BEGIN TRANSACTION")
    cur.execute("LOCK TABLE utilizador")
    # parameterized queries, good for security and performance
    statement = """
                  INSERT INTO utilizador (username, email, password, banned, admin, authcode)
                          VALUES (%s, %s, %s, false, %s, DEFAULT)"""

    values = (payload["username"], payload["email"], payload["password"], payload["admin"])

    try:
        cur.execute(statement, values)
        cur.execute("commit")
        result = {'userId': payload["username"]}

    except (Exception, psycopg2.DatabaseError) as error:
        logger.error(error)
        cur.execute("ROLLBACK")
        result = {'erro': str(type(error))}

    finally:
        if conn is not None:
            conn.close()

    return jsonify(result)

#ADD LEILAO
@app.route("/dbproj/leilao/", methods=['POST'])
def add_leilao():

    logger.info("###              POST /dbproj/leilao/              ###")
    payload = request.get_json()

    if not isLoggedIn(payload):
        return jsonify({"authError": "Please log in before executing this"})

    conn = db_connection()
    cur = conn.cursor()

    logger.info("---- novo leilao  ----")

    cur.execute("BEGIN TRANSACTION")
    cur.execute("LOCK TABLE leilao")

    cur.execute("SELECT add_leilao(%s, %s, %s, %s, %s, %s);", (payload["titulo"], payload["momento_fim"], payload["preco_minimo"], payload["descricao"], payload["artigo_id"], payload["authcode"]))
    result = cur.fetchall()

    if result[0][0] != 0:
        cur.execute("commit")
        result = {'id_leilao': result[0][0]}

    else:
        cur.execute("ROLLBACK")
        result = {'Erro': 'Artigo j?? em venda ou hora de t??rmino inv??lida'}

    conn.close()
    return jsonify(result)

#ADD ARTIGO
@app.route("/dbproj/artigo/", methods=['POST'])
def add_artigo():

    logger.info("###              POST /dbproj/artigo/              ###")
    payload = request.get_json()

    if not isLoggedIn(payload):
        return jsonify({"authError": "Please log in before executing this"})

    conn = db_connection()
    cur = conn.cursor()

    logger.info("---- novo artigo  ----")

    cur.execute("BEGIN TRANSACTION")
    cur.execute("LOCK TABLE artigo")
    # parameterized queries, good for security and performance
    statement = """
                  INSERT INTO artigo (id, nome, descricao)
                          VALUES (DEFAULT, %s, %s)"""

    values = (payload["nome"], payload["descricao"])

    try:
        cur.execute(statement, values)
        cur.execute("commit")
        result = {'artigoNome': payload["nome"]}

    except (Exception, psycopg2.DatabaseError) as error:
        logger.error(error)
        cur.execute("ROLLBACK")
        result = {'erro': str(type(error))}

    finally:
        if conn is not None:
            conn.close()

    return jsonify(result)

@app.route("/dbproj/leilao/message", methods=['POST'])
def add_message_to_leilao():

    logger.info("###              POST /dbproj/leilao/message              ###");
    payload = request.get_json()

    if not isLoggedIn(payload):
        return jsonify({"authError": "Please log in before executing this"})

    conn = db_connection()
    cur = conn.cursor()

    cur.execute("BEGIN TRANSACTION")
    cur.execute("LOCK TABLE mensagem")
    cur.execute("SELECT add_message(%s, %s, %s);", (payload["id_leilao"], payload["conteudo"],payload["authcode"]))
    sucessful = cur.fetchall()

    if sucessful[0][0]:
        cur.execute("commit")
        result = 'Mensagem adicionada com sucesso!'
    else:
        cur.execute("ROLLBACK")
        result = 'Erro a adicionar mensagem: Por favor tente outra vez.!'

    return jsonify(result)

##########################################################
## PUTS
##########################################################

#LOGIN
@app.route("/dbproj/user/", methods=['PUT'])
def login():
    logger.info("###               PUT /dbproj/user/              ###")
    content = request.get_json()

    if "username" not in content or "password" not in content:
        return 'username and password are required to update'

    conn = db_connection()
    cur = conn.cursor()

    logger.info("----  login  ----")
    logger.info(f'content: {content}')

    statement = "SELECT count(*) FROM utilizador WHERE utilizador.username = %s AND utilizador.password = %s"
    values = [content["username"], content["password"]]

    cur.execute(statement, values)
    loggedIn = cur.fetchall()

    if loggedIn[0][0] == 1:
        statement = "SELECT authcode FROM utilizador WHERE utilizador.username = %s"
        values = [content["username"]]

        cur.execute(statement, values)
        result = {"authCode": cur.fetchall()[0][0]}

    else:
        logger.error("Username ou password errados")
        result = {"erro": "Username ou password errados"}

    conn.close()
    return jsonify(result)

#BANIR UTILIZADOR
@app.route("/dbproj/user/<username>/ban", methods=['PUT'])
def ban_user(username):
    logger.info("###              PUT /dbproj/user/<username>/ban              ###")
    payload = request.get_json()

    if not isAdmin(payload):
        return jsonify({"authError": "Admin permissions needed"})

    conn = db_connection()
    cur = conn.cursor()

    logger.info("---- ban user  ----")

    cur.execute("BEGIN TRANSACTION")
    cur.execute("LOCK TABLE utilizador")
    cur.execute("LOCK TABLE leilao")
    cur.execute("LOCK TABLE licitacao")

    try:
            # Colocar o atribudo "banned" a True
        statement ="""
                    UPDATE utilizador
                    SET banned = %s
                    WHERE username = %s"""

        values = (True, username)

        cur.execute(statement, values)

        # Cancelar todos os leiloes desse utilizador
        statement ="""
                    UPDATE leilao
                    SET cancelled = %s
                    WHERE creator_username = %s"""

        values = (True, username)

        cur.execute(statement, values)

        # Invalidar todas as licitacoes desse utilizador
        statement ="""
                    UPDATE licitacao
                    SET cancelled = %s
                    WHERE utilizador_username = %s"""

        values = (True, username)

        cur.execute(statement, values)

        cur.execute("SELECT DISTINCT leilao_id_leilao FROM licitacao where utilizador_username = %s", (username,))
        rows = cur.fetchall()

        logger.debug(rows)

        for row in rows:
            cur.execute("SELECT * FROM licitacao where leilao_id_leilao = %s AND utilizador_username = %s ORDER BY valor DESC LIMIT 1", (row[0], username))
            maior_licitacao_banned = cur.fetchall()

            logger.debug(maior_licitacao_banned)

            cur.execute("SELECT * FROM licitacao where leilao_id_leilao = %s AND valor > %s ORDER BY valor DESC", (row[0], maior_licitacao_banned[0][1]))
            licitacoes_afetadas = cur.fetchall()

            logger.debug(licitacoes_afetadas)

            for i in range(len(licitacoes_afetadas)):
                licitacao = licitacoes_afetadas[i]
                
                if i == 0:
                    cur.execute("UPDATE licitacao SET valor = %s WHERE id = %s", (maior_licitacao_banned[0][1], licitacao[0]))

                else:
                    cur.execute(f"INSERT INTO notificacao VALUES(DEFAULT, 'A sua licita????o foi invalidada porque um utilizador foi banido.', '{licitacao[4]}', {row[0]})")

        result = f'Updated: {cur.rowcount}'
        cur.execute("commit")

    except (Exception, psycopg2.DatabaseError) as error:
        logger.error(error)
        cur.execute("ROLLBACK")
        result = 'Erro: Por favor tente outra vez!'
    finally:
        if conn is not None:
            conn.close()

    return jsonify(result)


# EDIT LEILAO
@app.route("/dbproj/leilao/<id_leilao>", methods=['PUT'])
def edit_leilao(id_leilao):
    logger.info("###              PUT /dbproj/leilao/              ###")
    payload = request.get_json()

    if not isLoggedIn(payload):
        return jsonify({"authError": "Please log in before executing this"})

    conn = db_connection()
    cur = conn.cursor()

    logger.info("---- editar leilao  ----")

    cur.execute("BEGIN TRANSACTION")
    cur.execute("LOCK TABLE leilao")
    cur.execute("SELECT edit_leilao(%s, %s, %s, %s, %s, %s, %s);", (payload["titulo"], payload["momento_fim"], payload["preco_minimo"], payload["descricao"], id_leilao, payload["artigo_id"], payload["authcode"]))
    sucessful = cur.fetchall()

    if sucessful[0][0]:
        cur.execute("commit")
        result = 'Leil??o editado com sucesso!'
    else:
        cur.execute("ROLLBACK")
        result = 'Erro: por favor tente outra vez!'

    conn.close ()
    return jsonify(result)

# CANCELAR LEILAO
@app.route("/dbproj/leilao/<id_leilao>/cancel", methods=['PUT'])
def cancel_leilao(id_leilao):
    logger.info("###              PUT /dbproj/leilao/<id_leilao>/cancel              ###")
    payload = request.get_json()

    if not isAdmin(payload):
        return jsonify({"authError": "Admin permissions needed"})

    conn = db_connection()
    cur = conn.cursor()

    logger.info("---- editar leilao  ----")

    cur.execute("BEGIN TRANSACTION")
    cur.execute("LOCK TABLE leilao")

    # parameterized queries, good for security and performance
    statement ="""
                UPDATE leilao
                SET cancelled = %s
                WHERE id_leilao = %s; SELECT notify_cancelled(%s)"""

    values = (True, id_leilao, id_leilao);

    try:
        cur.execute(statement, values)
        result = f'Updated: {cur.rowcount}'
        cur.execute("commit")
    except (Exception, psycopg2.DatabaseError) as error:
        logger.error(error)
        cur.execute("ROLLBACK")
        result = 'Erro: por favor tente outra vez!'
    finally:
        if conn is not None:
            conn.close()

    return jsonify(result)

#TERMINAR LEILOES
@app.route("/dbproj/leiloes/end", methods=['PUT'])
def terminar_leiloes():
    logger.info("###              PUT /dbproj/leiloes/end              ###")
    payload = request.get_json()

    if not isAdmin(payload):
        return jsonify({"authError": "Admin permissions needed"})

    conn = db_connection()
    cur = conn.cursor()

    logger.info("---- terminar leiloes  ----")

    cur.execute("BEGIN TRANSACTION")
    cur.execute("LOCK TABLE leilao")

    # parameterized queries, good for security and performance
    statement ="""
                UPDATE leilao
                SET terminado = %s
                WHERE leilao.momento_fim >= CURRENT_TIMESTAMP AND leilao.terminado = false"""

    values = (True,)
    
    try:
        cur.execute(statement, values)
        result = f'Updated: {cur.rowcount}'
        
        statement ="""
                SELECT id_leilao FROM leilao WHERE leilao.terminado = true
                """
        cur.execute(statement)
        rows = cur.fetchall()
        for row in rows:
            statement ="""
                UPDATE leilao
                SET vencedor_username = %s
                WHERE leilao.terminado = true and leilao.id_leilao = %s"""
            logger.info(row[0])
            logger.info(getHighestBidder(row[0]))
            values = (getHighestBidder(row[0])[1][0][0], row[0])
            cur.execute(statement, values)
        
        cur.execute("commit")
    except (Exception, psycopg2.DatabaseError) as error:
        logger.error(error)
        cur.execute("ROLLBACK")
        result = 'Erro: Por favor tente outra vez.'
    finally:
        if conn is not None:
            conn.close()

    return jsonify(result)

##########################################################
## AUXILIARY FUNCTIONS
##########################################################

def isLoggedIn(content):

    conn = db_connection()
    cur = conn.cursor()

    if "authcode" not in content:
        return 'authcode is required to verify login status'

    logger.info("----  AUX: isLoggedIn  ----")
    logger.info(f'content: {content}')

    statement = "SELECT count(*) FROM utilizador WHERE utilizador.authcode = %s and utilizador.banned = false"
    values = [content["authcode"]]

    cur.execute(statement, values)
    count = cur.fetchall()

    if count[0][0] == 1:
        status = True

    else:
        status = False

    conn.close()
    return status

def isAdmin(content):

    if not isLoggedIn(content):
        return False

    else:
        conn = db_connection()
        cur = conn.cursor()
        statement = "SELECT admin FROM utilizador WHERE utilizador.authcode = %s"
        values = [content["authcode"]]
        cur.execute(statement, values)
        admin = cur.fetchall()

        if admin[0][0] == True:
            return True;
        else:
            return False;
        conn.close()

def getHighestBidder(id_leilao):

    conn = db_connection()
    cur = conn.cursor()
    # procurar a maior bid associada ao leilao em questao e o nome do user que a fez
    statement = """SELECT utilizador_username, MAX(valor)
    FROM licitacao
    WHERE licitacao.leilao_id_leilao = %s AND licitacao.cancelled = false
    GROUP BY utilizador_username
    ORDER BY 2 DESC
    """
    values = [id_leilao]
    cur.execute(statement, values)
    highest = cur.fetchall();

    # Quando nao ha bid nenhuma
    if highest == []:
        return (None, None)

    # Se houver bid vai buscar a info toda do user que a fez
    utilizador_username = highest[0][0];
    statement = "SELECT * FROM utilizador WHERE utilizador.username = %s"
    values = [utilizador_username]
    cur.execute(statement, values)
    user = cur.fetchall();

    conn.close()
    return (highest,user);

##########################################################
## DATABASE ACCESS
##########################################################

def db_connection():

    db = psycopg2.connect(user = "aulaspl",
                            password = "aulaspl",
                            host = "db",
                            port = "5432",
                            database = "dbfichas")
    return db

##########################################################
## MAIN
##########################################################

if __name__ == "__main__":

    # Set up the logging
    logging.basicConfig(filename="logs/log_file.log")
    logger = logging.getLogger('logger')
    logger.setLevel(logging.DEBUG)
    ch = logging.StreamHandler()
    ch.setLevel(logging.DEBUG)

    # create formatter
    formatter = logging.Formatter('%(asctime)s [%(levelname)s]:  %(message)s',
                              '%H:%M:%S')
                              # "%Y-%m-%d %H:%M:%S") # not using DATE to simplify
    ch.setFormatter(formatter)
    logger.addHandler(ch)

    time.sleep(1) # just to let the DB start before this print :-)

    logger.info("\n---------------------------------------------------------------\n" +
                  "API v1.0 online: http://localhost:8080/departments/\n\n")

    app.run(host="0.0.0.0", debug=True, threaded=True)
