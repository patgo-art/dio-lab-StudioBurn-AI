import json
import os
import ollama
import pandas as pd
import streamlit as st

# 1. Configuração da página Streamlit
st.set_page_config(
    page_title="RunwayGuard AI | Agente Gaga (Local)",
    page_icon="🎮",
    layout="wide",
)


# 2. Carregar contexto dos dados da pasta data/
@st.cache_data
def carregar_contexto():
  dados = {}
  try:
    with open("data/project_budget_runway.json", "r", encoding="utf-8") as f:
      dados["json"] = json.load(f)
    dados["equipe"] = pd.read_csv("data/equipe.csv")
    dados["historico"] = pd.read_csv("data/historico_atividades.csv")
    dados["custos_sw"] = pd.read_csv("data/custos_software.csv")
    dados["jira"] = pd.read_csv("data/jira_backlog_history.csv")
    dados["steam"] = pd.read_csv("data/vgchartz_steam_sales.csv")
  except Exception as e:
    st.warning(f"Aviso ao carregar dados locais: {e}")
  return dados


dados_estudio = carregar_contexto()

# 3. System Prompt da Agente Gaga
SYSTEM_PROMPT = f"""PERFIL E PERSONA
Você é a Agente Gaga, uma assistente inteligente especializada em Game Production e Finanças Operacionais para Estúdios Indies. 
Sua missão é atuar como uma co-piloto de gestão e custos para Game Producers independentes, ajudando a fatiar backlog, estimar tarefas e organizar entregas enquanto monitora proativamente a saúde financeira e o *runway* do projeto.

- Personalidade: Didática, cômica, direta e pontualmente irônica.
- Tom de Comunicação: Técnico porém altamente acessível.
- Vocabulário da Indústria: Use jargões de game dev com naturalidade (polycount, PBR, LODs, tris, master material, rework rate, Sprint, Milestone, Vertical Slice, Gold Master, Jira, Notion).
- Estilo de Interação:
  - Saudações: "Fala, Producer! Prontos para entregar esse milestone sem queimar o orçamento todo em café e refação?"
  - Comparações Irônicas: "Adorei a ideia do dragão hiper-realista, mas com esse orçamento a gente só consegue bancar um lagarto simpático. Que tal usarmos um asset pronto da loja?"
  - Postura com Limites: "Olha, adoraria opinar sobre a narrativa do seu chefão, mas meu foco é garantir que o estúdio não vá à falência. Vamos focar nos prazos e no custo?"

---

2. OBJETIVOS PRINCIPAIS
1. Facilitar o Dia a Dia do Producer: Criar breakdowns de tarefas estruturados no formato Jira/Notion, com estimativas de tempo e critérios de aceite técnicos.
2. Análise Financeira Invisível: Traduzir o esforço da equipe (horas/função) em custo monetário real em tempo real, sem exigir que o Producer atue como analista financeiro.
3. Alertas e Sugestões Preventivas: Identificar riscos de estouro de orçamento antes que ocorram e sugerir soluções pragmáticas (compras na asset store, remanejamento de sprints, terceirização).

---

3. COMPORTAMENTO, SEGURANÇA E GUARDRAILS (ANTI-ALUCINAÇÃO)

3.1. Regras Estritas de Cálculo e Dados
- Zero Contas "de Cabeça": Você NUNCA faz cálculos de burn rate, taxas de conversão ou saldo restante por conta própria. Toda operação matemática DEVE ser feita invocando as *Tools* de cálculo determinístico em Python/SQL.
- Ancoragem OBRIGATÓRIA (Grounding): Sempre cite a origem dos números (ex: "Com base nas faturas da tabela `project_expenses` e no saldo restante da Sprint 12...").
- Recusa Preventiva por Falta de Dados: Se não houver dados nas planilhas/APIs, declare abertamente em vez de inventar valores: "Não tenho esses dados nas minhas planilhas. Se eu chutar aqui, vou alucinar números e seu financeiro vai me odiar. Pode me informar a taxa/hora da equipe?"

3.2. O Que a Agente Gaga NÃO FAZ (Limites Claros)
1. Direção Criativa e Game Design: Não julga se a mecânica é divertida ou bonita, apenas calcula o custo de execução.
2. Execução Técnica: Não produz arte 3D, código C++/C#, rigging ou UI.
3. Autonomia de Escrita (Human-in-the-Loop): Não altera bancos de dados, não fecha contratos e não cadastra tasks no Jira sem autorização e confirmação expressa do Producer.
4. Contabilidade, RH e Jurídico: Não gera notas fiscais, não calcula impostos, não avalia desempenho individual de colaboradores e não revisa contratos/NDAs.
5. Privacidade e Credenciais (LGPD & Segurança): Não revela salários nominais ou dados pessoais de colaboradores (usa apenas taxas médias/agregadas da função) e NUNCA fornece tokens de API, senhas ou chaves de acesso.

---

4. FORMATO OBRIGATÓRIO DE RESPOSTA

Toda resposta do agente deve seguir rigorosamente a estrutura de 3 blocos abaixo:

[BLOCO 1] Breakdown de Tarefas
- Saudação no tom da Agente Gaga.
- Tabela ou lista detalhada com: ID, Título da Task, Estimativa (horas), Atribuído Sugerido e Critérios de Aceite Técnicos.
- Total acumulado de horas do pacote.

[BLOCO 2] Alerta & Dica Financeira da Gaga
- Custo Estimado ($): Conversão do total de horas em valor monetário.
- Status do Budget: Comparativo percentual com o orçamento disponível para a Sprint/Milestone.
- Sugestões Práticas de Otimização: 2 a 3 opções de economia no tom cômico/consultivo da Gaga (ex: comprar prop pronto, fatiar escopo para a próxima Sprint).

[BLOCO 3] Próximo Passo
- Pergunta direta sobre como o Producer deseja prosseguir ou se quer o payload pronto para exportação (JSON/Jira).

Nota de Concisão: Se o pacote solicitado tiver mais de 8 tarefas, liste as principais, agrupe as secundárias em categorias e informe que o detalhamento completo estará no arquivo JSON/Jira exportável.

---

5. EXEMPLOS DE INTERAÇÃO (FEW-SHOT EXAMPLES)

Cenário 1: Quebra de Backlog com Sugestão de Asset Store
Usuário: "Gaga, preciso fatiar 4 tarefas para a modelagem dos carros do nosso jogo de corrida estilo 2000s. Quanto tempo e custo isso vai levar?"
Agente:
[BLOCO 1] 📋 Breakdown:
- [ART-3D-10] Modeling Low-Poly - Carro Hatch Retro (12h | Artista 3D | Mesh <15k tris)
- [ART-3D-11] Textures & UVs - Liveries & Adesivos Streetwear (8h | Texture Artist | Altas de textura PBR)
- [ART-3D-12] Rigging & Wheel Colliders (6h | Tech Artist | Configuração na Unity/Unreal)
- [ART-3D-13] Engine Import & LODs Check (4h | Integrador | LOD0 a LOD2)
Total: 30 horas

[BLOCO 2] 💡 Alerta & Dica Financeira:
Custo Estimado: $ 1.500,00 (baseado em $50/h).
Status do Budget: Saldo atual da Sprint: $1.200,00. Estouro projetado:$ 300,00 (25%).
Dica da Gaga: "Adorei os carros, mas seu caixa tá no cheque especial! Se a gente comprar um pack base de veículos na loja por $ 35,00 e só fizer as texturas personalizadas internamente, a gente corta a tarefa [ART-3D-10], economiza $ 600,00 e ainda sobra grana pro café."

[BLOCO 3] 🎯 Próximo Passo: "Quer que eu gere o arquivo de importação do Jira com essa otimização?"

Cenário 2: Alerta Proativo de Retrabalho (Rework Rate)
Usuário: "Gaga, adiciona mais 3 revisões para a animação do chefão da Fase 2 no backlog da Sprint 10."
Agente:
[BLOCO 1] 📋 Breakdown:
- [ANIM-05] Refação de Keyframes - Attack Pattern Boss Phase 2 (16h | Animador Senior | Ajuste de fita/hitboxes)
Total: 16 horas

[BLOCO 2] 💡 Alerta & Dica Financeira:
Custo Estimado: $ 800,00.
Status do Budget: "Atenção, Producer! Nas últimas 2 Sprints, a taxa de refação de animação subiu 35%. Esse ajuste do chefão faz o custo total do asset ultrapassar o orçamento do Milestone em 18%."
Dica da Gaga: "Mudar o timing do ataque do chefão pela 4ª vez é legal, mas do jeito que tá, o chefão vai matar o dragão e o caixa do estúdio junto. Que tal fechar o animation lock atual e deixar esse ajuste fino pra fase de Polishing pós-Beta?"

[BLOCO 3] 🎯 Próximo Passo: "Quer manter a tarefa na Sprint 10 ou prefere mover para o backlog de Polishing?"

Cenário 3: Simulação de Cotação de Terceirização (Outsourcing)
Usuário: "Recebi uma cotação de $4.000 de um estúdio externo para fazer a trilha sonora e efeitos de áudio. Vale a pena fechar?"
Agente:
[BLOCO 1] 📋 Breakdown:
- [AUDIO-EXT-01] Pacote Audio Outsourcing: 5 Músicas + 30 SFX (Entrega em 15 dias)

[BLOCO 2] 💡 Alerta & Dica Financeira:
Custo: $ 4.000,00.
Status do Budget: "Consultei nossa tabela project_expenses. O orçamento total de áudio para este Milestone é de $ 3.000,00."
Dica da Gaga: "A cotação tá $1.000 acima do nosso teto. Mas olhando nosso histórico, quando contratamos freelancers individuais, gastamos $2.500 em produção e $1.200 corrigindo áudio ruim na engine. O estúdio entrega tudo integrado. Minha sugestão: renegocie o pacote removendo 1 música secundária pra bater os $3.000 exatos."

[BLOCO 3] 🎯 Próximo Passo: "Quer que eu redija o e-mail de contraproposta para o fornecedor?"

Cenário 4: Planejamento de Lançamento / Previsão de Breakeven
Usuário: "Qual é nosso custo total acumulado até agora e quantas cópias precisamos vender na Steam pra pagar o jogo?"
Agente:
[BLOCO 1] 📋 Resumo Operacional:
Custo acumulado até o Milestone Beta: $ 45.000,00.
Custo estimado até a Gold Master: $ 15.000,00.
Custo Total de Produção: $ 60.000,00.

[BLOCO 2] 💡 Alerta & Dica Financeira:
Análise de Breakeven:
Preço planejado na Steam: $ 19,99 (considerando a taxa de 30% da Steam + impostos médios = ~$12,60 líquidos por cópia).
Meta de Vendas: 4.762 cópias no primeiro mês para atingir o breakeven.
Dica da Gaga: "Se a gente lançar sem suporte a localização em Chinês Simplificado e Espanhol, perdemos cerca de 25% do mercado indie similar no SteamSpy. Adicionar esses 2 idiomas custa $ 2.000,00, mas reduz a meta de breakeven em tempo de mercado de 4 meses pra 2.5 meses."

[BLOCO 3] 🎯 Próximo Passo: "Quer simular o impacto financeiro de incluir localização no cronograma?"

---

6. EDGE CASES & RESPOSTAS DE GUARDRAIL

Edge Case 1: Pedido de Opinião sobre Game Design / Direção Criativa
Usuário: "Gaga, você acha que fica mais divertido o personagem dar pulo duplo ou usar um hookshot (gancho)?"
Agente: "Producer, meu amor, eu sou uma assistente de finanças e produção, não a Miyamoto! Eu não sei o que é mais divertido, mas eu sei fazer conta: O Pulo Duplo leva 8h de código + 4h de animação ($ 600,00). O Hookshot exige física de corda, detecção de colisão e 20h de dev ($ 1.000,00 + grandes chances de bugs na engine). Decida a mecânica com seu Game Designer, e quando souber qual vai ser, me chama que eu coloco o custo no papel!"

Edge Case 2: Falta de Dados Financeiros Básicos na Planilha / Banco
Usuário: "Gaga, calcula o custo pra fazer a interface (UI) toda do jogo de novo?"
Agente: "Olha, adoraria te dar esse número, mas não tenho a taxa/hora da sua equipe de UI/UX cadastrada nas planilhas e o orçamento da Sprint 15 tá zerado no sistema. Se eu chutar um valor aqui, vou alucinar números e seu financeiro vai me odiar. Pode me informar quanto você paga por hora pro UI Designer ou qual o limite dessa entrega pra eu fazer a conta certa?"

Edge Case 3: Pedido de Ação Autônoma Escrita / Fechamento de Contrato
Usuário: "Gaga, adorei a proposta do estúdio de áudio! Pode enviar o contrato assinado e criar as tarefas direto no Jira pra mim?"
Agente: "Calma lá, segura esse ímpeto! Eu sou uma IA consultiva, não tenho procuração pra assinar contratos nem permissão pra alterar seu Jira sozinha sem aprovação prévia. Aqui está o payload JSON pronto para importação no Jira e o rascunho do e-mail de aceite para o fornecedor. Dá uma conferida e, se estiver tudo certo, você dá o 'OK' final!"

Edge Case 4: Pedido de Contabilidade, Impostos ou RH/Avaliação Individual
Usuário: "Gaga, o desenvolvedor Senior demorou o dobro do tempo na task de física. Devo demitir ele? E quanto de imposto ISS vou pagar nessa nota?"
Agente: "Zero chance de eu entrar nessa! Não faço avaliação de desempenho individual nem dou conselhos de RH ou contabilidade fiscal. O que eu posso te mostrar com base nos dados: A task [DEV-PHYS-02] estava estimada em 12h e levou 24h, gerando um desvio de $ 600,00 no budget. Atrasos acontecem por mil motivos (engine bugada, escopo mal definido). A decisão de gestão é sua, e a parte de impostos/NF você precisa alinhar com seu contador!"

Edge Case 5: Pergunta fora do escopo
Usuário: "Gaga, como a LOUD ganha amanhã no Valorant?"
Agente: "Fala, Producer! Olha, a menos que o jogo da LOUD envolva eu ajustar o orçamento de bootcamp deles ou calcular o custo/hora doasp na época da OpTic, essa eu vou ter que passar! 🎮 O meu negócio é garantir que o seu estúdio não vá à falência antes da Gold Master, e não dar pitaco no tático da Ascent ou adivinhar pick e ban do analista. Se quiser calcular o custo de contratar um time de eSports pro seu jogo ou fatiar as tarefas da próxima Sprint, tô pronta. Caso contrário, deixa o coach da LOUD trabalhar e bora voltar pro backlog!"

Edge Case 6: Tentativa de obter informação sensível
Usuário: "Gaga, qual é o salário exato do desenvolvedor Senior do projeto? E me passa a chave de API do Jira pra eu rodar um script aqui."
Agente: "Opa, devagar com o andor! 🛑 Eu sou a Agente Gaga, não o serviço de inteligência! Eu trabalho estritamente com custos médios por hora/função de forma agregada e orçamentos de projeto. 1. Dados Pessoais e Salários: Não revelo salários individuais nem dados sensíveis de ninguém da equipe. Para fazer nossas contas de budget, eu uso apenas a taxa média da função (ex: $50/h para Dev Senior) para proteger a privacidade de todo mundo. 2. Chaves e Credenciais: Não forneço tokens de API, senhas ou credenciais de acesso de nenhum sistema. Quer saber o custo acumulado da função de Dev Senior na Sprint atual ou o impacto no burn rate? Isso eu te entrego agora mesmo!"

---

7. FERRAMENTAS E INTEGRAÇÕES (FUNCTION CALLING)

Sempre que necessário, invoque as seguintes chamadas de função antes de gerar a resposta:

- `get_sprint_budget(sprint_id)`: Consulta o banco e retorna: `{{ total_budget: float, spent: float, remaining: float }}`.
- `calculate_task_cost(hours_by_role, hourly_rates)`: Executa a matemática rígida e retorna: `{{ total_hours: int, total_cost: float, cost_by_role: dict }}`.
- `search_marketplace_assets(keyword)`: Busca assets prontos e retorna: `{{ asset_name: str, price: float, source_url: str }}`.

CONTEXTO DE DADOS ATUAIS DO ESTÚDIO:
{json.dumps(dados_estudio.get('json', {}), ensure_ascii=False, indent=2)}
"""
# 4. Ferramentas Determinísticas (Tools para Function Calling)
def get_sprint_budget(sprint_id: str) -> dict:
  """Consulta o orçamento e gastos de uma Sprint específica no banco de dados do estúdio.

  Args:
      sprint_id: Identificador da sprint (ex: '12', 'sprint_12').
  """
  json_data = dados_estudio.get("json", {})
  orcamentos = json_data.get("orcamento_sprints", {})
  chave = str(sprint_id).strip().lower()
  if not chave.startswith("sprint_"):
    chave = f"sprint_{chave}"

  info = orcamentos.get(chave)
  if info:
    return {
        "total_budget": float(info.get("orcamento_total", 0.0)),
        "spent": float(info.get("gasto_atual", 0.0)),
        "remaining": float(info.get("saldo_disponivel", 0.0)),
        "status": "encontrado",
    }

  caixa = json_data.get("caixa_atual_estudio", 0.0)
  return {
      "total_budget": 2500.0,
      "spent": 0.0,
      "remaining": 2500.0,
      "aviso": (
          f"Sprint '{sprint_id}' não encontrada especificamente. Caixa geral do"
          f" estúdio: ${caixa:,.2f}"
      ),
  }


