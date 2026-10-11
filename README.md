# 🎮 Agente Gaga — Co-piloto Financeiro e Operacional para Game Producers

> **Projeto desenvolvido para o Desafio DIO:** *Agente Financeiro Inteligente com IA Generativa*.  
> **Tema Adaptado:** Gestão de Orçamento (*Burn Rate*), Alocação de Recursos e Análise de Risco/ROI para Estúdios de Jogos Independentes.

---

## 📌 Contexto

No desenvolvimento de jogos, especialmente no cenário *indie*, o maior risco de um estúdio é ficar sem caixa no meio da produção (o famoso *runway* que acaba antes da versão final / *Gold Master*). 

A **Agente Gaga** une o trabalho de **Game Production** à **Gestão Financeira Proativa**, atuando como uma co-piloto no dia a dia do Producer para:

- **Antecipar estouros de orçamento:** Monitora a velocidade de queima de caixa (*burn rate*) e taxas de refação (*rework*) diretamente na quebra de tarefas.
- **Sugerir otimizações de escopo:** Recomenda soluções pragmáticas (ex: uso de assets prontos na loja, remanejamento de sprints) sem burocracia.
- **Separar generativo de determinístico:** O modelo de linguagem gera as tarefas e a comunicação, enquanto scripts Python/SQL rígidos executam toda a matemática financeira.
- **Blindagem Anti-Alucinação:** Opera sob diretrizes rígidas de *Grounding*, validação de schemas e arquitetura *Human-in-the-Loop*.

---

## 📂 O Que Este Repositório Entrega

### 1. Documentação do Agente
Detalhamento da proposta de valor, público-alvo, persona e arquitetura técnica:
- **Caso de Uso:** Gestão de custos e prevenção de déficit em estúdios de jogos.
- **Persona & Tom de Voz:** Didática, técnica, cômica e pontualmente irônica.
- **Arquitetura & Fluxo:** Diagrama Mermaid detalhado com fluxo de *Function Calling* e *Human-in-the-Loop*.
- **Segurança & Anti-Alucinação:** 4 pilares de proteção (Determinismo, Schemas, Grounding e HITL).

📄 **Documento:** [`docs/01-documentacao-agente.md`](./docs/01-documentacao-agente.md)

---

### 2. Base de Conhecimento
Integração de dados reais da indústria de games e engenharia de software com tabelas operacionais mockadas:

| Arquivo | Formato | Descrição no Projeto |
|---------|---------|-----------------------|
| `vgchartz_steam_sales.csv` | CSV | Histórico de vendas, preços médios e benchmarks para cálculo de *breakeven* na Steam. |
| `software_effort_cocomo.csv` | CSV | Esforço estimado vs. horas reais e taxas de refação (*PROMISE/Cocomo*). |
| `project_budget_runway.json` | JSON | Tetos de orçamento por Sprint/Milestone, despesas de *outsourcing* e saldo em caixa. |
| `jira_backlog_history.csv` | CSV | Backlog com metadados técnicos de game dev (polycount, PBR, LODs) e taxas/hora por função. |

📄 **Documento:** [`docs/02-base-conhecimento.md`](./docs/02-base-conhecimento.md)

---

### 3. Prompts do Agente
Engenharia de prompts robusta com diretrizes operacionais estritas:
- **System Prompt:** Regras de conduta, vocabulário da indústria e limitações declaradas.
- **Estrutura de Resposta Obrigatória:** Respostas padronizadas em 3 blocos (`[BLOCO 1] Tarefas`, `[BLOCO 2] Alerta Financeiro`, `[BLOCO 3] Próximo Passo`).
- **Exemplos de Interação (*Few-Shot*):** Quebra de tarefas, refação de animação, cotação de áudio terceirizado e simulação de *breakeven*.
- **Tratamento de Edge Cases:** Guardrails para recusa de direção criativa, dados incompletos, bloqueio de ações autônomas, questões de RH/fiscais e proteção de credenciais.

