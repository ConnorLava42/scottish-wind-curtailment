from pathlib import Path

import pandas as pd
from elexon import get

ROOT = Path(__file__).resolve().parent.parent   # the project folder
PROC = ROOT / "data" / "processed"
PROC.mkdir(parents=True, exist_ok=True)          # creates it if missing

units = pd.DataFrame(get("/reference/bmunits/all"))
print(units.columns.tolist())
print(units["fuelType"].value_counts(dropna=False))
print(units["gspGroupName"].value_counts(dropna=False))

is_wind = units["fuelType"].eq("WIND")
is_scot = (
    units["gspGroupId"].isin(["_N", "_P"])
    | units["gspGroupName"].str.contains("Scotland", case=False, na=False)
)

# Transmission-connected units have no GSP group: export them for tagging
no_gsp = units["gspGroupId"].isna()
to_tag = units.loc[is_wind & no_gsp, ["elexonBmUnit", "bmUnitName", "leadPartyName",
                                      "generationCapacity", "transmissionLossFactor"]].copy()
scot_tlf = set(units.loc[is_wind & is_scot, "transmissionLossFactor"].round(6))
to_tag["tlf_hint_scotland"] = to_tag["transmissionLossFactor"].round(6).isin(scot_tlf)
to_tag.sort_values("generationCapacity", ascending=False).to_csv(PROC / "wind_units_to_tag.csv", index=False)
print(len(to_tag), "transmission-connected wind units to tag")

# Units with a Scottish GSP group
scot_wind = units.loc[is_wind & is_scot, [
    "elexonBmUnit", "nationalGridBmUnit", "bmUnitName",
    "leadPartyName", "gspGroupName", "generationCapacity",
]]

# Add the transmission-connected units tagged Y in manual_overrides.csv
overrides = pd.read_csv(PROC / "manual_overrides.csv")
extra_ids = overrides.loc[overrides["is_scottish"] == "Y", "elexonBmUnit"]
extra = units[units["elexonBmUnit"].isin(extra_ids)].drop_duplicates("elexonBmUnit")
extra["gspGroupName"] = extra["elexonBmUnit"].map(overrides.set_index("elexonBmUnit")["tlf_zone"])
scot_wind = (pd.concat([scot_wind, extra[scot_wind.columns]])
               .drop_duplicates("elexonBmUnit")
               .sort_values("generationCapacity", ascending=False))

print(len(scot_wind), "Scottish wind units")
print(scot_wind.head(20))

units.to_csv(PROC / "bmunits_all.csv", index=False)
scot_wind.to_csv(PROC / "scottish_wind_units.csv", index=False)