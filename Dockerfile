# glp1_clinic — OSCE room for a GLP-1 AE-monitoring agent
FROM rust:1.85-bookworm AS tracer
WORKDIR /src
COPY runtime /src
RUN cargo build --release

FROM python:3.12-slim-bookworm
LABEL org.opencontainers.image.source="https://github.com/wetwarehq/glp1_clinic"
LABEL org.opencontainers.image.title="glp1_clinic"
LABEL org.opencontainers.image.description="OSCE stations: GLP-1 AE monitoring at routine follow-up (off-label longevity)"

RUN useradd -m -u 1000 clinic
WORKDIR /clinic
COPY --from=tracer /src/target/release/glp1-trace /usr/local/bin/glp1-trace
COPY TASK.md frame.toml taskset.py harness.py rubric.py systems_review.json vignettes.jsonl /clinic/
COPY scripts /clinic/scripts
RUN mkdir -p /trace /score && chown -R clinic:clinic /clinic /trace /score
USER clinic
ENV PYTHONUNBUFFERED=1 \
    GLP1_TRACER=/usr/local/bin/glp1-trace \
    TRACE_PATH=/trace/trace.jsonl \
    SCORE_DIR=/score \
    NAMESPACE=glp1_clinic
ENTRYPOINT ["python", "harness.py"]
CMD ["--list"]
