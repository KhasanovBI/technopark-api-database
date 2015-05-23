import MySQLdb
from settings import DATABASE
from flask import Response
import ujson
import ujson as json

def get_connection():
    return MySQLdb.connect(host=DATABASE['HOST'], user=DATABASE['USER'], passwd=DATABASE['PASSWORD'],
                           db=DATABASE['NAME'], charset=DATABASE['CHARSET'])


def extract_params(input_dict, keys_list):
    output_dict = {}
    for key in keys_list:
        output_dict[key] = input_dict.get(key, None)
    return output_dict


def jsonify(input_dict):
    return Response(mimetype='application/json', response=ujson.dumps(input_dict))


def parse_json(request):
    return json.loads(request.data)