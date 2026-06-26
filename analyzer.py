import pandas as pd
import json
import re
from pypdf import PdfReader

class SmartFinanceAnalyzer:
    def __init__(self, renda_mensal, limite_micro):
        self.renda_mensal = renda_mensal
        self.limite_micro = limite_micro
        self.meses_map = {
            'janeiro': '01', 'fevereiro': '02', 'março': '03', 'marco': '03', 'abril': '04',
            'maio': '05', 'junho': '06', 'julho': '07', 'agosto': '08',
            'setembro': '09', 'outubro': '10', 'novembro': '11', 'dezembro': '12'
        }
        # Heurística de fluxo: entradas (créditos) e saídas (débitos)
        # IMPORTANTE: entradas têm prioridade na classificação porque seus
        # termos são mais específicos (ex.: "PIX RECEBIDO" antes de cair em "-")
        self.termos_entrada = [
            'PIX RECEBIDO', 'TRANSF RECEBIDA', 'TRANSFERENCIA RECEBIDA',
            'TED RECEBIDA', 'DOC RECEBIDO', 'DEPOSITO', 'CREDITO',
            'RENDIMENTO', 'ESTORNO', 'REEMBOLSO', 'CASHBACK',
            'RESGATE', 'RECEBIMENTO', 'SALARIO', 'PROVENTO', 'RECEBIDO'
        ]
        self.termos_saida = [
            'COMPRA', 'PAGAMENTO', 'PIX ENVIADO', 'DES:', 'DEB', 'DEBITO',
            'TAR ', 'TARIFA', 'SAQUE', 'TRANSF ENVIADA', 'TED ENVIADA',
            'DOC ENVIADO', 'PAG '
        ]

    def processar_arquivo(self, uploaded_file):
        ext = uploaded_file.name.split('.')[-1].lower()
        if ext == 'pdf':
            return self._minerar_pdf_contextual(uploaded_file)
        elif ext == 'json':
            df = pd.DataFrame(json.load(uploaded_file))
            return self._normalizar_estruturado(df)
        else:
            df = pd.read_csv(uploaded_file, sep=None, engine='python', encoding='utf-8')
            return self._normalizar_estruturado(df)

    def _classificar_fluxo(self, linha_upper):
        """Classifica uma linha em 'entrada', 'saida' ou None pela heurística de termos.
        Entrada tem prioridade — seus termos são mais específicos."""
        if any(termo in linha_upper for termo in self.termos_entrada):
            return 'entrada'
        if any(termo in linha_upper for termo in self.termos_saida):
            return 'saida'
        return None

    def _minerar_pdf_contextual(self, file):
        reader = PdfReader(file)
        registros = []
        data_corrente = "01/01/2026"

        # 1. Padrões de Data
        re_data_extenso = r'(\d{1,2})\s+de\s+([A-Za-zçÇ]+)\s+de\s+(\d{4})'
        re_data_curta = r'\b(\d{2})[/.-](\d{2})(?:[/.-](\d{2,4}))?\b'

        # 2. Padrão Universal de Valor Monetário Brasileiro
        re_valores = r'(?:-R\$|-)?\s?(?:R\$)?\s?(\d{1,3}(?:\.\d{3})*,\d{2})'

        for page in reader.pages:
            content = page.extract_text()
            if not content:
                continue

            content = re.sub(r' +', ' ', content)

            for linha in content.split('\n'):
                linha = linha.strip()
                if not linha:
                    continue

                # TENTATIVA A: Data por Extenso (Banco Inter, etc)
                match_extenso = re.search(re_data_extenso, linha, re.IGNORECASE)
                if match_extenso:
                    dia = match_extenso.group(1).zfill(2)
                    mes_nome = match_extenso.group(2).lower()
                    ano = match_extenso.group(3)
                    mes = self.meses_map.get(mes_nome, '01')
                    data_corrente = f"{dia}/{mes}/{ano}"
                    continue

                # TENTATIVA B: Data Curta (Bradesco, Santander, Nubank, Itaú)
                match_curta = re.search(re_data_curta, linha)
                if match_curta:
                    dia = match_curta.group(1).zfill(2)
                    mes = match_curta.group(2).zfill(2)
                    ano = match_curta.group(3) if match_curta.group(3) else "2026"
                    if len(ano) == 2:
                        ano = "20" + ano
                    data_corrente = f"{dia}/{mes}/{ano}"

                # BUSCA DE VALORES MONETÁRIOS NA LINHA
                valores = re.findall(re_valores, linha)
                if not valores:
                    continue

                linha_upper = linha.upper()

                # Classifica o fluxo (entrada x saída) — entrada tem prioridade
                tipo_fluxo = self._classificar_fluxo(linha_upper)

                if tipo_fluxo is None:
                    # Sem palavra-chave: o sinal de menos sugere saída,
                    # mas só vale como fallback (nunca sobrepõe um termo de entrada)
                    if '-' in linha:
                        tipo_fluxo = 'saida'
                    else:
                        # Linha ambígua sem indicação de fluxo: pula
                        continue

                # Pega o PRIMEIRO valor (ignora o saldo no fim da linha)
                val_str = valores[0].replace('.', '').replace(',', '.')

                try:
                    valor_f = float(val_str)
                    if valor_f > 0:
                        registros.append({
                            'data': data_corrente,
                            'descricao': linha[:50],
                            'valor': valor_f,
                            'categoria': self._classificar_transacao(linha),
                            'tipo': tipo_fluxo
                        })
                except:
                    continue

        df = pd.DataFrame(registros)

        if df.empty:
            raise ValueError("O sistema não conseguiu extrair transações. Formato de PDF não mapeado ou protegido.")

        df['data'] = pd.to_datetime(df['data'], dayfirst=True, errors='coerce')
        return df.dropna(subset=['data'])

    def _normalizar_estruturado(self, df):
        """Garante que CSV/JSON tenham as colunas mínimas (data, descricao, valor,
        categoria, tipo) e que o valor seja sempre positivo."""
        if df.empty:
            return df

        # 1. Coluna 'tipo': se não vier explícita, deduz pelo sinal do valor ou pela descrição
        if 'tipo' not in df.columns:
            tipo_inferido = None

            if 'valor' in df.columns:
                vals = pd.to_numeric(df['valor'], errors='coerce')
                if vals.notna().any() and (vals < 0).any():
                    # Valores assinados: negativo = saída, positivo = entrada
                    tipo_inferido = vals.apply(lambda v: 'saida' if (pd.notna(v) and v < 0) else 'entrada')

            if tipo_inferido is None and 'descricao' in df.columns:
                # Sem sinal no valor: tenta classificar pela descrição
                tipo_inferido = df['descricao'].astype(str).str.upper().apply(
                    lambda s: self._classificar_fluxo(s) or 'saida'
                )

            if tipo_inferido is None:
                # Último recurso: assume tudo como saída — o usuário pode corrigir na auditoria
                tipo_inferido = pd.Series(['saida'] * len(df), index=df.index)

            df['tipo'] = tipo_inferido

        # 2. Valor sempre positivo (módulo)
        if 'valor' in df.columns:
            df['valor'] = pd.to_numeric(df['valor'], errors='coerce').abs()
            df = df.dropna(subset=['valor'])

        # 3. Categoria: se não vier, classifica pela descrição
        if 'categoria' not in df.columns:
            if 'descricao' in df.columns:
                df['categoria'] = df['descricao'].astype(str).apply(self._classificar_transacao)
            else:
                df['categoria'] = 'Outros'

        # 4. Normaliza data
        if 'data' in df.columns:
            df['data'] = pd.to_datetime(df['data'], errors='coerce', dayfirst=True)
            df = df.dropna(subset=['data'])

        # 5. Normaliza valores da coluna tipo (lowercase, fallback 'saida')
        df['tipo'] = df['tipo'].astype(str).str.lower()
        df.loc[~df['tipo'].isin(['saida', 'entrada']), 'tipo'] = 'saida'

        return df.reset_index(drop=True)

    def _classificar_transacao(self, desc):
        desc = str(desc).upper()
        mapping = {
            'Transporte': ['UBER', '99APP', '99POP', 'POSTO', 'AUTO', 'SHELL', 'IPIRANGA', 'ESTACIO', 'CONECTCAR', 'VELOE'],
            'Alimentação': ['IFOOD', 'MCDONALD', 'BK', 'BURGER', 'RESTAURANTE', 'PADARIA', 'MERCADO', 'EXTRA', 'CARREFOUR', 'PAO DE ACUCAR', 'SORVETE', 'ZAMP', 'DOCE', 'PARRILLA'],
            'Assinaturas/Taxas': ['SPOTIFY', 'NETFLIX', 'DISNEY', 'PRIME VIDEO', 'GOOGLE', 'APPLE.COM', 'TARIFA', 'MANUTENCAO', 'ANUIDADE', 'IOF', 'JUROS'],
            'Saúde': ['DROGASIL', 'DROGA RAIA', 'FARMACIA', 'UNIMED', 'HOSPITAL', 'LABORAT', 'RAIA'],
            'Lazer': ['CINEMA', 'INGRESSO', 'HOTEL', 'AIRBNB', 'RESERVA', 'STEAM', 'PLAYSTATION', 'BEBIDAS', 'BAR']
        }
        for cat, keywords in mapping.items():
            if any(key in desc for key in keywords):
                return cat
        return 'Outros'

    def calcular_im(self, df_micro):
        total = df_micro['valor'].sum()
        im = (total / self.renda_mensal) * 100 if self.renda_mensal > 0 else 0
        return total, im

    def gerar_plano_acao(self, df_micro, im):
        if df_micro.empty or im < 3:
            return "O volume de microgastos está dentro de uma margem segura."
        top_categoria = df_micro.groupby('categoria')['valor'].sum().idxmax()

        dicas = {
            'Alimentação': "Alta frequência em delivery ou alimentação. Reduzir 2 pedidos por semana gera economia visível.",
            'Transporte': "Avalie pacotes de assinatura em apps de transporte para rotas frequentes.",
            'Assinaturas/Taxas': "Há alta incidência de taxas bancárias ou serviços recorrentes ociosos. Revise suas assinaturas.",
            'Saúde': "Gastos frequentes em farmácias. Priorize redes com programas de fidelidade.",
            'Lazer': "Defina uma verba fixa mensal para entretenimento.",
            'Outros': "Despesas fragmentadas. Detalhe estas compras na próxima auditoria."
        }
        return dicas.get(top_categoria, dicas['Outros'])
