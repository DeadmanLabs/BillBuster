# BillBuster Project Guidelines

## Build & Run Commands
- Backend: `docker-compose up -d backend`
- Python poller: `docker-compose up -d api-poller`
- Full stack: `docker-compose up -d`
- Stop services: `docker-compose down`
- Backend dev mode: `cd src/backend && npm run dev`
- Backend logs: `docker-compose logs -f backend`
- Test API key: `cd src/python && python test_legiscan_api.py your_api_key_here`

## Code Style Guidelines
- **Imports**: Group imports (built-ins first, then third-party, finally local)
- **Backend**: Use Express.js patterns with async/await for MongoDB operations
- **Python**: Follow PEP 8 style guide with type hints where applicable
- **Naming**: camelCase for JavaScript, snake_case for Python
- **Models**: Follow MongoDB schema defined in Bill.js, with proper validation
- **Error Handling**: Use try/catch blocks for async operations, proper HTTP status codes
- **Documentation**: Add JSDoc comments for functions, maintain README.md for major changes

## API Endpoints
- `GET /api/bills` - Get all bills
- `GET /api/bills/search` - Search bills with filters (state, isFederal, status, tags, date ranges)
- `GET /api/bills/:id` - Get bill by ID
- `GET /api/bills/:id/download/:fileIndex` - Download bill file (fileIndex refers to index in filePath array)
- `POST/PATCH/DELETE` endpoints for bill management

## Project Structure
- Backend: Express.js + MongoDB (models, routes)
- Python: API polling service with async processing
- Dockerized services with shared network and volumes