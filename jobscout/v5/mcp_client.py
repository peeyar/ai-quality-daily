"""MCP client for connecting to CareerTailor's MCP server.

Production-style: graceful degradation if the server is unreachable.
Logs errors clearly. Times out after 30 seconds.

The CAREERTAILER_MCP_URL env var controls where to connect. Defaults to
the local development URL.

v5 difference from v4: the call function is wrapped in a `v5.mcp.analyze_job_fit`
span so the cross-process boundary is visible in Phoenix. The MCPInstrumentor
adds protocol-level child spans automatically; this manual span is the
JobScout-side parent that anchors them.
"""
import asyncio
import os
from contextlib import asynccontextmanager
from typing import Any

from mcp import ClientSession
from mcp.client.streamable_http import streamablehttp_client

from v5.instrumentation import get_tracer


tracer = get_tracer()


CAREERTAILER_MCP_URL = os.environ.get(
    "CAREERTAILER_MCP_URL",
    "http://localhost:8765/mcp",
)
CALL_TIMEOUT_SECONDS = 30


@asynccontextmanager
async def careertailer_session():
    """Open an MCP session to the CareerTailor server.

    Usage:
        async with careertailer_session() as session:
            result = await session.call_tool("analyze_job_fit", {...})
    """
    async with streamablehttp_client(CAREERTAILER_MCP_URL) as (read, write, _):
        async with ClientSession(read, write) as session:
            await session.initialize()
            yield session


async def call_analyze_job_fit(
    user_id: str,
    job_description: str,
) -> dict[str, Any] | None:
    """Call the analyze_job_fit tool. Returns None if MCP server is unreachable.

    Returns the structured tool output dict, or None on connection / timeout
    error. Caller should handle None as graceful degradation.
    """
    with tracer.start_as_current_span("v5.mcp.analyze_job_fit") as span:
        span.set_attribute("user_id", user_id)
        try:
            async with asyncio.timeout(CALL_TIMEOUT_SECONDS):
                async with careertailer_session() as session:
                    response = await session.call_tool(
                        "analyze_job_fit",
                        {
                            "input": {
                                "user_id": user_id,
                                "job_description": job_description,
                            }
                        },
                    )
                    if response.structuredContent:
                        return response.structuredContent
                    return None
        except (TimeoutError, ConnectionError, OSError) as e:
            print(f"[v5 MCP] CareerTailor server unreachable: {e}")
            return None
        except Exception as e:
            import traceback
            print(f"[v5 MCP] Unexpected error calling CareerTailor: {e}")
            print(f"[v5 MCP] Full traceback:")
            traceback.print_exc()
            return None
