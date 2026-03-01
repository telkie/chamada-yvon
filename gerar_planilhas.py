import gspread
from oauth2client.service_account import ServiceAccountCredentials

# --- CONFIGURAÇÕES ---
ARQUIVO_CREDENCIAIS = "credentials.json"
ID_BANCO_DADOS = "1qJsrj_-vAqC1oIb-YrN0VPMdnFbeki88_xvXwEci7xg" # Planilha Mestre

# IDs das planilhas individuais (Visualização) na ordem correta
# (Baseado nos links que você mandou por último)
IDS_INDIVIDUAIS = [
    "1kzRXpwDkKJdIGfm5iHBAIn4btn2y5G_xUWB4b_gqjGs", # Bebês
    "14lokWrqkCNCUZoDCy7rauADIvjbI75H2xH8yYCLlfVo", # Maternal
    "11kyhJQECwO-sdlz7gu40oQh1TQHIgjXUDlhEelj2Wlk", # Jardim
    "1oiNDX0DmVU6ZV-HGg7D10uMY-IcPniNNoZvWxs8hpHI", # 1° Ciclo
    "1psPfh2g21XtDynTyOqosY8hkCg2wSFnMyumNAzWAoTU", # 2° Ciclo
    "1AsfH6JpzNF_Mmh87vcxVSlKQ87Fh3d3AjyJ8Tz0HBpc", # 3° Ciclo
    "1Zz-2Z1Vf2XTgYoVvdjRV_UySP5pljq-CNpvfQuzSaFM", # Pré-juventude
    "1tYwlQydWhUyZvS_Rek1SqG9jAa5-F3FUhaOcc_dHf8M"  # Juventude
]

# Nomes exatos das abas no Banco de Dados
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

def atualizar_formulas():
    print("🔄 Iniciando atualização das fórmulas no Banco de Dados...\n")
    
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    creds = ServiceAccountCredentials.from_json_keyfile_name(ARQUIVO_CREDENCIAIS, scope)
    client = gspread.authorize(creds)
    
    # Abre o Banco de Dados
    sh_banco = client.open_by_key(ID_BANCO_DADOS)

    for i, turma in enumerate(TURMAS):
        try:
            print(f"📂 Processando aba: {turma}...")
            ws = sh_banco.worksheet(turma)
            
            # --- FÓRMULA 1 (Célula A1) - Puxa do Forms ---
            # ID do Forms: 17njX9mxmQj8ikhgve6LRVXVLOuahYp2NQoi69gmFQo8
            # Nota: Col8 'Observações forms' foi adicionado conforme pedido
            formula_a1 = (
                f'=QUERY(IMPORTRANGE("17njX9mxmQj8ikhgve6LRVXVLOuahYp2NQoi69gmFQo8"; "\'Respostas ao formulário 1\'!A:H"); '
                f'"SELECT Col2, Col3, Col4, Col5, Col6, Col8 WHERE Col7 = \'{turma}\' '
                f'ORDER BY Col2 LABEL Col2 \'Nome\', Col3 \'Nascimento\', Col4 \'Contato Aluno\', '
                f'Col5 \'Responsável\', Col6 \'Contato Resp\', Col8 \'Observações forms\'")'
            )
            
            # --- FÓRMULA 2 (Célula G1) - Puxa da Planilha Individual ---
            id_individual = IDS_INDIVIDUAIS[i]
            
            # ATENÇÃO: Se na planilha individual a aba se chama "Dados", use 'Dados'.
            # Se for o nome da turma, use '{turma}'. 
            # Como o script anterior renomeou a aba para o nome da turma, usarei '{turma}' por segurança.
            # Se você renomeou manualmente para "Dados", mude abaixo para 'Dados'.
            aba_origem = turma  
            
            formula_g1 = f'=IMPORTRANGE("{id_individual}"; "\'{aba_origem}\'!G:G")'
            
            # Atualiza as células em lote (mais rápido)
            ws.update_acell('A1', formula_a1)
            ws.update_acell('G1', formula_g1)
            
            print(f"   ✅ Fórmulas atualizadas em A1 e G1.")
            
        except Exception as e:
            print(f"   ❌ Erro na turma {turma}: {e}")

    print("\n✨ Processo concluído! Verifique o Banco de Dados.")
    print("⚠️ IMPORTANTE: Pode ser necessário abrir o Banco de Dados e clicar em 'Permitir Acesso' nas células G1 de cada aba.")

if __name__ == "__main__":
    atualizar_formulas()