import streamlit as st
import plotly.express as px
import pandas as pd
from analyzer import SmartFinanceAnalyzer
from database import (
    registrar_usuario, login_usuario, logout_usuario,
    salvar_microgastos_supabase, buscar_historico_supabase
)

# ==========================================
# 1. CONFIGURAÇÃO INICIAL E ESTILOS
# ==========================================
st.set_page_config(page_title="SDM Analytics", page_icon="📊", layout="wide")

css_style = """
<link href="https://fonts.googleapis.com/icon?family=Material+Icons" rel="stylesheet">
<style>
    /* Corpo geral — aumento moderado da base tipográfica */
    .stApp {
        background-color: #0e1117;
        color: #f8fafc;
        font-family: 'Inter', sans-serif;
        font-size: 16px;
    }
    h1, h2, h3, h4, label { color: #ffffff !important; }

    /* Textos em prosa (st.write, markdown livre) — mais respiração */
    .stMarkdown p, .stMarkdown li, .stMarkdown span {
        font-size: 1.05rem;
        line-height: 1.6;
    }

    /* Labels de inputs (Renda, Threshold, E-mail, etc.) */
    label {
        font-size: 1.05rem !important;
        font-weight: 500 !important;
    }

    /* Métricas (Impacto Acumulado / Índice de Microgastos) — DESTAQUE */
    div[data-testid="stMetric"] {
        background-color: #1e293b;
        padding: 28px;
        border-radius: 12px;
        border: 1px solid #334155;
        box-shadow: 0 4px 6px rgba(0,0,0,0.2);
    }
    /* Rótulo da métrica ("Impacto Acumulado (R$)") */
    div[data-testid="stMetricLabel"] {
        font-size: 1.1rem !important;
        font-weight: 500 !important;
    }
    /* Valor da métrica (o número grande) */
    div[data-testid="stMetricValue"] {
        font-size: 2.4rem !important;
        font-weight: 600 !important;
    }

    .material-icons { vertical-align: middle; margin-right: 10px; color: #3b82f6; }

    /* Abas mais legíveis (Ingestão / Auditoria / Análise) */
    .stTabs [data-baseweb="tab-list"] { gap: 24px; border-bottom: 2px solid #334155; }
    .stTabs [data-baseweb="tab-list"] button {
        font-size: 1.05rem !important;
        font-weight: 500 !important;
    }
    .stTabs [aria-selected="true"] { color: #3b82f6 !important; border-bottom-color: #3b82f6 !important; }

    /* Tabelas e data grid */
    [data-testid="stTable"] { background-color: #1e293b; border-radius: 8px; }
    [data-testid="stDataFrame"] {
        font-size: 1rem !important;
    }

    /* Botões */
    .stButton button {
        font-size: 1.02rem !important;
        font-weight: 500 !important;
    }

    /* Caixas de instrução */
    .caixa-guia {
        background-color: #1e293b;
        padding: 20px 24px;
        border-radius: 8px;
        margin-bottom: 24px;
        border-left: 4px solid #3b82f6;
        font-size: 1.05rem;
        line-height: 1.6;
    }

    /* Mensagens de status (success, warning, error) */
    div[data-testid="stAlert"] {
        font-size: 1.05rem !important;
    }
</style>
"""
st.markdown(css_style, unsafe_allow_html=True)

if 'user' not in st.session_state: st.session_state.user = None
if 'df_master' not in st.session_state: st.session_state.df_master = None
if 'perfil_configurado' not in st.session_state: st.session_state.perfil_configurado = False


def calcular_microgasto(df, limite):
    """Determina o flag 'Microgasto?' considerando DUAS condições:
    (1) é uma SAÍDA de caixa (tipo == 'saida')
    (2) o valor está abaixo do threshold definido pelo usuário
    Entradas (créditos, PIX recebido, estorno, etc.) NUNCA são microgastos."""
    if 'tipo' not in df.columns:
        df['tipo'] = 'saida'
    return (df['valor'] <= limite) & (df['tipo'].astype(str).str.lower() == 'saida')


