from pathlib import Path
import pandas as pd

RAW = Path(__file__).resolve().parent.parent / "data" / "raw"
PROC = Path(__file__).resolve().parent.parent / "data" / "processed"

def load(name: str) -> pd.DataFrame:
    files = sorted((RAW / name).glob("*.parquet"))
    return pd.concat([pd.read_parquet(f) for f in files], ignore_index=True)

units = pd.read_csv(PROC / "scottish_wind_units.csv")
scot_ids = set(units["elexonBmUnit"])

# --- volumes ---
vol = load("volumes")
print(vol["dataType"].value_counts())
vol = vol[vol["dataType"] == "Original"]           # avoid double counting
vol = vol[vol["bmUnit"].isin(scot_ids)]
vol = vol[["bmUnit", "settlementDate", "settlementPeriod", "startTime",
           "totalVolumeAccepted"]]

# --- cashflows ---
cash = load("cashflows")
cash = cash[cash["bmUnit"].isin(scot_ids)]
cash = cash[["bmUnit", "settlementDate", "settlementPeriod", "totalCashflow"]]

# --- join ---
keys = ["bmUnit", "settlementDate", "settlementPeriod"]
df = vol.merge(cash, on=keys, how="outer", indicator=True)
print(df["_merge"].value_counts())                 # investigate any one-sided rows

# --- tidy columns ---
df["curtailed_mwh"] = -df["totalVolumeAccepted"]   # bids are negative; flip sign
df["payment_gbp"] = df["totalCashflow"]
df["start_utc"] = pd.to_datetime(df["startTime"], utc=True)
df["start_local"] = df["start_utc"].dt.tz_convert("Europe/London")

df = df.merge(units[["elexonBmUnit", "bmUnitName", "generationCapacity"]],
              left_on="bmUnit", right_on="elexonBmUnit", how="left")

df.to_parquet(PROC / "scottish_wind_curtailment.parquet", index=False)
print(df.describe())