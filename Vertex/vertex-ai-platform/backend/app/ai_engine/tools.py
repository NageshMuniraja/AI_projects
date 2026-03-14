"""AI Tool definitions for Claude function calling."""

from datetime import datetime, timezone
from typing import Optional
import structlog

logger = structlog.get_logger()


def get_available_tools(industry: str = "general") -> list[dict]:
    """Return tool definitions based on industry."""
    base_tools = [
        {
            "name": "book_appointment",
            "description": "Book an appointment for the customer. Use this when the customer wants to schedule a visit, consultation, or service.",
            "input_schema": {
                "type": "object",
                "properties": {
                    "customer_name": {
                        "type": "string",
                        "description": "Customer's full name"
                    },
                    "customer_phone": {
                        "type": "string",
                        "description": "Customer's phone number"
                    },
                    "service": {
                        "type": "string",
                        "description": "The service or type of appointment"
                    },
                    "preferred_date": {
                        "type": "string",
                        "description": "Preferred date in YYYY-MM-DD format"
                    },
                    "preferred_time": {
                        "type": "string",
                        "description": "Preferred time in HH:MM format"
                    },
                    "notes": {
                        "type": "string",
                        "description": "Any additional notes or special requests"
                    }
                },
                "required": ["customer_name", "service", "preferred_date", "preferred_time"]
            }
        },
        {
            "name": "capture_lead",
            "description": "Capture a potential customer's information as a lead. Use when someone expresses interest but isn't ready to book.",
            "input_schema": {
                "type": "object",
                "properties": {
                    "name": {
                        "type": "string",
                        "description": "Lead's name"
                    },
                    "phone": {
                        "type": "string",
                        "description": "Lead's phone number"
                    },
                    "email": {
                        "type": "string",
                        "description": "Lead's email address"
                    },
                    "interest": {
                        "type": "string",
                        "description": "What the lead is interested in"
                    },
                    "notes": {
                        "type": "string",
                        "description": "Additional context from the conversation"
                    }
                },
                "required": ["name", "interest"]
            }
        },
        {
            "name": "check_availability",
            "description": "Check available appointment slots for a given date and service.",
            "input_schema": {
                "type": "object",
                "properties": {
                    "date": {
                        "type": "string",
                        "description": "Date to check in YYYY-MM-DD format"
                    },
                    "service": {
                        "type": "string",
                        "description": "Service type to check availability for"
                    }
                },
                "required": ["date"]
            }
        },
        {
            "name": "escalate_to_human",
            "description": "Transfer the conversation to a human team member. Use when the customer specifically requests it or when the query is beyond your capabilities.",
            "input_schema": {
                "type": "object",
                "properties": {
                    "reason": {
                        "type": "string",
                        "description": "Reason for escalation"
                    },
                    "priority": {
                        "type": "string",
                        "enum": ["low", "medium", "high", "urgent"],
                        "description": "Priority level"
                    }
                },
                "required": ["reason"]
            }
        },
    ]

    return base_tools


async def execute_tool(
    tool_name: str,
    tool_input: dict,
    tenant: dict,
) -> dict:
    """Execute a tool call and return the result."""
    logger.info("Executing tool", tool=tool_name, input=tool_input)

    if tool_name == "book_appointment":
        return await _handle_book_appointment(tool_input, tenant)
    elif tool_name == "capture_lead":
        return await _handle_capture_lead(tool_input, tenant)
    elif tool_name == "check_availability":
        return await _handle_check_availability(tool_input, tenant)
    elif tool_name == "escalate_to_human":
        return await _handle_escalate(tool_input, tenant)
    else:
        return {"status": "error", "message": f"Unknown tool: {tool_name}"}


async def _handle_book_appointment(input_data: dict, tenant: dict) -> dict:
    """Handle appointment booking tool call."""
    # In production, this would create an actual appointment in the database
    # and integrate with calendar systems
    return {
        "status": "success",
        "message": f"Appointment booked for {input_data['customer_name']}",
        "details": {
            "service": input_data["service"],
            "date": input_data["preferred_date"],
            "time": input_data["preferred_time"],
            "confirmation_id": f"APT-{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}",
        }
    }


async def _handle_capture_lead(input_data: dict, tenant: dict) -> dict:
    """Handle lead capture tool call."""
    return {
        "status": "success",
        "message": f"Lead captured for {input_data['name']}",
        "lead_id": f"LEAD-{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}",
    }


async def _handle_check_availability(input_data: dict, tenant: dict) -> dict:
    """Handle availability check tool call."""
    # In production, this would check actual appointment database
    return {
        "status": "success",
        "date": input_data["date"],
        "available_slots": [
            "09:00", "09:30", "10:00", "10:30", "11:00",
            "14:00", "14:30", "15:00", "15:30", "16:00"
        ],
        "message": "These slots are currently available."
    }


async def _handle_escalate(input_data: dict, tenant: dict) -> dict:
    """Handle escalation to human agent."""
    return {
        "status": "success",
        "message": "Conversation has been flagged for human review.",
        "priority": input_data.get("priority", "medium"),
        "reason": input_data["reason"],
    }
