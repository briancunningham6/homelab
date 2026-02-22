"""Vision tool for analyzing images using Claude Vision or GPT-4V."""
import base64
from pathlib import Path
from typing import List
import uuid
import anthropic
import openai

from .base import BaseTool, ToolParameter, ToolResult


class VisionTool(BaseTool):
    """Analyze images using vision AI models."""

    @property
    def name(self) -> str:
        return "analyze_image"

    @property
    def description(self) -> str:
        return "Analyze an image to extract text, numbers, objects, or contextual information. Use this to read odometers, receipts, documents, diagrams, or any visual information."

    @property
    def parameters(self) -> List[ToolParameter]:
        return [
            ToolParameter(
                name="file_id",
                type="string",
                description="UUID of the image file to analyze",
                required=True,
            ),
            ToolParameter(
                name="prompt",
                type="string",
                description="Specific question or instruction about what to look for in the image (optional)",
                required=False,
            ),
        ]

    async def execute(self, file_id: str, prompt: str = None, db_session=None, llm_provider=None, **kwargs) -> ToolResult:
        """Analyze an image file using vision AI.

        Args:
            file_id: UUID of the image file
            prompt: Optional specific question about the image
            db_session: Optional database session to use
            llm_provider: Optional LLM provider to use

        Returns:
            ToolResult with vision analysis
        """
        try:
            # Import here to avoid circular dependency
            from app.models.mission_file import MissionFile
            from app.models.llm_provider import LLMProvider
            from app.database import SessionLocal
            from app.utils.encryption import decrypt_api_key
            import os

            FILES_DIR = Path("/app/data/files")

            # Use provided session or create new one
            db = db_session if db_session else SessionLocal()
            should_close_db = db_session is None

            try:
                file_obj = db.query(MissionFile).filter(
                    MissionFile.id == uuid.UUID(file_id)
                ).first()

                if not file_obj:
                    return ToolResult(
                        success=False,
                        error=f"Image file {file_id} not found",
                    )

                # Check if it's an image
                if not file_obj.mime_type or not file_obj.mime_type.startswith('image/'):
                    return ToolResult(
                        success=False,
                        error=f"File {file_obj.original_name} is not an image (type: {file_obj.mime_type})",
                    )

                # Use provided provider or get enabled vision-capable provider
                provider = llm_provider
                if not provider:
                    provider = db.query(LLMProvider).filter(
                        LLMProvider.is_enabled == True,
                        LLMProvider.api_key_encrypted.isnot(None),
                    ).first()

                if not provider or not provider.api_key_encrypted:
                    return ToolResult(
                        success=False,
                        error="No LLM provider configured for vision analysis. Please add an API key in Settings.",
                    )

                # Read image file
                image_path = FILES_DIR / file_obj.storage_path
                if not image_path.exists():
                    return ToolResult(
                        success=False,
                        error=f"Image file not found at {file_obj.storage_path}",
                    )

                with open(image_path, 'rb') as f:
                    image_data = base64.b64encode(f.read()).decode()

                # Default prompt if none provided
                if not prompt:
                    prompt = "Describe this image in detail. Extract any text, numbers, dates, or key information you can see."

                # Analyze with appropriate provider
                if provider.name == "claude":
                    result = await self._analyze_with_claude(
                        image_data,
                        file_obj.mime_type,
                        prompt,
                        provider,
                    )
                elif provider.name == "openai":
                    result = await self._analyze_with_openai(
                        image_data,
                        file_obj.mime_type,
                        prompt,
                        provider,
                    )
                else:
                    return ToolResult(
                        success=False,
                        error=f"Provider {provider.name} does not support vision",
                    )

                return ToolResult(
                    success=True,
                    data={
                        "description": result["description"],
                        "filename": file_obj.original_name,
                        "model": result["model"],
                    },
                    metadata={
                        "file_id": str(file_obj.id),
                        "mime_type": file_obj.mime_type,
                        "provider": provider.name,
                    },
                )

            finally:
                if should_close_db:
                    db.close()

        except Exception as e:
            return ToolResult(
                success=False,
                error=f"Vision analysis failed: {str(e)}",
            )

    async def _analyze_with_claude(
        self,
        image_data: str,
        mime_type: str,
        prompt: str,
        provider,
    ) -> dict:
        """Analyze image using Claude Vision."""
        from app.utils.encryption import decrypt_api_key

        api_key = decrypt_api_key(provider.api_key_encrypted)
        client = anthropic.AsyncAnthropic(api_key=api_key)

        response = await client.messages.create(
            model="claude-3-5-sonnet-20241022",  # Vision-capable model
            max_tokens=1024,
            messages=[
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "image",
                            "source": {
                                "type": "base64",
                                "media_type": mime_type,
                                "data": image_data,
                            },
                        },
                        {
                            "type": "text",
                            "text": prompt,
                        },
                    ],
                }
            ],
        )

        return {
            "description": response.content[0].text,
            "model": response.model,
        }

    async def _analyze_with_openai(
        self,
        image_data: str,
        mime_type: str,
        prompt: str,
        provider,
    ) -> dict:
        """Analyze image using GPT-4V."""
        from app.utils.encryption import decrypt_api_key

        api_key = decrypt_api_key(provider.api_key_encrypted)
        client = openai.AsyncOpenAI(api_key=api_key)

        response = await client.chat.completions.create(
            model="gpt-4o",  # GPT-4 Omni has built-in vision capabilities
            messages=[
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": prompt,
                        },
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:{mime_type};base64,{image_data}",
                            },
                        },
                    ],
                }
            ],
            max_tokens=1024,
        )

        return {
            "description": response.choices[0].message.content,
            "model": response.model,
        }
