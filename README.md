# 📊 SDM - Sistema inteligente para detecção de microgastos

![Python](https://img.shields.io/badge/Python-3.x-blue?style=for-the-badge&logo=python)
![Streamlit](https://img.shields.io/badge/Streamlit-FF4B4B?style=for-the-badge&logo=streamlit&logoColor=white)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-316192?style=for-the-badge&logo=postgresql&logoColor=white)
![Supabase](https://img.shields.io/badge/Supabase-3ECF8E?style=for-the-badge&logo=supabase&logoColor=white)

Solução avançada de análise de extratos financeiros desenvolvida para identificar, categorizar e monitorar microgastos em transações bancárias. O sistema processa entradas em múltiplos formatos, aplica regras de mineração contextual (Regex) e gera indicadores de *Business Intelligence* precisos para otimização do controle financeiro pessoal.

## 📑 Índice
- [Autores](#-autores)
- [Funcionalidades principais](#-funcionalidades-principais)
- [Capturas de tela](#-capturas-de-tela)
- [Arquitetura do sistema](#-arquitetura-do-sistema)
- [Stack tecnológica](#️-stack-tecnológica)
- [Instalação e execução local](#-instalação-e-execução-local)
- [Guia rápido de uso](#-guia-rápido-de-uso)
- [Limitações conhecidas](#️-limitações-conhecidas)
- [Roadmap](#-roadmap--trabalhos-futuros)
- [Licença acadêmica](#-licença-acadêmica)

## 👥 Autores
- **Mateus dos Santos Moreira** — Engenharia de Software
- **Sarah Costa Silva** — Sistemas de Informação

---

## 🚀 Funcionalidades principais

- **Autenticação e segurança (multi-tenant):** Sistema de login com criptografia de senhas e isolamento de dados por usuário (*Privacy by Design*), totalmente alinhado aos preceitos da LGPD.
- **Ciclo completo de credenciais:** Cadastro com confirmação de conta por e-mail, redefinição de senha ("Esqueci minha senha") via link temporário e exclusão definitiva de conta pelo próprio usuário — ciclo de vida completo da credencial, do cadastro à remoção.
- **UI/UX premium (tema claro/escuro):** Interface com alternância dinâmica entre modo escuro e modo claro — incluindo os gráficos analíticos (Plotly) e os componentes internos do Streamlit — projetada com os mesmos padrões de usabilidade de painéis avançados de BI do mercado.
- **Extração universal (ETL):** Ingestão e processamento em memória de extratos nos formatos PDF, CSV e JSON de diversas instituições bancárias.
- **Categorização heurística (sistema especialista):** Motor de regras baseado em Regex contextual e listas de palavras-chave que extrai e pré-categoriza transações em documentos não estruturados. É uma abordagem de IA simbólica clássica (sistema baseado em regras, escritas pelos autores) — **não emprega Machine Learning nem modelos treinados** nesta versão do protótipo.
- **Auditoria humana integrada (*human-in-the-loop*):** Interface interativa (*data grid*) que permite ao usuário validar e editar categorias antes da geração de relatórios, garantindo a precisão final dos dados.
- **Formulários ágeis:** Telas de login, cadastro e redefinição de senha aceitam envio via tecla **Enter**, sem necessidade de clicar no botão.
- **Cálculo de comprometimento (IM):** Métrica exclusiva para mensurar matematicamente o impacto da "bola de neve" dos pequenos gastos na renda mensal.
- **Diagnóstico personalizado:** Card de feedback dinâmico que classifica o cenário financeiro do usuário (Positivo / Atenção / Risco) e sugere uma dica prática de acordo com a categoria de maior impacto no período.
- **Persistência em nuvem e histórico evolutivo:** Banco de dados integrado via **Supabase (PostgreSQL)**, gerando gráficos automatizados de evolução temporal mês a mês.
- **Comparativo categórico mensal:** Gráfico de barras agrupadas que evidencia, mês a mês, qual categoria de despesa mais cresceu — permitindo identificar tendências de consumo ao longo do tempo.

---

## 📸 Capturas de tela

### Autenticação

<table>
<tr>
<td width="50%"><img src="docs/screenshots/01-login-escuro.png" alt="Tela de login - modo escuro"/><br/><sub>Login — modo escuro (padrão)</sub></td>
<td width="50%"><img src="docs/screenshots/02-login-claro.png" alt="Tela de login - modo claro"/><br/><sub>Login — modo claro</sub></td>
</tr>
<tr>
<td width="50%"><img src="docs/screenshots/03-cadastro.png" alt="Tela de cadastro"/><br/><sub>Cadastro com confirmação por e-mail</sub></td>
<td width="50%"><img src="docs/screenshots/04-esqueci-senha.png" alt="Tela de redefinição de senha"/><br/><sub>Redefinição de senha</sub></td>
</tr>
</table>

### Ingestão e auditoria

<table>
<tr>
<td width="50%"><img src="docs/screenshots/05-ingestao-etl.png" alt="Aba de ingestão de dados"/><br/><sub>Ingestão de dados (ETL)</sub></td>
<td width="50%"><img src="docs/screenshots/06-auditoria.png" alt="Aba de auditoria transacional"/><br/><sub>Auditoria transacional (human-in-the-loop)</sub></td>
</tr>
</table>

### Análise de impacto & histórico

<img src="docs/screenshots/07-diagnostico.png" alt="Card de diagnóstico personalizado"/>
<p><sub>Diagnóstico personalizado por categoria</sub></p>

<img src="docs/screenshots/08-dashboards.png" alt="Dashboards de distribuição e crescimento"/>
<p><sub>Distribuição por categoria e crescimento acumulado</sub></p>

<img src="docs/screenshots/09-comparativo-mensal.png" alt="Comparativo por categoria entre meses"/>
<p><sub>Comparativo de microgastos por categoria entre meses</sub></p>

### Gerenciamento de conta

<img src="docs/screenshots/10-excluir-conta.png" alt="Exclusão de conta"/>
<p><sub>Exclusão de conta com confirmação por e-mail digitado</sub></p>

---

## 📊 Arquitetura do sistema

O projeto adota um padrão arquitetural modular, separando a lógica de negócio, a visualização e a persistência de dados:

1. **`app.py` (View / Frontend):** Interface do usuário em Streamlit responsável pelo roteamento (login/cadastro/reset/app), alternância de tema, inputs numéricos de alta precisão, auditoria humana e renderização de *dashboards* limpos.
2. **`analyzer.py` (Controller / Engine):** Motor de mineração e processamento de dados. Contém as heurísticas de Regex, normalização de *DataFrames* e a lógica do sistema especialista gerador de "planos de ação".
3. **`database.py` (Model / Integração):** Camada de segurança e banco de dados. Gerencia a comunicação com a API do Supabase — login, cadastro, redefinição de senha, exclusão de conta e persistência de microgastos — utilizando *JSON Web Tokens* (JWT) para garantir que cada usuário só acesse seus próprios dados.

<img src="docs/diagramas/diagrama_componentes.png" alt="Diagrama de componentes do sistema"/>
<p><sub>Diagrama de componentes (UML)</sub></p>

### Pipeline de dados (ETL)

O processamento dos extratos bancários segue um fluxo adaptado do modelo ETL tradicional, com uma etapa intermediária de validação humana (*Audit*), conforme o paradigma *human-in-the-loop* (Holzinger, 2016):

<img src="docs/diagramas/fluxograma_etl.png" alt="Fluxograma do pipeline ETL"/>
<p><sub>Fluxograma do pipeline Extract, Transform, Audit e Load</sub></p>

### Modelo de dados

O banco relacional (PostgreSQL/Supabase) é composto por três entidades — `usuarios`, `microgastos` e `categorias` — com isolamento de dados garantido por Row-Level Security e integridade referencial entre todas as tabelas.

<img src="docs/diagramas/mer_sdm_analytics_v2.png" alt="Modelo Entidade-Relacionamento"/>
<p><sub>MER — Modelo entidade-relacionamento (notação de Chen)</sub></p>

### Casos de uso

<img src="docs/diagramas/diagrama_casos_de_uso_v2.png" alt="Diagrama de casos de uso"/>
<p><sub>Diagrama de casos de uso (UML)</sub></p>

---

## 🛠️ Stack tecnológica

| Componente | Tecnologia | Função |
| :--- | :--- | :--- |
| **Linguagem base** | [Python 3.x](https://www.python.org/) | Backend, engenharia de dados e lógica |
| **Interface (UI)** | [Streamlit](https://streamlit.io/) | Criação do dashboard web SPA (*Single Page Application*) |
| **Data engine** | [Pandas](https://pandas.pydata.org/) | Manipulação, limpeza e agregação dos DataFrames |
| **Visualização (BI)** | [Plotly](https://plotly.com/python/) | Renderização de gráficos dinâmicos de alta legibilidade |
| **Cloud DB & Auth**| [Supabase](https://supabase.com/) | Autenticação (BaaS) e persistência relacional PostgreSQL |
| **PDF mining** | [PyPDF](https://pypdf.readthedocs.io/) | Leitura e extração binária de documentos não estruturados |
| **Segurança** | JWT + Row-Level Security (RLS) | Emissão de tokens de sessão e isolamento de dados por usuário no PostgreSQL |

---

## 📦 Instalação e execução local

1. Clone o repositório para a sua máquina:
```bash
git clone https://github.com/MateusMoreira1/tcc-sistema-deteccao-microgastos.git
cd tcc-sistema-deteccao-microgastos
```

> 📁 As imagens deste README ficam em `docs/screenshots/` (capturas de tela do sistema) e `docs/diagramas/` (MER, diagrama de casos de uso, diagrama de componentes e fluxograma ETL). Ambas as pastas já acompanham o repositório.

2. Crie e ative o ambiente virtual Python (recomendado):
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

4. **Configuração de variáveis de ambiente (segurança):**
Crie uma pasta oculta chamada `.streamlit` na raiz do projeto e, dentro dela, um arquivo `secrets.toml`. Adicione suas credenciais do Supabase neste arquivo:
```toml
# Arquivo: .streamlit/secrets.toml
SUPABASE_URL = "SUA_URL_AQUI"
SUPABASE_KEY = "SUA_CHAVE_AQUI"
```

5. **Configuração do Supabase (painel web):**
No painel do seu projeto Supabase, ajuste:
   - `Authentication → Providers → Email` → ative **"Confirm email"** para exigir confirmação de conta por e-mail no cadastro.
   - `Authentication → URL Configuration` → configure **Site URL** e **Redirect URLs** com a URL onde a aplicação está publicada (ex.: `https://seu-app.streamlit.app`), para que os links de confirmação de cadastro e de redefinição de senha funcionem corretamente.
   - `SQL Editor` → execute o script abaixo **uma única vez**, para habilitar a exclusão de conta pelo próprio usuário:

```sql
create or replace function delete_own_account()
returns void
language plpgsql
security definer
set search_path = public
as $$
begin
  delete from public.microgastos where usuario_id = auth.uid()::text;
  delete from auth.users where id = auth.uid();
end;
$$;

grant execute on function public.delete_own_account() to authenticated;
```

   > ⚠️ O plano gratuito do Supabase limita o envio de e-mails a aproximadamente **3 por hora** (cadastro + redefinição de senha). Planeje testes e demonstrações considerando esse limite.

6. Inicie a aplicação:
```bash
streamlit run app.py
```

---

## 📋 Guia rápido de uso

1. **Acesso:** Na tela inicial, crie uma conta com senha segura (mín. 6 caracteres), faça login, ou utilize a opção **"Esqueci minha senha"** caso necessário.
2. **Parametrização:** Informe sua renda mensal e defina numericamente o limite de corte do que deve ser considerado um "microgasto".
3. **Ingestão:** Faça o upload do arquivo do extrato (PDF, CSV ou JSON).
4. **Auditoria:** Revise as sugestões do motor heurístico de categorização na tabela. Altere categorias usando o menu suspenso, se necessário.
5. **Business Intelligence:** Acesse a aba "Análise de Impacto & Histórico" para ver o card de diagnóstico personalizado (categoria de maior impacto e dica prática), o comparativo de categorias entre meses, e clicar em **Persistir Dados** para alimentar seu histórico evolutivo na nuvem.
6. **Gerenciamento de conta:** No topo do dashboard, a seção **"Excluir conta permanentemente"** exibe a quantidade real de microgastos salvos e exige que você digite o e-mail da conta para confirmar — evitando exclusões acidentais.

---

## ⚠️ Limitações conhecidas

- O sistema **não utiliza Machine Learning ou IA generativa**. A categorização e classificação de fluxo são feitas por heurística de palavras-chave (regras fixas, escritas pelos autores).
- Extratos protegidos por senha ou digitalizados como imagem (sem OCR) não são processados.
- A categorização automática está limitada a seis categorias fixas.
- A tabela de auditoria (*data grid*) tem usabilidade reduzida em telas de toque (dispositivos móveis).
- Autenticação por código enviado ao e-mail (OTP) foi avaliada durante o desenvolvimento, mas não incorporada, em razão do limite de envio de e-mails do plano gratuito do Supabase.
- A exclusão de conta depende de uma função SQL com privilégio elevado (`SECURITY DEFINER`) criada previamente no banco — o cliente Python usa apenas a chave anônima e não tem permissão para excluir usuários diretamente, por design de segurança do Supabase.
- Não foram coletadas métricas quantitativas formais de precisão do motor de extração, nem a pontuação estruturada do System Usability Scale (SUS). A validação de usabilidade ocorreu de forma informal, por meio do uso do protótipo por aproximadamente 30 pessoas entre familiares e colegas, cujo retorno qualitativo orientou ajustes na interface, mas não substitui uma validação estatística formal.
- O sistema encontra-se em fase de protótipo funcional, testado informalmente quanto à usabilidade, mas ainda não implantado em ambiente de produção comercial.

## 🔭 Roadmap / trabalhos futuros

- Integração com **Open Finance**, substituindo o upload manual por consumo direto de APIs bancárias.
- Incorporação de **Machine Learning preditivo** para antecipar meses de maior risco de microgastos.
- Interface otimizada para dispositivos móveis (*mobile-first*).
- Evolução para ambiente de produção real: domínio próprio, política de privacidade formal, infraestrutura de e-mail independente do plano gratuito e testes de carga com múltiplos usuários simultâneos.
- Aplicação formal do System Usability Scale (SUS) e medição estruturada da taxa de acerto do motor de extração, para validação estatística complementar ao retorno qualitativo já coletado.

---

## 📝 Licença acadêmica
Este projeto foi desenvolvido integralmente como Trabalho de Conclusão de Curso (TCC) dos cursos de Engenharia de Software e Sistemas de Informação. Uso, cópia e distribuição são permitidos para fins estritamente acadêmicos, mediante a citação obrigatória dos autores originais.
