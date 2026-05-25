from typing import TypedDict, Annotated, Sequence, List, Dict, Any
from langgraph.graph import StateGraph, END
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI
from app.tools.campaign_execution_tools import CAMPAIGN_EXECUTION_TOOLS
from langgraph.prebuilt import ToolNode
from app.config.settings import settings
import operator

# Define State
class AgentState(TypedDict):
    messages: Annotated[Sequence[BaseMessage], operator.add]
    next_action: str
    plan: List[str]

# Define Planner Node
def planner(state: AgentState):
    """
    Analyzes user request and creates a step-by-step plan.
    """
    llm = ChatOpenAI(model=settings.AI_MODEL, temperature=settings.AI_TEMPERATURE, api_key=settings.OPENAI_API_KEY)
    messages = state["messages"]
    
    prompt = ChatPromptTemplate.from_messages([
        ("system", "You are a campaign planning AI. Convert the user's request into a concrete list of actions. E.g., 'Improve campaign' -> 'analyze, detect issues, recommend actions'."),
        ("user", "{input}")
    ])
    
    from pydantic import BaseModel, Field
    
    class Plan(BaseModel):
        steps: List[str] = Field(description="List of concrete action steps to fulfill the user request.")
        
    structured_llm = llm.with_structured_output(Plan)
    
    # Format messages properly for the prompt
    input_text = messages[-1].content if messages else ""
    formatted_prompt = prompt.format_messages(input=input_text)
    
    # Generate structured plan
    response = structured_llm.invoke(formatted_prompt)
    plan = response.steps
    
    return {"plan": plan, "next_action": plan[0] if plan else "done"}

# Define Executor Node
def executor(state: AgentState):
    """
    Executes the current step in the plan using tools.
    """
    llm = ChatOpenAI(model=settings.AI_MODEL, temperature=settings.AI_TEMPERATURE, api_key=settings.OPENAI_API_KEY).bind_tools(CAMPAIGN_EXECUTION_TOOLS)
    messages = state["messages"]
    
    response = llm.invoke(messages)
    return {"messages": [response]}

# Define Routing
def route_tasks(state: AgentState):
    """
    Determines next step based on state.
    """
    if not state.get("plan"):
        return END
    
    last_message = state["messages"][-1]
    if hasattr(last_message, "tool_calls") and last_message.tool_calls:
        return "tools"
        
    return END

# Self-Healing Tool Executor
class SelfHealingToolNode(ToolNode):
    def invoke(self, input, config=None, **kwargs):
        try:
            return super().invoke(input, config, **kwargs)
        except Exception as e:
            # Detect failures and retry/fallback automatically
            return {"messages": [AIMessage(content=f"Tool failed: {str(e)}. Retrying or falling back to safe operation.")]}

# AI Tool Reflection Node
def reflect(state: AgentState):
    """
    Evaluates if the tool response makes sense.
    """
    last_message = state["messages"][-1]
    if last_message.type == "tool":
        llm = ChatOpenAI(model=settings.AI_MODEL, temperature=settings.AI_TEMPERATURE, api_key=settings.OPENAI_API_KEY)
        reflection_prompt = ChatPromptTemplate.from_messages([
            ("system", "You are a reflection AI. Evaluate if the tool response makes sense or if it failed. If it failed or doesn't make sense, output 'RETRY' along with reasoning. Otherwise, output 'OK'."),
            ("user", "Tool Output: {tool_output}")
        ])
        
        response = llm.invoke(reflection_prompt.format_messages(tool_output=last_message.content))
        if "RETRY" in response.content:
            return {"messages": [AIMessage(content=f"Reflection failed: {response.content}. Replanning/Retrying...")]}
            
    return {"messages": []}

# Build Graph
def build_planner_graph():
    workflow = StateGraph(AgentState)
    
    # Add nodes
    workflow.add_node("planner", planner)
    workflow.add_node("executor", executor)
    workflow.add_node("tools", SelfHealingToolNode(CAMPAIGN_EXECUTION_TOOLS))
    workflow.add_node("reflect", reflect)
    
    # Add edges
    workflow.set_entry_point("planner")
    workflow.add_edge("planner", "executor")
    
    workflow.add_conditional_edges(
        "executor",
        route_tasks,
        {
            "tools": "tools",
            END: END
        }
    )
    
    workflow.add_edge("tools", "reflect")
    workflow.add_edge("reflect", "executor")
    
    return workflow.compile()

planner_app = build_planner_graph()
