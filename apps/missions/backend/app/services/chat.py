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
from app.models.suggested_action import SuggestedAction, ActionType, ActionPriority, ActionStatus
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
        attachment_ids: list[str] = None,
    ) -> AsyncGenerator[dict, None]:
        """Stream chat response from LLM.

        Args:
            mission_id: Mission UUID
            user_message: User's message
            attachment_ids: Optional list of file UUIDs attached to this message

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

        # Link attachments to this message if present
        # Also automatically analyze images with vision tool
        if attachment_ids:
            from app.models.message_attachment import MessageAttachment
            from app.models.mission_file import MissionFile

            for file_id in attachment_ids:
                # Get the mission file to copy metadata
                mission_file = self.db.query(MissionFile).filter(
                    MissionFile.id == UUID(file_id)
                ).first()

                if mission_file:
                    attachment = MessageAttachment(
                        message_id=user_msg.id,
                        filename=mission_file.original_name,
                        original_name=mission_file.original_name,
                        mime_type=mission_file.mime_type,
                        size_bytes=mission_file.size_bytes,
                        storage_path=mission_file.storage_path,
                    )
                    self.db.add(attachment)

                    # Automatically analyze images with vision tool
                    if mission_file.mime_type and mission_file.mime_type.startswith('image/'):
                        yield {"type": "tool_start", "tool_name": "analyze_image", "tool_id": f"auto-vision-{file_id}"}

                        # Execute vision analysis with current session and provider
                        vision_result = await tool_registry.execute(
                            "analyze_image",
                            file_id=file_id,
                            prompt="Describe this image in detail. Extract any text, numbers, dates, or key information visible in the image.",
                            db_session=self.db,
                            llm_provider=provider
                        )

                        # Save vision result to attachment
                        if vision_result.success:
                            attachment.description = vision_result.data.get("description", "")
                            attachment.vision_model = vision_result.data.get("model", "")

                        yield {
                            "type": "tool_result",
                            "tool_name": "analyze_image",
                            "tool_id": f"auto-vision-{file_id}",
                            "success": vision_result.success,
                            "result": vision_result.data if vision_result.success else vision_result.error,
                        }

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
        from app.models.mission_file import MissionFile

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

        # Add context files information
        context_files = self.db.query(MissionFile).filter(
            MissionFile.mission_id == mission.id
        ).all()

        if context_files:
            prompt += "\n\nContext Files Available:\n"
            prompt += "The user has uploaded the following files as context for this mission. You can use the analyze_image or parse_document tools to extract information from these files:\n"
            for file in context_files:
                file_type = "Image" if file.mime_type and file.mime_type.startswith("image/") else "Document"
                prompt += f"- {file.original_name} ({file_type}, uploaded {file.uploaded_at.strftime('%Y-%m-%d')}, ID: {file.id})\n"

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

            # Generate suggested actions
            mission = messages[0].mission if messages else None
            if mission:
                suggestions = await self._generate_suggestions(mission, provider, messages)

                for suggestion in suggestions:
                    # Check if similar suggestion already exists
                    existing = self.db.query(SuggestedAction).filter(
                        SuggestedAction.mission_id == mission.id,
                        SuggestedAction.title == suggestion["title"],
                        SuggestedAction.status == ActionStatus.PENDING,
                    ).first()

                    if not existing:
                        action = SuggestedAction(
                            mission_id=mission.id,
                            type=ActionType(suggestion["type"]),
                            title=suggestion["title"],
                            description=suggestion["description"],
                            reasoning=suggestion.get("reasoning"),
                            priority=ActionPriority(suggestion["priority"]),
                            status=ActionStatus.PENDING,
                            related_goal=suggestion.get("related_goal"),
                        )
                        self.db.add(action)

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

            # Generate suggested actions
            mission = messages[0].mission if messages else None
            if mission:
                suggestions = await self._generate_suggestions(mission, provider, messages)

                for suggestion in suggestions:
                    # Check if similar suggestion already exists
                    existing = self.db.query(SuggestedAction).filter(
                        SuggestedAction.mission_id == mission.id,
                        SuggestedAction.title == suggestion["title"],
                        SuggestedAction.status == ActionStatus.PENDING,
                    ).first()

                    if not existing:
                        action = SuggestedAction(
                            mission_id=mission.id,
                            type=ActionType(suggestion["type"]),
                            title=suggestion["title"],
                            description=suggestion["description"],
                            reasoning=suggestion.get("reasoning"),
                            priority=ActionPriority(suggestion["priority"]),
                            status=ActionStatus.PENDING,
                            related_goal=suggestion.get("related_goal"),
                        )
                        self.db.add(action)

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

    async def _generate_suggestions(
        self,
        mission: Mission,
        provider: LLMProvider,
        recent_messages: list[Message],
    ) -> list[dict]:
        """Generate suggested actions based on conversation context.

        Args:
            mission: The mission object
            provider: LLM provider to use
            recent_messages: Recent conversation messages

        Returns:
            list[dict]: List of suggested action data
        """
        # Only generate suggestions every few messages to avoid spam
        message_count = len(recent_messages)

        # DEBUG: Log message count for troubleshooting
        print(f"[SUGGESTIONS] Message count: {message_count}")

        # Trigger every 2nd turn, aligned with observed odd counts in active chats
        # (e.g. 65, 67, 69...) so we don't permanently miss generation.
        if message_count < 3 or message_count % 2 == 0:
            print(f"[SUGGESTIONS] Skipping generation (count={message_count})")
            return []

        print(f"[SUGGESTIONS] Generating suggestions for mission {mission.id}...")

        # Build context for suggestion generation
        conversation_context = "\n".join([
            f"{msg.role}: {msg.content[:200]}"
            for msg in recent_messages[-6:]
        ])

        suggestion_prompt = f"""Based on this mission and recent conversation, suggest 1-3 concrete actions that would help accomplish the mission goals.

