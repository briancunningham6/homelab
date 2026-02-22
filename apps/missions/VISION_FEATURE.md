# Vision Feature: Image Attachments in Chat

## Overview

Allow users to attach images to chat messages. AI agents analyze images using vision models (Claude Vision, GPT-4V) to extract information like text, numbers, objects, and context.

**Use Case Example:**
- Attach odometer photo → AI reads "145,287 km" and date
- Attach insurance document → AI extracts policy number, expiry date
- Attach receipt → AI reads total amount, vendor, date
- Attach diagram → AI describes the technical setup

---

## Implementation Steps

### Phase 1: Database & Backend

#### 1. Database Migration

Create Alembic migration for `message_attachments` table:

```bash
cd apps/missions/backend
alembic revision -m "add message attachments for vision"
```

Migration content:
```python
def upgrade():
    op.create_table(
        'message_attachments',
        sa.Column('id', UUID(as_uuid=True), primary_key=True),
        sa.Column('message_id', UUID(as_uuid=True), ForeignKey('messages.id', ondelete='CASCADE')),
        sa.Column('filename', sa.String(255), nullable=False),
        sa.Column('original_name', sa.String(255), nullable=False),
        sa.Column('mime_type', sa.String(100)),
        sa.Column('size_bytes', sa.Integer()),
        sa.Column('storage_path', sa.Text(), nullable=False),
        sa.Column('description', sa.Text()),
        sa.Column('extracted_text', sa.Text()),
        sa.Column('vision_model', sa.String(100)),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=func.now()),
    )
```

#### 2. Update Chat Service for Vision

File: `backend/app/services/chat.py`

Add vision support to both Claude and OpenAI:

**Claude Vision (supports images natively):**
```python
async def _stream_claude_with_images(
    self,
    provider: LLMProvider,
    system_prompt: str,
    messages: list[Message],
) -> AsyncGenerator[dict, None]:
    """Stream Claude response with image support."""

    # Convert messages with attachments
    claude_messages = []
    for msg in messages:
        if msg.role in ["user", "assistant"]:
            content_parts = []

            # Add text content
            if msg.content:
                content_parts.append({
                    "type": "text",
                    "text": msg.content
                })

            # Add image attachments
            for attachment in msg.attachments:
                if attachment.mime_type and attachment.mime_type.startswith('image/'):
                    # Read image file
                    image_path = Path(FILES_DIR) / attachment.storage_path
                    with open(image_path, 'rb') as f:
                        image_data = base64.b64encode(f.read()).decode()

                    content_parts.append({
                        "type": "image",
                        "source": {
                            "type": "base64",
                            "media_type": attachment.mime_type,
                            "data": image_data
                        }
                    })

            claude_messages.append({
                "role": msg.role,
                "content": content_parts if len(content_parts) > 1 else content_parts[0]
            })
```

**OpenAI Vision (GPT-4V):**
```python
async def _stream_openai_with_images(
    self,
    provider: LLMProvider,
    system_prompt: str,
    messages: list[Message],
) -> AsyncGenerator[dict, None]:
    """Stream OpenAI response with image support."""

    openai_messages = [{"role": "system", "content": system_prompt}]

    for msg in messages:
        if msg.role in ["user", "assistant"]:
            content_parts = []

            # Add text
            if msg.content:
                content_parts.append({
                    "type": "text",
                    "text": msg.content
                })

            # Add images
            for attachment in msg.attachments:
                if attachment.mime_type and attachment.mime_type.startswith('image/'):
                    image_path = Path(FILES_DIR) / attachment.storage_path
                    with open(image_path, 'rb') as f:
                        image_data = base64.b64encode(f.read()).decode()

                    content_parts.append({
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:{attachment.mime_type};base64,{image_data}"
                        }
                    })

            openai_messages.append({
                "role": msg.role,
                "content": content_parts
            })

    # Use GPT-4V model
    model = "gpt-4-vision-preview"  # or provider.default_model if vision-capable
```

