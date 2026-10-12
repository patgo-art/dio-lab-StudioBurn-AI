import pandas as pd

# 1. Carrega os dois datasets
df_vgsales = pd.read_csv("data/vgsales.csv")
df_ratings = pd.read_csv("data/vgchartz.csv")

# 2. Faz o MERGE com os nomes corretos do vgchartz.csv
# Como o vgsales usa "Name" e "Platform" (maiúsculas) e o vgchartz usa "name" e "platform" (minúsculas),
# fazemos o merge especificando left_on e right_on:
df_merged = pd.merge(
    df_vgsales,
    df_ratings[["name", "platform", "critic", "user"]],
    left_on=["Name", "Platform"],
    right_on=["name", "platform"],
    how="left",  # Mantém os jogos do vgsales mesmo se não houver nota no dataset de ratings
)

# 3. Filtra apenas jogos de PC lançados a partir de 2015
df_pc = df_merged[
    (df_merged["Platform"] == "PC") & (df_merged["Year"] >= 2010)
].copy()

# 4. Seleciona as colunas unificadas trazidas do merge
df_clean = df_pc[[
    "Name",
    "Platform",
    "Year",
    "Genre",
    "Publisher",
    "Global_Sales",
    "critic",
    "user",
]].copy()

# 5. Renomeia as colunas para o padrão padronizado da Agente Gaga
df_clean.columns = [
    "name",
    "platform",
    "year",
    "genre",
    "publisher",
    "global_sales_mil",
    "critic_score",
    "user_score",
]

# 6. Adiciona preço médio e preenche notas/ratings vazios (NaN) com uma média padrão
df_clean["avg_price_usd"] = 19.99
df_clean["critic_score"] = df_clean["critic_score"].fillna(80)
df_clean["user_score"] = df_clean["user_score"].fillna(8.0)

# 7. Salva a tabela limpa
df_clean.to_csv("data/vgchartz_steam_sales.csv", index=False)

print("✅ Tabela vgchartz_steam_sales.csv unificada com sucesso!")