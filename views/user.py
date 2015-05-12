import MySQLdb
from flask import Blueprint, request, jsonify
from settings import BASE_URL, db, RESPONSE_CODES
from utils import queries
from utils.queries import list_followers, list_following
from utils.helper import extract_params

user_API = Blueprint('user_API', __name__, url_prefix=BASE_URL + 'user/')


@user_API.route('create/', methods=['POST'])
def user_create():
    params = ['email', 'username', 'name', 'about', 'isAnonymous']
    params = extract_params(request.json, params)
    if params['isAnonymous'] is None:
        params['isAnonymous'] = False

    cursor = db.cursor()
    try:
        cursor.execute(
            """INSERT INTO `users` (`email`, `username`, `name`, `about`, `isAnonymous`) VALUE (%s, %s, %s, %s, %s);""",
            (params['email'], params['username'], params['name'], params['about'], params['isAnonymous']))
        user_id = cursor.lastrowid
        db.commit()
    except MySQLdb.Error:
        db.rollback()
        cursor.close()
        code = 5
        return jsonify(code=code, response=RESPONSE_CODES[code])
    cursor.close()

    user = params
    user.update({'id': user_id})

    return jsonify(code=0, response=user)


@user_API.route('details/')
def user_details():
    email = request.args.get('user', None)

    if email is None:
        code = 1
        return jsonify(code=code, response=RESPONSE_CODES[code])

    cursor = db.cursor(MySQLdb.cursors.DictCursor)
    user = queries.user_details(cursor, email)
    cursor.close()

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

    cursor = db.cursor(MySQLdb.cursors.DictCursor)
    cursor.execute(query, query_params)

    posts = [i for i in cursor.fetchall()]

    cursor.close()

    for post in posts:
        post.update({'date': str(post['date'])})

    return jsonify(code=0, response=posts)


@user_API.route('updateProfile/', methods=['POST'])
def user_update_profile():
    user = request.json.get('user', None)
    about = request.json.get('about', None)
    name = request.json.get('name', None)

    cursor = db.cursor(MySQLdb.cursors.DictCursor)
    try:
        cursor.execute("""UPDATE `users` SET `about` = %s, `name` = %s WHERE `email` = %s;""", (about, name, user))
        db.commit()
    except MySQLdb.Error:
        db.rollback()

    user = queries.user_details(cursor, user)
    cursor.close()

    return jsonify(code=0, response=user)


@user_API.route('follow/', methods=['POST'])
def user_follow():
    follower = request.json.get('follower', None)
    followee = request.json.get('followee', None)

    cursor = db.cursor(MySQLdb.cursors.DictCursor)

    try:
        cursor.execute("""INSERT INTO `follower_followee` (`follower`, `followee`)
                          SELECT `u1`.`id`, `u2`.`id` FROM `users` AS `u1`
                          JOIN `users` AS `u2` ON `u1`.`email` = %s AND `u2`.`email` = %s;""", (follower, followee))

        db.commit()
    except MySQLdb.Error:
        db.rollback()

    user = queries.user_details(cursor, follower)
    cursor.close()

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

    query = """SELECT DISTINCT `u1`.* FROM `users` AS `u1`
            JOIN `follower_followee` AS `ff` ON `u1`.`id` = `ff`.`follower`
            JOIN `users` AS `u2` ON `ff`.`followee` = `u2`.`id`
            WHERE `u2`.`email` = %s """
    query_params = (user,)

    if since_id is not None:
        query += "AND `u1`.`id` >= %s "
        query_params += (int(since_id),)

    query += "ORDER BY `name` " + order + " "

    if limit is not None:
        query += "LIMIT %s;"
        query_params += (int(limit),)

    cursor = db.cursor(MySQLdb.cursors.DictCursor)
    cursor.execute(query, query_params)

    users = [i for i in cursor.fetchall()]

    for user in users:
        following = list_following(cursor, user['id'])
        followers = list_followers(cursor, user['id'])

        cursor.execute("""SELECT `thread` FROM `users_threads` WHERE `user` = %s;""", (user['email'],))
        threads = [i['thread'] for i in cursor.fetchall()]

        user.update({'following': following, 'followers': followers, 'subscriptions': threads})

    cursor.close()

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

    query = """SELECT DISTINCT `u1`.* FROM `users` AS `u1`
               JOIN `follower_followee` AS `ff` ON `u1`.`id` = `ff`.`followee`
               JOIN `users` AS `u2` ON `ff`.`follower` = `u2`.`id`
               WHERE `u2`.`email` = %s """
    query_params = (user,)

    if since_id is not None:
        query += "AND `u1`.`id` >= %s "
        query_params += (int(since_id),)

    query += "ORDER BY `name` " + order + " "

    if limit is not None:
        query += "LIMIT %s;"
        query_params += (int(limit),)

    cursor = db.cursor(MySQLdb.cursors.DictCursor)
    cursor.execute(query, query_params)

    users = [i for i in cursor.fetchall()]

    for user in users:
        following = list_following(cursor, user['id'])
        followers = list_followers(cursor, user['id'])

        cursor.execute("""SELECT `thread` FROM `users_threads` WHERE `user` = %s;""", (user['email'],))
        threads = [i['thread'] for i in cursor.fetchall()]

        user.update({'following': following, 'followers': followers, 'subscriptions': threads})

    cursor.close()
    return jsonify(code=0, response=users)


@user_API.route('unfollow/', methods=['POST'])
def user_unfollow():
    follower = request.json.get('follower', None)
    followee = request.json.get('followee', None)

    cursor = db.cursor(MySQLdb.cursors.DictCursor)
    try:
        cursor.execute("""SELECT `u1`.`id`, `u2`.`id` FROM `users` AS `u1`
                      INNER JOIN `users` AS `u2` ON `u1`.`email` = %s AND `u2`.`email` = %s;""", (follower, followee))
        f_er_id, f_ee_id = cursor.fetchone().values()

        cursor.execute("""DELETE FROM `follower_followee` WHERE `follower` = %s AND `followee` = %s;""",
                       (f_er_id, f_ee_id))
        db.commit()
    except MySQLdb.Error:
        db.rollback()

    user = queries.user_details(cursor, follower)
    cursor.close()
    return jsonify(code=0, response=user)