#### 3. WebSocket Message with Attachment Upload

Update `app/api/chat.py` to handle file uploads via WebSocket:

```python
@router.websocket("/api/missions/{mission_id}/chat")
async def chat_websocket(websocket: WebSocket, mission_id: UUID):
    await websocket.accept()

    while True:
        data = await websocket.receive_text()
        message = json.loads(data)

        if message.get("type") == "message":
            # Handle text message
            user_content = message.get("content", "")

            # Check for attachment data (base64 encoded)
            attachments = message.get("attachments", [])

            # Save user message with attachments
            user_msg = Message(
                mission_id=mission_id,
                role="user",
                content=user_content,
            )
            db.add(user_msg)
            db.flush()  # Get message ID

            # Save attachments
            for att in attachments:
                # Save file
                file_ext = Path(att['filename']).suffix
                unique_filename = f"{uuid4()}{file_ext}"
                storage_path = f"{mission_id}/{unique_filename}"

                # Decode base64 and save
                file_data = base64.b64decode(att['data'])
                file_path = Path(FILES_DIR) / storage_path
                file_path.parent.mkdir(parents=True, exist_ok=True)
                file_path.write_bytes(file_data)

                # Create attachment record
                attachment = MessageAttachment(
                    message_id=user_msg.id,
                    filename=unique_filename,
                    original_name=att['filename'],
                    mime_type=att.get('mime_type'),
                    size_bytes=len(file_data),
                    storage_path=storage_path,
                )
                db.add(attachment)

            db.commit()
```

### Phase 2: Frontend

#### 1. Update Chat Component

File: `frontend/src/components/Chat.tsx`

Add file input and attachment preview:

```tsx
const [attachments, setAttachments] = useState<File[]>([])

const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
  const files = Array.from(e.target.files || [])
  setAttachments(prev => [...prev, ...files])
}

const removeAttachment = (index: number) => {
  setAttachments(prev => prev.filter((_, i) => i !== index))
}

const handleSend = async () => {
  if (!input.trim() && attachments.length === 0) return

  // Convert attachments to base64
  const attachmentData = await Promise.all(
    attachments.map(async (file) => {
      const data = await fileToBase64(file)
      return {
        filename: file.name,
        mime_type: file.type,
        data: data.split(',')[1]  // Remove data:image/... prefix
      }
    })
  )

  // Send via WebSocket
  wsRef.current?.send(JSON.stringify({
    type: 'message',
    content: input,
    attachments: attachmentData
  }))

  setAttachments([])
  setInput('')
}

// UI for attachment preview
{attachments.length > 0 && (
  <div className="attachment-preview">
    {attachments.map((file, i) => (
      <div key={i} className="attachment-item">
        {file.type.startsWith('image/') && (
          <img src={URL.createObjectURL(file)} alt={file.name} />
        )}
        <span>{file.name}</span>
        <button onClick={() => removeAttachment(i)}>×</button>
      </div>
    ))}
  </div>
)}

// File input button
<input
  type="file"
  ref={fileInputRef}
  onChange={handleFileSelect}
  accept="image/*"
  multiple
  style={{ display: 'none' }}
/>
<button onClick={() => fileInputRef.current?.click()}>
  📎 Attach
</button>
```

#### 2. Display Attachments in Messages

```tsx
{messages.map((msg) => (
  <div key={msg.id} className={`message message-${msg.role}`}>
    {msg.attachments?.map(att => (
      <div key={att.id} className="message-attachment">
        <img src={`/api/attachments/${att.id}`} alt={att.original_name} />
        {att.description && (
          <p className="ai-description">{att.description}</p>
        )}
      </div>
    ))}
    <div className="message-content">{msg.content}</div>
  </div>
))}
```

### Phase 3: Vision Analysis Service

Create dedicated service for image analysis:

