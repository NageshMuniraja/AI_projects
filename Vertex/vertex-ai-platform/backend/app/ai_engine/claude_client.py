"""Claude API client with streaming, tool use, and error handling."""

import anthropic
import structlog
from typing import Optional, AsyncGenerator

from app.core.config import get_settings
from app.ai_engine.prompt_builder import build_full_prompt
from app.ai_engine.tools import get_available_tools, execute_tool

logger = structlog.get_logger()
settings = get_settings()


class ClaudeClient:
    """Async Claude API client for generating AI responses."""

    def __init__(self):
        self.client = anthropic.AsyncAnthropic(api_key=settings.ANTHROPIC_API_KEY)
        self.model = settings.CLAUDE_MODEL
        self.max_tokens = settings.CLAUDE_MAX_TOKENS

    async def generate_response(
        self,
        tenant: dict,
        messages: list[dict],
        channel: str = "web",
        rag_context: Optional[str] = None,
        contact_info: Optional[dict] = None,
        use_tools: bool = True,
    ) -> dict:
        """
        Generate an AI response using Claude API.

        Returns:
            dict with keys: content, tokens_used, model, tool_calls, confidence
        """
        system_prompt, formatted_messages = build_full_prompt(
            tenant=tenant,
            channel=channel,
            rag_context=rag_context,
            contact_info=contact_info,
            messages=messages,
        )

        # Build API call params
        params = {
            "model": self.model,
            "max_tokens": self.max_tokens,
            "system": system_prompt,
            "messages": formatted_messages,
        }

        # Add tools if enabled
        if use_tools:
            tools = get_available_tools(tenant.get("industry", "general"))
            if tools:
                params["tools"] = tools

        try:
            response = await self.client.messages.create(**params)

            # Handle tool use
            tool_calls = []
            final_content = ""

            for block in response.content:
                if block.type == "text":
                    final_content += block.text
                elif block.type == "tool_use":
                    tool_result = await execute_tool(
                        tool_name=block.name,
                        tool_input=block.input,
                        tenant=tenant,
                    )
                    tool_calls.append({
                        "tool": block.name,
                        "input": block.input,
                        "result": tool_result,
                    })

            # If there were tool calls, get a final response with tool results
            if tool_calls and response.stop_reason == "tool_use":
                # Add assistant's tool use message
                formatted_messages.append({
                    "role": "assistant",
                    "content": response.content,
                })

                # Add tool results
                tool_result_content = []
                for i, block in enumerate(response.content):
                    if block.type == "tool_use":
                        matching_call = next(
                            (tc for tc in tool_calls if tc["tool"] == block.name),
                            None
                        )
                        tool_result_content.append({
                            "type": "tool_result",
                            "tool_use_id": block.id,
                            "content": str(matching_call["result"]) if matching_call else "Tool execution failed",
                        })

                formatted_messages.append({
                    "role": "user",
                    "content": tool_result_content,
                })

                # Get final response
                final_response = await self.client.messages.create(
                    model=self.model,
                    max_tokens=self.max_tokens,
                    system=system_prompt,
                    messages=formatted_messages,
                )

                final_content = ""
                for block in final_response.content:
                    if block.type == "text":
                        final_content += block.text

                total_tokens = (
                    response.usage.input_tokens + response.usage.output_tokens +
                    final_response.usage.input_tokens + final_response.usage.output_tokens
                )
            else:
                total_tokens = response.usage.input_tokens + response.usage.output_tokens

            return {
                "content": final_content,
                "tokens_used": total_tokens,
                "model": self.model,
                "tool_calls": tool_calls if tool_calls else None,
                "stop_reason": response.stop_reason,
            }

        except anthropic.RateLimitError:
            logger.warning("Claude API rate limit reached")
            return {
                "content": "I'm experiencing high demand right now. Please try again in a moment.",
                "tokens_used": 0,
                "model": self.model,
                "tool_calls": None,
                "error": "rate_limit",
            }
        except anthropic.APIError as e:
            logger.error("Claude API error", error=str(e))
            return {
                "content": "I'm having trouble processing your request. Let me connect you with a team member.",
                "tokens_used": 0,
                "model": self.model,
                "tool_calls": None,
                "error": str(e),
            }

    async def generate_stream(
        self,
        tenant: dict,
        messages: list[dict],
        channel: str = "web",
        rag_context: Optional[str] = None,
        contact_info: Optional[dict] = None,
    ) -> AsyncGenerator[str, None]:
        """Stream AI response tokens for real-time display."""
        system_prompt, formatted_messages = build_full_prompt(
            tenant=tenant,
            channel=channel,
            rag_context=rag_context,
            contact_info=contact_info,
            messages=messages,
        )

        async with self.client.messages.stream(
            model=self.model,
            max_tokens=self.max_tokens,
            system=system_prompt,
            messages=formatted_messages,
        ) as stream:
            async for text in stream.text_stream:
                yield text

    async def analyze_intent(self, message: str, industry: str = "general") -> dict:
        """Quickly classify message intent and sentiment."""
        response = await self.client.messages.create(
            model="claude-haiku-4-5-20251001",  # Use Haiku for fast classification
            max_tokens=200,
            system="You are an intent classifier. Respond ONLY with valid JSON.",
            messages=[{
                "role": "user",
                "content": f"""Classify this customer message for a {industry} business.
Message: "{message}"

Respond with JSON:
{{"intent": "booking|inquiry|complaint|emergency|greeting|farewell|other", "sentiment": "positive|neutral|negative", "confidence": 0.0-1.0, "extracted_entities": {{"name": null, "phone": null, "email": null, "service": null, "date": null, "time": null}}}}"""
            }],
        )

        import json
        try:
            return json.loads(response.content[0].text)
        except (json.JSONDecodeError, IndexError):
            return {"intent": "other", "sentiment": "neutral", "confidence": 0.5}


# Singleton instance
claude_client = ClaudeClient()
