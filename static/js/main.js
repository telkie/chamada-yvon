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

// --- LÓGICA DE TURMA ---
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

socket.on('dados_turma', (data) => {
    alunosData = data.alunos;
    if (data.modo === 'editar_cadastro') {
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
// --- ENVIAR PRESENÇA (Item 6: Validação de Sábado) ---
function enviarPresenca() {
    if(!turmaAtual) return alert("Selecione a turma");
    const dt = document.getElementById('data-picker').value;

    // VALIDAÇÃO DE SÁBADO
    // Adiciona 'T12:00:00' para garantir que o fuso horário não mude o dia
    const dataObj = new Date(dt + 'T12:00:00');
    const diaSemana = dataObj.getDay(); // 0=Domingo, 6=Sábado

    if (diaSemana !== 6) {
        alert("🚫 Erro: A chamada só pode ser enviada aos Sábados!");
        return;
    }

    if(!confirm(`Confirmar envio para ${turmaAtual} em ${dt}?`)) return;
    
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
    // Aviso visual extra pois o webhook pode levar uns 2 segundos
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

// --- EDITAR CADASTRO (CRUD) ---
function abrirModalEdicao(nome) {
    document.getElementById('loading').style.display = 'flex';
    socket.emit('solicitar_dados_aluno', { nome: nome });
}

socket.on('dados_aluno_recebidos', (dados) => {
    document.getElementById('loading').style.display = 'none';
    document.getElementById('modal-editar').style.display = 'block';
    
    document.getElementById('edit-row-id').value = dados.row_id;
    document.getElementById('edit-nome').value = dados.nome;
    document.getElementById('edit-nasc').value = dados.nasc;
    document.getElementById('edit-contato-aluno').value = dados.contato_aluno || "";
    document.getElementById('edit-resp').value = dados.responsavel;
    document.getElementById('edit-contato-resp').value = dados.contato_resp;
    document.getElementById('edit-turma').value = dados.turma;
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
            turma: document.getElementById('edit-turma').value
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