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