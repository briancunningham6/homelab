"""Agent tools for Phase 3."""
from .base import BaseTool, ToolRegistry
from .web_search import WebSearchTool
from .document_parser import DocumentParserTool
from .vision import VisionTool

# Global tool registry
tool_registry = ToolRegistry()

# Register available tools
tool_registry.register(WebSearchTool())
tool_registry.register(DocumentParserTool())
tool_registry.register(VisionTool())

__all__ = [
    "BaseTool",
    "ToolRegistry",
    "WebSearchTool",
    "DocumentParserTool",
    "VisionTool",
    "tool_registry",
]
