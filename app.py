import streamlit as st
import plotly.express as px
import pandas as pd
from analyzer import SmartFinanceAnalyzer
from database import (
    registrar_usuario, login_usuario, logout_usuario,
    salvar_microgastos_supabase, buscar_historico_supabase
)

# Import defensivo da função NOVA de reset de senha.
# Caso o database.py ainda não tenha sido atualizado, o site continua funcionando
# no modo tradicional (sem a opção "Esqueci minha senha"), sem quebrar.
try:
    from database import enviar_reset_senha
    RESET_DISPONIVEL = True
except ImportError:
    RESET_DISPONIVEL = False

# ==========================================
# 1. CONFIGURAÇÃO INICIAL
# ==========================================
st.set_page_config(page_title="SDM Analytics", page_icon="📊", layout="wide")

# --- Estado inicial ---
if 'user' not in st.session_state: st.session_state.user = None
if 'df_master' not in st.session_state: st.session_state.df_master = None
if 'perfil_configurado' not in st.session_state: st.session_state.perfil_configurado = False
if 'theme' not in st.session_state: st.session_state.theme = 'dark'  # padrão: escuro
if 'reset_enviado' not in st.session_state: st.session_state.reset_enviado = False
if 'cadastro_sucesso_email' not in st.session_state: st.session_state.cadastro_sucesso_email = None

# Resolve troca de modo pendente (agendada em um rerun anterior) ANTES do
# widget de rádio "Selecione o acesso" ser instanciado nesta execução.
# Isso evita o erro do Streamlit "valor não pode ser alterado após o
# widget ser instanciado", que ocorreria se tentássemos mudar o modo
# DEPOIS de o rádio já ter sido desenhado na mesma rodada.
if 'pending_auth_mode' in st.session_state:
    st.session_state.auth_radio = st.session_state.pop('pending_auth_mode')

# ==========================================
# 1.1 TEMA NATIVO DO STREAMLIT
# ==========================================
# Além do CSS abaixo (que cobre nossos elementos customizados), aplicamos
# o tema oficial do Streamlit via API de configuração. Isso é necessário
# porque alguns componentes (data_editor, dropdown de multiselect, ícone
# de mostrar/ocultar senha) são desenhados internamente usando o tema
# "de verdade" do Streamlit — CSS puro não alcança essas partes.
# Envolto em try/except: se essa API interna mudar em versão futura do
# Streamlit, o app continua funcionando normalmente (só com o CSS abaixo).
try:
    from streamlit import config as _st_config
    if st.session_state.theme == 'light':
        _st_config.set_option('theme.base', 'light')
        _st_config.set_option('theme.backgroundColor', '#ffffff')
        _st_config.set_option('theme.secondaryBackgroundColor', '#f1f5f9')
        _st_config.set_option('theme.textColor', '#0f172a')
        _st_config.set_option('theme.primaryColor', '#FF4B4B')
    else:
        _st_config.set_option('theme.base', 'dark')
        _st_config.set_option('theme.backgroundColor', '#0e1117')
        _st_config.set_option('theme.secondaryBackgroundColor', '#1e293b')
        _st_config.set_option('theme.textColor', '#f8fafc')
        _st_config.set_option('theme.primaryColor', '#FF4B4B')
except Exception:
    pass


