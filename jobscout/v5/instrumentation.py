"""Phoenix observability setup for v5.

v5 is structurally identical to v4 except every subgraph node and the MCP
client are wrapped in OpenTelemetry spans. Traces flow to a local Phoenix
server at http://localhost:6006.

Setup is one register_phoenix() call from run.py. After that, the
LangChainInstrumentor and MCPInstrumentor automatically add spans on every
LLM and MCP call. Manual `with tracer.start_as_current_span(...)` blocks
in each subgraph node make the four-subgraph structure visible in Phoenix's
trace tree.
"""
from openinference.instrumentation.langchain import LangChainInstrumentor
from openinference.instrumentation.mcp import MCPInstrumentor
from opentelemetry import trace
from phoenix.otel import register


_initialized = False


def register_phoenix(project_name: str = "jobscout-v5") -> None:
    """Register Phoenix as the OpenTelemetry destination and activate
    LangChain + MCP instrumentors. Safe to call multiple times — only the
    first call has effect.

    Phoenix UI: http://localhost:6006
    Start the Phoenix server separately: `phoenix serve` or `python -m phoenix.server.main serve`
    """
    global _initialized
    if _initialized:
        return

    tracer_provider = register(
        project_name=project_name,
        endpoint="http://localhost:6006/v1/traces",
        auto_instrument=False,  # we activate instrumentors explicitly below
    )
    LangChainInstrumentor().instrument(tracer_provider=tracer_provider)
    MCPInstrumentor().instrument(tracer_provider=tracer_provider)
    _initialized = True


def get_tracer():
    """Return the OpenTelemetry tracer for manual span creation."""
    return trace.get_tracer("jobscout.v5")
