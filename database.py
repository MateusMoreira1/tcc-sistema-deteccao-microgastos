import pandas as pd
from supabase import create_client, Client


SUPABASE_URL = "https://hmmcxgxkqewcjowhcbnr.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImhtbWN4Z3hrcWV3Y2pvd2hjYm5yIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NzMzNTkxODksImV4cCI6MjA4ODkzNTE4OX0.eACTz-a_UyRw2oH0TUA8mPnemaOl3G-Fn-9FFBTS4_U"

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# ==========================================
# MÓDULO DE AUTENTICAÇÃO (LOGIN/CADASTRO)
# ==========================================
def registrar_usuario(email, senha):
    """Cria um novo usuário no sistema de autenticação do Supabase."""
    try:
        response = supabase.auth.sign_up({"email": email, "password": senha})
        return response.user, None
    except Exception as e:
        return None, str(e)

def login_usuario(email, senha):
    """Autentica o usuário e retorna os dados da sessão."""
    try:
        response = supabase.auth.sign_in_with_password({"email": email, "password": senha})
        return response.user, None
    except Exception as e:
        return None, "E-mail ou senha incorretos."

def logout_usuario():
    """Encerra a sessão atual."""
    try:
        supabase.auth.sign_out()
    except Exception:
        pass

# ==========================================
# MÓDULO DE DADOS (AGORA COM FILTRO DE USUÁRIO)
# ==========================================
def salvar_microgastos_supabase(df, usuario_id):
    """Salva os gastos vinculando-os ao ID do usuário logado."""
    try:
        df_micro = df[df['Microgasto?']].copy()
        if df_micro.empty: return True
            
        df_micro['data'] = pd.to_datetime(df_micro['data']).dt.strftime('%Y-%m-%d')
        # Adiciona a coluna com o ID do usuário para garantir privacidade
        df_micro['usuario_id'] = usuario_id 
        
        registros = df_micro[['data', 'descricao', 'valor', 'categoria', 'usuario_id']].to_dict(orient='records')
        supabase.table("microgastos").insert(registros).execute()
        return True
    except Exception as e:
        print(f"Erro na integração com Supabase: {e}")
        return False

def buscar_historico_supabase(usuario_id):
    """Busca APENAS o histórico do usuário que está logado (Privacidade de Dados)."""
    try:
        # O .eq() atua como uma cláusula WHERE no SQL (WHERE usuario_id = 'id_do_usuario')
        response = supabase.table("microgastos").select("*").eq("usuario_id", usuario_id).execute()
        if response.data:
            df_hist = pd.DataFrame(response.data)
            df_hist['data'] = pd.to_datetime(df_hist['data'])
            return df_hist
        return pd.DataFrame()
    except Exception as e:
        print(f"Erro ao buscar histórico: {e}")
        return pd.DataFrame()