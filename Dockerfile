# from https://github.com/jacobtomlinson/python-container-action/tree/master

FROM python:3.12-slim AS builder
ADD . /app
WORKDIR /app

# We are installing a dependency here directly into our app source dir
RUN pip install --target=/app/src .

# A distroless container image with Python and some basics like SSL certificates
# https://github.com/GoogleContainerTools/distroless
FROM gcr.io/distroless/python3-debian12
COPY --from=builder /app /app
WORKDIR /app
ENV PYTHONPATH=/app/src
ENTRYPOINT ["python3", "-m", "src.streamlined_releases"]