# ==========================================
# 2. TEMA — CSS DINÂMICO
# ==========================================
def gerar_css(tema='dark'):
    """Gera o bloco de CSS de acordo com o tema selecionado.
    Escuro (padrão) mantém a paleta atual do sistema.
    Claro usa uma paleta acadêmica/editorial (fundo branco, cinzas frios).
    O CSS força cores em TODOS os componentes Streamlit para garantir
    contraste adequado em ambos os temas — não só no fundo."""
    if tema == 'dark':
        cores = {
            'bg':          '#0e1117',
            'text':        '#f8fafc',
            'text_head':   '#ffffff',
            'text_muted':  '#cbd5e1',
            'card':        '#1e293b',
            'card_border': '#334155',
            'input_bg':    '#0f172a',
            'input_text':  '#f8fafc',
            'accent':      '#3b82f6',
            'guia_bg':     '#1e293b',
            'shadow':      '0 4px 6px rgba(0,0,0,0.2)',
            'btn_sec_bg':      '#1e293b',
            'btn_sec_text':    '#f8fafc',
            'btn_sec_border':  '#334155',
            'plotly_bg':       '#0e1117',
            'plotly_text':     '#f8fafc',
        }
    else:
        cores = {
            'bg':          '#ffffff',
            'text':        '#0f172a',
            'text_head':   '#0f172a',
            'text_muted':  '#475569',
            'card':        '#f8fafc',
            'card_border': '#e2e8f0',
            'input_bg':    '#ffffff',
            'input_text':  '#0f172a',
            'accent':      '#2563eb',
            'guia_bg':     '#f1f5f9',
            'shadow':      '0 2px 4px rgba(15,23,42,0.08)',
            'btn_sec_bg':      '#f1f5f9',
            'btn_sec_text':    '#0f172a',
            'btn_sec_border':  '#cbd5e1',
            'plotly_bg':       '#ffffff',
            'plotly_text':     '#0f172a',
        }
    return f"""
    <link href="https://fonts.googleapis.com/icon?family=Material+Icons" rel="stylesheet">
    <style>
        /* ===== BASE ===== */
        .stApp {{
            background-color: {cores['bg']};
            color: {cores['text']};
            font-family: 'Inter', sans-serif;
            font-size: 16px;
        }}
        h1, h2, h3, h4, h5, h6, label, p, span, li {{ color: {cores['text_head']} !important; }}

        .stMarkdown p, .stMarkdown li, .stMarkdown span {{
            color: {cores['text']} !important;
            font-size: 1.05rem;
            line-height: 1.6;
        }}
        label {{ font-size: 1.05rem !important; font-weight: 500 !important; color: {cores['text']} !important; }}

        /* ===== RADIO BUTTONS ===== */
        .stRadio label,
        .stRadio [role="radiogroup"] label,
        .stRadio [role="radiogroup"] label > div,
        .stRadio [role="radiogroup"] label p,
        div[data-baseweb="radio"] label {{
            color: {cores['text']} !important;
        }}

        /* ===== ABAS ===== */
        .stTabs [data-baseweb="tab-list"] {{ gap: 24px; border-bottom: 2px solid {cores['card_border']}; }}
        .stTabs [data-baseweb="tab-list"] button {{
            font-size: 1.05rem !important;
            font-weight: 500 !important;
            color: {cores['text_muted']} !important;
        }}
        .stTabs [data-baseweb="tab-list"] button p {{
            color: {cores['text_muted']} !important;
        }}
        .stTabs [data-baseweb="tab-list"] button[aria-selected="true"],
        .stTabs [data-baseweb="tab-list"] button[aria-selected="true"] p,
        .stTabs [aria-selected="true"] {{
            color: {cores['accent']} !important;
            border-bottom-color: {cores['accent']} !important;
        }}

        /* ===== INPUTS (text, number, password) ===== */
        .stTextInput input,
        .stNumberInput input,
        .stTextArea textarea,
        [data-baseweb="input"] input,
        [data-baseweb="base-input"] input {{
            background-color: {cores['input_bg']} !important;
            color: {cores['input_text']} !important;
        }}
        .stTextInput div[data-baseweb="input"],
        .stNumberInput div[data-baseweb="input"] {{
            background-color: {cores['input_bg']} !important;
            border-color: {cores['card_border']} !important;
        }}
        /* Botões +/- do number input */
        .stNumberInput button {{
            background-color: {cores['btn_sec_bg']} !important;
            color: {cores['btn_sec_text']} !important;
        }}

        /* ===== BOTÕES ===== */
        .stButton button {{
            font-size: 1.02rem !important;
            font-weight: 500 !important;
        }}
        /* Botão secundário (padrão) */
        .stButton button[kind="secondary"],
        .stButton button:not([kind="primary"]) {{
            background-color: {cores['btn_sec_bg']} !important;
            color: {cores['btn_sec_text']} !important;
            border: 1px solid {cores['btn_sec_border']} !important;
        }}
        /* Botão primário — sempre texto branco (fundo vermelho do Streamlit) */
        .stButton button[kind="primary"] {{
            color: #ffffff !important;
        }}
        .stButton button[kind="primary"] p {{
            color: #ffffff !important;
        }}

        /* ===== MÉTRICAS ===== */
        div[data-testid="stMetric"] {{
            background-color: {cores['card']};
            padding: 28px;
            border-radius: 12px;
            border: 1px solid {cores['card_border']};
            box-shadow: {cores['shadow']};
        }}
        div[data-testid="stMetricLabel"],
        div[data-testid="stMetricLabel"] p {{
            font-size: 1.1rem !important;
            font-weight: 500 !important;
            color: {cores['text']} !important;
        }}
        div[data-testid="stMetricValue"] {{
            font-size: 2.4rem !important;
            font-weight: 600 !important;
            color: {cores['text_head']} !important;
        }}
        div[data-testid="stMetricValue"] > div {{
            color: {cores['text_head']} !important;
        }}

        /* ===== FILE UPLOADER ===== */
        [data-testid="stFileUploaderDropzone"] {{
            background-color: {cores['card']} !important;
            border-color: {cores['card_border']} !important;
        }}
        [data-testid="stFileUploaderDropzone"] * {{
            color: {cores['text']} !important;
        }}
        [data-testid="stFileUploader"] button {{
            background-color: {cores['btn_sec_bg']} !important;
            color: {cores['btn_sec_text']} !important;
        }}

        /* ===== ALERTS (info, success, warning, error) ===== */
        [data-testid="stAlert"] {{
            font-size: 1.05rem !important;
        }}
        [data-testid="stAlert"] *,
        [data-testid="stAlert"] p,
        [data-testid="stAlert"] div,
        [data-testid="stAlert"] span {{
            color: {cores['text']} !important;
        }}
        /* Preserva a cor dos ícones e destaques dentro dos alerts */
        [data-testid="stAlert"] strong {{
            color: {cores['text_head']} !important;
        }}

        /* ===== SELECTBOX / MULTISELECT ===== */
        .stSelectbox [data-baseweb="select"],
        .stMultiSelect [data-baseweb="select"] {{
            background-color: {cores['input_bg']} !important;
        }}
        .stSelectbox [data-baseweb="select"] *,
        .stMultiSelect [data-baseweb="select"] * {{
            color: {cores['input_text']} !important;
        }}

        /* ===== TABELAS E DATA EDITOR ===== */
        [data-testid="stTable"] {{ background-color: {cores['card']}; border-radius: 8px; }}
        [data-testid="stDataFrame"] {{
            font-size: 1rem !important;
        }}
        [data-testid="stDataFrame"] * {{
            color: {cores['text']} !important;
        }}

        /* ===== DIVIDER ===== */
        hr {{ border-color: {cores['card_border']} !important; }}

        /* ===== ÍCONES MATERIAL ===== */
        .material-icons {{ vertical-align: middle; margin-right: 10px; color: {cores['accent']}; }}

        /* ===== CAIXAS DE GUIA (custom) ===== */
        .caixa-guia {{
            background-color: {cores['guia_bg']};
            padding: 20px 24px;
            border-radius: 8px;
            margin-bottom: 24px;
            border-left: 4px solid {cores['accent']};
            font-size: 1.05rem;
            line-height: 1.6;
            color: {cores['text']};
        }}
        .caixa-guia strong, .caixa-guia b {{
            color: {cores['text_head']};
        }}

        /* ===== LINKS ===== */
        a {{ color: {cores['accent']} !important; }}

        /* ===== FILE UPLOADER — nome do arquivo enviado ===== */
        [data-testid="stFileUploaderFile"],
        [data-testid="stFileUploaderFile"] *,
        [data-testid="stFileUploaderFile"] small,
        [data-testid="stFileUploader"] > section > div small,
        [data-testid="stFileUploaderDeleteBtn"] {{
            color: {cores['text']} !important;
        }}

        /* ===== BOTÕES DENTRO DE INPUTS (olho da senha, +/- number) ===== */
        [data-baseweb="input"] button,
        [data-baseweb="base-input"] button,
        div[data-baseweb="input"] > div > button {{
            background-color: {cores['btn_sec_bg']} !important;
            color: {cores['btn_sec_text']} !important;
            border-color: {cores['btn_sec_border']} !important;
        }}
        [data-baseweb="input"] button svg,
        [data-baseweb="input"] button * {{
            fill: {cores['btn_sec_text']} !important;
            color: {cores['btn_sec_text']} !important;
        }}

        /* ===== DATA EDITOR (glide-data-grid) — usa CSS variables próprias ===== */
        [data-testid="stDataFrame"],
        [data-testid="stDataFrameResizable"] {{
            --gdg-bg-cell: {cores['input_bg']};
            --gdg-bg-cell-medium: {cores['card']};
            --gdg-bg-header: {cores['card']};
            --gdg-bg-header-has-focus: {cores['card_border']};
            --gdg-bg-header-hovered: {cores['card_border']};
            --gdg-text-dark: {cores['input_text']};
            --gdg-text-medium: {cores['text_muted']};
            --gdg-text-light: {cores['text_muted']};
            --gdg-text-bubble: {cores['input_text']};
            --gdg-bg-bubble: {cores['card']};
            --gdg-bg-bubble-selected: {cores['accent']};
            --gdg-text-header: {cores['text_head']};
            --gdg-text-header-selected: {cores['text_head']};
            --gdg-text-group-header: {cores['text_head']};
            --gdg-border-color: {cores['card_border']};
            --gdg-drilldown-border: {cores['card_border']};
            --gdg-header-bottom-border-color: {cores['card_border']};
            --gdg-horizontal-border-color: {cores['card_border']};
            --gdg-accent-color: {cores['accent']};
            --gdg-accent-light: {cores['guia_bg']};
            background-color: {cores['input_bg']} !important;
        }}

        /* ===== CURSOR (caret) NOS CAMPOS DE TEXTO =====
           No modo claro, o cursor piscante podia herdar cor clara e
           ficar invisível sobre fundo branco. Forçamos a cor do texto. */
        input, textarea {{
            caret-color: {cores['input_text']} !important;
        }}

        /* ===== SELECTBOX / MULTISELECT — CAIXA FECHADA =====
           Reforço adicional (além do bloco acima) para garantir que a
           caixa fechada (antes de abrir o menu) tenha fundo e texto
           corretos, inclusive o placeholder ("Choose options"). */
        div[data-baseweb="select"] > div {{
            background-color: {cores['input_bg']} !important;
            border-color: {cores['card_border']} !important;
        }}
        div[data-baseweb="select"] > div * {{
            color: {cores['input_text']} !important;
        }}
        div[data-baseweb="select"] [class*="placeholder"] {{
            color: {cores['text_muted']} !important;
        }}

        /* ===== MENU/POPOVER (opções abertas do select e multiselect) =====
           Esses menus são renderizados em um portal FORA do container
           principal da página — por isso os seletores aqui são globais,
           sem prefixo de container, para conseguir alcançá-los. */
        div[data-baseweb="popover"] div[data-baseweb="menu"],
        ul[data-baseweb="menu"],
        div[data-baseweb="menu"] {{
            background-color: {cores['input_bg']} !important;
        }}
        li[role="option"],
        div[role="option"] {{
            background-color: {cores['input_bg']} !important;
            color: {cores['input_text']} !important;
        }}
        li[role="option"]:hover,
        div[role="option"]:hover,
        li[aria-selected="true"] {{
            background-color: {cores['guia_bg']} !important;
        }}
        /* Chips das opções já selecionadas no multiselect */
        span[data-baseweb="tag"] {{
            background-color: {cores['accent']} !important;
        }}
        span[data-baseweb="tag"] span {{
            color: #ffffff !important;
        }}
    </style>
    """

