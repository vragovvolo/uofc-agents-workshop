# Building Agentic AI Solutions — Hands-on Workshop

**UofC AI Summer School · 90 minutes · no Databricks experience needed**

You'll build a working **multi-agent AI system** over real Calgary open data — 311 complaints,
pet licenses, crime stats, live traffic incidents — on a free Databricks workspace you keep
after the workshop.

```
you ──▶ SUPERVISOR agent ──▶ 🐕 pets analyst · 🚨 city services analyst · 🧞 Genie
                                      │
                              real Calgary data (Delta tables)
```

## Step 0 — Get your free workspace (do this first!)

1. Go to **<https://www.databricks.com/learn/free-edition>** and click **Sign up** (or search "Databricks Free Edition").
2. Sign in with Google/Microsoft or your school email (an email code logs you in — no password).
3. Create a new account when prompted.
4. **Important: select "United States" as your region** (more compute available than Canadian regions).
5. Wait ~30 seconds while your workspace is created. Skip the tutorials.

## Step 1 — Import this repo into your workspace

1. In your workspace, left sidebar → **Workspace** → **Home**.
2. Click **Create** (top right) → **Git folder**.
3. Paste this repo's URL: `https://github.com/vragovvolo/uofc-agents-workshop`
4. Click **Create Git folder**. Everything — notebooks *and* data — arrives in one go.

## Step 2 — Follow the notebooks in order

| Step | File | What you'll do | Time |
|---|---|---|---|
| 1 | `notebooks/01_setup_data` | Load Calgary open data into Delta tables (governed database tables in your workspace) | ~10 min |
| 2 | `GENIE_SETUP.md` | Create a Genie space — text-to-SQL with zero code | ~10 min |
| 3 | `notebooks/02_simple_agent` | Build an agent from scratch: LLM + tools + loop | ~20 min |
| 4 | `notebooks/03_multi_agent` | Specialists + a supervisor = agentic workflow | ~15 min |
| 5 | `notebooks/04_extensions` | AI functions in SQL, challenges, what's next | open-ended |

Open a notebook, click **Connect** (top right) if asked — Free Edition picks serverless
compute automatically — then **Run all**, and read as it runs.

## The data

All from [data.calgary.ca](https://data.calgary.ca), bundled in `data/` (prep code in `scripts/prep_data.py`):

| Table | Source dataset | Notes |
|---|---|---|
| `c311` | [311 Service Requests](https://data.calgary.ca/d/iahh-g8bj) | 12-month slice, ~500K rows |
| `pets` | [Licensed Pets](https://data.calgary.ca/d/5dgy-88cq) | cats & dogs by community, monthly |
| `crime` | [Community Crime Statistics](https://data.calgary.ca/d/78gh-n26t) | 2018 – Sept 2024 (historical) |
| `traffic` | [Traffic Incidents](https://data.calgary.ca/d/35ra-9556) | near-live at time of bundling |
| `population` | [Civic Census](https://data.calgary.ca/d/jtpc-xgsh) | by community, ends 2019 |
| `communities` | [Communities by Ward](https://data.calgary.ca/d/jd78-wxjp) | join dimension |

Data licensed under the [Open Government Licence – City of Calgary](https://data.calgary.ca/stories/s/u45n-7awa).

## If something breaks

- **"No known chat model found"** → run the cell again after a minute, or check
  Serving in the left sidebar to see your available endpoints.
- **Compute quota message** → Free Edition has a daily fair-use limit. Pair up with a neighbour.
- **Genie answers look off** → add the Instructions from `GENIE_SETUP.md`.

## Presenter

Volo Vragov — Specialist Solutions Architect, ML & GenAI, Databricks
