import logging
import os

import pandas as pd
import streamlit as st
from supabase import create_client

log = logging.getLogger(__name__)

CHAVE_CLIENTE = 'supabase_client'


SUPABASE_URL_PADRAO = "https://hmmcxgxkqewcjowhcbnr.supabase.co"
SUPABASE_KEY_PADRAO = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImhtbWN4Z3hrcWV3Y2pvd2hjYm5yIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NzMzNTkxODksImV4cCI6MjA4ODkzNTE4OX0.eACTz-a_UyRw2oH0TUA8mPnemaOl3G-Fn-9FFBTS4_U"


def _credencial(nome, padrao):
    valor = os.environ.get(nome)
    if valor:
        return valor
    try:
        return st.secrets[nome]
    except (KeyError, FileNotFoundError):
        return padrao


def _cliente():
    if CHAVE_CLIENTE not in st.session_state:
        st.session_state[CHAVE_CLIENTE] = create_client(
            _credencial('SUPABASE_URL', SUPABASE_URL_PADRAO),
            _credencial('SUPABASE_KEY', SUPABASE_KEY_PADRAO),
        )
    return st.session_state[CHAVE_CLIENTE]


def registrar_usuario(email, senha):
    try:
        resposta = _cliente().auth.sign_up({"email": email, "password": senha})
        if resposta.user and not resposta.user.identities:
            return None, (
                "Este e-mail já está cadastrado. Se você já confirmou a conta antes, faça login "
                "normalmente. Se ainda não confirmou, verifique sua caixa de entrada (e o spam) "
                "pelo e-mail de confirmação já enviado anteriormente."
            )
        return resposta.user, None
    except Exception as e:
        return None, str(e)


def login_usuario(email, senha):
    try:
        resposta = _cliente().auth.sign_in_with_password({"email": email, "password": senha})
        return resposta.user, None
    except Exception as e:
        if "not confirmed" in str(e).lower():
            return None, (
                "Seu e-mail ainda não foi confirmado. Verifique sua caixa de entrada (e o spam) "
                "e clique no link de confirmação antes de fazer login."
            )
        return None, "Credenciais inválidas. Verifique e-mail e senha."


def logout_usuario():
    try:
        _cliente().auth.sign_out()
    except Exception:
        pass
    st.session_state.pop(CHAVE_CLIENTE, None)


def enviar_reset_senha(email):
    try:
        _cliente().auth.reset_password_for_email(email)
        return True, None
    except Exception as e:
        return False, str(e)


def excluir_conta():
    try:
        _cliente().rpc('delete_own_account').execute()
    except Exception as e:
        return False, str(e)
    logout_usuario()
    return True, None


def buscar_perfil_usuario(usuario_id):
    vazio = {"renda_mensal": None, "threshold_microgasto": None, "tema_preferido": None}
    try:
        resposta = (
            _cliente().table("usuarios")
            .select("renda_mensal, threshold_microgasto, tema_preferido")
            .eq("id", usuario_id)
            .execute()
        )
    except Exception:
        log.exception("Falha ao buscar o perfil do usuário")
        return vazio
    return resposta.data[0] if resposta.data else vazio


def atualizar_perfil_usuario(usuario_id, renda_mensal, threshold_microgasto):
    try:
        resposta = (
            _cliente().table("usuarios")
            .update({"renda_mensal": renda_mensal, "threshold_microgasto": threshold_microgasto})
            .eq("id", usuario_id)
            .execute()
        )
    except Exception as e:
        return False, str(e)
    if not resposta.data:
        return False, "Nenhum registro de perfil foi atualizado. Verifique as políticas de acesso da tabela usuarios."
    return True, None


def salvar_microgastos_supabase(df, usuario_id):
    if df.empty:
        return True, None
    try:
        registros = df[['data', 'descricao', 'valor', 'categoria']].copy()
        registros['data'] = pd.to_datetime(registros['data']).dt.strftime('%Y-%m-%d')
        registros['usuario_id'] = usuario_id
        _cliente().table("microgastos").insert(registros.to_dict(orient='records')).execute()
        return True, None
    except Exception as e:
        log.exception("Falha ao persistir os microgastos")
        return False, str(e)


def buscar_historico_supabase(usuario_id):
    try:
        resposta = (
            _cliente().table("microgastos")
            .select("data, descricao, valor, categoria")
            .eq("usuario_id", usuario_id)
            .execute()
        )
    except Exception:
        log.exception("Falha ao recuperar o histórico")
        return pd.DataFrame()
    if not resposta.data:
        return pd.DataFrame()
    historico = pd.DataFrame(resposta.data)
    historico['data'] = pd.to_datetime(historico['data'])
    historico['valor'] = pd.to_numeric(historico['valor'])
    return historico