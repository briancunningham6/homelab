"""Web search tool using Tavily API."""
import os
from typing import List
import httpx

from .base import BaseTool, ToolParameter, ToolResult


class WebSearchTool(BaseTool):
    """Search the web using Tavily API."""

    @property
    def name(self) -> str:
        return "web_search"

    @property
    def description(self) -> str:
        return "Search the web for current information, news, facts, and research. Use this when you need up-to-date information or need to verify facts."

    @property
    def parameters(self) -> List[ToolParameter]:
        return [
            ToolParameter(
                name="query",
                type="string",
                description="The search query to look up on the web",
                required=True,
            ),
            ToolParameter(
                name="max_results",
                type="number",
                description="Maximum number of results to return (default: 5)",
                required=False,
            ),
        ]

    async def execute(self, query: str, max_results: int = 5, **kwargs) -> ToolResult:
        """Execute web search using Tavily API.

        Args:
            query: Search query
            max_results: Max results to return

        Returns:
            ToolResult with search results
        """
        api_key = os.getenv("TAVILY_API_KEY")
        if not api_key:
            return ToolResult(
                success=False,
                error="Tavily API key not configured. Set TAVILY_API_KEY environment variable.",
            )

        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    "https://api.tavily.com/search",
                    json={
                        "api_key": api_key,
                        "query": query,
                        "max_results": max_results,
                        "include_answer": True,
                        "include_raw_content": False,
                    },
                    timeout=30.0,
                )

                if response.status_code != 200:
                    return ToolResult(
                        success=False,
                        error=f"Tavily API error: {response.status_code} - {response.text}",
                    )

                data = response.json()

                # Format results
                results = []
                for item in data.get("results", []):
                    results.append({
                        "title": item.get("title"),
                        "url": item.get("url"),
                        "content": item.get("content"),
                        "score": item.get("score"),
                    })

                return ToolResult(
                    success=True,
                    data={
                        "answer": data.get("answer"),  # AI-generated summary
                        "results": results,
                        "query": query,
                    },
                    metadata={
                        "search_engine": "tavily",
                        "result_count": len(results),
                    },
                )

        except Exception as e:
            return ToolResult(
                success=False,
                error=f"Web search failed: {str(e)}",
            )
