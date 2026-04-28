"""JobScout v1 — single LangGraph agent with ReAct loop."""
import os
from dotenv import load_dotenv
from langchain_core.messages import SystemMessage
from langchain_google_genai import ChatGoogleGenerativeAI
from langgraph.graph import StateGraph
from langgraph.prebuilt import ToolNode, tools_condition

from v1.state import JobScoutState
from v1.tools import search_jobs, fetch_description

load_dotenv()

SYSTEM_PROMPT = """You are JobScout, an agent that helps users find jobs.

You have two tools:
- search_jobs: search for jobs by natural-language query
- fetch_description: get the full description for a single job URL

Search first. Fetch descriptions only when you need details the search results
don't include (like salary, remote status, or requirements).

When you have enough information, summarize the matching jobs clearly and stop
calling tools. Do not invent salary, remote status, company size, or any detail
you haven't actually seen in tool output. If you can't find what the user asked
for, say so directly."""


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
        # Inject system prompt only once at the start
        has_system = any(
            getattr(m, "type", None) == "system" for m in messages
        )
        if not has_system:
            messages = [SystemMessage(content=SYSTEM_PROMPT)] + list(messages)
        response = llm_with_tools.invoke(messages)
        return {"messages": [response]}

    graph = StateGraph(JobScoutState)
    graph.add_node("agent", agent_node)
    graph.add_node("tools", ToolNode(tools))
    graph.set_entry_point("agent")
    graph.add_conditional_edges("agent", tools_condition)
    graph.add_edge("tools", "agent")

    return graph.compile()
