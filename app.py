import streamlit as st
import plotly.express as px
import pandas as pd
from analyzer import SmartFinanceAnalyzer
from database import (
    registrar_usuario, login_usuario, logout_usuario, 
    salvar_microgastos_supabase, buscar_historico_supabase
)

# 1. Configuração inicial obrigatória
st.set_page_config(page_title="SDM Analytics", page_icon="📊", layout="wide")

# 2. Injeção de CSS e Ícones (Corrigido para evitar vazamento de texto)
css_style = """
<link href="https://fonts.googleapis.com/icon?family=Material+Icons" rel="stylesheet">
<style>
    .stApp { background-color: #0e1117; color: #f8fafc; font-family: 'Inter', sans-serif; }
    h1, h2, h3, h4, label { color: #ffffff !important; }
    div[data-testid="stMetric"] {
        background-color: #1e293b; padding: 24px; border-radius: 12px; 
        border: 1px solid #334155; box-shadow: 0 4px 6px rgba(0,0,0,0.2);
    }
    .material-icons { vertical-align: middle; margin-right: 10px; color: #3b82f6; }
    .stTabs [data-baseweb="tab-list"] { gap: 24px; border-bottom: 2px solid #334155; }
    .stTabs [aria-selected="true"] { color: #3b82f6 !important; border-bottom-color: #3b82f6 !important; }
    [data-testid="stTable"] { background-color: #1e293b; border-radius: 8px; }
</style>
"""
st.markdown(css_style, unsafe_allow_html=True)

# 3. Gestão de Estado da Sessão
if 'user' not in st.session_state: st.session_state.user = None
if 'df_master' not in st.session_state: st.session_state.df_master = None
if 'perfil_configurado' not in st.session_state: st.session_state.perfil_configurado = False

# Restante do código de autenticação...

if st.session_state.user is None:
    st.write("<br><br><br>", unsafe_allow_html=True)
    c1, col_auth, c2 = st.columns([1, 1.5, 1])
    
    with col_auth:
        st.markdown('<h1><span class="material-icons" style="font-size: 40px;">shield</span>SDM Analytics</h1>', unsafe_allow_html=True)
        st.write("Sistema de Detecção de Microgastos | Inteligência em Auditoria Financeira")
        st.divider()
        
        modo = st.radio("Selecione o tipo de acesso:", ["Acessar Sistema", "Novo Cadastro"], horizontal=True)
        st.write("<br>", unsafe_allow_html=True)
        
        email = st.text_input("E-mail corporativo")
        senha = st.text_input("Senha de acesso", type="password")
        
        if modo == "Acessar Sistema":
            if st.button("Autenticar", type="primary", use_container_width=True):
                with st.spinner("Validando..."):
                    user, erro = login_usuario(email, senha)
                    if user:
                        st.session_state.user = user
                        st.rerun()
                    else: st.error(erro)
        else:
            if st.button("Registrar Credenciais", type="primary", use_container_width=True):
                with st.spinner("Criando conta..."):
                    user, erro = registrar_usuario(email, senha)
                    if user: st.success("Usuário registrado. Realize o login.")
                    else: st.error(erro)

