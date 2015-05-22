import MySQLdb
from settings import DATABASE
from flask import Response
import ujson


def get_connection():
    return MySQLdb.connect(host=DATABASE['HOST'], user=DATABASE['USER'], passwd=DATABASE['PASSWORD'],
                           db=DATABASE['NAME'], charset=DATABASE['CHARSET'])


def extract_params(input_dict, keys_list):
    output_dict = {}
    for key in keys_list:
        output_dict[key] = input_dict.get(key, None)
    return output_dict


def jsonify(*args, **kwargs):
    return Response(mimetype='application/json', response=ujson.dumps(dict(*args, **kwargs)))


def parse_json(request):
    return ujson.loads(request.data)