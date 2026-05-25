from typing import TypedDict, Annotated, List, Dict, Any
from langgraph.graph import StateGraph, END
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage

# Define the State
class AgentState(TypedDict):
    messages: Annotated[List[BaseMessage], "The conversation history"]
    workspace_id: int
    user_id: int
    context: Dict[str, Any]
    next_agent: str

# Define Agent Functions
def analytics_agent(state: AgentState) -> AgentState:
    print(f"Analytics Agent analyzing data for workspace {state['workspace_id']}")
    # Perform analytics task
    messages = state.get("messages", [])
    response = AIMessage(content="Analytics complete. Data trends look positive.")
    messages.append(response)
    return {"messages": messages, "next_agent": "campaign_agent"}

def campaign_agent(state: AgentState) -> AgentState:
    print(f"Campaign Agent optimizing campaigns for workspace {state['workspace_id']}")
    messages = state.get("messages", [])
    response = AIMessage(content="Campaigns optimized based on analytics.")
    messages.append(response)
    return {"messages": messages, "next_agent": "reporting_agent"}

def reporting_agent(state: AgentState) -> AgentState:
    print(f"Reporting Agent generating reports for workspace {state['workspace_id']}")
    messages = state.get("messages", [])
    response = AIMessage(content="Report generated successfully.")
    messages.append(response)
    return {"messages": messages, "next_agent": "automation_agent"}

def automation_agent(state: AgentState) -> AgentState:
    print(f"Automation Agent executing rules for workspace {state['workspace_id']}")
    messages = state.get("messages", [])
    response = AIMessage(content="Automations executed.")
    messages.append(response)
    return {"messages": messages, "next_agent": "END"}

# Router function
def router(state: AgentState) -> str:
    next_agent = state.get("next_agent", "END")
    if next_agent == "END":
        return END
    return next_agent

# Build the Graph
workflow = StateGraph(AgentState)

workflow.add_node("analytics_agent", analytics_agent)
workflow.add_node("campaign_agent", campaign_agent)
workflow.add_node("reporting_agent", reporting_agent)
workflow.add_node("automation_agent", automation_agent)

workflow.set_entry_point("analytics_agent")

workflow.add_conditional_edges(
    "analytics_agent",
    router,
    {
        "campaign_agent": "campaign_agent",
        "reporting_agent": "reporting_agent",
        "automation_agent": "automation_agent",
        END: END
    }
)

workflow.add_conditional_edges(
    "campaign_agent",
    router,
    {
        "reporting_agent": "reporting_agent",
        "automation_agent": "automation_agent",
        END: END
    }
)

workflow.add_conditional_edges(
    "reporting_agent",
    router,
    {
        "automation_agent": "automation_agent",
        END: END
    }
)

workflow.add_conditional_edges(
    "automation_agent",
    router,
    {
        END: END
    }
)

multi_agent_coordinator = workflow.compile()
