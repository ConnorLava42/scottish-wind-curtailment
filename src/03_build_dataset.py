from pathlib import Path
import pandas as pd

RAW = Path(__file__).resolve().parent.parent / "data" / "raw"
PROC = Path(__file__).resolve().parent.parent / "data" / "processed"

def load(name: str, columns: list[str], keep_units: set[str]) -> pd.DataFrame:
    """Read each daily file, keep only Scottish units and the columns we need,
    then combine. Filtering file by file keeps memory use small."""
    frames = []
    for f in sorted((RAW / name).glob("*.parquet")):
        try:
            d = pd.read_parquet(f)
        except Exception as e:
            raise RuntimeError(f"Could not read {f}: {e}") from e
        if d.empty:
            continue
        frames.append(d.loc[d["bmUnit"].isin(keep_units), columns])
    return pd.concat(frames, ignore_index=True)

units = pd.read_csv(PROC / "scottish_wind_units.csv")
scot_ids = set(units["elexonBmUnit"])

# --- volumes ---
vol = load("volumes", ["bmUnit", "settlementDate", "settlementPeriod", "startTime",
                       "dataType", "totalVolumeAccepted"], scot_ids)
print(vol.groupby("dataType")["totalVolumeAccepted"].agg(["count", "sum"]))
# "Tagged" equals the sum of accepted bid volumes from the BOAV endpoint (checked on
# 2025-01-15 for Moray East and Seagreen); "Original" holds only a small part of it.
vol = vol[vol["dataType"] == "Tagged"]
vol = vol.drop(columns="dataType")

# --- cashflows ---
cash = load("cashflows", ["bmUnit", "settlementDate", "settlementPeriod",
                          "totalCashflow"], scot_ids)

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