Mission: {mission.name}
Goals: {mission.goals}

Recent conversation:
{conversation_context}

For each suggestion, provide:
1. type: "user_action" (user should do), "agent_action" (AI should do), or "info_request" (need more info)
2. title: Brief action title (max 50 chars)
3. description: What should be done (max 200 chars)
4. reasoning: Why this action would help (max 150 chars)
5. priority: "high", "medium", or "low"
6. related_goal: Which mission goal this relates to (optional)

Return ONLY valid JSON array format:
[{{"type": "user_action", "title": "...", "description": "...", "reasoning": "...", "priority": "high", "related_goal": "..."}}]

Only suggest actions that are:
- Concrete and actionable
- Directly related to mission goals
- Not already discussed or completed
- Truly valuable (quality over quantity)

If no good suggestions, return empty array: []"""

        try:
            api_key = decrypt_api_key(provider.api_key_encrypted)

            if provider.name == "claude":
                print(f"[SUGGESTIONS] Using Claude provider")
                client = anthropic.AsyncAnthropic(api_key=api_key)
                response = await client.messages.create(
                    model=provider.default_model or "claude-sonnet-4-20250514",
                    max_tokens=1024,
                    messages=[{"role": "user", "content": suggestion_prompt}],
                )
                content = response.content[0].text
                print(f"[SUGGESTIONS] Claude response: {content[:200]}...")

            elif provider.name == "openai":
                print(f"[SUGGESTIONS] Using OpenAI provider")
                client = openai.AsyncOpenAI(api_key=api_key)
                response = await client.chat.completions.create(
                    model=provider.default_model or "gpt-4-turbo-preview",
                    messages=[{"role": "user", "content": suggestion_prompt}],
                )
                content = response.choices[0].message.content
                print(f"[SUGGESTIONS] OpenAI response: {content[:200]}...")
            else:
                print(f"[SUGGESTIONS] Unsupported provider: {provider.name}")
                return []

            # Parse JSON response
            # Extract JSON from markdown code blocks if present
            if "```json" in content:
                content = content.split("```json")[1].split("```")[0].strip()
            elif "```" in content:
                content = content.split("```")[1].split("```")[0].strip()

            print(f"[SUGGESTIONS] Parsing JSON from: {content[:100]}...")
            suggestions = json.loads(content)
            print(f"[SUGGESTIONS] Parsed {len(suggestions)} suggestions")

            # Validate and filter suggestions
            valid_suggestions = []
            for suggestion in suggestions:
                if not isinstance(suggestion, dict):
                    print(f"[SUGGESTIONS] Skipping non-dict suggestion: {suggestion}")
                    continue

                # Validate required fields
                if not all(k in suggestion for k in ["type", "title", "description", "priority"]):
                    print(f"[SUGGESTIONS] Missing required fields in: {suggestion}")
                    continue

                # Validate enum values
                if suggestion["type"] not in ["user_action", "agent_action", "info_request"]:
                    print(f"[SUGGESTIONS] Invalid type: {suggestion['type']}")
                    continue
                if suggestion["priority"] not in ["high", "medium", "low"]:
                    print(f"[SUGGESTIONS] Invalid priority: {suggestion['priority']}")
                    continue

                valid_suggestions.append(suggestion)
                print(f"[SUGGESTIONS] Valid suggestion: {suggestion['title']}")

            print(f"[SUGGESTIONS] Returning {len(valid_suggestions)} valid suggestions")
            return valid_suggestions[:3]  # Max 3 suggestions

        except Exception as e:
            # Log the error for debugging
            print(f"[SUGGESTIONS] Error generating suggestions: {e}")
            import traceback
            traceback.print_exc()
            return []

    async def autonomous_check(self, mission: Mission) -> dict:
        """Perform an autonomous check of a mission.

        This method is called by the scheduler to review mission progress,
        analyze context, and generate suggestions without user interaction.

        Args:
            mission: The mission to check

        Returns:
            dict with keys: success, suggestions_count, summary
        """
        from datetime import datetime, timezone

        print(f"[AUTONOMOUS] Starting check for mission: {mission.name}")

        try:
            # Get provider
            provider = mission.llm_provider
            if not provider:
                provider = self.db.query(LLMProvider).filter(
                    LLMProvider.is_enabled == True,
                    LLMProvider.api_key_encrypted.isnot(None),
                ).first()

            if not provider or not provider.api_key_encrypted:
                print(f"[AUTONOMOUS] No LLM provider available for mission {mission.id}")
                return {
                    "success": False,
                    "suggestions_count": 0,
                    "summary": "No LLM provider configured",
                }

            # Get recent messages for context
            recent_messages = (
                self.db.query(Message)
                .filter(Message.mission_id == mission.id)
                .order_by(Message.created_at.desc())
                .limit(10)
                .all()
            )

            # Build context summary
            conversation_summary = ""
            if recent_messages:
                conversation_summary = "\n".join([
                    f"[{msg.created_at.strftime('%Y-%m-%d %H:%M')}] {msg.role}: {msg.content[:150]}..."
                    for msg in reversed(recent_messages[-5:])
                ])
            else:
                conversation_summary = "No conversation history yet."

            # Get mission files for context
            file_context = ""
            if mission.files:
                file_context = "\n".join([
                    f"- {file.original_name} ({file.mime_type})"
                    for file in mission.files[:5]
                ])

            # Create autonomous check prompt
            check_prompt = f"""You are performing an autonomous check on this mission. Review the current status and suggest next actions if needed.

