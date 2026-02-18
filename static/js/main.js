/* static/js/main.js */

const socket = io();
let modoAtual = ""; 
let alunosData = [];
let selecionados = new Set();
let turmaAtual = "";

// --- NAVEGAÇÃO ---
function irPara(viewId) {
    document.querySelectorAll('.view-section').forEach(el => el.classList.remove('view-active'));
    document.getElementById('view-' + viewId).classList.add('view-active');
}

// --- MODO CHAMADA ---
function modoFazerChamada() {
    modoAtual = 'chamada';
    selecionados.clear();
    document.getElementById('titulo-chamada').innerText = "Nova Chamada";
    document.getElementById('btn-buscar-presenca').style.display = 'none';
    document.getElementById('data-picker').value = new Date().toISOString().split('T')[0];
    
    // Auto-load se já tiver turma selecionada
    const turmaSelecionada = document.getElementById('select-turma').value;
    if (turmaSelecionada) {
        carregarTurma();
    } else {
        document.getElementById('lista-alunos-container').innerHTML = '<div class="text-center text-muted mt-5">Selecione a turma acima.</div>';
    }
    
    irPara('chamada');
}

function modoEditarChamada() {
    modoAtual = 'edicao_presenca';
    selecionados.clear();
    document.getElementById('titulo-chamada').innerText = "Editar Presença";
    document.getElementById('btn-buscar-presenca').style.display = 'block';
    document.getElementById('lista-alunos-container').style.display = 'none';
    irPara('chamada');
}

function modoEditarCadastro() {
    modoAtual = 'editar_cadastro';
    irPara('editar-cadastro-lista');
}

// --- LÓGICA DE TURMA (SOCKET) ---
function carregarTurmaManual() {
    const t = document.getElementById('select-turma').value;
    if(!t) return alert("Selecione uma turma primeiro!");
    
    document.getElementById('lista-alunos-container').innerHTML = '<div class="text-center mt-5 text-warning">Forçando atualização... <i class="fas fa-sync fa-spin"></i></div>';
    
    setTimeout(() => {
        socket.emit('selecionar_turma', { turma: t, modo: modoAtual });
    }, 500);
}

function carregarTurma() {
    const t = document.getElementById('select-turma').value;
    turmaAtual = t;
    if (modoAtual === 'chamada') {
        document.getElementById('lista-alunos-container').style.display = 'block';
        document.getElementById('lista-alunos-container').innerHTML = '<div class="text-center mt-5">Carregando... <i class="fas fa-circle-notch fa-spin"></i></div>';
        socket.emit('selecionar_turma', { turma: t, modo: modoAtual });
    } else {
        document.getElementById('lista-alunos-container').style.display = 'none';
    }
}

function carregarTurmaParaEdicaoCad() {
    const t = document.getElementById('select-turma-edit-cad').value;
    document.getElementById('lista-alunos-edicao').innerHTML = '<div class="text-center mt-5">Carregando...</div>';
    socket.emit('selecionar_turma', { turma: t, modo: 'editar_cadastro' });
}

// --- NOVA FUNÇÃO: Carregar lista para Fichas ---
function carregarAlunosParaFicha() {
    const t = document.getElementById('select-turma-ficha').value;
    document.getElementById('container-lista-fichas').innerHTML = '<div class="text-center mt-3 text-muted">Carregando... <i class="fas fa-spinner fa-spin"></i></div>';
    
    // Usa o mesmo socket, mas com modo diferente
    socket.emit('selecionar_turma', { turma: t, modo: 'visualizar_fichas' });
}

// --- RECEPTOR DE DADOS DO SOCKET ---
socket.on('dados_turma', (data) => {
    alunosData = data.alunos;
    
    if (data.modo === 'visualizar_fichas') {
        // Renderiza lista para Fichas
        const container = document.getElementById('container-lista-fichas');
        container.innerHTML = '';
        if(alunosData.length === 0) {
            container.innerHTML = '<div class="text-center text-muted">Nenhum evangelizando encontrado.</div>';
            return;
        }
        alunosData.forEach(nome => {
            const btn = document.createElement('button');
            btn.className = 'btn btn-dark border-secondary text-start p-3 text-white mb-2 w-100';
            btn.innerHTML = `<i class="fas fa-user text-primary me-2"></i> ${nome}`;
            btn.onclick = () => abrirFicha(nome);
            container.appendChild(btn);
        });

    } else if (data.modo === 'editar_cadastro') {
        // Renderiza lista para Edição
        const container = document.getElementById('lista-alunos-edicao');
        container.innerHTML = '';
        alunosData.forEach(nome => {
            const div = document.createElement('div');
            div.className = 'aluno-card';
            div.innerHTML = `<span>${nome}</span><i class="fas fa-pencil-alt edit-icon"></i>`;
            div.onclick = () => abrirModalEdicao(nome);
            container.appendChild(div);
        });

    } else {
        // Renderiza lista para Chamada
        selecionados.clear();
        renderizarListaPresenca();
    }
});

