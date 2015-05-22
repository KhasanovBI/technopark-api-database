import MySQLdb
from flask import Blueprint, request
from settings import BASE_URL, RESPONSE_CODES
from utils import queries
from utils.helper import jsonify, get_connection


thread_API = Blueprint('thread_API', __name__, url_prefix=BASE_URL + 'thread/')


@thread_API.route('create/', methods=['POST'])
def thread_create():
    is_deleted = request.json.get('isDeleted', False)
    forum = request.json.get('forum', None)
    title = request.json.get('title', None)
    is_closed = request.json.get('isClosed', False)
    user = request.json.get('user', None)
    date = request.json.get('date', None)
    message = request.json.get('message', None)
    slug = request.json.get('slug', None)

    thread_id = 0

    db = get_connection()
    cursor = db.cursor()
    try:
        cursor.execute("""INSERT INTO `threads`
                          (`isDeleted`, `forum`, `title`, `isClosed`, `user`, `date`, `message`, `slug`)
                          VALUES (%s, %s, %s, %s, %s, %s, %s, %s);""",
                       (is_deleted, forum, title, is_closed, user, date, message, slug))

        thread_id = cursor.lastrowid

        db.commit()

    except MySQLdb.Error:
        db.rollback()

    cursor.close()
    db.close()

    thread = {
        "date": date,
        "forum": forum,
        "id": thread_id,
        "isClosed": is_closed,
        "isDeleted": is_deleted,
        "message": message,
        "slug": slug,
        "title": title,
        "user": user
    }
    return jsonify(code=0, response=thread)


@thread_API.route('details/')
def thread_details():
    thread_id = request.args.get('thread', None)
    related = request.args.getlist('related')
    thread_id = int(thread_id)

    if 'thread' in related:
        code = 3
        return jsonify(code=code, response=RESPONSE_CODES[code])

    if thread_id is None or thread_id < 1:
        code = 1
        return jsonify(code=code, response=RESPONSE_CODES[code])

    db = get_connection()
    cursor = db.cursor(MySQLdb.cursors.DictCursor)

    thread = queries.thread_details(cursor, thread_id)

    if 'user' in related:
        user = queries.user_details(cursor, thread['user'])
        thread.update({'user': user})

    if 'forum' in related:
        forum = queries.forum_details(cursor, thread['forum'])
        thread.update({'forum': forum})

    cursor.close()
    db.close()
    return jsonify(code=0, response=thread)


@thread_API.route('list/')
def thread_list():
    forum = request.args.get('forum', None)
    user = request.args.get('user', None)
    since = request.args.get('since')
    limit = request.args.get('limit')
    order = request.args.get('order', 'desc')

    if user is None and forum is None:
        code = 1
        return jsonify(code=code, response=RESPONSE_CODES[code])

    if forum is not None:
        query = """SELECT * FROM `threads` WHERE `forum` = %s """
        query_params = (forum,)
    else:
        query = """SELECT * FROM `threads` WHERE `user` = %s """
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

    threads = [i for i in cursor.fetchall()]

    for thread in threads:
        thread.update({'date': str(thread['date'])})

    cursor.close()
    db.close()
    return jsonify(code=0, response=threads)


@thread_API.route('listPosts/')
def thread_list_posts():
    thread = request.args.get('thread', None)
    since = request.args.get('since')
    limit = request.args.get('limit')
    order = request.args.get('order')

    if thread is None:
        code = 1
        return jsonify(code=code, response=RESPONSE_CODES[code])

    query = """SELECT * FROM `posts` WHERE `thread` = %s """
    query_params = (int(thread),)

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
        post.update({'date': str(post['date'])})

    cursor.close()
    db.close()
    return jsonify(code=0, response=posts)


@thread_API.route('remove/', methods=['POST'])
def thread_remove():
    thread = request.json.get('thread')
    thread = int(thread)

    db = get_connection()
    cursor = db.cursor()

    try:
        cursor.execute("""UPDATE `threads` SET `isDeleted` = TRUE, `posts` = 0 WHERE `id` = %s;""", (thread,))
        cursor.execute("""UPDATE `posts` SET `isDeleted` = TRUE WHERE `thread` = %s;""", (thread,))
        db.commit()

    except MySQLdb.Error:
        db.rollback()

    cursor.close()
    db.close()
    return jsonify(code=0, response={'thread': thread})


