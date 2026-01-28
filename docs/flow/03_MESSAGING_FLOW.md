# Messaging Flow

This document traces the complete messaging flow from sending messages to real-time delivery via WebSocket, including file attachments, read receipts, and thread management.

## Table of Contents
- [Send Message Flow](#send-message-flow)
- [Real-Time WebSocket Delivery](#real-time-websocket-delivery)
- [Message Thread Management](#message-thread-management)
- [File Attachment Flow](#file-attachment-flow)
- [Read Receipt Flow](#read-receipt-flow)
- [Message Search Flow](#message-search-flow)
- [Edit and Delete Flow](#edit-and-delete-flow)

---

## Send Message Flow

### 1. User Composes Message

**Frontend Component:** `frontend/app/messages/page.tsx` or `frontend/components/messaging/ChatWindow.tsx`

```typescript
const handleSend = async () => {
  const message = await messages.send(
    recipientId,
    messageText,
    bookingId  // optional
  );
};
```

### 2. API Client Sends Request

**File:** `frontend/lib/api.ts` (lines 869-887)

**Method:** `messages.send()`

**HTTP Request:**
- **Method:** `POST`
- **URL:** `/api/messages`
- **Headers:** `Authorization: Bearer <token>`, `Content-Type: application/json`
- **Body:**
```json
{
  "recipient_id": 50,
  "message": "Hi, I'd like to schedule a session for next week",
  "booking_id": 100
}
```

### 3. Backend Receives Request

**File:** `backend/modules/messages/api.py` (lines 118-191)

**Endpoint:** `POST /api/messages`

**Handler:** `send_message()`

**Request Schema:** `SendMessageRequest`
- `recipient_id`: int (required, > 0)
- `message`: str (1-2000 characters)
- `booking_id`: int | None (optional context)

**Dependencies:**
- `CurrentUser` - Authenticated user
- `MessageService` - Business logic

### 4. Service Layer Processing

**File:** `backend/modules/messages/service.py`

**Method:** `MessageService.send_message()`

**Validation Steps:**
1. **Self-messaging check** - Cannot send to self
2. **Recipient existence** - Verify recipient user exists and is active
3. **Content validation** - 1-2000 characters
4. **PII masking** - Mask email, phone, external links (pre-booking only)
5. **Booking context** - If booking_id provided, verify both users are participants

**PII Protection:**
```python
# If no active booking between users, mask PII
if not has_active_booking(sender_id, recipient_id):
    content = mask_pii(content)
    # "john@example.com" -> "j***@e***.com"
    # "555-1234" -> "***-****"
    # "http://malicious.com" -> "[external link removed]"
```

**Database Operations:**
```sql
-- Insert message
INSERT INTO messages (
  sender_id, recipient_id, booking_id,
  message, is_read, is_edited,
  created_at, updated_at
) VALUES (
  42, 50, 100,
  'Hi, I''d like to schedule a session', false, false,
  NOW(), NOW()
);
```

### 5. Real-Time WebSocket Notification

**File:** `backend/modules/messages/api.py` (lines 145-162)

**WebSocket Manager:** `backend/modules/messages/websocket.py`

**Notifications Sent:**

**To Recipient:**
```python
await manager.send_personal_message(
    {
        "type": "new_message",
        "message_id": 150,
        "sender_id": 42,
        "sender_email": "john@example.com",
        "sender_role": "student",
        "recipient_id": 50,
        "booking_id": 100,
        "message": "Hi, I'd like to schedule a session",
        "created_at": "2025-10-21T10:30:00Z",
        "is_read": false,
        "is_edited": false
    },
    recipient_id=50
)
```

**To Sender (Multi-Device Sync):**
```python
await manager.send_personal_message(
    {
        "type": "message_sent",
        "message_id": 150,
        "recipient_id": 50,
        "message": "Hi, I'd like to schedule a session",
        "created_at": "2025-10-21T10:30:00Z"
    },
    recipient_id=42
)
```

### 6. Response to Frontend

**Response Schema:** `MessageResponse`

```json
{
  "id": 150,
  "sender_id": 42,
  "sender_email": "john@example.com",
  "sender_first_name": "John",
  "sender_last_name": "Doe",
  "recipient_id": 50,
  "recipient_email": "jane@example.com",
  "recipient_first_name": "Jane",
  "recipient_last_name": "Smith",
  "message": "Hi, I'd like to schedule a session",
  "booking_id": 100,
  "is_read": false,
  "is_edited": false,
  "read_at": null,
  "edited_at": null,
  "created_at": "2025-10-21T10:30:00Z",
  "updated_at": "2025-10-21T10:30:00Z"
}
```

---

## Real-Time WebSocket Delivery

### 1. WebSocket Connection Establishment

**Frontend Hook:** `frontend/hooks/useWebSocket.ts`

```typescript
useEffect(() => {
  const token = Cookies.get('token');
  const ws = new WebSocket(`ws://localhost:8000/ws?token=${token}`);
  
  ws.onopen = () => {
    console.log('WebSocket connected');
  };
  
  ws.onmessage = (event) => {
    const data = JSON.parse(event.data);
    handleWebSocketMessage(data);
  };
  
  return () => ws.close();
}, []);
```

### 2. Backend WebSocket Manager

**File:** `backend/modules/messages/websocket.py`

**Class:** `ConnectionManager`

**Connection Handling:**
```python
@router.websocket("/ws")
async def websocket_endpoint(
    websocket: WebSocket,
    token: str = Query(...),
    db: Session = Depends(get_db)
):
    # Validate JWT token
    user = await authenticate_websocket(token, db)
    
    # Accept connection
    await manager.connect(websocket, user.id)
    
    try:
        while True:
            # Keep connection alive (ping/pong)
            data = await websocket.receive_text()
            
    except WebSocketDisconnect:
        manager.disconnect(user.id)
```

**Connection Storage:**
```python
class ConnectionManager:
    def __init__(self):
        # Map user_id -> list of WebSocket connections
        self.active_connections: dict[int, list[WebSocket]] = {}
    
    async def connect(self, websocket: WebSocket, user_id: int):
        await websocket.accept()
        if user_id not in self.active_connections:
            self.active_connections[user_id] = []
        self.active_connections[user_id].append(websocket)
    
    def disconnect(self, user_id: int, websocket: WebSocket):
        if user_id in self.active_connections:
            self.active_connections[user_id].remove(websocket)
```

### 3. Message Broadcasting

**Method:** `manager.send_personal_message()`

```python
async def send_personal_message(
    self,
    message: dict,
    user_id: int
):
    """Send message to all connections of a specific user."""
    if user_id in self.active_connections:
        # Send to all devices/tabs of this user
        for connection in self.active_connections[user_id]:
            try:
                await connection.send_json(message)
            except Exception as e:
                logger.error(f"Failed to send to connection: {e}")
                # Remove stale connection
                self.active_connections[user_id].remove(connection)
```

### 4. Frontend Message Handling

**Component:** `frontend/components/messaging/ChatWindow.tsx`

```typescript
const handleWebSocketMessage = (data: any) => {
  switch (data.type) {
    case 'new_message':
      // Add to message list if in current thread
      if (data.sender_id === otherUserId) {
        setMessages(prev => [...prev, data]);
        // Auto-mark as read if window is focused
        if (document.hasFocus()) {
          markRead(data.message_id);
        }
      }
      // Update unread count
      incrementUnreadCount();
      break;
      
    case 'message_sent':
      // Update sent message status (multi-device sync)
      setMessages(prev => 
        prev.map(m => 
          m.temp_id === data.temp_id 
            ? { ...m, id: data.message_id, status: 'sent' }
            : m
        )
      );
      break;
      
    case 'message_read':
      // Update read status in UI
      setMessages(prev =>
        prev.map(m =>
          m.id === data.message_id
            ? { ...m, is_read: true, read_at: data.read_at }
            : m
        )
      );
      break;
      
    case 'message_edited':
      // Update message content
      setMessages(prev =>
        prev.map(m =>
          m.id === data.message_id
            ? { ...m, message: data.new_content, is_edited: true }
            : m
        )
      );
      break;
      
    case 'message_deleted':
      // Remove from UI
      setMessages(prev => prev.filter(m => m.id !== data.message_id));
      break;
  }
};
```

---

## Message Thread Management

### 1. Load Thread List

**Frontend Component:** `frontend/app/messages/page.tsx`

```typescript
useEffect(() => {
  const loadThreads = async () => {
    const threads = await messages.listThreads(100);
    setThreads(threads);
  };
  loadThreads();
}, []);
```

### 2. API Client Request

**File:** `frontend/lib/api.ts` (lines 889-894)

**Method:** `messages.listThreads()`

**HTTP Request:**
- **Method:** `GET`
- **URL:** `/api/messages/threads?limit=100`
- **Headers:** `Authorization: Bearer <token>`

### 3. Backend Fetches Threads

**File:** `backend/modules/messages/api.py` (lines 193-244)

**Endpoint:** `GET /api/messages/threads`

**Handler:** `list_threads()`

**Query Parameters:**
- `limit`: int (1-200, default 100)

### 4. Service Layer Query

**File:** `backend/modules/messages/service.py`

**Method:** `MessageService.get_user_threads()`

**SQL Query:**
```sql
WITH latest_messages AS (
  SELECT DISTINCT ON (
    LEAST(sender_id, recipient_id), 
    GREATEST(sender_id, recipient_id),
    COALESCE(booking_id, -1)
  )
    id, sender_id, recipient_id, booking_id,
    message, created_at
  FROM messages
  WHERE sender_id = 42 OR recipient_id = 42
  ORDER BY 
    LEAST(sender_id, recipient_id), 
    GREATEST(sender_id, recipient_id),
    COALESCE(booking_id, -1),
    created_at DESC
)
SELECT 
  CASE 
    WHEN sender_id = 42 THEN recipient_id 
    ELSE sender_id 
  END as other_user_id,
  u.email as other_user_email,
  u.first_name as other_user_first_name,
  u.last_name as other_user_last_name,
  u.role as other_user_role,
  booking_id,
  message as last_message,
  created_at as last_message_time,
  sender_id as last_sender_id,
  (
    SELECT COUNT(*) 
    FROM messages 
    WHERE recipient_id = 42 
      AND sender_id = other_user_id
      AND is_read = false
  ) as unread_count
FROM latest_messages lm
JOIN users u ON u.id = other_user_id
ORDER BY created_at DESC
LIMIT 100;
```

**Response:**
```json
[
  {
    "other_user_id": 50,
    "other_user_email": "jane@example.com",
    "other_user_first_name": "Jane",
    "other_user_last_name": "Smith",
    "other_user_role": "tutor",
    "booking_id": 100,
    "last_message": "Sure, how about 2pm next Tuesday?",
    "last_message_time": "2025-10-21T10:45:00Z",
    "last_sender_id": 50,
    "unread_count": 2
  }
]
```

### 5. Load Conversation Messages

**Frontend:** User clicks on thread

```typescript
const loadConversation = async (otherUserId: number) => {
  const result = await messages.getThreadMessages(
    otherUserId,
    bookingId,
    page,
    pageSize
  );
  setMessages(result.messages);
};
```

### 6. Backend Returns Messages

**File:** `backend/modules/messages/api.py` (lines 246-296)

**Endpoint:** `GET /api/messages/threads/{other_user_id}`

**Query Parameters:**
- `booking_id`: int | None (filter by booking)
- `page`: int (default 1)
- `page_size`: int (1-100, default 50)

**SQL Query:**
```sql
SELECT 
  m.id, m.sender_id, m.recipient_id, m.message,
  m.booking_id, m.is_read, m.is_edited,
  m.read_at, m.edited_at, m.created_at,
  s.email as sender_email, s.first_name as sender_first_name,
  r.email as recipient_email, r.first_name as recipient_first_name
FROM messages m
JOIN users s ON s.id = m.sender_id
JOIN users r ON r.id = m.recipient_id
WHERE (
  (m.sender_id = 42 AND m.recipient_id = 50) OR
  (m.sender_id = 50 AND m.recipient_id = 42)
)
AND (m.booking_id = 100 OR 100 IS NULL)
AND m.deleted_at IS NULL
ORDER BY m.created_at ASC  -- Chronological order
LIMIT 50 OFFSET 0;
```

---

## File Attachment Flow

### 1. User Selects File

**Frontend Component:** Chat window with file upload

```typescript
const handleFileUpload = async (file: File) => {
  const formData = new FormData();
  formData.append('recipient_id', recipientId);
  formData.append('message', messageText);
  formData.append('file', file);
  
  const message = await api.post('/api/messages/with-attachment', formData, {
    headers: { 'Content-Type': 'multipart/form-data' }
  });
};
```

### 2. Backend Receives Upload

**File:** `backend/modules/messages/api.py` (lines 453-557)

**Endpoint:** `POST /api/messages/with-attachment`

**Handler:** `send_message_with_attachment()`

**Form Parameters:**
- `recipient_id`: int (Form field)
- `message`: str (Form field)
- `booking_id`: int | None (Form field)
- `file`: UploadFile (File upload)

### 3. File Validation

**File:** `backend/core/message_storage.py`

**Function:** `store_message_attachment()`

**Validation Rules:**
- **Size limits:**
  - Images: 5 MB max
  - Documents: 10 MB max
- **Allowed types:**
  - Images: JPEG, PNG, GIF, WebP
  - Documents: PDF, DOCX, TXT, CSV
- **Filename sanitization** - Remove special characters
- **Virus scan placeholder** - Status set to "pending"

### 4. Storage Processing

**S3/MinIO Upload:**
```python
# Generate unique file key
file_key = f"message_attachments/{user_id}/{message_id}/{uuid4()}_{filename}"

# Upload to private bucket
s3_client.upload_fileobj(
    file,
    bucket="private-attachments",
    key=file_key,
    ExtraArgs={
        'ContentType': mime_type,
        'ServerSideEncryption': 'AES256'
    }
)

# Return metadata
return {
    "file_key": file_key,
    "original_filename": filename,
    "mime_type": mime_type,
    "file_size": file.size
}
```

### 5. Database Record Creation

**SQL:**
```sql
INSERT INTO message_attachments (
  message_id, uploaded_by, file_key,
  original_filename, mime_type, file_size,
  scan_result, is_public, created_at, updated_at
) VALUES (
  150, 42, 'message_attachments/42/150/uuid_document.pdf',
  'document.pdf', 'application/pdf', 524288,
  'pending', false, NOW(), NOW()
);
```

### 6. Download File

**Frontend:** User clicks download link

```typescript
const handleDownload = async (attachmentId: number) => {
  const response = await api.get(`/api/messages/attachments/${attachmentId}/download`);
  
  // Open presigned URL
  window.open(response.data.download_url, '_blank');
};
```

### 7. Backend Generates Presigned URL

**File:** `backend/modules/messages/api.py` (lines 559-640)

**Endpoint:** `GET /api/messages/attachments/{attachment_id}/download`

**Handler:** `get_attachment_download_url()`

**Access Control:**
1. **Verify attachment exists** - Query database
2. **Check authorization** - User must be sender or recipient
3. **Scan status check** - Block if virus detected
4. **Generate URL** - Create presigned S3 URL (1 hour expiry)

**Presigned URL Generation:**
```python
download_url = s3_client.generate_presigned_url(
    'get_object',
    Params={
        'Bucket': 'private-attachments',
        'Key': attachment.file_key
    },
    ExpiresIn=3600  # 1 hour
)
```

**Response:**
```json
{
  "download_url": "https://s3.amazonaws.com/private-attachments/...",
  "filename": "document.pdf",
  "size": 524288,
  "mime_type": "application/pdf",
  "expires_in_seconds": 3600
}
```

---

## Read Receipt Flow

### 1. Mark Message as Read

**Frontend:** Message visible in viewport

```typescript
useEffect(() => {
  if (isVisible && !message.is_read) {
    messages.markRead(message.id);
  }
}, [isVisible, message]);
```

### 2. API Client Request

**File:** `frontend/lib/api.ts` (lines 941-944)

**Method:** `messages.markRead()`

**HTTP Request:**
- **Method:** `PATCH`
- **URL:** `/api/messages/150/read`
- **Headers:** `Authorization: Bearer <token>`

### 3. Backend Updates Status

**File:** `backend/modules/messages/api.py` (lines 356-402)

**Endpoint:** `PATCH /api/messages/{message_id}/read`

**Handler:** `mark_read()`

**Authorization:** Must be recipient of the message

**Process:**
1. **Load message** - Verify exists
2. **Check authorization** - Must be recipient
3. **Update status** - Set is_read=true, read_at=NOW()
4. **Send WebSocket notification** - Notify sender

**Database Operation:**
```sql
UPDATE messages 
SET is_read = true,
    read_at = NOW()
WHERE id = 150 
  AND recipient_id = 42
  AND is_read = false;
```

### 4. Real-Time Read Receipt

**WebSocket to Sender:**
```python
await manager.send_personal_message(
    {
        "type": "message_read",
        "message_id": 150,
        "reader_id": 42,
        "read_at": "2025-10-21T10:50:00Z"
    },
    message.sender_id
)
```

### 5. Mark Thread as Read

**Frontend:** User opens conversation

```typescript
useEffect(() => {
  messages.markThreadRead(otherUserId, bookingId);
}, [otherUserId]);
```

**Endpoint:** `PATCH /api/messages/threads/{other_user_id}/read-all`

**SQL:**
```sql
UPDATE messages 
SET is_read = true,
    read_at = NOW()
WHERE recipient_id = 42 
  AND sender_id = 50
  AND (booking_id = 100 OR 100 IS NULL)
  AND is_read = false;
```

---

## Message Search Flow

### 1. User Enters Search Query

**Frontend Component:** Message search input

```typescript
const handleSearch = async (query: string) => {
  const results = await messages.searchMessages(query, 1, 20);
  setSearchResults(results.messages);
};
```

### 2. API Client Request

**File:** `frontend/lib/api.ts` (lines 926-939)

**Method:** `messages.searchMessages()`

**HTTP Request:**
- **Method:** `GET`
- **URL:** `/api/messages/search?q=calculus&page=1&page_size=20`

### 3. Backend Search

**File:** `backend/modules/messages/api.py` (lines 298-349)

**Endpoint:** `GET /api/messages/search`

**Handler:** `search_messages()`

**Query Parameters:**
- `q`: str (min 2 characters)
- `page`: int (default 1)
- `page_size`: int (1-50, default 20)

### 4. Service Layer Query

**File:** `backend/modules/messages/service.py`

**Method:** `MessageService.search_messages()`

**SQL Query:**
```sql
SELECT 
  m.id, m.sender_id, m.recipient_id, m.message,
  m.booking_id, m.is_read, m.created_at,
  s.email as sender_email, s.first_name as sender_first_name,
  r.email as recipient_email, r.first_name as recipient_first_name,
  ts_rank(
    to_tsvector('english', m.message),
    plainto_tsquery('english', 'calculus')
  ) as rank
FROM messages m
JOIN users s ON s.id = m.sender_id
JOIN users r ON r.id = m.recipient_id
WHERE (m.sender_id = 42 OR m.recipient_id = 42)
  AND m.deleted_at IS NULL
  AND to_tsvector('english', m.message) @@ plainto_tsquery('english', 'calculus')
ORDER BY rank DESC, m.created_at DESC
LIMIT 20 OFFSET 0;
```

**Response:**
```json
{
  "messages": [...],
  "total": 15,
  "page": 1,
  "page_size": 20,
  "total_pages": 1
}
```

---

## Edit and Delete Flow

### 1. Edit Message

**Frontend:** User clicks edit (within 15 minutes)

```typescript
const handleEdit = async (messageId: number, newText: string) => {
  const updated = await messages.editMessage(messageId, newText);
};
```

### 2. Backend Validation

**File:** `backend/modules/messages/api.py` (lines 729-780)

**Endpoint:** `PATCH /api/messages/{message_id}`

**Handler:** `edit_message()`

**Validation:**
1. **Ownership** - Must be sender
2. **Time window** - Within 15 minutes of sending
3. **Content validation** - 1-2000 characters
4. **PII masking** - Applied to new content

**Database Operation:**
```sql
UPDATE messages 
SET message = 'Updated text',
    is_edited = true,
    edited_at = NOW(),
    updated_at = NOW()
WHERE id = 150 
  AND sender_id = 42
  AND created_at > NOW() - INTERVAL '15 minutes';
```

### 3. Delete Message

**Frontend:** User clicks delete

```typescript
const handleDelete = async (messageId: number) => {
  await messages.deleteMessage(messageId);
};
```

### 4. Backend Soft Delete

**File:** `backend/modules/messages/api.py` (lines 782-825)

**Endpoint:** `DELETE /api/messages/{message_id}`

**Handler:** `delete_message()`

**Process:**
1. **Verify ownership** - Must be sender
2. **Soft delete** - Set deleted_at, deleted_by
3. **Keep record** - For audit trail
4. **Hide from both users** - UI filters deleted_at != NULL

**Database Operation:**
```sql
UPDATE messages 
SET deleted_at = NOW(),
    deleted_by = 42,
    updated_at = NOW()
WHERE id = 150 
  AND sender_id = 42;
```

---

## Related Files

### Frontend
- `frontend/app/messages/page.tsx` - Main messaging page
- `frontend/components/messaging/ChatWindow.tsx` - Chat interface
- `frontend/components/messaging/MessageBubble.tsx` - Message display
- `frontend/components/messaging/ThreadList.tsx` - Thread list
- `frontend/hooks/useWebSocket.ts` - WebSocket connection
- `frontend/hooks/useMessaging.ts` - Messaging logic
- `frontend/lib/api.ts` - API client methods

### Backend
- `backend/modules/messages/api.py` - Message endpoints
- `backend/modules/messages/service.py` - Business logic
- `backend/modules/messages/websocket.py` - WebSocket manager
- `backend/core/message_storage.py` - File attachment storage
- `backend/models.py` - Message and MessageAttachment models

### Database
- Tables: `messages`, `message_attachments`
- Indexes: Full-text search on message content