📄 **Documento:** [`docs/03-prompts.md`](./docs/03-prompts.md)

---

### 4. Aplicação Funcional
Protótipo interativo conectando a interface ao modelo com execução determinística:
- Chatbot interativo em **Streamlit**.
- Orquestração de ferramentas via **Function Calling** (`calculate_task_cost`, `get_sprint_budget`, etc.).
- Camada de cálculo matemático em Python livre de alucinações.

📁 **Código-fonte:** [`src/`](./src/)

---

### 5. Avaliação e Métricas
Critérios de aferição de qualidade e segurança do agente:
- Taxa de assertividade das estimativas de tempo e custo.
- 0% de divergência matemática (tolerância zero a contas "de cabeça" da IA).
- Aderência ao tom de voz e cumprimento estrito dos guardrails de escopo.

📄 **Documento:** [`docs/04-metricas.md`](./docs/04-metricas.md)

---

### 6. Pitch
Roteiro estruturado para apresentação de 3 minutos:
- A dor real da indústria de jogos independentes.
- Demonstração da Agente Gaga em ação no fluxo do Producer.
- O diferencial competitivo da arquitetura anti-alucinação.

📄 **Documento:** [`docs/05-pitch.md`](./docs/05-pitch.md)

---

## 🛠️ Tecnologias e Ferramentas

| Categoria | Ferramentas Utilizadas |
|-----------|------------------------|
| **LLM & Orquestração** | OpenAI GPT-4 / Function Calling |
| **Interface / Frontend** | Streamlit |
| **Cálculo Determinístico & Backend** | Python 3.10+, Pandas, Pydantic |
| **Bancos de Dados & Contexto** | JSON, SQLite / CSVs Estruturados |
| **Modelagem e Diagramas** | Mermaid.js |

---

## 📁 Estrutura do Repositório

```bash
📁 dio-agente-gaga/
│
├── 📄 README.md                      # Visão geral do projeto (este arquivo)
│
├── 📁 data/                          # Base de conhecimento e dados operacionais
│   ├── jira_backlog_history.csv      # Histórico de tarefas e esforço técnico
│   ├── project_budget_runway.json    # Orçamento, caixas e limites da Sprint
│   ├── software_effort_cocomo.csv    # Benchmarks de esforço e refação
│   └── vgchartz_steam_sales.csv      # Dados de mercado para simulação de vendas
│
├── 📁 docs/                          # Documentação detalhada do desafio
│   ├── 01-documentacao-agente.md     # Caso de uso, persona e arquitetura
│   ├── 02-base-conhecimento.md       # Estratégia de dados e grounding
│   ├── 03-prompts.md                 # System prompt, cenários e edge cases
│   ├── 04-metricas.md                # Avaliação de qualidade e segurança
│   └── 05-pitch.md                   # Roteiro do pitch em vídeo
│
├── 📁 src/                           # Código da aplicação
│   ├── app.py                        # Interface principal em Streamlit
│   ├── data_manager.py               # Manipulação de dados e RAG local
│   └── tools.py                      # Funções matemáticas determinísticas
│
└── 📁 assets/                        # Diagramas e prints de tela
    └── architecture-diagram.png

```

--- 


# 🚀 Como Executar o Protótipo
### 1. Clone o repositório:

```bash
git clone https://github.com/seu-usuario/dio-agente-gaga.git
cd dio-agente-gaga
```

### 2. Crie e ative um ambiente virtual:
```bash
python -m venv venv
No Windows:
venv\Scripts\activate
No Linux/Mac:
source venv/bin/activate
```

### 3. Instale as dependências:
```bash
pip install -r requirements.txt
```

### 4. Configure sua chave de API: Crie um arquivo .env na raiz do projeto com:

```env
OPENAI_API_KEY="sua-chave-aqui"
```
### 5. Inicie o Streamlit:
```bash
streamlit run src/app.py
```

