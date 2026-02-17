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
                    
                    # Tenta separar por vírgula (padrão) ou ponto e vírgula
                    if ';' in raw_turmas:
                        return [t.strip() for t in raw_turmas.split(';') if t.strip()]
                    return [t.strip() for t in raw_turmas.split(',') if t.strip()]
            return None
        except Exception as e:
            print(f"Erro Login: {e}")
            return None

    def obter_alunos(self, turma):
        try:
            client = self.get_client()
            sh = client.open_by_key(Config.SHEET_ID_DB)
            ws = sh.worksheet(turma)
            # Na planilha do Banco de Dados (que vem do QUERY), o Nome é a Coluna A (1)
            nomes = ws.col_values(1)[1:] 
            return sorted([n for n in nomes if n])
        except Exception as e:
            print(f"Erro ao ler alunos da turma '{turma}': {e}")
            return []

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
                # Aciona o Webhook de LOG (se houver um específico para isso, senão ignora)
                try: requests.get(Config.WEBHOOK_LOG_URL + "?p=1", timeout=1)
                except: pass
                
            return True, "✅ Dados salvos com sucesso!"
        except Exception as e:
            self.client = None 
            return False, f"Erro ao salvar: {str(e)}"

    def buscar_dados_aluno(self, nome_aluno):
        try:
            client = self.get_client()
            # Conecta na planilha bruta de RESPOSTAS DO FORMULÁRIO
            ws = client.open_by_key(Config.SHEET_ID_CADASTRO).worksheet("Respostas ao formulário 1")
            
            # Coluna B (2) é o Nome Completo
            coluna_nomes = ws.col_values(2) 
            
            try:
                # +1 porque lista começa em 0, mas planilha começa em 1
                row_index = coluna_nomes.index(nome_aluno) + 1
            except ValueError:
                return False, "Aluno não encontrado."

            dados_linha = ws.row_values(row_index)
            
            # Função auxiliar para não dar erro se a linha estiver incompleta
            def get_val(idx): return dados_linha[idx] if len(dados_linha) > idx else ""

            # MAPEAMENTO NOVO (Baseado nos seus arquivos):
            # Col A (0): Carimbo
            # Col B (1): Nome
            # Col C (2): Nascimento
            # Col D (3): Contato Evan (NOVO)
            # Col E (4): Responsável
            # Col F (5): Contato Resp
            # Col G (6): Turma

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
            
            # Usa USER_ENTERED para formatar datas e números automaticamente (evita o apóstrofe)
            ws.update(f"B{row_id}:G{row_id}", valores, value_input_option='USER_ENTERED')
            return True, "✅ Cadastro atualizado!"
        except Exception as e:
            return False, str(e)

# Instância global
google_service = GoogleManager()