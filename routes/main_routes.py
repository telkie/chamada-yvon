from flask import Blueprint, render_template, request, redirect, url_for, session, jsonify
from services.google_manager import google_service
from config import Config
import requests

main_bp = Blueprint('main', __name__)

# Mapeamento de Links para o botão "Banco de Dados"
# Admin vê o original, turmas veem suas planilhas individuais (Visualização)
LINKS_BANCO_DADOS = {
    "Admin": "https://docs.google.com/spreadsheets/d/1qJsrj_-vAqC1oIb-YrN0VPMdnFbeki88_xvXwEci7xg/edit", # Planilha Mestre
    "Bebês (0 a 2)": "https://docs.google.com/spreadsheets/d/1kzRXpwDkKJdIGfm5iHBAIn4btn2y5G_xUWB4b_gqjGs/edit",
    "Maternal (3 e 4)": "https://docs.google.com/spreadsheets/d/14lokWrqkCNCUZoDCy7rauADIvjbI75H2xH8yYCLlfVo/edit",
    "Jardim (5 e 6)": "https://docs.google.com/spreadsheets/d/11kyhJQECwO-sdlz7gu40oQh1TQHIgjXUDlhEelj2Wlk/edit",
    "1° Ciclo (7 e 8)": "https://docs.google.com/spreadsheets/d/1oiNDX0DmVU6ZV-HGg7D10uMY-IcPniNNoZvWxs8hpHI/edit",
    "2° Ciclo (9 e 10)": "https://docs.google.com/spreadsheets/d/1psPfh2g21XtDynTyOqosY8hkCg2wSFnMyumNAzWAoTU/edit",
    "3° Ciclo (11 e 12)": "https://docs.google.com/spreadsheets/d/1AsfH6JpzNF_Mmh87vcxVSlKQ87Fh3d3AjyJ8Tz0HBpc/edit",
    "Pré-juventude (13 e 14)": "https://docs.google.com/spreadsheets/d/1Zz-2Z1Vf2XTgYoVvdjRV_UySP5pljq-CNpvfQuzSaFM/edit",
    "Juventude (15+)": "https://docs.google.com/spreadsheets/d/1tYwlQydWhUyZvS_Rek1SqG9jAa5-F3FUhaOcc_dHf8M/edit"
}

@main_bp.route('/', methods=['GET', 'POST'])
def index():
    if 'usuario' not in session:
        return render_template('login.html')
    
    usuario = session['usuario']
    turmas = session['turmas']
    
    # Lógica para definir qual link de Banco de Dados exibir
    link_db = "#"
    if usuario == "Admin":
        link_db = LINKS_BANCO_DADOS["Admin"]
    elif turmas:
        # Pega a primeira turma da lista do usuário.
        # Se um usuário tiver várias turmas, ele vai para a planilha da primeira.
        # (Futuramente poderia ser um modal para escolher, mas por enquanto simplificamos)
        turma_principal = turmas[0]
        if turma_principal in LINKS_BANCO_DADOS:
            link_db = LINKS_BANCO_DADOS[turma_principal]

    return render_template('index.html', usuario=usuario, turmas=turmas, link_db=link_db)

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

# --- NOVO: Rota para buscar detalhes da ficha do aluno ---
@main_bp.route('/ficha_aluno', methods=['POST'])
def ficha_aluno():
    if 'usuario' not in session:
        return jsonify({'erro': 'Não autorizado'}), 403
        
    dados = request.json
    turma = dados.get('turma')
    nome = dados.get('nome')
    
    ficha = google_service.obter_ficha_aluno(turma, nome)
    
    if ficha:
        return jsonify(ficha)
    return jsonify({'erro': 'Aluno não encontrado no Banco de Dados.'}), 404

# --- Cadastro Rápido com Webhook (Mantido) ---
@main_bp.route('/cadastro_rapido', methods=['POST'])
def cadastro_rapido():
    if 'usuario' not in session: 
        return jsonify({'erro': 'Não logado'}), 403
        
    dados = request.json
    nome = dados.get('nome')
    turma = dados.get('turma')
    
    # Preenchimento para o Google Forms
    form_data = {
        "entry.1091823087": nome,               # Nome
        "entry.883252145": turma,               # Turma
        "entry.477279343": "2026-01-01",        # Nascimento (Placeholder)
        "entry.2141494783": ".",                # Contato Evan (Placeholder)
        "entry.146137968": ".",                 # Nome Resp (Placeholder)
        "entry.2118960068": "."                 # Contato Resp (Placeholder)
    }
    
    try:
        # 1. Envia para o Forms
        requests.post(Config.FORM_URL, data=form_data)
        
        # 2. Aciona o Webhook de Sincronização
        try:
            requests.post(Config.SYNC_WEBHOOK_URL, timeout=5)
        except:
            pass # Ignora timeout do webhook

        return jsonify({'msg': 'Cadastro realizado e sincronizado com sucesso!'})
        
    except Exception as e:
        return jsonify({'erro': str(e)}), 500