from time import time

import polars as pl

# The default batch size is 50000, but you can adjust using `batch_size` parameter.
batches = pl.read_csv_batched(
    "~/data/yellow_tripdata_2021-01.csv", try_parse_dates=True, batch_size=100_000
)

idx = 1
while batches:
    for batch in batches.next_batches(5):  # Read 5 batches at a time
        t_start = time()
        batch.write_database(
            table_name="ny_taxi_polars",
            connection="postgresql://root:root@localhost:5432/ny_taxi",
            if_table_exists="append",
        )
        t_end = time()
        print(f"Inserted batch #{idx} in {t_end - t_start:.3f}s")
        idx += 1
