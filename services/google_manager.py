import gspread
from oauth2client.service_account import ServiceAccountCredentials
import requests
import datetime
from config import Config

class GoogleManager:
    def __init__(self):
        self.client = None
        self.MAPA_TURMAS_IDS = {
            "Bebês (0 a 2)": "1kzRXpwDkKJdIGfm5iHBAIn4btn2y5G_xUWB4b_gqjGs",
            "Maternal (3 e 4)": "14lokWrqkCNCUZoDCy7rauADIvjbI75H2xH8yYCLlfVo",
            "Jardim (5 e 6)": "11kyhJQECwO-sdlz7gu40oQh1TQHIgjXUDlhEelj2Wlk",
            "1° Ciclo (7 e 8)": "1oiNDX0DmVU6ZV-HGg7D10uMY-IcPniNNoZvWxs8hpHI",
            "2° Ciclo (9 e 10)": "1psPfh2g21XtDynTyOqosY8hkCg2wSFnMyumNAzWAoTU",
            "3° Ciclo (11 e 12)": "1AsfH6JpzNF_Mmh87vcxVSlKQ87Fh3d3AjyJ8Tz0HBpc",
            "Pré-juventude (13 e 14)": "1Zz-2Z1Vf2XTgYoVvdjRV_UySP5pljq-CNpvfQuzSaFM",
            "Juventude (15+)": "1tYwlQydWhUyZvS_Rek1SqG9jAa5-F3FUhaOcc_dHf8M"
        }

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
                    raw_turmas = str(row['Turma']).replace('"', '').replace('\n', '')
                    if ';' in raw_turmas:
                        return [t.strip() for t in raw_turmas.split(';') if t.strip()]
                    return [t.strip() for t in raw_turmas.split(',') if t.strip()]
            return None
        except Exception as e:
            print(f"Erro Login: {e}")
            return None

    def obter_lista_alunos(self, turma):
        try:
            client = self.get_client()
            sh = client.open_by_key(Config.SHEET_ID_DB)
            ws = sh.worksheet(turma)
            nomes = ws.col_values(1)[1:] 
            return sorted([n for n in nomes if n], key=str.lower)
        except: return []

    def obter_ficha_aluno(self, turma, nome_aluno):
        try:
            client = self.get_client()
            sh = client.open_by_key(Config.SHEET_ID_DB)
            ws = sh.worksheet(turma)
            
            cell = ws.find(nome_aluno)
            if not cell: return None
            
            row = ws.row_values(cell.row)
            def get(idx): return row[idx] if len(row) > idx else ""
            
            return {
                'nome': get(0),
                'nasc': get(1),
                'contato_aluno': get(2),
                'responsavel': get(3),
                'contato_resp': get(4),
                'obs_cadastral': get(5) if get(5) else "Nenhuma.",
                'obs_evangelizador': get(6) if get(6) else "Nenhuma."
            }
        except: return None

    def buscar_dados_aluno(self, nome_aluno, turma_contexto=None):
        try:
            client = self.get_client()
            ws_cad = client.open_by_key(Config.SHEET_ID_CADASTRO).worksheet("Respostas ao formulário 1")
            coluna_nomes = ws_cad.col_values(2) 
            
            try:
                row_index = coluna_nomes.index(nome_aluno) + 1
            except ValueError:
                return False, "Aluno não encontrado no Cadastro Geral."

            dados_linha = ws_cad.row_values(row_index)
            def get_val(idx): return dados_linha[idx] if len(dados_linha) > idx else ""

            obs_evangelizador = ""
            if turma_contexto and turma_contexto in self.MAPA_TURMAS_IDS:
                try:
                    id_individual = self.MAPA_TURMAS_IDS[turma_contexto]
                    ws_ind = client.open_by_key(id_individual).sheet1
                    cell_ind = ws_ind.find(nome_aluno)
                    if cell_ind:
                        obs_evangelizador = ws_ind.cell(cell_ind.row, 7).value 
                except Exception as e:
                    print(f"Erro ao buscar obs evangelizador: {e}")
            
            aluno_obj = {
                'row_id': row_index,
                'nome': get_val(1),
                'nasc': get_val(2),
                'contato_aluno': get_val(3),
                'responsavel': get_val(4),
                'contato_resp': get_val(5),
                'turma': get_val(6),
                'obs_cadastral': get_val(7),
                'obs_evangelizador': obs_evangelizador
            }
            return True, aluno_obj
        except Exception as e:
            return False, str(e)

    def atualizar_cadastro(self, row_id, dados):
        try:
            client = self.get_client()
            ws_cad = client.open_by_key(Config.SHEET_ID_CADASTRO).worksheet("Respostas ao formulário 1")
            
            def limpar(val): return str(val).lstrip("'")

            nome_novo = limpar(dados['nome'])
            nome_antigo = limpar(dados.get('nome_antigo', ''))
            turma = limpar(dados['turma'])

            valores_cad = [[
                nome_novo,
                limpar(dados['nasc']),
                limpar(dados['contato_aluno']),
                limpar(dados['responsavel']),
                limpar(dados['contato_resp']),
                turma,
                limpar(dados['obs_cadastral'])
            ]]
            
            ws_cad.update(f"B{row_id}:H{row_id}", valores_cad, value_input_option='USER_ENTERED')
            
            if turma in self.MAPA_TURMAS_IDS:
                try:
                    id_ind = self.MAPA_TURMAS_IDS[turma]
                    ws_ind = client.open_by_key(id_ind).sheet1
                    cell = ws_ind.find(nome_novo)
                    if not cell and nome_antigo:
                        cell = ws_ind.find(nome_antigo)
                    if cell:
                        ws_ind.update_cell(cell.row, 7, limpar(dados['obs_evangelizador']))
                except Exception as e:
                    print(f"Erro ao salvar obs evangelizador: {e}")

            if nome_antigo and nome_antigo != nome_novo:
                try:
                    ID_ANALISE = "1mF7WDCkY8Bh10hGkkFp8gfKrS9HoQa7ErKraTOb-aPM"
                    ws_presenca = client.open_by_key(ID_ANALISE).worksheet(turma)
                    cell_pres = ws_presenca.find(nome_antigo)
                    if cell_pres:
                        ws_presenca.update_cell(cell_pres.row, cell_pres.col, nome_novo)
                except Exception as e:
                    print(f"Erro cascata Análise de Presença: {e}")

                try:
                    ws_log = client.open_by_key(Config.SHEET_ID_DB).worksheet("Log_Chamada")
                    col_alunos = ws_log.col_values(4)
                    
                    cells_to_update = []
                    for i, val in enumerate(col_alunos):
                        if val == nome_antigo:
                            cells_to_update.append({'range': f'D{i+1}', 'values': [[nome_novo]]})
                    
                    if cells_to_update:
                        ws_log.batch_update(cells_to_update)
                except Exception as e:
                    print(f"Erro cascata Log_Chamada: {e}")

            return True, "✅ Cadastro atualizado com sucesso!"
        except Exception as e:
            return False, str(e)

    def obter_alunos(self, turma): return self.obter_lista_alunos(turma)
    
    def recuperar_presenca(self, turma, data):
        try:
            client = self.get_client()
            ws_log = client.open_by_key(Config.SHEET_ID_DB).worksheet("Log_Chamada")
            records = ws_log.get_all_records()
            dt_fmt = datetime.datetime.strptime(data, "%Y-%m-%d").strftime("%d/%m/%Y")
            presentes = set()
            for row in records:
                if str(row.get('Turma')) == turma and str(row.get('Data')) == dt_fmt and row.get('Status') == 'P':
                     presentes.add(row.get('Aluno'))
            return list(presentes)
        except: return []

    def salvar_chamada(self, turma, data, presentes, tipo):
        try:
            client = self.get_client()
            ws_log = client.open_by_key(Config.SHEET_ID_DB).worksheet("Log_Chamada")
            dt_fmt = datetime.datetime.strptime(data, "%Y-%m-%d").strftime("%d/%m/%Y")
            todos = self.obter_alunos(turma)
            linhas = []
            if tipo == 'sem_aula':
                for aluno in todos: linhas.append([f"{turma}-{aluno}-{dt_fmt}", dt_fmt, turma, aluno, "SA", ""])
            else:
                set_presentes = set(presentes)
                for aluno in todos:
                    status = "P" if aluno in set_presentes else "F"
                    linhas.append([f"{turma}-{aluno}-{dt_fmt}-{status}", dt_fmt, turma, aluno, status, ""])
            if linhas:
                ws_log.append_rows(linhas)
                try: requests.get(Config.WEBHOOK_LOG_URL + "?p=1", timeout=1)
                except: pass
            return True, "✅ Dados salvos com sucesso!"
        except Exception as e: return False, f"Erro: {str(e)}"

google_service = GoogleManager()