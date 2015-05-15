from settings import sqlSchema, request_db


def list_following(cursor, user_id):
    cursor.execute("""SELECT `u1`.`email` FROM `users` AS `u1` IGNORE INDEX (`PRIMARY`)
                      INNER JOIN `follower_followee` AS `ff` ON `u1`.`id` = `ff`.`followee`
                      WHERE `ff`.`follower` = %s;""", (user_id,))
    z = cursor.fetchall()
    following = [i['email'] for i in z]

    return following


def list_followers(cursor, user_id):
    cursor.execute("""SELECT `u1`.`email` FROM `users` AS `u1` IGNORE INDEX (`PRIMARY`)
                      INNER JOIN `follower_followee` AS `ff` ON `u1`.`id` = `ff`.`follower`
                      WHERE `ff`.`followee` = %s;""", (user_id,))
    followers = [i['email'] for i in cursor.fetchall()]

    return followers


def user_details(cursor, email):
    cursor.execute("""SELECT * FROM `users` WHERE `email` = %s;""", (email,))
    user = cursor.fetchone()

    if user is None:
        return None

    following = list_following(cursor, user['id'])
    followers = list_followers(cursor, user['id'])

    cursor.execute("""SELECT `thread` FROM `users_threads` WHERE `user` = %s;""", (email,))
    threads = [i['thread'] for i in cursor.fetchall()]

    user.update({'following': following, 'followers': followers, 'subscriptions': threads})
    return user


def forum_details(cursor, short_name):
    cursor.execute("""SELECT * FROM `forums` WHERE `short_name` = %s;""", (short_name,))
    forum = cursor.fetchone()
    return forum


def thread_details(cursor, thread_id):
    cursor.execute("""SELECT * FROM `threads` WHERE `id` = %s;""", (thread_id,))
    thread = cursor.fetchone()

    if thread is None:
        return None

    thread.update({'date': str(thread['date'])})
    return thread


def post_details(cursor, post_id):
    cursor.execute("""SELECT * FROM `posts` WHERE `id` = %s;""", (post_id,))
    post = cursor.fetchone()

    if post is None:
        return None

    post.update({'date': str(post['date'])})
    return post


def init_tables():
    query = ''
    db = request_db()
    cursor = db.cursor()
    f = open(sqlSchema, 'r')
    for line in f:
        query += line
        if ';' in line:
            cursor.execute(query)
            db.commit()
            query = ''
    f.close()
    cursor.close()
    db.close()