function renderizarListaPresenca() {
    const container = document.getElementById('lista-alunos-container');
    container.innerHTML = '';
    alunosData.forEach(nome => {
        const isSelected = selecionados.has(nome);
        const div = document.createElement('div');
        div.className = `aluno-card ${isSelected ? 'selected' : ''}`;
        div.onclick = () => {
            if (selecionados.has(nome)) selecionados.delete(nome); else selecionados.add(nome);
            renderizarListaPresenca();
        };
        div.innerHTML = `<span>${nome}</span><i class="fas fa-check check-icon"></i>`;
        container.appendChild(div);
    });
}

// --- BUSCAR PRESENÇA (Anterior) ---
function buscarPresencaAnterior() {
    const dt = document.getElementById('data-picker').value;
    if(!turmaAtual) return alert("Selecione a turma");
    document.getElementById('loading').style.display = 'flex';
    socket.emit('selecionar_turma', { turma: turmaAtual, modo: 'chamada' }); 
    setTimeout(() => {
        socket.emit('buscar_presenca_anterior', { turma: turmaAtual, data: dt });
    }, 500);
}

socket.on('presenca_anterior_carregada', (data) => {
    document.getElementById('loading').style.display = 'none';
    document.getElementById('lista-alunos-container').style.display = 'block';
    selecionados = new Set(data.presentes);
    renderizarListaPresenca();
});

// --- ENVIAR PRESENÇA ---
function enviarPresenca() {
    if(!turmaAtual) return alert("Selecione a turma");
    const dt = document.getElementById('data-picker').value;

    // Validação de Sábado
    const dataObj = new Date(dt + 'T12:00:00');
    if (dataObj.getDay() !== 6) {
        alert("🚫 Erro: A chamada só pode ser enviada aos Sábados!");
        return;
    }

    if(!confirm(`Confirmar envio?`)) return;
    document.getElementById('loading').style.display = 'flex';
    socket.emit('registrar_chamada', { tipo: 'presenca', turma_atual: turmaAtual, data: dt, presentes: Array.from(selecionados) });
}

socket.on('sucesso', (msg) => {
    document.getElementById('loading').style.display = 'none';
    alert(msg.msg);
    if(modoAtual === 'chamada') irPara('menu'); 
});

// --- CADASTRO RÁPIDO ---
function salvarCadastroRapido() {
    const nome = document.getElementById('cad-nome').value;
    const turma = document.getElementById('cad-turma').value;
    if(!nome) return alert("Digite o nome");
    
    document.getElementById('loading').style.display = 'flex';
    
    // Feedback visual
    const btnSalvar = document.querySelector('#view-cadastro-rapido button');
    const textoOriginal = btnSalvar.innerText;
    btnSalvar.innerText = "Sincronizando...";
    btnSalvar.disabled = true;

    fetch('/cadastro_rapido', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({ nome: nome, turma: turma })
    })
    .then(res => res.json())
    .then(data => {
        document.getElementById('loading').style.display = 'none';
        btnSalvar.innerText = textoOriginal;
        btnSalvar.disabled = false;

        if(data.erro) {
            alert("Erro: " + data.erro);
        } else {
            alert("✅ Cadastrado e Sincronizado!");
            document.getElementById('cad-nome').value = "";
        }
    });
}

// --- EDITAR CADASTRO (CRUD COM NOVOS CAMPOS) ---
function abrirModalEdicao(nome) {
    document.getElementById('loading').style.display = 'flex';
    // Precisamos enviar a turma para buscar a obs do evangelizador na planilha certa
    const turma = document.getElementById('select-turma-edit-cad').value;
    socket.emit('solicitar_dados_aluno', { nome: nome, turma_contexto: turma });
}

socket.on('dados_aluno_recebidos', (dados) => {
    document.getElementById('loading').style.display = 'none';
    // Mostra o modal (agora usando display flex ou block conforme css do modal-custom)
    document.getElementById('modal-editar').style.display = 'flex';
    
    document.getElementById('edit-row-id').value = dados.row_id;
    document.getElementById('edit-nome').value = dados.nome;
    document.getElementById('edit-nasc').value = dados.nasc;
    document.getElementById('edit-contato-aluno').value = dados.contato_aluno || "";
    document.getElementById('edit-resp').value = dados.responsavel;
    document.getElementById('edit-contato-resp').value = dados.contato_resp;
    document.getElementById('edit-turma').value = dados.turma;

    // PREENCHE OS NOVOS CAMPOS DE OBSERVAÇÃO
    document.getElementById('edit-obs-cadastral').value = dados.obs_cadastral || "";
    document.getElementById('edit-obs-evangelizador').value = dados.obs_evangelizador || "";
});

