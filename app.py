import logging
import re

import plotly.express as px
import streamlit as st

from analyzer import CATEGORIAS, COLUNA_MICROGASTO, TIPOS_FLUXO, SmartFinanceAnalyzer
from database import (
    atualizar_perfil_usuario, buscar_historico_supabase, buscar_perfil_usuario,
    enviar_reset_senha, excluir_conta, login_usuario, logout_usuario,
    registrar_usuario, salvar_microgastos_supabase,
)

log = logging.getLogger(__name__)

st.set_page_config(page_title="SDM Analytics", page_icon="📊", layout="wide")

ESTADO_INICIAL = {
    'user': None,
    'df_master': None,
    'historico': None,
    'perfil_configurado': False,
    'renda_salva': 5000.0,
    'threshold_salvo': 50.0,
    'arquivo_processado_assinatura': None,
    'dados_persistidos': False,
    'reset_enviado': False,
    'cadastro_sucesso_email': None,
    'aviso_persistencia': None,
    'feedback_config': None,
}

CAMPOS_CONFIGURACAO = ('renda_texto', 'limite_texto')

NIVEIS_RISCO = {
    'positivo': ('🎯', 'Cenário Positivo'),
    'atencao': ('⚠️', 'Ponto de Atenção'),
    'risco': ('🚨', 'Risco Orçamentário'),
}

PALETAS = {
    'dark': {
        'bg': '#0e1117', 'text': '#f8fafc', 'text_head': '#ffffff', 'text_muted': '#cbd5e1',
        'card': '#1e293b', 'card_border': '#334155', 'input_bg': '#0f172a', 'input_text': '#f8fafc',
        'accent': '#3b82f6', 'guia_bg': '#1e293b', 'shadow': '0 4px 6px rgba(0,0,0,0.2)',
        'btn_sec_bg': '#1e293b', 'btn_sec_text': '#f8fafc', 'btn_sec_border': '#334155',
        'fb_positivo_bg': 'rgba(16, 185, 129, 0.12)', 'fb_positivo_border': '#10b981',
        'fb_atencao_bg': 'rgba(245, 158, 11, 0.12)', 'fb_atencao_border': '#f59e0b',
        'fb_risco_bg': 'rgba(239, 68, 68, 0.14)', 'fb_risco_border': '#ef4444',
    },
    'light': {
        'bg': '#ffffff', 'text': '#0f172a', 'text_head': '#0f172a', 'text_muted': '#475569',
        'card': '#f8fafc', 'card_border': '#e2e8f0', 'input_bg': '#ffffff', 'input_text': '#0f172a',
        'accent': '#2563eb', 'guia_bg': '#f1f5f9', 'shadow': '0 2px 4px rgba(15,23,42,0.08)',
        'btn_sec_bg': '#f1f5f9', 'btn_sec_text': '#0f172a', 'btn_sec_border': '#cbd5e1',
        'fb_positivo_bg': 'rgba(16, 185, 129, 0.08)', 'fb_positivo_border': '#059669',
        'fb_atencao_bg': 'rgba(245, 158, 11, 0.10)', 'fb_atencao_border': '#d97706',
        'fb_risco_bg': 'rgba(239, 68, 68, 0.08)', 'fb_risco_border': '#dc2626',
    },
}

TEMA_NATIVO = {
    'light': {
        'theme.base': 'light', 'theme.backgroundColor': '#ffffff',
        'theme.secondaryBackgroundColor': '#f1f5f9', 'theme.textColor': '#0f172a',
        'theme.primaryColor': '#FF4B4B',
    },
    'dark': {
        'theme.base': 'dark', 'theme.backgroundColor': '#0e1117',
        'theme.secondaryBackgroundColor': '#1e293b', 'theme.textColor': '#f8fafc',
        'theme.primaryColor': '#FF4B4B',
    },
}

PLOTLY = {
    'dark': {'template': 'plotly_dark', 'fundo': '#0e1117', 'texto': '#f8fafc'},
    'light': {'template': 'plotly_white', 'fundo': '#ffffff', 'texto': '#0f172a'},
}

