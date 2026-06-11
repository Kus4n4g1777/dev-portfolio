import asyncio
from app.agent import app
from langchain_core.messages import HumanMessage

async def run_agent():
    # We define our input query
    query = "Hey, can you check the database for any detections with low confidence?"
    
    print(f"User: {query}")
    
    # We invoke the graph with the initial message
    # We use stream() to see how the graph moves between nodes
    async for output in app.astream({"messages": [HumanMessage(content=query)]}):
        # We print the node that is currently processing
        for key, value in output.items():
            print(f"Node '{key}' finished processing.")
            
    print("Workflow completed.")

if __name__ == "__main__":
    asyncio.run(run_agent())