function fecharModalEdicao() { document.getElementById('modal-editar').style.display = 'none'; }

function salvarEdicaoAluno() {
    if(!confirm("Salvar alterações?")) return;
    document.getElementById('loading').style.display = 'flex';
    
    socket.emit('salvar_edicao_cadastro', {
        row_id: document.getElementById('edit-row-id').value,
        dados: {
            nome: document.getElementById('edit-nome').value,
            nasc: document.getElementById('edit-nasc').value,
            contato_aluno: document.getElementById('edit-contato-aluno').value,
            responsavel: document.getElementById('edit-resp').value,
            contato_resp: document.getElementById('edit-contato-resp').value,
            turma: document.getElementById('edit-turma').value,

            // ENVIA OS NOVOS CAMPOS PARA O PYTHON
            obs_cadastral: document.getElementById('edit-obs-cadastral').value,
            obs_evangelizador: document.getElementById('edit-obs-evangelizador').value
        }
    });
}

socket.on('sucesso_edicao', (msg) => {
    document.getElementById('loading').style.display = 'none';
    alert(msg.msg);
    fecharModalEdicao();
});

socket.on('erro', (msg) => {
    document.getElementById('loading').style.display = 'none';
    alert(msg.msg);
});

// --- NOVA FUNCIONALIDADE: FICHA DO ALUNO (COM COR AZUL/CIANO) ---
function abrirFicha(nome) {
    const turma = document.getElementById('select-turma-ficha').value;
    document.getElementById('loading').style.display = 'flex';
    
    // Abre o modal primeiro com "Carregando..."
    document.getElementById('ficha-conteudo').innerHTML = '<div class="text-center text-white"><i class="fas fa-spinner fa-spin"></i> Buscando dados...</div>';
    document.getElementById('modal-ficha').style.display = 'flex'; 

    fetch('/ficha_aluno', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({ turma: turma, nome: nome })
    })
    .then(res => res.json())
    .then(data => {
        document.getElementById('loading').style.display = 'none';
        
        if(data.erro) {
            document.getElementById('ficha-conteudo').innerHTML = `<div class="text-danger text-center">${data.erro}</div>`;
            return;
        }
        
        const html = `
            <div class="mb-3 text-center">
                <h4 class="text-white mb-0">${data.nome}</h4>
                <small class="text-muted">${turma}</small>
            </div>
            
            <div class="ficha-item">
                <span class="ficha-label"><i class="fas fa-birthday-cake text-info"></i> Nascimento:</span>
                <span class="ficha-val text-white">${data.nasc}</span>
            </div>
            
            <hr class="border-secondary my-3">
            
            <div class="ficha-item">
                <span class="ficha-label"><i class="fas fa-user-shield text-success"></i> Responsável:</span>
                <span class="ficha-val text-white">${data.responsavel}</span>
            </div>
            
            <div class="row mt-2">
                <div class="col-6">
                    <div class="ficha-item">
                        <span class="ficha-label"><i class="fab fa-whatsapp text-success"></i> Resp.:</span>
                        <a href="https://wa.me/55${limparTel(data.contato_resp)}" target="_blank" class="ficha-val text-info text-decoration-none">${data.contato_resp}</a>
                    </div>
                </div>
                <div class="col-6">
                    <div class="ficha-item">
                        <span class="ficha-label"><i class="fab fa-whatsapp text-success"></i> Evang.:</span>
                        <a href="https://wa.me/55${limparTel(data.contato_aluno)}" target="_blank" class="ficha-val text-info text-decoration-none">${data.contato_aluno}</a>
                    </div>
                </div>
            </div>

            <hr class="border-secondary my-3">
            
            <div class="ficha-item">
                <span class="ficha-label text-info"><i class="fas fa-clipboard-list"></i> Obs. Cadastrais:</span>
                <div class="obs-box text-white border border-info">
                    ${data.obs_cadastral}
                </div>
            </div>
            
            <div class="ficha-item mt-3">
                <span class="ficha-label text-warning"><i class="fas fa-sticky-note"></i> Obs. Evangelizador:</span>
                <div class="obs-box text-white border border-warning">
                    ${data.obs_evangelizador}
                </div>
            </div>
        `;
        
        document.getElementById('ficha-conteudo').innerHTML = html;
    })
    .catch(err => {
        document.getElementById('loading').style.display = 'none';
        alert("Erro ao buscar ficha: " + err);
        fecharModalFicha();
    });
}

function fecharModalFicha() {
    document.getElementById('modal-ficha').style.display = 'none';
}

// Helper para limpar telefone pro link do WhatsApp
function limparTel(tel) {
    if(!tel) return "";
    return tel.replace(/\D/g, '');
}