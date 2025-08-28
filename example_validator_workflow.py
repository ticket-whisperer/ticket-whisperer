#!/usr/bin/env python3
"""
Example workflow demonstrating validator failure ticket triage with separated agents.

This shows the new architecture:
1. Main Agent - Orchestrates the triage workflow  
2. JIRA Agent - Handles ticket operations via MCP server
3. Main Agent - Analyzes results and makes decisions
"""

import asyncio
import sys
from pathlib import Path

# Add the src directory to Python path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from whisperer import Ticket, TicketStatus, TicketPriority
from whisperer.agents.jira_agent.agent import JiraAgent
from whisperer.agents.main_agent.agent import MainAgent


async def main():
    """Demonstrate validator failure triage workflow with separated agents."""
    
    print("🔍 Validator Failure Triage Workflow Demo - Separated Agents")
    print("=" * 60)
    
    try:
        print("🎯 Initializing Main Agent (Orchestrator)...")
        main_agent = MainAgent()
        
        print("🎫 Initializing JIRA Agent (Ticket Operations)...")
        jira_agent = JiraAgent()
        
        print("\n" + "="*60)
        print("🚀 DEMO 1: Main Agent Orchestrated Triage")
        print("="*60)
        
        print("Running full triage cycle via Main Agent...")
        triage_results = await main_agent.run_validator_triage_cycle()
        print("📊 Triage Results Summary:")
        print(f"- Steps completed: {len(triage_results.get('steps', []))}")
        print(f"- Tickets discovered: {len(triage_results.get('findings', {}).get('discovered_tickets', []))}")
        print(f"- Cycle completed: {triage_results.get('cycle_completed', False)}")
        
        print("\n" + "="*60)
        print("🎫 DEMO 2: Direct JIRA Agent Operations")
        print("="*60)
        
        print("\n📋 Step 1: Search via JIRA Agent")
        search_response = await jira_agent.chat(
            "Search for validator failure tickets from the last 7 days"
        )
        print(f"JIRA Agent Search:\n{search_response[:300]}...\n")
        
        print("📄 Step 2: Get ticket description via JIRA Agent")
        description_response = await jira_agent.chat(
            "Get the detailed description of ticket TICKET-003 with link extraction and failure analysis enabled"
        )
        print(f"JIRA Agent Description:\n{description_response[:300]}...\n")
        
        print("✅ Both Workflows Complete!")
        print("\n🏗️  Architecture Demonstrated:")
        print("1. Main Agent - Orchestrates and makes decisions")
        print("2. JIRA Agent - Handles ticket operations via MCP server")
        print("3. Both agents use the same MCP server but have different roles")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        print("\nTo run this demo:")
        print("1. Set GOOGLE_API_KEY environment variable")
        print("2. Run: pip install -e .")
        print("3. Run: python example_validator_workflow.py")


def show_workflow_diagram():
    """Show the planned workflow architecture."""
    print("""
🏗️  Updated Validator Failure Triage Architecture:

┌─────────────────┐    ┌─────────────────┐
│   Main Agent    │    │   JIRA Agent    │  
│  (Orchestrator) │    │ (Ticket Ops)   │  
│                 │    │                 │    
│ - Runs triage   │    │ - Ticket CRUD   │    ┌─────────────────┐
│ - Analyzes logs │    │ - Searches      │───▶│  MCP Server     │
│ - Makes decisions│    │ - Extracts data │    │                 │
│ - Updates status│    │ - Delegates     │    │ - ticket tools  │
└─────────────────┘    └─────────────────┘    │ - search tools  │
         │                       │             │ - analysis tools│
         └───────────────────────┘             └─────────────────┘

Usage:
• main-agent                    # Interactive orchestration
• main-agent --triage          # Run full triage cycle  
• jira-agent                   # Interactive ticket operations
• jira-agent -m "search..."    # Single ticket command

Workflow:
1. Main Agent → Orchestrates workflow via MCP server
2. JIRA Agent → Handles specific ticket operations via MCP server  
3. Both agents → Use same MCP server, different responsibilities
4. Main Agent → Analyzes results and makes strategic decisions
""")


if __name__ == "__main__":
    import os
    
    if "--diagram" in sys.argv:
        show_workflow_diagram()
    elif os.getenv("GOOGLE_API_KEY") or os.getenv("GOOGLE_APPLICATION_CREDENTIALS"):
        try:
            asyncio.run(main())
        except KeyboardInterrupt:
            print("\n👋 Demo stopped.")
    else:
        print("⚠️  No Google API credentials found.")
        print("Set GOOGLE_API_KEY to run the interactive demo.")
        print("\nOr run with --diagram to see the workflow architecture:")
        print("python example_validator_workflow.py --diagram")
        show_workflow_diagram()
