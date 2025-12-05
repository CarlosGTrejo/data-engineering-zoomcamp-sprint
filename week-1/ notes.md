# Week 1 Notes
## Docker
```dockerfile
FROM python:3.9.25-slim

RUN pip install pandas

WORKDIR /app
COPY pipeline.py pipeline.py

ENTRYPOINT [ "python", "pipeline.py" ]
```
1. Create the dockerfile
2. Build it with `docker build -t <image_tag_name> .` (`.` is the path to the Dockerfile)
3. Run it with `docker run -it <image_tag_name>`

Other notes:
- You can pass arguments to a docker script using `docker run <image_name> <arg1> <arg2> ...`, and if you add `-it` it allows for interactive terminal access. The args can be accessed in the python script using `sys.argv` list
  - If you don't use `-it` you can still create an interactive terminal session using `docker exec -it <container_id> /bin/bash`.
- The entry point can be set to run a specific script when the container starts using the `ENTRYPOINT` directive in the Dockerfile.
- Use `COPY` in the Dockerfile to copy files from your local machine into the docker image.
- Cleanup docker resources using:
  - `docker system prune` to remove unused data.
    - Use `docker system prune --filter "until=24h"` to remove resources unused for more than 24 hours.
  - `docker image prune` to remove unused images.
  - `docker container prune` to remove stopped containers.
  - `docker volume prune` to remove unused volumes.

---

## Postgres (in Docker)
### Spinning up Postgres in Docker
In this video the instructor adapted a section of a docker compose file to a docker command. I decided to turn it into a docker file to practice further.

**Docker Compose (Original Source)**
```yaml
services:
  postgres:
    image: postgres:13
    environment:
      POSTGRES_USER: airflow
      POSTGRES PASSWORD: airflow
      POSTGRES DB: airflow
    volumes:
      - postgres-db-volume:/var/lib/postgresq1/data
    healthcheck:
      test: ["CMD", "pg_isready", "-U", "airflow"]
      interval: 5s
      retries: 5
    restart: always
```

**Docker Command Equivalent**
```bash
docker run -it \
  -e POSTGRES_USER="root" \
  -e POSTGRES_PASSWORD="root" \
  -e POSTGRES_DB="ny_taxi" \
  -v $(pwd)/ny_taxi_postgres_data:/var/lib/postgresql/data \
  -p 5432:5432 \
  postgres:13
```

**Dockerfile Equivalent**
```dockerfile
FROM postgres:13

WORKDIR /app

RUN mkdir /data

ENV POSTGRES_USER=root
ENV POSTGRES_PASSWORD=root
ENV POSTGRES_DB=ny_taxi

# This creates a volume to persist the database data.
# To map it to a host directory, use the -v flag with `docker run`.
# If you don't map it, Docker will create an anonymous volume.
VOLUME "/var/lib/postgresql/data"

# This line serves more as a documentation of the port being used.
# To map the port, use the -p flag with `docker run`.
EXPOSE 5432
```

During the build phase (`docker build -t postgres:taxi .`), the following warning came up:
> SecretsUsedInArgOrEnv: Do not use ARG or ENV instructions for sensitive data (ENV "POSTGRES_PASSWORD") (line 8)

Which is understandable since we do not want to commit this dockerfile to a repo and have sensitive data be exposed. The proper way to handle this would be to use docker secrets, but for local development this is acceptable.

To run the Postgres container using the Dockerfile, you would still need to map the volume and port as shown in the docker command equivalent:
```bash
docker run -it \
  --name pg-db-taxi
  -v $(pwd)/ny_taxi_postgres_data:/var/lib/postgresql/data \
  -p 5432:5432 \
  postgres:taxi
```

**NOTE: I gave the container a name so it could be reused. To start the container next time use `docker start -ia <container_name>` (`-i` interactive, `-a` attach terminal to container) or else you will get an error saying the name is already in use. To spin up a temporary container use the `--rm` flag on `docker run` which will automatically remove the container when it exits. You do not need to re-specify the volume, portnumbers, env variables, etc. when you start the container by name again since it is saved during the creation the first time.**

