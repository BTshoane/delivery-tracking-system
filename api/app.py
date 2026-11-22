import os
from functools import wraps
from flask import Flask, request, jsonify
from dotenv import load_dotenv

from database.connection import get_connection

load_dotenv()
app = Flask(__name__)
VALID_STATUSES = {"Pending", "Assigned", "In Transit", "Delivered", "Failed"}


def require_token(function):
    @wraps(function)
    def wrapper(*args, **kwargs):
        expected = os.getenv("API_TOKEN", "")
        supplied = request.headers.get("Authorization", "")
        if not expected or supplied != f"Bearer {expected}":
            return jsonify({"error": "Unauthorized"}), 401
        return function(*args, **kwargs)
    return wrapper


@app.get("/api/health")
def health():
    return jsonify({"status": "running", "service": "Delivery Tracking API"})


@app.get("/api/deliveries/<int:delivery_id>")
@require_token
def get_delivery(delivery_id):
    connection = get_connection()
    if connection is None:
        return jsonify({"error": "Database unavailable"}), 503
    cursor = connection.cursor(dictionary=True)
    try:
        cursor.execute(
            """SELECT d.delivery_id, c.full_name AS customer,
                      dr.full_name AS driver, d.delivery_address,
                      d.delivery_date, d.status
               FROM deliveries d
               JOIN customers c ON c.customer_id=d.customer_id
               LEFT JOIN drivers dr ON dr.driver_id=d.driver_id
               WHERE d.delivery_id=%s""",
            (delivery_id,)
        )
        row = cursor.fetchone()
        if not row:
            return jsonify({"error": "Delivery not found"}), 404
        for key in ("delivery_date",):
            if row.get(key):
                row[key] = row[key].isoformat()
        return jsonify(row)
    finally:
        cursor.close()
        connection.close()


@app.patch("/api/deliveries/<int:delivery_id>/status")
@require_token
def update_status(delivery_id):
    data = request.get_json(silent=True) or {}
    status = data.get("status")
    notes = data.get("notes", "Status updated through API")

    if status not in VALID_STATUSES:
        return jsonify({
            "error": "Invalid status",
            "allowed_statuses": sorted(VALID_STATUSES)
        }), 400

    connection = get_connection()
    if connection is None:
        return jsonify({"error": "Database unavailable"}), 503
    cursor = connection.cursor()
    try:
        cursor.execute(
            "SELECT delivery_id FROM deliveries WHERE delivery_id=%s",
            (delivery_id,)
        )
        if not cursor.fetchone():
            return jsonify({"error": "Delivery not found"}), 404

        cursor.execute("SELECT user_id FROM users ORDER BY user_id LIMIT 1")
        user = cursor.fetchone()
        if not user:
            return jsonify({"error": "Create a staff/admin user first"}), 500

        cursor.execute(
            """UPDATE deliveries SET status=%s,
               delivered_at=CASE WHEN %s='Delivered'
                   THEN COALESCE(delivered_at, NOW()) ELSE delivered_at END
               WHERE delivery_id=%s""",
            (status, status, delivery_id)
        )
        cursor.execute(
            """INSERT INTO delivery_updates (delivery_id, user_id, status, notes)
               VALUES (%s, %s, %s, %s)""",
            (delivery_id, user[0], status, str(notes)[:1000])
        )
        connection.commit()
        return jsonify({
            "message": "Delivery status updated",
            "delivery_id": delivery_id,
            "status": status
        })
    except Exception as error:
        connection.rollback()
        return jsonify({"error": str(error)}), 500
    finally:
        cursor.close()
        connection.close()


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000, debug=False)
