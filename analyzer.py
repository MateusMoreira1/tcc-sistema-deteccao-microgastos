import csv
import io
import json
import re
import unicodedata
from datetime import datetime

import pandas as pd
from pypdf import PdfReader

CATEGORIAS = ['Alimentação', 'Transporte', 'Assinaturas/Taxas', 'Saúde', 'Lazer', 'Outros']
TIPOS_FLUXO = ['saida', 'entrada']
COLUNA_MICROGASTO = 'Microgasto?'
COLUNAS_PADRAO = ['data', 'descricao', 'valor', 'categoria', 'tipo']

LIMITE_RISCO_POSITIVO = 5
LIMITE_RISCO_ATENCAO = 12

MESES = {
    'janeiro': '01', 'fevereiro': '02', 'março': '03', 'marco': '03', 'abril': '04',
    'maio': '05', 'junho': '06', 'julho': '07', 'agosto': '08',
    'setembro': '09', 'outubro': '10', 'novembro': '11', 'dezembro': '12',
}

TERMOS_ENTRADA = (
    'PIX RECEBIDO', 'TRANSF RECEBIDA', 'TRANSFERENCIA RECEBIDA',
    'TED RECEBIDA', 'DOC RECEBIDO', 'DEPOSITO', 'CREDITO',
    'RENDIMENTO', 'ESTORNO', 'REEMBOLSO', 'CASHBACK',
    'RESGATE', 'RECEBIMENTO', 'SALARIO', 'PROVENTO', 'RECEBIDO',
)

TERMOS_SAIDA = (
    'COMPRA', 'PAGAMENTO', 'PIX ENVIADO', 'DES:', 'DEB', 'DEBITO',
    'TAR ', 'TARIFA', 'SAQUE', 'TRANSF ENVIADA', 'TED ENVIADA',
    'DOC ENVIADO', 'PAG ',
)

PALAVRAS_CHAVE = {
    'Transporte': ['UBER', '99APP', '99POP', 'POSTO', 'AUTO', 'SHELL', 'IPIRANGA', 'ESTACIO', 'CONECTCAR', 'VELOE'],
    'Alimentação': ['IFOOD', 'MCDONALD', 'BK', 'BURGER', 'RESTAURANTE', 'PADARIA', 'MERCADO', 'EXTRA',
                    'CARREFOUR', 'PAO DE ACUCAR', 'SORVETE', 'ZAMP', 'DOCE', 'PARRILLA'],
    'Assinaturas/Taxas': ['SPOTIFY', 'NETFLIX', 'DISNEY', 'PRIME VIDEO', 'GOOGLE', 'APPLE.COM', 'TARIFA',
                          'MANUTENCAO', 'ANUIDADE', 'IOF', 'JUROS'],
    'Saúde': ['DROGASIL', 'DROGA RAIA', 'FARMACIA', 'UNIMED', 'HOSPITAL', 'LABORAT', 'RAIA'],
    'Lazer': ['CINEMA', 'INGRESSO', 'HOTEL', 'AIRBNB', 'RESERVA', 'STEAM', 'PLAYSTATION', 'BEBIDAS', 'BAR'],
}

DICAS = {
    'Alimentação': "Planeje as refeições da semana com antecedência e evite pedidos por aplicativo em dias seguidos — pequenas trocas aqui costumam gerar a maior economia.",
    'Transporte': "Avalie se corridas de aplicativo recorrentes podem ser parcialmente substituídas por transporte público ou caronas compartilhadas.",
    'Assinaturas/Taxas': "Revise suas assinaturas ativas: serviços de streaming, apps e tarifas bancárias esquecidas são microgastos clássicos.",
    'Saúde': "Verifique se há gastos recorrentes com farmácia ou suplementos que poderiam ser comprados em maior quantidade, com desconto.",
    'Lazer': "Considere estabelecer um limite mensal para saídas e entretenimento, mantendo espaço para o que realmente importa para você.",
    'Outros': "Boa parte desses gastos ainda está classificada como 'Outros' — vale revisar a auditoria para identificar padrões mais específicos.",
}

