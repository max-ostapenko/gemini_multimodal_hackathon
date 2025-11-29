"""Gemini LLM service for multimodal processing."""

import base64
import json
from typing import Any, Type, TypeVar

from google import genai
from google.genai import types
from pydantic import BaseModel

from app.config import get_settings

T = TypeVar("T", bound=BaseModel)


class GeminiService:
    """Service for interacting with Google Gemini API."""

    def __init__(self):
        """Initialize the Gemini client."""
        settings = get_settings()
        self.client = genai.Client(api_key=settings.google_api_key)
        self.model = settings.gemini_model

    def _create_image_part(self, image_base64: str) -> types.Part:
        """Create an image part from base64 encoded data."""
        # Detect image type from base64 header or default to jpeg
        if image_base64.startswith("data:"):
            # Extract mime type from data URL
            header, image_base64 = image_base64.split(",", 1)
            mime_type = header.split(":")[1].split(";")[0]
        else:
            mime_type = "image/jpeg"

        image_bytes = base64.b64decode(image_base64)
        return types.Part.from_bytes(data=image_bytes, mime_type=mime_type)

    async def generate_structured_output(
        self,
        prompt: str,
        response_schema: Type[T],
        image_base64: str | None = None,
        system_instruction: str | None = None,
    ) -> T:
        """
        Generate structured JSON output from multimodal input.

        Args:
            prompt: Text prompt
            response_schema: Pydantic model class for response structure
            image_base64: Optional base64 encoded image
            system_instruction: Optional system instruction

        Returns:
            Parsed response as the specified Pydantic model
        """
        contents = []

        # Add image if provided
        if image_base64:
            contents.append(self._create_image_part(image_base64))

        # Add text prompt
        contents.append(prompt)

        # Configure generation with JSON schema
        config = types.GenerateContentConfig(
            response_mime_type="application/json",
            response_schema=response_schema,
        )

        if system_instruction:
            config.system_instruction = system_instruction

        # Generate response
        response = self.client.models.generate_content(
            model=self.model,
            contents=contents,
            config=config,
        )

        # Parse response into Pydantic model
        response_text = response.text
        response_dict = json.loads(response_text)
        return response_schema.model_validate(response_dict)

    async def generate_text(
        self,
        prompt: str,
        image_base64: str | None = None,
        system_instruction: str | None = None,
    ) -> str:
        """
        Generate text from multimodal input.

        Args:
            prompt: Text prompt
            image_base64: Optional base64 encoded image
            system_instruction: Optional system instruction

        Returns:
            Generated text response
        """
        contents = []

        # Add image if provided
        if image_base64:
            contents.append(self._create_image_part(image_base64))

        # Add text prompt
        contents.append(prompt)

        config = types.GenerateContentConfig()
        if system_instruction:
            config.system_instruction = system_instruction

        response = self.client.models.generate_content(
            model=self.model,
            contents=contents,
            config=config,
        )

        return response.text
