#!/usr/bin/env python3
"""
Simple Jira MCP Server using FastMCP

A clean, working implementation of a Jira MCP server using the FastMCP framework.
"""

import os
import asyncio
from typing import Any, Dict

from jira import JIRA
from mcp.server.fastmcp import FastMCP


# Create the MCP server
mcp = FastMCP("jira-mcp")

# Global Jira client
jira_client = None


def connect_to_jira():
    """Initialize connection to Jira."""
    global jira_client
    
    jira_url = os.getenv("JIRA_URL")
    jira_token = os.getenv("JIRA_PERSONAL_TOKEN")

    if not jira_url or not jira_token:
        raise ValueError(
            "JIRA_URL and JIRA_PERSONAL_TOKEN environment variables must be set"
        )

    try:
        jira_client = JIRA(
            server=jira_url,
            token_auth=jira_token,
            options={"verify": True}
        )
        # Test the connection
        jira_client.myself()
        print(f"✅ Connected to Jira: {jira_url}")
    except Exception as e:
        raise ConnectionError(f"Failed to connect to Jira: {e}")


@mcp.tool()
def search_issues(jql: str, max_results: int = 50) -> str:
    """
    Search for Jira issues using JQL (Jira Query Language).
    
    Args:
        jql: The JQL query string
        max_results: Maximum number of issues to return (default: 50)
    
    Returns:
        List of matching issues with their details
    """
    if not jira_client:
        connect_to_jira()
    
    try:
        issues = jira_client.search_issues(jql, maxResults=max_results)
        
        if not issues:
            return f"No issues found for JQL: {jql}"

        issue_summaries = []
        for issue in issues:
            issue_summaries.append(
                f"Issue Key: {issue.key}, Summary: {issue.fields.summary}, "
                f"Status: {issue.fields.status.name}, "
                f"Assignee: {issue.fields.assignee.displayName if issue.fields.assignee else 'Unassigned'}"
            )
        
        return "\n".join(issue_summaries)
        
    except Exception as e:
        return f"Error searching issues: {str(e)}"


@mcp.tool()
def get_issue(issue_key: str) -> str:
    """
    Get details of a specific Jira issue by its key.
    
    Args:
        issue_key: The key of the Jira issue (e.g., 'PROJ-123')
    
    Returns:
        Detailed information about the issue
    """
    if not jira_client:
        connect_to_jira()
    
    try:
        issue = jira_client.issue(issue_key)
        
        details = (
            f"Issue Key: {issue.key}\n"
            f"Summary: {issue.fields.summary}\n"
            f"Description: {issue.fields.description if issue.fields.description else 'N/A'}\n"
            f"Status: {issue.fields.status.name}\n"
            f"Assignee: {issue.fields.assignee.displayName if issue.fields.assignee else 'Unassigned'}\n"
            f"Reporter: {issue.fields.reporter.displayName if issue.fields.reporter else 'N/A'}\n"
            f"Priority: {issue.fields.priority.name if issue.fields.priority else 'N/A'}\n"
            f"Created: {issue.fields.created}\n"
            f"Updated: {issue.fields.updated}"
        )
        return details
        
    except Exception as e:
        return f"Error getting issue {issue_key}: {str(e)}"


@mcp.tool()
def get_projects() -> str:
    """
    Get a list of all accessible Jira projects.
    
    Returns:
        List of available projects
    """
    if not jira_client:
        connect_to_jira()
    
    try:
        projects = jira_client.projects()
        project_summaries = [f"Key: {p.key}, Name: {p.name}" for p in projects]
        return "\n".join(project_summaries)
        
    except Exception as e:
        return f"Error getting projects: {str(e)}"


@mcp.tool()
def create_issue(project: str, summary: str, description: str = "", issue_type: str = "Task") -> str:
    """
    Create a new Jira issue.
    
    Args:
        project: The project key or ID
        summary: Summary of the issue
        description: Detailed description of the issue
        issue_type: Type of issue (e.g., 'Bug', 'Task', 'Story')
    
    Returns:
        The key of the newly created issue
    """
    if not jira_client:
        connect_to_jira()
    
    try:
        issue_dict = {
            "project": {"key": project},
            "summary": summary,
            "description": description,
            "issuetype": {"name": issue_type},
        }

        new_issue = jira_client.create_issue(fields=issue_dict)
        return f"Issue created: {new_issue.key}"
        
    except Exception as e:
        return f"Error creating issue: {str(e)}"


@mcp.tool()
def add_comment(issue_key: str, comment_body: str) -> str:
    """
    Add a comment to a Jira issue.
    
    Args:
        issue_key: The key of the Jira issue (e.g., 'PROJ-123')
        comment_body: The text content of the comment
    
    Returns:
        Confirmation message
    """
    if not jira_client:
        connect_to_jira()
    
    try:
        jira_client.add_comment(issue_key, comment_body)
        return f"Comment added to {issue_key}"
        
    except Exception as e:
        return f"Error adding comment to {issue_key}: {str(e)}"


if __name__ == "__main__":
    # Initialize Jira connection on startup
    try:
        connect_to_jira()
    except Exception as e:
        print(f"Warning: Could not connect to Jira on startup: {e}")
        print("Will try to connect when tools are called.")
    
    # Run the server
    mcp.run()