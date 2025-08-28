"""MCP Server for ticket management."""

import asyncio
import json
import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional

import click
from mcp.server.lowlevel import Server
from mcp.types import Resource, Tool, TextContent
from mcp.server.models import InitializationOptions
from mcp.types import ServerCapabilities, ToolsCapability

from whisperer.mcp_servers.models import Ticket, TicketStatus, TicketPriority, TicketSummary, TicketFilter


class TicketStore:
    """In-memory ticket storage (replace with database in production)."""
    
    def __init__(self):
        self.tickets: Dict[str, Ticket] = {}
        self._init_sample_data()
    
    def _init_sample_data(self):
        """Initialize with some sample tickets."""
        sample_tickets = [
            {
                "id": "TICKET-001",
                "title": "Fix login bug",
                "description": "Users cannot log in with special characters in password",
                "status": TicketStatus.OPEN,
                "priority": TicketPriority.HIGH,
                "reporter": "alice@example.com",
                "tags": ["bug", "authentication"]
            },
            {
                "id": "TICKET-002", 
                "title": "Add dark mode",
                "description": "Implement dark mode theme for better user experience",
                "status": TicketStatus.IN_PROGRESS,
                "priority": TicketPriority.MEDIUM,
                "assignee": "bob@example.com",
                "reporter": "carol@example.com",
                "tags": ["feature", "ui"]
            },
            {
                "id": "TICKET-003",
                "title": "Validator failure in CI/CD pipeline",
                "description": "The validator failed during the nightly build process. Error occurred in the data validation step. Full logs available at: https://jenkins.example.com/job/validator-pipeline/123/console. Stack trace shows null pointer exception in ValidationEngine.validate() method. This needs immediate attention as it's blocking the release pipeline.",
                "status": TicketStatus.OPEN,
                "priority": TicketPriority.CRITICAL,
                "reporter": "ci-system@example.com",
                "assignee": "dev-team@example.com",
                "tags": ["validator", "ci-cd", "critical", "pipeline"]
            }
        ]
        
        for ticket_data in sample_tickets:
            ticket = Ticket(**ticket_data)
            self.tickets[ticket.id] = ticket
    
    async def create_ticket(self, ticket_data: Dict[str, Any]) -> Ticket:
        """Create a new ticket."""
        if "id" not in ticket_data:
            ticket_data["id"] = f"TICKET-{uuid.uuid4().hex[:8].upper()}"
        
        ticket = Ticket(**ticket_data)
        self.tickets[ticket.id] = ticket
        return ticket
    
    async def get_ticket(self, ticket_id: str) -> Optional[Ticket]:
        """Get a ticket by ID."""
        return self.tickets.get(ticket_id)
    
    async def update_ticket(self, ticket_id: str, updates: Dict[str, Any]) -> Optional[Ticket]:
        """Update an existing ticket."""
        if ticket_id not in self.tickets:
            return None
        
        ticket = self.tickets[ticket_id]
        for key, value in updates.items():
            if hasattr(ticket, key):
                setattr(ticket, key, value)
        
        ticket.updated_at = datetime.now()
        return ticket
    
    async def list_tickets(self, filter_criteria: Optional[TicketFilter] = None) -> List[Ticket]:
        """List tickets with optional filtering."""
        tickets = list(self.tickets.values())
        
        if not filter_criteria:
            return tickets
        
        filtered_tickets = []
        for ticket in tickets:
            if filter_criteria.status and ticket.status != filter_criteria.status:
                continue
            if filter_criteria.priority and ticket.priority != filter_criteria.priority:
                continue
            if filter_criteria.assignee and ticket.assignee != filter_criteria.assignee:
                continue
            if filter_criteria.reporter and ticket.reporter != filter_criteria.reporter:
                continue
            if filter_criteria.tags:
                if not any(tag in ticket.tags for tag in filter_criteria.tags):
                    continue
            
            filtered_tickets.append(ticket)
        
        return filtered_tickets
    
    async def get_summary(self) -> TicketSummary:
        """Get ticket summary statistics."""
        tickets = list(self.tickets.values())
        return TicketSummary(
            total_tickets=len(tickets),
            open_tickets=len([t for t in tickets if t.status == TicketStatus.OPEN]),
            in_progress_tickets=len([t for t in tickets if t.status == TicketStatus.IN_PROGRESS]),
            resolved_tickets=len([t for t in tickets if t.status == TicketStatus.RESOLVED]),
            closed_tickets=len([t for t in tickets if t.status == TicketStatus.CLOSED]),
            high_priority_tickets=len([t for t in tickets if t.priority == TicketPriority.HIGH]),
            critical_priority_tickets=len([t for t in tickets if t.priority == TicketPriority.CRITICAL]),
        )