# ==========================================
# 2. FLUXO DE ACESSO
# ==========================================
if st.session_state.user is None:
    st.write("<br><br><br>", unsafe_allow_html=True)
    c1, col_auth, c2 = st.columns([1, 1.5, 1])

    with col_auth:
        st.markdown('<h1><span class="material-icons" style="font-size: 40px;">shield</span>SDM Analytics</h1>', unsafe_allow_html=True)
        st.write("Sistema de Detecção de Microgastos | Autenticação")
        st.divider()

        modo = st.radio("Selecione o acesso:", ["Acessar Sistema", "Novo Cadastro"], horizontal=True)
        st.write("<br>", unsafe_allow_html=True)

        email = st.text_input("E-mail corporativo")
        senha = st.text_input("Senha", type="password")

        if modo == "Acessar Sistema":
            if st.button("Autenticar", type="primary", width="stretch"):
                with st.spinner("Conectando..."):
                    user, erro = login_usuario(email, senha)
                    if user:
                        st.session_state.user = user
                        st.rerun()
                    else: st.error(erro)
        else:
            if st.button("Registrar Credenciais", type="primary", width="stretch"):
                with st.spinner("Criando..."):
                    user, erro = registrar_usuario(email, senha)
                    if user: st.success("Conta criada com sucesso! Realize o login.")
                    else: st.error(erro)

