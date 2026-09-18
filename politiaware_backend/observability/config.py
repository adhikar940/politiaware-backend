"""
Observability Configuration Loader.
Reads settings from Django settings, conf_loader, and environment variables.
Supports Jaeger and Arize dual/single tracing backends (both default to False).
"""

import os
from typing import Any, Dict

try:
    from politiaware_backend.conf.conf_loader import config as raw_config
    _conf_obs = raw_config.get("observability") or {}
except Exception:
    _conf_obs = {}


def _to_bool(val: Any, default: bool = False) -> bool:
    if val is None:
        return default
    return str(val).strip().lower() in ("true", "1", "yes", "on")


class ObservabilityConfig:
    """Centralized configuration for OpenTelemetry Tracing (Jaeger, Arize), Metrics, and OpenSearch Logging."""

    def __init__(self):
        # Global toggle
        self.enabled: bool = _to_bool(
            os.getenv("OTEL_ENABLED", _conf_obs.get("enabled")),
            default=True
        )

        # Service Information
        self.service_name: str = (
            os.getenv("OTEL_SERVICE_NAME")
            or _conf_obs.get("service_name")
            or "politiaware-backend"
        )
        self.service_version: str = os.getenv("OTEL_SERVICE_VERSION", "1.0.0")
        self.environment: str = os.getenv("ENVIRONMENT", "local")

        # -------------------------------------------------------------------
        # 1. JAEGER TRACING BACKEND (Defaults to False)
        # -------------------------------------------------------------------
        self.jaeger_enabled: bool = _to_bool(
            os.getenv("JAEGER_ENABLED", os.getenv("OTEL_JAEGER_ENABLED", _conf_obs.get("jaeger_enabled"))),
            default=False
        )
        default_jaeger_endpoint = "http://localhost:4318/v1/traces"
        self.jaeger_endpoint: str = (
            os.getenv("JAEGER_ENDPOINT")
            or os.getenv("OTEL_EXPORTER_OTLP_ENDPOINT")
            or _conf_obs.get("jaeger_endpoint")
            or _conf_obs.get("otlp_endpoint")
            or default_jaeger_endpoint
        )
        # Backward compatibility alias
        self.otlp_endpoint: str = self.jaeger_endpoint
        self.otlp_insecure: bool = _to_bool(
            os.getenv("OTEL_EXPORTER_OTLP_INSECURE", "True"),
            default=True
        )

        # -------------------------------------------------------------------
        # 2. ARIZE TRACING BACKEND (Defaults to False)
        # -------------------------------------------------------------------
        self.arize_enabled: bool = _to_bool(
            os.getenv("ARIZE_ENABLED", _conf_obs.get("arize_enabled")),
            default=False
        )
        default_arize_endpoint = "http://localhost:6006/v1/traces"
        self.arize_endpoint: str = (
            os.getenv("ARIZE_ENDPOINT")
            or _conf_obs.get("arize_endpoint")
            or default_arize_endpoint
        )
        self.arize_space_id: str = (
            os.getenv("ARIZE_SPACE_ID")
            or _conf_obs.get("arize_space_id")
            or ""
        )
        self.arize_api_key: str = (
            os.getenv("ARIZE_API_KEY")
            or _conf_obs.get("arize_api_key")
            or ""
        )

        # Sampling: always_on, always_off, traceidratio, parentbased_always_on
        self.sampler_name: str = (
            os.getenv("OTEL_TRACES_SAMPLER")
            or _conf_obs.get("sampler")
            or "always_on"
        ).lower()
        try:
            self.sampler_rate: float = float(os.getenv("OTEL_TRACES_SAMPLER_ARG", "1.0"))
        except (ValueError, TypeError):
            self.sampler_rate = 1.0

        # -------------------------------------------------------------------
        # 3. OPENSEARCH LOGGING CONFIGURATION
        # -------------------------------------------------------------------
        self.opensearch_url: str = (
            os.getenv("OPENSEARCH_URL")
            or _conf_obs.get("opensearch_url")
            or "http://localhost:9200"
        )
        self.opensearch_logging_enabled: bool = _to_bool(
            os.getenv("OPENSEARCH_LOGGING_ENABLED", _conf_obs.get("opensearch_logging_enabled")),
            default=True
        )
        self.opensearch_index_prefix: str = (
            os.getenv("OPENSEARCH_INDEX_PREFIX")
            or _conf_obs.get("opensearch_index_prefix")
            or "politiaware-logs"
        )
        self.opensearch_buffer_size: int = int(os.getenv("OPENSEARCH_BUFFER_SIZE", "50"))
        self.opensearch_flush_interval: float = float(os.getenv("OPENSEARCH_FLUSH_INTERVAL", "3.0"))

        # Component specific toggles
        self.instrument_django: bool = _to_bool(os.getenv("OTEL_INSTRUMENT_DJANGO", "True"), default=True)
        self.instrument_db: bool = _to_bool(os.getenv("OTEL_INSTRUMENT_DB", "True"), default=True)
        self.instrument_valkey: bool = _to_bool(os.getenv("OTEL_INSTRUMENT_VALKEY", "True"), default=True)
        self.instrument_graphql: bool = _to_bool(os.getenv("OTEL_INSTRUMENT_GRAPHQL", "True"), default=True)
        self.instrument_http: bool = _to_bool(os.getenv("OTEL_INSTRUMENT_HTTP", "True"), default=True)
        self.instrument_servers: bool = _to_bool(os.getenv("OTEL_INSTRUMENT_SERVERS", "True"), default=True)
        self.instrument_logging: bool = _to_bool(os.getenv("OTEL_INSTRUMENT_LOGGING", "True"), default=True)

        # Excluded URLs (health checks, static assets, etc.)
        self.excluded_urls: str = os.getenv(
            "OTEL_PYTHON_DJANGO_EXCLUDED_URLS",
            "healthz,metrics,static/*,favicon.ico"
        )

    @property
    def has_active_trace_backend(self) -> bool:
        """Returns True if either Jaeger or Arize is enabled."""
        return self.enabled and (self.jaeger_enabled or self.arize_enabled)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "enabled": self.enabled,
            "service_name": self.service_name,
            "service_version": self.service_version,
            "environment": self.environment,
            "jaeger_enabled": self.jaeger_enabled,
            "jaeger_endpoint": self.jaeger_endpoint,
            "arize_enabled": self.arize_enabled,
            "arize_endpoint": self.arize_endpoint,
            "arize_space_id": self.arize_space_id,
            "sampler": self.sampler_name,
            "opensearch_url": self.opensearch_url,
            "opensearch_logging_enabled": self.opensearch_logging_enabled,
            "opensearch_index_prefix": self.opensearch_index_prefix,
        }


# Global singleton instance
config = ObservabilityConfig()
