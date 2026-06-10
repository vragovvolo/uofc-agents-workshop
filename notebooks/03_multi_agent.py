# Databricks notebook source
# MAGIC %md
# MAGIC # 03 — Adding Agents & Combining into an Agentic Workflow
# MAGIC
# MAGIC One generalist agent works, but real systems use **specialists**: each agent owns one
# MAGIC domain, with its own focused prompt and tools. A **supervisor** agent routes questions
# MAGIC to the right specialist and combines their answers.
# MAGIC
# MAGIC We'll build:
# MAGIC
# MAGIC ```
# MAGIC                       ┌──────────────────┐
# MAGIC        you ─────────▶│    SUPERVISOR    │
# MAGIC                       └──┬──────┬─────┬─┘
# MAGIC               ┌──────────┘      │     └──────────┐
# MAGIC               ▼                 ▼                ▼
# MAGIC      🐕 pets & people    🚨 city services    🧞 your Genie space
# MAGIC      (pets, population)  (c311, crime,       (optional — plain-English
# MAGIC                           traffic)            SQL agent you built in the UI)
# MAGIC ```
# MAGIC
# MAGIC **Prerequisites:** notebooks `01` and `02` (we reuse the same loop pattern).

# COMMAND ----------

# MAGIC %pip install -q -U openai mlflow
# MAGIC dbutils.library.restartPython()

# COMMAND ----------

import json

import mlflow
from databricks.sdk import WorkspaceClient
from openai import OpenAI

w = WorkspaceClient()
HOST = w.config.host
TOKEN = w.config.authenticate()["Authorization"].replace("Bearer ", "")

available = {e.name for e in w.serving_endpoints.list()}
PREFERRED = [
    "databricks-claude-sonnet-4-5", "databricks-claude-sonnet-4", "databricks-claude-3-7-sonnet",
    "databricks-gpt-oss-120b", "databricks-meta-llama-3-3-70b-instruct", "databricks-gpt-oss-20b",
]
MODEL = next((m for m in PREFERRED if m in available), None)
assert MODEL, f"No known chat model found. Available: {sorted(available)}"

client = OpenAI(api_key=TOKEN, base_url=f"{HOST}/serving-endpoints")
mlflow.openai.autolog()
print(f"Using model endpoint: {MODEL}")

# COMMAND ----------

# MAGIC %md
# MAGIC ## A reusable mini-agent
# MAGIC
# MAGIC Same loop as notebook 02, but packaged as a function so we can stamp out specialists.
# MAGIC Each specialist gets its **own system prompt** describing only the tables it owns —
# MAGIC smaller scope means better SQL and fewer mistakes.

# COMMAND ----------

@mlflow.trace
def run_sql(query: str) -> str:
    """Run SQL and return up to 50 rows as CSV, or the error text so agents can self-correct."""
    try:
        pdf = spark.sql(query).limit(50).toPandas()
        return pdf.to_csv(index=False) or "(no rows)"
    except Exception as e:
        return f"SQL ERROR (fix your query and try again): {e}"


SQL_TOOL = [{
    "type": "function",
    "function": {
        "name": "run_sql",
        "description": "Run a Spark SQL query. Use fully qualified table names like workspace.calgary.pets.",
        "parameters": {
            "type": "object",
            "properties": {"query": {"type": "string"}},
            "required": ["query"],
        },
    },
}]


def make_specialist(name: str, system_prompt: str):
    """Build a mini SQL agent with its own scope. Returns a callable: question -> answer."""

    @mlflow.trace(name=name)
    def specialist(question: str) -> str:
        messages = [{"role": "system", "content": system_prompt},
                    {"role": "user", "content": question}]
        for _ in range(6):
            msg = client.chat.completions.create(
                model=MODEL, messages=messages, tools=SQL_TOOL, tool_choice="auto",
            ).choices[0].message
            messages.append({
                "role": "assistant", "content": msg.content or "",
                "tool_calls": [
                    {"id": tc.id, "type": "function",
                     "function": {"name": tc.function.name, "arguments": tc.function.arguments}}
                    for tc in (msg.tool_calls or [])
                ] or None,
            })
            if not msg.tool_calls:
                return msg.content
            for tc in msg.tool_calls:
                result = run_sql(json.loads(tc.function.arguments)["query"])
                messages.append({"role": "tool", "tool_call_id": tc.id, "content": result})
        return "(specialist hit max hops)"

    return specialist

