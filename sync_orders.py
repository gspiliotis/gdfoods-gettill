#!/usr/bin/env python3
"""
Script to sync order totals from two PostgreSQL databases to Google Sheets.
"""

import argparse
import os
import sys
from datetime import datetime, timedelta
from typing import List, Optional, Tuple, Dict

import psycopg
from dotenv import load_dotenv
import gspread
from google.oauth2.service_account import Credentials


def parse_arguments() -> Tuple[str, str, bool]:
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description='Sync order totals from PostgreSQL databases to Google Sheets'
    )
    parser.add_argument(
        '--from-date',
        type=str,
        help='Start date in YYYY-MM-DD format (default: today)',
        default=None
    )
    parser.add_argument(
        '--to-date',
        type=str,
        help='End date in YYYY-MM-DD format (default: today)',
        default=None
    )
    parser.add_argument(
        '--overwrite',
        action='store_true',
        help='Overwrite existing rows with matching dates instead of skipping them'
    )

    args = parser.parse_args()

    # Default to today if not specified
    today = datetime.now().strftime('%Y-%m-%d')
    from_date = args.from_date if args.from_date else today
    to_date = args.to_date if args.to_date else today

    # Validate date format
    try:
        datetime.strptime(from_date, '%Y-%m-%d')
        datetime.strptime(to_date, '%Y-%m-%d')
    except ValueError as e:
        print(f"Error: Invalid date format. Use YYYY-MM-DD. {e}")
        sys.exit(1)

    return from_date, to_date, args.overwrite


def generate_date_range(from_date: str, to_date: str) -> List[str]:
    """Generate a list of dates between from_date and to_date (inclusive)."""
    start = datetime.strptime(from_date, '%Y-%m-%d')
    end = datetime.strptime(to_date, '%Y-%m-%d')

    dates = []
    current = start
    while current <= end:
        dates.append(current.strftime('%Y-%m-%d'))
        current += timedelta(days=1)

    return dates


def get_db_connection(host: str, database: str, user: str, password: str):
    """Create a PostgreSQL database connection."""
    try:
        conn = psycopg.connect(
            host=host,
            dbname=database,
            user=user,
            password=password
        )
        return conn
    except psycopg.Error as e:
        print(f"Error connecting to database {database}: {e}")
        sys.exit(1)


def fetch_order_total(conn, date: str) -> float:
    """Fetch order total from database for a specific date."""
    query = """
        SELECT SUM(order_total)
        FROM orders_hist
        WHERE (sp_id=2 OR sp_id=3)
        AND payment_id=1
        AND order_total IS NOT NULL
        AND fo_day = %s
    """

    try:
        with conn.cursor() as cursor:
            cursor.execute(query, (date,))
            result = cursor.fetchone()[0]
            return float(result) if result is not None else 0.0
    except psycopg.Error as e:
        print(f"Error executing query: {e}")
        sys.exit(1)


def get_google_sheet(spreadsheet_id: str, credentials_file: str):
    """Get Google Sheets client and sheet object."""
    try:
        scopes = [
            'https://www.googleapis.com/auth/spreadsheets',
            'https://www.googleapis.com/auth/drive'
        ]
        creds = Credentials.from_service_account_file(credentials_file, scopes=scopes)
        client = gspread.authorize(creds)
        sheet = client.open_by_key(spreadsheet_id).sheet1
        return sheet
    except Exception as e:
        print(f"Error connecting to Google Sheets: {e}")
        sys.exit(1)


def get_existing_dates(sheet) -> Dict[str, int]:
    """Get a dictionary mapping dates to their row numbers in the sheet."""
    try:
        all_values = sheet.get_all_values()
        date_to_row = {}

        # Start from row 1 (index 0) - assuming no header row
        # If there's a header, change range(len(all_values)) to range(1, len(all_values))
        for idx, row in enumerate(all_values):
            if row and len(row) > 0:
                date = row[0]
                # Row number in Google Sheets (1-indexed)
                date_to_row[date] = idx + 1

        return date_to_row
    except Exception as e:
        print(f"Error reading existing data from Google Sheets: {e}")
        sys.exit(1)


