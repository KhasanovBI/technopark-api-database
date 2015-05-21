import MySQLdb
import os
BASE_URL = '/db/api/'
sqlSchema = os.path.join(os.path.dirname(__file__), 'schema.sql')
RESPONSE_CODES = {0: "OK",
                  1: "Requested Object Not Found",
                  2: "Not Valid Request",
                  3: "Bad Request",
                  4: "Unknown Error",
                  5: "User already exists"}
try:
    from local_settings import *
except ImportError:
    pass

def get_connection():
    return MySQLdb.connect(host=DATABASE['HOST'], user=DATABASE['USER'], passwd=DATABASE['PASSWORD'],
                           db=DATABASE['NAME'], charset=DATABASE['CHARSET'])