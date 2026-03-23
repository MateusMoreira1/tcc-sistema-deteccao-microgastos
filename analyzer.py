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
            'setembro': '09', 'outubro': '10', 'novembro': '11', 'dezembro': '12',
            'jan': '01', 'fev': '02', 'mar': '03', 'abr': '04', 'mai': '05', 'jun': '06',
            'jul': '07', 'ago': '08', 'set': '09', 'out': '10', 'nov': '11', 'dez': '12'
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
        
        # PADRÕES EXPANDIDOS
        re_data = r'(\d{2}/\d{2}(?:/\d{2,4})?)' # Aceita 02/03 ou 02/03/2026
        # Padrão de valor que aceita quase tudo: R$, -, números com vírgula e ponto
        re_valor = r'(?:R\$\s?|[-–]\s?)?(\d+(?:\.\d{3})*,\d{2})'

        for page in reader.pages:
            content = page.extract_text()
            if not content: continue
            
            # NORMALIZAÇÃO: Remove espaços duplos e caracteres estranhos
            content = re.sub(r' +', ' ', content)
            
            for linha in content.split('\n'):
                linha = linha.strip()
                if not linha: continue

                # 1. Tenta achar data na linha para atualizar o contexto
                match_data = re.search(re_data, linha)
                if match_data:
                    data_raw = match_data.group(1)
                    # Se a data for curta (02/03), completa com o ano
                    if len(data_raw) <= 5:
                        data_corrente = f"{data_raw}/2026"
                    else:
                        data_corrente = data_raw

                # 2. Busca Valor (foca em linhas que parecem transações)
                match_valor = re.search(re_valor, linha)
                if match_valor:
                    try:
                        val_str = match_valor.group(1).replace('.', '').replace(',', '.')
                        valor_f = float(val_str)
                        
                        # Filtro de segurança: ignora valores zerados
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
        
        # Se após tudo isso ainda estiver vazio, vamos lançar um erro mais informativo
        if df.empty:
            raise ValueError("O sistema não conseguiu extrair dados legíveis deste PDF. Certifique-se de que não é um arquivo scaneado (imagem) ou protegido por senha.")
        
        df['data'] = pd.to_datetime(df['data'], dayfirst=True, errors='coerce')
        return df.dropna(subset=['data'])

    def _classificar_transacao(self, desc):
        desc = desc.upper()
        # Dicionário expandido para bancos brasileiros
        mapping = {
            'Transporte': ['UBER', '99APP', '99POP', 'POSTO', 'AUTO', 'SHELL', 'IPIRANGA', 'ESTACIO', 'CONECTCAR', 'VELOE'],
            'Alimentação': ['IFOOD', 'MCDONALD', 'BK', 'BURGER', 'RESTAURANTE', 'PADARIA', 'MERCADO', 'EXTRA', 'CARREFOUR', 'PAO DE ACUCAR', 'SORVETE', 'ZAMP'],
            'Assinaturas/Taxas': ['SPOTIFY', 'NETFLIX', 'DISNEY', 'PRIME VIDEO', 'GOOGLE', 'APPLE.COM', 'TARIFA', 'MANUTENCAO', 'ANUIDADE', 'IOF', 'JUROS'],
            'Saúde': ['DROGASIL', 'DROGA RAIA', 'FARMACIA', 'UNIMED', 'HOSPITAL', 'LABORAT'],
            'Lazer': ['CINEMA', 'INGRESSO', 'HOTEL', 'AIRBNB', 'RESERVA', 'STEAM', 'PLAYSTATION']
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
            return "O volume de microgastos está dentro de uma margem segura. Mantenha o monitoramento mensal."
        
        top_categoria = df_micro.groupby('categoria')['valor'].sum().idxmax()
        
        alerta = "Alerta de Impacto: " if im <= 10 else "Risco Orçamentário: "
        
        dicas = {
            'Alimentação': "Identificamos alta frequência em serviços de delivery ou alimentação externa. Reduzir 2 pedidos por semana pode gerar uma economia significativa.",
            'Transporte': "Gastos recorrentes com mobilidade urbana detectados. Considere planos de assinatura de apps ou verifique trajetos curtos que podem ser feitos a pé.",
            'Assinaturas/Taxas': "Há incidência de taxas bancárias ou serviços recorrentes. Recomenda-se revisar assinaturas digitais subutilizadas.",
            'Saúde': "Gastos com farmácia detectados. Verifique programas de fidelidade ou descontos de laboratórios.",
            'Lazer': "Gastos com entretenimento digital ou hobbies. Defina uma verba fixa mensal para evitar o uso da reserva de emergência.",
            'Outros': "Existem despesas fragmentadas sem categoria definida. Recomenda-se detalhar estas compras na próxima auditoria para identificar gargalos."
        }
        
        return f"{alerta} {dicas.get(top_categoria, dicas['Outros'])}"