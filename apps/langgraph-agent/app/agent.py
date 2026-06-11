from langgraph.graph import StateGraph, END
from langgraph.prebuilt import ToolNode
from .state import AgentState
from .nodes import call_model, should_continue
from .tools import tools

# We initialize the graph with my AgentState to track the conversation flow
workflow = StateGraph(AgentState)

# We define the core nodes:
# 'agent' is where We process the logic through the LLM
# 'tools' is the node where We execute external functions via ToolNode
workflow.add_node("agent", call_model)
workflow.add_node("tools", ToolNode(tools))

# We set the agent as the entry point to start the reasoning process
workflow.set_entry_point("agent")

# We add conditional edges to determine if We need to run a tool or finish the task
workflow.add_conditional_edges(
    "agent",
    should_continue,
)

# After my tools run, We always route back to the agent to evaluate the results
workflow.add_edge("tools", "agent")

# We compile the graph into an executable app
app = workflow.compile()
