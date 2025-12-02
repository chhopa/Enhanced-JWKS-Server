# Project 3: Enhanced JWKS Server

A Flask-based web server that implements a JSON Web Key Set (JWKS) endpoint for secure authentication. This project includes user registration, JWT token generation with RSA signing, and secure key management with encryption.

**Name:** Tanchhopa Limbu Sanba  
**Course:** CSCE 3550 - Fall 2025  
**Project:** Project 3 - JWKS Server Implementation

## Features

- **RESTful API** for authentication and user management
- **JWKS Endpoint** (`.well-known/jwks.json`) for public key distribution
- **User Registration** with UUIDv4 password generation
- **Secure Password Hashing** using Argon2
- **JWT Token Generation** with RSA key pairs
- **AES Encryption** for private key storage
- **Rate Limiting** (10 requests/second per IP)
- **Authentication Logging** with IP tracking
- **SQLite Database** for persistent storage

## Tech Stack

- **Flask** - Web framework
- **PyCryptodome** - RSA key generation and cryptography
- **Argon2** - Password hashing
- **SQLite** - Database
- **pytest** - Testing framework

## Project Structure

```
.
├── app.py                 # Main Flask application
├── db.py                  # Database initialization and connection
├── jwks.py                # JWKS and RSA key management
├── crypto.py              # AES encryption/decryption utilities
├── routes/
│   ├── auth.py            # Authentication endpoints
│   └── register.py        # User registration endpoint
├── tests/
│   └── test_app.py        # Unit tests
├── requirements.txt       # Python dependencies
└── totally_not_my_privateKeys.db  # SQLite database (generated)
```

## Installation

### Prerequisites

- Python 3.8+
- pip

### Setup

1. **Clone the repository**
   ```bash
   git clone https://github.com/chhopa/Enhanced-JWKS-Server.git
   cd Enhanced-JWKS-Server
   ```

2. **Create a virtual environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure environment variables**
   
   Create a `.env` file in the project root:
   ```env
   NOT_MY_KEY=your-secret-key-here
   ```
   
   This key is used for AES encryption of private keys stored in the database.

## Usage

### Running the Server

```bash
python app.py
```

The server will start on `http://localhost:8080`

### API Endpoints

#### 1. Health Check
```http
GET /ping
```
Returns server status.

**Response:**
```json
{
  "message": "project 3 jwks server alive"
}
```

#### 2. JWKS Endpoint
```http
GET /.well-known/jwks.json
```
Returns the public keys in JWKS format.

**Response:**
```json
{
  "keys": [
    {
      "kty": "RSA",
      "use": "sig",
      "kid": "1",
      "n": "...",
      "e": "AQAB"
    }
  ]
}
```

#### 3. User Registration
```http
POST /register
Content-Type: application/json

{
  "username": "john_doe",
  "email": "john@example.com"
}
```

**Response (201):**
```json
{
  "password": "generated-uuid-password"
}
```

#### 4. Authentication
```http
POST /auth
Content-Type: application/json

{
  "username": "john_doe",
  "password": "generated-uuid-password"
}
```

**Response (200):**
```json
{
  "token": "eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCIsImtpZCI6IjEifQ..."
}
```

**Optional Query Parameter:**
- `?expired=true` - Request an expired token (for testing)

**Rate Limiting:**
- Maximum 10 requests per second per IP address
- Returns `429 Too Many Requests` if exceeded

## Database Schema

### users
| Column | Type | Description |
|--------|------|-------------|
| id | INTEGER | Primary key |
| username | TEXT | Unique username |
| password_hash | TEXT | Argon2 hashed password |
| email | TEXT | User email (unique) |
| date_registered | TIMESTAMP | Registration timestamp |
| last_login | TIMESTAMP | Last login timestamp |

### keys
| Column | Type | Description |
|--------|------|-------------|
| kid | INTEGER | Key ID (primary key) |
| key | BLOB | AES-encrypted RSA private key |
| exp | INTEGER | Unix timestamp expiration |

### auth_logs
| Column | Type | Description |
|--------|------|-------------|
| id | INTEGER | Primary key |
| request_ip | TEXT | Client IP address |
| request_timestamp | TIMESTAMP | Request time |
| user_id | INTEGER | Foreign key to users table |

## Security Features

1. **Password Security**
   - UUIDv4 generation for strong passwords
   - Argon2 hashing with built-in salt
   - Memory-hard algorithm resistant to brute-force

2. **Private Key Protection**
   - RSA private keys encrypted with AES-256
   - Encryption key derived from `NOT_MY_KEY` environment variable
   - Keys stored as encrypted blobs in database

3. **Rate Limiting**
   - Per-IP rate limiting to prevent abuse
   - Configurable time window and request limit

4. **Authentication Logging**
   - All authentication attempts logged with IP and timestamp
   - User ID tracking for successful authentications

## Testing

Run the test suite:

```bash
pytest tests/
```

Run with coverage:

```bash
coverage run -m pytest tests/
coverage report
```

Test Coverage Sample Output
```
platform darwin -- Python 3.13.1, pytest-8.3.4, pluggy-1.6.0
rootdir: /Users/tanchhopalimbu/Desktop/Fall 2025/CSCE 3550/Project 3
collected 4 items                                                                                                                                  

tests/test_app.py ....                                                                                                                       [100%]

================================================================ 4 passed in 3.02s =================================================================
Name                 Stmts   Miss  Cover
----------------------------------------
app.py                  20      1    95%
crypto.py               25      1    96%
db.py                   14      0   100%
jwks.py                 47      0   100%
routes/__init__.py       0      0   100%
routes/auth.py          44      6    86%
routes/register.py      26      4    85%
tests/__init__.py        0      0   100%
tests/test_app.py       69      0   100%
----------------------------------------
TOTAL                  245     12    95%
```
### Run the testclient (Gradebot)
```bash
./gradebot project3
```

### Sample Gradebot Output
```
╭────────────────────────────────────────────┬────────┬──────────┬─────────╮
│ RUBRIC ITEM                                │ ERROR? │ POSSIBLE │ AWARDED │
├────────────────────────────────────────────┼────────┼──────────┼─────────┤
│ Create users table                         │        │        5 │       5 │
│ /register endpoint                         │        │       20 │      20 │
│ Private Keys are encrypted in the database │        │       25 │      25 │
│ Create auth_logs table                     │        │        5 │       5 │
│ /auth requests are logged                  │        │       10 │      10 │
│ /auth is rate-limited (optional)           │        │       25 │      25 │
├────────────────────────────────────────────┼────────┼──────────┼─────────┤
│                                            │  TOTAL │       90 │      90 │
╰────────────────────────────────────────────┴────────┴──────────┴─────────╯
```


## Development

### Adding New Routes

1. Create a new blueprint in `routes/`
2. Register the blueprint in `app.py`

Example:
```python
# routes/new_route.py
from flask import Blueprint

bp_new = Blueprint("new", __name__)

@bp_new.get("/new-endpoint")
def new_endpoint():
    return {"message": "Hello"}
```

```python
# app.py
from routes.new_route import bp_new
app.register_blueprint(bp_new)
```

## Environment Variables

| Variable | Description | Required |
|----------|-------------|----------|
| NOT_MY_KEY | AES encryption key for private keys | Yes |

## Notes

- Database file (`totally_not_my_privateKeys.db`) is automatically created on first run
- RSA keys are generated and encrypted on initialization
- Rate limiter is configured for 10 requests per second per IP
- All private keys stored in the database are AES-encrypted
