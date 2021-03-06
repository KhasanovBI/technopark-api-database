import MySQLdb
from flask import Blueprint, request
from settings import BASE_URL, RESPONSE_CODES
from utils import queries
from utils.helper import jsonify, get_connection, parse_json

forum_API = Blueprint('forum_API', __name__, url_prefix=BASE_URL + 'forum/')


@forum_API.route('create/', methods=['POST'])
def forum_create():
    json_dict = parse_json(request)
    name = json_dict.get('name', None)
    short_name = json_dict.get('short_name', None)
    user = json_dict.get('user', None)
    db = get_connection()
    cursor = db.cursor(MySQLdb.cursors.DictCursor)

    try:
        cursor.execute("""INSERT INTO `forums` (`name`, `short_name`, `user`) VALUES (%s, %s, %s);""",
                       (name, short_name, user))
        db.commit()

    except MySQLdb.Error:
        db.rollback()

    forum = queries.forum_details(cursor, short_name)

    cursor.close()
    db.close()
    return jsonify({'code': 0, 'response': forum})


@forum_API.route('details/')
def forum_details():
    short_name = request.args.get('forum', None)
    related = request.args.get('related', [])

    if short_name is None:
        code = 1
        return jsonify({'code': code, 'response': RESPONSE_CODES[code]})
    db = get_connection()
    cursor = db.cursor(MySQLdb.cursors.DictCursor)

    forum = queries.forum_details(cursor, short_name)

    if 'user' in related:
        user = queries.user_details(cursor, forum['user'])
        forum.update({'user': user})

    cursor.close()
    db.close()
    return jsonify({'code': 0, 'response': forum})


@forum_API.route('listPosts/')
def forum_list_posts():
    forum = request.args.get('forum', None)
    since = request.args.get('since')
    limit = request.args.get('limit')
    order = request.args.get('order', 'desc')
    related = request.args.getlist('related')

    if forum is None:
        code = 1
        return jsonify({'code': code, 'response': RESPONSE_CODES[code]})

    query = """SELECT  `id`, `message`, `forum`, `user`, `thread`, `likes`, `dislikes`, `points`, `isDeleted`,
`isSpam`, `isEdited`, `isApproved`, `isHighlighted`, `date`, `parent` FROM `posts` WHERE `forum` = %s """
    query_params = (forum,)

    if since is not None:
        query += "AND `date` >= %s "
        query_params += (since,)

    query += "ORDER BY `date` " + order + " "

    if limit is not None:
        query += "LIMIT %s;"
        query_params += (int(limit),)

    db = get_connection()
    cursor = db.cursor(MySQLdb.cursors.DictCursor)
    cursor.execute(query, query_params)

    posts = [i for i in cursor.fetchall()]

    for post in posts:
        if 'user' in related:
            user = queries.user_details(cursor, post['user'])
            post.update({'user': user})

        if 'forum' in related:
            forum = queries.forum_details(cursor, post['forum'])
            post.update({'forum': forum})

        if 'thread' in related:
            thread = queries.thread_details(cursor, post['thread'])
            post.update({'thread': thread})

        post.update({'date': str(post['date'])})

    cursor.close()
    db.close()
    return jsonify({'code': 0, 'response': posts})


@forum_API.route('listThreads/')
def forum_list_threads():
    forum = request.args.get('forum')
    since = request.args.get('since')
    limit = request.args.get('limit')
    order = request.args.get('order', 'desc')
    related = request.args.getlist('related')

    if forum is None:
        code = 1
        return jsonify({'code': code, 'response': RESPONSE_CODES[code]})

    query = """SELECT * FROM `threads` WHERE `forum` = %s"""
    query_params = (forum,)

    if since is not None:
        query += "AND `date` >= %s "
        query_params += (since,)

    query += "ORDER BY `date` " + order + " "

    if limit is not None:
        query += "LIMIT %s;"
        query_params += (int(limit),)

    db = get_connection()
    cursor = db.cursor(MySQLdb.cursors.DictCursor)
    cursor.execute(query, query_params)

    threads = [i for i in cursor.fetchall()]

    for thread in threads:
        if 'user' in related:
            user = queries.user_details(cursor, thread['user'])
            thread.update({'user': user})

        if 'forum' in related:
            forum = queries.forum_details(cursor, thread['forum'])
            thread.update({'forum': forum})

        thread.update({'date': str(thread['date'])})

    cursor.close()
    db.close()
    return jsonify({'code': 0, 'response': threads})


@forum_API.route('listUsers/')
def forum_list_users():
    forum = request.args.get('forum', None)
    since_id = request.args.get('since_id')
    limit = request.args.get('limit')
    order = request.args.get('order', 'desc')

    if forum is None:
        code = 1
        return jsonify({'code': code, 'response': RESPONSE_CODES[code]})

    query = """SELECT * FROM `users`
            WHERE `email` IN (SELECT DISTINCT `user` FROM `posts` WHERE `forum` = %s)"""
    query_params = (forum,)

    if since_id is not None:
        query += "AND `id` >= %s "
        query_params += (int(since_id),)

    query += " ORDER BY `name` " + order + " "

    if limit is not None:
        query += "LIMIT %s;"
        query_params += (int(limit),)

    db = get_connection()
    cursor = db.cursor(MySQLdb.cursors.DictCursor)
    cursor.execute(query, query_params)

    users = [i for i in cursor.fetchall()]

    for user in users:
        following = queries.list_following(cursor, user['email'])
        followers = queries.list_followers(cursor, user['email'])

        cursor.execute("""SELECT `thread` FROM `users_threads` WHERE `user` = %s;""", (user['email'],))
        threads = [i['thread'] for i in cursor.fetchall()]

        user.update({'following': following, 'followers': followers, 'subscriptions': threads})

    cursor.close()
    db.close()
    return jsonify({'code': 0, 'response': users})
