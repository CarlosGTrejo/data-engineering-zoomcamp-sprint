from time import time

import pandas as pd
from sqlalchemy import create_engine

engine = create_engine("postgresql://root:root@localhost:5432/ny_taxi")

df_iter = pd.read_csv(
    "~/data/yellow_tripdata_2021-01.csv",
    parse_dates=["tpep_pickup_datetime", "tpep_dropoff_datetime"],
    iterator=True,
    chunksize=100_000,
)

for idx, chunk in enumerate(df_iter, start=1):
    t_start = time()
    chunk.to_sql(
        name="yellow_taxi_data2", con=engine, if_exists="append", method="multi"
    )
    t_end = time()
    print(f"Inserted chunk #{idx} in {t_end - t_start:.3f}")
