"""Chat service for LLM integration."""
from typing import AsyncGenerator
from uuid import UUID
from sqlalchemy.orm import Session
import anthropic
import openai
import json

from app.models.mission import Mission
from app.models.message import Message
from app.models.llm_provider import LLMProvider
from app.utils.encryption import decrypt_api_key
from app.tools import tool_registry


class ChatService:
    """Service for handling LLM chat interactions."""

    def __init__(self, db: Session):
        self.db = db

    async def stream_chat(
        self,
        mission_id: UUID,
        user_message: str,
    ) -> AsyncGenerator[dict, None]:
        """Stream chat response from LLM.

        Args:
            mission_id: Mission UUID
            user_message: User's message

        Yields:
            dict: Streaming chunks with type, content, and metadata
        """
        # Get mission
        mission = self.db.query(Mission).filter(Mission.id == mission_id).first()
        if not mission:
            yield {"type": "error", "content": "Mission not found"}
            return

        # Get LLM provider
        provider = None
        if mission.llm_provider_id:
            provider = (
                self.db.query(LLMProvider)
                .filter(LLMProvider.id == mission.llm_provider_id)
                .first()
            )

        # Fallback to first enabled provider WITH API key if mission doesn't have one
        if not provider:
            provider = (
                self.db.query(LLMProvider)
                .filter(
                    LLMProvider.is_enabled == True,
                    LLMProvider.api_key_encrypted.isnot(None),
                )
                .first()
            )

        # If mission-selected provider has no key, fallback to a configured provider
        if provider and not provider.api_key_encrypted:
            provider = (
                self.db.query(LLMProvider)
                .filter(
                    LLMProvider.is_enabled == True,
                    LLMProvider.api_key_encrypted.isnot(None),
                )
                .first()
            )

        if not provider or not provider.api_key_encrypted:
            yield {
                "type": "error",
                "content": "No LLM provider configured. Please add an API key in Settings.",
            }
            return

        # Save user message
        user_msg = Message(
            mission_id=mission_id,
            role="user",
            content=user_message,
        )
        self.db.add(user_msg)
        self.db.commit()

        yield {"type": "user_message_saved", "message_id": str(user_msg.id)}

        # Get conversation history
        messages = (
            self.db.query(Message)
            .filter(Message.mission_id == mission_id)
            .order_by(Message.created_at.asc())
            .all()
        )

        # Build system prompt
        system_prompt = self._build_system_prompt(mission)

        # Stream response based on provider
        if provider.name == "claude":
            async for chunk in self._stream_claude(provider, system_prompt, messages):
                yield chunk
        elif provider.name == "openai":
            async for chunk in self._stream_openai(provider, system_prompt, messages):
                yield chunk
        else:
            yield {"type": "error", "content": f"Unsupported provider: {provider.name}"}

    def _build_system_prompt(self, mission: Mission) -> str:
        """Build system prompt from mission context."""
        prompt = f"""You are an AI agent working on the following mission:

Mission: {mission.name}

Description: {mission.description}

Goals: {mission.goals}

Your role is to help the user accomplish these goals. Be helpful, proactive, and use your knowledge to provide valuable assistance.

You have access to tools that can help you:
- web_search: Search the web for current information
- analyze_image: Analyze images uploaded by the user to extract text, numbers, or visual information
- parse_document: Extract text from uploaded documents (PDFs, images with OCR)

Use these tools when appropriate to provide better assistance. Always explain what you're doing when using a tool."""

        return prompt

    async def _stream_claude(
        self,
        provider: LLMProvider,
        system_prompt: str,
        messages: list[Message],
    ) -> AsyncGenerator[dict, None]:
        """Stream response from Claude with tool support."""
        try:
            api_key = decrypt_api_key(provider.api_key_encrypted)
            client = anthropic.AsyncAnthropic(api_key=api_key)

            # Convert messages to Claude format
            claude_messages = []
            for msg in messages:
                if msg.role in ["user", "assistant"]:
                    claude_messages.append({"role": msg.role, "content": msg.content})

            model = provider.default_model or "claude-sonnet-4-20250514"

            # Get available tools
            tools = tool_registry.get_claude_tools()

            # Track response
            full_response = ""
            input_tokens = 0
            output_tokens = 0
            tool_uses = []

            # Stream from Claude with tools
            async with client.messages.stream(
                model=model,
                max_tokens=4096,
                system=system_prompt,
                messages=claude_messages,
                tools=tools,
            ) as stream:
                async for text in stream.text_stream:
                    full_response += text
                    yield {"type": "content", "content": text}

                # Get final message
                final_message = await stream.get_final_message()
                input_tokens = final_message.usage.input_tokens
                output_tokens = final_message.usage.output_tokens

                # Check for tool uses
                for block in final_message.content:
                    if block.type == "tool_use":
                        tool_uses.append({
                            "id": block.id,
                            "name": block.name,
                            "input": block.input,
                        })

            # If tools were used, execute them and continue conversation
            if tool_uses:
                for tool_use in tool_uses:
                    yield {
                        "type": "tool_start",
                        "tool_name": tool_use["name"],
                        "tool_id": tool_use["id"],
                    }

                    # Execute tool
                    result = await tool_registry.execute(
                        tool_use["name"],
                        **tool_use["input"]
                    )

                    # Save tool call message
                    tool_msg = Message(
                        mission_id=messages[0].mission_id if messages else None,
                        role="tool",
                        content=f"Used {tool_use['name']}",
                        tool_name=tool_use["name"],
                        tool_input=tool_use["input"],
                        tool_output=result.data if result.success else {"error": result.error},
                    )
                    self.db.add(tool_msg)
                    self.db.commit()

                    yield {
                        "type": "tool_result",
                        "tool_name": tool_use["name"],
                        "tool_id": tool_use["id"],
                        "success": result.success,
                        "result": result.data if result.success else result.error,
                    }

                # Continue conversation with tool results
                tool_results = []
                for tool_use, result_data in zip(tool_uses, tool_uses):  # Need actual results here
                    tool_results.append({
                        "type": "tool_result",
                        "tool_use_id": tool_use["id"],
                        "content": json.dumps(result.data) if result.success else result.error,
                    })

                # Add tool results to messages and get new response
                claude_messages.append({
                    "role": "assistant",
                    "content": final_message.content,
                })
                claude_messages.append({
                    "role": "user",
                    "content": tool_results,
                })

                # Stream continuation
                async with client.messages.stream(
                    model=model,
                    max_tokens=4096,
                    system=system_prompt,
                    messages=claude_messages,
                    tools=tools,
                ) as stream:
                    continuation = ""
                    async for text in stream.text_stream:
                        continuation += text
                        full_response += text
                        yield {"type": "content", "content": text}

                    final_message = await stream.get_final_message()
                    input_tokens += final_message.usage.input_tokens
                    output_tokens += final_message.usage.output_tokens

            # Save assistant message
            assistant_msg = Message(
                mission_id=messages[0].mission_id if messages else None,
                role="assistant",
                content=full_response,
                input_tokens=input_tokens,
                output_tokens=output_tokens,
                model_used=model,
            )
            self.db.add(assistant_msg)
            self.db.commit()

            yield {
                "type": "done",
                "message_id": str(assistant_msg.id),
                "input_tokens": input_tokens,
                "output_tokens": output_tokens,
                "model": model,
            }

        except Exception as e:
            yield {"type": "error", "content": f"Claude API error: {str(e)}"}

    async def _stream_openai(
        self,
        provider: LLMProvider,
        system_prompt: str,
        messages: list[Message],
    ) -> AsyncGenerator[dict, None]:
        """Stream response from OpenAI with tool support."""
        try:
            api_key = decrypt_api_key(provider.api_key_encrypted)
            client = openai.AsyncOpenAI(api_key=api_key)

            # Convert messages to OpenAI format
            openai_messages = [{"role": "system", "content": system_prompt}]
            for msg in messages:
                if msg.role in ["user", "assistant", "system"]:
                    openai_messages.append({"role": msg.role, "content": msg.content})

            model = provider.default_model or "gpt-4-turbo-preview"

            # Get available tools
            tools = tool_registry.get_openai_tools()

            # Track response
            full_response = ""
            input_tokens = 0
            output_tokens = 0
            tool_calls = []
            current_tool_call = None

            # Stream from OpenAI with tools
            stream = await client.chat.completions.create(
                model=model,
                messages=openai_messages,
                stream=True,
                max_completion_tokens=4096,
                tools=tools,
                tool_choice="auto",
            )

            async for chunk in stream:
                delta = chunk.choices[0].delta

                # Handle text content
                if delta.content:
                    full_response += delta.content
                    yield {"type": "content", "content": delta.content}

                # Handle tool calls
                if delta.tool_calls:
                    for tool_call_delta in delta.tool_calls:
                        if tool_call_delta.index is not None:
                            # New tool call
                            if current_tool_call is None or tool_call_delta.index != current_tool_call["index"]:
                                if current_tool_call:
                                    tool_calls.append(current_tool_call)

                                current_tool_call = {
                                    "index": tool_call_delta.index,
                                    "id": tool_call_delta.id or "",
                                    "name": tool_call_delta.function.name if tool_call_delta.function else "",
                                    "arguments": tool_call_delta.function.arguments if tool_call_delta.function else "",
                                }
                            else:
                                # Continue existing tool call
                                if tool_call_delta.function and tool_call_delta.function.arguments:
                                    current_tool_call["arguments"] += tool_call_delta.function.arguments

                # Get token counts
                if hasattr(chunk, "usage") and chunk.usage:
                    input_tokens = chunk.usage.prompt_tokens
                    output_tokens = chunk.usage.completion_tokens

            # Add last tool call if exists
            if current_tool_call:
                tool_calls.append(current_tool_call)

            # Execute tools if any were called
            if tool_calls:
                for tool_call in tool_calls:
                    yield {
                        "type": "tool_start",
                        "tool_name": tool_call["name"],
                        "tool_id": tool_call["id"],
                    }

                    # Parse arguments
                    try:
                        args = json.loads(tool_call["arguments"])
                    except json.JSONDecodeError:
                        args = {}

                    # Execute tool
                    result = await tool_registry.execute(tool_call["name"], **args)

                    # Save tool call
                    tool_msg = Message(
                        mission_id=messages[0].mission_id if messages else None,
                        role="tool",
                        content=f"Used {tool_call['name']}",
                        tool_name=tool_call["name"],
                        tool_input=args,
                        tool_output=result.data if result.success else {"error": result.error},
                    )
                    self.db.add(tool_msg)
                    self.db.commit()

                    yield {
                        "type": "tool_result",
                        "tool_name": tool_call["name"],
                        "tool_id": tool_call["id"],
                        "success": result.success,
                        "result": result.data if result.success else result.error,
                    }

                    # Add tool result to messages
                    openai_messages.append({
                        "role": "assistant",
                        "content": None,
                        "tool_calls": [{
                            "id": tool_call["id"],
                            "type": "function",
                            "function": {
                                "name": tool_call["name"],
                                "arguments": tool_call["arguments"],
                            },
                        }],
                    })
                    openai_messages.append({
                        "role": "tool",
                        "tool_call_id": tool_call["id"],
                        "content": json.dumps(result.data) if result.success else result.error,
                    })

                # Get continuation with tool results
                stream = await client.chat.completions.create(
                    model=model,
                    messages=openai_messages,
                    stream=True,
                    max_completion_tokens=4096,
                )

                async for chunk in stream:
                    if chunk.choices[0].delta.content:
                        content = chunk.choices[0].delta.content
                        full_response += content
                        yield {"type": "content", "content": content}

                    if hasattr(chunk, "usage") and chunk.usage:
                        input_tokens += chunk.usage.prompt_tokens
                        output_tokens += chunk.usage.completion_tokens

            # Save assistant message
            assistant_msg = Message(
                mission_id=messages[0].mission_id if messages else None,
                role="assistant",
                content=full_response,
                input_tokens=input_tokens,
                output_tokens=output_tokens,
                model_used=model,
            )
            self.db.add(assistant_msg)
            self.db.commit()

            yield {
                "type": "done",
                "message_id": str(assistant_msg.id),
                "input_tokens": input_tokens,
                "output_tokens": output_tokens,
                "model": model,
            }

        except Exception as e:
            yield {"type": "error", "content": f"OpenAI API error: {str(e)}"}
