# Databricks notebook source
# MAGIC %md
# MAGIC # 01 — Connecting to your Data
# MAGIC
# MAGIC Welcome! In this notebook you'll load **real Calgary Open Data** into Delta tables
# MAGIC in Unity Catalog. Everything you need is already bundled in this repo — no downloads.
# MAGIC
# MAGIC **Datasets** (from [data.calgary.ca](https://data.calgary.ca)):
# MAGIC | Table | What it is | Rows |
# MAGIC |---|---|---|
# MAGIC | `c311` | 311 service requests, last 12 months | ~500K |
# MAGIC | `pets` | Licensed cats & dogs by community, monthly since 2018 | ~43K |
# MAGIC | `crime` | Crime counts by community & category, 2018–2024 | ~77K |
# MAGIC | `traffic` | Traffic incidents (near-live feed) | ~62K |
# MAGIC | `population` | Civic census population by community, 1958–2019 | ~10K |
# MAGIC | `communities` | Community → sector / ward lookup | ~312 |
# MAGIC
# MAGIC Most tables join on `comm_code` or the uppercase community name.
# MAGIC
# MAGIC **▶ Run all cells** (Run menu → Run all). Takes about 2 minutes.

# COMMAND ----------

CATALOG = "workspace"   # Free Edition default catalog
SCHEMA = "calgary"

spark.sql(f"CREATE SCHEMA IF NOT EXISTS {CATALOG}.{SCHEMA}")
spark.sql(f"USE {CATALOG}.{SCHEMA}")
print(f"Tables will be created in {CATALOG}.{SCHEMA}")

# COMMAND ----------

# MAGIC %md
# MAGIC The CSVs live in this repo's `data/` folder, which was cloned into your workspace
# MAGIC when you imported the repo. We read them with pandas and save as **Delta tables**.

# COMMAND ----------

import os
from pathlib import Path

import pandas as pd

DATA_DIR = Path(os.getcwd()).parent / "data"
assert DATA_DIR.exists(), f"Can't find {DATA_DIR} — did you import the full repo as a Git folder?"

TABLE_COMMENTS = {
    "communities": "Calgary communities lookup: comm_code, name (UPPERCASE), class, sector, ward number.",
    "pets": "Licensed pets (CATS/DOGS) per community per month since 2018. license_volume = number of active licenses.",
    "crime": "Monthly crime counts by community name and category, Jan 2018 - Sep 2024 (historical).",
    "traffic": "Traffic incidents with location text, timestamp, quadrant (NW/NE/SW/SE) and lat/long. No community column.",
    "population": "Civic census population and dwellings by community, 1958-2019. Use census_year=2019 for per-capita math.",
    "c311": "311 service requests since June 2025: service_name, agency, status, community (comm_code/comm_name), lat/long.",
}

for name, comment in TABLE_COMMENTS.items():
    pdf = pd.read_csv(DATA_DIR / f"{name}.csv.gz")
    df = spark.createDataFrame(pdf)
    df.write.mode("overwrite").option("overwriteSchema", "true").saveAsTable(name)
    spark.sql(f"COMMENT ON TABLE {name} IS '{comment}'")
    print(f"✓ {CATALOG}.{SCHEMA}.{name:12s} {len(pdf):>8,} rows")

print("\nAll tables created!")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Take a look
# MAGIC Which communities have the most licensed pets right now?

# COMMAND ----------

# MAGIC %sql
# MAGIC SELECT community_name, animal, license_volume
# MAGIC FROM pets
# MAGIC WHERE date = (SELECT MAX(date) FROM pets) AND community_name IS NOT NULL
# MAGIC ORDER BY license_volume DESC
# MAGIC LIMIT 10

# COMMAND ----------

# MAGIC %md
# MAGIC And the top 311 complaint types in the last year:

# COMMAND ----------

# MAGIC %sql
# MAGIC SELECT service_name, COUNT(*) AS requests
# MAGIC FROM c311
# MAGIC GROUP BY service_name
# MAGIC ORDER BY requests DESC
# MAGIC LIMIT 10

# COMMAND ----------

# MAGIC %md
# MAGIC ## Try it yourself (2 min)
# MAGIC
# MAGIC 1. Open the **Catalog** icon in the left sidebar → `workspace` → `calgary` → click a table to see its schema and sample data.
# MAGIC 2. Add a cell below and ask the **Assistant** (the ✦ icon, or right-click → "Generate with Assistant") something like:
# MAGIC    *"write a SQL query showing crime count by year for the BELTLINE community"* — this is vibe-coding, Databricks style.
# MAGIC
# MAGIC **Next up:** `GENIE_SETUP.md` in this repo — create a Genie space and talk to these tables in plain English. Then notebook `02_simple_agent`.
