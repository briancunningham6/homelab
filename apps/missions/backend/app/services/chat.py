"""Chat service for LLM integration."""
from typing import AsyncGenerator
from uuid import UUID
from sqlalchemy.orm import Session
import anthropic
import openai

from app.models.mission import Mission
from app.models.message import Message
from app.models.llm_provider import LLMProvider
from app.utils.encryption import decrypt_api_key


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

        # Fallback to first enabled provider if mission doesn't have one
        if not provider:
            provider = (
                self.db.query(LLMProvider)
                .filter(LLMProvider.is_enabled == True)
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

Your role is to help the user accomplish these goals. Be helpful, proactive, and use your knowledge to provide valuable assistance. Ask clarifying questions when needed."""

        return prompt

    async def _stream_claude(
        self,
        provider: LLMProvider,
        system_prompt: str,
        messages: list[Message],
    ) -> AsyncGenerator[dict, None]:
        """Stream response from Claude."""
        try:
            api_key = decrypt_api_key(provider.api_key_encrypted)
            client = anthropic.AsyncAnthropic(api_key=api_key)

            # Convert messages to Claude format
            claude_messages = []
            for msg in messages:
                if msg.role in ["user", "assistant"]:
                    claude_messages.append({"role": msg.role, "content": msg.content})

            model = provider.default_model or "claude-sonnet-4-20250514"

            # Track response
            full_response = ""
            input_tokens = 0
            output_tokens = 0

            # Stream from Claude
            async with client.messages.stream(
                model=model,
                max_tokens=4096,
                system=system_prompt,
                messages=claude_messages,
            ) as stream:
                async for text in stream.text_stream:
                    full_response += text
                    yield {"type": "content", "content": text}

                # Get final message with token counts
                final_message = await stream.get_final_message()
                input_tokens = final_message.usage.input_tokens
                output_tokens = final_message.usage.output_tokens

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
        """Stream response from OpenAI."""
        try:
            api_key = decrypt_api_key(provider.api_key_encrypted)
            client = openai.AsyncOpenAI(api_key=api_key)

            # Convert messages to OpenAI format
            openai_messages = [{"role": "system", "content": system_prompt}]
            for msg in messages:
                if msg.role in ["user", "assistant", "system"]:
                    openai_messages.append({"role": msg.role, "content": msg.content})

            model = provider.default_model or "gpt-4-turbo-preview"

            # Track response
            full_response = ""
            input_tokens = 0
            output_tokens = 0

            # Stream from OpenAI
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

                # Get token counts from the final chunk
                if hasattr(chunk, "usage") and chunk.usage:
                    input_tokens = chunk.usage.prompt_tokens
                    output_tokens = chunk.usage.completion_tokens

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
