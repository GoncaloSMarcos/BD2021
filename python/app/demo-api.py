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

@app.route("/dbproj/user/", methods=['GET'])
def get_all_users():

    logger.info("###              GET /dbproj/user/              ###");   

    conn = db_connection()
    cur = conn.cursor()

    cur.execute("SELECT username, email FROM utilizador")
    rows = cur.fetchall()

    payload = []
    logger.debug("---- Utilizadores  ----")
    for row in rows:
        logger.debug(row)
        content = {'username': row[0], 'email': row[1]}
        payload.append(content) # appending to the payload to be returned

    conn.close()
    return jsonify(payload)


@app.route("/dbproj/leiloes/", methods=['GET'])
def get_all_leiloes():

    logger.info("###              GET /dbproj/leiloes/              ###");   

    conn = db_connection()
    cur = conn.cursor()

    cur.execute("SELECT id_leilao, titulo, descricao, preco_minimo, momento_fim, id_versao  FROM leilao")
    rows = cur.fetchall()

    payload = []
    logger.debug("---- Leiloes  ----")
    for row in rows:
        logger.debug(row)
        content = {'username': row[0], 'email': row[1]}
        content = {'id_leilao': row[0], 'titulo': row[1], 'descricao': row[2], 'preco_minimo': row[3], 'momento_fim': row[4], 'id_versao': row[5]}
        payload.append(content) # appending to the payload to be returned

    conn.close()
    return jsonify(payload)

##########################################################
## POSTS
##########################################################

@app.route("/dbproj/user/", methods=['POST'])
def add_utilizador():

    logger.info("###              POST /dbproj/user/              ###");   
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

##########################################################
## PUTS
##########################################################

@app.route("/dbproj/user/", methods=['PUT'])
def update_departments():
    logger.info("###               PUT /dbproj/user/              ###");   
    content = request.get_json()

    conn = db_connection()
    cur = conn.cursor()


    #if content["ndep"] is None or content["nome"] is None :
    #    return 'ndep and nome are required to update'

    if "ndep" not in content or "localidade" not in content:
        return 'ndep and localidade are required to update'


    logger.info("---- update department  ----")
    logger.info(f'content: {content}')

    # parameterized queries, good for security and performance
    statement ="""
                UPDATE dep 
                  SET local = %s
                WHERE ndep = %s"""


    values = (content["localidade"], content["ndep"])

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
