import os
# At the begining before starting the LLM:
os.environ["GOOGLE_API_KEY"] = os.environ.get("GEMINI_API_KEY", "")

from typing import Literal
from langgraph.graph import END
from langchain_google_genai import ChatGoogleGenerativeAI
from .state import AgentState
from .tools import tool_node

# We initialize our LLM. We are using Gemini for its great reasoning capabilities
llm = ChatGoogleGenerativeAI(model="gemini-2.5-flash")

# We bind the tools to the LLM so it knows it can use them
llm_with_tools = llm.bind_tools(list(tool_node.tools_by_name.values()))

def call_model(state: AgentState):
    """
    We process the messages through the LLM. 
    We take the current state and return the updated message list.
    """
    messages = state["messages"]
    response = llm_with_tools.invoke(messages)
    return {"messages": [response]}

def should_continue(state: AgentState) -> Literal["tools", END]:
    """
    We analyze the last message to decide if we need to call a tool 
    or if we have reached the end of the task.
    """
    messages = state["messages"]
    last_message = messages[-1]
    
    # If the LLM has tool calls, we route to the 'tools' node
    if last_message.tool_calls:
        return "tools"
    
    # Otherwise, we conclude the workflow
    return END
