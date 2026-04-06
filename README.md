# 📊 SDM - Sistema Inteligente para Detecção de Microgastos

![Python](https://img.shields.io/badge/Python-3.x-blue?style=for-the-badge&logo=python)
![Streamlit](https://img.shields.io/badge/Streamlit-FF4B4B?style=for-the-badge&logo=streamlit&logoColor=white)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-316192?style=for-the-badge&logo=postgresql&logoColor=white)
![Supabase](https://img.shields.io/badge/Supabase-3ECF8E?style=for-the-badge&logo=supabase&logoColor=white)

Solução avançada de análise de extratos financeiros desenvolvida para identificar, categorizar e monitorar microgastos em transações bancárias. O sistema processa entradas em múltiplos formatos, aplica regras de mineração contextual (Regex) e gera indicadores de *Business Intelligence* precisos para otimização do controle financeiro pessoal.

## 👥 Autores
- **Mateus dos Santos Moreira** — Engenharia de Software
- **Sarah Silva Costa** — Sistemas de Informação

---

## 🚀 Funcionalidades Principais

- **Autenticação e Segurança (Multi-tenant):** Sistema de login com criptografia de senhas e isolamento de dados por usuário (*Privacy by Design*), totalmente alinhado aos preceitos da LGPD.
- **UI/UX Premium (Dark Mode):** Interface imersiva fixada em Modo Escuro, projetada com os mesmos padrões de usabilidade de painéis avançados de BI do mercado.
- **Extração Universal (ETL):** Ingestão e processamento em memória de extratos nos formatos PDF, CSV e JSON de diversas instituições bancárias.
- **Mapeamento de Contexto via IA:** Algoritmo heurístico baseado em **Regex Contextual** que extrai e pré-categoriza transações em documentos não estruturados.
- **Auditoria Humana Integrada:** Interface interativa (*Data Grid*) que permite ao usuário validar e editar categorias antes da geração de relatórios.
- **Cálculo de Comprometimento (IM):** Métrica exclusiva para mensurar matematicamente o impacto da "bola de neve" dos pequenos gastos na renda mensal.
- **Persistência em Nuvem e Histórico Evolutivo:** Banco de dados integrado via **Supabase (PostgreSQL)**, gerando gráficos automatizados de evolução temporal mês a mês.

---

## 📊 Arquitetura do Sistema

*(Se possuir uma imagem da arquitetura, insira-a aqui. Exemplo: `![Arquitetura do Sistema](arquitetura.png)`)*

O projeto adota um padrão arquitetural modular, separando a lógica de negócio, a visualização e a persistência de dados:

1. **`app.py` (View / Frontend):** Interface do usuário em Streamlit responsável pelo roteamento (Login/App), inputs numéricos de alta precisão, auditoria humana e renderização de *dashboards* limpos.
2. **`analyzer.py` (Controller / Engine):** Motor de mineração e processamento de dados. Contém as heurísticas de Regex, normalização de *DataFrames* e a lógica do sistema especialista gerador de "Planos de Ação".
3. **`database.py` (Model / Integração):** Camada de segurança e banco de dados. Gerencia a comunicação assíncrona com a API do Supabase utilizando *JSON Web Tokens* (JWT) para garantir que cada usuário só acesse seus próprios dados.

---

## 🛠️ Stack Tecnológica

| Componente | Tecnologia | Função |
| :--- | :--- | :--- |
| **Linguagem Base** | [Python 3.x](https://www.python.org/) | Backend, Engenharia de Dados e Lógica |
| **Interface (UI)** | [Streamlit](https://streamlit.io/) | Criação do Dashboard Web SPA (*Single Page Application*) |
| **Data Engine** | [Pandas](https://pandas.pydata.org/) | Manipulação, limpeza e agregação dos DataFrames |
| **Visualização (BI)** | [Plotly](https://plotly.com/python/) | Renderização de gráficos dinâmicos de alta legibilidade |
| **Cloud DB & Auth**| [Supabase](https://supabase.com/) | Autenticação (BaaS) e persistência relacional PostgreSQL |
| **PDF Mining** | [PyPDF](https://pypdf.readthedocs.io/) | Leitura e extração binária de documentos não estruturados |

---

## 📦 Instalação e Execução Local

1. Clone o repositório para a sua máquina:
```bash
git clone [https://github.com/MateusMoreira1/tcc-sistema-deteccao-microgastos.git](https://github.com/MateusMoreira1/tcc-sistema-deteccao-microgastos.git)
cd tcc-sistema-deteccao-microgastos
```

2. Crie e ative o ambiente virtual Python (Recomendado):
```bash
python -m venv .venv

# Ativação no Windows:
.venv\Scripts\activate

# Ativação no Linux/Mac:
source .venv/bin/activate
```

3. Instale as dependências listadas:
```bash
pip install -r requirements.txt
```

4. **Configuração de Variáveis de Ambiente (Segurança):**
Crie uma pasta oculta chamada `.streamlit` na raiz do projeto e, dentro dela, um arquivo `secrets.toml`. Adicione suas credenciais do Supabase neste arquivo:
```toml
# Arquivo: .streamlit/secrets.toml
SUPABASE_URL = "SUA_URL_AQUI"
SUPABASE_KEY = "SUA_CHAVE_AQUI"
```
*(Nota de Desenvolvimento: Para facilitar testes locais, recomendamos desativar a verificação obrigatória de e-mail ["Confirm Email"] no painel de Authentication do Supabase).*

5. Inicie a aplicação:
```bash
streamlit run app.py
```

---

## 📋 Guia Rápido de Uso

1. **Acesso:** Na tela inicial, crie uma conta com senha segura (mín. 6 caracteres) ou faça login.
2. **Parametrização:** Informe sua Renda Mensal e defina numericamente o limite de corte do que deve ser considerado um "Microgasto".
3. **Ingestão:** Faça o upload do arquivo do extrato (PDF, CSV ou JSON).
4. **Auditoria:** Revise as sugestões da Inteligência Artificial na tabela. Altere categorias usando o menu suspenso, se necessário.
5. **Business Intelligence:** Acesse a aba 3 para ver o diagnóstico do mês, ler o plano de ação gerado e clicar em **Persistir Dados** para alimentar seu histórico evolutivo na nuvem.

---

## 📝 Licença Acadêmica
Este projeto foi desenvolvido integralmente como Trabalho de Conclusão de Curso (TCC), unindo conhecimentos práticos de **Engenharia de Software** e **Sistemas de Informação**. Uso, cópia e distribuição são permitidos para fins estritamente acadêmicos, mediante a citação obrigatória dos autores originais.
```