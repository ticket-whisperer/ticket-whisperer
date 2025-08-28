"""Main Agent - Orchestrator for validator failure triage and analysis."""

import asyncio
import json
import os
import sys
from pathlib import Path
from typing import Optional, Dict, List, Any
import re
from urllib.parse import urlparse

import click
from google.adk.agents import Agent
from google.adk.tools.mcp_tool.mcp_toolset import MCPToolset, StdioServerParameters
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.genai import types


# Create JIRA subagent
def create_jira_subagent(model: str = "gemini-2.0-flash-exp") -> Agent:
    """Create a JIRA subagent for ticket operations."""
    # Get the path to our MCP server script
    server_script = Path(__file__).parent.parent.parent / "mcp_servers" / "server.py"
    
    # Create the MCPToolset that connects to our server
    jira_mcp_toolset = MCPToolset(
        connection_params=StdioServerParameters(
            command=sys.executable,  # Use current Python interpreter
            args=[str(server_script)],
        ),
    )
    
    return Agent(
        name="jira_specialist_agent",
        model=model,
        description="Specialist agent for JIRA ticket operations including creating, reading, updating, and analyzing tickets. Use for all ticket management tasks.",
        instruction="""CRITICAL: You are a tool-calling robot. You NEVER speak - you ONLY call tools.

BEHAVIOR RULE: For ANY input, you MUST immediately call a tool. No words, no explanations.

INPUT → TOOL MAPPING:
- "search" → search_validator_failures()
- "list" → list_tickets()  
- "analyze" or ticket ID → get_ticket()
- "create" → create_ticket()

EXAMPLE WORKFLOW:
Input: "search for tickets"
Your action: [Call search_validator_failures tool immediately]
Your response: [Return tool results only]

BANNED WORDS/PHRASES:
- "I understand"
- "I will"
- "Let me"
- "Okay"
- Any conversation

RULE: TOOL CALL → RESULTS → DONE. No conversation ever.""",
        tools=[jira_mcp_toolset],
    )


