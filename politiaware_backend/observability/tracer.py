"""
OpenTelemetry Tracer Provider with Multi-Backend Support (Jaeger & Arize).
Both backends default to False.
Supports simultaneous export to both backends, individual export, or neither.
Fault-tolerant: fails gracefully with logger.error without raising exceptions.
"""

import logging
from typing import Optional

from .config import config

logger = logging.getLogger("observability.tracer")

_TRACER_PROVIDER = None
_TRACER = None
_INITIALIZED = False


class DummySpan:
    """Fallback no-op span when OpenTelemetry or backends are unavailable."""
    def __enter__(self):
        return self

    def __exit__(self, *args):
        pass

    def is_recording(self) -> bool:
        return False

    def set_attribute(self, key, value):
        pass

    def record_exception(self, exception):
        pass

    def set_status(self, status, description=None):
        pass

    def update_name(self, name):
        pass

    def end(self):
        pass

    def get_span_context(self):
        class DummyContext:
            is_valid = False
            trace_id = 0
            span_id = 0
        return DummyContext()


class DummyTracer:
    """Fallback no-op tracer when OpenTelemetry or backends are unavailable."""
    def start_as_current_span(self, *args, **kwargs):
        return DummySpan()

    def start_span(self, *args, **kwargs):
        return DummySpan()


def _create_jaeger_exporter():
    """
    Safely creates the Jaeger OTLP exporter.
    Logs logger.error on failure without raising exceptions.
    """
    endpoint = config.jaeger_endpoint
    try:
        if "4318" in endpoint or endpoint.startswith("http"):
            from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter as HttpOTLPExporter
            exporter = HttpOTLPExporter(endpoint=endpoint)
            logger.info("Configured Jaeger OTLP HTTP Span Exporter targeting %s", endpoint)
            return exporter
        else:
            from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter as GrpcOTLPExporter
            exporter = GrpcOTLPExporter(endpoint=endpoint, insecure=config.otlp_insecure)
            logger.info("Configured Jaeger OTLP gRPC Span Exporter targeting %s", endpoint)
            return exporter
    except Exception as exc:
        logger.error(
            "Failed to initialize Jaeger trace exporter (endpoint: %s): %s",
            endpoint,
            exc,
            exc_info=True,
        )
        return None


def _create_arize_exporter():
    """
    Safely creates the Arize OTLP exporter (supports Arize Phoenix & Arize Cloud).
    Logs logger.error on failure without raising exceptions.
    """
    endpoint = config.arize_endpoint
    headers = {}
    if config.arize_space_id:
        headers["space_id"] = config.arize_space_id
    if config.arize_api_key:
        headers["api_key"] = config.arize_api_key

    try:
        from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter as HttpOTLPExporter
        exporter = HttpOTLPExporter(
            endpoint=endpoint,
            headers=headers if headers else None,
        )
        logger.info("Configured Arize OTLP Span Exporter targeting %s", endpoint)
        return exporter
    except Exception as exc:
        logger.error(
            "Failed to initialize Arize trace exporter (endpoint: %s): %s",
            endpoint,
            exc,
            exc_info=True,
        )
        return None


def init_tracer():
    """
    Initializes the OpenTelemetry TracerProvider and registers active exporters:
    - Jaeger (if JAEGER_ENABLED=True)
    - Arize (if ARIZE_ENABLED=True)
    - Both (if both are True)
    - Neither (if both are False, defaults to False)
    """
    global _TRACER_PROVIDER, _TRACER, _INITIALIZED

    if _INITIALIZED:
        return _TRACER

    # Check if tracing backends are enabled
    if not config.has_active_trace_backend:
        logger.info(
            "OpenTelemetry Tracing backends are disabled (jaeger_enabled=%s, arize_enabled=%s).",
            config.jaeger_enabled,
            config.arize_enabled,
        )
        _INITIALIZED = True
        _TRACER = DummyTracer()
        return _TRACER

    try:
        from opentelemetry import trace
        from opentelemetry.sdk.trace import TracerProvider
        from opentelemetry.sdk.trace.export import BatchSpanProcessor
        from opentelemetry.sdk.trace.sampling import (
            ALWAYS_ON,
            ALWAYS_OFF,
            DEFAULT_OFF,
            DEFAULT_ON,
            ParentBased,
            TraceIdRatioBased,
        )
        from opentelemetry.sdk.resources import Resource, SERVICE_NAME, SERVICE_VERSION, DEPLOYMENT_ENVIRONMENT
    except ImportError as e:
        logger.warning("OpenTelemetry SDK packages not installed. Tracing disabled. Error: %s", e)
        _INITIALIZED = True
        _TRACER = DummyTracer()
        return _TRACER

    # 1. Build Standard Resource Attributes
    resource = Resource.create({
        SERVICE_NAME: config.service_name,
        SERVICE_VERSION: config.service_version,
        DEPLOYMENT_ENVIRONMENT: config.environment,
        "telemetry.sdk.language": "python",
    })

    # 2. Configure Sampler
    sampler = ALWAYS_ON
    if config.sampler_name in ("always_off", "off", "0"):
        sampler = ALWAYS_OFF
    elif config.sampler_name in ("traceidratio", "ratio"):
        sampler = TraceIdRatioBased(config.sampler_rate)
    elif config.sampler_name in ("parentbased_always_on", "parentbased"):
        sampler = ParentBased(DEFAULT_ON)
    elif config.sampler_name in ("parentbased_always_off",):
        sampler = ParentBased(DEFAULT_OFF)

    # 3. Create TracerProvider
    provider = TracerProvider(resource=resource, sampler=sampler)
    active_processors_count = 0

    # 4. Attach Jaeger Exporter if enabled
    if config.jaeger_enabled:
        jaeger_exporter = _create_jaeger_exporter()
        if jaeger_exporter:
            try:
                processor = BatchSpanProcessor(
                    jaeger_exporter,
                    max_queue_size=2048,
                    max_export_batch_size=512,
                    schedule_delay_millis=2000,
                )
                provider.add_span_processor(processor)
                active_processors_count += 1
            except Exception as exc:
                logger.error("Failed to attach Jaeger BatchSpanProcessor: %s", exc, exc_info=True)

    # 5. Attach Arize Exporter if enabled
    if config.arize_enabled:
        arize_exporter = _create_arize_exporter()
        if arize_exporter:
            try:
                processor = BatchSpanProcessor(
                    arize_exporter,
                    max_queue_size=2048,
                    max_export_batch_size=512,
                    schedule_delay_millis=2000,
                )
                provider.add_span_processor(processor)
                active_processors_count += 1
            except Exception as exc:
                logger.error("Failed to attach Arize BatchSpanProcessor: %s", exc, exc_info=True)

    # Register as global tracer provider
    trace.set_tracer_provider(provider)
    _TRACER_PROVIDER = provider
    _TRACER = trace.get_tracer(config.service_name, config.service_version)
    _INITIALIZED = True

    logger.info(
        "OpenTelemetry Tracing initialized with %d active exporter(s) (jaeger=%s, arize=%s).",
        active_processors_count,
        config.jaeger_enabled,
        config.arize_enabled,
    )
    return _TRACER


def get_tracer(name: Optional[str] = None):
    """Returns an OpenTelemetry tracer for manual instrumentation."""
    if not _INITIALIZED:
        init_tracer()

    try:
        from opentelemetry import trace
        return trace.get_tracer(name or config.service_name, config.service_version)
    except ImportError:
        return DummyTracer()
