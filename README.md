# BillBuster Docker Setup

This project contains a Docker setup with a Node.js backend, MongoDB database, and a Python script that polls the LegiScan API every 24 hours to track and process new legislation and bills from all states and the federal level.

## Project Structure

```
.
├── docker-compose.yml
├── .env                  # Root environment variables
├── .gitignore
├── README.md
├── src
│   ├── backend
│   │   ├── Dockerfile
│   │   ├── package.json
│   │   ├── server.js
│   │   ├── db.js
│   │   ├── .env
│   │   ├── models/
│   │   │   └── Bill.js  # MongoDB schema for bills
│   │   └── routes/
│   │       └── bills.js # API routes for bills
│   └── python
│       ├── Dockerfile
│       ├── api_poller.py
│       ├── test_legiscan_api.py  # Script to test LegiScan API key
│       ├── requirements.txt
│       └── .env
```

## Services

1. **Node.js Backend**: Express server with MongoDB connection and RESTful API for managing bills
2. **MongoDB**: Database for storing bill data with a structured schema
3. **Python LegiScan API Poller**: Script that runs every 24 hours to poll the LegiScan API for new legislation and bills across all states and federal level. It downloads new bills, saves them to disk, and processes them asynchronously.

## MongoDB Schema

The system uses the following MongoDB schema for bills:

```
Bill {
  _id: UUID (Primary Key)
  billId: String
  date: DateTime
  isFederal: Boolean
  state: String (2 characters)
  filePath: String[] (Array of file paths)
  proposer: String
  status: String
  title: String
  citation: String[]
  tags: String[]
  summary: String[]
  createdAt: DateTime
  updatedAt: DateTime
}
```

## API Endpoints

The Node.js backend provides the following RESTful API endpoints:

### Bills

- `GET /api/bills` - Get all bills
- `GET /api/bills/search` - Search bills with filters (state, isFederal, status, tags, startDate, endDate)
- `GET /api/bills/:id` - Get a specific bill by ID
- `POST /api/bills` - Create a new bill
- `PATCH /api/bills/:id` - Update a bill
- `DELETE /api/bills/:id` - Delete a bill

### Bill Files

- `POST /api/bills/:id/files` - Add a file path to a bill

### Bill Tags

- `POST /api/bills/:id/tags` - Add a tag to a bill
- `DELETE /api/bills/:id/tags/:tag` - Remove a tag from a bill

## Prerequisites

- Docker and Docker Compose installed on your system
- Basic knowledge of Docker, Node.js, and Python

## Getting Started

1. Clone this repository
2. Configure the environment variables in `.env` files if needed
3. Build and start the containers:

```bash
docker-compose up -d
```

4. To stop the containers:

```bash
docker-compose down
```

## Configuration

### Node.js Backend

The backend environment variables are in `src/backend/.env`:

- `PORT`: The port the server runs on (default: 3000)
- `MONGODB_URI`: MongoDB connection string
- `NODE_ENV`: Environment (development/production)

### Python LegiScan API Poller

The Python script environment variables are in `src/python/.env`:

- `MONGODB_URI`: MongoDB connection string
- `LEGISCAN_API_KEY`: Your LegiScan API key (required)
- `BILLS_DIRECTORY`: Directory where downloaded bills will be stored

**Important**: You need to obtain a LegiScan API key from [LegiScan API](https://legiscan.com/legiscan) to use the bill polling functionality.

You can set your LegiScan API key in one of three ways:
1. Edit the `src/python/.env` file directly
2. Edit the root `.env` file (recommended)
3. Set it as an environment variable when running docker-compose:

```bash
LEGISCAN_API_KEY=your_api_key_here docker-compose up -d
```

The root `.env` file is the recommended approach as it will be automatically picked up by docker-compose without requiring additional command-line parameters.

#### Testing Your LegiScan API Key

Before running the full Docker setup, you can test your LegiScan API key using the provided test script:

```bash
cd src/python
pip install requests
python test_legiscan_api.py your_api_key_here
```

This script will verify that your API key is working correctly by making a test request to the LegiScan API.

## Accessing the Services

- **Node.js Backend**: http://localhost:3000
- **MongoDB**: mongodb://localhost:27017

## Logs

To view logs for a specific service:

```bash
docker-compose logs -f backend
docker-compose logs -f mongodb
docker-compose logs -f api-poller
```

## Customization

### Modifying the API Polling Interval

The Python script is configured to poll the LegiScan API every 24 hours. To change this interval, modify the `schedule.every(24).hours.do(poll_legiscan_api)` line in `src/python/api_poller.py`.

### Customizing Bill Processing Logic

To customize how the downloaded bills are processed, modify the `process_bill_async` function in `src/python/api_poller.py`. This is an asynchronous function that is called in a separate thread for each new bill that is downloaded.

### Accessing Downloaded Bills

Bills are downloaded and stored in the `/usr/src/app/bills` directory inside the container, which is mapped to a Docker volume named `bills-data`. Each state has its own subdirectory, and bills are named using the format `{state}_{bill_number}_{doc_id}.txt`.