# COMMAND ----------

# MAGIC %md
# MAGIC ## Specialist 1 — 🐕 Pets & People analyst

# COMMAND ----------

pets_analyst = make_specialist("pets_analyst", """You are the Pets & People analyst for Calgary.
You ONLY know these tables (query with run_sql, fully qualified):
- workspace.calgary.pets: date, community_code, community_name (UPPERCASE), animal (CATS/DOGS), license_volume. Monthly snapshots — for "current" numbers filter to MAX(date).
- workspace.calgary.population: comm_code, name (UPPERCASE), census_year, population. Use census_year=2019 for per-capita.
- workspace.calgary.communities: comm_code, name, sector, ward_num.
Answer with real numbers from SQL. Be concise.""")

print(pets_analyst("Which community has the most licensed cats right now?"))

# COMMAND ----------

# MAGIC %md
# MAGIC ## Specialist 2 — 🚨 City Services analyst

# COMMAND ----------

services_analyst = make_specialist("services_analyst", """You are the City Services analyst for Calgary.
You ONLY know these tables (query with run_sql, fully qualified):
- workspace.calgary.c311: requested_date, status_description, service_name, agency_responsible, comm_code, comm_name (UPPERCASE). Last 12 months of 311 requests.
- workspace.calgary.crime: comm_code, community_name (UPPERCASE), category, crime_count, year, month. 2018-2024 historical.
- workspace.calgary.traffic: incident_info, description, start_dt, quadrant (NW/NE/SW/SE), longitude, latitude. No community column — use quadrant.
Answer with real numbers from SQL. Be concise.""")

print(services_analyst("What are the top 3 311 complaint types in SUNNYSIDE?"))

# COMMAND ----------

# MAGIC %md
# MAGIC ## Specialist 3 (optional) — 🧞 Your Genie space as an agent
# MAGIC
# MAGIC If you created a Genie space (see `GENIE_SETUP.md`), it's already a full text-to-SQL agent —
# MAGIC we can call it through the **Genie Conversation API** and plug it in as one more team member.
# MAGIC
# MAGIC Grab the space ID from your Genie space URL: `.../genie/rooms/<THIS-LONG-ID>` and paste below.
# MAGIC *(Skip this cell if you didn't make one — the supervisor works fine without it.)*

# COMMAND ----------

GENIE_SPACE_ID = ""  # ← paste yours, e.g. "01f01a2b3c4d5e6f..." — or leave empty to skip


@mlflow.trace(name="genie_agent")
def ask_genie(question: str) -> str:
    """Ask the Genie space a question and return its answer (text + SQL + rows)."""
    msg = w.genie.start_conversation_and_wait(space_id=GENIE_SPACE_ID, content=question)
    parts = [f"[genie] {msg.content}"] if msg.content else []
    for att in (msg.attachments or []):
        if att.text and att.text.content:
            parts.append(f"[answer] {att.text.content}")
        if att.query and att.query.query:
            parts.append(f"[sql] {att.query.query}")
            try:
                qr = w.genie.get_message_query_result_by_attachment(
                    space_id=GENIE_SPACE_ID, conversation_id=msg.conversation_id,
                    message_id=msg.message_id, attachment_id=att.attachment_id,
                )
                if qr.statement_response and qr.statement_response.result:
                    rows = qr.statement_response.result.data_array or []
                    parts.append(f"[rows] {rows[:15]}")
            except Exception as e:
                parts.append(f"[rows unavailable: {e}]")
    return "\n".join(parts) or "(genie returned nothing)"


