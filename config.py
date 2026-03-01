import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    SECRET_KEY = 'segredo_yvon_sistema_2026_final_v4_webhook'
    
    # IDs das Planilhas
    SHEET_ID_DB = "1qJsrj_-vAqC1oIb-YrN0VPMdnFbeki88_xvXwEci7xg"
    SHEET_ID_CADASTRO = "17njX9mxmQj8ikhgve6LRVXVLOuahYp2NQoi69gmFQo8"
    
    # URLs Externas
    # O webhook de registro de presença continua o mesmo (se houver)
    WEBHOOK_LOG_URL = "https://script.google.com/macros/s/AKfycbyDlq9uHRlYEYvNnAkbkQmbujsY6NA5BH0FoRuMpNY4Il7b5829eqJdaG8B9xywy-4D/exec"
    
    # URL DO NOVO FORMULÁRIO (Form Response)
    FORM_URL = "https://docs.google.com/forms/d/e/1FAIpQLSeJ5THz9ErhPoM5xAFRzT_ZoJ-Lxt3jfVcTOuTGeKK_Fi4pwg/formResponse"
    
    # URL DO SEU WEBHOOK DE SINCRONIZAÇÃO (NOVO!) ⚡
    SYNC_WEBHOOK_URL = "https://script.google.com/macros/s/AKfycbz4Vu8_2ATxioLdyd8GAvLcaXWnsCxk8aclSeJ0xEU0xTkDOHvUCZxFrAfWISV8wwvQCw/exec"
    
    # Arquivo de Credenciais
    CREDS_FILE = "credentials.json"