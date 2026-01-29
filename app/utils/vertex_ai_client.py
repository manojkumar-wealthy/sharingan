"""
Google AI client wrapper for the Multi-Agent system.

Provides a unified interface for interacting with Google AI (Gemini)
generative models, with support for:
- Tool/function calling
- Retry logic
- Response parsing
- Error handling
"""

import json
from typing import Any, Dict, List, Optional, Callable, TypeVar
from functools import wraps
import asyncio

import google.generativeai as genai
from google.generativeai.types import (
    GenerationConfig,
    Tool,
    FunctionDeclaration,
    content_types,
)

from app.config import get_settings
from app.utils.logging import get_logger
from app.utils.exceptions import AgentReasoningError

logger = get_logger(__name__)

T = TypeVar("T")


class VertexAIClient:
    """
    Client wrapper for Google AI (Gemini) generative models.
    
    Handles model initialization, configuration, and provides
    methods for chat-based interactions with tool calling support.
    """

    _initialized: bool = False

    def __init__(
        self,
        model_name: Optional[str] = None,
        temperature: float = 0.1,
        max_output_tokens: int = 2048,
        tools: Optional[List[Tool]] = None,
        system_instruction: Optional[str] = None,
    ):
        """
        Initialize the Google AI client.
        
        Args:
            model_name: Model to use (defaults to GEMINI_FAST_MODEL)
            temperature: Generation temperature (0-1)
            max_output_tokens: Maximum tokens in response
            tools: List of tools for function calling
            system_instruction: System prompt for the model
        """
        settings = get_settings()

        # Initialize Google AI SDK if not already done
        if not VertexAIClient._initialized:
            genai.configure(api_key=settings.GOOGLE_AI_API_KEY)
            VertexAIClient._initialized = True

        self.model_name = model_name or settings.GEMINI_FAST_MODEL
        self.temperature = temperature
        self.max_output_tokens = max_output_tokens
        self.tools = tools
        self.system_instruction = system_instruction

        # Create generation config
        self.generation_config = GenerationConfig(
            temperature=temperature,
            max_output_tokens=max_output_tokens,
            response_mime_type="application/json" if not tools else None,
        )

        # Initialize model
        self.model = self._create_model()

    def _create_model(self) -> genai.GenerativeModel:
        """Create and configure the generative model."""
        return genai.GenerativeModel(
            model_name=self.model_name,
            generation_config=self.generation_config,
            tools=self.tools,
            system_instruction=self.system_instruction,
        )

    async def generate_content(
        self,
        prompt: str,
        **kwargs,
    ) -> str:
        """
        Generate content from a prompt (single turn).
        
        Args:
            prompt: The input prompt
            **kwargs: Additional generation parameters
        
        Returns:
            Generated text response
        """
        try:
            response = await asyncio.to_thread(
                self.model.generate_content,
                prompt,
                **kwargs,
            )

            if response.candidates:
                return response.text

            raise AgentReasoningError(
                agent_name="google_ai",
                message="No candidates in response",
            )

        except Exception as e:
            logger.error("google_ai_generation_error", error=str(e))
            raise

    async def chat_with_tools(
        self,
        prompt: str,
        tool_handlers: Dict[str, Callable],
        max_turns: int = 10,
    ) -> str:
        """
        Execute a chat session with tool calling support.
        
        This method handles multi-turn conversations where the model
        can call tools (functions) and receive their results.
        
        Args:
            prompt: Initial user prompt
            tool_handlers: Dict mapping tool names to handler functions
            max_turns: Maximum conversation turns to prevent infinite loops
        
        Returns:
            Final text response from the model
        """
        chat = self.model.start_chat()
        current_response = await asyncio.to_thread(
            chat.send_message,
            prompt,
        )

        turns = 0
        while turns < max_turns:
            turns += 1

            # Check if response has function calls
            if not current_response.candidates:
                break

            candidate = current_response.candidates[0]
            content = candidate.content

            # Check for function calls in parts
            function_calls = []
            for part in content.parts:
                if hasattr(part, "function_call") and part.function_call:
                    function_calls.append(part.function_call)

            if not function_calls:
                # No more function calls, return final response
                break

            # Process each function call
            function_responses = []
            for fc in function_calls:
                tool_name = fc.name
                tool_args = dict(fc.args) if fc.args else {}

                logger.info(
                    "executing_tool",
                    tool_name=tool_name,
                    args=tool_args,
                )

                if tool_name in tool_handlers:
                    try:
                        # Execute the tool handler
                        result = await self._execute_tool_handler(
                            tool_handlers[tool_name],
                            tool_args,
                        )
                        function_responses.append(
                            genai.protos.Part(
                                function_response=genai.protos.FunctionResponse(
                                    name=tool_name,
                                    response={"result": result},
                                )
                            )
                        )
                    except Exception as e:
                        logger.error(
                            "tool_execution_error",
                            tool_name=tool_name,
                            error=str(e),
                        )
                        function_responses.append(
                            genai.protos.Part(
                                function_response=genai.protos.FunctionResponse(
                                    name=tool_name,
                                    response={"error": str(e)},
                                )
                            )
                        )
                else:
                    logger.warning(
                        "unknown_tool_called",
                        tool_name=tool_name,
                    )
                    function_responses.append(
                        genai.protos.Part(
                            function_response=genai.protos.FunctionResponse(
                                name=tool_name,
                                response={"error": f"Unknown tool: {tool_name}"},
                            )
                        )
                    )

            # Send function responses back to model
            current_response = await asyncio.to_thread(
                chat.send_message,
                function_responses,
            )

        # Extract final text response
        if current_response.candidates:
            return current_response.text

        return ""

    async def _execute_tool_handler(
        self,
        handler: Callable,
        args: Dict[str, Any],
    ) -> Any:
        """Execute a tool handler, handling both sync and async functions."""
        if asyncio.iscoroutinefunction(handler):
            return await handler(**args)
        else:
            return await asyncio.to_thread(handler, **args)

    def parse_json_response(
        self,
        response_text: str,
        expected_type: type[T],
    ) -> T:
        """
        Parse a JSON response into a Pydantic model.
        
        Args:
            response_text: Raw JSON text from model
            expected_type: Pydantic model class to parse into
        
        Returns:
            Parsed and validated model instance
        """
        try:
            # Handle markdown code blocks
            text = response_text.strip()
            if text.startswith("```json"):
                text = text[7:]
            if text.startswith("```"):
                text = text[3:]
            if text.endswith("```"):
                text = text[:-3]

            data = json.loads(text.strip())
            return expected_type(**data)

        except json.JSONDecodeError as e:
            logger.error(
                "json_parse_error",
                error=str(e),
                response_preview=response_text[:500],
            )
            raise AgentReasoningError(
                agent_name="google_ai",
                message=f"Invalid JSON in response: {str(e)}",
                raw_response=response_text,
            )
        except Exception as e:
            logger.error(
                "response_validation_error",
                error=str(e),
                expected_type=expected_type.__name__,
            )
            raise


def create_function_declaration(
    name: str,
    description: str,
    parameters: Dict[str, Any],
    required: Optional[List[str]] = None,
) -> FunctionDeclaration:
    """
    Create a function declaration for tool calling.
    
    Args:
        name: Function name
        description: Function description
        parameters: Parameter schema (JSON Schema format)
        required: List of required parameter names
    
    Returns:
        FunctionDeclaration for use with Google AI tools
    """
    return FunctionDeclaration(
        name=name,
        description=description,
        parameters={
            "type": "object",
            "properties": parameters,
            "required": required or [],
        },
    )


def create_tool_from_functions(
    functions: List[FunctionDeclaration],
) -> Tool:
    """
    Create a Tool from a list of function declarations.
    
    Args:
        functions: List of FunctionDeclaration objects
    
    Returns:
        Tool object for use with generative models
    """
    return Tool(function_declarations=functions)
