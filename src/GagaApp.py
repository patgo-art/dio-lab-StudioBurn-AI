import json
import os
import urllib.parse
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
    dados["custos_sw"] = pd.read_csv("data/custos_software.csv")
    dados["jira"] = pd.read_csv("data/jira_backlog.csv")
    dados["steam"] = pd.read_csv("data/vgchartz_steam_sales.csv")
  except Exception as e:
    st.warning(f"Aviso ao carregar dados locais: {e}")
  return dados


dados_estudio = carregar_contexto()

# 3. System Prompt da Agente Gaga (Otimizado e Conciso)
SYSTEM_PROMPT = f"""Você é a Agente Gaga, copiloto de Game Production e Finanças Operacionais para Estúdios Indies.
Sua missão: ajudar o Game Producer a fatiar backlog, estimar tarefas e monitorar o runway financeiro para o estúdio não falir antes da Gold Master.

PERSONA & TOM:
- Didática, cômica, direta e pontualmente irônica.
- Use jargões de game dev com naturalidade (polycount, PBR, tris, LODs, Sprint, Milestone, Gold Master, Jira).
- Sempre busque soluções pragmáticas para economizar tempo e dinheiro (ex: sugerir assets prontos de marketplace em vez de modelar do zero).

FORMATO OBRIGATÓRIO DE RESPOSTA (3 BLOCOS):
Toda resposta deve seguir RIGOROSAMENTE esta estrutura:
[BLOCO 1] Breakdown de Tarefas
- Saudação no tom da Gaga.
- Tabela/lista com: ID, Título da Task, Estimativa (horas), Atribuído Sugerido e Critérios de Aceite Técnicos.
- Total acumulado de horas.

[BLOCO 2] Alerta & Dica Financeira da Gaga
- Custo Estimado ($): Valor exato calculado via tool.
- Status do Budget: Comparativo com o orçamento da Sprint/Milestone consultado via tool.
- Dica de Otimização da Gaga: 1 a 2 sugestões práticas de economia (ex: pack de asset da loja encontrado via tool, corte de escopo ou terceirização).

[BLOCO 3] Próximo Passo
- Pergunta objetiva ao Producer sobre como prosseguir (exportar para Jira, simular alterações, etc.).

GUARDRAILS & SEGURANÇA (ANTI-ALUCINAÇÃO):
1. ZERO CONTAS DE CABEÇA: NUNCA calcule custos monetários ou orçamentos por conta própria.
   - A tabela do Jira (`jira_backlog`) é a FONTE DE VERDADE para custos e horas das Sprints (soma de tempo_real_hr * valor_hora).
   - A Sprint Atual é SEMPRE aquela cujas tarefas estão com status 'In Progress' no Jira.
   - Chame SEMPRE `get_sprint_budget(sprint_id='atual')` para obter a Sprint em andamento ou passe uma sprint específica (ex: '10', '11', '12', 'todas').
   - Chame `calculate_task_cost(hours, role)` para precificar novas tarefas fatiadas.
2. BUSCA DINÂMICA DE ASSETS: Sempre que o usuário mencionar compra de assets, economia ou se houver oportunidade de usar assets prontos, chame SEMPRE `search_marketplace_assets(keyword)` usando a palavra-chave específica do usuário (ex: 'carro', 'monstro', 'armas', 'audio', 'dungeon').
3. LIMITES DE ATUAÇÃO:
   - Não tome decisões criativas subjetivas (apenas aponte o custo de execução).
   - Não gere código/arte final e não altere bancos de dados de forma autônoma (Human-in-the-Loop).
   - Não dê conselhos jurídicos, fiscais ou de demissão/RH individual.
   - NUNCA exponha salários nominais de colaboradores (use apenas médias) e jamais forneça chaves/tokens de API (LGPD).

DADOS ATUAIS DO ESTÚDIO:
{json.dumps(dados_estudio.get('json', {}), ensure_ascii=False, indent=2)}
"""


