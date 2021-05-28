from flask import Flask, jsonify, request
import logging, psycopg2, time

app = Flask(__name__)

@app.route('/')
def hello():

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




@app.route("/dbproj/leiloes/{keyword}", methods=['GET'])
def get_leilao():

    logger.info("###              GET  /dbproj/leiloes/{keyword}             ###")

    conn = db_connection()
    cur = conn.cursor()

    cur.execute("SELECT id_leilao, titulo, descricao, preco_minimo, momento_fim, id_familia  FROM leilao")
    rows = cur.fetchall()

    payload = []
    logger.debug("---- Leiloes  ----")
    for row in rows:
        logger.debug(row)
        content = {'id_leilao': row[0], 'titulo': row[1], 'descricao': row[2], 'preco_minimo': row[3], 'momento_fim': row[4], 'id_familia': row[5]}
        payload.append(content) # appending to the payload to be returned

    conn.close()
    return jsonify(payload)




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
                          VALUES (%s, %s, %s, false, false, DEFAULT)"""

    values = (payload["username"], payload["email"], payload["password"])

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