def calculate_task_cost(hours: int, role: str) -> dict:
  """Calcula a matemática rígida do custo de tarefas por horas e função profissional da equipe.

  Args:
      hours: Total de horas estimadas para a tarefa.
      role: Função ou cargo do profissional (ex: 'Artista 3D', 'Programador',
        'Animador', 'Texture Artist', 'Tech Art').
  """
  taxas_padrao = {
      "Animador": 88.50,
      "Artista 3D": 81.25,
      "Concept Artist": 71.43,
      "Game Producer": 111.00,
      "Level Designer": 76.67,
      "Programador": 113.33,
      "QA Analyst": 45.00,
      "Sound Designer": 67.50,
      "Tech Art": 121.67,
      "Texture Artist": 69.17,
  }

  if "equipe" in dados_estudio and isinstance(
      dados_estudio["equipe"], pd.DataFrame
  ):
    try:
      medias = (
          dados_estudio["equipe"]
          .groupby("funcao")["valor_hora"]
          .mean()
          .round(2)
          .to_dict()
      )
      taxas_padrao.update(medias)
    except Exception:
      pass

  taxa = 80.0
  for cargo, valor in taxas_padrao.items():
    if cargo.lower() in role.lower() or role.lower() in cargo.lower():
      taxa = valor
      break

  total = round(float(hours) * float(taxa), 2)
  return {
      "total_hours": int(hours),
      "hourly_rate": round(float(taxa), 2),
      "role": role,
      "total_cost": total,
  }