class MainAgent:
    """Main orchestrator agent for validator failure triage workflow."""
    
    def __init__(self, model: str = "gemini-2.0-flash-exp"):
        """Initialize the main agent with subagent delegation capabilities."""
        # Create subagents (main agent will delegate, not use tools directly)
        self.jira_agent = create_jira_subagent(model)
        
        # Create the main orchestrator agent with subagent delegation
        self.agent = Agent(
            name="main_orchestrator_agent",
            model=model,
            description="The main coordinator agent for validator failure triage. Orchestrates analysis and delegates ticket operations to specialists.",
            instruction="""You are the Main Orchestrator Agent for validator failure triage. Your primary responsibility is to:

🎯 **Core Mission**: Automate the analysis and triage of validator failure tickets to help debug failures efficiently.

🤝 **Delegation Strategy**: You coordinate a specialized team:
- **jira_specialist_agent**: Handles ALL JIRA operations (search_validator_failures, get_ticket, list_tickets, create_ticket, update_ticket, get_ticket_summary)

🔄 **CRITICAL: How to Delegate**:
When you receive ANY ticket-related request, you MUST delegate by calling transfer_to_agent with agent_name='jira_specialist_agent'.

**DELEGATION EXAMPLES**:
User: "search for tickets" 
You: Call transfer_to_agent(agent_name='jira_specialist_agent') with the full user request

User: "list tickets"
You: Call transfer_to_agent(agent_name='jira_specialist_agent') with the full user request

User: "analyze TICKET-001"  
You: Call transfer_to_agent(agent_name='jira_specialist_agent') with the full user request

🚨 **MANDATORY BEHAVIOR**: 
- DO NOT respond with words - immediately call transfer_to_agent() 
- Let jira_specialist_agent handle the actual work
- Only provide analysis AFTER getting specialist results

💬 **Communication Style**: Be analytical, concise, and action-oriented. Delegate to specialists to get real data, then provide clear recommendations and next steps.""",
            tools=[],  # Main agent has no direct tools - must delegate
            sub_agents=[self.jira_agent],   # Delegates all ticket operations to specialist
        )
        
        # Create the runner for proper ADK execution
        self.runner = Runner(
            app_name="validator_triage_orchestrator",
            agent=self.agent,
            session_service=InMemorySessionService()
        )
        
        # Initialize session info
        self.user_id = "triage_user"
        self.session_id = "triage_session"
    
    async def chat(self, message: str) -> str:
        """Send a message to the main agent and get a response."""
        try:
            # Ensure session exists
            await self._ensure_session()
            
            # Create message content
            message_content = types.Content(
                parts=[types.Part(text=message)]
            )
            
            # Send message via runner
            response_parts = []
            for event in self.runner.run(
                user_id=self.user_id,
                session_id=self.session_id,
                new_message=message_content
            ):
                # Extract clean text from response events
                if hasattr(event, 'content') and event.content:
                    if hasattr(event.content, 'parts'):
                        for part in event.content.parts:
                            if hasattr(part, 'text') and part.text:
                                response_parts.append(part.text.strip())
                    elif hasattr(event.content, 'text'):
                        response_parts.append(event.content.text.strip())
                elif hasattr(event, 'text') and event.text:
                    response_parts.append(event.text.strip())
            
            return "".join(response_parts) if response_parts else "No response received"
            
        except Exception as e:
            return f"Error: {str(e)}"
    
    async def _ensure_session(self):
        """Ensure the session exists."""
        try:
            await self.runner.session_service.create_session(
                app_name="validator_triage_orchestrator",
                user_id=self.user_id,
                session_id=self.session_id
            )
        except Exception:
            # Session might already exist, which is fine
            pass
    
    async def run_validator_triage_cycle(self) -> Dict[str, Any]:
        """Run a complete validator failure triage cycle using delegation."""
        results = {
            "cycle_started": True,
            "steps": [],
            "findings": {},
            "actions_taken": [],
            "recommendations": []
        }
        
        try:
            # Step 1: Search for validator failures (delegates to JIRA agent)
            step1_response = await self.chat(
                "Search for validator failure tickets from the last 7 days. Focus on open tickets with critical and high priority. "
                "I need detailed information about each ticket including their current status and failure descriptions."
            )
            results["steps"].append({
                "step": "search_failures",
                "response": step1_response,
                "status": "completed"
            })
            
            # Step 2: Analyze findings and extract ticket IDs
            ticket_ids = self._extract_ticket_ids_from_response(step1_response)
            results["findings"]["discovered_tickets"] = ticket_ids
            
            # Step 3: Analyze each ticket in detail (delegates to JIRA agent)
            for ticket_id in ticket_ids[:3]:  # Limit to 3 for demo
                analysis_response = await self.chat(
                    f"Get the detailed description and analysis of ticket {ticket_id}. "
                    f"I need you to extract any URLs or links to failure logs (Jenkins, CI/CD systems), "
                    f"identify error patterns, and provide insights about the failure type and severity. "
                    f"Also check if this ticket is related to any other existing tickets."
                )
                
                results["steps"].append({
                    "step": f"analyze_ticket_{ticket_id}",
                    "response": analysis_response,
                    "status": "completed"
                })
                
                # Extract URLs for potential log analysis
                urls = self._extract_urls_from_response(analysis_response)
                if urls:
                    results["findings"][f"{ticket_id}_log_urls"] = urls
            
            # Step 4: Generate comprehensive recommendations
            if ticket_ids:
                recommendations_response = await self.chat(
                    f"Based on the analysis of validator failure tickets {', '.join(ticket_ids[:3])}, "
                    f"provide a comprehensive summary of findings and recommend specific next steps for the development team. "
                    f"Include: 1) Common failure patterns, 2) Priority recommendations, 3) Suggested assignees or teams, "
                    f"4) Any tickets that should be updated or escalated."
                )
            else:
                recommendations_response = await self.chat(
                    "No validator failure tickets were found in the recent search. "
                    "Provide recommendations for proactive monitoring and validation improvements."
                )
            
            results["recommendations"].append(recommendations_response)
            results["cycle_completed"] = True
            
        except Exception as e:
            results["error"] = str(e)
            results["cycle_completed"] = False
        
        return results
    
    def _extract_ticket_ids_from_response(self, response: str) -> List[str]:
        """Extract ticket IDs from agent response."""
        # Simple regex to find ticket IDs like TICKET-001, PROJ-123, etc.
        ticket_pattern = r'\b[A-Z]+-\d+\b'
        tickets = re.findall(ticket_pattern, response)
        return list(set(tickets))  # Remove duplicates
    
    def _extract_urls_from_response(self, response: str) -> List[str]:
        """Extract URLs from agent response."""
        url_pattern = r'https?://[^\s<>"{}|\\^`\[\]]+'
        urls = re.findall(url_pattern, response)
        return urls
    
    async def start_interactive_triage_session(self):
        """Start an interactive triage session with subagent delegation."""
        print("🎯 Welcome to Main Agent - Validator Failure Triage!")
        print("I orchestrate the analysis of validator failures using specialized agents.")
        print("\nMy team:")
        print("  🎫 JIRA Specialist - Handles all ticket operations")
        print("\nCommands:")
        print("  'triage' - Run full triage cycle")
        print("  'search' - Search for validator failures")
        print("  'analyze TICKET-ID' - Analyze specific ticket")
        print("  'create ticket DESCRIPTION' - Create a new ticket")
        print("  'list tickets' - Show recent tickets")
        print("  'quit' or 'exit' - Stop")
        print()
        
        while True:
            try:
                user_input = input("Main Agent: ").strip()
                
                if user_input.lower() in ['quit', 'exit', 'bye']:
                    print("👋 Triage session ended!")
                    break
                
                if not user_input:
                    continue
                
                if user_input.lower() == 'triage':
                    print("🔄 Running full triage cycle with agent delegation...")
                    results = await self.run_validator_triage_cycle()
                    print("📊 Triage Results:")
                    print(json.dumps(results, indent=2, default=str))
                elif user_input.lower() == 'search':
                    print("🔍 Delegating search to JIRA specialist...")
                    response = await self.chat("Search for validator failure tickets and provide a detailed summary")
                    print(f"Results: {response}")
                elif user_input.lower().startswith('analyze '):
                    ticket_id = user_input[8:].strip()
                    print(f"🔬 Delegating analysis of ticket {ticket_id} to JIRA specialist...")
                    response = await self.chat(
                        f"Analyze ticket {ticket_id} in detail. Extract failure information, URLs to logs, "
                        f"and provide recommendations for resolution."
                    )
                    print(f"Analysis: {response}")
                elif user_input.lower().startswith('create ticket '):
                    description = user_input[14:].strip()
                    print("📝 Delegating ticket creation to JIRA specialist...")
                    response = await self.chat(f"Create a new validator failure ticket with description: {description}")
                    print(f"Result: {response}")
                elif user_input.lower() == 'list tickets':
                    print("📋 Getting ticket list from JIRA specialist...")
                    response = await self.chat("List recent tickets, focusing on validator failures and critical issues")
                    print(f"Tickets: {response}")
                else:
                    print("🤖 Processing request with agent delegation...")
                    response = await self.chat(user_input)
                    print(f"Response: {response}")
                
                print()
                
            except KeyboardInterrupt:
                print("\n👋 Triage session ended!")
                break
            except Exception as e:
                print(f"Error: {e}\n")