PADRAO_BRASILEIRO = re.compile(r'^(\d{1,3}(\.\d{3})+|\d+)(,\d{1,2})?$')


def formatar_numero(valor, casas=2):
    texto = f"{valor:,.{casas}f}"
    return texto.replace(',', '#').replace('.', ',').replace('#', '.')


def formatar_moeda(valor):
    return f"R$ {formatar_numero(valor)}"


def formatar_percentual(valor, casas=2):
    return f"{formatar_numero(valor, casas)}%"


def ler_valor_brasileiro(texto):
    limpo = texto.replace('R$', '').replace(' ', '')
    if not PADRAO_BRASILEIRO.match(limpo):
        return None
    return float(limpo.replace('.', '').replace(',', '.'))


def inicializar_estado():
    for chave, valor in ESTADO_INICIAL.items():
        st.session_state.setdefault(chave, valor)
    st.session_state.setdefault('theme', 'dark')


def limpar_sessao():
    for chave, valor in ESTADO_INICIAL.items():
        st.session_state[chave] = valor
    for chave in CAMPOS_CONFIGURACAO:
        st.session_state.pop(chave, None)


def preencher_campos_configuracao():
    st.session_state.renda_texto = formatar_numero(st.session_state.renda_salva)
    st.session_state.limite_texto = formatar_numero(st.session_state.threshold_salvo)


def aplicar_tema_nativo():
    try:
        from streamlit import config
        for opcao, valor in TEMA_NATIVO[st.session_state.theme].items():
            config.set_option(opcao, valor)
    except Exception:
        log.debug("Não foi possível aplicar o tema nativo do Streamlit", exc_info=True)