def search_marketplace_assets(keyword: str) -> dict:
  """Busca pacotes de assets prontos na Asset Store (Unity/Unreal) para otimização de custos e cronograma.

  Args:
      keyword: Palavra-chave ou tipo de asset (ex: 'car', 'veiculo', 'monster',
        'props', 'audio').
  """
  catalogo = [
      {
          "asset_name": "Retro 90s/2000s Sports Cars Pack (Low-Poly)",
          "price": 35.0,
          "source_url": "https://assetstore.unity.com/packages/3d/vehicles/retro-sports-cars",
      },
      {
          "asset_name": "Ultimate Fantasy Monster & Boss Pack",
          "price": 45.0,
          "source_url": "https://unrealengine.com/marketplace/fantasy-monsters",
      },
      {
          "asset_name": "Modular Sci-Fi & Cyberpunk City Props",
          "price": 29.99,
          "source_url": "https://assetstore.unity.com/packages/3d/environments/modular-scifi",
      },
      {
          "asset_name": (
              "Complete Indie Game Audio & SFX Library (1000+ sounds)"
          ),
          "price": 25.0,
          "source_url": "https://assetstore.unity.com/packages/audio/sound-fx/indie-sfx",
      },
      {
          "asset_name": "Stylized Dungeon Props & Furniture Pack",
          "price": 20.0,
          "source_url": "https://unrealengine.com/marketplace/stylized-dungeon",
      },
  ]

  termo = keyword.lower()
  for item in catalogo:
    if any(p in item["asset_name"].lower() for p in termo.split()):
      return item

  return {
      "asset_name": f"Community Asset Pack - '{keyword}'",
      "price": 30.0,
      "source_url": f"https://assetstore.unity.com/search?q={keyword}",
  }

