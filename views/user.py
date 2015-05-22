import MySQLdb
from flask import Blueprint, request
from settings import BASE_URL, RESPONSE_CODES
from utils import queries
from utils.queries import list_followers, list_following
from utils.helper import extract_params, get_connection, jsonify, parse_json

user_API = Blueprint('user_API', __name__, url_prefix=BASE_URL + 'user/')


@user_API.route('create/', methods=['POST'])
def user_create():

    params = ['email', 'username', 'name', 'about', 'isAnonymous']
    params = extract_params(parse_json(request), params)
    if params['isAnonymous'] is None:
        params['isAnonymous'] = False

    db = get_connection()
    cursor = db.cursor()
    try:
        cursor.execute(
            """INSERT INTO `users` (`email`, `username`, `name`, `about`, `isAnonymous`)
VALUES (%s, %s, %s, %s, %s);""",
            (params['email'], params['username'], params['name'], params['about'], params['isAnonymous']))
        user_id = cursor.lastrowid
        db.commit()
    except MySQLdb.Error:
        db.rollback()
        cursor.close()
        code = 5
        return jsonify(code=code, response=RESPONSE_CODES[code])
    cursor.close()
    db.close()
    user = params
    user.update({'id': user_id})
    return jsonify(code=0, response=user)


@user_API.route('details/')
def user_details():
    email = request.args.get('user', None)

    if email is None:
        code = 1
        return jsonify(code=code, response=RESPONSE_CODES[code])

    db = get_connection()
    cursor = db.cursor(MySQLdb.cursors.DictCursor)
    user = queries.user_details(cursor, email)
    cursor.close()
    db.close()
    return jsonify(code=0, response=user)


@user_API.route('listPosts/')
def user_list_posts():
    user = request.args.get('user')
    since = request.args.get('since')
    limit = request.args.get('limit')
    order = request.args.get('order', 'desc')

    if user is None:
        code = 1
        return jsonify(code=code, response=RESPONSE_CODES[code])

    query = """SELECT * FROM `posts` WHERE `user` = %s """
    query_params = (user,)

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

    cursor.close()
    db.close()

    for post in posts:
        post.update({'date': str(post['date'])})

    return jsonify(code=0, response=posts)


@user_API.route('updateProfile/', methods=['POST'])
def user_update_profile():
    user = parse_json(request).get('user', None)
    about = parse_json(request).get('about', None)
    name = parse_json(request).get('name', None)

    db = get_connection()
    cursor = db.cursor(MySQLdb.cursors.DictCursor)
    try:
        cursor.execute("""UPDATE `users` SET `about` = %s, `name` = %s WHERE `email` = %s;""", (about, name, user))
        db.commit()
    except MySQLdb.Error:
        db.rollback()

    user = queries.user_details(cursor, user)
    cursor.close()
    db.close()

    return jsonify(code=0, response=user)


@user_API.route('follow/', methods=['POST'])
def user_follow():
    follower = parse_json(request).get('follower', None)
    followee = parse_json(request).get('followee', None)

    db = get_connection()
    cursor = db.cursor(MySQLdb.cursors.DictCursor)

    try:
        cursor.execute("""INSERT INTO `follower_followee` (`follower`, `followee`)
VALUES (%s, %s);""", (follower, followee))

        db.commit()
    except MySQLdb.Error:
        db.rollback()

    user = queries.user_details(cursor, follower)
    cursor.close()
    db.close()
    return jsonify(code=0, response=user)


@user_API.route('listFollowers/')
def user_list_followers():
    user = request.args.get('user', None)
    since_id = request.args.get('since_id')
    limit = request.args.get('limit')
    order = request.args.get('order', 'desc')

    if user is None:
        code = 1
        return jsonify(code=code, response=RESPONSE_CODES[code])

    query = """SELECT `about`, `email`, `id`, `isAnonymous`, `name`, `username`  FROM `follower_followee` AS `ff`
JOIN `users` ON `users`.`email` = `ff`.`follower`
WHERE `ff`.followee = %s"""
    query_params = (user,)

    if since_id is not None:
        query += "AND `users`.`id` >= %s "
        query_params += (int(since_id),)

    query += "ORDER BY `name` " + order + " "

    if limit is not None:
        query += "LIMIT %s;"
        query_params += (int(limit),)

    db = get_connection()
    cursor = db.cursor(MySQLdb.cursors.DictCursor)
    cursor.execute(query, query_params)

    users = [i for i in cursor.fetchall()]

    for user in users:
        following = list_following(cursor, user['email'])
        followers = list_followers(cursor, user['email'])

        cursor.execute("""SELECT `thread` FROM `users_threads` WHERE `user` = %s;""", (user['email'],))
        threads = [i['thread'] for i in cursor.fetchall()]

        user.update({'following': following, 'followers': followers, 'subscriptions': threads})

    cursor.close()
    db.close()
    return jsonify(code=0, response=users)


@user_API.route('listFollowing/')
def user_list_following():
    user = request.args.get('user', None)
    since_id = request.args.get('since_id')
    limit = request.args.get('limit')
    order = request.args.get('order', 'desc')

    if user is None:
        code = 1
        return jsonify(code=code, response=RESPONSE_CODES[code])

    query = """SELECT `about`, `email`, `id`, `isAnonymous`, `name`, `username`  FROM `follower_followee` AS `ff`
JOIN `users` ON `users`.`email` = `ff`.`followee`
WHERE `ff`.follower = %s"""
    query_params = (user,)

    if since_id is not None:
        query += "AND `users`.`id` >= %s "
        query_params += (int(since_id),)

    query += "ORDER BY `name` " + order + " "

    if limit is not None:
        query += "LIMIT %s;"
        query_params += (int(limit),)

    db = get_connection()
    cursor = db.cursor(MySQLdb.cursors.DictCursor)
    cursor.execute(query, query_params)

    users = [i for i in cursor.fetchall()]

    for user in users:
        following = list_following(cursor, user['email'])
        followers = list_followers(cursor, user['email'])

        cursor.execute("""SELECT `thread` FROM `users_threads` WHERE `user` = %s;""", (user['email'],))
        threads = [i['thread'] for i in cursor.fetchall()]

        user.update({'following': following, 'followers': followers, 'subscriptions': threads})

    cursor.close()
    db.close()
    return jsonify(code=0, response=users)


@user_API.route('unfollow/', methods=['POST'])
def user_unfollow():
    follower = parse_json(request).get('follower', None)
    followee = parse_json(request).get('followee', None)

    db = get_connection()
    cursor = db.cursor(MySQLdb.cursors.DictCursor)
    try:
        cursor.execute("""DELETE FROM `follower_followee` WHERE `follower` = %s AND `followee` = %s;""",
                       (follower, followee))
        db.commit()
    except MySQLdb.Error:
        db.rollback()

    user = queries.user_details(cursor, follower)
    cursor.close()
    db.close()
    return jsonify(code=0, response=user)