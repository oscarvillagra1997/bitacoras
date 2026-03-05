import eventlet
eventlet.monkey_patch()

from app import app, socketio  # noqa: F401

# Gunicorn necesita un callable WSGI llamado "app"
# Flask-SocketIO detectará eventlet y habilitará WebSocket/long-polling según correspond