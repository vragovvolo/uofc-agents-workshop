"""Prep Calgary Open Data extracts for the UofC agents workshop.

Pulls raw CSVs (downloaded from data.calgary.ca Socrata exports, see README)
from raw/, trims columns, normalizes community join keys, and writes gzipped
CSVs to data/. Re-run after re-downloading raw files to refresh the bundle.

Sources (Socrata dataset IDs):
  311 service requests  iahh-g8bj  (slice: requested_date > 2025-06-01)
  licensed pets         5dgy-88cq
  community crime       78gh-n26t  (historical, ends 2024-09)
  traffic incidents     35ra-9556
  community populations jtpc-xgsh  (civic census, ends 2019)
  communities by ward   jd78-wxjp
"""

from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
RAW = ROOT / "raw"
OUT = ROOT / "data"
OUT.mkdir(exist_ok=True)


def write(df: pd.DataFrame, name: str) -> None:
    path = OUT / f"{name}.csv.gz"
    df.to_csv(path, index=False, compression="gzip")
    mb = path.stat().st_size / 1e6
    print(f"{name:14s} {len(df):>8,} rows  {mb:6.1f} MB  -> {path.name}")


def norm_name(s: pd.Series) -> pd.Series:
    return s.astype("string").str.strip().str.upper()


# Communities dimension — canonical comm_code <-> name mapping
comm = pd.read_csv(RAW / "communities.csv")
comm = comm[["comm_code", "name", "class", "sector", "comm_structure", "ward_num"]]
comm["name"] = norm_name(comm["name"])
write(comm, "communities")
code_by_name = dict(zip(comm["name"], comm["comm_code"]))

# Licensed pets — monthly license volume by community and animal
pets = pd.read_csv(RAW / "pets.csv")
pets = pets[["date", "community_code", "community_name", "animal", "license_volume"]]
pets["date"] = pd.to_datetime(pets["date"]).dt.date
pets["community_name"] = norm_name(pets["community_name"])
pets["license_volume"] = pets["license_volume"].astype("Int64")
write(pets, "pets")

# Community crime — monthly counts; `community` holds the community NAME
crime = pd.read_csv(RAW / "crime.csv")
crime["community_name"] = norm_name(crime["community"])
crime["comm_code"] = crime["community_name"].map(code_by_name)
crime = crime[["comm_code", "community_name", "category", "crime_count", "year", "month"]]
write(crime, "crime")

# Traffic incidents — live feed, no community column (lat/long + quadrant only)
traffic = pd.read_csv(RAW / "traffic.csv")
traffic["incident_info"] = traffic["incident_info"].astype("string").str.strip()
traffic = traffic[["incident_info", "description", "start_dt", "quadrant", "longitude", "latitude"]]
write(traffic, "traffic")

# Community populations — civic census 1958-2019 (census discontinued after 2019)
pop = pd.read_csv(RAW / "population.csv")
pop["name"] = norm_name(pop["name"])
pop = pop[["comm_code", "name", "census_year", "population", "occupied_dwellings"]]
write(pop, "population")

# 311 service requests — 12-month slice
c311 = pd.read_csv(RAW / "c311.csv", low_memory=False)
c311 = c311[
    [
        "service_request_id", "requested_date", "closed_date", "status_description",
        "source", "service_name", "agency_responsible", "comm_code", "comm_name",
        "longitude", "latitude",
    ]
]
c311["comm_name"] = norm_name(c311["comm_name"])
write(c311, "c311")

total = sum(p.stat().st_size for p in OUT.glob("*.csv.gz")) / 1e6
print(f"\ntotal bundle: {total:.1f} MB")
