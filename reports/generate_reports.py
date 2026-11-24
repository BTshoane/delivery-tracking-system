from pathlib import Path
from datetime import date, timedelta
from html import escape

from database.connection import get_connection


def generate_weekly_report():
    today = date.today()
    week_start = today - timedelta(days=today.weekday())
    week_end = week_start + timedelta(days=6)

    connection = get_connection()
    if connection is None:
        raise RuntimeError("Could not connect to database.")

    cursor = connection.cursor()
    try:
        cursor.execute(
            """SELECT status, COUNT(*) FROM deliveries
               WHERE delivery_date BETWEEN %s AND %s
               GROUP BY status ORDER BY status""",
            (week_start, week_end)
        )
        summary = cursor.fetchall()

        cursor.execute(
            """SELECT d.delivery_id, c.full_name,
                      COALESCE(dr.full_name, 'Unassigned'),
                      d.delivery_date, d.status
               FROM deliveries d
               JOIN customers c ON c.customer_id=d.customer_id
               LEFT JOIN drivers dr ON dr.driver_id=d.driver_id
               WHERE d.delivery_date BETWEEN %s AND %s
               ORDER BY d.delivery_date, d.delivery_id""",
            (week_start, week_end)
        )
        deliveries = cursor.fetchall()
    finally:
        cursor.close()
        connection.close()

    total = sum(row[1] for row in summary)
    summary_rows = "".join(
        f"<tr><td>{escape(str(status))}</td><td>{count}</td></tr>"
        for status, count in summary
    ) or '<tr><td colspan="2">No deliveries recorded this week.</td></tr>'

    detail_rows = "".join(
        "<tr>"
        f"<td>{delivery_id}</td><td>{escape(customer)}</td>"
        f"<td>{escape(driver)}</td><td>{delivery_date}</td>"
        f"<td>{escape(status)}</td></tr>"
        for delivery_id, customer, driver, delivery_date, status in deliveries
    ) or '<tr><td colspan="5">No deliveries recorded this week.</td></tr>'

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Weekly Delivery Performance Report</title>
<style>
body {{ font-family: Arial, sans-serif; margin: 35px; color: #172B4D; }}
h1 {{ color: #172B4D; }}
p {{ color: #526078; }}
table {{ border-collapse: collapse; width: 100%; margin: 18px 0 30px; }}
th, td {{ border: 1px solid #dce2ea; padding: 10px; text-align: left; }}
th {{ background: #172B4D; color: white; }}
tr:nth-child(even) {{ background: #f3f5f9; }}
</style>
</head>
<body>
<h1>Weekly Delivery Performance Report</h1>
<p>Reporting period: {week_start} to {week_end}</p>
<p>Total deliveries scheduled this week: <strong>{total}</strong></p>
<h2>Delivery status summary</h2>
<table><tr><th>Status</th><th>Number of deliveries</th></tr>
{summary_rows}</table>
<h2>Delivery details</h2>
<table>
<tr><th>ID</th><th>Customer</th><th>Driver</th><th>Delivery date</th><th>Status</th></tr>
{detail_rows}
</table>
</body>
</html>"""

    output_dir = Path(__file__).resolve().parent.parent / "generated_reports"
    output_dir.mkdir(exist_ok=True)
    output_path = output_dir / f"weekly_report_{today.isoformat()}.html"
    output_path.write_text(html, encoding="utf-8")
    return str(output_path)


if __name__ == "__main__":
    print("Report generated:", generate_weekly_report())
