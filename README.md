# Tableau Report Tracker

A web application for browsing Tableau reports and submitting change requests via Trello integration.

## Features

- **Report Search**: Browse and search Tableau workbooks with folder navigation mirroring Tableau's project structure
- **Request Creation**: Submit change requests that automatically create Trello cards with workflow checklists
- **Request Tracking**: Track the status and progress of submitted requests

## Tech Stack

| Layer | Technology |
|-------|------------|
| Backend | Python 3.10+, Flask, Tableau Server Client |
| Frontend | React 19, TypeScript, Tailwind CSS, TanStack Query |
| Integrations | Tableau Server API, Trello API |

## Prerequisites

- Python 3.10 or higher
- Node.js 18 or higher
- npm 9 or higher

## Setup

### Backend (Flask Server)

```bash
cd server

# Create virtual environment
python -m venv venv

# Activate virtual environment
.\venv\Scripts\Activate.ps1  # PowerShell
# or
.\venv\Scripts\activate.bat  # Command Prompt

# Install dependencies
pip install -r requirements.txt

# Create environment file
cp .env.example .env
# Edit .env with your credentials
```

### Frontend (React Client)

```bash
cd client

# Install dependencies
npm install
```

## Environment Variables

Create a `server/.env` file with the following variables:

```bash
# Tableau Server Connection
TABLEAU_SERVER_URL=https://your-tableau-server.com
TABLEAU_SITE_NAME=your-site-name
TABLEAU_TOKEN_NAME=your-personal-access-token-name
TABLEAU_TOKEN_SECRET=your-personal-access-token-secret

# Trello Integration
TRELLO_API_KEY=your-trello-api-key
TRELLO_TOKEN=your-trello-token
TRELLO_BOARD_NAME=The Report Report
```

> **Note**: The application works without credentials using mock data for development.

## Running the Application

### Development Mode

**Terminal 1 - Backend:**
```bash
cd server
.\venv\Scripts\Activate.ps1
python run.py --port 5000 --debug
```

**Terminal 2 - Frontend:**
```bash
cd client
npm run dev
```

The frontend runs at `http://localhost:5173` and proxies API requests to the backend.

### Verify Setup

```bash
# Health check
curl http://localhost:5000/api/health
# Expected: {"status":"ok","service":"tableau-report-tracker","tableauConfigured":true}

# Reports endpoint
curl http://localhost:5000/api/reports
# Expected: {"success":true,"data":[...],"total":N}
```

## Running Tests

### Backend Tests

```bash
cd server
.\venv\Scripts\Activate.ps1
pytest tests/ -v
# Expected: 46 passed
```

### Frontend Build Check

```bash
cd client
npm run build
# Verifies TypeScript compilation and production build
```

## Project Structure

```
tableau-report-tracker/
├── README.md                    # This file
├── DEVELOPMENT_PLAN.md          # Development phases and session notes
├── client/                      # React frontend
│   ├── src/
│   │   ├── api/                 # API client and TanStack Query hooks
│   │   ├── components/          # Reusable UI components
│   │   ├── lib/                 # Utility functions
│   │   ├── pages/               # Page components
│   │   └── types/               # TypeScript type definitions
│   └── package.json
└── server/                      # Flask backend
    ├── src/
    │   ├── app.py               # Flask application factory
    │   ├── routes/              # API route handlers
    │   └── services/            # Tableau and Trello service classes
    ├── tests/                   # pytest test files
    └── requirements.txt
```

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/health` | Health check with configuration status |
| GET | `/api/reports` | List all Tableau workbooks |
| GET | `/api/reports/:id` | Get workbook details with views |
| GET | `/api/reports/projects` | List unique project paths |
| GET | `/api/requests?email=` | Get change requests by requester email |
| GET | `/api/requests/:id` | Get request details with checklist |
| POST | `/api/requests` | Create a new change request |

## License

Internal use only.
