# run.py
from app import app, socketio

if __name__ == "__main__":
    socketio.run(
        app,
        host="0.0.0.0",   # 👈 acepta conexiones desde otras máquinas
        port=5000,        # o el puerto que quieras
        debug=True,
        allow_unsafe_werkzeug=True  # IMPORTANTE EN WINDOWS
    )