@thread_API.route('restore/', methods=['POST'])
def thread_restore():
    thread = request.json.get('thread', None)
    thread = int(thread)

    db = get_connection()
    cursor = db.cursor()
    try:
        count = cursor.execute("""UPDATE `posts` SET `isDeleted` = FALSE WHERE `thread` = %s;""", (thread,))
        cursor.execute("""UPDATE `threads` SET `isDeleted` = FALSE, `posts` = %s WHERE `id` = %s;""",
                       (count, thread))
        db.commit()
    except MySQLdb.Error:
        db.rollback()

    cursor.close()
    db.close()
    return jsonify(code=0, response={'thread': thread})


@thread_API.route('close/', methods=['POST'])
def thread_close():
    thread = request.json.get('thread', None)
    thread = int(thread)

    db = get_connection()
    cursor = db.cursor()
    try:
        cursor.execute("""UPDATE `threads` SET `isClosed` = TRUE WHERE `id` = %s;""", (thread,))
        db.commit()
    except MySQLdb.Error:
        db.rollback()

    cursor.close()
    db.close()
    return jsonify(code=0, response={'thread': thread})


@thread_API.route('open/', methods=['POST'])
def thread_open():
    thread = request.json.get('thread', None)
    thread = int(thread)

    db = get_connection()
    cursor = db.cursor()
    try:
        cursor.execute("""UPDATE `threads` SET `isClosed` = FALSE WHERE `id` = %s;""", (thread,))
        db.commit()
    except MySQLdb.Error:
        db.rollback()

    cursor.close()
    db.close()
    return jsonify(code=0, response={'thread': thread})


@thread_API.route('update/', methods=['POST'])
def thread_update():
    message = request.json.get('message', None)
    slug = request.json.get('slug', None)
    thread = request.json.get('thread', None)
    thread = int(thread)

    db = get_connection()
    cursor = db.cursor(MySQLdb.cursors.DictCursor)
    try:
        cursor.execute("""UPDATE `threads` SET `message` = %s, `slug` = %s WHERE `id` = %s;""",
                       (message, slug, thread))
        db.commit()
    except MySQLdb.Error:
        db.rollback()

    thread = queries.thread_details(cursor, thread)

    cursor.close()
    db.close()
    return jsonify(code=0, response={'thread': thread})


@thread_API.route('vote/', methods=['POST'])
def thread_vote():
    vote = request.json.get('vote', None)
    thread = request.json.get('thread', None)
    thread = int(thread)

    db = get_connection()
    cursor = db.cursor(MySQLdb.cursors.DictCursor)
    try:
        if vote == 1:
            cursor.execute("""UPDATE `threads` SET `likes` = `likes` + 1, `points` = `points` + 1 WHERE `id` = %s;""",
                           (thread,))
        else:
            cursor.execute(
                """UPDATE `threads` SET `dislikes` = `dislikes` + 1, `points` = `points` - 1 WHERE `id` = %s;""",
                (thread,))
        db.commit()

    except MySQLdb.Error:
        db.rollback()

    thread = queries.thread_details(cursor, thread)

    cursor.close()
    db.close()
    return jsonify(code=0, response=thread)


@thread_API.route('subscribe/', methods=['POST'])
def thread_subscribe():
    user = request.json.get('user', None)
    thread = request.json.get('thread', None)

    db = get_connection()
    cursor = db.cursor()

    try:
        cursor.execute("""INSERT INTO `users_threads` (`user`, `thread`) VALUES (%s, %s);""",
                       (user, thread))
        db.commit()
    except MySQLdb.Error:
        db.rollback()

    cursor.close()
    db.close()
    return jsonify(code=0, response={'thread': thread, 'user': user})


@thread_API.route('unsubscribe/', methods=['POST'])
def thread_unsubscribe():
    user = request.json.get('user', None)
    thread = request.json.get('thread', None)

    db = get_connection()
    cursor = db.cursor()

    try:
        cursor.execute("""DELETE FROM `users_threads` WHERE `user` = %s AND `thread` = %s;""", (user, thread))
        db.commit()
    except MySQLdb.Error:
        db.rollback()

    cursor.close()
    db.close()
    return jsonify(code=0, response={'thread': thread, 'user': user})