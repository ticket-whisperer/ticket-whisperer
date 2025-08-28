"""Data models for ticket management."""

from datetime import datetime
from enum import Enum
from typing import List, Optional
from pydantic import BaseModel, Field


class TicketStatus(str, Enum):
    """Ticket status enumeration."""
    OPEN = "open"
    IN_PROGRESS = "in_progress"
    RESOLVED = "resolved"
    CLOSED = "closed"


class TicketPriority(str, Enum):
    """Ticket priority enumeration."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class Ticket(BaseModel):
    """Ticket model."""
    id: str = Field(..., description="Unique ticket identifier")
    title: str = Field(..., description="Ticket title")
    description: str = Field(..., description="Ticket description")
    status: TicketStatus = Field(default=TicketStatus.OPEN, description="Ticket status")
    priority: TicketPriority = Field(default=TicketPriority.MEDIUM, description="Ticket priority")
    assignee: Optional[str] = Field(None, description="Assigned user")
    reporter: str = Field(..., description="User who reported the ticket")
    created_at: datetime = Field(default_factory=datetime.now, description="Creation timestamp")
    updated_at: datetime = Field(default_factory=datetime.now, description="Last update timestamp")
    tags: List[str] = Field(default_factory=list, description="Ticket tags")
    estimated_hours: Optional[float] = Field(None, description="Estimated hours to complete")


class TicketSummary(BaseModel):
    """Summary of tickets."""
    total_tickets: int
    open_tickets: int
    in_progress_tickets: int
    resolved_tickets: int
    closed_tickets: int
    high_priority_tickets: int
    critical_priority_tickets: int


class TicketFilter(BaseModel):
    """Filter criteria for tickets."""
    status: Optional[TicketStatus] = None
    priority: Optional[TicketPriority] = None
    assignee: Optional[str] = None
    reporter: Optional[str] = None
    tags: Optional[List[str]] = None
