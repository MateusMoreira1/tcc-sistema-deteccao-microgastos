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

    def processar_arquivo(self, uploaded_file):
        ext = uploaded_file.name.split('.')[-1].lower()
        if ext == 'pdf':
            return self._minerar_pdf_contextual(uploaded_file)
        elif ext == 'json':
            return pd.DataFrame(json.load(uploaded_file))
        return pd.read_csv(uploaded_file, sep=None, engine='python', encoding='utf-8')

    def _minerar_pdf_contextual(self, file):
        reader = PdfReader(file)
        registros = []
        data_corrente = "01/01/2026" 
        
        # 1. Padrões de Data
        re_data_extenso = r'(\d{1,2})\s+de\s+([A-Za-zçÇ]+)\s+de\s+(\d{4})'
        re_data_curta = r'\b(\d{2})[/.-](\d{2})(?:[/.-](\d{2,4}))?\b'
        
        # 2. Padrão Universal de Valor Monetário Brasileiro (Lê números com ou sem sinal)
        re_valores = r'(?:-R\$|-)?\s?(?:R\$)?\s?(\d{1,3}(?:\.\d{3})*,\d{2})'

        # 3. Dicionário Heurístico: Palavras que indicam saída de dinheiro em bancos tradicionais
        termos_saida = ['COMPRA', 'PAGAMENTO', 'PIX ENVIADO', 'DES:', 'DEB', 'DEBITO', 'TAR ', 'TARIFA', 'SAQUE', 'TRANSF']

        for page in reader.pages:
            content = page.extract_text()
            if not content: continue
            
            content = re.sub(r' +', ' ', content)
            
            for linha in content.split('\n'):
                linha = linha.strip()
                if not linha: continue

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
                    if len(ano) == 2: ano = "20" + ano
                    data_corrente = f"{dia}/{mes}/{ano}"

                # BUSCA DE VALORES MONETÁRIOS NA LINHA
                valores = re.findall(re_valores, linha)
                
                # Se encontrou algum dinheiro na linha, vamos analisar se é um gasto
                if valores:
                    linha_upper = linha.upper()
                    
                    # Identifica se é gasto: ou tem sinal de menos explícito, ou tem uma palavra-chave de saída
                    is_saida = '-' in linha or any(termo in linha_upper for termo in termos_saida)
                    
                    if is_saida:
                        # Pega o PRIMEIRO valor da linha (Ignora o Saldo que geralmente fica no final)
                        val_str = valores[0].replace('.', '').replace(',', '.')
                        
                        try:
                            valor_f = float(val_str)
                            
                            # Filtro final de segurança para evitar transações zeradas
                            if valor_f > 0:
                                registros.append({
                                    'data': data_corrente,
                                    'descricao': linha[:50],
                                    'valor': valor_f,
                                    'categoria': self._classificar_transacao(linha)
                                })
                        except:
                            continue
        
        df = pd.DataFrame(registros)
        
        if df.empty:
            raise ValueError("O sistema não conseguiu extrair transações. Formato de PDF não mapeado ou protegido.")
        
        df['data'] = pd.to_datetime(df['data'], dayfirst=True, errors='coerce')
        return df.dropna(subset=['data'])

    def _classificar_transacao(self, desc):
        desc = desc.upper()
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