import pandas as pd
from elexon import get
from pathlib import Path

units = pd.DataFrame(get("/reference/bmunits/all"))
print(units.columns.tolist())          # check the field names first
print(units["fuelType"].value_counts(dropna=False))
print(units["gspGroupName"].value_counts(dropna=False))

is_wind = units["fuelType"].eq("WIND")
is_scot = (
    units["gspGroupId"].isin(["_N", "_P"])
    | units["gspGroupName"].str.contains("Scotland", case=False, na=False)
)

scot_wind = units.loc[is_wind & is_scot, [
    "elexonBmUnit", "nationalGridBmUnit", "bmUnitName",
    "leadPartyName", "gspGroupName", "generationCapacity",
]].sort_values("generationCapacity", ascending=False)

print(len(scot_wind), "Scottish wind units")
print(scot_wind.head(20))

ROOT = Path(__file__).resolve().parent.parent   # the project folder
PROC = ROOT / "data" / "processed"
PROC.mkdir(parents=True, exist_ok=True)          # creates it if missing

units.to_csv(PROC / "bmunits_all.csv", index=False)
scot_wind.to_csv(PROC / "scottish_wind_units.csv", index=False)