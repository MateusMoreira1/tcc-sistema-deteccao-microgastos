import streamlit as st
import plotly.express as px
import pandas as pd
from analyzer import SmartFinanceAnalyzer
from database import (
    registrar_usuario, login_usuario, logout_usuario, 
    salvar_microgastos_supabase, buscar_historico_supabase
)

# ==========================================
# 1. CONFIGURAÇÃO BASE E ESTADO
# ==========================================
st.set_page_config(page_title="SDM | Microgastos", page_icon="📊", layout="wide")

if 'user' not in st.session_state: st.session_state.user = None
if 'df_master' not in st.session_state: st.session_state.df_master = None
if 'perfil_configurado' not in st.session_state: st.session_state.perfil_configurado = False

# ==========================================
# 2. MOTOR DE TEMA FIXO (MODO ESCURO PREMIUM)
# ==========================================
bg_color = "#0e1117"
text_color = "#f8fafc"
card_bg = "#1e293b"
border_color = "#334155"
plotly_theme = "plotly_dark"

st.markdown(f"""
    <style>
    /* Força o fundo escuro em toda a aplicação */
    .stApp {{ background-color: {bg_color}; }}
    h1, h2, h3, .stMarkdown p, label {{ color: {text_color} !important; font-family: 'Inter', sans-serif; }}
    
    /* Estilização dos Cards de Métrica */
    div[data-testid="stMetric"] {{
        background-color: {card_bg}; 
        padding: 24px; 
        border-radius: 16px; 
        border: 1px solid {border_color}; 
        box-shadow: 0 4px 10px rgba(0, 0, 0, 0.3);
    }}
    div[data-testid="stMetricLabel"] > label {{ color: {text_color} !important; opacity: 0.8; font-weight: 500; }}
    div[data-testid="stMetricValue"] > div {{ color: {text_color} !important; font-weight: 800 !important; font-size: 2.2rem !important; }}
    
    /* Estilo das abas ativas/inativas */
    .stTabs [data-baseweb="tab-list"] {{ border-bottom: 2px solid {border_color}; }}
    .stTabs [data-baseweb="tab"] {{ color: {text_color}; opacity: 0.7; }}
    .stTabs [aria-selected="true"] {{ color: #3b82f6 !important; opacity: 1; border-bottom-color: #3b82f6 !important; }}
    </style>
    """, unsafe_allow_html=True)

@st.cache_data(show_spinner=False)
def extrair_dados_cacheados(file_bytes, file_name, renda, limite):
    engine = SmartFinanceAnalyzer(renda, limite)
    df = engine.processar_arquivo(file_bytes)
    df['Microgasto?'] = df['valor'] <= limite
    return df

# ==========================================
# 3. ROTEAMENTO: TELA DE LOGIN / CADASTRO
# ==========================================
if st.session_state.user is None:
    st.write("<br><br>", unsafe_allow_html=True)
    col_vazia1, col_login, col_vazia2 = st.columns([1, 1.5, 1])
    
    with col_login:
        st.title("📊 SDM - Microgastos")
        st.markdown("**Sistema Inteligente para Detecção de Microgastos**")
        st.markdown("Acesse a plataforma para analisar seu extrato com privacidade de ponta a ponta.")
        st.divider()
        
        opcao_acesso = st.radio("Selecione uma opção:", ["Fazer Login", "Criar Nova Conta"], horizontal=True)
        st.write("<br>", unsafe_allow_html=True)
        
        if opcao_acesso == "Fazer Login":
            st.subheader("Entrar na sua conta")
            email_login = st.text_input("E-mail", key="log_email")
            senha_login = st.text_input("Senha", type="password", key="log_senha")
            if st.button("Acessar Sistema", type="primary", use_container_width=True):
                if email_login and senha_login:
                    with st.spinner("Autenticando..."):
                        user, erro = login_usuario(email_login, senha_login)
                        if user:
                            st.session_state.user = user
                            st.rerun()
                        else:
                            st.error(erro)
                else:
                    st.warning("Preencha todos os campos para entrar.")
                    
        elif opcao_acesso == "Criar Nova Conta":
            st.subheader("Cadastrar novo usuário")
            email_cad = st.text_input("E-mail", key="cad_email")
            senha_cad = st.text_input("Senha (mínimo 6 caracteres)", type="password", key="cad_senha")
            if st.button("Registrar e Criar Cofre", type="primary", use_container_width=True):
                if email_cad and len(senha_cad) >= 6:
                    with st.spinner("Criando credenciais de segurança..."):
                        user, erro = registrar_usuario(email_cad, senha_cad)
                        if user:
                            st.success("Conta criada! Selecione 'Fazer Login' acima para entrar.")
                        else:
                            st.error(f"Erro: {erro}")
                else:
                    st.warning("Preencha um e-mail válido e senha de no mínimo 6 caracteres.")

