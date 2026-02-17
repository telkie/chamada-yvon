from flask import Blueprint, render_template, request, redirect, url_for, session, jsonify
from services.google_manager import google_service
from config import Config
import requests

main_bp = Blueprint('main', __name__)

@main_bp.route('/', methods=['GET', 'POST'])
def index():
    if 'usuario' not in session:
        return render_template('login.html')
    return render_template('index.html', usuario=session['usuario'], turmas=session['turmas'])

@main_bp.route('/login', methods=['POST'])
def login():
    usuario = request.form.get('login')
    senha = request.form.get('senha')
    
    turmas = google_service.validar_login(usuario, senha)
    
    if turmas:
        session['usuario'] = usuario
        session['turmas'] = turmas
        return redirect(url_for('main.index'))
    
    return render_template('login.html', erro="Login incorreto!")

@main_bp.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('main.index'))

@main_bp.route('/cadastro_rapido', methods=['POST'])
def cadastro_rapido():
    if 'usuario' not in session: 
        return jsonify({'erro': 'Não logado'}), 403
        
    dados = request.json
    nome = dados.get('nome')
    turma = dados.get('turma')
    
    # 1. Mapeamento dos IDs do Novo Formulário
    # Preenchemos campos vazios com "." para evitar erro de "Campo Obrigatório"
    form_data = {
        "entry.1091823087": nome,               # Nome
        "entry.883252145": turma,               # Turma
        "entry.477279343": "2026-01-01",        # Nascimento (Placeholder)
        "entry.2141494783": ".",                # Contato Evan (Placeholder)
        "entry.146137968": ".",                 # Nome Resp (Placeholder)
        "entry.2118960068": "."                 # Contato Resp (Placeholder)
    }
    
    try:
        # 2. Envia para o Google Forms
        requests.post(Config.FORM_URL, data=form_data)
        
        # 3. ACIONA O WEBHOOK PARA SINCRONIZAR NA HORA! ⚡
        # Timeout de 5s para não travar o site caso o script demore
        try:
            requests.post(Config.SYNC_WEBHOOK_URL, timeout=5)
        except:
            pass # Se der timeout, vida que segue, o Forms já salvou.

        return jsonify({'msg': 'Cadastro realizado e sincronizado com sucesso!'})
        
    except Exception as e:
        return jsonify({'erro': str(e)}), 500