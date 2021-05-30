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

    conn = db_connection()
    cur = conn.cursor()

    cur.execute("SELECT * FROM utilizador")
    rows = cur.fetchall()

    payload = []

    for row in rows:
        content = {'username': row[0], 'email': row[1], 'password': row[2], 'banned': row[3], 'admin': row[4], 'authcode': row[5]}
        payload.append(content) # appending to the payload to be returned

    conn.close()
    return jsonify(payload)

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
        content = {'id_leilao': row[0], 'titulo': row[1], 'descricao': row[2], 'preco_minimo': row[3], 'momento_fim': row[4], 'id_familia': row[5], 'versao': row[6], 'creator_username': row[7], 'artigo_id': int(row[8]), 'cancelled': row[9], 'highestBid': getHighestBidder(row[0])[0][0][1], 'highestBidder': getHighestBidder(row[0])[1][0][0]}
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
        cur.execute("""SELECT id_leilao, titulo, momento_fim, preco_minimo, descricao, artigo_id, creator_username
                    FROM leilao 
                    WHERE leilao.id_leilao = %s AND leilao.cancelled = false""", (id_leilao,) )
        
        rows = cur.fetchall()
        row = rows[0]

        content = {'id_leilao': int(row[0]), 'titulo': row[1], 'momento_fim': row[2], 'preco_minimo': int(row[3]), 'descricao': row[4], 'artigo_id': int(row[5]), 'creator_username': row[6], 'highestBid': getHighestBidder(row[0])[0][0][1], 'highestBidder': getHighestBidder(row[0])[1][0][0]}

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
        cur.execute(f"SELECT id_leilao, titulo, momento_fim, preco_minimo, descricao, artigo_id, creator_username FROM leilao WHERE (CAST(id_leilao as VARCHAR(10)) = '{keyword}' OR descricao LIKE '%{keyword}%') AND leilao.cancelled = false")      #id_leilao*1 = id_leilao significa se e numerico
        rows = cur.fetchall()

        output = []

        for row in rows:
            content = {'id_leilao': int(row[0]), 'titulo': row[1], 'momento_fim': row[2], 'preco_minimo': int(row[3]), 'descricao': row[4], 'artigo_id': int(row[5]), 'creator_username': row[6], 'highestBid': getHighestBidder(row[0])[0][0][1], 'highestBidder': getHighestBidder(row[0])[1][0][0]}
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
        cur.execute(f"""SELECT id_leilao, descricao 
                        FROM leilao 
                        WHERE leilao.id_familia = (SELECT id_familia
                                                   FROM leilao
                                                   WHERE leilao.id_leilao = {id_leilao})
                        ORDER BY versao DESC""") 
        rows = cur.fetchall()

        output = []

        for row in rows:
            content = {'id_leilao': int(row[0]), 'descricao': row[1]}
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

        return jsonify('ERROR: Leilao missing from database!') # TODO meter algo de jeito aqui

#EFETUAR LICITACAO
@app.route("/dbproj/licitar/<leilaoId>/<licitacao>", methods=['GET'])
def licitar(leilaoId, licitacao):

    logger.info("###              GET /dbproj/licitar/<leilaoId>/<licitacao>              ###");

    payload = request.get_json()

    if not isLoggedIn(payload):
        return jsonify({"authError": "Please log in before executing this"})

    conn = db_connection()
    cur = conn.cursor()

    cur.execute("SELECT licitar(%s, %s, %s);", (licitacao, payload["authcode"], leilaoId))
    sucessful = cur.fetchall()

    if sucessful[0][0]:
        cur.execute("commit")
        result = 'Licitação realizada com sucesso!'
    else:
        result = 'Erro! Verifique se está a licitar um valor superior ao atual e ao preço mínimo.'

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

    cur.execute("SELECT * FROM get_top10_criadores(%s);", (payload["authcode"],))
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

    cur.execute("SELECT * FROM get_top10_vencedores(%s);", (payload["authcode"],))
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
    
    content = {'Total de leilões nos últimos 10 dias': total[0][0]}
    
    conn.close()
    return jsonify(content)


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

    cur.execute("SELECT add_leilao(%s, %s, %s, %s, %s, %s);", (payload["titulo"], payload["momento_fim"], payload["preco_minimo"], payload["descricao"], payload["artigo_id"], payload["authcode"]))
    result = cur.fetchall()
    
    if result[0][0] != 0:
        cur.execute("commit")
        result = {'id_leilao': result[0][0]}

    else:

        result = {'Erro': 'Artigo já em venda, por favor escolha outro artigo'}

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

    cur.execute("SELECT add_message(%s, %s, %s);", (payload["id_leilao"], payload["conteudo"],payload["authcode"]))
    sucessful = cur.fetchall()

    if sucessful[0][0]:
        cur.execute("commit")
        result = 'Teste: Sucedido!' # TODO Mudar isto para outputs adequados
    else:
        result = 'Teste: Failed!' # TODO Mudar isto para outputs adequados

    conn.close ()
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

    cur.execute("SELECT edit_leilao(%s, %s, %s, %s, %s, %s, %s);", (payload["titulo"], payload["momento_fim"], payload["preco_minimo"], payload["descricao"], id_leilao, payload["artigo_id"], payload["authcode"]))
    sucessful = cur.fetchall()

    if sucessful[0][0]:
        cur.execute("commit")
        result = 'Teste: Sucedido!' # TODO Mudar isto para outputs adequados
    else:
        result = 'Teste: Failed!' # TODO Mudar isto para outputs adequados

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

    # parameterized queries, good for security and performance
    statement ="""
                UPDATE leilao 
                SET cancelled = %s
                WHERE id_leilao = %s"""

    values = (True, id_leilao)
    
    try:
        cur.execute(statement, values)
        result = f'Updated: {cur.rowcount}'
        cur.execute("commit")
    except (Exception, psycopg2.DatabaseError) as error:
        logger.error(error)
        result = 'Failed!' # TODO Mudar isto para outputs adequados
    finally:
        if conn is not None:
            conn.close()
    
    return jsonify(result)

#TERMINAR LEILOES
@app.route("/dbproj/leiloes/end", methods=['PUT'])
def terminar_leiloes(id_leilao):
    logger.info("###              PUT /dbproj/leiloes/end              ###")
    payload = request.get_json()

    if not isAdmin(payload):
        return jsonify({"authError": "Admin permissions needed"})

    conn = db_connection()
    cur = conn.cursor()

    logger.info("---- terminar leiloes  ----")

    # parameterized queries, good for security and performance
    statement ="""
                UPDATE leilao 
                SET terminado = %s
                WHERE leilao.momento_fim >= CURRENT_TIMESTAMP()"""

    values = (True,)
    
    try:
        cur.execute(statement, values)
        result = f'Updated: {cur.rowcount}' # TODO N sei se isto funciona, gonçalo, test it
        cur.execute("commit")
    except (Exception, psycopg2.DatabaseError) as error:
        logger.error(error)
        result = 'Failed!' # TODO Mudar isto para outputs adequados
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
        return jsonify({"authError": "Please log in before executing this"})
    
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