def gerar_css(tema):
    cores = PALETAS[tema]
    return f"""
    <link href="https://fonts.googleapis.com/icon?family=Material+Icons" rel="stylesheet">
    <style>
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

        .stRadio label,
        .stRadio [role="radiogroup"] label,
        .stRadio [role="radiogroup"] label > div,
        .stRadio [role="radiogroup"] label p,
        div[data-baseweb="radio"] label {{
            color: {cores['text']} !important;
        }}

        .stTabs [data-baseweb="tab-list"] {{ gap: 24px; border-bottom: 2px solid {cores['card_border']}; }}
        .stTabs [data-baseweb="tab-list"] button {{
            font-size: 1.05rem !important;
            font-weight: 500 !important;
            color: {cores['text_muted']} !important;
        }}
        .stTabs [data-baseweb="tab-list"] button p {{ color: {cores['text_muted']} !important; }}
        .stTabs [data-baseweb="tab-list"] button[aria-selected="true"],
        .stTabs [data-baseweb="tab-list"] button[aria-selected="true"] p,
        .stTabs [aria-selected="true"] {{
            color: {cores['accent']} !important;
            border-bottom-color: {cores['accent']} !important;
        }}

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
        .stNumberInput button {{
            background-color: {cores['btn_sec_bg']} !important;
            color: {cores['btn_sec_text']} !important;
        }}
        input, textarea {{ caret-color: {cores['input_text']} !important; }}
        [data-testid="InputInstructions"] {{ display: none !important; }}

        .stButton button {{ font-size: 1.02rem !important; font-weight: 500 !important; }}
        .stButton button[kind="secondary"],
        .stButton button:not([kind="primary"]) {{
            background-color: {cores['btn_sec_bg']} !important;
            color: {cores['btn_sec_text']} !important;
            border: 1px solid {cores['btn_sec_border']} !important;
        }}
        .stButton button[kind="primary"],
        .stButton button[kind="primary"] p {{ color: #ffffff !important; }}

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
        div[data-testid="stMetricValue"] > div {{ color: {cores['text_head']} !important; }}

        [data-testid="stFileUploaderDropzone"] {{
            background-color: {cores['card']} !important;
            border-color: {cores['card_border']} !important;
        }}
        [data-testid="stFileUploaderDropzone"] * {{ color: {cores['text']} !important; }}
        [data-testid="stFileUploader"] button {{
            background-color: {cores['btn_sec_bg']} !important;
            color: {cores['btn_sec_text']} !important;
        }}
        [data-testid="stFileUploaderFile"],
        [data-testid="stFileUploaderFile"] *,
        [data-testid="stFileUploaderFile"] small,
        [data-testid="stFileUploader"] > section > div small,
        [data-testid="stFileUploaderDeleteBtn"] {{ color: {cores['text']} !important; }}

        [data-testid="stAlert"] {{ font-size: 1.05rem !important; }}
        [data-testid="stAlert"] *,
        [data-testid="stAlert"] p,
        [data-testid="stAlert"] div,
        [data-testid="stAlert"] span {{ color: {cores['text']} !important; }}
        [data-testid="stAlert"] strong {{ color: {cores['text_head']} !important; }}

        .stSelectbox [data-baseweb="select"],
        .stMultiSelect [data-baseweb="select"] {{ background-color: {cores['input_bg']} !important; }}
        .stSelectbox [data-baseweb="select"] *,
        .stMultiSelect [data-baseweb="select"] * {{ color: {cores['input_text']} !important; }}
        div[data-baseweb="select"] > div {{
            background-color: {cores['input_bg']} !important;
            border-color: {cores['card_border']} !important;
        }}
        div[data-baseweb="select"] > div * {{ color: {cores['input_text']} !important; }}
        div[data-baseweb="select"] [class*="placeholder"] {{ color: {cores['text_muted']} !important; }}
        div[data-baseweb="popover"] div[data-baseweb="menu"],
        ul[data-baseweb="menu"],
        div[data-baseweb="menu"] {{ background-color: {cores['input_bg']} !important; }}
        li[role="option"],
        div[role="option"] {{
            background-color: {cores['input_bg']} !important;
            color: {cores['input_text']} !important;
        }}
        li[role="option"]:hover,
        div[role="option"]:hover,
        li[aria-selected="true"] {{ background-color: {cores['guia_bg']} !important; }}
        span[data-baseweb="tag"] {{ background-color: {cores['accent']} !important; }}
        span[data-baseweb="tag"] span {{ color: #ffffff !important; }}

        [data-testid="stTable"] {{ background-color: {cores['card']}; border-radius: 8px; }}
        [data-testid="stDataFrame"] {{ font-size: 1rem !important; }}
        [data-testid="stDataFrame"] * {{ color: {cores['text']} !important; }}
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

        hr {{ border-color: {cores['card_border']} !important; }}
        a {{ color: {cores['accent']} !important; }}
        .material-icons {{ vertical-align: middle; margin-right: 10px; color: {cores['accent']}; }}

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
        .caixa-guia strong, .caixa-guia b {{ color: {cores['text_head']}; }}

        .feedback-card {{
            border-radius: 14px;
            padding: 24px 28px;
            margin: 8px 0 24px 0;
            border-left: 6px solid;
            box-shadow: {cores['shadow']};
        }}
        .feedback-positivo {{ background-color: {cores['fb_positivo_bg']}; border-left-color: {cores['fb_positivo_border']}; }}
        .feedback-atencao {{ background-color: {cores['fb_atencao_bg']}; border-left-color: {cores['fb_atencao_border']}; }}
        .feedback-risco {{ background-color: {cores['fb_risco_bg']}; border-left-color: {cores['fb_risco_border']}; }}
        .feedback-header {{ display: flex; align-items: center; gap: 16px; margin-bottom: 10px; }}
        .feedback-emoji {{ font-size: 2.4rem; line-height: 1; }}
        .feedback-title {{ font-size: 1.35rem; font-weight: 700; color: {cores['text_head']}; margin: 0; }}
        .feedback-subtitle {{ font-size: 1rem; color: {cores['text_muted']}; margin-top: 2px; }}
        .feedback-highlight {{
            background-color: {cores['card']};
            border: 1px solid {cores['card_border']};
            border-radius: 8px;
            padding: 12px 16px;
            margin: 12px 0;
            font-size: 1rem;
            color: {cores['text']};
        }}
        .feedback-tip {{
            font-size: 1rem;
            color: {cores['text']};
            margin-top: 12px;
            padding-top: 12px;
            border-top: 1px solid {cores['card_border']};
        }}
    </style>
    """


