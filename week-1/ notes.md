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

## Postgres (in Docker)

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
  -v $(pwd)/ny_taxi_postgres_data:/var/lib/postgresql/data \
  -p 5432:5432 \
  postgres:taxi
```

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