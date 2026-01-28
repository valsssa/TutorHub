# User Roles, Separation, and Redirects (Developer Guide)

This document shows how the template distinguishes students, tutors, and admins at the database, backend, and frontend layers. Use it as a quick reference when extending the role system.

---

## 1. Database schema

`database/init.sql`
```sql
CREATE TABLE IF NOT EXISTS users (
    id SERIAL PRIMARY KEY,
    email VARCHAR(255) UNIQUE NOT NULL,
    hashed_password VARCHAR(255) NOT NULL,
    role VARCHAR(50) NOT NULL DEFAULT 'student',
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

`backend/models.py`
```python
class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    role = Column(String, default="student", nullable=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
```
- The **`role`** column holds the string discriminator (`student`, `tutor`, or `admin`).
- `is_active` toggles login eligibility; the backend requires both the correct role and `is_active=True`.

---

## 2. Backend: authentication and role guards

`backend/auth.py`
```python
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

async def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)) -> User:
    payload = jwt.decode(token, auth_settings.secret_key, algorithms=[auth_settings.algorithm])
    email: str = payload.get("sub")
    if email is None:
        raise credentials_exception
    user = db.query(User).filter(User.email == email).first()
    if user is None:
        raise credentials_exception
    return user

async def get_current_admin_user(current_user: User = Depends(get_current_user)) -> User:
    if current_user.role != "admin":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not enough permissions")
    return current_user
```

Key handlers in `backend/main.py`:
```python
@app.get("/admin/users")
async def get_all_users(current_user: User = Depends(get_current_admin_user), db: Session = Depends(get_db)):
    return db.query(User).all()

@app.put("/admin/users/{user_id}")
async def update_user(...):
    user = _validate_user_exists(user_id, db)
    if user_update.role is not None:
        _validate_self_modification(user, current_user, "role", user_update.role)
    if user_update.is_active is not None:
        _validate_self_modification(user, current_user, "is_active", user_update.is_active)
    ...
```

Self-protection logic:
```python
def _validate_self_modification(user: User, current_user: User, field: str, value) -> None:
    if user.id != current_user.id:
        return
    if field == "role" and value != "admin":
        raise HTTPException(status_code=400, detail="Cannot change your own role")
    if field == "is_active" and value is False:
        raise HTTPException(status_code=400, detail="Cannot deactivate yourself")
```
> **Bug note**: This check correctly compares booleans in code, but an earlier version cast `value` to string. If you still observe self-deactivation succeeding, ensure this helper uses the boolean directly and add regression tests.

---

## 3. API usage examples

### 3.1 Registration (creates `student` role)
```bash
curl -X POST http://localhost:8000/register \
  -H "Content-Type: application/json" \
  -d '{ "email": "alice@example.com", "password": "secret123" }'
# → { "id": 5, "email": "alice@example.com", "role": "student", ... }
```

### 3.2 Login and token usage
```bash
TOKEN=$(curl -X POST http://localhost:8000/token \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d 'username=alice@example.com&password=secret123' \
  | jq -r '.access_token')

curl http://localhost:8000/api/auth/me -H "Authorization: Bearer $TOKEN"
# → shows role `student`
```

### 3.3 Admin-only endpoint
```bash
curl http://localhost:8000/admin/users -H "Authorization: Bearer $TOKEN"
# user token → 403 {"detail":"Not enough permissions"}

curl http://localhost:8000/admin/users -H "Authorization: Bearer $ADMIN_TOKEN"
# admin token → list of users
```

### 3.4 Promote a user (admin token required)
```bash
curl -X PUT http://localhost:8000/admin/users/5 \
  -H "Authorization: Bearer $ADMIN_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{ "role": "admin" }'
# → updated user response
```

### 3.5 Attempted self-demotion/deactivation
```bash
curl -X PUT http://localhost:8000/admin/users/1 \
  -H "Authorization: Bearer $ADMIN_TOKEN" \
  -H "Content-Type: application/json" \
-d '{ "role": "tutor" }'
# → 400 {"detail": "Cannot change your own role"}
```

---

## 4. Frontend enforcement

`frontend/app/page.tsx`
```tsx
const token = Cookies.get('token')
if (!token) {
  router.replace('/login')
  return
}
const response = await axios.get(`${API_URL}/api/auth/me`, { headers: { Authorization: `Bearer ${token}` } })
setUser(response.data)
...
{user?.role === 'admin' && (
  <button onClick={() => router.push('/admin')}>Manage Users</button>
)}
```

`frontend/app/admin/page.tsx`
```tsx
const fetchUsers = useCallback(async () => {
  const token = Cookies.get('token')
  if (!token) {
    router.push('/login')
    return
  }

  try {
    const [usersResponse, meResponse] = await Promise.all([
      axios.get(`${API_URL}/admin/users`, { headers: { Authorization: `Bearer ${token}` } }),
      axios.get(`${API_URL}/api/auth/me`, { headers: { Authorization: `Bearer ${token}` } })
    ])
    setUsers(usersResponse.data)
    setCurrentUser(meResponse.data)
  } catch (error: any) {
    if (error.response?.status === 401) {
      Cookies.remove('token')
      router.push('/login')
    } else if (error.response?.status === 403) {
      showError('Access denied. Admin privileges required.')
      router.push('/unauthorized')
    } else {
      showError('Failed to fetch users')
    }
  }
})
```

`frontend/app/unauthorized/page.tsx`
- Renders an “Access Denied” page with links back to `/` and `/login`.

---

## 5. Typical flows

1. **Anonymous → Login**: Redirected to `/login`, submits credentials, backend issues token, frontend stores it in the `token` cookie, then redirects to `/`.
2. **User visits `/admin`**: Backend returns `403`; frontend clears the view and sends the user to `/unauthorized` with a toast.
3. **Admin edits another user**: Sends `PUT /admin/users/{id}` with changed fields. Backend checks role, uniqueness, and self-protection before committing.

---

## 6. Extending role logic

- Add new roles by updating the `users.role` constraints, `_validate_role`, and any switch statements in the frontend (e.g., role badges).
- Update `auth.get_current_admin_user` or add new dependencies (e.g., `get_current_manager_user`) to protect additional routes.
- Create database migrations if you introduce new tables referencing `users.id`; consider using Alembic for non-trivial changes.
- Add integration tests covering new role scenarios (`tests/test_auth.py` for API, `frontend/__tests__/` for UI behaviour).

---

## 7. Related references
- `docs/API.md` – Endpoint contract and status codes.
- `docs/KNOWN_ISSUES.md` – Current caveats (e.g., self-deactivation bug).
- `docs/TESTING.md` – Running backend and frontend tests.
- `docs/db_and_models_overview.md` – Broader DB/ORM explanation.
