# Week 1 Notes
## Docker
```dockerfile
FROM python:3.9.25-slim

RUN pip install pandas

WORKDIR /app
COPY pipeline.py pipeline.py

ENTRYPOINT [ "python", "pipeline.py" ]
```

- You can pass arguments to a docker script using `docker run <image_name> <arg1> <arg2> ...`, and if you add `-it` it allows for interactive terminal access.
  - If you don't use `-it` you can still create an interactive terminal session using `docker exec -it <container_id> /bin/bash`.
  - These arguments can be accessed in the python script using `sys.argv` list.
- The entry point can be set to run a specific script when the container starts using the `ENTRYPOINT` directive in the Dockerfile.
- You can build a docker image using the command `docker build -t <image_tag_name> .` where `.` is the path to the Dockerfile.
- Use `COPY` in the Dockerfile to copy files from your local machine into the docker image.
- Cleanup docker resources using:
  - `docker system prune` to remove unused data.
    - Use `docker system prune --filter "until=24h"` to remove resources unused for more than 24 hours.
  - `docker image prune` to remove unused images.
  - `docker container prune` to remove stopped containers.
  - `docker volume prune` to remove unused volumes.

## 