def botao_tema(sufixo):
    rotulo = "☀️ Modo Claro" if st.session_state.theme == 'dark' else "🌙 Modo Escuro"
    if st.button(rotulo, key=f"toggle_tema_{sufixo}", width="stretch"):
        st.session_state.theme = 'light' if st.session_state.theme == 'dark' else 'dark'
        st.rerun()


def titulo_com_icone(tag, icone, texto, tamanho=None):
    estilo = f' style="font-size: {tamanho}px;"' if tamanho else ''
    st.markdown(
        f'<{tag}><span class="material-icons"{estilo}>{icone}</span>{texto}</{tag}>',
        unsafe_allow_html=True,
    )


def estilo_plotly():
    return PLOTLY[st.session_state.theme]


def estilizar_figura(fig, **extras):
    estilo = estilo_plotly()
    fig.update_layout(
        paper_bgcolor=estilo['fundo'],
        plot_bgcolor=estilo['fundo'],
        font=dict(size=15, color=estilo['texto']),
        title_font=dict(size=20, color=estilo['texto']),
        separators=',.',
        **extras,
    )


def eixo(titulo):
    cor = estilo_plotly()['texto']
    return dict(title=titulo, tickfont=dict(size=13, color=cor), title_font=dict(size=15, color=cor))


def historico_usuario(forcar=False):
    if forcar or st.session_state.historico is None:
        st.session_state.historico = buscar_historico_supabase(st.session_state.user.id)
    return st.session_state.historico


def motor_analitico():
    return SmartFinanceAnalyzer(st.session_state.renda_salva, st.session_state.threshold_salvo)


def entrar(email, senha):
    if not email or not senha:
        st.error("Informe e-mail e senha.")
        return
    with st.spinner("Conectando..."):
        usuario, erro = login_usuario(email, senha)
    if not usuario:
        st.error(erro)
        return
    st.session_state.user = usuario
    perfil = buscar_perfil_usuario(usuario.id)
    if perfil.get('renda_mensal') is not None:
        st.session_state.renda_salva = float(perfil['renda_mensal'])
    if perfil.get('threshold_microgasto') is not None:
        st.session_state.threshold_salvo = float(perfil['threshold_microgasto'])
    preencher_campos_configuracao()
    st.session_state.cadastro_sucesso_email = None
    st.rerun()


def cadastrar(email, senha):
    if not email or not senha:
        st.error("Informe e-mail e senha.")
        return
    with st.spinner("Criando conta..."):
        usuario, erro = registrar_usuario(email, senha)
    if not usuario:
        st.error(erro)
        return
    st.session_state.cadastro_sucesso_email = email
    st.session_state.pending_auth_mode = "Acessar Sistema"
    st.rerun()


def solicitar_reset(email):
    if not email:
        st.error("Informe seu e-mail para receber o link.")
        return
    with st.spinner("Enviando link de redefinição..."):
        ok, erro = enviar_reset_senha(email)
    if not ok:
        st.error(f"Falha ao enviar: {erro}")
        return
    st.session_state.reset_enviado = True
    st.rerun()


def formulario_login():
    if st.session_state.cadastro_sucesso_email:
        st.success(
            "✅ Conta criada! Verifique o e-mail "
            f"**{st.session_state.cadastro_sucesso_email}** e clique no link de "
            "confirmação antes de entrar."
        )
    with st.form("form_login", clear_on_submit=False):
        email = st.text_input("E-mail corporativo", key="login_email")
        senha = st.text_input("Senha", type="password", key="login_senha")
        enviado = st.form_submit_button("Autenticar", type="primary", width="stretch")
    if enviado:
        entrar(email, senha)


def formulario_cadastro():
    with st.form("form_cadastro", clear_on_submit=True):
        email = st.text_input("E-mail corporativo", key="cadastro_email")
        senha = st.text_input("Senha", type="password", key="cadastro_senha")
        st.info(
            "🔒 Ao clicar em **Registrar Credenciais**, um e-mail de confirmação será "
            "enviado. Você precisa clicar no link do e-mail antes de conseguir acessar "
            "o sistema."
        )
        enviado = st.form_submit_button("Registrar Credenciais", type="primary", width="stretch")
    if enviado:
        cadastrar(email, senha)


