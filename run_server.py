# coding: utf-8
from flask import Flask
from views.general import general_API
from views.forum import forum_API
from views.post import post_API
from views.user import user_API
from views.thread import thread_API

app = Flask(__name__)

app.register_blueprint(general_API)
app.register_blueprint(forum_API)
app.register_blueprint(post_API)
app.register_blueprint(user_API)
app.register_blueprint(thread_API)

if __name__ == "__main__":
    app.run(port=4242)