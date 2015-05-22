from flask import Blueprint, Response
from settings import BASE_URL, RESPONSE_CODES, get_connection
import ujson
from utils.queries import init_tables

general_API = Blueprint('general_API', __name__, url_prefix=BASE_URL)


@general_API.route('clear/', methods=['POST'])
def clear():
    init_tables()
    code = 0
    return Response(mimetype='application/json', response=ujson.dumps({'code':code, 'response':RESPONSE_CODES[code]}))


@general_API.route('status/')
def status():
    tables = ['users', 'threads', 'forums', 'posts']
    response = {}
    db = get_connection()
    cursor = db.cursor()
    for table in tables:
        cursor.execute('SELECT COUNT(1) FROM %s' % table)
        db.commit()
        response[table] = cursor.fetchone()[0]
    cursor.close()
    db.close()
    return Response(mimetype='application/json', response=ujson.dumps({'code':0, 'response':response}))
