"""Agent state for JobScout v1.

v1 keeps state minimal — just the message history. add_messages appends
new messages to the list (instead of replacing it) which is how the agent
loop accumulates context across tool calls and LLM responses.
"""
from typing import TypedDict, Annotated
from langgraph.graph.message import add_messages


class JobScoutState(TypedDict):
    messages: Annotated[list, add_messages]