def formulario_reset():
    if st.session_state.reset_enviado:
        st.success(
            "✅ **Link enviado!** Verifique sua caixa de entrada (e a pasta de spam). "
            "Após redefinir sua senha, volte aqui e faça o login pela opção 'Acessar Sistema'."
        )
        if st.button("Voltar ao login", width="stretch"):
            st.session_state.reset_enviado = False
            st.session_state.pending_auth_mode = "Acessar Sistema"
            st.rerun()
        return

    with st.form("form_reset", clear_on_submit=False):
        email = st.text_input("E-mail corporativo cadastrado", key="reset_email")
        st.info(
            "🔐 Enviaremos um **link de redefinição** para o seu e-mail. Basta "
            "clicar no link, definir uma nova senha e voltar aqui para acessar "
            "o sistema."
        )
        enviado = st.form_submit_button("Enviar link de redefinição", type="primary", width="stretch")
    if enviado:
        solicitar_reset(email)


def tela_autenticacao():
    st.markdown("<br><br>", unsafe_allow_html=True)
    _, coluna, _ = st.columns([1, 1.5, 1])

    with coluna:
        _, topo = st.columns([3, 1])
        with topo:
            botao_tema("login")

        titulo_com_icone('h1', 'shield', 'SDM Analytics', tamanho=40)
        st.write("Sistema de Detecção de Microgastos | Autenticação")
        st.divider()

        if 'pending_auth_mode' in st.session_state:
            st.session_state.auth_radio = st.session_state.pop('pending_auth_mode')

        modo = st.radio(
            "Selecione o acesso:",
            ["Acessar Sistema", "Novo Cadastro", "Esqueci minha senha"],
            horizontal=True,
            key="auth_radio",
        )
        st.markdown("<br>", unsafe_allow_html=True)

        if modo == "Acessar Sistema":
            formulario_login()
        elif modo == "Novo Cadastro":
            formulario_cadastro()
        else:
            formulario_reset()


def secao_exclusao_conta():
    usuario = st.session_state.user
    with st.expander("Excluir conta permanentemente"):
        quantidade = len(historico_usuario())

        st.markdown(
            f"Esta ação apaga a conta **{usuario.email}** e todos os microgastos vinculados a ela "
            "no banco de dados. Não há como desfazer ou recuperar esses dados depois de confirmado."
        )
        if quantidade > 0:
            st.markdown(f"Você tem **{quantidade} microgasto(s)** salvos na nuvem que serão apagados junto com a conta.")
        else:
            st.markdown("Você ainda não tem nenhum microgasto salvo na nuvem — apenas a conta de acesso será removida.")

        st.write(f"Para confirmar, digite seu e-mail de cadastro (`{usuario.email}`):")
        confirmacao = st.text_input(
            "Confirmação de e-mail", key="confirmacao_exclusao_email",
            label_visibility="collapsed", placeholder=usuario.email,
        )
        pode_excluir = confirmacao.strip().lower() == usuario.email.strip().lower()
        if confirmacao and not pode_excluir:
            st.caption("O e-mail digitado não corresponde à sua conta.")

        if st.button("Excluir conta e todos os dados", type="primary", disabled=not pode_excluir):
            with st.spinner("Excluindo conta..."):
                ok, erro = excluir_conta()
            if ok:
                limpar_sessao()
                st.rerun()
            else:
                st.error(f"Erro ao excluir conta: {erro}")


def confirmar_configuracao():
    renda = ler_valor_brasileiro(st.session_state.renda_texto)
    limite = ler_valor_brasileiro(st.session_state.limite_texto)
    if not renda or not limite:
        st.session_state.feedback_config = (
            'error', "Informe valores maiores que zero no formato brasileiro, por exemplo 5.000,00."
        )
        return
    st.session_state.perfil_configurado = True
    st.session_state.renda_salva = renda
    st.session_state.threshold_salvo = limite
    preencher_campos_configuracao()
    ok, erro = atualizar_perfil_usuario(st.session_state.user.id, renda, limite)
    if ok:
        st.session_state.feedback_config = ('success', "Configuração salva. Liberação para upload concedida.")
    else:
        st.session_state.feedback_config = (
            'warning', f"Configuração aplicada nesta sessão, mas não foi possível salvá-la no perfil: {erro}"
        )


