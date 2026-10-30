from datetime import date, timedelta
from pathlib import Path
import time

import pandas as pd
from tqdm import tqdm
from elexon import get

START = date(2024, 1, 1)        # move earlier if Step 1 showed older data exists
END = date.today() - timedelta(days=2)

ENDPOINTS = {
    "volumes": "/balancing/settlement/indicative/volumes/all/bid/{d}",
    "cashflows": "/balancing/settlement/indicative/cashflows/all/bid/{d}",
}

RAW = Path(__file__).resolve().parent.parent / "data" / "raw"

def daterange(a: date, b: date):
    d = a
    while d <= b:
        yield d
        d += timedelta(days=1)

for name, template in ENDPOINTS.items():
    out_dir = RAW / name
    out_dir.mkdir(parents=True, exist_ok=True)
    for d in tqdm(list(daterange(START, END)), desc=name):
        out = out_dir / f"{d.isoformat()}.parquet"
        if out.exists():
            continue                      # cache: skip days already saved
        rows = get(template.format(d=d.isoformat()))
        df = pd.json_normalize(rows)      # flattens nested pair columns
        df.to_parquet(out, index=False)
        time.sleep(0.2)                   # be polite to the API