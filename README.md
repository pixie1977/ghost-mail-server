# Ghost Mail Server

Secure and fully anonymous messaging server built with FastAPI and Uvicorn.

## Features

- End-to-end anonymous messaging
- JWT-based authentication
- Secure password hashing with bcrypt
- Full request logging with structured output
- Modular FastAPI architecture
- Environment-based configuration
- Rate limiting for authentication endpoints
- Automatic backups (optional)

## Technologies

- **Framework**: FastAPI >=0.68.0
- **ASGI Server**: Uvicorn >=0.15.0
- **Authentication**: JWT, python-jose[cryptography] >=3.3.0
- **Password Hashing**: bcrypt >=3.2.0
- **Environment Management**: python-dotenv >=0.19.0
- **Cryptography**: cryptography >=3.4.8
- **JWT Library**: PyJWT >=2.4.0
- **Multipart Form Data**: python-multipart >=0.0.5
- **Dependencies**: See `requirements.txt`

## Project Structure

```
ghost-mail-server/
├── app/
│   ├── auth/
│   │   ├── auth.py
│   │   ├── schemas.py
│   │   └── __init__.py
│   ├── messages/
│   │   ├── messages.py
│   │   ├── schemas.py
│   │   └── __init__.py
│   ├── config/
│   │   ├── config.py
│   │   └── __init__.py
│   ├── utils/
│   │   ├── logging.py
│   │   ├── security.py
│   │   ├── storage.py
│   │   └── __init__.py
│   └── fast_api_main.py
├── test/
│   ├── test_client.py
│   ├── test_client_register_and_login_scenario.py
│   ├── test_client_send_and_recieve_scenario.py
│   └── conftest.py
├── backups/
├── .env.example
├── .gitignore
├── analytics.txt
├── main.py
├── README.md
├── requirements.txt
└── users.json
```

## Installation

1. Clone the repository:
```bash
git clone https://github.com/pixie1977/ghost-mail-server.git
```

2. Create a virtual environment:
```bash
python -m venv venv
```

3. Activate the virtual environment:
```bash
# On Windows
venv\Scripts\activate
```

4. Install dependencies:
```bash
pip install -r requirements.txt
```

5. Create `.env` file in the project root (use `.env.example` as reference):
```env
JWT_TOKEN_SECRET_KEY=your-secret-key-here
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=60
RATE_LIMIT_REGISTER=5/minute
RATE_LIMIT_LOGIN=10/minute
BACKUP_ENABLED=true
LOG_LEVEL=INFO
HOST="0.0.0.0"
PORT=8000
```

## Running the Server

Start the development server:
```bash
python main.py
```

Or run directly with reload:
```bash
uvicorn app.fast_api_main:app --host 0.0.0.0 --port 8000 --reload
```

The server will be available at `http://localhost:8000`.

## API Endpoints

### Authentication (`/auth`)
- `POST /auth/register` - Register a new user
- `POST /auth/login` - Login and get JWT token

### Messages (`/messages`)
- `POST /messages/send` - Send an anonymous message
- `GET /messages/received` - Get received messages
- `GET /messages/sent` - Get sent messages

### Root
- `GET /` - Welcome message

## Example Usage

1. Register a user:
```bash
curl -X POST "http://localhost:8000/auth/register" \
-H "Content-Type: application/json" \
-d '{"username":"user1", "password":"pass123"}'
```

2. Login to get token:
```bash
curl -X POST "http://localhost:8000/auth/login" \
-H "Content-Type: application/json" \
-d '{"username":"user1", "password":"pass123"}'
```

3. Send a message (using obtained token):
```bash
curl -X POST "http://localhost:8000/messages/send" \
-H "Authorization: Bearer <your_token>" \
-H "Content-Type: application/json" \
-d '{"recipient":"user2", "content":"Hello, this is anonymous!"}'
```

## Testing

Run tests using pytest:
```bash
pytest test/
```

The test suite includes:
- Authentication flow (registration and login)
- Message sending and receiving scenarios
- Client integration tests

## Logging

All requests and server events are logged via the built-in Logger system. Logs are output to stdout with structured format including timestamp, level, module, and message.

## License

This project is licensed under the MIT License - see the LICENSE file for details.