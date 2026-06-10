# Create a Genie Space — talk to your data in plain English

**Genie** is Databricks' built-in text-to-SQL agent. You configure it with clicks, not code —
and in notebook `03_multi_agent` you can plug it into your agent team via its API.

**Prerequisite:** you ran `notebooks/01_setup_data` (the tables exist in `workspace.calgary`).

## Steps (~3 minutes)

1. In the left sidebar, click **Genie** (under *SQL* — or find it via the search bar at the top).
2. Click **+ New** (top right).
3. **Connect your data:** pick catalog `workspace` → schema `calgary` → select **all 6 tables**
   (`c311`, `communities`, `crime`, `pets`, `population`, `traffic`) → **Create**.
4. Genie opens a chat. That's it — you have a working text-to-SQL agent.

## Ask it things

Start simple, then get weird:

- *Which community has the most licensed dogs?*
- *Show me 311 requests per month as a line chart*
- *Cats vs dogs in BELTLINE over time*
- *Which ward gets the most graffiti complaints?*
- *Top 5 communities by crime in 2024 — and what were their populations in 2019?*

Click **Show code** under any answer to see the SQL Genie wrote. If an answer looks wrong,
say so — Genie takes feedback in the chat.

## Make it smarter (optional, 2 min)

Open **Configure** (left panel inside your Genie space):

- **Instructions** — paste this:
  > Community names are UPPERCASE (e.g. 'BELTLINE'). For "current" pet numbers use the most
  > recent date in pets. Crime data ends Sept 2024; population census ends 2019 — use
  > census_year=2019 for per-capita calculations. Traffic has no community, only quadrant.
- **Sample questions** — add one of the questions above so visitors see a starter.

## Grab your Space ID (for notebook 03)

Look at the URL: `https://<workspace>/genie/rooms/`**`<THIS-LONG-HEX-ID>`**`?...`
Copy that ID — you'll paste it into `03_multi_agent` to make Genie a member of your agent team.