def processar_upload(arquivo):
    assinatura = f"{arquivo.name}_{arquivo.size}_{st.session_state.threshold_salvo}"
    if st.session_state.arquivo_processado_assinatura == assinatura:
        st.success("✅ Arquivo já processado. Suas edições na Auditoria estão preservadas — envie um novo arquivo se quiser reprocessar do zero.")
        return

    with st.spinner("Processando o extrato..."):
        try:
            motor = motor_analitico()
            df = motor.processar_arquivo(arquivo)
            df[COLUNA_MICROGASTO] = motor.calcular_microgasto(df)
        except ValueError as e:
            st.error(f"Erro de formato: {e}")
        except Exception:
            log.exception("Falha inesperada ao processar o arquivo")
            st.error("Erro inesperado no processamento do arquivo.")
        else:
            st.session_state.df_master = df
            st.session_state.arquivo_processado_assinatura = assinatura
            st.session_state.dados_persistidos = False
            st.success("✅ Dados minerados! Siga para a aba 'Auditoria Transacional'.")


def aba_ingestao():
    st.markdown("""
    <div class="caixa-guia">
        <strong>Instruções de Uso:</strong><br>
        1. Preencha sua renda e o threshold (limite) para classificar um microgasto. Clique em Confirmar.<br>
        2. Realize o upload do seu arquivo de extrato bancário no campo ao lado.<br>
        3. Após o processamento, siga para a aba <b>"Auditoria Transacional"</b> no topo da tela.
    </div>
    """, unsafe_allow_html=True)

    coluna_parametros, coluna_upload = st.columns(2, gap="large")

    with coluna_parametros:
        titulo_com_icone('h4', 'settings', 'Parâmetros do Algoritmo')
        if CAMPOS_CONFIGURACAO[0] not in st.session_state:
            preencher_campos_configuracao()
        st.text_input("Renda Mensal (R$)", key='renda_texto')
        st.text_input("Threshold de Microgasto (R$)", key='limite_texto')
        st.button("Confirmar Configuração", type="primary", on_click=confirmar_configuracao)
        feedback = st.session_state.feedback_config
        if feedback:
            st.session_state.feedback_config = None
            getattr(st, feedback[0])(feedback[1])

    with coluna_upload:
        titulo_com_icone('h4', 'cloud_upload', 'Upload do Extrato')
        if not st.session_state.perfil_configurado:
            st.warning("Confirme os parâmetros do algoritmo primeiro.")
            return
        arquivo = st.file_uploader("Formatos aceitos: PDF, CSV, JSON", type=['pdf', 'csv', 'json'])
        if arquivo is not None:
            processar_upload(arquivo)


def aba_auditoria():
    base = st.session_state.df_master
    if base is None:
        st.info("Aguardando upload do extrato na aba de Ingestão de Dados (ETL).")
        return

    st.markdown("""
    <div class="caixa-guia" style="border-left-color: #10b981;">
        <strong>Validação de Categorias e Fluxo:</strong><br>
        Revise as classificações sugeridas pelo sistema. Altere a categoria, o
        tipo de fluxo (saída/entrada) ou desmarque o flag de microgasto se necessário.<br>
        Ao finalizar, clique em "Salvar Auditoria" e acesse a aba <b>"Análise de Impacto & Histórico"</b>.
    </div>
    """, unsafe_allow_html=True)

    exibicao = base.copy()
    exibicao['valor'] = exibicao['valor'].map(formatar_moeda)

    editado = st.data_editor(
        exibicao,
        column_config={
            "data": st.column_config.DateColumn("Data", format="DD/MM/YYYY"),
            "valor": st.column_config.TextColumn("Valor (R$)", disabled=True),
            "tipo": st.column_config.SelectboxColumn("Fluxo", options=TIPOS_FLUXO, help="Saída = gasto; Entrada = crédito"),
            "categoria": st.column_config.SelectboxColumn("Categoria", options=CATEGORIAS),
            COLUNA_MICROGASTO: st.column_config.CheckboxColumn("Analisar como Microgasto"),
        },
        hide_index=True,
        width="stretch",
    )
    if st.button("Salvar Auditoria", type="primary"):
        atualizado = base.copy()
        for coluna in ('data', 'descricao', 'categoria', 'tipo', COLUNA_MICROGASTO):
            atualizado[coluna] = editado[coluna]
        st.session_state.df_master = motor_analitico().aplicar_auditoria(atualizado)
        st.success("✅ Dados auditados! Prossiga para a geração dos indicadores.")


