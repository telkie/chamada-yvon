import requests
import random
import time

# --- CONFIGURAÇÕES ---
URL_FORM = "https://docs.google.com/forms/d/e/1FAIpQLSeJ5THz9ErhPoM5xAFRzT_ZoJ-Lxt3jfVcTOuTGeKK_Fi4pwg/formResponse"

# Lista exata das turmas do seu sistema
TURMAS = [
    "Bebês (0 a 2)", 
    "Maternal (3 e 4)", 
    "Jardim (5 e 6)", 
    "1° Ciclo (7 e 8)", 
    "2° Ciclo (9 e 10)", 
    "3° Ciclo (11 e 12)", 
    "Pré-juventude (13 e 14)", 
    "Juventude (15+)"
]

# Dados para geração aleatória
NOMES = ["Miguel", "Arthur", "Gael", "Théo", "Heitor", "Ravi", "Davi", "Bernardo", "Noah", "Gabriel", "Helena", "Alice", "Laura", "Maria", "Sophia", "Manuela", "Maitê", "Liz", "Cecília", "Isabella", "Pedro", "João", "Lucas", "Enzo", "Valentina", "Beatriz", "Mariana", "Ana", "Lara", "Júlia"]
SOBRENOMES = ["Silva", "Santos", "Oliveira", "Souza", "Rodrigues", "Ferreira", "Alves", "Pereira", "Lima", "Gomes", "Costa", "Ribeiro", "Martins", "Carvalho", "Almeida", "Lopes", "Soares", "Fernandes", "Vieira", "Barbosa", "Rocha", "Dias", "Nascimento", "Andrade", "Moreira", "Nunes", "Marques"]

RESPONSAVEIS = ["Carlos", "Fernanda", "Patrícia", "Roberto", "Juliana", "Marcos", "Luciana", "Ricardo", "Vanessa", "Eduardo", "Tatiane", "Fábio", "Renata", "André"]

def gerar_telefone():
    ddd = random.choice(["11", "21", "31", "41", "51", "61", "71", "81", "91"])
    parte1 = random.randint(90000, 99999)
    parte2 = random.randint(1000, 9999)
    return f"({ddd}) {parte1}-{parte2}"

def gerar_data_nascimento(turma):
    ano_atual = 2026
    
    # Define a faixa de idade baseada no nome da turma
    if "0 a 2" in turma: idade_min, idade_max = 0, 2
    elif "3 e 4" in turma: idade_min, idade_max = 3, 4
    elif "5 e 6" in turma: idade_min, idade_max = 5, 6
    elif "7 e 8" in turma: idade_min, idade_max = 7, 8
    elif "9 e 10" in turma: idade_min, idade_max = 9, 10
    elif "11 e 12" in turma: idade_min, idade_max = 11, 12
    elif "13 e 14" in turma: idade_min, idade_max = 13, 14
    elif "15+" in turma: idade_min, idade_max = 15, 18
    else: idade_min, idade_max = 5, 15

    idade = random.randint(idade_min, idade_max)
    ano = ano_atual - idade
    mes = random.randint(1, 12)
    dia = random.randint(1, 28) # Para evitar problemas com fevereiro
    
    return f"{ano}-{mes:02d}-{dia:02d}"

print("🚀 Iniciando preenchimento em massa do Sistema Yvon...\n")

total_cadastrados = 0

for turma in TURMAS:
    qtd_alunos = random.randint(5, 7)
    print(f"📂 Processando {turma}: Gerando {qtd_alunos} alunos...")
    
    for _ in range(qtd_alunos):
        # Monta os dados
        nome = f"{random.choice(NOMES)} {random.choice(SOBRENOMES)}"
        # 30% de chance de ter sobrenome duplo
        if random.random() > 0.7:
            nome += f" {random.choice(SOBRENOMES)}"
            
        nome_resp = f"{random.choice(RESPONSAVEIS)} {random.choice(SOBRENOMES)}"
        
        dados = {
            "entry.1091823087": nome,                           # Nome
            "entry.883252145": turma,                           # Turma
            "entry.477279343": gerar_data_nascimento(turma),    # Nascimento (Realista)
            "entry.2141494783": gerar_telefone(),               # Contato Evan
            "entry.146137968": nome_resp,                       # Responsavel
            "entry.2118960068": gerar_telefone()                # Contato Resp
        }

        try:
            requests.post(URL_FORM, data=dados)
            print(f"   ✅ {nome} cadastrado com sucesso.")
            total_cadastrados += 1
            # Pequeno delay para não sobrecarregar o webhook do Google
            time.sleep(0.5) 
        except Exception as e:
            print(f"   ❌ Erro ao cadastrar {nome}: {e}")

print(f"\n✨ Concluído! Total de {total_cadastrados} novos alunos inseridos no sistema.")