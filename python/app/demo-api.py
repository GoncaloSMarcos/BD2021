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

    cur.execute("SELECT username, email FROM utilizador")
    rows = cur.fetchall()

    payload = []

    for row in rows:
        logger.debug(row)
        content = {'username': row[0], 'email': row[1]}
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

    logger.debug("---- Leiloes  ----")
    
    cur.execute("SELECT id_leilao, titulo, descricao, preco_minimo, momento_fim, id_familia  FROM leilao")
    rows = cur.fetchall()

    payload = []

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
                  INSERT INTO utilizador (username, email, password, banned, admin)
                          VALUES (%s, %s, %s, false, false)"""

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
                  INSERT INTO leilao (artigo_id, preco_minimo, titulo, descricao, momento_fim, versao, id_leilao, id_familia, cancelled)
                          VALUES (%s, %s, %s, %s, %s, 1, %s, %s,false)"""

    values = (payload["artigo_id"], payload["preco_minimo"], payload["titulo"], payload["descricao"], payload["momento_fim"], payload["id_leilao"], payload["id_familia"])

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
    
    statement = "SELECT password FROM utilizador WHERE utilizador.username = %s"           
    values = [content["username"]]

    cur.execute(statement, values)
    password = cur.fetchall()

    if not password:
        logger.error("Utilizador não existente")
        result = {"erro": "Utilizador não existente"}

    elif password[0][0] == content["password"]:

        statement = "SELECT authcode FROM utilizador WHERE utilizador.username = %s"           
        values = [content["username"]]

        cur.execute(statement, values)
        result = {"authCode": cur.fetchall()[0][0]}

    else:
        logger.error("Password errada")
        result = {"erro": "Password errada"}

    conn.close()
    return jsonify(result)

##########################################################
## AUXILIARY FUNCTIONS
##########################################################

def isLoggedIn(content):

    conn = db_connection()
    cur = conn.cursor()

    if "username" not in content or "authcode" not in content:
        return 'username and authcode are required to update'
    
    logger.info("----  AUX: isLoggedIn  ----")
    logger.info(f'content: {content}')

    statement = "SELECT authcode FROM utilizador WHERE utilizador.username = %s"           
    values = [content["username"]]

    cur.execute(statement, values)
    authcode = cur.fetchall()

    if authcode and str(authcode[0][0]) == content["authcode"]:
        conn.close()
        return True

    else:
        conn.close()
        return False

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
