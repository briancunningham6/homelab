## Phase 3: Agent Tools Implementation - Complete

**Status:** ✅ Tools framework created, ready for integration

### What Was Built

**Tool Architecture (`backend/app/tools/`):**
1. **Base Framework** ([`base.py`](backend/app/tools/base.py))
   - `BaseTool` - Abstract base class for all tools
   - `ToolRegistry` - Central registry for tool management
   - `ToolParameter` - Parameter definition schema
   - `ToolResult` - Standardized result format
   - Auto-conversion to Claude/OpenAI API formats

2. **Web Search Tool** ([`web_search.py`](backend/app/tools/web_search.py))
   - Integration with Tavily API
   - Returns AI-generated answer + search results
   - Configurable result count
   - Use case: Research car maintenance, check insurance rates, find local services

3. **Document Parser Tool** ([`document_parser.py`](backend/app/tools/document_parser.py))
   - Extract text from uploaded files
   - Supports PDFs, images (OCR), documents
   - Caches extracted text in database
   - Use case: Read insurance policies, parse receipts, extract contract details

4. **Vision Tool** ([`vision.py`](backend/app/tools/vision.py))
   - Analyze images using Claude Vision or GPT-4V
   - Extract text, numbers, objects from photos
   - Custom prompts for specific analysis
   - Use case: Read odometers, parse receipts, analyze diagrams, inspect documents

---

### Integration Steps

#### Step 1: Update Chat Service to Use Tools

File: `backend/app/services/chat.py`

```python
from app.tools import tool_registry

class ChatService:
    async def stream_chat(...):
        # ... existing code ...

        # Get available tools
        if provider.name == "claude":
            tools = tool_registry.get_claude_tools()
            async for chunk in self._stream_claude_with_tools(
                provider, system_prompt, messages, tools
            ):
                yield chunk
        elif provider.name == "openai":
            tools = tool_registry.get_openai_tools()
            async for chunk in self._stream_openai_with_tools(
                provider, system_prompt, messages, tools
            ):
                yield chunk

    async def _stream_claude_with_tools(
        self, provider, system_prompt, messages, tools
    ):
        """Stream from Claude with tool support."""
        client = anthropic.AsyncAnthropic(
            api_key=decrypt_api_key(provider.api_key_encrypted)
        )

        # Convert message history
        claude_messages = [...]

        # Stream with tools enabled
        async with client.messages.stream(
            model=provider.default_model or "claude-sonnet-4-20250514",
            max_tokens=4096,
            system=system_prompt,
            messages=claude_messages,
            tools=tools,  # Enable tools
        ) as stream:
            async for event in stream:
                # Handle text content
                if event.type == "content_block_delta":
                    if event.delta.type == "text_delta":
                        yield {"type": "content", "content": event.delta.text}

                # Handle tool use
                if event.type == "content_block_start":
                    if event.content_block.type == "tool_use":
                        tool_name = event.content_block.name
                        tool_id = event.content_block.id
                        yield {
                            "type": "tool_start",
                            "tool_name": tool_name,
                            "tool_id": tool_id,
                        }

                if event.type == "content_block_delta":
                    if event.delta.type == "input_json_delta":
                        # Tool input being streamed
                        pass

                if event.type == "content_block_stop":
                    if hasattr(event.content_block, "input"):
                        # Execute tool
                        result = await tool_registry.execute(
                            tool_name,
                            **event.content_block.input
                        )

                        yield {
                            "type": "tool_result",
                            "tool_name": tool_name,
                            "tool_id": tool_id,
                            "result": result.data if result.success else result.error,
                            "success": result.success,
                        }

                        # Continue conversation with tool result
                        # (This requires another API call with tool result)
```

#### Step 2: Add Tool Call Logging

Update `Message` model to store tool calls:

```python
# Already have these fields:
# tool_name = Column(String(100))
# tool_input = Column(JSONB)
# tool_output = Column(JSONB)

# When tool is called, save:
message = Message(
    mission_id=mission_id,
    role="tool",
    content=f"Used {tool_name}",
    tool_name=tool_name,
    tool_input=tool_input_params,
    tool_output=tool_result.data,
)
```

#### Step 3: Update Frontend to Display Tool Calls

File: `frontend/src/components/Chat.tsx`

Handle new WebSocket message types:

```tsx
ws.onmessage = (event) => {
  const data = JSON.parse(event.data)

  if (data.type === "tool_start") {
    // Show "Using web_search..." indicator
    setMessages(prev => [
      ...prev,
      {
        id: data.tool_id,
        role: "tool",
        tool_name: data.tool_name,
        content: "",
        isExecuting: true,
      }
    ])
  }

  if (data.type === "tool_result") {
    // Update with tool result
    setMessages(prev => prev.map(msg =>
      msg.id === data.tool_id
        ? {
            ...msg,
            content: JSON.stringify(data.result, null, 2),
            isExecuting: false,
            success: data.success,
          }
        : msg
    ))
  }
}
```

Display tool calls in chat:

