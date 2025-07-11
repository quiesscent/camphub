# CampHub

A comprehensive campus management system with Django REST Framework backend and React frontend.

## Project Structure

```
camphub/
├── backend/          # Django REST Framework backend
│   ├── academic/     # Academic management
│   ├── community/    # Community features
│   ├── content/      # Content management
│   ├── messaging/    # Messaging system
│   └── users/        # User management
└── frontend/         # React + Vite frontend
```

## Development Setup

### Backend Setup

1. Navigate to the backend directory:
```bash
cd backend
```

2. Create a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows use: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Run migrations:
```bash
python manage.py migrate
```

5. Start the development server:
```bash
python manage.py runserver
```

The backend will be available at http://127.0.0.1:8000

### Frontend Setup

1. Navigate to the frontend directory:
```bash
cd frontend
```

2. Install dependencies:
```bash
npm install
```

3. Start the development server:
```bash
npm run dev
```

The frontend will be available at http://127.0.0.1:5173

## API Documentation

The API documentation is available in three formats:

1. **Swagger UI** (Interactive documentation):
   - URL: http://127.0.0.1:8000/api/docs/
   - Best for testing endpoints directly in the browser

2. **ReDoc** (Readable documentation):
   - URL: http://127.0.0.1:8000/api/redoc/
   - Better for reading and understanding the API structure

3. **Raw Schema**:
   - URL: http://127.0.0.1:8000/api/schema/
   - OpenAPI schema in JSON format

## API Authentication

The API uses JWT (JSON Web Token) authentication:

1. Get your access token by sending a POST request to:
   ```
   POST /api/v1/auth/token/
   {
     "username": "your_username",
     "password": "your_password"
   }
   ```

2. Include the token in your requests:
   ```
   Authorization: Bearer <your_access_token>
   ```

3. Refresh your token when it expires:
   ```
   POST /api/v1/auth/token/refresh/
   {
     "refresh": "your_refresh_token"
   }
   ```

## Available Endpoints

- Authentication: `/api/v1/auth/`
- User Management: `/api/v1/users/`
- Academic: `/api/v1/academic/`
- Community: `/api/v1/community/`
- Messaging: `/api/v1/messaging/`

For detailed endpoint documentation, please refer to the API documentation using Swagger UI or ReDoc.

## Development Guidelines

1. Always check the API documentation before implementing new features
2. Backend follows Django REST Framework best practices
3. Frontend uses TypeScript for better type safety
4. Use the provided API client in `frontend/src/lib/api.ts` for making API calls