Mission: {mission.name}
Description: {mission.description}
Goals: {mission.goals}
Status: {mission.status}
Check Interval: {mission.check_interval}

Recent Activity:
{conversation_summary}

Available Context Files:
{file_context if file_context else "None"}

Your task:
1. Assess progress toward mission goals
2. Identify if any action is needed
3. Generate 0-3 concrete suggestions (only if truly valuable)

Return a JSON object with:
{{
  "status_summary": "Brief (1-2 sentences) assessment of current mission status",
  "progress_assessment": "Brief statement about progress toward goals",
  "suggestions": [
    {{"type": "user_action/agent_action/info_request", "title": "...", "description": "...", "reasoning": "...", "priority": "high/medium/low", "related_goal": "..."}}
  ]
}}

IMPORTANT:
- Only suggest actions if there's something meaningful to do
- If mission is on track and no action needed, return empty suggestions array
- Be concise and actionable
- Return ONLY valid JSON"""

            # Call LLM
            api_key = decrypt_api_key(provider.api_key_encrypted)

            if provider.name == "claude":
                client = anthropic.AsyncAnthropic(api_key=api_key)
                response = await client.messages.create(
                    model=provider.default_model or "claude-sonnet-4-20250514",
                    max_tokens=1024,
                    messages=[{"role": "user", "content": check_prompt}],
                )
                content = response.content[0].text

            elif provider.name == "openai":
                client = openai.AsyncOpenAI(api_key=api_key)
                response = await client.chat.completions.create(
                    model=provider.default_model or "gpt-4-turbo-preview",
                    messages=[{"role": "user", "content": check_prompt}],
                    max_tokens=1024,
                )
                content = response.choices[0].message.content
            else:
                return {
                    "success": False,
                    "suggestions_count": 0,
                    "summary": f"Unsupported provider: {provider.name}",
                }

            # Parse response
            if "```json" in content:
                content = content.split("```json")[1].split("```")[0].strip()
            elif "```" in content:
                content = content.split("```")[1].split("```")[0].strip()

            result = json.loads(content)

            # Extract suggestions and create them
            suggestions = result.get("suggestions", [])
            suggestions_count = 0

            for suggestion in suggestions:
                # Validate suggestion structure
                if not all(k in suggestion for k in ["type", "title", "description", "priority"]):
                    continue

                # Check if similar suggestion already exists
                existing = self.db.query(SuggestedAction).filter(
                    SuggestedAction.mission_id == mission.id,
                    SuggestedAction.title == suggestion["title"],
                    SuggestedAction.status == ActionStatus.PENDING,
                ).first()

                if not existing:
                    action = SuggestedAction(
                        mission_id=mission.id,
                        type=ActionType(suggestion["type"]),
                        title=suggestion["title"],
                        description=suggestion["description"],
                        reasoning=suggestion.get("reasoning"),
                        priority=ActionPriority(suggestion["priority"]),
                        status=ActionStatus.PENDING,
                        related_goal=suggestion.get("related_goal"),
                    )
                    self.db.add(action)
                    suggestions_count += 1

            # Update mission check timestamps
            now = datetime.now(timezone.utc)
            mission.last_checked_at = now

            # Calculate next check time based on interval
            from datetime import timedelta
            if mission.check_interval == "hourly":
                mission.next_check_at = now + timedelta(hours=1)
            elif mission.check_interval == "daily":
                mission.next_check_at = now + timedelta(days=1)
            elif mission.check_interval == "weekly":
                mission.next_check_at = now + timedelta(weeks=1)
            # manual = no next check scheduled

            self.db.commit()

            summary = f"{result.get('status_summary', 'Check completed')} - {result.get('progress_assessment', 'Progress assessed')}"

            print(f"[AUTONOMOUS] Check complete for {mission.name}: {suggestions_count} suggestions")

            return {
                "success": True,
                "suggestions_count": suggestions_count,
                "summary": summary,
            }

        except Exception as e:
            print(f"[AUTONOMOUS] Error checking mission {mission.id}: {e}")
            import traceback
            traceback.print_exc()
            return {
                "success": False,
                "suggestions_count": 0,
                "summary": f"Check failed: {str(e)}",
            }
