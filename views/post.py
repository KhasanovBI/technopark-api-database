import MySQLdb
from flask import Blueprint, request, jsonify
from settings import BASE_URL, RESPONSE_CODES, get_connection
from utils import queries

post_API = Blueprint('post_API', __name__, url_prefix=BASE_URL + 'post/')


@post_API.route('create/', methods=['POST'])
def post_create():
    parent = request.json.get('parent', None)
    thread = request.json.get('thread', None)
    is_deleted = request.json.get('isDeleted', False)
    is_spam = request.json.get('isSpam', False)
    is_edited = request.json.get('isEdited', False)
    is_post_approved = request.json.get('isApproved', False)
    is_highlighted = request.json.get('isHighlighted', False)
    forum = request.json.get('forum', None)
    user = request.json.get('user', None)
    date = request.json.get('date', None)
    message = request.json.get('message', None)

    db = get_connection()
    cursor = db.cursor()

    post_id = 0
    try:
        cursor.execute(
            """INSERT INTO `posts`
            (`parent`, `thread`, `isDeleted`, `isSpam`, `isEdited`, `isApproved`, `isHighlighted`, `forum`,
             `user`, `date`, `message`)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s);""",
            (parent, thread, is_deleted, is_spam, is_edited, is_post_approved, is_highlighted, forum, user, date,
             message))

        post_id = cursor.lastrowid

        cursor.execute("""UPDATE `threads` SET `posts` = `posts` + 1 WHERE `id` = %s;""", (thread,))
        db.commit()

    except MySQLdb.Error:
        db.rollback()

    cursor.close()
    db.close()
    post = {
        "date": date,
        "forum": forum,
        "id": post_id,
        "isApproved": is_post_approved,
        "isDeleted": is_deleted,
        "isEdited": is_edited,
        "isHighlighted": is_highlighted,
        "isSpam": is_spam,
        "message": message,
        "parent": parent,
        "thread": thread,
        "user": user
    }
    return jsonify(code=0, response=post)


@post_API.route('details/')
def post_details():
    post_id = request.args.get('post', None)
    related = request.args.getlist('related')

    if post_id is None:
        code = 1
        return jsonify(code=code, response=RESPONSE_CODES[code])

    post_id = int(post_id)

    if post_id < 1:
        code = 1
        return jsonify(code=code, response=RESPONSE_CODES[code])

    db = get_connection()
    cursor = db.cursor(MySQLdb.cursors.DictCursor)

    post = queries.post_details(cursor, post_id)

    if 'user' in related:
        user = queries.user_details(cursor, post['user'])
        post.update({'user': user})

    if 'forum' in related:
        forum = queries.forum_details(cursor, post['forum'])
        post.update({'forum': forum})

    if 'thread' in related:
        thread = queries.thread_details(cursor, post['thread'])
        post.update({'thread': thread})

    cursor.close()
    db.close()
    return jsonify(code=0, response=post)


@post_API.route('list/')
def post_list():
    forum = request.args.get('forum', None)
    thread = request.args.get('thread', None)
    since = request.args.get('since')
    limit = request.args.get('limit')
    order = request.args.get('order', 'desc')

    if thread is None and forum is None:
        code = 1
        return jsonify(code=code, response=RESPONSE_CODES[code])

    if forum is not None:
        query = """SELECT * FROM `posts` WHERE `forum` = %s """
        query_params = (forum,)
    else:
        query = """SELECT * FROM `posts` WHERE `thread` = %s """
        query_params = (thread,)

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


@post_API.route('remove/', methods=['POST'])
def post_remove():
    post = request.json.get('post', None)
    post = int(post)

    db = get_connection()
    cursor = db.cursor(MySQLdb.cursors.DictCursor)

    try:
        cursor.execute("""UPDATE `threads` SET `posts` = `posts` - 1 WHERE `id` =
(SELECT `thread` FROM `posts` WHERE `id` = %s);""",
                       (post,))
        cursor.execute("""UPDATE `posts` SET `isDeleted` = TRUE WHERE `id` = %s;""", (post,))
        db.commit()
    except MySQLdb.Error:
        db.rollback()

    cursor.close()
    db.close()
    return jsonify(code=0, response={'post': post})


@post_API.route('restore/', methods=['POST'])
def post_restore():
    post = request.json.get('post', None)
    post = int(post)

    db = get_connection()
    cursor = db.cursor(MySQLdb.cursors.DictCursor)

    try:
        cursor.execute("""UPDATE `threads` SET `posts` = `posts` + 1 WHERE `id` =
(SELECT `thread` FROM `posts` WHERE `id` = %s);""",
                       (post,))
        cursor.execute("""UPDATE `posts` SET `isDeleted` = FALSE WHERE `id` = %s;""", (post,))

        db.commit()
    except MySQLdb.Error:
        db.rollback()

    cursor.close()
    db.close()
    return jsonify(code=0, response={'post': post})


@post_API.route('update/', methods=['POST'])
def post_update():
    message = request.json.get('message', None)
    post = request.json.get('post', None)
    post = int(post)

    db = get_connection()
    cursor = db.cursor(MySQLdb.cursors.DictCursor)

    try:
        cursor.execute("""UPDATE `posts` SET `message` = %s WHERE `id` = %s;""", (message, post))
        db.commit()

    except MySQLdb.Error:
        db.rollback()

    post = queries.post_details(cursor, post)
    cursor.close()
    db.close()
    return jsonify(code=0, response=post)


@post_API.route('vote/', methods=['POST'])
def post_vote():
    vote = request.json.get('vote', None)
    post = request.json.get('post', None)
    post = int(post)

    db = get_connection()
    cursor = db.cursor(MySQLdb.cursors.DictCursor)

    try:
        if vote == 1:
            cursor.execute("""UPDATE `posts` SET `likes` = `likes` + 1, `points` = `points` + 1 WHERE `id` = %s;""",
                           (post,))
        else:
            cursor.execute(
                """UPDATE `posts` SET `dislikes` = `dislikes` + 1, `points` = `points` - 1 WHERE `id` = %s;""", (post,))
        db.commit()

    except MySQLdb.Error:
        db.rollback()

    post = queries.post_details(cursor, post)

    cursor.close()
    db.close()
    return jsonify(code=0, response=post)