import bcrypt
from getpass import getpass
from database.connection import get_connection


def create_admin():
    username = input("Admin username: ").strip()
    full_name = input("Admin full name: ").strip()
    password = getpass("Admin password: ")
    confirm = getpass("Confirm password: ")

    if not username or not full_name or not password:
        print("All fields are required.")
        return
    if password != confirm:
        print("Passwords do not match.")
        return

    connection = get_connection()
    if connection is None:
        print("Could not connect to MySQL.")
        return

    cursor = None
    try:
        cursor = connection.cursor()
        hashed = bcrypt.hashpw(
            password.encode("utf-8"), bcrypt.gensalt()
        ).decode("utf-8")
        cursor.execute(
            """INSERT INTO users (username, password_hash, full_name, role)
               VALUES (%s, %s, %s, 'Admin')""",
            (username, hashed, full_name)
        )
        connection.commit()
        print("Admin account created.")
    except Exception as error:
        connection.rollback()
        print("Could not create account:", error)
    finally:
        if cursor:
            cursor.close()
        connection.close()


if __name__ == "__main__":
    create_admin()
