# Cache Management Runbook

## Quick Reference

| Operation | Command |
|-----------|---------|
| Connect to Redis | `docker compose exec redis redis-cli` |
| Clear all cache | `docker compose exec redis redis-cli FLUSHDB` |
| View memory usage | `docker compose exec redis redis-cli INFO memory` |
| View keys | `docker compose exec redis redis-cli KEYS '*'` |

---

## Redis Operations

### Connect to Redis CLI

```bash
docker compose exec redis redis-cli
```

### View All Keys

```bash
# List all keys (use with caution in production)
docker compose exec redis redis-cli KEYS '*'

# Count keys
docker compose exec redis redis-cli DBSIZE
```

### Clear All Cache

```bash
# Clear current database
docker compose exec redis redis-cli FLUSHDB

# Clear all databases (if using multiple)
docker compose exec redis redis-cli FLUSHALL
```

### Clear Specific Keys

```bash
# Delete specific key
docker compose exec redis redis-cli DEL "key_name"

# Delete keys matching pattern
docker compose exec redis redis-cli KEYS "user:*" | xargs docker compose exec redis redis-cli DEL
```

---

## Cache Debugging

### Check if Redis is Responding

```bash
docker compose exec redis redis-cli PING
# Should return: PONG
```

### View Memory Usage

```bash
docker compose exec redis redis-cli INFO memory
```

Key metrics:
- `used_memory_human`: Current memory usage
- `maxmemory_human`: Max configured memory
- `mem_fragmentation_ratio`: Should be close to 1.0

### View Connection Count

```bash
docker compose exec redis redis-cli INFO clients
```

### View Hit/Miss Rate

```bash
docker compose exec redis redis-cli INFO stats | grep keyspace
```

---

## Common Issues

### Redis Not Responding

1. Check if container is running
   ```bash
   docker compose ps redis
   ```

2. Check logs
   ```bash
   docker compose logs redis
   ```

3. Restart Redis
   ```bash
   docker compose restart redis
   ```

### Memory Full

1. Check memory usage
   ```bash
   docker compose exec redis redis-cli INFO memory
   ```

2. If near limit, clear non-essential cache
   ```bash
   # Clear all cache (will be rebuilt)
   docker compose exec redis redis-cli FLUSHDB
   ```

3. Consider increasing memory limit in docker-compose.yml

### High Latency

1. Check slow log
   ```bash
   docker compose exec redis redis-cli SLOWLOG GET 10
   ```

2. Check for large keys
   ```bash
   docker compose exec redis redis-cli --bigkeys
   ```

---

## Application-Level Cache

### Clear Application In-Memory Cache

The backend uses in-memory caching. To clear:

```bash
# Restart the backend service
docker compose restart backend
```

### Frontend Cache

Frontend caches API responses. To clear:

1. User can clear browser cache
2. For all users, deploy with new cache-busting hashes (automatic on rebuild)

---

## Cache Best Practices

1. **Set TTLs**: All cached data should have expiration
2. **Cache invalidation**: Invalidate on write operations
3. **Monitor hit rate**: Track cache effectiveness
4. **Size limits**: Monitor memory usage

---

## Redis Configuration

Current configuration (in docker-compose.yml):
- Max memory: 256MB
- Eviction policy: allkeys-lru

To change configuration:
```yaml
# docker-compose.yml
redis:
  command: redis-server --maxmemory 512mb --maxmemory-policy allkeys-lru
```
