"""Ticket Whisperer - MCP Server and Agent for ticket management."""

from .mcp_servers.models import Ticket, TicketStatus, TicketPriority, TicketSummary, TicketFilter
from .mcp_servers.server import TicketStore, app as mcp_server
# from .agents.jira_agent.agent import JiraAgent  # Import handled by entry point

__version__ = "0.1.0"
__all__ = [
    "Ticket",
    "TicketStatus", 
    "TicketPriority",
    "TicketSummary",
    "TicketFilter",
    "TicketStore",
    "mcp_server",
]
