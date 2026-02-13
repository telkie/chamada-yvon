import os
import datetime
import socket
import requests
from flask import Flask, render_template, request, session, redirect, url_for
from flask_socketio import SocketIO, emit
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
app.config['SECRET_KEY'] = 'segredo_yvon_2026_v4'
app.config['SESSION_PERMANENT'] = True 
app.config['PERMANENT_SESSION_LIFETIME'] = datetime.timedelta(days=30)

socketio = SocketIO(app, cors_allowed_origins="*", host='0.0.0.0', manage_session=False)

# --- CONFIGURAÇÕES ---
CREDS_FILE = "credentials.json"
ID_BANCO_DADOS = "1qJsrj_-vAqC1oIb-YrN0VPMdnFbeki88_xvXwEci7xg"
ID_CADASTRO = "17njX9mxmQj8ikhgve6LRVXVLOuahYp2NQoi69gmFQo8"
WEBHOOK_URL = "https://script.google.com/macros/s/AKfycbyDlq9uHRlYEYvNnAkbkQmbujsY6NA5BH0FoRuMpNY4Il7b5829eqJdaG8B9xywy-4D/exec"

GLOBAL_CLIENT = None

def get_client():
    global GLOBAL_CLIENT
    if GLOBAL_CLIENT is None:
        scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
        creds = ServiceAccountCredentials.from_json_keyfile_name(CREDS_FILE, scope)
        GLOBAL_CLIENT = gspread.authorize(creds)
    return GLOBAL_CLIENT

def carregar_mapa_ids():
    try:
        client = get_client()
        sh = client.open_by_key(ID_CADASTRO)
        ws = sh.worksheet("Alunos ativos")
        records = ws.get_all_records()
        mapa = {}
        for row in records:
            # Tenta pegar ID e Nome removendo espaços extras
            uid = str(row.get('ID_Aluno', '')).strip()
            nome = str(row.get('Nome completo', '')).strip()
            if uid and nome:
                mapa[uid] = nome
        return mapa
    except Exception as e:
        print(f"Erro ao carregar mapa de IDs: {e}")
        return {}

def obter_alunos_realtime(nome_turma):
    print(f"☁️ Baixando lista fresca da {nome_turma}...")
    try:
        client = get_client()
        sh = client.open_by_key(ID_BANCO_DADOS)
        ws = sh.worksheet(nome_turma)
        nomes = ws.col_values(1)[1:] 
        return [n for n in nomes if n]
    except Exception as e:
        print(f"Erro ao ler {nome_turma}: {e}")
        return []

# --- ROTAS ---
@app.route('/', methods=['GET', 'POST'])
def index():
    if 'usuario' not in session: return render_template('login.html')
    return render_template('index.html', usuario=session['usuario'], turmas=session['turmas'])

@app.route('/login', methods=['POST'])
def login():
    usuario = request.form.get('login')
    senha = request.form.get('senha')
    try:
        client = get_client()
        ws_users = client.open_by_key(ID_BANCO_DADOS).worksheet("Evangelizadores")
        records = ws_users.get_all_records()
        for row in records:
            if str(row['Login']) == usuario and str(row['Senha']) == senha:
                session['usuario'] = usuario
                session['turmas'] = [t.strip() for t in str(row['Turma']).split(',') if t.strip()]
                return redirect(url_for('index'))
    except Exception as e:
        print(f"Erro login: {e}")
    return render_template('login.html', erro="Login incorreto!")

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('index'))

# --- SOCKETS ---
@socketio.on('selecionar_turma')
def handle_selecao(data):
    nome_turma = data.get('turma')
    if 'turmas' in session and nome_turma in session['turmas']:
        alunos = obter_alunos_realtime(nome_turma)
        mapa_ids = carregar_mapa_ids()
        emit('dados_turma', {
            'alunos': alunos,
            'mapa_ids': mapa_ids, 
            'turma_nome': nome_turma,
            'data_default': datetime.date.today().strftime("%Y-%m-%d")
        })
    else:
        emit('erro', {'msg': 'Acesso negado.'})

@socketio.on('registrar_chamada')
def handle_chamada(payload):
    if 'usuario' not in session: return
    turma = payload.get('turma_atual')
    data_sel = payload.get('data')
    
    # VALIDAÇÃO DE SÁBADO
    try:
        dt_obj = datetime.datetime.strptime(data_sel, "%Y-%m-%d")
        if dt_obj.weekday() != 5: # 5 = Sábado
            emit('erro', {'msg': '🚫 Apenas sábados são permitidos!'})
            return
    except:
        emit('erro', {'msg': 'Data inválida!'}); return

    try:
        client = get_client()
        sh = client.open_by_key(ID_BANCO_DADOS)
        ws_log = sh.worksheet("Log_Chamada")
        dt_fmt = dt_obj.strftime("%d/%m/%Y")
        
        todos_alunos = obter_alunos_realtime(turma)
        linhas = []

        if payload['tipo'] == 'sem_aula':
            for aluno in todos_alunos:
                linhas.append([f"{turma}-{aluno}-{dt_fmt}", dt_fmt, turma, aluno, "SA", ""])
        elif payload['tipo'] == 'presenca':
            presentes = set(payload['presentes'])
            for aluno in todos_alunos:
                 linhas.append([f"{turma}-{aluno}-{dt_fmt}-F", dt_fmt, turma, aluno, "F", ""])
            for aluno in presentes:
                 linhas.append([f"{turma}-{aluno}-{dt_fmt}-P", dt_fmt, turma, aluno, "P", ""])

        if linhas:
            ws_log.append_rows(linhas)
            try: requests.get(WEBHOOK_URL + "?p=1", timeout=1)
            except: pass
            emit('sucesso', {'msg': '✅ Chamada salva!'})
            
    except Exception as e:
        GLOBAL_CLIENT = None 
        emit('erro', {'msg': f'Erro: {str(e)}'})

if __name__ == '__main__':
    socketio.run(app, debug=True, host='0.0.0.0', port=5000)