@click.command()
@click.option(
    "--model", 
    default="gemini-2.0-flash-exp",
    help="LLM model to use (default: gemini-2.0-flash-exp)"
)
@click.option(
    "--message", 
    "-m",
    help="Send a single message instead of starting interactive mode"
)
@click.option(
    "--triage",
    is_flag=True,
    help="Run a full validator failure triage cycle"
)
@click.option(
    "--examples",
    is_flag=True,
    help="Show usage examples"
)
def main(model: str, message: Optional[str], triage: bool, examples: bool):
    """Run the Main Orchestrator Agent for validator failure triage."""
    
    if examples:
        show_examples()
        return
    
    # Check for required environment variables
    if not os.getenv("GOOGLE_API_KEY") and not os.getenv("GOOGLE_APPLICATION_CREDENTIALS"):
        print("⚠️  Warning: No Google API credentials found.")
        print("   Please set GOOGLE_API_KEY environment variable")
        print("   or configure Google Application Credentials.\n")
    
    async def run_agent():
        agent = MainAgent(model=model)
        
        if triage:
            # Run full triage cycle
            print("🎯 Running validator failure triage cycle...")
            results = await agent.run_validator_triage_cycle()
            print("\n📊 Triage Cycle Results:")
            print(json.dumps(results, indent=2, default=str))
        elif message:
            # Single message mode
            response = await agent.chat(message)
            print(f"Main Agent: {response}")
        else:
            # Interactive mode
            await agent.start_interactive_triage_session()
    
    try:
        asyncio.run(run_agent())
    except KeyboardInterrupt:
        print("\n👋 Goodbye!")


def show_examples():
    """Show usage examples."""
    examples = """
🎯 Main Agent - Usage Examples (With Subagent Delegation)

## Interactive Triage Mode with Team Delegation
main-agent

## Single Command Mode  
main-agent -m "Search for critical validator failures and delegate analysis"
main-agent -m "Analyze ticket TICKET-003 for root cause using specialist agents"

## Run Full Triage Cycle with Delegation
main-agent --triage

## Example Interactive Commands

1. **Full Triage Cycle (with automatic delegation):**
   > triage
   
2. **Search for Failures (delegates to JIRA specialist):**
   > search
   
3. **Analyze Specific Ticket (delegates to JIRA specialist):**
   > analyze TICKET-003
   
4. **Create New Ticket (delegates to JIRA specialist):**
   > create ticket "Validator timeout error in payment processing"
   
5. **List Tickets (delegates to JIRA specialist):**
   > list tickets
   
6. **Custom Analysis with Delegation:**
   > "Find all validator failures with timeout errors and recommend fixes"

## New Architecture (ADK Subagent Pattern)
Main Agent (Orchestrator)
    ↓ contains subagents
    ├── JIRA Specialist Agent (handles all ticket operations)
    ↓ delegates automatically based on request type
JIRA Specialist uses MCP Server
    ↓ returns specialized results
Main Agent (coordinates and provides final recommendations)

## Key Benefits
✅ Automatic delegation based on request content
✅ Specialized agents for different tasks  
✅ Better separation of concerns
✅ Improved error handling and context
✅ More maintainable and extensible

## Environment Setup
export GOOGLE_API_KEY="your-api-key-here"
# or
export GOOGLE_APPLICATION_CREDENTIALS="/path/to/credentials.json"
"""
    print(examples)


if __name__ == "__main__":
    main()
