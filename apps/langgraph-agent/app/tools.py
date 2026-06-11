from langchain_core.tools import tool
from typing import List, Dict

# We define our tools here. 
# Each function decorated with @tool will be automatically detected by the Agent.

@tool
def get_low_confidence_detections(threshold: float = 0.5) -> List[Dict]:
    """
    We use this tool to query the database for object detections 
    with a confidence score lower than the provided threshold.
    """
    # Here, we will implement the actual SQL/SQLAlchemy query logic later.
    # For now, we return a mock result so we can test the graph flow.
    print(f"We are querying the DB for detections with confidence < {threshold}")
    
    return [
        {"id": 101, "object": "person", "confidence": 0.42},
        {"id": 102, "object": "vehicle", "confidence": 0.35}
    ]

# We group our tools into a list to be bound to the LLM
tools = [get_low_confidence_detections]

# We create the ToolNode that LangGraph uses to execute the tools
from langgraph.prebuilt import ToolNode
tool_node = ToolNode(tools)
