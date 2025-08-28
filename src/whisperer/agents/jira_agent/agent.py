"""JIRA Agent - Lightweight ADK agent for JIRA ticket management using MCP server."""

import asyncio
import os
import sys
from pathlib import Path
from typing import Optional

import click
from google.adk.agents import LlmAgent
from google.adk.tools.mcp_tool.mcp_toolset import MCPToolset, StdioServerParameters


class JiraAgent:
    """Lightweight agent for ticket management using MCP server."""
    
    def __init__(self, model: str = "gemini-2.0-flash-exp"):
        """Initialize the agent with MCP toolset."""
        # Get the path to our MCP server script
        server_script = Path(__file__).parent.parent / "mcp_servers" / "server.py"
        
        # Create the MCPToolset that connects to our server
        self.mcp_toolset = MCPToolset(
            connection_params=StdioServerParameters(
                command=sys.executable,  # Use current Python interpreter
                args=[str(server_script)],
            ),
        )
        
        # Create the ADK agent
        self.agent = LlmAgent(
            model=model,
            name="jira_agent",
            instruction="""You are a helpful JIRA ticket management assistant. You can help users:

1. **Create tickets** - Help users create new tickets with proper details
2. **View tickets** - Retrieve and display ticket information  
3. **Update tickets** - Modify ticket status, priority, assignee, etc.
4. **List tickets** - Show tickets with filtering options
5. **Analyze tickets** - Provide insights on workload, priorities, and trends
6. **Get summaries** - Show ticket statistics and overviews

Always be helpful and provide clear, actionable information. When creating or updating tickets, make sure to capture all relevant details. When analyzing tickets, provide meaningful insights that can help with project management.

Use the available MCP tools to perform all ticket operations. Be conversational and ask clarifying questions when needed.""",
            tools=[self.mcp_toolset],
        )
    
    async def chat(self, message: str) -> str:
        """Send a message to the agent and get a response."""
        try:
            response = await self.agent.send_message(message)
            return response.content
        except Exception as e:
            return f"Error: {str(e)}"
    
    async def start_interactive_session(self):
        """Start an interactive chat session."""
        print("🎫 Welcome to JIRA Agent!")
        print("I can help you manage JIRA tickets. Type 'quit' or 'exit' to stop.\n")
        
        while True:
            try:
                user_input = input("You: ").strip()
                
                if user_input.lower() in ['quit', 'exit', 'bye']:
                    print("👋 Goodbye!")
                    break
                
                if not user_input:
                    continue
                
                print("🤖 Thinking...")
                response = await self.chat(user_input)
                print(f"Agent: {response}\n")
                
            except KeyboardInterrupt:
                print("\n👋 Goodbye!")
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
    "--examples",
    is_flag=True,
    help="Show usage examples"
)
def main(model: str, message: Optional[str], examples: bool):
    """Run the JIRA Agent."""
    
    if examples:
        show_examples()
        return
    
    # Check for required environment variables
    if not os.getenv("GOOGLE_API_KEY") and not os.getenv("GOOGLE_APPLICATION_CREDENTIALS"):
        print("⚠️  Warning: No Google API credentials found.")
        print("   Please set GOOGLE_API_KEY environment variable")
        print("   or configure Google Application Credentials.\n")
    
    async def run_agent():
        agent = JiraAgent(model=model)
        
        if message:
            # Single message mode
            response = await agent.chat(message)
            print(f"Agent: {response}")
        else:
            # Interactive mode
            await agent.start_interactive_session()
    
    try:
        asyncio.run(run_agent())
    except KeyboardInterrupt:
        print("\n👋 Goodbye!")


def show_examples():
    """Show usage examples."""
    examples = """
🎫 JIRA Agent - Usage Examples

## Interactive Mode
jira-agent

## Single Message Mode  
jira-agent -m "Create a new ticket for fixing the login bug"
jira-agent -m "Show me all high priority tickets"
jira-agent -m "What's the current ticket summary?"

## Example Conversations

1. **Creating a ticket:**
   "Create a new ticket for implementing dark mode in the UI. Priority should be medium, and assign it to alice@example.com"

2. **Viewing tickets:**
   "Show me all tickets assigned to bob@example.com"
   "List all open tickets with high priority"

3. **Updating tickets:**
   "Update ticket TICKET-001 to mark it as in progress"
   "Change the priority of ticket TICKET-002 to critical"

4. **Analysis:**
   "Analyze the workload distribution across team members"
   "Show me the priority distribution of current tickets"
   "What are the current ticket trends?"

5. **General queries:**
   "What's the status of our project?"
   "Who has the most tickets assigned?"
   "Are there any critical tickets that need attention?"

## Environment Setup
export GOOGLE_API_KEY="your-api-key-here"
# or
export GOOGLE_APPLICATION_CREDENTIALS="/path/to/credentials.json"
"""
    print(examples)


if __name__ == "__main__":
    main()
