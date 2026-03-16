# Sistema inteligente de detecção de microgastos

Solução de análise de extratos financeiros para identificar e monitorar microgastos em transações bancárias. O sistema processa entradas em múltiplos formatos, aplica regras de mineração contextual e gera indicadores úteis para controle financeiro.

## 👤 Autores
- **Mateus dos Santos Moreira** — Engenharia de Software
- **Sarah Silva Costa** — Sistemas de Informação

---

## 🚀 Funcionalidades Principais

- **Extração Universal (ETL):** Processamento de extratos em formatos PDF, CSV e JSON de diversas instituições bancárias.
- **Mapeamento de Contexto:** Algoritmo de mineração baseado em **Regex Contextual** que vincula valores monetários às suas respectivas datas e seções em documentos não estruturados.
- **Auditoria Interativa (UX):** Interface que permite ao usuário validar, editar ou excluir transações mineradas antes da geração dos diagnósticos finais.
- **Cálculo do Índice de Microgastos (IM):** Implementação de métrica para mensurar o comprometimento percentual da renda mensal por pequenas despesas.
- **Persistência em Nuvem:** Camada de dados integrada ao **Supabase (PostgreSQL)**, garantindo integridade e armazenamento histórico.
---

## 📊 Arquitetura do Sistema

O projeto segue um fluxo de processamento dividido em três camadas principais:

1.  **`app.py` (View):** Interface do usuário responsável pelo upload, auditoria e visualização dos resultados de Business Intelligence.
2.  **`analyzer.py` (Controller):** Motor de inteligência que contém os algoritmos de Regex e a lógica de classificação de gastos.
3.  **`database.py` (Model):** Camada de integração responsável pela comunicação e persistência de dados no Supabase.

---

## 🛠️ Stack Tecnológica

| Componente | Tecnologia | Função |
| :--- | :--- | :--- |
| **Linguagem** | [Python 3.x](https://www.python.org/) | Backend e Lógica de Negócio |
| **Interface** | [Streamlit](https://streamlit.io/) | Dashboard Web e Interação |
| **Data Engine** | [Pandas](https://pandas.pydata.org/) | Manipulação e Normalização de Dados |
| **BI & Analytics** | [Plotly](https://plotly.com/python/) | Geração de Gráficos Dinâmicos |
| **Cloud DB** | [Supabase](https://supabase.com/) | Banco de Dados PostgreSQL na Nuvem |
| **PDF Mining** | [PyPDF](https://pypdf.readthedocs.io/) | Extração de Texto de Arquivos Binários |

---

## 📦 Instalação rápida

1. Clone o repositório:
```bash
git clone https://github.com/MateusMoreira1/tcc-sistema-deteccao-microgastos.git
cd tcc-sistema-deteccao-microgastos/app
```
2. Crie e ative ambiente Python (recomendado):
```bash
python -m venv .venv
source .venv/Scripts/activate # Windows
```
3. Instale dependências:
```bash
pip install -r requirements.txt
```
4. Configure o Supabase em `database.py`:
```python
SUPABASE_URL = "SUA_SUPABASE_URL"
SUPABASE_KEY = "SUA_SUPABASE_KEY"
```
5. Execute a aplicação:
```bash
streamlit run app.py
```

---

## 📋 Uso
1. Faça upload de um extrato (CSV/JSON/PDF)
2. Valide e ajuste as transações extraídas
3. Visualize dashboards e métricas de microgasto
4. Salve consultas e análises no banco

---

## 📝 Licença acadêmica
Projeto desenvolvido para Trabalho de Conclusão de Curso (TCC). Uso e distribuição permitidos apenas para fins acadêmicos, com citação dos autores.