MAPA_COLUNAS = (
    ('data', 'data'),
    ('valor', 'valor'),
    ('descri', 'descricao'),
    ('histor', 'descricao'),
    ('categoria', 'categoria'),
    ('tipo', 'tipo'),
    ('fluxo', 'tipo'),
)

PALAVRAS_CABECALHO = ('data', 'valor', 'descri', 'histor', 'categoria', 'tipo', 'lançamento', 'lancamento')

RE_DATA_EXTENSO = re.compile(r'(\d{1,2})\s+de\s+([A-Za-zçÇ]+)\s+de\s+(\d{4})', re.IGNORECASE)
RE_DATA_CURTA = re.compile(r'\b(\d{2})[/.-](\d{2})(?:[/.-](\d{2,4}))?\b')
RE_VALOR = re.compile(r'(?:-R\$|-)?\s?(?:R\$)?\s?(\d{1,3}(?:\.\d{3})*,\d{2})')


class SmartFinanceAnalyzer:
    def __init__(self, renda_mensal, limite_micro):
        self.renda_mensal = renda_mensal
        self.limite_micro = limite_micro

    def processar_arquivo(self, arquivo):
        extensao = arquivo.name.rsplit('.', 1)[-1].lower()
        if extensao == 'pdf':
            return self._minerar_pdf_contextual(arquivo)
        if extensao == 'json':
            return self._normalizar_estruturado(self._ler_json(arquivo))
        if extensao == 'csv':
            return self._normalizar_estruturado(self._ler_csv(arquivo))
        raise ValueError("Formato não suportado. Envie um arquivo PDF, CSV ou JSON.")

    def _ler_json(self, arquivo):
        try:
            return pd.DataFrame(json.load(arquivo))
        except ValueError:
            raise ValueError("O arquivo JSON está inválido ou fora do formato esperado.") from None

    def _ler_csv(self, arquivo):
        conteudo = arquivo.read()
        try:
            texto = conteudo.decode('utf-8-sig')
        except UnicodeDecodeError:
            texto = conteudo.decode('latin-1')
        inicio = self._detectar_inicio_tabela(texto)
        try:
            return pd.read_csv(io.StringIO(texto), sep=None, engine='python', skiprows=inicio)
        except (pd.errors.EmptyDataError, pd.errors.ParserError, csv.Error):
            raise ValueError("Não foi possível ler o CSV. Verifique se o arquivo está vazio ou corrompido.") from None

    def _detectar_inicio_tabela(self, texto):
        for indice, linha in enumerate(texto.splitlines()[:15]):
            minuscula = linha.lower()
            if sum(palavra in minuscula for palavra in PALAVRAS_CABECALHO) >= 2:
                return indice
        return 0

    def _classificar_fluxo(self, linha_upper):
        if any(termo in linha_upper for termo in TERMOS_ENTRADA):
            return 'entrada'
        if any(termo in linha_upper for termo in TERMOS_SAIDA):
            return 'saida'
        return None

    def _minerar_pdf_contextual(self, arquivo):
        registros = self._extrair_registros_pdf(self._ler_paginas_pdf(arquivo))
        if not registros:
            raise ValueError("O sistema não conseguiu extrair transações. Formato de PDF não mapeado ou protegido.")

        df = pd.DataFrame(registros)
        df['data'] = pd.to_datetime(df['data'], dayfirst=True, errors='coerce')
        df = df.dropna(subset=['data'])
        if df.empty:
            raise ValueError("Nenhuma transação com data válida foi encontrada no PDF.")
        return df[COLUNAS_PADRAO].reset_index(drop=True)

    def _ler_paginas_pdf(self, arquivo):
        try:
            leitor = PdfReader(arquivo)
            return [pagina.extract_text() or '' for pagina in leitor.pages]
        except Exception:
            raise ValueError(
                "Não foi possível ler o PDF. Verifique se o arquivo não está corrompido ou protegido por senha."
            ) from None

    def _extrair_registros_pdf(self, paginas):
        ano_padrao = str(datetime.now().year)
        data_corrente = f"01/01/{ano_padrao}"
        registros = []

        for texto in paginas:
            texto = re.sub(r' +', ' ', texto)
            for linha in texto.split('\n'):
                linha = linha.strip()
                if not linha:
                    continue

                extenso = RE_DATA_EXTENSO.search(linha)
                if extenso:
                    dia, nome_mes, ano = extenso.groups()
                    mes = MESES.get(nome_mes.lower())
                    if mes:
                        data_corrente = f"{dia.zfill(2)}/{mes}/{ano}"
                    continue

                curta = RE_DATA_CURTA.search(linha)
                if curta:
                    dia, mes, ano = curta.groups()
                    ano = ano or ano_padrao
                    if len(ano) == 2:
                        ano = '20' + ano
                    data_corrente = f"{dia}/{mes}/{ano}"

                valores = RE_VALOR.findall(linha)
                if not valores:
                    continue

                tipo = self._classificar_fluxo(linha.upper())
                if tipo is None:
                    if '-' not in linha:
                        continue
                    tipo = 'saida'

                valor = float(valores[0].replace('.', '').replace(',', '.'))
                if valor > 0:
                    registros.append({
                        'data': data_corrente,
                        'descricao': linha[:50],
                        'valor': valor,
                        'categoria': self._classificar_transacao(linha),
                        'tipo': tipo,
                    })
        return registros

    def _remover_acentos(self, texto):
        decomposto = unicodedata.normalize('NFD', texto)
        return ''.join(c for c in decomposto if unicodedata.category(c) != 'Mn')

    def _mapear_colunas_estruturado(self, df):
        renomeacoes = {}
        usados = set()
        for coluna in df.columns:
            normalizada = self._remover_acentos(str(coluna)).lower()
            for palavra_chave, nome_padrao in MAPA_COLUNAS:
                if nome_padrao in usados:
                    continue
                if palavra_chave in normalizada:
                    renomeacoes[coluna] = nome_padrao
                    usados.add(nome_padrao)
                    break
        return df.rename(columns=renomeacoes)

    def _converter_valor_brasileiro(self, valor):
        if pd.isna(valor):
            return float('nan')
        if isinstance(valor, (int, float)):
            return float(valor)
        texto = str(valor).replace('R$', '').replace(' ', '').strip()
        numero = pd.to_numeric(texto, errors='coerce')
        if pd.notna(numero):
            return float(numero)
        numero_br = pd.to_numeric(texto.replace('.', '').replace(',', '.'), errors='coerce')
        return float(numero_br) if pd.notna(numero_br) else float('nan')

    def _inferir_tipo(self, valores, descricoes):
        if valores.notna().any() and (valores < 0).any():
            return valores.apply(lambda v: 'saida' if (pd.notna(v) and v < 0) else 'entrada')
        return descricoes.astype(str).str.upper().apply(lambda s: self._classificar_fluxo(s) or 'saida')

    def _normalizar_estruturado(self, df):
        if df.empty:
            raise ValueError("O arquivo não contém transações.")

        df = self._mapear_colunas_estruturado(df)

        faltando = [coluna for coluna in ('data', 'valor') if coluna not in df.columns]
        if faltando:
            raise ValueError(
                "Colunas obrigatórias não encontradas: " + ", ".join(faltando) +
                ". Verifique se o arquivo é um extrato com colunas de data e valor."
            )

        if 'descricao' not in df.columns:
            df['descricao'] = 'Sem descrição'

        valores = df['valor'].apply(self._converter_valor_brasileiro)

        if 'tipo' not in df.columns:
            df['tipo'] = self._inferir_tipo(valores, df['descricao'])

        df['valor'] = valores.abs()
        df = df.dropna(subset=['valor'])

        classificadas = df['descricao'].astype(str).apply(self._classificar_transacao)
        if 'categoria' in df.columns:
            df['categoria'] = df['categoria'].where(df['categoria'].isin(CATEGORIAS), classificadas)
        else:
            df['categoria'] = classificadas

        df['data'] = pd.to_datetime(df['data'], errors='coerce', dayfirst=True)
        df = df.dropna(subset=['data'])

        df['tipo'] = df['tipo'].astype(str).str.lower()
        df.loc[~df['tipo'].isin(TIPOS_FLUXO), 'tipo'] = 'saida'

        if df.empty:
            raise ValueError("Nenhuma transação válida foi encontrada no arquivo.")
        return df[COLUNAS_PADRAO].reset_index(drop=True)

    def _classificar_transacao(self, descricao):
        descricao = str(descricao).upper()
        for categoria, palavras in PALAVRAS_CHAVE.items():
            if any(palavra in descricao for palavra in palavras):
                return categoria
        return 'Outros'

    def calcular_microgasto(self, df):
        return (df['valor'] <= self.limite_micro) & (df['tipo'].astype(str).str.lower() == 'saida')

    def aplicar_auditoria(self, df):
        df = df.copy()
        df.loc[df['tipo'].astype(str).str.lower() == 'entrada', COLUNA_MICROGASTO] = False
        return df

    def filtrar_microgastos(self, df):
        marcados = df[COLUNA_MICROGASTO].fillna(False).astype(bool)
        return df[marcados].copy()

    def calcular_im(self, df_micro):
        total = float(df_micro['valor'].sum())
        im = total / self.renda_mensal * 100 if self.renda_mensal > 0 else 0.0
        return total, im

    def nivel_risco(self, im):
        if im <= LIMITE_RISCO_POSITIVO:
            return 'positivo'
        if im <= LIMITE_RISCO_ATENCAO:
            return 'atencao'
        return 'risco'

    def gerar_plano_acao(self, categoria_top):
        if categoria_top is None:
            return "Nenhum microgasto identificado neste período."
        return DICAS.get(categoria_top, "Continue acompanhando seus microgastos regularmente para manter o controle.")

    def diagnosticar(self, df_micro):
        total, im = self.calcular_im(df_micro)
        categoria_top, valor_top, pct_top = None, 0.0, 0.0
        if not df_micro.empty:
            por_categoria = df_micro.groupby('categoria')['valor'].sum().sort_values(ascending=False)
            categoria_top = por_categoria.index[0]
            valor_top = float(por_categoria.iloc[0])
            pct_top = valor_top / total * 100 if total > 0 else 0.0
        return {
            'total': total,
            'im': im,
            'nivel': self.nivel_risco(im),
            'categoria_top': categoria_top,
            'valor_top': valor_top,
            'pct_top': pct_top,
            'dica': self.gerar_plano_acao(categoria_top),
        }

    def evolucao_diaria(self, df_micro):
        df = df_micro.copy()
        df['data'] = pd.to_datetime(df['data'], dayfirst=True, errors='coerce')
        df = df.dropna(subset=['data'])
        if df.empty:
            return pd.DataFrame(columns=['data', 'valor_diario', 'valor_acumulado', 'dia_mes'])
        calendario = pd.date_range(df['data'].min().normalize(), df['data'].max().normalize(), freq='D')
        diario = df.groupby(df['data'].dt.normalize())['valor'].sum().reindex(calendario, fill_value=0)
        evolucao = diario.rename_axis('data').reset_index(name='valor_diario')
        evolucao['valor_acumulado'] = evolucao['valor_diario'].cumsum()
        evolucao['dia_mes'] = evolucao['data'].dt.strftime('%d/%m')
        return evolucao

    def resumo_mensal_por_categoria(self, historico):
        if historico.empty:
            return pd.DataFrame(columns=['mes_ano', 'categoria', 'valor'])
        df = historico.copy()
        df['data'] = pd.to_datetime(df['data'], errors='coerce')
        df = df.dropna(subset=['data'])
        df['mes_ano'] = df['data'].dt.strftime('%m/%Y')
        return df.groupby(['mes_ano', 'categoria'])['valor'].sum().reset_index()

    def meses_ordenados(self, resumo):
        meses = resumo['mes_ano'].unique()
        return sorted(meses, key=lambda m: pd.to_datetime(m, format='%m/%Y'))

    def maior_alta(self, resumo, mes_anterior, mes_atual):
        recorte = resumo[resumo['mes_ano'].isin([mes_anterior, mes_atual])]
        tabela = recorte.pivot(index='categoria', columns='mes_ano', values='valor').fillna(0)
        if mes_anterior not in tabela.columns or mes_atual not in tabela.columns:
            return None
        variacao = tabela[mes_atual] - tabela[mes_anterior]
        if variacao.max() <= 0:
            return None
        return variacao.idxmax(), float(variacao.max())