File: `backend/app/services/vision.py`

```python
class VisionService:
    """Analyze images using vision models."""

    async def analyze_image(
        self,
        image_path: Path,
        prompt: str,
        provider: LLMProvider,
    ) -> dict:
        """Analyze image and return description + extracted text."""

        # Read image
        with open(image_path, 'rb') as f:
            image_data = base64.b64encode(f.read()).decode()

        if provider.name == 'claude':
            return await self._analyze_with_claude(image_data, prompt, provider)
        elif provider.name == 'openai':
            return await self._analyze_with_openai(image_data, prompt, provider)

    async def _analyze_with_claude(self, image_data: str, prompt: str, provider):
        """Use Claude Vision."""
        client = anthropic.AsyncAnthropic(
            api_key=decrypt_api_key(provider.api_key_encrypted)
        )

        response = await client.messages.create(
            model="claude-3-5-sonnet-20241022",  # Vision-capable
            max_tokens=1024,
            messages=[{
                "role": "user",
                "content": [
                    {
                        "type": "image",
                        "source": {
                            "type": "base64",
                            "media_type": "image/jpeg",
                            "data": image_data
                        }
                    },
                    {
                        "type": "text",
                        "text": prompt or "Describe this image in detail. Extract any text, numbers, or key information."
                    }
                ]
            }]
        )

        return {
            "description": response.content[0].text,
            "model": response.model
        }
```

---

## Example User Flow

1. **User opens mission** "Car Manager"
2. **User clicks** 📎 Attach in chat
3. **User selects** odometer photo (odometer_2024_02_22.jpg)
4. **User types:** "Here's today's odometer reading"
5. **User clicks Send**
6. **Backend:**
   - Saves image to `data/files/{mission-uuid}/xyz-789.jpg`
   - Creates `MessageAttachment` record
   - Creates `Message` record with user role
   - Passes to Claude Vision with image + text
7. **Claude sees:**
   - Image of odometer showing 145,287 km
   - User message: "Here's today's odometer reading"
8. **Claude responds:** "I can see the odometer reads 145,287 km as of February 22, 2024. I've recorded this in the mission context. Would you like me to calculate kilometers driven since the last reading?"
9. **Frontend displays:**
   - User message with attached odometer photo preview
   - AI response with extracted information

---

## Configuration

### Enable Vision Models

In Settings → LLM Providers:
- **Claude:** Use `claude-3-5-sonnet-20241022` or newer (supports vision)
- **OpenAI:** Use `gpt-4-vision-preview` or `gpt-4-turbo` (supports vision)

### File Size Limits

```python
# backend/app/config.py
MAX_ATTACHMENT_SIZE = 10 * 1024 * 1024  # 10MB
ALLOWED_IMAGE_TYPES = ['image/jpeg', 'image/png', 'image/webp', 'image/gif']
```

---

## Benefits

1. **Richer Context:** Images provide visual information that's hard to describe in text
2. **OCR Built-in:** Extract text from documents, receipts, signs
3. **Data Extraction:** Read numbers, dates, measurements from photos
4. **Memory Aid:** Visual timeline of mission progress
5. **Verification:** Photos as evidence/proof of work completed

---

## Next Steps

This feature sets up Phase 3 groundwork (agent tools). Once vision is working, you can add:
- **Document parsing tool** - Extract structured data from forms
- **Receipt scanner** - Parse expense details
- **Diagram analyzer** - Understand technical drawings
- **Progress tracking** - Compare before/after photos

---

## Migration Command

```bash
cd apps/missions/backend
alembic revision --autogenerate -m "add message attachments for vision"
alembic upgrade head
```

---

## Testing

1. Create test mission
2. Attach odometer photo in chat
3. Ask: "What's the mileage shown?"
4. Verify AI reads the number correctly
5. Check attachment is saved in `data/files/{mission-id}/`
6. Verify attachment appears in message history on reload
