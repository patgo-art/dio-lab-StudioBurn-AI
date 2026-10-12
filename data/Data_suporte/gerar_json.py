import json
import os

# Garante que a pasta data/ existe
os.makedirs("data", exist_ok=True)

dados_estudio = {
    "projeto": "RunwayGuard AI",
    "estudio": "Nebula Shift Studios",
    "milestone_atual": "Alpha",
    "sprint_atual": 12,
    "caixa_atual_estudio": 45000.00,
    "burn_rate_mensal_estimado": 12500.00,
    "runway_meses_restantes": 3.6,
    "orcamento_sprints": {
        "sprint_12": {
            "orcamento_total": 2500.00,
            "gasto_atual": 1300.00,
            "saldo_disponivel": 1200.00,
        },
        "sprint_13": {
            "orcamento_total": 2800.00,
            "gasto_atual": 0.00,
            "saldo_disponivel": 2800.00,
        },
    },
    "previsao_lancamento_steam": {
        "preco_sugerido_usd": 19.99,
        "taxa_plataforma_porcentagem": 0.30,
        "meta_breakeven_copias": 4762,
    },
}

caminho_arquivo = os.path.join("data", "project_budget_runway.json")

with open(caminho_arquivo, "w", encoding="utf-8") as f:
  json.dump(dados_estudio, f, ensure_ascii=False, indent=2)

print(f"✅ Arquivo criado com sucesso em: {caminho_arquivo}")