st.markdown(gerar_css(st.session_state.theme), unsafe_allow_html=True)

# Template e cores dos gráficos Plotly mudam junto com o tema
if st.session_state.theme == 'dark':
    plotly_template = "plotly_dark"
    plotly_bg = "#0e1117"
    plotly_text = "#f8fafc"
else:
    plotly_template = "plotly_white"
    plotly_bg = "#ffffff"
    plotly_text = "#0f172a"


def toggle_tema_btn(key_suffix=""):
    """Renderiza o botão de alternar tema. Chama st.rerun() para aplicar."""
    label = "☀️ Modo Claro" if st.session_state.theme == 'dark' else "🌙 Modo Escuro"
    if st.button(label, key=f"toggle_tema_{key_suffix}", width="stretch"):
        st.session_state.theme = 'light' if st.session_state.theme == 'dark' else 'dark'
        st.rerun()


def calcular_microgasto(df, limite):
    """Determina o flag 'Microgasto?' considerando DUAS condições:
    (1) é uma SAÍDA de caixa (tipo == 'saida')
    (2) o valor está abaixo do threshold definido pelo usuário
    Entradas (créditos, PIX recebido, estorno, etc.) NUNCA são microgastos."""
    if 'tipo' not in df.columns:
        df['tipo'] = 'saida'
    return (df['valor'] <= limite) & (df['tipo'].astype(str).str.lower() == 'saida')


