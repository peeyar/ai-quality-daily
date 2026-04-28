"""JobScout v2 — single LangGraph agent with structured tool I/O and memory."""
import os
from dotenv import load_dotenv
from langchain_core.messages import SystemMessage, ToolMessage
from langchain_google_genai import ChatGoogleGenerativeAI
from langgraph.graph import StateGraph
from langgraph.prebuilt import ToolNode, tools_condition

from v2.state import JobScoutState
from v2.tools import search_jobs, fetch_description
from v2.schemas import SearchQuery

load_dotenv()

SYSTEM_PROMPT = """You are JobScout, an agent that helps users find jobs.

You have two tools:
- search_jobs: takes a STRUCTURED query (keywords, location, role_seniority)
- fetch_description: fetches full details for a single job URL

CRITICAL: when calling search_jobs, decompose the user's request:
- keywords: list of single technical terms (e.g. ['Python'], ['ML', 'engineer'])
- location: city name or 'Remote' (None if unspecified)
- role_seniority: 'senior', 'junior', 'staff', 'principal' (None if unspecified)

Do NOT pass full sentences as keywords. Each keyword is a single term.

Examples of good decomposition:
- "Find Python jobs in Seattle" → keywords=['Python'], location='Seattle'
- "Senior ML engineer roles, remote" → keywords=['ML', 'engineer'], location='Remote', role_seniority='senior'
- "Compare job_001 and job_003" → don't search, fetch each URL directly

If a search returns no results, try with fewer or different keywords before giving up.
If you've already tried a similar search, try a different decomposition rather than repeating.

Do not invent data you haven't seen in tool output.
"""


def build_graph(max_steps: int = 10):
    llm = ChatGoogleGenerativeAI(
        model="gemini-2.5-flash",
        temperature=0,
        google_api_key=os.environ["GEMINI_API_KEY"],
    )
    tools = [search_jobs, fetch_description]
    llm_with_tools = llm.bind_tools(tools)

    def agent_node(state: JobScoutState):
        messages = state["messages"]
        has_system = any(getattr(m, "type", None) == "system" for m in messages)
        if not has_system:
            messages = [SystemMessage(content=SYSTEM_PROMPT)] + list(messages)
        response = llm_with_tools.invoke(messages)
        return {"messages": [response]}

    def tracking_node(state: JobScoutState):
        """Wrap ToolNode to also update search_history and fetched_urls."""
        tool_node = ToolNode(tools)
        result = tool_node.invoke(state)

        new_history = list(state.get("search_history", []))
        new_fetched = list(state.get("fetched_urls", []))

        for msg in result.get("messages", []):
            if isinstance(msg, ToolMessage):
                # Find the AIMessage that issued this tool_call_id (most recent
                # AIMessage with tool_calls in the prior state)
                for prev in reversed(state["messages"]):
                    if hasattr(prev, "tool_calls") and prev.tool_calls:
                        for tc in prev.tool_calls:
                            if tc.get("id") == msg.tool_call_id:
                                if tc["name"] == "search_jobs":
                                    args = tc.get("args", {}).get("query", {})
                                    if args:
                                        try:
                                            new_history.append(SearchQuery(**args))
                                        except Exception:
                                            pass
                                elif tc["name"] == "fetch_description":
                                    args = tc.get("args", {}).get("input", {})
                                    url = args.get("url") if isinstance(args, dict) else None
                                    if url:
                                        new_fetched.append(url)
                        break

        return {
            "messages": result["messages"],
            "search_history": new_history,
            "fetched_urls": new_fetched,
        }

    graph = StateGraph(JobScoutState)
    graph.add_node("agent", agent_node)
    graph.add_node("tools", tracking_node)
    graph.set_entry_point("agent")
    graph.add_conditional_edges("agent", tools_condition)
    graph.add_edge("tools", "agent")

    return graph.compile()
