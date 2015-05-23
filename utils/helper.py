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


def jsonify(*args, **kwargs):
    return Response(mimetype='application/json', response=ujson.dumps(dict(*args, **kwargs)))


def parse_json(request):
    return ujson.loads(request.data)


def _get_data(req, cache):
    getter = getattr(req, 'get_data', None)
    if getter is not None:
        return getter(cache=cache)
    return req.data
_missing = object()

def get_json(request, silent=False, cache=True):
    rv = getattr(request, '_cached_json', _missing)
    if rv is not _missing:
        return rv

    if request.mimetype != 'application/json':
        return None

    request_charset = request.mimetype_params.get('charset')
    try:
        data = _get_data(request, True)
        if request_charset is not None:
            rv = json.loads(data, encoding=request_charset)
        else:
            rv = json.loads(data)
    except ValueError as e:
        if silent:
            rv = None
        else:
            rv = request.on_json_loading_failed(e)
    request._cached_json = rv
    return rv