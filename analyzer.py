import pandas as pd
import json
import re
from pypdf import PdfReader

class SmartFinanceAnalyzer:
    def __init__(self, renda_mensal, limite_micro):
        self.renda_mensal = renda_mensal
        self.limite_micro = limite_micro
        self.meses_map = {
            'janeiro': '01', 'fevereiro': '02', 'março': '03', 'abril': '04',
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
        
        for page in reader.pages:
            content = page.extract_text()
            if not content: continue
            
            for linha in content.split('\n'):
                data_match = re.search(r'(\d{1,2})\sde\s(\w+)\sde\s(\d{4})', linha, re.IGNORECASE)
                if data_match:
                    dia, mes_n, ano = data_match.groups()
                    data_corrente = f"{dia.zfill(2)}/{self.meses_map.get(mes_n.lower(), '01')}/{ano}"
                    continue
                
                valor_match = re.search(r'(?:-R\$|-)\s?(\d+(?:\.\d{3})*,\d{2})', linha)
                if valor_match:
                    valor_f = float(valor_match.group(1).replace('.', '').replace(',', '.'))
                    registros.append({
                        'data': data_corrente,
                        'descricao': linha.strip()[:40],
                        'valor': valor_f,
                        'categoria': self._classificar_transacao(linha)
                    })
        
        df = pd.DataFrame(registros)
        if df.empty: raise ValueError("Nenhuma transação detectada.")
        df['data'] = pd.to_datetime(df['data'], dayfirst=True)
        return df

    def _classificar_transacao(self, desc):
        desc = desc.upper()
        if any(x in desc for x in ['99', 'UBER', 'POSTO', 'AUTO']): return 'Transporte'
        if any(x in desc for x in ['SORVETE', 'PADARIA', 'IFOOD', 'MERCADO']): return 'Alimentação'
        if any(x in desc for x in ['SPOTIFY', 'NETFLIX', 'INTER', 'TARIFA']): return 'Assinaturas/Taxas'
        return 'Outros'

    def calcular_im(self, df_micro):
        total = df_micro['valor'].sum()
        return total, (total / self.renda_mensal) * 100

    def gerar_plano_acao(self, df_micro, im):
        """Inteligência que gera dicas baseadas no MAIOR ralo de dinheiro."""
        if df_micro.empty or im < 5:
            return "✅ **Saúde Financeira Intacta:** Você tem um controle excepcional. Continue investindo e poupando."
        
        # Descobre qual categoria gastou mais
        top_categoria = df_micro.groupby('categoria')['valor'].sum().idxmax()
        
        alerta = f"⚠️ **Alerta (Impacto de {im:.1f}%):** " if im <= 15 else f"🚨 **Crítico (Impacto de {im:.1f}%):** "
        
        dicas = {
            'Alimentação': "Seu maior vilão são pequenos gastos com comida (apps, padaria). Tente definir um limite semanal para delivery ou cozinhar mais em casa.",
            'Transporte': "Gastos frequentes com apps de transporte estão corroendo sua renda. Avalie pacotes de desconto nos apps ou rotas alternativas.",
            'Assinaturas/Taxas': "Você está pagando muitas taxas bancárias ou serviços digitais que talvez nem use. Cancele assinaturas ociosas hoje mesmo.",
            'Outros': "Existem muitos gastos 'invisíveis' não classificados. Analise sua fatura com lupa e corte compras por impulso."
        }
        
        recomendacao = dicas.get(top_categoria, dicas['Outros'])
        return alerta + recomendacao