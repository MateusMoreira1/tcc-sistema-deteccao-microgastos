import pandas as pd
from supabase import create_client, Client


SUPABASE_URL = "https://hmmcxgxkqewcjowhcbnr.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImhtbWN4Z3hrcWV3Y2pvd2hjYm5yIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NzMzNTkxODksImV4cCI6MjA4ODkzNTE4OX0.eACTz-a_UyRw2oH0TUA8mPnemaOl3G-Fn-9FFBTS4_U"

# Inicialização do Cliente
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# --- MÓDULO DE AUTENTICAÇÃO ---
def registrar_usuario(email, senha):
    """Realiza o cadastro de novos usuários no provedor de autenticação."""
    try:
        response = supabase.auth.sign_up({"email": email, "password": senha})
        return response.user, None
    except Exception as e:
        return None, str(e)

def login_usuario(email, senha):
    try:
        # O método sign_in_with_password é o padrão para e-mail/senha
        response = supabase.auth.sign_in_with_password({"email": email, "password": senha})
        return response.user, None
    except Exception as e:
        # Se cair aqui, o Supabase rejeitou as credenciais
        return None, "Credenciais inválidas. Verifique e-mail e senha."
    
def logout_usuario():
    """Encerra a sessão ativa do usuário."""
    try:
        supabase.auth.sign_out()
    except Exception:
        pass


def enviar_reset_senha(email):
    """Envia link de redefinição de senha para o e-mail informado.

    O Supabase gera automaticamente um link seguro (com token temporário)
    e envia por e-mail. Ao clicar, o usuário é redirecionado para a página
    de definição de nova senha do próprio Supabase.

    Retorna: (sucesso: bool, mensagem_erro: str | None)
    """
    try:
        supabase.auth.reset_password_for_email(email)
        return True, None
    except Exception as e:
        return False, str(e)


# --- MÓDULO DE PERSISTÊNCIA DE DADOS ---
def salvar_microgastos_supabase(df, usuario_id):
    """Persiste os dados auditados na nuvem vinculados ao usuario_id (Multi-tenant)."""
    try:
        df_micro = df[df['Microgasto?']].copy()
        if df_micro.empty:
            return True
            
        df_micro['data'] = pd.to_datetime(df_micro['data']).dt.strftime('%Y-%m-%d')
        df_micro['usuario_id'] = usuario_id 
        
        registros = df_micro[['data', 'descricao', 'valor', 'categoria', 'usuario_id']].to_dict(orient='records')
        supabase.table("microgastos").insert(registros).execute()
        return True
    except Exception as e:
        print(f"Erro na persistência: {e}")
        return False

def buscar_historico_supabase(usuario_id):
    """Recupera o histórico transacional persistido para análise de BI."""
    try:
        # Cláusula .eq() garante isolamento de dados por usuário
        response = supabase.table("microgastos").select("*").eq("usuario_id", usuario_id).execute()
        if response.data:
            df_hist = pd.DataFrame(response.data)
            df_hist['data'] = pd.to_datetime(df_hist['data'])
            return df_hist
        return pd.DataFrame()
    except Exception as e:
        print(f"Erro na recuperação histórica: {e}")
        return pd.DataFrame()