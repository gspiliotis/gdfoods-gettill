# Order Totals Sync

A Python script that syncs order totals from two PostgreSQL databases (Juan's and Texans) to a Google Spreadsheet.

## Features

- Connects to two PostgreSQL databases
- Queries order totals based on date range
- Appends results to Google Sheets
- Configurable date ranges via command line
- Dockerized for easy deployment
- Automatic Docker image publishing to GitHub Container Registry

## Prerequisites

- Python 3.11+
- PostgreSQL databases access
- Google Cloud Service Account with Sheets API access
- Docker (for containerized deployment)

## Setup

### 1. Clone the repository

```bash
git clone <repository-url>
cd get-cash
```

### 2. Configure environment variables

Copy the example environment file and fill in your actual values:

```bash
cp .env.example .env
```

Edit `.env` with your actual database credentials and Google Sheets ID:

```
JUAN_DB_ADDRESS=ip_address_of_database1
JUAN_DB_DATABASE=your_database1
JUAN_DB_USERNAME=your_username
JUAN_DB_PASSWORD=your_actual_password

TEXANS_DB_ADDRESS=ip_address_of_database2
TEXANS_DB_DATABASE=tyour_database2
TEXANS_DB_USERNAME=your_username2
TEXANS_DB_PASSWORD=your_actual_password2

GOOGLE_SHEET_ID=your_google_sheet_id_here
GOOGLE_CREDENTIALS_FILE=google-credentials.json
```

### 3. Set up Google Sheets API

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select an existing one
3. Enable the Google Sheets API and Google Drive API
4. Create a Service Account
5. Download the credentials JSON file
6. Save it as `credentials.json` in the project root
7. Share your Google Spreadsheet with the service account email (found in the credentials file)

### 4. Install dependencies (for local development)

```bash
pip install -r requirements.txt
```

## Usage

### Local Execution

Run the script with default date (today):

```bash
python sync_orders.py
```

Run with specific date:

```bash
python sync_orders.py --from-date 2025-12-10 --to-date 2025-12-10
```

Run with date range:

```bash
python sync_orders.py --from-date 2025-12-01 --to-date 2025-12-10
```

### Docker Execution

Build the Docker image:

```bash
docker build -t order-sync .
```

Run the container:

```bash
docker run --rm \
  --env-file .env \
  -v $(pwd)/google-credentials.json:/app/credentials.json \
  order-sync --from-date 2025-12-10
```

### Using Published Docker Image

Once the GitHub Action has run, you can pull and use the published image:

```bash
docker pull ghcr.io/<your-username>/get-cash:latest

docker run --rm \
  --env-file .env \
  -v $(pwd)/credentials.json:/app/credentials.json \
  ghcr.io/<your-username>/get-cash:latest --from-date 2025-12-10
```

## Output

The script appends a row to the Google Spreadsheet with:
- Date (or date range)
- Order total from database1
- Order total from database2

## CI/CD

The repository includes a GitHub Action (`.github/workflows/docker-publish.yml`) that automatically:
- Builds the Docker image
- Pushes it to GitHub Container Registry (ghcr.io)
- Tags it with the branch name and `latest` for the main branch

The action triggers on:
- Push to `main` branch
- Manual workflow dispatch

## Troubleshooting

### Database Connection Issues

- Verify database credentials in `.env`
- Check network connectivity to database server
- Ensure PostgreSQL port (default 5432) is accessible

### Google Sheets Issues

- Verify `credentials.json` is present and valid
- Check that the service account email has access to the spreadsheet
- Verify `GOOGLE_SHEET_ID` is correct (found in the spreadsheet URL)

### Docker Issues

- Ensure `.env` file exists when running with `--env-file`
- Mount credentials file correctly with `-v` flag
- Check Docker daemon is running

## License

MIT