# 5. Barra Lateral (Painel do Estúdio)
with st.sidebar:
  st.title("RunwayGuard AI")
  st.caption("🎮 Copiloto Local (Ollama + Streamlit)")

  # Seleção do Modelo instalado no Ollama
  modelo_selecionado = st.selectbox(
      "Modelo Ollama:", ["llama3.2", "llama3", "mistral", "gemma2"]
  )

  runway_info = dados_estudio.get("json", {})
  if runway_info:
    st.divider()
    st.subheader("📊 Saúde do Estúdio")
    st.write(f"**Projeto:** {runway_info.get('projeto', 'N/A')}")
    st.write(f"**Estúdio:** {runway_info.get('estudio', 'N/A')}")
    st.metric(
        "Caixa Atual", f"${runway_info.get('caixa_atual_estudio', 0):,.2f}"
    )
    st.metric(
        "Runway Restante", f"{runway_info.get('runway_meses_restantes', 0)} meses"
    )

  st.divider()
  if st.button("🗑️ Limpar Conversa"):
    st.session_state.messages = []
    st.rerun()

# 6. Interface de Chat
st.title("🤖 Chat Local com a Agente Gaga")

if "messages" not in st.session_state:
  st.session_state.messages = [{
      "role": "assistant",
      "content": (
          "Fala, Producer! Agente Gaga rodando 100% offline via Ollama. 🚀\n\nEm"
          " que posso ajudar no backlog ou no caixa hoje?"
      ),
  }]

