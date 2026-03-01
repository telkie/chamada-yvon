from flask import session
from flask_socketio import emit
from services.google_manager import google_service
import datetime

def register_socket_events(socketio):
    
    @socketio.on('selecionar_turma')
    def handle_selecao(data):
        turma = data.get('turma')
        modo = data.get('modo')
        
        if 'turmas' in session and turma in session['turmas']:
            alunos = google_service.obter_alunos(turma)
            emit('dados_turma', {
                'alunos': alunos,
                'turma_nome': turma,
                'modo': modo,
                'data_default': datetime.date.today().strftime("%Y-%m-%d")
            })

    @socketio.on('buscar_presenca_anterior')
    def handle_busca_anterior(data):
        turma = data.get('turma')
        dt = data.get('data')
        presentes = google_service.recuperar_presenca(turma, dt)
        emit('presenca_anterior_carregada', {'presentes': presentes})

    @socketio.on('registrar_chamada')
    def handle_chamada(data):
        if 'usuario' not in session: return
        
        sucesso, msg = google_service.salvar_chamada(
            data['turma_atual'], 
            data['data'], 
            data.get('presentes', []), 
            data['tipo']
        )
        if sucesso: emit('sucesso', {'msg': msg})
        else: emit('erro', {'msg': msg})

    # --- EDIÇÃO DE CADASTRO ---
    
    @socketio.on('solicitar_dados_aluno')
    def handle_get_aluno(data):
        sucesso, resposta = google_service.buscar_dados_aluno(data.get('nome'))
        if sucesso:
            emit('dados_aluno_recebidos', resposta)
        else:
            emit('erro', {'msg': resposta})

    @socketio.on('salvar_edicao_cadastro')
    def handle_save_cadastro(data):
        sucesso, msg = google_service.atualizar_cadastro(data['row_id'], data['dados'])
        if sucesso: emit('sucesso_edicao', {'msg': msg})
        else: emit('erro', {'msg': msg})