Then using pgcli we connect to our posgres container with:
```bash
pgcli -h localhost -p 5432 -u root -d ny_taxi
```

Then I downloaded the csv data and unzippted it:
``` bash
wget -P ~/data https://github.com/DataTalksClub/nyc-tlc-data/releases/download/yellow/yellow_tripdata_2021-01.csv.gz
gunzip ~/data/yellow_tripdata_2021-01.csv.gz
```

We counted the lines using `wc -l yellow_tripdata_2021-01.csv`

### Using pandas to process and load the data

#### Process
- Load the data into pandas `df = pd.read_csv('yellow_tripdata_2021-01.csv', nrows=100)`
- Get the schema using `pd.io.sql.get_schema(df, name='yellow_taxi_data')`
  - Pandas does not detect timestamps always, and for financial transactions using decimal is preferred since it maintains better accuracy. But for the course using real will be fine.
  - Tranform the pickup/dropoff times to timestamp using `df.col_name = pd.to_datetime(df.col_name)`
    - If you know which columns are datetime beforehand, you can parse them as datetime when loading the csv data with `df = pd.read_csv('file.csv', parse_dates=['col1', 'col2', 'etc'])`

**Schema (without parsing as datetime on read):**
```sql
CREATE TABLE "yellow_taxi_data" (
"VendorID" INTEGER,
  "tpep_pickup_datetime" TEXT,
  "tpep_dropoff_datetime" TEXT,
  "passenger_count" INTEGER,
  "trip_distance" REAL,
  "RatecodeID" INTEGER,
  "store_and_fwd_flag" TEXT,
  "PULocationID" INTEGER,
  "DOLocationID" INTEGER,
  "payment_type" INTEGER,
  "fare_amount" REAL,
  "extra" REAL,
  "mta_tax" REAL,
  "tip_amount" REAL,
  "tolls_amount" REAL,
  "improvement_surcharge" REAL,
  "total_amount" REAL,
  "congestion_surcharge" REAL
)
```

The sql schema might or might not work, we need to adapt it to posgresql using sqlalchemy (`postgresql://<user>:<pass>@<address>:<port>/<db_name>`):
```python
from sqlalchemy import create_engine
engine = create_engine('postgresql://root:root@localhost:5432/ny_taxi')

# The correct schema should show up now
print(pd.io.sql.get_schema(df, name='yellow_taxi_data', con=engine))
```

**Schema (with correct data types):**
```sql
CREATE TABLE yellow_taxi_data (
        "VendorID" BIGINT, 
        tpep_pickup_datetime TIMESTAMP WITHOUT TIME ZONE, 
        tpep_dropoff_datetime TIMESTAMP WITHOUT TIME ZONE, 
        passenger_count BIGINT, 
        trip_distance FLOAT(53), 
        "RatecodeID" BIGINT, 
        store_and_fwd_flag TEXT, 
        "PULocationID" BIGINT, 
        "DOLocationID" BIGINT, 
        payment_type BIGINT, 
        fare_amount FLOAT(53), 
        extra FLOAT(53), 
        mta_tax FLOAT(53), 
        tip_amount FLOAT(53), 
        tolls_amount FLOAT(53), 
        improvement_surcharge FLOAT(53), 
        total_amount FLOAT(53), 
        congestion_surcharge FLOAT(53)
)
```

#### Load
```python
# Since the data is too big we chuck it by turning it into an iterator:
df_iter = pd.read_csv('yellow_tripdata_2021-01.csv', parse_dates=['tpep_pickup_datetime', 'tpep_dropoff_datetime'], iterator=True, chunksize=100_000)

# Load it in
from time import time
for idx, chunk in enumerate(df_iter, start=1):
  t_start = time()
  chunk.to_sql(name='yellow_taxi_data', con=engine, if_exists='append')
  t_end = time()
  print(f'Inserted chunk #{idx} in {t_end-t_start:.3f}')
```

