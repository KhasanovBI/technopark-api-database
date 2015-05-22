from flask import Blueprint
from settings import BASE_URL, RESPONSE_CODES
from utils.helper import jsonify, get_connection
from utils.queries import init_tables

general_API = Blueprint('general_API', __name__, url_prefix=BASE_URL)


@general_API.route('clear/', methods=['POST'])
def clear():
    init_tables()
    code = 0
    return jsonify(code=code, response=RESPONSE_CODES[code])


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
    return jsonify(code=0, response=response)