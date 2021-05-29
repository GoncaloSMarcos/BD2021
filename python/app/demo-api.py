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

    logger.debug("---- Utilizadores  ----")

    cur.execute("SELECT * FROM utilizador")
    rows = cur.fetchall()

    payload = []

    for row in rows:
        logger.debug(row)
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

    logger.debug("----  Leiloes  ----")

    cur.execute("SELECT id_leilao, titulo, descricao, preco_minimo, momento_fim, id_familia, versao FROM leilao")
    rows = cur.fetchall()

    payload = []

    for row in rows:
        logger.debug(row)
        content = {'id_leilao': row[0], 'titulo': row[1], 'descricao': row[2], 'preco_minimo': row[3], 'momento_fim': row[4], 'id_familia': row[5], 'versao': row[6]}
        payload.append(content) # appending to the payload to be returned

    conn.close()
    return jsonify(payload)

#GET LEILAO BY ID
@app.route("/dbproj/leilao/<id_leilao>", methods=['GET'])
def get_leilao(id_leilao):
    logger.info("###              DEMO: GET /leilao/<id_leilao>              ###");

    logger.debug(f'id_leilao: {id_leilao}')

    conn = db_connection()
    cur = conn.cursor()


    try:
        cur.execute("""SELECT id_leilao, titulo, momento_fim, preco_minimo, descricao, cancelled, artigo_id
                    FROM leilao 
                    WHERE id_leilao = %s""", (id_leilao,) )
        rows = cur.fetchall()

        row = rows[0]

        logger.debug("---- selected leilao  ----")
        logger.debug(row)
        content = {'id_leilao': int(row[0]), 'titulo': row[1], 'momento_fim': row[2], 'preco_minimo': int(row[3]), 'descricao': row[4], 'cancelled': row[5], 'artigo_id': int(row[6])}

        conn.close ()
        return jsonify(content)

    except (Exception) as error:
        logger.debug("Este aqui mesmo:")
        logger.error(error)
        logger.error(type(error))

        return jsonify('ERROR: Leilao missing from database!')

#GET ALL ARTIGOS
@app.route("/dbproj/artigo/", methods=['GET'])
def get_all_artigos():

    logger.info("###              GET /dbproj/artigo/              ###")

    conn = db_connection()
    cur = conn.cursor()

    logger.debug("---- Artigos  ----")

    cur.execute("SELECT * FROM artigo")
    rows = cur.fetchall()

    payload = []

    for row in rows:
        logger.debug(row)
        content = {'id': row[0], 'nome': row[1], 'descricao': row[2]}
        payload.append(content) # appending to the payload to be returned

    conn.close()
    return jsonify(payload)

#GET LEILAO BY KEYWORD
@app.route("/dbproj/leiloes/<keyword>", methods=['GET'])
def get_leilao_keyword(keyword):

    logger.info("###              DEMO: GET /leiloes/<keyword>              ###");

    logger.debug(f'keyword: {keyword}')

    conn = db_connection()
    cur = conn.cursor()

    try:
        cur.execute(f"SELECT id_leilao, descricao FROM leilao WHERE CAST(id_leilao as VARCHAR(10)) = '{keyword}' OR descricao LIKE '%{keyword}%'")      #id_leilao*1 = id_leilao significa se e numerico
        rows = cur.fetchall()

        row = rows[0]

        logger.debug("---- selected leilao  ----")
        logger.debug(row)
        content = {'id_leilao': int(row[0]), 'descricao': row[1]}

        conn.close ()
        return jsonify(content)

    except (Exception) as error:
        logger.error(error)
        logger.error(type(error))

        return jsonify('ERROR: Leilao missing from database!')

#EFETUAR LICITACAO
@app.route("/dbproj/licitar/<leilaoId>/<licitacao>", methods=['GET'])
def licitar(leilaoId, licitacao):
    
    logger.info("###              GET /dbproj/licitar/<leilaoId>/<licitacao>              ###");
    logger.debug(f'leilaoId: {leilaoId}')
    logger.debug(f'licitacao: {licitacao}')
    
    payload = request.get_json()
    
    if not isLoggedIn(payload):
        return jsonify({"authError": "Please log in before executing this"})

    conn = db_connection()
    cur = conn.cursor()

    cur.execute("SELECT licitar(%s, %s, %s);", (licitacao, payload["authcode"], leilaoId))
    sucessful = cur.fetchall()
    
    logger.debug(f'sucessful: {sucessful}')

    if sucessful[0][0]:
        cur.execute("commit")
        result = 'Teste: Sucedido!'
    else:
        result = 'Teste: Failed!' 
    
    conn.close ()
    return jsonify(result)


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
    logger.debug(f'payload: {payload}')

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
    logger.debug(f'payload: {payload}')

    # parameterized queries, good for security and performance
    statement = """
                  INSERT INTO leilao (id_leilao, titulo, momento_fim, preco_minimo, descricao, versao, id_familia, cancelled, artigo_id)
                          VALUES (DEFAULT, %s, %s, %s, %s, 1, %s, false, %s)"""

    values = (payload["titulo"], payload["momento_fim"], payload["preco_minimo"], payload["descricao"], payload["id_familia"], payload["artigo_id"])

    try:
        cur.execute(statement, values)
        cur.execute("commit")
        result = {'id_leilao': payload["id_leilao"]}

    except (Exception, psycopg2.DatabaseError) as error:
        logger.error(error)
        result = {'erro': str(type(error))}

    finally:
        if conn is not None:
            conn.close()

    return jsonify(result)

#ADD ARTIGO
@app.route("/dbproj/artigo/", methods=['POST'])
def add_artigo():

    logger.info("###              POST /dbproj/artigo/              ###")
    payload = request.get_json()

    conn = db_connection()
    cur = conn.cursor()

    logger.info("---- novo artigo  ----")
    logger.debug(f'payload: {payload}')

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
    logger.debug(f'payload: {payload}')

    # parameterized queries, good for security and performance
    statement = """
                  INSERT INTO leilao (id_leilao, titulo, momento_fim, preco_minimo, descricao, versao, id_familia, cancelled, artigo_id)
                          VALUES (DEFAULT, %s, %s, %s, %s, 2, %s, false, %s)"""

    cur.execute("SELECT edit_leilao(%s, %s, %s, %s, %s, %s);", (payload["titulo"], payload["momento_fim"], payload["preco_minimo"], payload["descricao"], id_leilao, payload["artigo_id"]))
    sucessful = cur.fetchall()
    
    logger.debug(f'sucessful: {sucessful}')

    if sucessful[0][0]:
        cur.execute("commit")
        result = 'Teste: Sucedido!'
    else:
        result = 'Teste: Failed!' 
        
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
    logger.debug(f'payload: {payload}')

    # parameterized queries, good for security and performance
    statement ="""
                UPDATE leilao 
                  SET cancelled = %s
                WHERE id_leilao = %s"""


    values = (True, id_leilao)
    
    try:
        res = cur.execute(statement, values)
        result = f'Updated: {cur.rowcount}'
        cur.execute("commit")
    except (Exception, psycopg2.DatabaseError) as error:
        logger.error(error)
        result = 'Failed!'
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

    statement = "SELECT count(*) FROM utilizador WHERE utilizador.authcode = %s"
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