def card_diagnostico(diagnostico):
    emoji, titulo = NIVEIS_RISCO[diagnostico['nivel']]
    partes = [
        f'<div class="feedback-card feedback-{diagnostico["nivel"]}">',
        '<div class="feedback-header">',
        f'<span class="feedback-emoji">{emoji}</span>',
        '<div>',
        f'<p class="feedback-title">{titulo}</p>',
        f'<div class="feedback-subtitle">Seu Índice de Microgastos está em {formatar_percentual(diagnostico["im"])}</div>',
        '</div>',
        '</div>',
    ]
    if diagnostico['categoria_top']:
        partes.append(
            f'<div class="feedback-highlight"><strong>Categoria de maior impacto:</strong> '
            f'{diagnostico["categoria_top"]} — {formatar_moeda(diagnostico["valor_top"])} '
            f'({formatar_percentual(diagnostico["pct_top"], 1)} dos seus microgastos)</div>'
        )
    partes.append(f'<div class="feedback-tip">💡 <strong>Dica personalizada:</strong> {diagnostico["dica"]}</div>')
    partes.append('</div>')
    st.markdown("".join(partes), unsafe_allow_html=True)


def grafico_categorias(df_micro):
    estilo = estilo_plotly()
    fig = px.pie(df_micro, values='valor', names='categoria', hole=0.5,
                 template=estilo['template'], title="Concentração por Categoria")
    estilizar_figura(fig, legend=dict(font=dict(size=14, color=estilo['texto'])))
    fig.update_traces(textfont_size=14)
    st.plotly_chart(fig, width="stretch", config={'displayModeBar': False})


def grafico_evolucao(evolucao):
    estilo = estilo_plotly()
    inicio = evolucao['data'].min().strftime('%d/%m/%Y')
    fim = evolucao['data'].max().strftime('%d/%m/%Y')
    fig = px.bar(evolucao, x='dia_mes', y='valor_acumulado', text='valor_acumulado',
                 template=estilo['template'], title=f"Crescimento Acumulado ({inicio} a {fim})")
    fig.update_traces(texttemplate='%{text:,.2f}', textposition='outside', cliponaxis=False,
                      textfont=dict(size=13))
    estilizar_figura(
        fig, dragmode=False, bargap=0.2,
        xaxis=dict(type='category', **eixo("Dias do Extrato")),
        yaxis=eixo("Impacto Acumulado (R$)"),
    )
    st.plotly_chart(fig, width="stretch", config={'displayModeBar': False})


def comparativo_mensal(motor):
    titulo_com_icone('h4', 'bar_chart', 'Comparativo por Categoria entre Meses')
    resumo = motor.resumo_mensal_por_categoria(historico_usuario())
    if resumo.empty:
        st.info("Nenhum histórico salvo na nuvem para realizar comparações.")
        return

    meses = motor.meses_ordenados(resumo)
    selecionados = st.multiselect(
        "Selecionar meses para comparação:", options=meses, default=meses[-2:],
    )
    filtrado = resumo[resumo['mes_ano'].isin(selecionados)] if selecionados else resumo

    estilo = estilo_plotly()
    fig = px.bar(filtrado, x='mes_ano', y='valor', color='categoria', barmode='group', text='valor',
                 template=estilo['template'], category_orders={'mes_ano': motor.meses_ordenados(filtrado)})
    fig.update_traces(texttemplate='R$ %{text:,.0f}', textposition='outside', textfont=dict(size=11))
    estilizar_figura(
        fig, dragmode=False, height=460, legend_title_text='Categoria',
        legend=dict(font=dict(size=13, color=estilo['texto'])),
        xaxis=dict(title="", tickfont=dict(size=13, color=estilo['texto'])),
        yaxis=eixo("Impacto Financeiro (R$)"),
    )
    st.plotly_chart(fig, width="stretch", config={'displayModeBar': False})

    if len(selecionados) >= 2:
        ordenados = motor.meses_ordenados(resumo[resumo['mes_ano'].isin(selecionados)])
        alta = motor.maior_alta(resumo, ordenados[-2], ordenados[-1])
        if alta:
            categoria, valor = alta
            st.info(
                f"📈 **{categoria}** foi a categoria que mais aumentou de "
                f"{ordenados[-2]} para {ordenados[-1]}, com alta de {formatar_moeda(valor)}."
            )