# ==========================================
# 3. FLUXO DE ACESSO (TELA DE LOGIN)
# ==========================================
if st.session_state.user is None:
    st.write("<br><br>", unsafe_allow_html=True)
    c1, col_auth, c2 = st.columns([1, 1.5, 1])

    with col_auth:
        # Toggle de tema no topo da tela de login
        c_top1, c_top2 = st.columns([3, 1])
        with c_top2:
            toggle_tema_btn("login")

        st.markdown('<h1><span class="material-icons" style="font-size: 40px;">shield</span>SDM Analytics</h1>', unsafe_allow_html=True)
        st.write("Sistema de Detecção de Microgastos | Autenticação")
        st.divider()

        # Radio de modo — inclui "Esqueci minha senha" se a função estiver disponível
        opcoes_modo = ["Acessar Sistema", "Novo Cadastro"]
        if RESET_DISPONIVEL:
            opcoes_modo.append("Esqueci minha senha")

        if 'auth_radio' not in st.session_state:
            st.session_state.auth_radio = "Acessar Sistema"

        modo = st.radio("Selecione o acesso:", opcoes_modo, horizontal=True, key="auth_radio")
        st.write("<br>", unsafe_allow_html=True)

        # =============================================
        # FLUXO: LOGIN COM SENHA
        # =============================================
        if modo == "Acessar Sistema":
            # Mensagem persistente após um cadastro bem-sucedido
            if st.session_state.cadastro_sucesso_email:
                st.success(
                    "✅ Conta criada! Verifique o e-mail "
                    f"**{st.session_state.cadastro_sucesso_email}** e clique no link de "
                    "confirmação antes de entrar."
                )

            # st.form permite submissão pressionando Enter em qualquer campo
            with st.form("form_login", clear_on_submit=False):
                email = st.text_input("E-mail corporativo", key="login_email")
                senha = st.text_input("Senha", type="password", key="login_senha")
                entrar = st.form_submit_button("Autenticar", type="primary", width="stretch")

            if entrar:
                with st.spinner("Conectando..."):
                    user, erro = login_usuario(email, senha)
                    if user:
                        st.session_state.user = user
                        st.session_state.cadastro_sucesso_email = None
                        st.rerun()
                    else:
                        st.error(erro)

        # =============================================
        # FLUXO: CADASTRO (com confirmação por e-mail)
        # =============================================
        elif modo == "Novo Cadastro":
            # clear_on_submit=True limpa e-mail/senha automaticamente após o envio
            with st.form("form_cadastro", clear_on_submit=True):
                email_cad = st.text_input("E-mail corporativo", key="cadastro_email")
                senha_cad = st.text_input("Senha", type="password", key="cadastro_senha")
                st.info(
                    "🔒 Ao clicar em **Registrar Credenciais**, um e-mail de confirmação será "
                    "enviado. Você precisa clicar no link do e-mail antes de conseguir acessar "
                    "o sistema."
                )
                registrar = st.form_submit_button("Registrar Credenciais", type="primary", width="stretch")

            if registrar:
                with st.spinner("Criando conta..."):
                    user, erro = registrar_usuario(email_cad, senha_cad)
                    if user:
                        # Guarda o e-mail para exibir a confirmação na tela de login,
                        # agenda a troca de modo (resolvida no topo do script, antes
                        # do rádio ser recriado) e recarrega a página já na tela de login.
                        st.session_state.cadastro_sucesso_email = email_cad
                        st.session_state.pending_auth_mode = "Acessar Sistema"
                        st.rerun()
                    else:
                        st.error(erro)

        # =============================================
        # FLUXO: ESQUECI MINHA SENHA
        # =============================================
        elif modo == "Esqueci minha senha":
            if not st.session_state.reset_enviado:
                with st.form("form_reset", clear_on_submit=False):
                    email_reset = st.text_input("E-mail corporativo cadastrado", key="reset_email")
                    st.info(
                        "🔐 Enviaremos um **link de redefinição** para o seu e-mail. Basta "
                        "clicar no link, definir uma nova senha e voltar aqui para acessar "
                        "o sistema."
                    )
                    enviar = st.form_submit_button("Enviar link de redefinição", type="primary", width="stretch")

                if enviar:
                    if not email_reset:
                        st.error("Informe seu e-mail para receber o link.")
                    else:
                        with st.spinner("Enviando link de redefinição..."):
                            ok, erro = enviar_reset_senha(email_reset)
                            if ok:
                                st.session_state.reset_enviado = True
                                st.rerun()
                            else:
                                st.error(f"Falha ao enviar: {erro}")
            else:
                st.success(
                    "✅ **Link enviado!** Verifique sua caixa de entrada (e a pasta de spam). "
                    "Após redefinir sua senha, volte aqui e faça o login pela opção 'Acessar Sistema'."
                )
                if st.button("Voltar ao login", width="stretch"):
                    st.session_state.reset_enviado = False
                    st.session_state.pending_auth_mode = "Acessar Sistema"
                    st.rerun()

