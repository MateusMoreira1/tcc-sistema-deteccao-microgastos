import pandas as pd
from supabase import create_client, Client

# Substitua pelas credenciais do seu projeto no console do Supabase
SUPABASE_URL = "https://hmmcxgxkqewcjowhcbnr.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImhtbWN4Z3hrcWV3Y2pvd2hjYm5yIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NzMzNTkxODksImV4cCI6MjA4ODkzNTE4OX0.eACTz-a_UyRw2oH0TUA8mPnemaOl3G-Fn-9FFBTS4_U"

# Inicializa o cliente Supabase
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

def salvar_microgastos_supabase(df):
    """
    Envia os microgastos para o Supabase corrigindo o formato de data.
    """
    try:
        df_micro = df[df['Microgasto?']].copy()
        
        if df_micro.empty:
            return True
            
        # CORREÇÃO: Força o pandas a entender que o dia vem antes (dayfirst=True)
        # Isso resolve o erro de '13/02/2026'
        df_micro['data'] = pd.to_datetime(df_micro['data'], dayfirst=True)
        
        # Converte para o formato ISO (AAAA-MM-DD) que o banco de dados exige
        df_micro['data'] = df_micro['data'].dt.strftime('%Y-%m-%d')
        
        registros = df_micro[['data', 'descricao', 'valor', 'categoria']].to_dict(orient='records')
        
        # Envio para o banco de dados na nuvem
        supabase.table("microgastos").insert(registros).execute()
        return True
    except Exception as e:
        print(f"Erro na integração com Supabase: {e}")
        return False