# ==========================================
# 3. APLICATIVO PRINCIPAL (DASHBOARD)
# ==========================================
else:
    c_h1, c_h2 = st.columns([4, 1])
    with c_h1:
        st.markdown('<h2><span class="material-icons" style="font-size: 32px;">analytics</span>Dashboard de BI</h2>', unsafe_allow_html=True)
        st.write(f"Sessão autenticada: **{st.session_state.user.email}**")
    with c_h2:
        st.write("<br>", unsafe_allow_html=True)
        if st.button("Encerrar Sessão", width="stretch"):
            logout_usuario()
            st.session_state.user = None
            st.rerun()

    st.divider()

    t1, t2, t3 = st.tabs(["Ingestão de Dados (ETL)", "Auditoria Transacional", "Análise de Impacto & Histórico"])

    # --- ABA 1: INGESTÃO ---
    with t1:
        st.markdown("""
        <div class="caixa-guia">
            <strong>Instruções de Uso:</strong><br>
            1. Preencha sua renda e o threshold (limite) para classificar um microgasto. Clique em Confirmar.<br>
            2. Realize o upload do seu arquivo de extrato bancário no campo ao lado.<br>
            3. Após o processamento, siga para a aba <b>"Auditoria Transacional"</b> no topo da tela.
        </div>
        """, unsafe_allow_html=True)

        col_s1, col_s2 = st.columns(2, gap="large")
        with col_s1:
            st.markdown('<h4><span class="material-icons">settings</span>Parâmetros do Algoritmo</h4>', unsafe_allow_html=True)
            renda = st.number_input("Renda Mensal (R$)", value=5000.0, step=500.0)
            limite = st.number_input("Threshold de Microgasto (R$)", value=50.0, step=10.0)
            if st.button("Confirmar Configuração", type="primary"):
                st.session_state.perfil_configurado = True
                st.success("Configuração salva. Liberação para upload concedida.")

        with col_s2:
            st.markdown('<h4><span class="material-icons">cloud_upload</span>Upload do Extrato</h4>', unsafe_allow_html=True)
            if st.session_state.perfil_configurado:
                file = st.file_uploader("Formatos aceitos: PDF, CSV, JSON", type=['pdf', 'csv', 'json'])
                if file:
                    with st.spinner("Minerando dados via Regex..."):
                        try:
                            engine = SmartFinanceAnalyzer(renda, limite)
                            df_proc = engine.processar_arquivo(file)
                            # CORREÇÃO: o flag Microgasto? agora exige SAÍDA + valor ≤ threshold.
                            # Entradas (PIX recebido, estorno, etc.) nunca entram no IM.
                            df_proc['Microgasto?'] = calcular_microgasto(df_proc, limite)
                            st.session_state.df_master = df_proc
                            st.success("✅ Dados minerados! Siga para a aba 'Auditoria Transacional'.")
                        except ValueError as e:
                            st.error(f"Erro de formato: {e}")
                        except Exception as e:
                            st.error("Erro inesperado no processamento do arquivo.")
            else:
                st.warning("Confirme os parâmetros do algoritmo primeiro.")

    # --- ABA 2: AUDITORIA ---
    with t2:
        if st.session_state.df_master is not None:
            st.markdown("""
            <div class="caixa-guia" style="border-left-color: #10b981;">
                <strong>Validação de Categorias e Fluxo:</strong><br>
                Revise as classificações sugeridas pela Inteligência do sistema. Altere a categoria, o
                tipo de fluxo (saída/entrada) ou desmarque o flag de microgasto se necessário.<br>
                Ao finalizar, clique em "Salvar Auditoria" e acesse a aba <b>"Análise de Impacto & Histórico"</b>.
            </div>
            """, unsafe_allow_html=True)

            cats = ['Alimentação', 'Transporte', 'Assinaturas/Taxas', 'Saúde', 'Lazer', 'Outros']
            tipos_fluxo = ['saida', 'entrada']

            df_edit = st.data_editor(
                st.session_state.df_master,
                column_config={
                    "data": st.column_config.DateColumn("Data", format="DD/MM/YYYY"),
                    "valor": st.column_config.NumberColumn("Valor (R$)", format="R$ %.2f"),
                    "tipo": st.column_config.SelectboxColumn("Fluxo", options=tipos_fluxo, help="Saída = gasto; Entrada = crédito"),
                    "categoria": st.column_config.SelectboxColumn("Categoria", options=cats),
                    "Microgasto?": st.column_config.CheckboxColumn("Analisar como Microgasto")
                },
                hide_index=True,
                width="stretch"
            )
            if st.button("Salvar Auditoria", type="primary"):
                # Garante consistência: se o usuário marcou uma transação como ENTRADA,
                # ela nunca pode ficar com Microgasto?=True. Saídas respeitam o flag manual.
                df_edit = df_edit.copy()
                mask_entrada = df_edit['tipo'].astype(str).str.lower() == 'entrada'
                df_edit.loc[mask_entrada, 'Microgasto?'] = False
                st.session_state.df_master = df_edit
                st.success("✅ Dados auditados! Prossiga para a geração dos indicadores.")
        else:
            st.info("Aguardando upload do extrato na aba de Ingestão de Dados (ETL).")

    # --- ABA 3: RESULTADOS E BI ---
    with t3:
        if st.session_state.df_master is not None:
            # Filtra apenas microgastos auditados. Como Microgasto? agora só pode ser True
            # para tipo='saida' E valor<=limite, este filtro já garante que créditos
            # NÃO entram na soma. Isso resolve o bug de "somar tudo do extrato".
            df_m = st.session_state.df_master[st.session_state.df_master['Microgasto?']].copy()
            total_m = df_m['valor'].sum()
            im = (total_m / renda) * 100 if renda > 0 else 0

            engine = SmartFinanceAnalyzer(renda, limite)
            plano_acao = engine.gerar_plano_acao(df_m, im)

            if im <= 5:
                st.success(f"🎯 **Cenário Positivo:** {plano_acao}")
            elif im <= 12:
                st.warning(f"⚠️ **Ponto de Atenção:** {plano_acao}")
            else:
                st.error(f"🚨 **Risco Orçamentário:** {plano_acao}")

            st.markdown('<h4><span class="material-icons">insights</span>Indicadores de Desempenho</h4>', unsafe_allow_html=True)
            c_m1, c_m2 = st.columns(2)
            c_m1.metric("Impacto Acumulado (R$)", f"R$ {total_m:.2f}")
            c_m2.metric("Índice de Microgastos (IM)", f"{im:.2f}%")

            col_g1, col_g2 = st.columns(2)
            with col_g1:
                if not df_m.empty:
                    fig1 = px.pie(df_m, values='valor', names='categoria', hole=0.5,
                                  template="plotly_dark", title="Concentração por Categoria")
                    # AJUSTE VISUAL: fontes maiores no gráfico
                    fig1.update_layout(
                        font=dict(size=15),
                        title_font=dict(size=20),
                        legend=dict(font=dict(size=14))
                    )
                    fig1.update_traces(textfont_size=14)
                    st.plotly_chart(fig1, width="stretch", config={'displayModeBar': False})
                else:
                    st.info("Não há microgastos identificados no período para gerar o gráfico de categorias.")
            with col_g2:

                # --- CRIAÇÃO DO CALENDÁRIO COM O PERÍODO COMPLETO DO EXTRATO ---
                if not df_m.empty:
                    df_m['data'] = pd.to_datetime(df_m['data'], dayfirst=True, errors='coerce')
                    df_m = df_m.dropna(subset=['data'])

                    if not df_m.empty:
                        # 1. Pega dinamicamente a data de início e fim baseada nos dados enviados
                        data_inicio = df_m['data'].min()
                        data_fim = df_m['data'].max()

                        # 2. Cria o calendário contínuo respeitando exatamente as pontas do extrato
                        calendario = pd.date_range(start=data_inicio, end=data_fim, freq='D')

                        # 3. Agrupa todos os gastos por dia exato
                        df_agrupado = df_m.groupby(df_m['data'].dt.date)['valor'].sum()
                        df_agrupado.index = pd.to_datetime(df_agrupado.index)

                        # 4. Injeta no calendário (dias sem gastos viram 0)
                        df_completo = df_agrupado.reindex(calendario, fill_value=0).reset_index()
                        df_completo.columns = ['data', 'valor_diario']

                        # 5. Calcula o acumulado e formata
                        df_completo['valor_acumulado'] = df_completo['valor_diario'].cumsum()
                        df_completo['dia_mes'] = df_completo['data'].dt.strftime('%d/%m')

                        # 6. Gráfico de Colunas dinâmico
                        fig2 = px.bar(
                            df_completo,
                            x='dia_mes',
                            y='valor_acumulado',
                            text='valor_acumulado',
                            template="plotly_dark",
                            title=f"Crescimento Acumulado ({data_inicio.strftime('%d/%m/%Y')} a {data_fim.strftime('%d/%m/%Y')})"
                        )

                        # AJUSTE VISUAL: rótulos das barras maiores
                        fig2.update_traces(
                            texttemplate='%{text:.2f}',
                            textposition='outside',
                            cliponaxis=False,
                            textfont=dict(size=13)
                        )

                        # AJUSTE VISUAL: fontes maiores em título, eixos e tick labels
                        fig2.update_layout(
                            dragmode=False,
                            bargap=0.2,
                            font=dict(size=15),
                            title_font=dict(size=20),
                            xaxis=dict(type='category', title="Dias do Extrato",
                                       tickfont=dict(size=13), title_font=dict(size=15)),
                            yaxis=dict(title="Impacto Acumulado (R$)",
                                       tickfont=dict(size=13), title_font=dict(size=15))
                        )

                        st.plotly_chart(fig2, width="stretch", config={'displayModeBar': False})
                else:
                    st.info("Não há dados de microgastos para gerar o gráfico.")

            st.divider()

            st.markdown('<h4><span class="material-icons">history</span>Evolução Mensal (Filtro Dinâmico)</h4>', unsafe_allow_html=True)
            df_hist = buscar_historico_supabase(st.session_state.user.id)

            if not df_hist.empty:
                # CORREÇÃO defensiva: se o banco tiver a coluna 'Microgasto?'
                # persistida, considera apenas os microgastos no somatório mensal.
                # (Nova persistência já entrega só microgastos, mas registros antigos
                # podem ter vindo com todas as transações; este filtro protege o gráfico.)
                if 'Microgasto?' in df_hist.columns:
                    df_hist = df_hist[df_hist['Microgasto?'] == True].copy()

                df_hist['mes_ano'] = df_hist['data'].dt.strftime('%m/%Y')
                res_mensal = df_hist.groupby('mes_ano')['valor'].sum().reset_index()

                filtros = st.multiselect("Selecionar meses para comparação:", options=res_mensal['mes_ano'].unique())
                df_final = res_mensal[res_mensal['mes_ano'].isin(filtros)] if filtros else res_mensal

                fig3 = px.bar(df_final, x='mes_ano', y='valor', text='valor', template="plotly_dark")
                # AJUSTE VISUAL: rótulos das barras
                fig3.update_traces(
                    texttemplate='R$ %{text:.2f}',
                    textposition='outside',
                    textfont=dict(size=14)
                )
                # AJUSTE VISUAL: fontes maiores nos eixos e no corpo
                fig3.update_layout(
                    dragmode=False,
                    font=dict(size=15),
                    xaxis=dict(title="", tickfont=dict(size=13)),
                    yaxis=dict(title="Impacto Financeiro (R$)",
                               tickfont=dict(size=13), title_font=dict(size=15))
                )
                st.plotly_chart(fig3, width="stretch", config={'displayModeBar': False})
            else:
                st.info("Nenhum histórico salvo na nuvem para realizar comparações.")

            st.write("<br>", unsafe_allow_html=True)
            if st.button("Persistir Dados na Nuvem", type="primary", width="stretch"):
                # CORREÇÃO: só persistir as linhas efetivamente marcadas como microgasto.
                # Antes, era passado o DataFrame inteiro, o que fazia o banco armazenar
                # todas as transações e inflava o gráfico de Evolução Mensal.
                df_para_salvar = st.session_state.df_master[
                    st.session_state.df_master['Microgasto?'] == True
                ].copy()
                if df_para_salvar.empty:
                    st.warning("Não há microgastos auditados para sincronizar.")
                elif salvar_microgastos_supabase(df_para_salvar, st.session_state.user.id):
                    st.success(f"Sincronizados {len(df_para_salvar)} microgastos no Supabase.")
                    st.balloons()