def botao_persistir(df_micro):
    ja_persistido = st.session_state.dados_persistidos
    if st.button("Persistir Dados na Nuvem", type="primary", width="stretch", disabled=ja_persistido):
        if df_micro.empty:
            st.warning("Não há microgastos auditados para sincronizar.")
            return
        ok, erro = salvar_microgastos_supabase(df_micro, st.session_state.user.id)
        if not ok:
            st.error(f"Não foi possível sincronizar os dados: {erro}")
            return
        st.session_state.dados_persistidos = True
        st.session_state.historico = None
        st.session_state.aviso_persistencia = f"Sincronizados {len(df_micro)} microgastos no Supabase."
        st.rerun()
    if ja_persistido:
        st.caption("Os dados deste arquivo já foram sincronizados. Envie um novo extrato para sincronizar outros dados.")


def aba_analise():
    if st.session_state.df_master is None:
        st.info("Aguardando upload do extrato na aba de Ingestão de Dados (ETL).")
        return

    aviso = st.session_state.aviso_persistencia
    if aviso:
        st.session_state.aviso_persistencia = None
        st.success(aviso)
        st.balloons()

    motor = motor_analitico()
    df_micro = motor.filtrar_microgastos(st.session_state.df_master)
    diagnostico = motor.diagnosticar(df_micro)

    card_diagnostico(diagnostico)

    titulo_com_icone('h4', 'insights', 'Indicadores de Desempenho')
    col_total, col_im = st.columns(2)
    col_total.metric("Impacto Acumulado (R$)", formatar_moeda(diagnostico['total']))
    col_im.metric("Índice de Microgastos (IM)", formatar_percentual(diagnostico['im']))

    col_pizza, col_evolucao = st.columns(2)
    evolucao = motor.evolucao_diaria(df_micro)
    with col_pizza:
        if df_micro.empty:
            st.info("Não há microgastos identificados no período para gerar o gráfico de categorias.")
        else:
            grafico_categorias(df_micro)
    with col_evolucao:
        if evolucao.empty:
            st.info("Não há dados de microgastos para gerar o gráfico.")
        else:
            grafico_evolucao(evolucao)

    st.divider()
    comparativo_mensal(motor)

    st.markdown("<br>", unsafe_allow_html=True)
    botao_persistir(df_micro)


def tela_dashboard():
    cab_titulo, cab_tema, cab_sessao = st.columns([4, 1, 1])
    with cab_titulo:
        titulo_com_icone('h2', 'analytics', 'Dashboard de BI', tamanho=32)
        st.write(f"Sessão autenticada: **{st.session_state.user.email}**")
    with cab_tema:
        st.markdown("<br>", unsafe_allow_html=True)
        botao_tema("dashboard")
    with cab_sessao:
        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("Encerrar Sessão", width="stretch"):
            logout_usuario()
            limpar_sessao()
            st.rerun()

    secao_exclusao_conta()
    st.divider()

    aba1, aba2, aba3 = st.tabs(["Ingestão de Dados (ETL)", "Auditoria Transacional", "Análise de Impacto & Histórico"])
    with aba1:
        aba_ingestao()
    with aba2:
        aba_auditoria()
    with aba3:
        aba_analise()


inicializar_estado()
aplicar_tema_nativo()
st.markdown(gerar_css(st.session_state.theme), unsafe_allow_html=True)

if st.session_state.user is None:
    tela_autenticacao()
else:
    tela_dashboard()