# Initialize ticket store
ticket_store = TicketStore()

# Initialize MCP server
app = Server("ticket-whisperer")


@app.list_tools()
async def handle_list_tools() -> List[Tool]:
    """List available tools."""
    return [
        Tool(
            name="create_ticket",
            description="Create a new ticket",
            inputSchema={
                "type": "object",
                "properties": {
                    "title": {"type": "string", "description": "Ticket title"},
                    "description": {"type": "string", "description": "Ticket description"},
                    "priority": {
                        "type": "string", 
                        "enum": ["low", "medium", "high", "critical"],
                        "description": "Ticket priority"
                    },
                    "reporter": {"type": "string", "description": "Reporter email"},
                    "assignee": {"type": "string", "description": "Assignee email (optional)"},
                    "tags": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Ticket tags"
                    }
                },
                "required": ["title", "description", "reporter"]
            }
        ),
        Tool(
            name="get_ticket",
            description="Get a ticket by ID",
            inputSchema={
                "type": "object",
                "properties": {
                    "ticket_id": {"type": "string", "description": "Ticket ID"}
                },
                "required": ["ticket_id"]
            }
        ),
        Tool(
            name="update_ticket",
            description="Update an existing ticket",
            inputSchema={
                "type": "object",
                "properties": {
                    "ticket_id": {"type": "string", "description": "Ticket ID"},
                    "updates": {
                        "type": "object",
                        "description": "Fields to update",
                        "properties": {
                            "title": {"type": "string"},
                            "description": {"type": "string"},
                            "status": {
                                "type": "string",
                                "enum": ["open", "in_progress", "resolved", "closed"]
                            },
                            "priority": {
                                "type": "string",
                                "enum": ["low", "medium", "high", "critical"]
                            },
                            "assignee": {"type": "string"},
                            "tags": {"type": "array", "items": {"type": "string"}}
                        }
                    }
                },
                "required": ["ticket_id", "updates"]
            }
        ),
        Tool(
            name="list_tickets",
            description="List tickets with optional filtering",
            inputSchema={
                "type": "object",
                "properties": {
                    "status": {
                        "type": "string",
                        "enum": ["open", "in_progress", "resolved", "closed"],
                        "description": "Filter by status"
                    },
                    "priority": {
                        "type": "string",
                        "enum": ["low", "medium", "high", "critical"],
                        "description": "Filter by priority"
                    },
                    "assignee": {"type": "string", "description": "Filter by assignee"},
                    "reporter": {"type": "string", "description": "Filter by reporter"},
                    "tags": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Filter by tags"
                    }
                }
            }
        ),
        Tool(
            name="get_ticket_summary",
            description="Get summary statistics of all tickets",
            inputSchema={"type": "object", "properties": {}}
        ),
        Tool(
            name="analyze_tickets",
            description="Analyze tickets and provide insights",
            inputSchema={
                "type": "object",
                "properties": {
                    "analysis_type": {
                        "type": "string",
                        "enum": ["workload", "priority", "trends"],
                        "description": "Type of analysis to perform"
                    }
                },
                "required": ["analysis_type"]
            }
        ),
        Tool(
            name="get_ticket_description",
            description="Get detailed ticket description with analysis for validator failures",
            inputSchema={
                "type": "object",
                "properties": {
                    "ticket_id": {"type": "string", "description": "Ticket ID"},
                    "extract_links": {
                        "type": "boolean", 
                        "description": "Extract URLs from description (default: true)",
                        "default": True
                    },
                    "analyze_failure": {
                        "type": "boolean",
                        "description": "Analyze for validator failure patterns (default: false)",
                        "default": False
                    }
                },
                "required": ["ticket_id"]
            }
        ),
        Tool(
            name="search_validator_failures",
            description="Search for validator failure tickets in JIRA",
            inputSchema={
                "type": "object",
                "properties": {
                    "jql_query": {
                        "type": "string",
                        "description": "Custom JQL query for validator failures (optional)",
                        "default": ""
                    },
                    "status_filter": {
                        "type": "string",
                        "enum": ["open", "in_progress", "resolved", "closed", "all"],
                        "description": "Filter by ticket status (default: open)",
                        "default": "open"
                    },
                    "days_back": {
                        "type": "integer",
                        "description": "Search tickets from last N days (default: 7)",
                        "default": 7
                    }
                }
            }
        )
    ]


