# ADR-008: MinIO for Object Storage

## Status

Accepted

## Date

2026-01-29

## Context

EduStream requires object storage for:
- Tutor profile photos
- Certification documents (PDF, images)
- Education credential documents
- Future: message attachments, session recordings

Key requirements:
- **S3-compatible API**: Industry standard for portability
- **Self-hosted option**: Privacy and cost control for MVP
- **Cloud migration path**: Easy transition to AWS S3 when scaling
- **Direct browser access**: Public URLs for profile images
- **Size limits**: Reasonable limits to prevent abuse (5MB per file)

## Decision

We will use **MinIO** as the object storage solution with S3-compatible API.

Configuration:
```python
MINIO_ENDPOINT = "http://minio:9000"
MINIO_PUBLIC_ENDPOINT = "https://minio.valsa.solutions"
MINIO_BUCKET = "tutor-assets"
```

Storage organization:
```
tutor-assets/
├── tutor_profiles/
│   └── {user_id}/
│       ├── photo/
│       │   └── {random_hex}.jpg
│       ├── certifications/
│       │   └── {random_hex}.pdf
│       └── education/
│           └── {random_hex}.pdf
```

Access patterns:
- **Public read**: Profile photos accessible via public URLs
- **Authenticated write**: Uploads require API authentication
- **Bucket policy**: GetObject allowed for all principals

Security measures:
- Filenames sanitized and randomized (16-byte hex)
- Content-Type validation (JPEG, PNG, PDF only)
- File size limits enforced (5MB max)
- Image processing: resize, normalize format
- No directory traversal via path construction

## Consequences

### Positive

- **S3 compatibility**: Uses boto3, same code works with AWS S3
- **Self-hosted**: Full control, no cloud vendor dependency
- **Cost effective**: Free for MVP, pay only for infrastructure
- **Easy migration**: Change endpoint URL to switch to AWS S3
- **Docker-friendly**: Official MinIO container for local dev

### Negative

- **Operational overhead**: Must manage MinIO infrastructure
- **Limited features**: No built-in CDN, replication requires setup
- **Scaling complexity**: High availability requires multiple nodes
- **No edge caching**: Latency for geographically distant users

### Neutral

- Bucket policies work similarly to AWS S3
- MinIO Console provides admin UI (port 9001)
- Compatible with existing S3 tools and libraries

## Alternatives Considered

### Option A: AWS S3 Direct

Use Amazon S3 from the start.

**Pros:**
- Highly scalable and reliable
- Built-in CDN integration (CloudFront)
- Managed service, no operations

**Cons:**
- Cost for MVP (storage + requests)
- AWS account required
- Data residency considerations
- Vendor lock-in from day one

**Why not chosen:** Unnecessary cost and complexity for MVP; MinIO provides migration path.

### Option B: Local Filesystem

Store files on application server filesystem.

**Pros:**
- Simplest implementation
- No additional services

**Cons:**
- Not scalable (single server)
- No redundancy
- Deployment complications
- Backup complexity

**Why not chosen:** Doesn't support horizontal scaling; too fragile for user content.

### Option C: Cloudflare R2

S3-compatible storage with no egress fees.

**Pros:**
- S3 compatible
- Zero egress pricing
- Global edge network

**Cons:**
- Requires Cloudflare account
- Less mature than S3/MinIO
- API differences in edge cases

**Why not chosen:** Cloud dependency not needed for MVP; considered for future migration.

### Option D: Database BLOB Storage

Store files directly in PostgreSQL.

**Pros:**
- Single data store
- Transactional with other data
- Simpler backup strategy

**Cons:**
- Database size bloat
- Performance issues at scale
- Not designed for large files
- Complicates database operations

**Why not chosen:** Databases should store structured data, not binary assets.

## Storage Strategy

### File Types and Limits

| Type | Formats | Max Size | Processing |
|------|---------|----------|------------|
| Profile Photo | JPEG, PNG | 5 MB | Resize, normalize |
| Certifications | PDF, JPEG, PNG | 5 MB | Validate, store |
| Education Docs | PDF, JPEG, PNG | 5 MB | Validate, store |

### Image Processing Pipeline

1. Validate content type matches declared MIME type
2. Check file size against limits
3. Load image with Pillow for validation
4. Resize if dimensions exceed limits (300-4096px)
5. Convert to target format (JPEG quality 90, PNG optimized)
6. Generate random filename
7. Upload to MinIO with correct content type

### URL Generation

Public URLs constructed as:
```
{MINIO_PUBLIC_ENDPOINT}/{BUCKET}/{key}
```

Example:
```
https://minio.valsa.solutions/tutor-assets/tutor_profiles/42/photo/a1b2c3d4e5f6.jpg
```

## Migration Path to AWS S3

When migrating to AWS S3:

1. **Create S3 bucket** with same structure
2. **Sync existing data**: `aws s3 sync` or rclone
3. **Update configuration**:
   ```python
   MINIO_ENDPOINT = "https://s3.amazonaws.com"
   MINIO_PUBLIC_ENDPOINT = "https://your-bucket.s3.amazonaws.com"
   MINIO_BUCKET = "edustream-assets"
   ```
4. **Update bucket policy** for public read
5. **Optional**: Add CloudFront CDN for caching
6. **DNS cutover**: Update public endpoint
7. **Decommission MinIO** after validation period

No code changes required due to S3 API compatibility.

## References

- Implementation: `backend/core/storage.py`
- Docker setup: `docker-compose.yml` (minio service)
- MinIO documentation: https://min.io/docs/minio/linux/index.html
- boto3 S3 client: https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/s3.html
