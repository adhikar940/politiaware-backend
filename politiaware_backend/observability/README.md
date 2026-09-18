# Politiaware Backend Observability Suite (OpenTelemetry + Jaeger + OpenSearch)

This package provides turnkey, production-grade observability for the Politiaware backend stack:
- **Tracing (Jaeger via OTLP)**: Automatic tracing for Django HTTP views, PostgreSQL queries, Valkey caching, Strawberry GraphQL execution, and outbound HTTP requests.
- **Logging (OpenSearch)**: High-performance asynchronous structured JSON logging with automatic trace correlation (`trace_id`, `span_id`).
- **Distributed Context**: Propagates trace context across services and outbound HTTP clients using W3C TraceContext (`traceparent`).

---

## Architecture Overview

```
                          ┌──────────────────────────┐
                          │   HTTP / GraphQL Client  │
                          └─────────────┬────────────┘
                                        │ (Injects X-Trace-ID)
                                        ▼
                   ┌─────────────────────────────────────────┐
                   │        Politiaware Django Backend       │
                   │                                         │
                   │  [ Observability Middleware ]           │
                   │         │                               │
                   │         ├─► [ Django Instrumentor ]     │
                   │         ├─► [ Strawberry GraphQL Inst ] │
                   │         ├─► [ Valkey Instrumentor ]     │
                   │         ├─► [ Postgres / Psycopg Inst ] │
                   │         └─► [ HTTP Clients Inst ]       │
                   │                   │                     │
                   └───────────┬───────┴──────────┬──────────┘
                               │                  │
                         Traces│ (OTLP)       Logs│ (JSON with trace_id)
                               ▼                  ▼
                   ┌───────────────────┐  ┌───────────────────┐
                   │      Jaeger       │  │    OpenSearch     │
                   │  (Port 4318/16686)│  │ (Port 9200/5601)  │
                   └───────────────────┘  └───────────────────┘
```

---

## Supported Auto-Instrumentations

| Component | Instrumentation Package / Module | What It Captures |
| :--- | :--- | :--- |
| **Django Framework** | `opentelemetry-instrumentation-django` | HTTP request path, method, status code, view name, middleware execution, template rendering. |
| **PostgreSQL / PostGIS** | `opentelemetry-instrumentation-psycopg2` / `psycopg` | SQL statement text (sanitized), execution latency, affected rows, database name. |
| **Valkey (Cache)** | `ValkeyInstrumentor` (`valkey_inst.py`) | Async & Sync Valkey operations (`GET`, `SET`, `DEL`, `EXPIRE`, keyspace), latency, host/port. |
| **Redis** | `opentelemetry-instrumentation-redis` | Redis operations if used. |
| **GraphQL** | Strawberry OpenTelemetry Tracing (`strawberry-graphql[opentelemetry]`) | Operation name, query/mutation text, resolver timings, field-level metrics. |
| **ASGI / WSGI** | `opentelemetry-instrumentation-asgi` / `wsgi` | Uvicorn / Gunicorn server lifecycle, scope handling, response timings. |
| **Outbound HTTP** | `requests`, `httpx`, `urllib3` | External HTTP requests (Cloudinary, external APIs), W3C `traceparent` propagation. |
| **Logging** | `opentelemetry-instrumentation-logging` & `OpenSearchHandler` | Enriches Python logs with `trace_id` & `span_id`; streams non-blocking JSON to OpenSearch. |

---

## Multi-Backend Tracing (Jaeger & Arize)

Both tracing backends default to **`False`**. You can enable either one or both simultaneously:
- **`JAEGER_ENABLED=True`**: Exports traces to Jaeger (`http://localhost:4318/v1/traces`).
- **`ARIZE_ENABLED=True`**: Exports traces to Arize Phoenix (`http://localhost:6006/v1/traces`) or Arize Cloud (`https://otlp.arize.com/v1/traces`).
- **Both `True`**: Simultaneously broadcasts all spans to both Jaeger and Arize.
- **Fault-Tolerant Resiliency**: If Jaeger, Arize, or Valkey becomes unreachable or throws an error, the system will **never raise an unhandled exception or crash the application**. It logs `logger.error(...)` and smoothly continues or falls back to database operations.

---

## Environment Variables (.env)

| Variable | Default | Description |
| :--- | :--- | :--- |
| `JAEGER_ENABLED` | `False` | Toggle export to Jaeger (defaults to `False`). |
| `JAEGER_ENDPOINT` | `http://localhost:4318/v1/traces` | Jaeger OTLP HTTP receiver endpoint. |
| `ARIZE_ENABLED` | `False` | Toggle export to Arize (defaults to `False`). |
| `ARIZE_ENDPOINT` | `http://localhost:6006/v1/traces` | Arize Phoenix or Arize Cloud OTLP endpoint. |
| `ARIZE_SPACE_ID` | *(empty)* | Optional Space ID for Arize Cloud authentication. |
| `ARIZE_API_KEY` | *(empty)* | Optional API Key for Arize Cloud authentication. |
| `OTEL_ENABLED` | `True` | Master toggle for OpenTelemetry. |
| `OTEL_SERVICE_NAME` | `politiaware-backend` | Service name displayed in Jaeger, Arize, and OpenSearch. |
| `OTEL_SERVICE_VERSION` | `1.0.0` | Application version tag. |
| `OTEL_TRACES_SAMPLER` | `always_on` | Sampling strategy (`always_on`, `always_off`, `traceidratio`). |
| `OPENSEARCH_URL` | `http://localhost:9200` | URL of the running OpenSearch instance. |
| `OPENSEARCH_LOGGING_ENABLED` | `True` | Enables asynchronous JSON log shipping to OpenSearch. |
| `OPENSEARCH_INDEX_PREFIX` | `politiaware-logs` | Index pattern prefix (results in `politiaware-logs-YYYY.MM.DD`). |
| `OTEL_PYTHON_DJANGO_EXCLUDED_URLS` | `healthz,metrics,static/*` | Comma-separated URL paths excluded from tracing. |

---

## How to Run & Use

### Method 1: Programmatic Initialization (Recommended)
Add to `m/settings.py`, `manage.py`, `asgi.py`, or `wsgi.py`:

```python
from politiaware_backend.observability import init_observability

# Automatically initializes tracer, instrumentors, and OpenSearch logging
init_observability()
```

### Method 2: Zero-Code CLI Auto-Instrumentation
Run via OpenTelemetry CLI wrapper:

```bash
opentelemetry-instrument \
  --traces_exporter otlp \
  --service_name politiaware-backend \
  gunicorn m.wsgi:application --bind 0.0.0.0:8000
```

---

## Tracing Custom Code Blocks

You can create custom spans anywhere in your views or services:

```python
from politiaware_backend.observability import trace_span

with trace_span("process_election_data", {"state": "Karnataka", "year": 2026}):
    # Your business logic here
    pass
```

---

## Correlated Logging in OpenSearch

Every log emitted through Python's standard `logging` module is automatically correlated with the active trace:

```python
import logging
logger = logging.getLogger(__name__)

# This log record will automatically contain trace_id and span_id in OpenSearch!
logger.info("Successfully fetched party members", extra={"party_id": 42})
```

### Viewing Traces and Logs

1. **Jaeger UI**: Open [http://localhost:16686](http://localhost:16686) in your browser. Select service `politiaware-backend` and click **Find Traces**.
2. **OpenSearch Dashboards**: Open [http://localhost:5601](http://localhost:5601). Create an Index Pattern for `politiaware-logs-*` to explore logs with `trace_id` and `span_id`.

