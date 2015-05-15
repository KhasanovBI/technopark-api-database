#!/bin/bash
gunicorn -c gunicorn.conf.py run_server:app
echo