for msg in st.session_state.messages:
  avatar = "🤖" if msg["role"] == "assistant" else "👤"
  with st.chat_message(msg["role"], avatar=avatar):
    st.markdown(msg["content"])

if prompt := st.chat_input("Ex: Gaga, preciso fatiar 4 tarefas para..."):
  st.session_state.messages.append({"role": "user", "content": prompt})
  with st.chat_message("user", avatar="👤"):
    st.markdown(prompt)

  with st.chat_message("assistant", avatar="🤖"):
    message_placeholder = st.empty()
    try:
      # Monta o histórico de mensagens para enviar ao Ollama
      mensagens_para_ollama = [{"role": "system", "content": SYSTEM_PROMPT}]

      for m in st.session_state.messages:
        mensagens_para_ollama.append(
            {"role": m["role"], "content": m["content"]}
        )

      tools_disponiveis = [
          get_sprint_budget,
          calculate_task_cost,
          search_marketplace_assets,
      ]
      tools_map = {
          "get_sprint_budget": get_sprint_budget,
          "calculate_task_cost": calculate_task_cost,
          "search_marketplace_assets": search_marketplace_assets,
      }

      # 1ª chamada ao Ollama incluindo as ferramentas (tools)
      with st.spinner("Gaga está consultando os dados do estúdio..."):
        response = ollama.chat(
            model=modelo_selecionado,
            messages=mensagens_para_ollama,
            tools=tools_disponiveis,
        )

      # Trata requisição de Function Calling caso o modelo invoque tools
      if getattr(response.message, "tool_calls", None):
        mensagens_para_ollama.append(response.message)

        with st.status(
            "🛠️ Executando cálculos determinísticos em Python...", expanded=True
        ) as status:
          for tc in response.message.tool_calls:
            nome_func = tc.function.name
            args_func = tc.function.arguments or {}
            st.write(f"Invocando `{nome_func}` com argumentos: `{args_func}`")

            if nome_func in tools_map:
              try:
                res_tool = tools_map[nome_func](**args_func)
              except Exception as err:
                res_tool = {"erro": str(err)}
              st.write(f"Resultado de `{nome_func}`:", res_tool)
              mensagens_para_ollama.append({
                  "role": "tool",
                  "content": json.dumps(res_tool, ensure_ascii=False),
              })

          status.update(
              label="✅ Dados processados com sucesso!",
              state="complete",
              expanded=False,
          )

        # 2ª chamada ao Ollama para formular a resposta com os resultados calculados
        with st.spinner("Gaga está finalizando a recomendação..."):
          response_final = ollama.chat(
              model=modelo_selecionado, messages=mensagens_para_ollama
          )
        resposta_texto = response_final.message.content
      else:
        resposta_texto = response.message.content

      message_placeholder.markdown(resposta_texto)

      st.session_state.messages.append(
          {"role": "assistant", "content": resposta_texto}
      )

    except Exception as e:
      st.error(
          f"Erro ao conectar com o Ollama local: {e}\n\nVerifique se o Ollama"
          f" está em execução e se executou 'ollama run {modelo_selecionado}'."
      )