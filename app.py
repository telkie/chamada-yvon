from flask import Flask
from flask_socketio import SocketIO
from config import Config
import datetime
import os
import time

# Inicialização do App
app = Flask(__name__)
app.config.from_object(Config)
app.config['SESSION_PERMANENT'] = True
app.config['PERMANENT_SESSION_LIFETIME'] = datetime.timedelta(days=30)

socketio = SocketIO(app, cors_allowed_origins="*", host='0.0.0.0', manage_session=False)

# --- IMPORTAÇÃO DOS MÓDULOS ---
# Importamos aqui para evitar "Circular Import"
from routes.main_routes import main_bp
from events.socket_events import register_socket_events

os.environ['TZ'] = 'America/Sao_Paulo'
try:
    time.tzset() # Funciona em Linux/Mac (Servidores)
except AttributeError:
    pass # Ignora no Windows (lá pega o do sistema)

# Registra as Rotas
app.register_blueprint(main_bp)

# Registra os Eventos de Socket
register_socket_events(socketio)

if __name__ == '__main__':
    print("🌳 Sistema Yvon Modularizado Iniciado!")
    # Mudamos o host, desligamos o reloader e permitimos o werkzeug
    socketio.run(app, host='127.0.0.1', port=5000, debug=True, use_reloader=False, allow_unsafe_werkzeug=True)