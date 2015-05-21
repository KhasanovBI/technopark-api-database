#!/usr/bin/python
from werkzeug.contrib.profiler import ProfilerMiddleware
from run_server import app

app.config['PROFILE'] = True
app.wsgi_app = ProfilerMiddleware(app.wsgi_app, restrictions = [30])
app.run(debug = True, port=4242)