else:
    c_h1, c_h2 = st.columns([4, 1])
    with c_h1:
        st.markdown('<h2><span class="material-icons" style="font-size: 32px;">analytics</span>Dashboard de BI</h2>', unsafe_allow_html=True)
        st.write(f"Sessão autenticada: **{st.session_state.user.email}**")
    with c_h2:
        st.write("<br>", unsafe_allow_html=True)
        if st.button("Encerrar Sessão", use_container_width=True):
            logout_usuario()
            st.session_state.user = None
            st.rerun()

    st.divider()
    
    t1, t2, t3 = st.tabs(["Ingestão de Dados (ETL)", "Auditoria Transacional", "Análise de Impacto & Histórico"])

    with t1:
        col_s1, col_s2 = st.columns(2, gap="large")
        with col_s1:
            st.markdown('<h4><span class="material-icons">settings</span>Parâmetros do Algoritmo</h4>', unsafe_allow_html=True)
            renda = st.number_input("Renda Mensal (R$)", value=5000.0, step=500.0)
            limite = st.number_input("Threshold de Microgasto (R$)", value=50.0, step=10.0)
            if st.button("Confirmar Configuração", type="primary"):
                st.session_state.perfil_configurado = True
                st.success("Configuração de perfil aplicada.")
        
        with col_s2:
            st.markdown('<h4><span class="material-icons">cloud_upload</span>Upload do Extrato</h4>', unsafe_allow_html=True)
            if st.session_state.perfil_configurado:
                file = st.file_uploader("Formatos aceitos: PDF, CSV e JSON", type=['pdf', 'csv', 'json'])
                if file:
                    with st.spinner("Executando mineração via Regex..."):
                        engine = SmartFinanceAnalyzer(renda, limite)
                        st.session_state.df_master = engine.processar_arquivo(file)
                        st.session_state.df_master['Microgasto?'] = st.session_state.df_master['valor'] <= limite
                        st.success("Dados minerados com sucesso.")
            else:
                st.warning("Aguardando definição de perfil financeiro.")

    with t2:
        if st.session_state.df_master is not None:
            st.markdown('<h4><span class="material-icons">fact_check</span>Validação de Categorias</h4>', unsafe_allow_html=True)
            st.write("Revise as classificações sugeridas pela IA antes de gerar os indicadores finais.")
            
            cats = ['Alimentação', 'Transporte', 'Assinaturas', 'Saúde', 'Lazer', 'Outros']
            
            df_edit = st.data_editor(
                st.session_state.df_master,
                column_config={
                    "data": st.column_config.DateColumn("Data", format="DD/MM/YYYY"),
                    "valor": st.column_config.NumberColumn("Valor (R$)", format="R$ %.2f"),
                    "categoria": st.column_config.SelectboxColumn("Categoria", options=cats),
                    "Microgasto?": st.column_config.CheckboxColumn("Analisar como Microgasto")
                },
                hide_index=True, use_container_width=True
            )
            if st.button("Salvar Auditoria", type="primary"):
                st.session_state.df_master = df_edit
                st.success("Dados auditados.")
        else:
            st.info("Aguardando upload na aba 1.")

    with t3:
        if st.session_state.df_master is not None:
            df_m = st.session_state.df_master[st.session_state.df_master['Microgasto?']]
            total_m = df_m['valor'].sum()
            im = (total_m / renda) * 100

            st.markdown('<h4><span class="material-icons">insights</span>Indicadores de Desempenho</h4>', unsafe_allow_html=True)
            c_m1, c_m2 = st.columns(2)
            c_m1.metric("Impacto Acumulado (R$)", f"{total_m:.2f}")
            c_m2.metric("Índice de Microgastos (IM)", f"{im:.2f}%")

            col_g1, col_g2 = st.columns(2)
            with col_g1:
                fig1 = px.pie(df_m, values='valor', names='categoria', hole=0.5, template="plotly_dark", title="Concentração por Categoria")
                st.plotly_chart(fig1, use_container_width=True, config={'displayModeBar': False})
            with col_g2:
                df_m_s = df_m.sort_values('data')
                df_m_s['acumulado'] = df_m_s['valor'].cumsum()
                fig2 = px.area(df_m_s, x='data', y='acumulado', template="plotly_dark", title="Crescimento Acumulado")
                fig2.update_layout(dragmode=False)
                st.plotly_chart(fig2, use_container_width=True, config={'displayModeBar': False})

            st.divider()

            st.markdown('<h4><span class="material-icons">history</span>Evolução Mensal (Filtro Dinâmico)</h4>', unsafe_allow_html=True)
            df_hist = buscar_historico_supabase(st.session_state.user.id)
            
            if not df_hist.empty:
                df_hist['mes_ano'] = df_hist['data'].dt.strftime('%m/%Y')
                res_mensal = df_hist.groupby('mes_ano')['valor'].sum().reset_index()
                
                filtros = st.multiselect("Selecionar meses para comparação:", options=res_mensal['mes_ano'].unique())
                df_final = res_mensal[res_mensal['mes_ano'].isin(filtros)] if filtros else res_mensal
                
                fig3 = px.bar(df_final, x='mes_ano', y='valor', text='valor', template="plotly_dark")
                fig3.update_traces(texttemplate='R$ %{text:.2f}', textposition='outside')
                fig3.update_layout(dragmode=False)
                st.plotly_chart(fig3, use_container_width=True, config={'displayModeBar': False})
            
            st.write("<br>", unsafe_allow_html=True)
            if st.button("Persistir Dados na Nuvem", type="primary", use_container_width=True):
                if salvar_microgastos_supabase(st.session_state.df_master, st.session_state.user.id):
                    st.success("Sincronização com Supabase concluída.")
                    st.balloons()