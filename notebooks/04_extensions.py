# Databricks notebook source
# MAGIC %md
# MAGIC # 04 — Experimentation Time: Fun Extensions
# MAGIC
# MAGIC Pick anything below, or keep extending your supervisor from notebook 03.
# MAGIC At the end, be ready to show the group one thing you built or discovered!

# COMMAND ----------

# MAGIC %md
# MAGIC ## 1. AI in plain SQL — `ai_query` and friends
# MAGIC
# MAGIC You don't always need an agent. Databricks SQL has **AI functions** that call an LLM
# MAGIC per row. One line of SQL = LLM over your whole table.

# COMMAND ----------

# MAGIC %sql
# MAGIC -- Summarize what's bugging a community, from raw 311 data, in one query
# MAGIC SELECT ai_query(
# MAGIC   'databricks-gpt-oss-20b',
# MAGIC   'In 2 sentences, what do these 311 complaint types say about life in this neighbourhood? ' ||
# MAGIC    concat_ws(', ', collect_list(service_name))
# MAGIC ) AS neighbourhood_vibe
# MAGIC FROM (
# MAGIC   SELECT service_name FROM workspace.calgary.c311
# MAGIC   WHERE comm_name = 'BELTLINE' LIMIT 100
# MAGIC )

# COMMAND ----------

# MAGIC %sql
# MAGIC -- Classify traffic incidents by severity — no training, no labels, just ai_classify
# MAGIC SELECT description,
# MAGIC        ai_classify(description, ARRAY('minor', 'major', 'hazard')) AS severity
# MAGIC FROM workspace.calgary.traffic
# MAGIC ORDER BY start_dt DESC
# MAGIC LIMIT 10

# COMMAND ----------

# MAGIC %md
# MAGIC ## 2. Give your agent a calculator (or any Python function)
# MAGIC
# MAGIC Tools don't have to be SQL. Go back to notebook 02 and add a second tool, e.g.:
# MAGIC
# MAGIC ```python
# MAGIC @mlflow.trace
# MAGIC def haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> str:
# MAGIC     """Distance between two points in km."""
# MAGIC     from math import asin, cos, radians, sin, sqrt
# MAGIC     dlat, dlon = radians(lat2 - lat1), radians(lon2 - lon1)
# MAGIC     a = sin(dlat/2)**2 + cos(radians(lat1)) * cos(radians(lat2)) * sin(dlon/2)**2
# MAGIC     return f"{6371 * 2 * asin(sqrt(a)):.2f} km"
# MAGIC ```
# MAGIC
# MAGIC ...then ask: *"How far is the most recent traffic incident from the University of Calgary (51.0775, -114.1335)?"*

# COMMAND ----------

# MAGIC %md
# MAGIC ## 3. Challenge ideas (ranked by ambition)
# MAGIC
# MAGIC | Level | Challenge |
# MAGIC |---|---|
# MAGIC | 🟢 | Make a specialist that answers ONLY about your own neighbourhood. |
# MAGIC | 🟢 | Ask Genie Code to build a chart of pets vs population by sector. |
# MAGIC | 🟡 | Add a `traffic_analyst` specialist to the supervisor (the notebook 03 exercise). |
# MAGIC | 🟡 | Make the supervisor produce a "City Pulse Report": one paragraph per domain. |
# MAGIC | 🔴 | Use `ai_query` *inside* a tool, so your agent can do per-row LLM analysis. |
# MAGIC | 🔴 | Build an eval set: 5 questions with known answers, score your agent with MLflow. |
# MAGIC
# MAGIC ## 4. Where to go from here
# MAGIC
# MAGIC Today you hand-built the loop. On the full Databricks platform this scales up to:
# MAGIC
# MAGIC - **Agent Bricks** — managed Knowledge Assistants (RAG over your documents) and
# MAGIC   Supervisor Agents (what we built in 03, productionized) — [docs](https://docs.databricks.com/aws/en/generative-ai/agent-bricks/)
# MAGIC - **MLflow evaluation** — score agent quality with LLM judges, catch regressions
# MAGIC - **Model Serving** — deploy your agent as a REST endpoint
# MAGIC - **Databricks Apps** — wrap it in a chat UI (3 free apps in your Free Edition account!)
# MAGIC - **Vector Search** — add semantic retrieval over documents as another tool
# MAGIC
# MAGIC Your Free Edition workspace is yours to keep — everything you built today stays.