def update_or_append_row(
    sheet,
    date_str: str,
    juan_total: float,
    texans_total: float,
    existing_dates: Dict[str, int],
    overwrite: bool
):
    """Update an existing row or append a new one based on overwrite flag."""
    try:
        row = [date_str, juan_total, texans_total]

        if date_str in existing_dates:
            if overwrite:
                row_num = existing_dates[date_str]
                sheet.update(values=[row], range_name=f'A{row_num}:C{row_num}')
                print(f"Updated row {row_num}: {row}")
            else:
                print(f"Skipping {date_str} (already exists)")
        else:
            sheet.append_row(row)
            print(f"Added new row: {row}")
    except Exception as e:
        print(f"Error writing to Google Sheets: {e}")
        sys.exit(1)


def main():
    """Main execution function."""
    # Load environment variables
    load_dotenv()

    # Parse command line arguments
    from_date, to_date, overwrite = parse_arguments()

    print(f"Processing dates: {from_date} to {to_date}")
    print(f"Overwrite mode: {'enabled' if overwrite else 'disabled'}")

    # Get database credentials from environment
    juan_host = os.getenv('JUAN_DB_ADDRESS')
    juan_db = os.getenv('JUAN_DB_DATABASE')
    juan_user = os.getenv('JUAN_DB_USERNAME')
    juan_pass = os.getenv('JUAN_DB_PASSWORD')

    texans_host = os.getenv('TEXANS_DB_ADDRESS')
    texans_db = os.getenv('TEXANS_DB_DATABASE')
    texans_user = os.getenv('TEXANS_DB_USERNAME')
    texans_pass = os.getenv('TEXANS_DB_PASSWORD')

    google_sheet_id = os.getenv('GOOGLE_SHEET_ID')
    google_creds_file = os.getenv('GOOGLE_CREDENTIALS_FILE', 'credentials.json')

    # Validate required environment variables
    required_vars = [
        ('JUAN_DB_ADDRESS', juan_host),
        ('JUAN_DB_DATABASE', juan_db),
        ('JUAN_DB_USERNAME', juan_user),
        ('JUAN_DB_PASSWORD', juan_pass),
        ('TEXANS_DB_ADDRESS', texans_host),
        ('TEXANS_DB_DATABASE', texans_db),
        ('TEXANS_DB_USERNAME', texans_user),
        ('TEXANS_DB_PASSWORD', texans_pass),
        ('GOOGLE_SHEET_ID', google_sheet_id),
    ]

    missing_vars = [var_name for var_name, var_value in required_vars if not var_value]
    if missing_vars:
        print(f"Error: Missing required environment variables: {', '.join(missing_vars)}")
        sys.exit(1)

    # Generate list of dates to process
    dates_to_process = generate_date_range(from_date, to_date)
    print(f"Total dates to process: {len(dates_to_process)}")

    # Connect to databases
    print("Connecting to Juan's database...")
    juan_conn = get_db_connection(juan_host, juan_db, juan_user, juan_pass)

    print("Connecting to Texans database...")
    texans_conn = get_db_connection(texans_host, texans_db, texans_user, texans_pass)

    # Connect to Google Sheets and get existing data
    print("Connecting to Google Sheets...")
    sheet = get_google_sheet(google_sheet_id, google_creds_file)
    existing_dates = get_existing_dates(sheet)
    print(f"Found {len(existing_dates)} existing rows in spreadsheet")

    # Process each date
    print("\nProcessing dates:")
    for date in dates_to_process:
        print(f"\nDate: {date}")

        # Fetch totals from both databases
        juan_total = fetch_order_total(juan_conn, date)
        print(f"  Juan's total: {juan_total}")

        texans_total = fetch_order_total(texans_conn, date)
        print(f"  Texans total: {texans_total}")

        # Update or append to Google Sheets
        update_or_append_row(
            sheet,
            date,
            juan_total,
            texans_total,
            existing_dates,
            overwrite
        )

        # Update existing_dates dict if we added a new row
        if date not in existing_dates:
            # Approximate row number (actual row number will be at the end)
            existing_dates[date] = len(existing_dates) + 1

    # Close database connections
    juan_conn.close()
    texans_conn.close()

    print("\nDone!")


if __name__ == '__main__':
    main()
