# Databricks notebook source
# MAGIC %md
# MAGIC # 02 — Building a Simple Agent
# MAGIC
# MAGIC An **agent** is just three things in a loop:
# MAGIC
# MAGIC 1. an **LLM** that can decide what to do,
# MAGIC 2. **tools** it's allowed to call (here: running SQL against your Calgary tables),
# MAGIC 3. a **loop**: the LLM calls a tool → sees the result → decides to call another tool or answer.
# MAGIC
# MAGIC No framework needed — we'll build it from scratch in ~60 lines so you can see every moving part.
# MAGIC
# MAGIC **Prerequisite:** you ran `01_setup_data`.

# COMMAND ----------

# MAGIC %pip install -q -U openai mlflow
# MAGIC dbutils.library.restartPython()

# COMMAND ----------

# MAGIC %md
# MAGIC ## Step 1 — Connect to an LLM
# MAGIC
# MAGIC Databricks hosts foundation models behind OpenAI-compatible endpoints, so the standard
# MAGIC `openai` client works — we just point it at your workspace. We pick the best chat model
# MAGIC available in your workspace automatically.

# COMMAND ----------

from databricks.sdk import WorkspaceClient
from openai import OpenAI

w = WorkspaceClient()
HOST = w.config.host
TOKEN = w.config.authenticate()["Authorization"].replace("Bearer ", "")

available = {e.name for e in w.serving_endpoints.list()}
PREFERRED = [
    "databricks-claude-sonnet-4-5",
    "databricks-claude-sonnet-4",
    "databricks-claude-3-7-sonnet",
    "databricks-gpt-oss-120b",
    "databricks-meta-llama-3-3-70b-instruct",
    "databricks-gpt-oss-20b",
]
MODEL = next((m for m in PREFERRED if m in available), None)
assert MODEL, f"No known chat model found. Available endpoints: {sorted(available)}"

client = OpenAI(api_key=TOKEN, base_url=f"{HOST}/serving-endpoints")
print(f"Using model endpoint: {MODEL}")

# COMMAND ----------

# Say hello — one plain LLM call, no tools yet
resp = client.chat.completions.create(
    model=MODEL,
    messages=[{"role": "user", "content": "In one sentence: what is Calgary famous for?"}],
)
print(resp.choices[0].message.content)

# COMMAND ----------

# MAGIC %md
# MAGIC ## Step 2 — Give it a tool
# MAGIC
# MAGIC An LLM alone knows nothing about *your* data. A **tool** is a Python function plus a
# MAGIC JSON description telling the LLM when and how to call it. Ours runs SQL and returns the rows.
# MAGIC
# MAGIC Note what happens on a bad query: we return the **error message to the agent** instead of
# MAGIC crashing — so it can read the error and fix its own SQL. That's the magic of the loop.

# COMMAND ----------

import mlflow

mlflow.openai.autolog()  # every LLM call gets traced automatically


@mlflow.trace
def run_sql(query: str) -> str:
    """Run SQL against workspace.calgary and return up to 50 rows as CSV text."""
    try:
        pdf = spark.sql(query).limit(50).toPandas()
        return pdf.to_csv(index=False) or "(no rows)"
    except Exception as e:
        return f"SQL ERROR (fix your query and try again): {e}"


TOOLS = [{
    "type": "function",
    "function": {
        "name": "run_sql",
        "description": (
            "Run a Spark SQL query against the workspace.calgary schema. "
            "Tables: c311 (311 requests, last 12 months), pets (licensed cats/dogs by community by month), "
            "crime (monthly counts by community_name + category, 2018-2024), traffic (incidents, quadrant + lat/long), "
            "population (civic census by community, use census_year=2019), communities (comm_code, name, sector, ward_num). "
            "Community names are UPPERCASE, e.g. 'BELTLINE'. Always use fully qualified names like workspace.calgary.pets."
        ),
        "parameters": {
            "type": "object",
            "properties": {"query": {"type": "string", "description": "A single Spark SQL query"}},
            "required": ["query"],
        },
    },
}]

# COMMAND ----------

# MAGIC %md
# MAGIC ## Step 3 — The agent loop
# MAGIC
# MAGIC This is the whole trick: keep calling the LLM until it stops asking for tools.

# COMMAND ----------

import json

SYSTEM_PROMPT = """You are a data analyst agent for the City of Calgary.
Answer questions using the run_sql tool against the workspace.calgary tables.
Look at real data before answering — never guess numbers. Community names are UPPERCASE.
When done, give a concise answer and mention which tables you used."""


@mlflow.trace(name="calgary_agent")
def run_agent(question: str, max_hops: int = 8, verbose: bool = True) -> str:
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": question},
    ]
    for _ in range(max_hops):
        msg = client.chat.completions.create(
            model=MODEL, messages=messages, tools=TOOLS, tool_choice="auto",
        ).choices[0].message

        messages.append({
            "role": "assistant",
            "content": msg.content or "",
            "tool_calls": [
                {"id": tc.id, "type": "function",
                 "function": {"name": tc.function.name, "arguments": tc.function.arguments}}
                for tc in (msg.tool_calls or [])
            ] or None,
        })

        if not msg.tool_calls:           # no more tools → final answer
            return msg.content

        for tc in msg.tool_calls:
            query = json.loads(tc.function.arguments)["query"]
            if verbose:
                print(f"  🔧 running SQL: {query[:120]}...")
            result = run_sql(query)
            messages.append({"role": "tool", "tool_call_id": tc.id, "content": result})
    return "(hit max hops without a final answer)"

# COMMAND ----------

# MAGIC %md
# MAGIC ## Step 4 — Ask it something!

# COMMAND ----------

print(run_agent("Which 5 communities have the most licensed dogs, and how does that compare to their cat counts?"))

# COMMAND ----------

print(run_agent("What are the top 3 types of 311 complaints in the BELTLINE community, and is that different from the city overall?"))

# COMMAND ----------

# MAGIC %md
# MAGIC ## Step 5 — Look inside the agent's head
# MAGIC
# MAGIC Every run was **traced with MLflow**. Click the **Trace** results above (or the experiment
# MAGIC icon 🧪 in the right sidebar) and expand `calgary_agent` — you can see every LLM call, every
# MAGIC SQL query it wrote, every error it recovered from. This is how you debug agents in real life.
# MAGIC
# MAGIC ## Try it yourself (5 min)
# MAGIC
# MAGIC - Ask your own question — try something that needs **two tables** (e.g. pets per capita using `population`).
# MAGIC - Break it on purpose: ask about a table that doesn't exist and watch the trace — how does it recover?
# MAGIC - Edit the `SYSTEM_PROMPT` (make it answer like a pirate, make it always show its SQL) and rerun.
# MAGIC
# MAGIC **Next:** `03_multi_agent` — give your agent *colleagues*.
