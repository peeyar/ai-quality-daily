"""Agent state for JobScout v2.

Adds search_history and fetched_urls so the agent has explicit memory of
what it has tried — beyond just the message thread.
"""
from typing import TypedDict, Annotated
from langgraph.graph.message import add_messages

from v2.schemas import SearchQuery


class JobScoutState(TypedDict):
    messages: Annotated[list, add_messages]
    search_history: list[SearchQuery]
    fetched_urls: list[str]
