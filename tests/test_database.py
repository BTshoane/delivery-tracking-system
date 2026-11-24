import unittest
from database.connection import get_connection


class DatabaseTests(unittest.TestCase):
    def test_database_connection(self):
        connection = get_connection()
        self.assertIsNotNone(connection, "Database connection should succeed.")
        self.assertTrue(connection.is_connected())
        connection.close()

    def test_required_tables_exist(self):
        connection = get_connection()
        self.assertIsNotNone(connection)
        cursor = connection.cursor()
        try:
            cursor.execute("SHOW TABLES")
            tables = {row[0] for row in cursor.fetchall()}
            required = {
                "users", "customers", "drivers",
                "deliveries", "delivery_updates"
            }
            self.assertTrue(required.issubset(tables))
        finally:
            cursor.close()
            connection.close()


if __name__ == "__main__":
    unittest.main()