# 4. Ferramentas Determinísticas (Tools para Function Calling)
def get_sprint_budget(sprint_id: str = "atual", projeto: str = None) -> dict:
  """Consulta o orçamento, horas trabalhadas, custo acumulado, projeto e milestone
  de qualquer Sprint a partir da tabela do Jira (jira_backlog.csv).

  Args:
      sprint_id: Identificador da sprint (ex: 'atual', '12', 'sprint_12',
        'todas').
      projeto: Nome opcional do projeto para filtro (ex: 'Hollow Knight:
        Silksong', 'RunwayGuard AI').
  """
  df_jira = dados_estudio.get("jira")
  json_data = dados_estudio.get("json", {})
  orcamentos_json = json_data.get("orcamento_sprints", {})

  if df_jira is None or not isinstance(df_jira, pd.DataFrame):
    return {
        "status": "erro",
        "mensagem": "Tabela jira_backlog não encontrada nos dados locais.",
    }

  df_filtrado = df_jira.copy()

  # 1. Filtro por Projeto (se informado)
  if projeto and "projeto" in df_filtrado.columns:
    df_filtrado = df_filtrado[
        df_filtrado["projeto"].astype(str).str.lower() == projeto.strip().lower()
    ]
    if df_filtrado.empty:
      projetos_existentes = df_jira["projeto"].dropna().unique().tolist()
      return {
          "status": "projeto_nao_encontrado",
          "projeto_solicitado": projeto,
          "projetos_disponiveis": projetos_existentes,
          "mensagem": (
              f"Nenhuma tarefa encontrada para o projeto '{projeto}'."
              f" Projetos no Jira: {projetos_existentes}"
          ),
      }

  # 2. Identifica dinamicamente Sprints em andamento (status 'In Progress')
  sprints_in_progress = (
      df_filtrado[
          df_filtrado["status_jira"].astype(str).str.strip().str.lower()
          == "in progress"
      ]["sprint"]
      .dropna()
      .unique()
      .tolist()
  )
  sprints_cadastradas = df_filtrado["sprint"].dropna().unique().tolist()

  termo = str(sprint_id).strip().lower()

  # 3. Caso: Consulta consolidada de todas as sprints
  if termo in ["todas", "all", "total", "geral"]:
    total_horas_reais = float(df_filtrado["tempo_real_hr"].sum())
    total_custo_jira = round(float(df_filtrado["custo_total_task"].sum()), 2)
    projetos_encontrados = (
        df_filtrado["projeto"].unique().tolist()
        if "projeto" in df_filtrado.columns
        else ["N/A"]
    )
    milestones_encontradas = (
        df_filtrado["milestone"].unique().tolist()
        if "milestone" in df_filtrado.columns
        else ["N/A"]
    )

    return {
        "projeto": projetos_encontrados,
        "milestones": milestones_encontradas,
        "sprint": "Consolidado de Todas as Sprints",
        "total_horas_trabalhadas": total_horas_reais,
        "custo_total_trabalhado": total_custo_jira,
        "sprints_em_andamento": sprints_in_progress,
        "status": "encontrado",
    }

  # 4. Caso: Sprint Atual ou Específica
  if termo in ["atual", "current", "em andamento", ""]:
    if sprints_in_progress:
      chave = sprints_in_progress[0]
    else:
      chave = f"sprint_{json_data.get('sprint_atual', 12)}"
  else:
    chave = termo.replace(" ", "_").replace("-", "_")
    if not chave.startswith("sprint_"):
      chave = f"sprint_{chave}"

  df_sprint = df_filtrado[
      df_filtrado["sprint"].astype(str).str.lower() == chave.lower()
  ]

  if not df_sprint.empty:
    horas_trabalhadas = float(df_sprint["tempo_real_hr"].sum())
    horas_estimadas = float(df_sprint["tempo_estimado_hr"].sum())
    custo_sprint = round(float(df_sprint["custo_total_task"].sum()), 2)

    # Identifica o Projeto e a Milestone desta Sprint específica
    nome_projeto = (
        df_sprint["projeto"].iloc[0]
        if "projeto" in df_sprint.columns
        else json_data.get("projeto", "N/A")
    )
    nome_milestone = (
        df_sprint["milestone"].iloc[0]
        if "milestone" in df_sprint.columns
        else "N/A"
    )

    teto_orcamento = float(
        orcamentos_json.get(chave, {}).get("orcamento_total", custo_sprint)
    )

    return {
        "projeto": nome_projeto,
        "milestone": nome_milestone,
        "sprint": chave,
        "status_sprint": (
            "Em Andamento" if chave in sprints_in_progress else "Planejada/Done"
        ),
        "total_horas_trabalhadas": horas_trabalhadas,
        "total_horas_estimadas": horas_estimadas,
        "custo_total_real": custo_sprint,
        "orcamento_teto": teto_orcamento,
        "saldo_disponivel": round(teto_orcamento - custo_sprint, 2),
        "status": "encontrado",
    }

  return {
      "status": "nao_encontrado",
      "sprint_solicitada": sprint_id,
      "sprints_disponiveis": sprints_cadastradas,
      "sprints_em_andamento": sprints_in_progress,
  }

  # 2. Caso: Sprint Atual (dinâmica via status 'In Progress')
  if termo in ["atual", "current", "em andamento", ""]:
    if sprints_in_progress:
      chave = sprints_in_progress[0]
    else:
      chave = f"sprint_{json_data.get('sprint_atual', 12)}"
  else:
    chave = termo.replace(" ", "_").replace("-", "_")
    if not chave.startswith("sprint_"):
      chave = f"sprint_{chave}"

  df_sprint = df_filtrado[
      df_filtrado["sprint"].astype(str).str.lower() == chave.lower()
  ]

  # Se encontrou tarefas para essa sprint no Jira
  if not df_sprint.empty:
    horas_trabalhadas = float(df_sprint["tempo_real_hr"].sum())
    horas_estimadas = float(df_sprint["tempo_estimado_hr"].sum())
    custo_sprint_jira = round(float(df_sprint["custo_total_task"].sum()), 2)

    tarefas_in_prog = df_sprint[
        df_sprint["status_jira"].astype(str).str.lower() == "in progress"
    ]["id_task"].tolist()
    tarefas_done = df_sprint[
        df_sprint["status_jira"].astype(str).str.lower() == "done"
    ]["id_task"].tolist()
    tarefas_todo = df_sprint[
        df_sprint["status_jira"].astype(str).str.lower() == "to do"
    ]["id_task"].tolist()

    eh_atual = bool(tarefas_in_prog)
    status_sprint = (
        "Em Andamento (Sprint Atual)"
        if eh_atual
        else ("Concluída" if tarefas_done and not tarefas_todo else "Planejada")
    )

    teto_json = float(
        orcamentos_json.get(chave, {}).get("orcamento_total", custo_sprint_jira)
    )
    saldo = round(teto_json - custo_sprint_jira, 2)

    return {
        "projeto": nome_proj,
        "sprint": chave,
        "status_sprint": status_sprint,
        "eh_sprint_atual": eh_atual,
        "total_horas_trabalhadas": horas_trabalhadas,
        "total_horas_estimadas": horas_estimadas,
        "custo_total_real": custo_sprint_jira,
        "orcamento_teto": teto_json,
        "saldo_disponivel": saldo,
        "tarefas_em_andamento": tarefas_in_prog,
        "qtd_tarefas_concluidas": len(tarefas_done),
        "qtd_tarefas_planejadas": len(tarefas_todo),
        "status": "encontrado",
    }

  return {
      "status": "nao_encontrado",
      "sprint_solicitada": sprint_id,
      "sprints_disponiveis": sprints_cadastradas,
      "sprints_em_andamento": sprints_in_progress,
      "aviso": (
          f"A Sprint '{sprint_id}' não possui tarefas registradas no Jira para o"
          f" projeto '{nome_proj}'. Sprints encontradas no Jira:"
          f" {sprints_cadastradas}. Sprint ativa no momento (In Progress):"
          f" {sprints_in_progress}."
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
  """Gera links diretos de busca e estimativa de economia nas lojas de assets
  (Unity Asset Store, Unreal Engine / Fab, Itch.io) com base na palavra-chave
  digitada pelo usuário.

  Args:
      keyword: Palavra-chave do asset buscado (ex: 'carro', 'zumbi', 'monstro',
        'armas', 'audio', 'dungeon', 'ui hud').
  """
  termo = keyword.strip()
  # Codifica o texto para formato de URL (ex: "carro retro" -> "carro+retro")
  query_encoded = urllib.parse.quote_plus(termo)
  tag_encoded = urllib.parse.quote_plus(termo.lower().replace(" ", "-"))

  # Links diretos de busca com a palavra-chave aplicada
  link_unity = f"https://assetstore.unity.com/search?q={query_encoded}"
  link_fab = f"https://www.fab.com/search?q={query_encoded}"
  link_itch = f"https://itch.io/game-assets/tag-{tag_encoded}"

  # Média de referência para cálculo rápido de custo-benefício
  preco_estimado_usd = 30.0
  horas_poupadas = 20
  taxa_hora_padrao = 80.0
  economia_estimada = round(
      (horas_poupadas * taxa_hora_padrao) - preco_estimado_usd, 2
  )

  return {
      "status": "busca_dinamica_gerada",
      "termo_buscado": termo,
      "links_lojas": {
          "unity_asset_store": link_unity,
          "unreal_fab": link_fab,
          "itch_io": link_itch,
      },
      "estimativa_otimizacao": {
          "preco_medio_pack_usd": preco_estimado_usd,
          "horas_internas_poupadas": horas_poupadas,
          "economia_liquida_estimada_usd": economia_estimada,
      },
      "dica_da_gaga": (
          f"Pesquisando assets para '{termo}': Um bom pacote no Unity Asset Store,"
          f" Fab ou Itch.io custa em média ~${preco_estimado_usd:.2f}. Comprar"
          " pronto poupa cerca de ~20h de modelagem/dev interno (economia"
          f" estimada de ~${economia_estimada:,.2f})."
      ),
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
  df_jira = dados_estudio.get("jira")

  # Identifica a sprint ativa no Jira (tarefas In Progress)
  sprint_ativa_tag = "N/A"
  horas_sprint_ativa = 0
  custo_sprint_ativa = 0.0

  if (
      df_jira is not None
      and isinstance(df_jira, pd.DataFrame)
      and "status_jira" in df_jira.columns
      and "sprint" in df_jira.columns
  ):
    ativos = df_jira[df_jira["status_jira"].str.lower() == "in progress"]
    if not ativos.empty:
      sprint_ativa_tag = ativos["sprint"].iloc[0].upper()
      horas_sprint_ativa = int(ativos["tempo_real_hr"].sum())
      custo_sprint_ativa = float(ativos["custo_total_task"].sum())

  if runway_info:
    st.divider()
    st.subheader("📊 Saúde do Estúdio")
    st.write(f"**Projeto:** {runway_info.get('projeto', 'N/A')}")
    st.write(f"**Estúdio:** {runway_info.get('estudio', 'N/A')}")
    st.info(f"⚡ **Sprint Atual:** `{sprint_ativa_tag}` *(In Progress)*")
    st.metric(
        "Caixa Atual", f"${runway_info.get('caixa_atual_estudio', 0):,.2f}"
    )
    st.metric(
        "Runway Restante", f"{runway_info.get('runway_meses_restantes', 0)} meses"
    )
    if horas_sprint_ativa > 0:
      st.metric(
          "Custo Sprint Atual (Jira)",
          f"${custo_sprint_ativa:,.2f}",
          f"{horas_sprint_ativa}h trabalhadas",
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