import pandas as pd
import json
import re
from pypdf import PdfReader

class SmartFinanceAnalyzer:
    """Motor de análise universal para extração e auditoria de microgastos"""
    
    def __init__(self, renda_mensal, limite_micro):
        self.renda_mensal = renda_mensal
        self.limite_micro = limite_micro
        self.meses_map = {
            'janeiro': '01', 'fevereiro': '02', 'março': '03', 'abril': '04',
            'maio': '05', 'junho': '06', 'julho': '07', 'agosto': '08',
            'setembro': '09', 'outubro': '10', 'novembro': '11', 'dezembro': '12'
        }

    def processar_arquivo(self, uploaded_file):
        """Identifica a extensão e aplica o método de extração correto"""
        ext = uploaded_file.name.split('.')[-1].lower()
        try:
            if ext == 'pdf':
                return self._minerar_pdf_contextual(uploaded_file)
            elif ext == 'json':
                return pd.DataFrame(json.load(uploaded_file))
            return pd.read_csv(uploaded_file, sep=None, engine='python', encoding='utf-8')
        except Exception as e:
            raise ValueError(f"Erro no processamento: {e}")

    def _minerar_pdf_contextual(self, file):
        """Varredura universal via Mapeamento de Contexto"""
        reader = PdfReader(file)
        registros = []
        data_corrente = "01/01/2026"
        
        for page in reader.pages:
            content = page.extract_text()
            if not content: continue
            
            for linha in content.split('\n'):
                # Busca datas por extenso (Ex: 11 de Fevereiro de 2026)
                data_match = re.search(r'(\d{1,2})\sde\s(\w+)\sde\s(\d{4})', linha, re.IGNORECASE)
                if data_match:
                    dia, mes_n, ano = data_match.groups()
                    data_corrente = f"{dia.zfill(2)}/{self.meses_map.get(mes_n.lower(), '01')}/{ano}"
                    continue
                
                # Busca gastos brasileiros (Ex: -R$ 10,00 ou -25,50)
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
        if df.empty: raise ValueError("Nenhuma transação detectada no padrão R$.")
        return df

    def _classificar_transacao(self, desc):
        desc = desc.upper()
        if any(x in desc for x in ['99', 'UBER', 'POSTO', 'AUTO']): return 'Transporte'
        if any(x in desc for x in ['SORVETE', 'PADARIA', 'IFOOD', 'MERCADO', 'CONTINI']): return 'Alimentação'
        if any(x in desc for x in ['SPOTIFY', 'NETFLIX', 'INTER', 'TARIFA']): return 'Assinaturas/Taxas'
        return 'Geral/Outros'

    def calcular_im(self, df_micro):
        total = df_micro['valor'].sum()
        return total, (total / self.renda_mensal) * 100

    def gerar_dicas(self, im):
        if im < 5:
            return "🌟 **SITUAÇÃO EXCELENTE:** Seu controle é exemplar. Menos de 5% da sua renda é drenada por microgastos."
        elif im <= 15:
            return "⚠️ **ALERTA DE ATENÇÃO:** Pequenos gastos diários estão 'vazando' uma parte relevante do seu salário."
        return "🚨 **RISCO FINANCEIRO:** Mais de 15% da sua renda está sumindo em microgastos."