# ==========================================
# 4. APLICATIVO PRINCIPAL (DASHBOARD)
# ==========================================
else:
    c_h1, c_h2, c_h3 = st.columns([4, 1, 1])
    with c_h1:
        st.markdown('<h2><span class="material-icons" style="font-size: 32px;">analytics</span>Dashboard de BI</h2>', unsafe_allow_html=True)
        st.write(f"Sessão autenticada: **{st.session_state.user.email}**")
    with c_h2:
        st.write("<br>", unsafe_allow_html=True)
        toggle_tema_btn("dashboard")
    with c_h3:
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
                                  template=plotly_template, title="Concentração por Categoria")
                    fig1.update_layout(
                        paper_bgcolor=plotly_bg,
                        plot_bgcolor=plotly_bg,
                        font=dict(size=15, color=plotly_text),
                        title_font=dict(size=20, color=plotly_text),
                        legend=dict(font=dict(size=14, color=plotly_text))
                    )
                    fig1.update_traces(textfont_size=14)
                    st.plotly_chart(fig1, width="stretch", config={'displayModeBar': False})
                else:
                    st.info("Não há microgastos identificados no período para gerar o gráfico de categorias.")
            with col_g2:
                if not df_m.empty:
                    df_m['data'] = pd.to_datetime(df_m['data'], dayfirst=True, errors='coerce')
                    df_m = df_m.dropna(subset=['data'])

                    if not df_m.empty:
                        data_inicio = df_m['data'].min()
                        data_fim = df_m['data'].max()
                        calendario = pd.date_range(start=data_inicio, end=data_fim, freq='D')
                        df_agrupado = df_m.groupby(df_m['data'].dt.date)['valor'].sum()
                        df_agrupado.index = pd.to_datetime(df_agrupado.index)
                        df_completo = df_agrupado.reindex(calendario, fill_value=0).reset_index()
                        df_completo.columns = ['data', 'valor_diario']
                        df_completo['valor_acumulado'] = df_completo['valor_diario'].cumsum()
                        df_completo['dia_mes'] = df_completo['data'].dt.strftime('%d/%m')

                        fig2 = px.bar(
                            df_completo,
                            x='dia_mes',
                            y='valor_acumulado',
                            text='valor_acumulado',
                            template=plotly_template,
                            title=f"Crescimento Acumulado ({data_inicio.strftime('%d/%m/%Y')} a {data_fim.strftime('%d/%m/%Y')})"
                        )
                        fig2.update_traces(
                            texttemplate='%{text:.2f}',
                            textposition='outside',
                            cliponaxis=False,
                            textfont=dict(size=13)
                        )
                        fig2.update_layout(
                            dragmode=False,
                            bargap=0.2,
                            paper_bgcolor=plotly_bg,
                            plot_bgcolor=plotly_bg,
                            font=dict(size=15, color=plotly_text),
                            title_font=dict(size=20, color=plotly_text),
                            xaxis=dict(type='category', title="Dias do Extrato",
                                       tickfont=dict(size=13, color=plotly_text),
                                       title_font=dict(size=15, color=plotly_text)),
                            yaxis=dict(title="Impacto Acumulado (R$)",
                                       tickfont=dict(size=13, color=plotly_text),
                                       title_font=dict(size=15, color=plotly_text))
                        )
                        st.plotly_chart(fig2, width="stretch", config={'displayModeBar': False})
                else:
                    st.info("Não há dados de microgastos para gerar o gráfico.")

            st.divider()

            st.markdown('<h4><span class="material-icons">history</span>Evolução Mensal (Filtro Dinâmico)</h4>', unsafe_allow_html=True)
            df_hist = buscar_historico_supabase(st.session_state.user.id)

            if not df_hist.empty:
                if 'Microgasto?' in df_hist.columns:
                    df_hist = df_hist[df_hist['Microgasto?'] == True].copy()

                df_hist['mes_ano'] = df_hist['data'].dt.strftime('%m/%Y')
                res_mensal = df_hist.groupby('mes_ano')['valor'].sum().reset_index()

                filtros = st.multiselect("Selecionar meses para comparação:", options=res_mensal['mes_ano'].unique())
                df_final = res_mensal[res_mensal['mes_ano'].isin(filtros)] if filtros else res_mensal

                fig3 = px.bar(df_final, x='mes_ano', y='valor', text='valor', template=plotly_template)
                fig3.update_traces(
                    texttemplate='R$ %{text:.2f}',
                    textposition='outside',
                    textfont=dict(size=14)
                )
                fig3.update_layout(
                    dragmode=False,
                    paper_bgcolor=plotly_bg,
                    plot_bgcolor=plotly_bg,
                    font=dict(size=15, color=plotly_text),
                    xaxis=dict(title="", tickfont=dict(size=13, color=plotly_text)),
                    yaxis=dict(title="Impacto Financeiro (R$)",
                               tickfont=dict(size=13, color=plotly_text),
                               title_font=dict(size=15, color=plotly_text))
                )
                st.plotly_chart(fig3, width="stretch", config={'displayModeBar': False})
            else:
                st.info("Nenhum histórico salvo na nuvem para realizar comparações.")

            st.write("<br>", unsafe_allow_html=True)
            if st.button("Persistir Dados na Nuvem", type="primary", width="stretch"):
                df_para_salvar = st.session_state.df_master[
                    st.session_state.df_master['Microgasto?'] == True
                ].copy()
                if df_para_salvar.empty:
                    st.warning("Não há microgastos auditados para sincronizar.")
                elif salvar_microgastos_supabase(df_para_salvar, st.session_state.user.id):
                    st.success(f"Sincronizados {len(df_para_salvar)} microgastos no Supabase.")
                    st.balloons()
