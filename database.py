import pandas as pd
from supabase import create_client, Client

SUPABASE_URL = "https://hmmcxgxkqewcjowhcbnr.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImhtbWN4Z3hrcWV3Y2pvd2hjYm5yIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NzMzNTkxODksImV4cCI6MjA4ODkzNTE4OX0.eACTz-a_UyRw2oH0TUA8mPnemaOl3G-Fn-9FFBTS4_U"

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

def registrar_usuario(email, senha):
    try:
        response = supabase.auth.sign_up({"email": email, "password": senha})

        if response.user and not response.user.identities:
            return None, (
                "Este e-mail já está cadastrado. Se você já confirmou a conta "
                "antes, faça login normalmente. Se ainda não confirmou, "
                "verifique sua caixa de entrada (e o spam) pelo e-mail de "
                "confirmação já enviado anteriormente."
            )

        return response.user, None
    except Exception as e:
        return None, str(e)

def login_usuario(email, senha):
    try:
        response = supabase.auth.sign_in_with_password({"email": email, "password": senha})
        return response.user, None
    except Exception as e:
        msg_erro = str(e).lower()
        if "email not confirmed" in msg_erro or "not confirmed" in msg_erro:
            return None, (
                "Seu e-mail ainda não foi confirmado. Verifique sua caixa "
                "de entrada (e o spam) e clique no link de confirmação "
                "antes de fazer login."
            )
        return None, "Credenciais inválidas. Verifique e-mail e senha."
    
def logout_usuario():
    try:
        supabase.auth.sign_out()
    except Exception:
        pass

def enviar_reset_senha(email):
    try:
        supabase.auth.reset_password_for_email(email)
        return True, None
    except Exception as e:
        return False, str(e)

def excluir_conta(usuario_id):
    try:
        supabase.rpc('delete_own_account').execute()
        supabase.auth.sign_out()
        return True, None
    except Exception as e:
        return False, str(e)

def buscar_perfil_usuario(usuario_id):
    try:
        response = supabase.table("usuarios") \
            .select("renda_mensal, threshold_microgasto, tema_preferido") \
            .eq("id", usuario_id).execute()
        if response.data:
            return response.data[0]
        return {"renda_mensal": None, "threshold_microgasto": None, "tema_preferido": None}
    except Exception as e:
        print(f"Erro ao buscar perfil: {e}")
        return {"renda_mensal": None, "threshold_microgasto": None, "tema_preferido": None}

def atualizar_perfil_usuario(usuario_id, renda_mensal, threshold_microgasto):
    try:
        supabase.table("usuarios").update({
            "renda_mensal": renda_mensal,
            "threshold_microgasto": threshold_microgasto,
        }).eq("id", usuario_id).execute()
        return True, None
    except Exception as e:
        return False, str(e)

def salvar_microgastos_supabase(df, usuario_id):
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
    try:
        response = supabase.table("microgastos").select("*").eq("usuario_id", usuario_id).execute()
        if response.data:
            df_hist = pd.DataFrame(response.data)
            df_hist['data'] = pd.to_datetime(df_hist['data'])
            return df_hist
        return pd.DataFrame()
    except Exception as e:
        print(f"Erro na recuperação histórica: {e}")
        return pd.DataFrame()
