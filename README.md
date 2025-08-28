# 🎫 Ticket Whisperer

A lightweight MCP (Model Context Protocol) server and ADK (Agent Development Kit) agent for intelligent ticket management.

## Overview

Ticket Whisperer consists of three main components:

1. **MCP Server** - Provides ticket management tools via Model Context Protocol
2. **Main Agent** - Orchestrator for validator failure triage and analysis workflows
3. **JIRA Agent** - Specialized agent for ticket operations and JIRA interactions

## Features

### Ticket Management
- ✅ Create new tickets with full metadata
- ✅ View and retrieve ticket details
- ✅ Update ticket status, priority, assignee, and more
- ✅ List tickets with flexible filtering
- ✅ Get ticket summary statistics
- ✅ Analyze workload distribution and trends

### Agent Capabilities

**Main Agent (Orchestrator):**
- 🎯 Automated validator failure triage workflows
- 🔄 Orchestrates complex multi-step analysis processes
- 🧠 Makes strategic decisions based on analysis results
- 📊 Provides comprehensive reporting and recommendations
- 🚨 Monitors and prioritizes critical failures

**JIRA Agent (Ticket Operations):**
- 🎫 Natural language ticket management
- 💬 Interactive chat interface for ticket operations
- 🔍 Smart ticket filtering and search capabilities
- 📝 Detailed ticket description analysis with link extraction
- 🔗 URL extraction from ticket descriptions for log analysis

## Installation

```bash
# Clone the repository
cd ticket-whisperer/second-try

# Install dependencies
pip install -e .

# Set up Google API credentials (required for ADK agent)
export GOOGLE_API_KEY="your-api-key-here"
# OR
export GOOGLE_APPLICATION_CREDENTIALS="/path/to/credentials.json"
```

## Quick Start

### Using the Main Agent (Orchestrator)

Start interactive triage session:
```bash
main-agent
```

Run full validator failure triage cycle:
```bash
main-agent --triage
```

Send single orchestration command:
```bash
main-agent -m "Analyze all critical validator failures and provide recommendations"
```

### Using the JIRA Agent (Ticket Operations)

Start an interactive session:
```bash
jira-agent
```

Send a single command:
```bash
jira-agent -m "Create a ticket for fixing the login bug"
jira-agent -m "Show me all high priority tickets" 
jira-agent -m "Get detailed description of TICKET-003 with link extraction"
```

### Using the MCP Server Directly

Start the MCP server:
```bash
ticket-whisperer-server
```

The server exposes the following tools:
- `create_ticket` - Create new tickets
- `get_ticket` - Retrieve ticket by ID
- `update_ticket` - Update existing tickets
- `list_tickets` - List tickets with filtering
- `get_ticket_summary` - Get statistics
- `analyze_tickets` - Analyze workload, priority, trends
- `get_ticket_description` - Get detailed ticket description with link extraction and failure analysis
- `search_validator_failures` - Search for validator failure tickets with JQL queries

## Usage Examples

### Creating Tickets
```
You: Create a new high-priority ticket for implementing user authentication with OAuth
Agent: I'll create a high-priority ticket for implementing OAuth authentication...
```

### Viewing Tickets
```
You: Show me all tickets assigned to alice@example.com
Agent: Here are the tickets assigned to alice@example.com...
```

### Updating Tickets
```
You: Mark ticket TICKET-001 as resolved
Agent: I've updated ticket TICKET-001 and marked it as resolved...
```

### Analysis
```
You: Analyze our current workload distribution
Agent: Here's the workload analysis across your team...
```

## MCP Integration

You can integrate this MCP server with other MCP-compatible clients by adding it to your MCP configuration:

```json
{
  "mcpServers": {
    "ticket-whisperer": {
      "type": "stdio",
      "command": "ticket-whisperer-server"
    }
  }
}
```

## Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   ADK Agent     │───▶│   MCP Server    │───▶│  Ticket Store   │
│                 │    │                 │    │  (In-Memory)    │
│ - Natural Lang  │    │ - Tools/APIs    │    │ - Tickets       │
│ - Conversation  │    │ - Validation    │    │ - Persistence   │
│ - Intelligence  │    │ - Business Logic│    │ - Queries       │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

## Ticket Model

```python
{
  "id": "TICKET-001",
  "title": "Fix login bug",
  "description": "Users cannot log in with special characters",
  "status": "open",           # open, in_progress, resolved, closed
  "priority": "high",         # low, medium, high, critical
  "assignee": "alice@example.com",
  "reporter": "bob@example.com", 
  "created_at": "2024-01-15T10:30:00Z",
  "updated_at": "2024-01-15T10:30:00Z",
  "tags": ["bug", "authentication"],
  "estimated_hours": 8.0
}
```

## Development

### Project Structure
```
src/whisperer/
├── __init__.py      # Package exports
├── models.py        # Pydantic data models
├── server.py        # MCP server implementation
└── agent.py         # ADK agent implementation
```

### Running Tests
```bash
# Run tests (when implemented)
python -m pytest tests/
```

### Extending the System

To add new ticket management features:

1. **Add new tools to the MCP server** (`server.py`)
2. **Update the agent instructions** (`agent.py`) 
3. **Add new data models** (`models.py`) if needed

## Configuration

### Environment Variables
- `GOOGLE_API_KEY` - Required for ADK agent
- `GOOGLE_APPLICATION_CREDENTIALS` - Alternative auth method

### Agent Options
- `--model` - Change the LLM model (default: gemini-2.0-flash-exp)
- `--message` - Send single message instead of interactive mode
- `--examples` - Show usage examples

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

## License

MIT License - see LICENSE file for details.

## Support

For issues and questions:
- 📧 Create an issue in this repository
- 💬 Check the examples with `ticket-whisperer-agent --examples`