# ==========================================
# 4. TELA PRINCIPAL (APLICATIVO)
# ==========================================
else:
    col_topo1, col_topo2 = st.columns([4, 1])
    with col_topo1:
        st.title("📊 SDM Analytics")
        st.markdown(f"Detecção Automática para: **{st.session_state.user.email}**")
    with col_topo2:
        st.write("<br>", unsafe_allow_html=True)
        if st.button("🚪 Encerrar Sessão", use_container_width=True):
            logout_usuario()
            st.session_state.user = None
            st.session_state.df_master = None
            st.session_state.perfil_configurado = False
            st.rerun()

    st.markdown("---")

    aba_setup, aba_auditoria, aba_diagnostico = st.tabs(["📋 1. Perfil & Upload", "🔎 2. Auditoria Humana", "🚀 3. Business Intelligence"])

    # --- ABA 1: SETUP ---
    with aba_setup:
        col1, col2 = st.columns([1, 1.2], gap="large")
        with col1:
            st.subheader("Passo 1: Parametrização")
            st.write("Defina as variáveis para o algoritmo.")
            renda = st.number_input("Renda Mensal (R$)", min_value=1.0, value=5000.0, step=500.0)
            
            # MUDANÇA: Substituído st.slider por st.number_input para facilitar a digitação exata
            limite = st.number_input("Valor limite para ser considerado 'Microgasto' (R$)", min_value=1.0, value=50.0, step=10.0)
            
            if st.button("Confirmar Parâmetros", type="primary", use_container_width=True):
                st.session_state.perfil_configurado = True
                st.success("Parâmetros salvos! Siga para o Passo 2.")

        with col2:
            st.subheader("Passo 2: Ingestão de Dados")
            if st.session_state.perfil_configurado:
                st.info("Insira o extrato (PDF, CSV ou JSON). O processamento utiliza Regex em memória.")
                file = st.file_uploader("Upload", type=['pdf', 'csv', 'json'], label_visibility="collapsed")
                if file:
                    with st.spinner("Minerando dados e executando ETL..."):
                        try:
                            st.session_state.df_master = extrair_dados_cacheados(file, file.name, renda, limite)
                            st.success("Extração concluída! Acesse a aba 2.")
                        except Exception as e:
                            st.error(f"Erro na mineração: {e}")
            else:
                st.warning("Confirme o Passo 1 para habilitar o upload.")

    # --- ABA 2: AUDITORIA ---
    with aba_auditoria:
        if st.session_state.df_master is not None:
            st.subheader("Auditoria e Categorização")
            st.write("A heurística classificou seus gastos. Verifique a tabela e altere a coluna 'Categoria' se discordar do robô.")
            
            categorias = ['Alimentação', 'Transporte', 'Assinaturas/Taxas', 'Saúde', 'Lazer', 'Moradia', 'Educação', 'Outros']
            
            df_validado = st.data_editor(
                st.session_state.df_master,
                column_config={
                    "data": st.column_config.DateColumn("Data da Transação", format="DD/MM/YYYY"),
                    "descricao": st.column_config.TextColumn("Descrição Original", disabled=True),
                    "valor": st.column_config.NumberColumn("Valor (R$)", format="R$ %.2f"),
                    "categoria": st.column_config.SelectboxColumn("Categoria", options=categorias, required=True),
                    "Microgasto?": st.column_config.CheckboxColumn("Marcado como Microgasto?")
                },
                hide_index=True, use_container_width=True, height=400
            )
            
            st.write("<br>", unsafe_allow_html=True)
            if st.button("Finalizar Auditoria e Gerar BI", type="primary"):
                st.session_state.df_master = df_validado
                st.success("Validação humana registrada! Vá para a aba 3.")
        else:
            st.info("Conclua a ingestão de dados na aba 1.")

    # --- ABA 3: DASHBOARD BI ---
    with aba_diagnostico: 
        if st.session_state.df_master is not None:
            df_m = st.session_state.df_master[st.session_state.df_master['Microgasto?']]
            engine = SmartFinanceAnalyzer(renda, limite)
            total_m, im = engine.calcular_im(df_m)

            st.subheader("Indicadores de Desempenho")
            c1, c2, c3 = st.columns([1, 1, 2.5])
            c1.metric("Somatório de Microgastos", f"R$ {total_m:.2f}")
            c2.metric("Índice de Microgastos (IM)", f"{im:.2f}%")
            with c3:
                st.info(engine.gerar_plano_acao(df_m, im))
            
            st.write("<br>", unsafe_allow_html=True)
            
            col_l, col_r = st.columns(2)
            with col_l:
                fig_pie = px.pie(df_m, values='valor', names='categoria', hole=0.6, template=plotly_theme)
                fig_pie.update_traces(textinfo='percent', hoverinfo='label+percent+value', marker=dict(line=dict(color=bg_color, width=2)))
                # MUDANÇA: dragmode=False bloqueia o arraste/seleção
                fig_pie.update_layout(dragmode=False, title_text="Concentração de Despesas por Categoria", title_x=0.5, margin=dict(t=40, b=10, l=10, r=10), paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)")
                # MUDANÇA: config={'displayModeBar': False} remove o menu superior direito
                st.plotly_chart(fig_pie, use_container_width=True, config={'displayModeBar': False})
                
            with col_r:
                df_m_sorted = df_m.sort_values(by='data')
                df_m_sorted['acumulado'] = df_m_sorted['valor'].cumsum()
                fig_area = px.area(df_m_sorted, x='data', y='acumulado', template=plotly_theme, color_discrete_sequence=['#ef4444'])
                # MUDANÇA: dragmode=False bloqueia o arraste/seleção
                fig_area.update_layout(dragmode=False, title_text="Crescimento do Impacto Orçamentário", title_x=0.5, xaxis_title="", yaxis_title="", margin=dict(t=40, b=10, l=10, r=10), paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)")
                # MUDANÇA: config={'displayModeBar': False} remove o menu superior direito
                st.plotly_chart(fig_area, use_container_width=True, config={'displayModeBar': False})

            st.divider()

            st.subheader("📊 Histórico Comparativo (Nuvem)")
            df_historico = buscar_historico_supabase(st.session_state.user.id)
            
            if not df_historico.empty:
                df_historico['mes_ano'] = df_historico['data'].dt.to_period('M').dt.strftime('%b/%Y')
                hist_agrupado = df_historico.groupby('mes_ano', as_index=False)['valor'].sum()
                
                fig_hist = px.line(hist_agrupado, x='mes_ano', y='valor', text='valor', markers=True, template=plotly_theme)
                fig_hist.update_traces(
                    textposition="top center", texttemplate="R$ %{text:.2f}",
                    line=dict(color='#3b82f6', width=4), marker=dict(size=12)
                )
                # MUDANÇA: dragmode=False bloqueia o arraste/seleção
                fig_hist.update_layout(dragmode=False, xaxis_title="", yaxis_title="", yaxis=dict(showgrid=False, zeroline=False, showticklabels=False), xaxis=dict(showgrid=False), margin=dict(t=20, b=20, l=0, r=0), paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)")
                # MUDANÇA: config={'displayModeBar': False} remove o menu superior direito
                st.plotly_chart(fig_hist, use_container_width=True, config={'displayModeBar': False})
            else:
                st.write("Banco de dados vazio para este usuário. Salve o mês atual para iniciar a rastreabilidade.")

            st.write("<br>", unsafe_allow_html=True)
            if st.button("☁️ Persistir Dados (Supabase)", type="primary", use_container_width=True):
                if salvar_microgastos_supabase(st.session_state.df_master, st.session_state.user.id):
                    st.success("Transação concluída! Os registros foram salvos sob criptografia no seu ID de usuário.")
                    st.balloons()
                else:
                    st.error("Erro de conexão (Time-out) com o banco de dados.")
        else:
            st.warning("Auditoria pendente na aba 2.")