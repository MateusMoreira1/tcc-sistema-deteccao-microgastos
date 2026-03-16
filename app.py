import streamlit as st
import plotly.express as px
import pandas as pd
from analyzer import SmartFinanceAnalyzer
from database import salvar_microgastos_supabase

# 1. CONFIGURAÇÃO DE INTERFACE E ESTILO (UI/UX)
st.set_page_config(
    page_title="TCC | Inteligência Financeira", 
    page_icon="💎", 
    layout="wide"
)

# CSS para garantir alto contraste e visual moderno
st.markdown("""
    <style>
    .main { background-color: #f8f9fa; }
    /* Correção de visibilidade das métricas */
    [data-testid="stMetricValue"] { color: #1f2937 !important; font-weight: bold !important; }
    [data-testid="stMetricLabel"] { color: #4b5563 !important; }
    .stMetric { 
        background-color: #ffffff; 
        padding: 20px; 
        border-radius: 12px; 
        border: 1px solid #e5e7eb;
        box-shadow: 0 4px 6px rgba(0,0,0,0.05);
    }
    </style>
    """, unsafe_allow_html=True)

# 2. TÍTULO OFICIAL DO PROJETO
st.title("SISTEMA INTELIGENTE PARA DETECÇÃO DE MICROGASTOS EM EXTRATOS FINANCEIROS POR MEIO DA ANÁLISE DE DADOS")
st.caption("Solução baseada em Análise de Dados para Auditoria de Consumo Pessoal.")
st.markdown("---")

# 3. GERENCIAMENTO DE ESTADO (SESSION STATE)
if 'df_master' not in st.session_state:
    st.session_state.df_master = None

# 4. PAINEL LATERAL (CONFIGURAÇÕES)
with st.sidebar:
    st.header("👤 Perfil do Usuário")
    renda = st.number_input("Sua Renda Mensal (R$)", min_value=1.0, value=5000.0)
    limite = st.slider("Limite para Microgasto (R$)", 1.0, 500.0, 50.0)
    st.divider()
    st.info("""
    **Metodologia:**
    O sistema utiliza Regex Contextual para extrair dados de PDFs, CSVs e JSONs, 
    calculando o impacto orçamentário real.
    """)

# 5. FLUXO DE TRABALHO (ABAS DE INTERAÇÃO)
aba_in, aba_edit, aba_out = st.tabs([
    "📤 1. Importação Multiformato", 
    "🔍 2. Auditoria e Validação", 
    "🚀 3. Business Intelligence"
])

# --- ABA 1: ENTRADA DE DADOS ---
with aba_in:
    st.subheader("Importar Extrato")
    file = st.file_uploader("Arraste seu arquivo (PDF, CSV ou JSON)", type=['pdf', 'csv', 'json'])
    
    if file:
        with st.spinner("Minerando dados do extrato..."):
            try:
                engine = SmartFinanceAnalyzer(renda, limite)
                df = engine.processar_arquivo(file)
                # Classificação binária inicial
                df['Microgasto?'] = df['valor'] <= limite
                st.session_state.df_master = df
                st.success("✅ Extração concluída! Prossiga para a aba de Auditoria.")
            except Exception as e:
                st.error(f"Erro no processamento: {e}")

# --- ABA 2: INTERAÇÃO E AJUSTES ---
with aba_edit:
    if st.session_state.df_master is not None:
        st.subheader("🔎 Auditoria Humana")
        st.info("Confirme ou corrija os dados identificados pelo algoritmo antes de gerar o BI.")
        
        # Editor interativo de dados
        df_validado = st.data_editor(
            st.session_state.df_master, 
            use_container_width=True, 
            num_rows="dynamic"
        )
        
        if st.button("Finalizar Auditoria"):
            st.session_state.df_master = df_validado
            st.success("Dados confirmados! Veja os resultados na aba 3.")
            st.balloons()
    else:
        st.warning("⚠️ Aguardando upload de arquivo na aba 1.")

# --- ABA 3: RESULTADOS E PERSISTÊNCIA ---
with aba_out: 
    if st.session_state.df_master is not None:
        df_final = st.session_state.df_master
        df_m = df_final[df_final['Microgasto?']]
        
        # Cálculos de Indicadores
        engine = SmartFinanceAnalyzer(renda, limite)
        total_m, im = engine.calcular_im(df_m)

        # Dashboard de KPIs
        c1, c2, c3 = st.columns([1, 1, 2])
        with c1:
            st.metric("Soma de Microgastos", f"R$ {total_m:.2f}")
        with c2:
            st.metric("Impacto (IM)", f"{im:.2f}%")
        with c3:
            st.markdown("**💡 Recomendação do Sistema:**")
            st.info(engine.gerar_dicas(im))

        st.divider()
        
        # Gráficos de Análise
        col_l, col_r = st.columns(2)
        with col_l:
            st.markdown("#### Distribuição por Categoria")
            fig_pie = px.pie(df_m, values='valor', names='categoria', hole=0.5)
            st.plotly_chart(fig_pie, use_container_width=True)
        
        with col_r:
            st.markdown("#### Evolução do Prejuízo Invisível")
            df_m = df_m.sort_values(by='data')
            df_m['acumulado'] = df_m['valor'].cumsum()
            fig_area = px.area(df_m, x='data', y='acumulado', color_discrete_sequence=['#ff4b4b'])
            st.plotly_chart(fig_area, use_container_width=True)

        st.divider()
        
        # Persistência em Nuvem
        st.subheader("☁️ Nuvem Supabase")
        if st.button("💾 Persistir Microgastos no Banco de Dados"):
            if salvar_microgastos_supabase(st.session_state.df_master):
                st.success("Transações salvas com sucesso no Supabase!")
            else:
                st.error("Erro ao conectar com o banco de dados remoto.")
    else:
        st.warning("⚠️ Conclua a auditoria na aba 2 primeiro.")