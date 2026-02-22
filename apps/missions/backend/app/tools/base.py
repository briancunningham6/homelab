"""Base tool class and registry for agent tools."""
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class ToolParameter(BaseModel):
    """Tool parameter definition."""
    name: str
    type: str  # string, number, boolean, array, object
    description: str
    required: bool = True
    enum: Optional[List[str]] = None


class ToolDefinition(BaseModel):
    """Tool definition for LLM API."""
    name: str
    description: str
    parameters: List[ToolParameter]


class ToolResult(BaseModel):
    """Result from tool execution."""
    success: bool
    data: Any = None
    error: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)


class BaseTool(ABC):
    """Base class for all agent tools."""

    @property
    @abstractmethod
    def name(self) -> str:
        """Unique tool identifier."""
        pass

    @property
    @abstractmethod
    def description(self) -> str:
        """Human-readable description of what the tool does."""
        pass

    @property
    @abstractmethod
    def parameters(self) -> List[ToolParameter]:
        """List of parameters this tool accepts."""
        pass

    @abstractmethod
    async def execute(self, **kwargs) -> ToolResult:
        """Execute the tool with given parameters.

        Args:
            **kwargs: Tool-specific parameters

        Returns:
            ToolResult with success status and data/error
        """
        pass

    def to_definition(self) -> ToolDefinition:
        """Convert to tool definition for LLM API."""
        return ToolDefinition(
            name=self.name,
            description=self.description,
            parameters=self.parameters,
        )

    def to_claude_tool(self) -> Dict[str, Any]:
        """Convert to Claude API tool format."""
        properties = {}
        required = []

        for param in self.parameters:
            properties[param.name] = {
                "type": param.type,
                "description": param.description,
            }
            if param.enum:
                properties[param.name]["enum"] = param.enum
            if param.required:
                required.append(param.name)

        return {
            "name": self.name,
            "description": self.description,
            "input_schema": {
                "type": "object",
                "properties": properties,
                "required": required,
            },
        }

    def to_openai_tool(self) -> Dict[str, Any]:
        """Convert to OpenAI API tool format."""
        properties = {}
        required = []

        for param in self.parameters:
            properties[param.name] = {
                "type": param.type,
                "description": param.description,
            }
            if param.enum:
                properties[param.name]["enum"] = param.enum
            if param.required:
                required.append(param.name)

        return {
            "type": "function",
            "function": {
                "name": self.name,
                "description": self.description,
                "parameters": {
                    "type": "object",
                    "properties": properties,
                    "required": required,
                },
            },
        }


class ToolRegistry:
    """Registry for managing available tools."""

    def __init__(self):
        self._tools: Dict[str, BaseTool] = {}

    def register(self, tool: BaseTool):
        """Register a tool."""
        self._tools[tool.name] = tool

    def get(self, name: str) -> Optional[BaseTool]:
        """Get tool by name."""
        return self._tools.get(name)

    def list_tools(self) -> List[BaseTool]:
        """List all registered tools."""
        return list(self._tools.values())

    def get_claude_tools(self) -> List[Dict[str, Any]]:
        """Get all tools in Claude API format."""
        return [tool.to_claude_tool() for tool in self._tools.values()]

    def get_openai_tools(self) -> List[Dict[str, Any]]:
        """Get all tools in OpenAI API format."""
        return [tool.to_openai_tool() for tool in self._tools.values()]

    async def execute(self, tool_name: str, **kwargs) -> ToolResult:
        """Execute a tool by name."""
        tool = self.get(tool_name)
        if not tool:
            return ToolResult(
                success=False,
                error=f"Tool '{tool_name}' not found",
            )

        try:
            return await tool.execute(**kwargs)
        except Exception as e:
            return ToolResult(
                success=False,
                error=f"Tool execution failed: {str(e)}",
            )
