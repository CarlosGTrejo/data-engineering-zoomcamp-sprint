import dlt
from dlt.sources.filesystem import filesystem, read_csv

# Extract and Transform
source = filesystem(bucket_url="/home/codespace/data") | read_csv()

pipeline = dlt.pipeline(
    pipeline_name="ny_taxi",
    destination=dlt.destinations.postgres(
        "postgresql://root:root@localhost:5432/ny_taxi"
    ),
    dataset_name="ny_taxi",  # to use public schema change to "public"
)

info = pipeline.run(source, table_name="yellow_taxi", loader_file_format="csv")

print(info)