if GENIE_SPACE_ID:
    print(ask_genie("How many 311 requests were there last month?"))
else:
    print("No Genie space configured — supervisor will run with 2 specialists.")

# COMMAND ----------

# MAGIC %md
# MAGIC ## The Supervisor — combining agents into a workflow
# MAGIC
# MAGIC To the supervisor, **each specialist is just a tool**. It never writes SQL itself —
# MAGIC it delegates, reads the specialists' answers, and synthesizes. Watch the trace to see
# MAGIC the routing decisions.

# COMMAND ----------

SPECIALISTS = {
    "ask_pets_analyst": (
        pets_analyst,
        "Pets & population questions: licensed cats/dogs by community, pet trends, per-capita stats, community population.",
    ),
    "ask_services_analyst": (
        services_analyst,
        "City services questions: 311 complaints, crime statistics (2018-2024), traffic incidents by quadrant.",
    ),
}
if GENIE_SPACE_ID:
    SPECIALISTS["ask_genie"] = (
        ask_genie,
        "General Calgary data questions in plain English — a text-to-SQL agent over all the Calgary tables.",
    )

SUPERVISOR_TOOLS = [{
    "type": "function",
    "function": {
        "name": name,
        "description": desc,
        "parameters": {
            "type": "object",
            "properties": {"question": {"type": "string", "description": "A clear, self-contained question"}},
            "required": ["question"],
        },
    },
} for name, (_, desc) in SPECIALISTS.items()]

SUPERVISOR_PROMPT = f"""You are the supervisor of a team of Calgary data analysts.
Your team (call them as tools): {', '.join(SPECIALISTS)}.
You never query data yourself — delegate to the right specialist. For questions spanning
domains, ask multiple specialists and combine their answers. Make follow-up questions
concrete (name the specific communities/categories found in earlier answers).
In your final answer, cite which analyst each fact came from."""


@mlflow.trace(name="supervisor")
def supervisor(question: str, max_hops: int = 8) -> str:
    messages = [{"role": "system", "content": SUPERVISOR_PROMPT},
                {"role": "user", "content": question}]
    for _ in range(max_hops):
        msg = client.chat.completions.create(
            model=MODEL, messages=messages, tools=SUPERVISOR_TOOLS, tool_choice="auto",
        ).choices[0].message
        messages.append({
            "role": "assistant", "content": msg.content or "",
            "tool_calls": [
                {"id": tc.id, "type": "function",
                 "function": {"name": tc.function.name, "arguments": tc.function.arguments}}
                for tc in (msg.tool_calls or [])
            ] or None,
        })
        if not msg.tool_calls:
            return msg.content
        for tc in msg.tool_calls:
            q = json.loads(tc.function.arguments)["question"]
            print(f"  📨 supervisor → {tc.function.name}: {q}")
            answer = SPECIALISTS[tc.function.name][0](q)
            messages.append({"role": "tool", "tool_call_id": tc.id, "content": answer})
    return "(supervisor hit max hops)"

# COMMAND ----------

# MAGIC %md
# MAGIC ## The payoff — a question no single agent can answer

# COMMAND ----------

print(supervisor(
    "Which community has the most licensed dogs, and does that community also rank high "
    "for 311 complaints? Anything interesting when you put those together?"
))

# COMMAND ----------

# MAGIC %md
# MAGIC ## Try it yourself
# MAGIC
# MAGIC - Ask a cross-domain question of your own (pets × crime? population × 311 per capita?).
# MAGIC - Open the **trace** for the supervisor run — count the hops. Did it delegate well?
# MAGIC - Add a **third specialist**: copy the `make_specialist` pattern and give it the `traffic`
# MAGIC   table only, then register it in `SPECIALISTS`. ~5 lines.
# MAGIC - Change the supervisor prompt to require it to **always consult two specialists** — what happens?
# MAGIC
# MAGIC **Next:** `04_extensions` — fun one-liners and where to go from here.
