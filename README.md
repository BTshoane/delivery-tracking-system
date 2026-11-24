# Delivery Tracking System

A Python desktop application for managing customers, drivers and deliveries.
It uses Tkinter for the graphical user interface, MySQL for persistent storage,
Flask for a REST API, and HTML for weekly delivery performance reports.

## Features

- Staff/admin login with bcrypt password hashing.
- Dashboard showing delivery and driver totals.
- Add, view, update and delete customer records.
- Add, view, update and delete driver records.
- Create deliveries, assign available drivers and update delivery statuses.
- Delivery status history stored in `delivery_updates`.
- Flask API for retrieving a delivery and remotely updating its status.
- Weekly HTML report grouped by delivery status.
- Primary key on `delivery_id` and indexes on delivery status and update lookups.

## Requirements

- Python 3.10 or later
- MySQL Server 8.0 or later

## Setup

1. Create and activate a virtual environment.
2. Install packages: `py -m pip install -r requirements.txt`
3. Copy `.env.example` to `.env` and enter your own MySQL credentials.
4. Run `database/schema.sql` in MySQL Workbench or the MySQL client.
5. Create an admin account: `py -m database.create_admin`
6. Start the desktop application: `py main.py`

Do not submit your real `.env` file or disclose your database password.

## Flask API

Set a long private `API_TOKEN` in `.env`, then start the API:

`py -m api.app`

Health check: `GET http://127.0.0.1:5000/api/health`

Retrieve a delivery:
`GET http://127.0.0.1:5000/api/deliveries/1`

Update a delivery status:
`PATCH http://127.0.0.1:5000/api/deliveries/1/status`

Send the header:
`Authorization: Bearer YOUR_API_TOKEN`

Send JSON:
`{"status": "In Transit", "notes": "Collected by driver"}`

Allowed statuses: Pending, Assigned, In Transit, Delivered, Failed.

## Weekly report

Use the Weekly Reports menu in the dashboard or run:

`py -m reports.generate_report`

The HTML file is saved in `generated_reports`.

## Tests

Run:

`py -m unittest tests.test_database -v`

## Database relationships

- One customer can have many deliveries.
- One driver can be assigned to many deliveries over time.
- One delivery can have many delivery status updates.
- One user can record many delivery status updates.

## Important

Test the application with sample data before demonstrating it. Use fictional customer
and driver details in screenshots. The API binds to localhost by default and should not
be exposed publicly without additional deployment security.
