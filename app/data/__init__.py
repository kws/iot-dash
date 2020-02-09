import pandas as pd
import os
from glob import glob

_DIR = os.getenv("IOT_DIR", os.path.abspath("../samples"))
_columns = [
    "date",
    "id",
    "name",
    "type",
    "value",
    "battery",
    "dark",
    "daylight"
]


def read_data():
    files = glob(os.path.join(_DIR, "iot-log-*.csv*"))
    dataframes = [pd.read_csv(f, names=_columns, parse_dates=["date"]) for f in files]
    df = pd.concat(dataframes)
    df = df.drop_duplicates()
    df = df.sort_values("date")
    return df

