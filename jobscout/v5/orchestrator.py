"""Parent graph for JobScout v5.

Coordinates planner -> searcher -> analyzer -> [fit_analyzer]. Conditional
logic:
- if the planner sets a refusal_reason, skip searcher and analyzer entirely
- after the analyzer, route to fit_analyzer when plan.analyze_fit_for is non-empty

v5 difference from v4: register_phoenix() is called at module-load time so the
LangChain and MCP instrumentors are active before any subgraph LLM/MCP code runs.
The four subgraph node bodies are individually wrapped in v5.{name} spans.
"""
from langgraph.graph import StateGraph, END

from v5.instrumentation import register_phoenix, get_tracer

# Register Phoenix before importing v5.agents.* — instrumentors patch
# LangChain/MCP class methods, so they need to be active before the agent
# subgraph code calls those classes.
register_phoenix()
tracer = get_tracer()

from v5.parent_state import ParentState
from v5.schemas import FinalAnswer
from v5.agents.planner import build_planner_graph
from v5.agents.searcher import build_searcher_graph
from v5.agents.analyzer import build_analyzer_graph
from v5.agents.fit_analyzer import build_fit_analyzer_graph


def build_graph():
    planner = build_planner_graph()
    searcher = build_searcher_graph()
    analyzer = build_analyzer_graph()
    fit_analyzer = build_fit_analyzer_graph()

    def planner_node(state: ParentState):
        result = planner.invoke({"user_query": state["user_query"], "plan": None})
        return {"plan": result["plan"]}

    def searcher_node(state: ParentState):
        result = searcher.invoke({"plan": state["plan"], "result": None})
        return {"searcher_result": result["result"]}

    def analyzer_node(state: ParentState):
        result = analyzer.invoke({
            "plan": state["plan"],
            "searcher_result": state["searcher_result"],
            "final_answer": None,
        })
        return {"final_answer": result["final_answer"]}

    def fit_analyzer_node(state: ParentState):
        result = fit_analyzer.invoke({
            "plan": state["plan"],
            "searcher_result": state["searcher_result"],
            "final_answer": state["final_answer"],
            "fit_analyses": [],
        })
        return {
            "final_answer": result["final_answer"],
            "fit_analyses": result["fit_analyses"],
        }

    def refusal_node(state: ParentState):
        # If the planner refused, build the FinalAnswer directly from refusal_reason
        return {
            "final_answer": FinalAnswer(answer=state["plan"].refusal_reason)
        }

    def route_after_planner(state: ParentState):
        if state["plan"].refusal_reason is not None:
            return "refusal"
        return "searcher"

    def route_after_analyzer(state: ParentState):
        if state["plan"].analyze_fit_for:
            return "fit_analyzer"
        return "end"

    graph = StateGraph(ParentState)
    graph.add_node("planner", planner_node)
    graph.add_node("searcher", searcher_node)
    graph.add_node("analyzer", analyzer_node)
    graph.add_node("fit_analyzer", fit_analyzer_node)
    graph.add_node("refusal", refusal_node)

    graph.set_entry_point("planner")
    graph.add_conditional_edges(
        "planner",
        route_after_planner,
        {"searcher": "searcher", "refusal": "refusal"},
    )
    graph.add_edge("searcher", "analyzer")
    graph.add_conditional_edges(
        "analyzer",
        route_after_analyzer,
        {"fit_analyzer": "fit_analyzer", "end": END},
    )
    graph.add_edge("fit_analyzer", END)
    graph.add_edge("refusal", END)

    return graph.compile()
