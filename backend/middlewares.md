# Middlewares Documentation

This project includes a set of middlewares to enhance security, observability, and performance.

## Available Middlewares

### 1. Request Logging (`middlewares/logging.py`)
Logs incoming requests and outgoing responses in **JSON format**.
- **Features**: Tracks request duration, status code, and includes `request_id` and `user_id` if available.
- **Headers**: Adds `X-Process-Time` header to the response.

### 2. Request ID Injection (`middlewares/request_id.py`)
Generates a unique UUID for each request and adds it to the `X-Request-ID` header.
- **Usage**: Useful for tracing requests across logs and services.

### 3. User Context (`middlewares/auth.py`)
Decodes the JWT Bearer token (if present) and populates `request.state.user` and `request.state.authenticated`.
- **Public Paths**: Can be configured to skip logic for certain paths.
- **State**:
    - `request.state.authenticated`: Boolean indicating if a valid token was found.
    - `request.state.user_id`: The user ID (sub) from the token.

### 4. Request Size Limiter (`middlewares/size_limit.py`)
Rejects requests where the `Content-Length` header exceeds the configured limit (default 10MB).
- **Status Code**: 413 Request Entity Too Large

### 5. Security Headers (`middlewares/security_headers.py`)
Adds standard security headers to every response:
- `X-Content-Type-Options: nosniff`
- `X-Frame-Options: DENY`
- `X-XSS-Protection: 1; mode=block`
- `Strict-Transport-Security`
- `Referrer-Policy`
- `Permissions-Policy`

### 6. Compression (GZip)
Compresses responses using GZip for reduced bandwidth usage.
- **Enabled**: Automatically for responses larger than 1KB.

## Registration
Middlewares are registered in `main.py` using `app.add_middleware()`. The order of registration matters (LIFO for request, FIFO for response).
