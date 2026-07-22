"""
LangGraph Agent — FastAPI HTTP Interface

Exposes the LangGraph agent as a REST API so any frontend
(React, Angular, Flutter) can send natural language prompts
and get structured responses back.

Architecture:
    Client → POST /agent/query → LangGraph graph → tools → response

Human-in-the-loop (HITL):
    The agent supports an optional approval step before executing
    tools. This is the pattern used in production agentic systems
    at big tech — the agent reasons, proposes a plan in natural
    language, pauses for human confirmation, then executes.

    POST /agent/query      → returns plan + thread_id (if HITL enabled)
    POST /agent/approve    → resumes execution after human approval
    POST /agent/reject     → cancels execution with optional feedback

    This is not a demo trick — it's the correct pattern for any
    agent that takes actions with real-world side effects (creating
    GitHub issues, modifying databases, sending notifications).

Endpoints:
    GET  /health           → liveness check
    POST /agent/query      → run agent with optional HITL pause
    POST /agent/approve    → approve pending HITL action
    POST /agent/reject     → reject pending HITL action
    GET  /agent/status     → check thread state
"""

import os
import uuid
import asyncio
from typing import Optional

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from langchain_core.messages import HumanMessage, AIMessage

# Set up Google API key before importing agent
os.environ["GOOGLE_API_KEY"] = os.environ.get("GEMINI_API_KEY", "")

from agent import app as langgraph_app

# ── FastAPI setup ──────────────────────────────────────────────────────────────

api = FastAPI(
    title="LangGraph Agent API",
    description="Natural language interface to the LLM Gateway analytics agent",
    version="1.0.0"
)

api.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Tighten in production
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── In-memory thread store (replace with Redis/DB in production) ───────────────
# Stores pending HITL states keyed by thread_id
pending_approvals: dict = {}

# ── Request / Response models ──────────────────────────────────────────────────

class QueryRequest(BaseModel):
    prompt: str
    require_approval: bool = False  # Enable HITL
    thread_id: Optional[str] = None

class ApprovalRequest(BaseModel):
    thread_id: str
    approved: bool
    feedback: Optional[str] = None  # Optional human feedback

class AgentResponse(BaseModel):
    thread_id: str
    status: str          # "completed" | "pending_approval" | "rejected"
    plan: Optional[str]  # What the agent plans to do (HITL step)
    result: Optional[str] # Final result after execution
    messages: list

# ── Helper: extract readable text from agent messages ─────────────────────────

def extract_final_message(messages: list) -> str:
    """
    Walk the message list backwards to find the last
    meaningful AI text response (not a tool call).
    """
    for msg in reversed(messages):
        if isinstance(msg, AIMessage) and msg.content:
            if isinstance(msg.content, str) and msg.content.strip():
                return msg.content
            if isinstance(msg.content, list):
                for block in msg.content:
                    if isinstance(block, dict) and block.get("type") == "text":
                        return block.get("text", "")
    return "Agent completed without a text response."

# ── Routes ─────────────────────────────────────────────────────────────────────

@api.get("/health")
def health():
    return {"status": "ok", "service": "langgraph-agent"}


@api.post("/agent/query", response_model=AgentResponse)
async def query_agent(req: QueryRequest):
    """
    Send a natural language prompt to the agent.

    With require_approval=False (default):
        Agent runs to completion and returns the result.

    With require_approval=True (HITL mode):
        Agent reasons about what it will do and returns a plan.
        Execution is paused. Use POST /agent/approve to proceed.

    This mirrors how production agentic systems work —
    the agent proposes, the human approves, the agent executes.
    """
    thread_id = req.thread_id or str(uuid.uuid4())
    initial_state = {"messages": [HumanMessage(content=req.prompt)]}

    if not req.require_approval:
        # ── Direct execution — no HITL ─────────────────────────────
        try:
            final_state = await langgraph_app.ainvoke(initial_state)
            messages = final_state.get("messages", [])
            result = extract_final_message(messages)

            return AgentResponse(
                thread_id=thread_id,
                status="completed",
                plan=None,
                result=result,
                messages=[
                    {"role": "ai" if isinstance(m, AIMessage) else "human",
                     "content": m.content if isinstance(m.content, str) else str(m.content)}
                    for m in messages
                ]
            )
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

    else:
        # ── HITL mode — agent proposes plan, waits for approval ────
        # Step 1: Ask agent to reason and describe its plan WITHOUT executing tools
        planning_prompt = f"""
The user wants you to: {req.prompt}

Before taking any action, describe in clear natural language:
1. What you understand the user wants
2. Exactly what tools you plan to call and why
3. What the expected outcome will be

Do NOT call any tools yet. Just describe your plan clearly so the user can approve it.
"""
        try:
            planning_state = await langgraph_app.ainvoke(
                {"messages": [HumanMessage(content=planning_prompt)]}
            )
            plan_messages = planning_state.get("messages", [])
            plan_text = extract_final_message(plan_messages)

            # Store pending state for approval
            pending_approvals[thread_id] = {
                "original_prompt": req.prompt,
                "plan": plan_text,
                "status": "pending"
            }

            return AgentResponse(
                thread_id=thread_id,
                status="pending_approval",
                plan=plan_text,
                result=None,
                messages=[
                    {"role": "ai" if isinstance(m, AIMessage) else "human",
                     "content": m.content if isinstance(m.content, str) else str(m.content)}
                    for m in plan_messages
                ]
            )
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))


@api.post("/agent/approve", response_model=AgentResponse)
async def approve_agent(req: ApprovalRequest):
    """
    Approve or reject a pending HITL action.

    If approved: agent executes with the original prompt.
    If rejected: agent is cancelled. Optional feedback is logged.

    This is the human-in-the-loop checkpoint — the moment where
    a human confirms the agent's plan before real-world actions happen.
    """
    pending = pending_approvals.get(req.thread_id)
    if not pending:
        raise HTTPException(
            status_code=404,
            detail=f"No pending approval found for thread_id: {req.thread_id}"
        )

    if not req.approved:
        # ── Rejected ───────────────────────────────────────────────
        del pending_approvals[req.thread_id]
        return AgentResponse(
            thread_id=req.thread_id,
            status="rejected",
            plan=pending["plan"],
            result=f"Action cancelled by human. Feedback: {req.feedback or 'none'}",
            messages=[]
        )

    # ── Approved — now execute with original prompt ────────────────
    original_prompt = pending["original_prompt"]
    del pending_approvals[req.thread_id]

    try:
        final_state = await langgraph_app.ainvoke(
            {"messages": [HumanMessage(content=original_prompt)]}
        )
        messages = final_state.get("messages", [])
        result = extract_final_message(messages)

        return AgentResponse(
            thread_id=req.thread_id,
            status="completed",
            plan=pending["plan"],
            result=result,
            messages=[
                {"role": "ai" if isinstance(m, AIMessage) else "human",
                 "content": m.content if isinstance(m.content, str) else str(m.content)}
                for m in messages
            ]
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@api.get("/agent/status/{thread_id}")
def get_status(thread_id: str):
    """Check if a thread is pending approval."""
    pending = pending_approvals.get(thread_id)
    if not pending:
        return {"thread_id": thread_id, "status": "not_found"}
    return {
        "thread_id": thread_id,
        "status": "pending_approval",
        "plan": pending["plan"]
    }
