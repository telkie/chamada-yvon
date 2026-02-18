import gspread
from oauth2client.service_account import ServiceAccountCredentials
import requests
import datetime
from config import Config

class GoogleManager:
    def __init__(self):
        self.client = None

    def get_client(self):
        if self.client is None:
            scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
            creds = ServiceAccountCredentials.from_json_keyfile_name(Config.CREDS_FILE, scope)
            self.client = gspread.authorize(creds)
        return self.client

    def validar_login(self, usuario, senha):
        try:
            client = self.get_client()
            ws = client.open_by_key(Config.SHEET_ID_DB).worksheet("Evangelizadores")
            records = ws.get_all_records()
            for row in records:
                if str(row['Login']) == usuario and str(row['Senha']) == senha:
                    # Limpa aspas e quebras de linha que podem vir do CSV/Excel
                    raw_turmas = str(row['Turma']).replace('"', '').replace('\n', '')
                    
                    # Tenta separar por ponto e vírgula ou vírgula
                    if ';' in raw_turmas:
                        return [t.strip() for t in raw_turmas.split(';') if t.strip()]
                    return [t.strip() for t in raw_turmas.split(',') if t.strip()]
            return None
        except Exception as e:
            print(f"Erro Login: {e}")
            return None

    # --- NOVO: Obtém lista simples de alunos para o menu "Meus Alunos" ---
    def obter_lista_alunos(self, turma):
        try:
            client = self.get_client()
            sh = client.open_by_key(Config.SHEET_ID_DB)
            ws = sh.worksheet(turma)
            # Coluna A (1) é o Nome no Banco de Dados
            nomes = ws.col_values(1)[1:] 
            return sorted([n for n in nomes if n])
        except Exception as e:
            print(f"Erro lista alunos: {e}")
            return []

    # --- NOVO: Obtém a ficha completa com as observações ---
    def obter_ficha_aluno(self, turma, nome_aluno):
        try:
            client = self.get_client()
            sh = client.open_by_key(Config.SHEET_ID_DB)
            ws = sh.worksheet(turma)
            
            # Procura a célula que contém o nome exato
            cell = ws.find(nome_aluno)
            if not cell:
                return None
            
            # Pega a linha inteira
            row = ws.row_values(cell.row)
            
            # Função auxiliar para evitar erro de índice (caso a coluna esteja vazia no final)
            def get(idx): return row[idx] if len(row) > idx else ""
            
            # Mapeamento baseado no Banco de Dados:
            # A(0): Nome
            # B(1): Nascimento
            # C(2): Contato Aluno
            # D(3): Responsável
            # E(4): Contato Resp
            # F(5): Obs. Cadastrais (Doenças/TEA/TDAH - Vindo do Forms)
            # G(6): Obs. Evangelizador (Vindo da Planilha Individual)
            
            return {
                'nome': get(0),
                'nasc': get(1),
                'contato_aluno': get(2),
                'responsavel': get(3),
                'contato_resp': get(4),
                'obs_cadastral': get(5) if get(5) else "Nenhuma observação cadastrada.",
                'obs_evangelizador': get(6) if get(6) else "Nenhuma anotação do evangelizador."
            }
        except Exception as e:
            print(f"Erro ficha aluno: {e}")
            return None

    # --- Mantido para a função de Chamada ---
    def obter_alunos(self, turma):
        return self.obter_lista_alunos(turma)

    def recuperar_presenca(self, turma, data):
        try:
            client = self.get_client()
            ws_log = client.open_by_key(Config.SHEET_ID_DB).worksheet("Log_Chamada")
            records = ws_log.get_all_records()
            dt_fmt = datetime.datetime.strptime(data, "%Y-%m-%d").strftime("%d/%m/%Y")
            
            presentes = set()
            for row in records:
                if str(row.get('Turma')) == turma and str(row.get('Data')) == dt_fmt:
                     if row.get('Status') == 'P':
                         presentes.add(row.get('Aluno'))
            return list(presentes)
        except Exception as e:
            print(f"Erro recuperar chamada: {e}")
            return []

    def salvar_chamada(self, turma, data, presentes, tipo):
        try:
            client = self.get_client()
            ws_log = client.open_by_key(Config.SHEET_ID_DB).worksheet("Log_Chamada")
            dt_fmt = datetime.datetime.strptime(data, "%Y-%m-%d").strftime("%d/%m/%Y")
            
            todos = self.obter_alunos(turma)
            linhas = []

            if tipo == 'sem_aula':
                for aluno in todos:
                    linhas.append([f"{turma}-{aluno}-{dt_fmt}", dt_fmt, turma, aluno, "SA", ""])
            else:
                set_presentes = set(presentes)
                for aluno in todos:
                    if aluno in set_presentes:
                        linhas.append([f"{turma}-{aluno}-{dt_fmt}-P", dt_fmt, turma, aluno, "P", ""])
                    else:
                        linhas.append([f"{turma}-{aluno}-{dt_fmt}-F", dt_fmt, turma, aluno, "F", ""])

            if linhas:
                ws_log.append_rows(linhas)
                # Webhook de log opcional
                try: requests.get(Config.WEBHOOK_LOG_URL + "?p=1", timeout=1)
                except: pass
                
            return True, "✅ Dados salvos com sucesso!"
        except Exception as e:
            self.client = None 
            return False, f"Erro ao salvar: {str(e)}"

    # --- CRUD: Busca dados na planilha BRUTA (Form Responses) para edição ---
    def buscar_dados_aluno(self, nome_aluno):
        try:
            client = self.get_client()
            # Conecta na planilha de CADASTRO (Fonte da verdade)
            ws = client.open_by_key(Config.SHEET_ID_CADASTRO).worksheet("Respostas ao formulário 1")
            
            # Coluna B (2) é o Nome Completo
            coluna_nomes = ws.col_values(2) 
            
            try:
                # +1 pois a lista começa em 0 e sheets em 1
                row_index = coluna_nomes.index(nome_aluno) + 1
            except ValueError:
                return False, "Aluno não encontrado."

            dados_linha = ws.row_values(row_index)
            def get_val(idx): return dados_linha[idx] if len(dados_linha) > idx else ""

            # Mapeamento da Planilha de Respostas do Formulário:
            # A(0): Carimbo
            # B(1): Nome
            # C(2): Nascimento
            # D(3): Contato Aluno
            # E(4): Responsável
            # F(5): Contato Resp
            # G(6): Turma
            
            aluno_obj = {
                'row_id': row_index,
                'nome': get_val(1),
                'nasc': get_val(2),
                'contato_aluno': get_val(3),
                'responsavel': get_val(4),
                'contato_resp': get_val(5),
                'turma': get_val(6)
            }
            return True, aluno_obj
        except Exception as e:
            return False, str(e)

    # --- CRUD: Salva edição na planilha BRUTA ---
    def atualizar_cadastro(self, row_id, dados):
        try:
            client = self.get_client()
            ws = client.open_by_key(Config.SHEET_ID_CADASTRO).worksheet("Respostas ao formulário 1")
            
            def limpar(val): return str(val).lstrip("'")

            # Atualiza Colunas B até G (Nome até Turma)
            valores = [[
                limpar(dados['nome']),          # B
                limpar(dados['nasc']),          # C
                limpar(dados['contato_aluno']), # D
                limpar(dados['responsavel']),   # E
                limpar(dados['contato_resp']),  # F
                limpar(dados['turma'])          # G
            ]]
            
            ws.update(f"B{row_id}:G{row_id}", valores, value_input_option='USER_ENTERED')
            return True, "✅ Cadastro atualizado!"
        except Exception as e:
            return False, str(e)

google_service = GoogleManager()