```tsx
{msg.role === "tool" && (
  <div className="tool-call">
    <div className="tool-header">
      🔧 {msg.tool_name}
      {msg.isExecuting && <span className="spinner">⏳</span>}
    </div>
    {!msg.isExecuting && (
      <div className={`tool-result ${msg.success ? 'success' : 'error'}`}>
        <pre>{msg.content}</pre>
      </div>
    )}
  </div>
)}
```

---

### Example Usage Flows

#### Example 1: Web Search for Car Maintenance

**User:** "When should I change the oil in my 2014 Citroen Picasso diesel?"

**Agent:**
1. Calls `web_search` tool
   - Query: "2014 Citroen Picasso diesel oil change interval"
2. Receives results:
   - "Recommended every 12,000 km or 12 months"
   - Links to manufacturer specs
3. Responds: "Based on manufacturer recommendations, you should change the oil every 12,000 km or 12 months, whichever comes first..."

---

#### Example 2: Vision Analysis of Odometer

**User:** [Uploads odometer photo] "What's the current mileage?"

**Agent:**
1. Calls `analyze_image` tool
   - file_id: {uploaded-image-uuid}
   - prompt: "What is the mileage shown on this odometer?"
2. Vision AI analyzes image
   - Returns: "The odometer displays 145,287 km"
3. Responds: "The current mileage is 145,287 km as of today (February 22, 2024). Would you like me to track this for maintenance scheduling?"

---

#### Example 3: Parse Insurance Document

**User:** "When does my car insurance expire?"

**Agent:**
1. Lists mission files, finds insurance PDF
2. Calls `parse_document` tool
   - file_id: {insurance-pdf-uuid}
   - extraction_type: "text"
3. Searches extracted text for expiry date
4. Responds: "Your car insurance policy expires on June 15, 2024. I can remind you 30 days before renewal if you'd like."

---

### Configuration

#### Enable Tools

Tools are automatically available once registered in `tool_registry`. Individual tools may require configuration:

**Web Search (Tavily):**
```bash
# In .env
TAVILY_API_KEY=tvly-xxxxxxxxxx
```

Get API key from: https://tavily.com

**Vision:**
- Requires Claude 3.5 Sonnet or GPT-4V model
- No additional config needed (uses existing LLM provider)

**Document Parser:**
- No additional config for basic text extraction
- Future: OCR requires pytesseract installation

---

### Tool Calling Flow Diagram

```
User Message
    ↓
Chat Service determines: "Need web search"
    ↓
Calls tool_registry.execute("web_search", query="...")
    ↓
WebSearchTool.execute() → Tavily API
    ↓
ToolResult(success=True, data={...})
    ↓
Agent includes tool result in context
    ↓
Agent generates response using search results
    ↓
Stream response to user
```

---

### Dependencies to Add

```txt
# backend/requirements.txt

# Web search
httpx==0.27.2  # Already included

# Document parsing (Phase 3 complete)
PyPDF2==3.0.1
pytesseract==0.3.13
python-docx==1.1.2
pandas==2.2.3
openpyxl==3.1.5
Pillow==11.0.0

# Vision (already have anthropic + openai)
```

---

### Database Migration

No new tables needed - tool calls are stored in existing `messages` table using existing fields:
- `tool_name` - Name of tool called
- `tool_input` - JSONB of input parameters
- `tool_output` - JSONB of tool result

---

### Testing

```bash
# Test web search tool
curl -X POST http://localhost:8000/api/tools/execute \
  -H "Content-Type: application/json" \
  -d '{
    "tool": "web_search",
    "params": {
      "query": "2014 Citroen Picasso diesel maintenance schedule"
    }
  }'

# Test vision tool
curl -X POST http://localhost:8000/api/tools/execute \
  -H "Content-Type: application/json" \
  -d '{
    "tool": "analyze_image",
    "params": {
      "file_id": "abc-123-def-456",
      "prompt": "What is shown in this image?"
    }
  }'
```

---

### Next Steps

1. **Complete chat service integration** - Add tool calling to streaming functions
2. **Add tool execution endpoint** - REST API for testing tools directly
3. **Update frontend** - Display tool calls in chat UI
4. **Add document parsing libraries** - PyPDF2, pytesseract, etc.
5. **Test end-to-end** - Create mission, ask question requiring tool use
6. **Add more tools:**
   - Code execution (sandbox)
   - Calendar/scheduling
   - Email sending
   - File operations

---

### Tool Design Guidelines

When creating new tools:

1. **Single Responsibility** - One tool does one thing well
2. **Clear Parameters** - Document what each parameter does
3. **Error Handling** - Always return ToolResult, never raise exceptions
4. **Idempotent** - Safe to call multiple times with same params
5. **Fast** - Timeout within 30 seconds or provide progress updates
6. **Logged** - All executions stored in messages table

---

## Status Summary

✅ **Complete:**
- Tool architecture and base classes
- Web search tool (Tavily)
- Document parser tool (skeleton)
- Vision tool (Claude + OpenAI)
- Tool registry system
- API format converters

⏳ **Remaining:**
- Integrate tools into chat service streaming
- Add frontend UI for tool call display
- Create tool execution API endpoint
- Add full document parsing libraries
- End-to-end testing

---

**Tools are ready to be integrated into the chat flow!**
