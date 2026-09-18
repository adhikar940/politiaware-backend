"""
Django Observability Middleware.
Enriches active OpenTelemetry spans with business context:
- User ID / username
- Client IP
- Custom Request / Correlation IDs
- GraphQL operation names
- Injects X-Trace-ID into HTTP response headers for frontend/client tracing
"""

import json
import logging
from typing import Callable

logger = logging.getLogger("observability.middleware")


class ObservabilityMiddleware:
    """
    Middleware that enriches OpenTelemetry spans and injects trace headers.
    """

    def __init__(self, get_response: Callable):
        self.get_response = get_response

    def __call__(self, request):
        trace_id = None
        try:
            from opentelemetry import trace
            current_span = trace.get_current_span()
            if current_span and current_span.is_recording():
                context = current_span.get_span_context()
                if context and context.is_valid:
                    trace_id = f"{context.trace_id:032x}"
                    current_span.set_attribute("http.trace_id", trace_id)

                # Client IP
                x_forwarded_for = request.META.get("HTTP_X_FORWARDED_FOR")
                client_ip = x_forwarded_for.split(",")[0].strip() if x_forwarded_for else request.META.get("REMOTE_ADDR")
                if client_ip:
                    current_span.set_attribute("http.client_ip", client_ip)

                # Correlation / Request ID from headers
                req_id = request.META.get("HTTP_X_REQUEST_ID") or request.META.get("HTTP_X_CORRELATION_ID")
                if req_id:
                    current_span.set_attribute("http.request_id", req_id)

                # Inspect GraphQL requests for operation name
                if "graphql" in request.path and request.method == "POST":
                    try:
                        # Attempt safe parsing if body is available and small
                        body_text = request.body.decode("utf-8", errors="ignore")
                        if body_text and body_text.startswith("{"):
                            data = json.loads(body_text)
                            op_name = data.get("operationName")
                            if op_name:
                                current_span.set_attribute("graphql.operation_name", op_name)
                                current_span.update_name(f"GraphQL {op_name}")
                    except Exception:
                        pass
        except Exception:
            pass

        response = self.get_response(request)

        # Enrich with authenticated user info (available after AuthenticationMiddleware)
        try:
            from opentelemetry import trace
            current_span = trace.get_current_span()
            if current_span and current_span.is_recording():
                user = getattr(request, "user", None)
                if user and getattr(user, "is_authenticated", False):
                    current_span.set_attribute("enduser.id", str(getattr(user, "pk", user.id)))
                    current_span.set_attribute("enduser.username", str(getattr(user, "username", "")))

            # Attach X-Trace-ID header to HTTP response
            if trace_id and hasattr(response, "__setitem__"):
                response["X-Trace-ID"] = trace_id
        except Exception:
            pass

        return response

