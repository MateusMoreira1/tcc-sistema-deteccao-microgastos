# 📊 SDM - Sistema Inteligente para Detecção de Microgastos

![Python](https://img.shields.io/badge/Python-3.x-blue?style=for-the-badge&logo=python)
![Streamlit](https://img.shields.io/badge/Streamlit-FF4B4B?style=for-the-badge&logo=streamlit&logoColor=white)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-316192?style=for-the-badge&logo=postgresql&logoColor=white)
![Supabase](https://img.shields.io/badge/Supabase-3ECF8E?style=for-the-badge&logo=supabase&logoColor=white)

Solução avançada de análise de extratos financeiros desenvolvida para identificar, categorizar e monitorar microgastos em transações bancárias. O sistema processa entradas em múltiplos formatos, aplica regras de mineração contextual (Regex) e gera indicadores de *Business Intelligence* precisos para otimização do controle financeiro pessoal.

## 👥 Autores
- **Mateus Santos Moreira** — Engenharia de Software
- **Sarah Costa Silva** — Sistemas de Informação

---

## 🚀 Funcionalidades Principais

- **Autenticação e Segurança (Multi-tenant):** Sistema de login com criptografia de senhas e isolamento de dados por usuário (*Privacy by Design*), totalmente alinhado aos preceitos da LGPD.
- **Ciclo Completo de Credenciais:** Cadastro com confirmação de conta por e-mail e fluxo de recuperação de senha ("Esqueci minha senha") via link temporário enviado ao e-mail do usuário.
- **UI/UX Premium (Tema Claro/Escuro):** Interface com alternância dinâmica entre Modo Escuro e Modo Claro — incluindo os gráficos analíticos (Plotly) e os componentes internos do Streamlit — projetada com os mesmos padrões de usabilidade de painéis avançados de BI do mercado.
- **Extração Universal (ETL):** Ingestão e processamento em memória de extratos nos formatos PDF, CSV e JSON de diversas instituições bancárias.
- **Categorização Heurística (Sistema Especialista):** Motor de regras baseado em Regex Contextual e listas de palavras-chave que extrai e pré-categoriza transações em documentos não estruturados. É uma abordagem de IA simbólica clássica (sistema baseado em regras, escritas pelos autores) — **não emprega Machine Learning nem modelos treinados** nesta versão do protótipo.
- **Auditoria Humana Integrada (*Human-in-the-loop*):** Interface interativa (*Data Grid*) que permite ao usuário validar e editar categorias antes da geração de relatórios, garantindo a precisão final dos dados.
- **Formulários Ágeis:** Telas de login, cadastro e redefinição de senha aceitam envio via tecla **Enter**, sem necessidade de clicar no botão.
- **Cálculo de Comprometimento (IM):** Métrica exclusiva para mensurar matematicamente o impacto da "bola de neve" dos pequenos gastos na renda mensal.
- **Diagnóstico Personalizado:** Card de feedback dinâmico que classifica o cenário financeiro do usuário (Positivo / Atenção / Risco) e sugere uma dica prática de acordo com a categoria de maior impacto no período.
- **Persistência em Nuvem e Histórico Evolutivo:** Banco de dados integrado via **Supabase (PostgreSQL)**, gerando gráficos automatizados de evolução temporal mês a mês.
- **Comparativo Categórico Mensal:** Gráfico de barras agrupadas que evidencia, mês a mês, qual categoria de despesa mais cresceu — permitindo identificar tendências de consumo ao longo do tempo.

---

## 📊 Arquitetura do Sistema

*Em desenvolvimento*

O projeto adota um padrão arquitetural modular, separando a lógica de negócio, a visualização e a persistência de dados:

1. **`app.py` (View / Frontend):** Interface do usuário em Streamlit responsável pelo roteamento (Login/Cadastro/Reset/App), alternância de tema, inputs numéricos de alta precisão, auditoria humana e renderização de *dashboards* limpos.
2. **`analyzer.py` (Controller / Engine):** Motor de mineração e processamento de dados. Contém as heurísticas de Regex, normalização de *DataFrames* e a lógica do sistema especialista gerador de "Planos de Ação".
3. **`database.py` (Model / Integração):** Camada de segurança e banco de dados. Gerencia a comunicação assíncrona com a API do Supabase — login, cadastro, redefinição de senha e persistência de microgastos — utilizando *JSON Web Tokens* (JWT) para garantir que cada usuário só acesse seus próprios dados.

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
| **Segurança** | JWT + Row-Level Security (RLS) | Emissão de tokens de sessão e isolamento de dados por usuário no PostgreSQL |

---

## 📦 Instalação e Execução Local

1. Clone o repositório para a sua máquina:
```bash
git clone https://github.com/MateusMoreira1/tcc-sistema-deteccao-microgastos.git
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

5. **Configuração do Supabase (painel web):**
No painel do seu projeto Supabase, ajuste:
   - `Authentication → Providers → Email` → ative **"Confirm email"** para habilitar a confirmação de conta por e-mail no cadastro.
   - `Authentication → URL Configuration` → configure **Site URL** e **Redirect URLs** como `http://localhost:8501` (ou a URL de produção), para que o link de "Esqueci minha senha" funcione corretamente.

   > *(Nota de desenvolvimento: para testes locais rápidos que não envolvam validar o fluxo de confirmação por e-mail, a opção "Confirm Email" pode ser temporariamente desativada. Lembre-se de reativá-la para demonstrar o fluxo completo.)*

   > ⚠️ O plano gratuito do Supabase limita o envio a aproximadamente **3 e-mails por hora** (cadastro + reset de senha). Planeje os testes e a demonstração considerando esse limite.

6. Inicie a aplicação:
```bash
streamlit run app.py
```

---

## 📋 Guia Rápido de Uso

1. **Acesso:** Na tela inicial, crie uma conta com senha segura (mín. 6 caracteres), faça login, ou utilize a opção **"Esqueci minha senha"** caso necessário.
2. **Parametrização:** Informe sua Renda Mensal e defina numericamente o limite de corte do que deve ser considerado um "Microgasto".
3. **Ingestão:** Faça o upload do arquivo do extrato (PDF, CSV ou JSON).
4. **Auditoria:** Revise as sugestões do motor heurístico de categorização na tabela. Altere categorias usando o menu suspenso, se necessário.
5. **Business Intelligence:** Acesse a aba "Análise de Impacto & Histórico" para ver o card de diagnóstico personalizado (categoria de maior impacto e dica prática), o comparativo de categorias entre meses, e clicar em **Persistir Dados** para alimentar seu histórico evolutivo na nuvem.

---

## ⚠️ Limitações Conhecidas

- O sistema **não utiliza Machine Learning ou IA generativa**. A categorização e classificação de fluxo são feitas por heurística de palavras-chave (regras fixas, escritas pelos autores).
- Extratos protegidos por senha ou digitalizados como imagem (sem OCR) não são processados.
- A categorização automática está limitada a seis categorias fixas.
- A tabela de auditoria (*Data Grid*) tem usabilidade reduzida em telas de toque (dispositivos móveis).
- Autenticação por código enviado ao e-mail (OTP) foi avaliada durante o desenvolvimento, mas não incorporada, em razão do limite de envio de e-mails do plano gratuito do Supabase.

## 🔭 Roadmap / Trabalhos Futuros

- Integração com **Open Finance**, substituindo o upload manual por consumo direto de APIs bancárias.
- Incorporação de **Machine Learning preditivo** para antecipar meses de maior risco de microgastos.
- Interface otimizada para dispositivos móveis (*mobile-first*).

---

## 📝 Licença Acadêmica
Este projeto foi desenvolvido integralmente como Trabalho de Conclusão de Curso (TCC) do curso de Sistemas de Informação e Engenharia de Software. Uso, cópia e distribuição são permitidos para fins estritamente acadêmicos, mediante a citação obrigatória dos autores originais.
