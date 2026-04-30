"""Parent graph for JobScout v3.

Coordinates planner -> searcher -> analyzer. The only conditional logic:
if the planner sets a refusal_reason, skip searcher and analyzer entirely
and return the planner's reasoning.
"""
from langgraph.graph import StateGraph, END

from v3.parent_state import ParentState
from v3.schemas import FinalAnswer
from v3.agents.planner import build_planner_graph
from v3.agents.searcher import build_searcher_graph
from v3.agents.analyzer import build_analyzer_graph


def build_graph():
    planner = build_planner_graph()
    searcher = build_searcher_graph()
    analyzer = build_analyzer_graph()

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

    def refusal_node(state: ParentState):
        # If the planner refused, build the FinalAnswer directly from refusal_reason
        return {
            "final_answer": FinalAnswer(answer=state["plan"].refusal_reason)
        }

    def route_after_planner(state: ParentState):
        if state["plan"].refusal_reason is not None:
            return "refusal"
        return "searcher"

    graph = StateGraph(ParentState)
    graph.add_node("planner", planner_node)
    graph.add_node("searcher", searcher_node)
    graph.add_node("analyzer", analyzer_node)
    graph.add_node("refusal", refusal_node)

    graph.set_entry_point("planner")
    graph.add_conditional_edges(
        "planner",
        route_after_planner,
        {"searcher": "searcher", "refusal": "refusal"},
    )
    graph.add_edge("searcher", "analyzer")
    graph.add_edge("analyzer", END)
    graph.add_edge("refusal", END)

    return graph.compile()
