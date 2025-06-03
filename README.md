# Secret manager

**`secret-manager`** is FastAPI-based service for one-time secret sharing.

This project was built as a test assignment, following the principles of **clean architecture and SOLID**.

---

## Tech Stack

- Python 3.12
- FastAPI
- PostgreSQL + SQLAlchemy
- cryptography
- bcrypt
- Pytest
- Docker + Docker Compose

---

## Project Setup

1. **Create a configuration file based on the template:**
   ```bash
   cp .env.dist .env
   ```

2. **Edit the `.env` file and set the required environment variables:**
   ```env
   # Database configuration
   POSTGRES_USER=youruser
   POSTGRES_PASSWORD=yourpassword
   POSTGRES_DB=yourdatabase
   
   REDIS_DB=yourredisdb
   
   SECRET_KEY=yoursecretkey
   ```

3. **Start the services using Docker Compose:**
   ```bash
   docker-compose up -d
   docker exec -it api sh -c 'alembic upgrade head'
   ```

---

## Examples of requests

### Create a new secret

```bash
curl -X POST "http://localhost:8000/api/secret" \
  -H "Content-Type: application/json" \
  -d '{
        "secret": "my-secret",
        "passphrase": "your-passphrase", 
        "ttl_seconds": 3600
      }'
```

**Parameters:**

- secret (required): The confidential data to be stored.
- passphrase (optional): A passphrase to protect delete a secret.
- ttl_seconds (optional): The time-to-live (TTL) in seconds for the secret. After this period, the secret will expire.

**Example of a response:**

```json
{
  "secret_key": "12345678-1234-5678-1234-567812345678"
}
```

---

### Get the secret by secret key

```bash
curl -X GET "http://localhost:8000/api/secret/{secret-key}" -H "accept: application/json"
```

**Example of a response:**

```json
{
  "secret": "my-secret"
}
```

### Delete the secret by secret key

```bash
curl -X DELETE "http://localhost:8000/api/secret/{secret-key}" -H "accept: application/json"
```

**Example of a response:**

* Status Code: 200 OK
* Response Body: No content (empty)

### Get log events

```bash
curl -X GET "http://localhost:8000/api/event?page=1&page_size=1" -H "accept: application/json"
```

**Example of a response:**

```json
{
  "total": 2,
  "size": 2,
  "events": [
    {
      "id": "104832d1-b7b2-4eca-ad4c-b5df407d119d",
      "client_ip": "127.0.0.1",
      "client_user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/112.0.0.0 Safari/537.36",
      "type": "CREATE",
      "created_at": "2025-03-27T12:34:56",
      "secret_id": "104832d1-b7b2-4eca-ad4c-b5df407d119d"
    }
  ]
}

```

**Note:** The `type` field can be one of the following:

- **CREATE**: Indicates that the secret was created.
- **READ**: Indicates that the secret was accessed or read.
- **DELETE**: Indicates that the secret was deleted.

---

## Tests

1. **Create test database**

```bash
docker exec -it db psql -U postgres -c "CREATE DATABASE test;"
```

2. **Run Tests**

> **Note:** Tests are specially located in the container so that they can be launched with minimal efforts

```bash
docker exec -it api sh -c 'TEST_DB=test TEST_REDIS_DB=1 python3 -m pytest tests --asyncio-mode=auto'

```

## API Documentation

Once the server is running, Swagger UI will be available at:  
[http://localhost:8000/api/docs](http://localhost:8000/api/docs)