Each chunk took about 9s to insert:
```
Inserted chunk #1 in 10.181
Inserted chunk #2 in 9.569
Inserted chunk #3 in 9.675
Inserted chunk #4 in 9.903
Inserted chunk #5 in 9.563
Inserted chunk #6 in 9.636
Inserted chunk #7 in 9.973
Inserted chunk #8 in 9.716
Inserted chunk #9 in 9.708
Inserted chunk #10 in 10.156
Inserted chunk #11 in 9.680
Inserted chunk #12 in 9.616
/workspaces/data-engineering-zoomcamp-sprint/week-1/2-docker-sql/pipeline.py:18: DtypeWarning: Columns (6) have mixed types. Specify dtype option on import or set low_memory=False.
  for idx, chunk in enumerate(df_iter, start=1):
Inserted chunk #13 in 9.859
Inserted chunk #14 in 6.129
```

The instructor noted that it would take a long time to load the data to the database, so I looked for better solutions and came across:
- [Polars](https://pola.rs/): A fast dataframe library written in Rust that has better performance than pandas for certain operations.
- [Dask](https://dask.org/): A flexible parallel computing library for analytics that integrates with pandas and NumPy.
- [dlt](https://dlthub.com/docs/intro): A data loading tool that simplifies the process of loading data into databases.
- `\copy` - a built-in command to load data into a table

So I tried using polars to load the data:
```python
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
```

And somehow it took more batches to insert the same amount of data, even though I specified the batch_size, and ended up taking about the same amount of time as pandas (probably because it uses pandas' `to_sql` method under the hood.)

Using dlt will have to wait for another day.

Using copy (after using the schema from pandas) took **8 seconds**:
```sql
\copy ny_taxi from '~/data/yellow_tripdata_2021-01.csv' with (format csv, header true);
```

---

## pgAdmin
If we run pgAdmin in a container, we cannot connect to our other postgres container when we specify `localhost` as our address, because it tries to look for an instance of postgres running inside of the pgAdmin.

To solve this we need to create a network so that both containers can communicate.
`docker network create pg-network`

Spin up our postgres container with the network we just created:
```bash
docker run -it \
  -e POSTGRES_USER="root" \
  -e POSTGRES_PASSWORD="root" \
  -e POSTGRES_DB="ny_taxi" \
  -v $(pwd)/ny_taxi_postgres_data:/var/lib/postgresql/data \
  -p 5432:5432 \
  --network=pg-network \
  --name pg-db-taxi \
  postgres:13
```

Then run pgadmin in the same docker network:
```bash
docker run -it \
  -e PGADMIN_DEFAULT_EMAIL="admin@admin.com" \
  -e PGADMIN_DEFAULT_PASSWORD="root" \
  -p 8080:80 \
  --network=pg-network \
  --name pgadmin \
  dpage/pgadmin4
```

Login with the credentials specified, then right click on _servers_ then _register>Server..._ and fill out the information for our pg database.

---

## Dockerizing the Ingestion Script

For this section I attempted to create a dlt pipeline since it seemed more robust and reliable than a script.

I followed the instructions in the [filesystem usage docs](https://dlthub.com/docs/dlt-ecosystem/verified-sources/filesystem/basic#3-create-and-run-a-pipeline).

I had issues before, when I ran `\dt` in pgcli it wouldn't show any new tables. So this time, I ran the pipeline with the env variable `PROGRESS=englighten` to see what was going on.

Although it said it completed and loaded the data, `\dt` still showed no tables. This is because `\dt` only displays tables that are visible in the current `search_path`, which by default is "$user", and "public". Since our tables are inside a different schema, we need to either add it to our `search_path` (`SET search_path TO schema_name, public;`) or pass it to the command like `\dt my_schema.*`

In my case:
```
root@localhost:ny_taxi> \dt ny_taxi_dataset.*
+-----------------+---------------------+-------+-------+
| Schema          | Name                | Type  | Owner |
|-----------------+---------------------+-------+-------|
| ny_taxi_dataset | _dlt_loads          | table | root  |
| ny_taxi_dataset | _dlt_pipeline_state | table | root  |
| ny_taxi_dataset | _dlt_version        | table | root  |
| ny_taxi_dataset | yellow_taxi_data    | table | root  |
+-----------------+---------------------+-------+-------+
SELECT 4
Time: 0.005s
```

But changing `dataset_name` to "public" will use the public schema. Although it is probably better to not do that since it is easier to drop the whole schema to start over.