@app.call_tool()
async def handle_call_tool(name: str, arguments: dict) -> List[TextContent]:
    """Handle tool calls."""
    
    if name == "create_ticket":
        ticket = await ticket_store.create_ticket(arguments)
        return [TextContent(
            type="text",
            text=f"Created ticket {ticket.id}: {ticket.title}\n\n" + 
                 json.dumps(ticket.model_dump(), indent=2, default=str)
        )]
    
    elif name == "get_ticket":
        ticket = await ticket_store.get_ticket(arguments["ticket_id"])
        if not ticket:
            return [TextContent(
                type="text",
                text=f"Ticket {arguments['ticket_id']} not found"
            )]
        return [TextContent(
            type="text",
            text=json.dumps(ticket.model_dump(), indent=2, default=str)
        )]
    
    elif name == "update_ticket":
        ticket = await ticket_store.update_ticket(
            arguments["ticket_id"], 
            arguments["updates"]
        )
        if not ticket:
            return [TextContent(
                type="text",
                text=f"Ticket {arguments['ticket_id']} not found"
            )]
        return [TextContent(
            type="text",
            text=f"Updated ticket {ticket.id}\n\n" + 
                 json.dumps(ticket.model_dump(), indent=2, default=str)
        )]
    
    elif name == "list_tickets":
        filter_criteria = None
        if arguments:
            filter_criteria = TicketFilter(**arguments)
        
        tickets = await ticket_store.list_tickets(filter_criteria)
        tickets_data = [ticket.model_dump() for ticket in tickets]
        return [TextContent(
            type="text",
            text=f"Found {len(tickets)} tickets:\n\n" + 
                 json.dumps(tickets_data, indent=2, default=str)
        )]
    
    elif name == "get_ticket_summary":
        summary = await ticket_store.get_summary()
        return [TextContent(
            type="text",
            text="Ticket Summary:\n\n" + 
                 json.dumps(summary.model_dump(), indent=2, default=str)
        )]
    
    elif name == "analyze_tickets":
        analysis_type = arguments["analysis_type"]
        tickets = await ticket_store.list_tickets()
        
        if analysis_type == "workload":
            workload = {}
            for ticket in tickets:
                if ticket.assignee:
                    workload[ticket.assignee] = workload.get(ticket.assignee, 0) + 1
            
            analysis = {
                "analysis_type": "workload",
                "workload_by_assignee": workload,
                "unassigned_tickets": len([t for t in tickets if not t.assignee])
            }
        
        elif analysis_type == "priority":
            priority_counts = {}
            for ticket in tickets:
                priority_counts[ticket.priority] = priority_counts.get(ticket.priority, 0) + 1
            
            analysis = {
                "analysis_type": "priority",
                "priority_distribution": priority_counts,
                "high_priority_open": len([
                    t for t in tickets 
                    if t.priority in ["high", "critical"] and t.status == "open"
                ])
            }
        
        elif analysis_type == "trends":
            status_counts = {}
            for ticket in tickets:
                status_counts[ticket.status] = status_counts.get(ticket.status, 0) + 1
            
            analysis = {
                "analysis_type": "trends",
                "status_distribution": status_counts,
                "completion_rate": round(
                    (status_counts.get("resolved", 0) + status_counts.get("closed", 0)) / 
                    len(tickets) * 100, 2
                ) if tickets else 0
            }
        
        return [TextContent(
            type="text",
            text="Ticket Analysis:\n\n" + json.dumps(analysis, indent=2, default=str)
        )]
    
    elif name == "get_ticket_description":
        ticket_id = arguments["ticket_id"]
        extract_links = arguments.get("extract_links", True)
        analyze_failure = arguments.get("analyze_failure", False)
        
        ticket = await ticket_store.get_ticket(ticket_id)
        if not ticket:
            return [TextContent(
                type="text",
                text=f"Ticket {ticket_id} not found"
            )]
        
        result = {
            "ticket_id": ticket.id,
            "title": ticket.title,
            "description": ticket.description,
            "status": ticket.status,
            "priority": ticket.priority
        }
        
        if extract_links:
            # Extract URLs from description
            import re
            url_pattern = r'https?://[^\s<>"{}|\\^`\[\]]+'
            urls = re.findall(url_pattern, ticket.description)
            result["extracted_urls"] = urls
        
        if analyze_failure:
            # Analyze for validator failure patterns
            description_lower = ticket.description.lower()
            failure_indicators = {
                "has_validator_failure": any(term in description_lower for term in [
                    "validator", "validation", "failed", "error", "exception"
                ]),
                "has_logs_link": any(term in description_lower for term in [
                    "log", "logs", "jenkins", "ci/cd", "build"
                ]),
                "error_keywords": [word for word in [
                    "timeout", "connection", "assertion", "null pointer", "stack trace"
                ] if word in description_lower]
            }
            result["failure_analysis"] = failure_indicators
        
        return [TextContent(
            type="text",
            text="Ticket Description Analysis:\n\n" + 
                 json.dumps(result, indent=2, default=str)
        )]
    
    elif name == "search_validator_failures":
        jql_query = arguments.get("jql_query", "")
        status_filter = arguments.get("status_filter", "open")
        days_back = arguments.get("days_back", 7)
        
        # If custom JQL provided, use it; otherwise use default validator failure search
        if not jql_query:
            # Default search for validator failures (you can customize this JQL)
            base_jql = 'project = "YOUR_PROJECT" AND (summary ~ "validator" OR summary ~ "validation" OR description ~ "validator failure")'
            
            if status_filter != "all":
                # Note: This JQL is for display only - actual filtering happens below with TicketStatus enum
                status_map = {
                    "open": "Open",
                    "in_progress": '"In Progress"',
                    "resolved": "Resolved", 
                    "closed": "Closed"
                }
                base_jql += f' AND status = {status_map.get(status_filter, "Open")}'
            
            base_jql += f' AND created >= -{days_back}d'
            jql_query = base_jql
        
        # For now, simulate search results since we don't have real JIRA connection
        # In real implementation, this would use JIRA API
        mock_results = []
        
        # Search our in-memory tickets for validator-related ones
        all_tickets = await ticket_store.list_tickets()
        for ticket in all_tickets:
            description_lower = ticket.description.lower()
            title_lower = ticket.title.lower()
            
            if any(term in description_lower or term in title_lower for term in [
                "validator", "validation", "failed", "error"
            ]):
                # Convert status filter to match TicketStatus enum values
                if status_filter == "all" or ticket.status.value == status_filter:
                    mock_results.append({
                        "ticket_id": ticket.id,
                        "title": ticket.title,
                        "status": ticket.status,
                        "priority": ticket.priority,
                        "created_at": ticket.created_at.isoformat(),
                        "assignee": ticket.assignee,
                        "description_preview": ticket.description[:200] + "..." if len(ticket.description) > 200 else ticket.description
                    })
        
        result = {
            "jql_query_used": jql_query,
            "total_found": len(mock_results),
            "tickets": mock_results
        }
        
        return [TextContent(
            type="text",
            text="Validator Failure Search Results:\n\n" + 
                 json.dumps(result, indent=2, default=str)
        )]
    
    else:
        return [TextContent(
            type="text",
            text=f"Unknown tool: {name}"
        )]


@click.command()
@click.option("--host", default="localhost", help="Host to bind to")
@click.option("--port", default=8000, type=int, help="Port to bind to")
def main(host: str, port: int):
    """Run the ticket whisperer MCP server."""
    import mcp.server.stdio
    
    async def run_server():
        async with mcp.server.stdio.stdio_server() as (read_stream, write_stream):
            await app.run(
                read_stream,
                write_stream,
                InitializationOptions(
                    server_name="ticket-whisperer",
                    server_version="0.1.0",
                    capabilities=ServerCapabilities(
                        tools=ToolsCapability()
                    )
                )
            )
    
    print(f"🎫 Starting Ticket Whisperer MCP Server...")
    asyncio.run(run_server())


if __name__ == "__main__":
    main()
