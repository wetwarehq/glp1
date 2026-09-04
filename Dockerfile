# glp1 — OSCE room for a GLP-1 AE-monitoring agent
FROM python:3.12-slim-bookworm
LABEL org.opencontainers.image.source="https://github.com/wetwarehq/glp1"
LABEL org.opencontainers.image.title="glp1"
LABEL org.opencontainers.image.description="OSCE stations: GLP-1 AE monitoring at routine follow-up (off-label longevity)"

RUN useradd -m -u 1000 clinic
WORKDIR /clinic
COPY bin/glp1-trace /usr/local/bin/glp1-trace
COPY TASK.md frame.toml fail_closed.json taskset.py harness.py rubric.py verifier.py handoff.py systems_review.json vignettes.jsonl /clinic/
COPY scripts /clinic/scripts
RUN chmod +x /usr/local/bin/glp1-trace \
    && mkdir -p /trace /score \
    && chown -R clinic:clinic /clinic /trace /score
USER clinic
ENV PYTHONUNBUFFERED=1 \
    GLP1_TRACER=/usr/local/bin/glp1-trace \
    TRACE_PATH=/trace/trace.jsonl \
    SCORE_DIR=/score \
    NAMESPACE=glp1
ENTRYPOINT ["python", "harness.py"]
CMD ["--list"]
