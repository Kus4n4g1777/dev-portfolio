from typing import Annotated, List, TypedDict
from langgraph.graph.message import add_messages
from langchain_core.messages import BaseMessage

class AgentState(TypedDict):
    # We use add_messages to ensure the agent remembers the entire conversation history
    messages: Annotated[List[BaseMessage], add_messages]
