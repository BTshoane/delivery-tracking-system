import tkinter as tk
from tkinter import messagebox
import bcrypt

from database.connection import get_connection
from gui.dashboard import DashboardWindow


class LoginWindow:
    def __init__(self, root):
        self.root = root
        self.root.title("Delivery Tracking System - Login")
        self.root.geometry("420x330")
        self.root.resizable(False, False)
        self.root.configure(bg="#F3F5F9")

        tk.Label(
            root, text="Delivery Tracking System",
            font=("Arial", 18, "bold"), bg="#F3F5F9", fg="#172B4D"
        ).pack(pady=(35, 25))

        tk.Label(root, text="Username", bg="#F3F5F9").pack()
        self.username_entry = tk.Entry(root, width=32)
        self.username_entry.pack(pady=6)

        tk.Label(root, text="Password", bg="#F3F5F9").pack()
        self.password_entry = tk.Entry(root, width=32, show="*")
        self.password_entry.pack(pady=6)
        self.password_entry.bind("<Return>", lambda event: self.login())

        tk.Button(
            root, text="Login", width=22, bg="#2563A6", fg="white",
            command=self.login
        ).pack(pady=22)

    def login(self):
        username = self.username_entry.get().strip()
        password = self.password_entry.get()

        if not username or not password:
            messagebox.showwarning(
                "Missing information", "Enter your username and password."
            )
            return

        connection = get_connection()
        if connection is None:
            messagebox.showerror(
                "Database error", "Could not connect to the database."
            )
            return

        cursor = None
        try:
            cursor = connection.cursor()
            cursor.execute(
                "SELECT password_hash FROM users WHERE username = %s",
                (username,)
            )
            result = cursor.fetchone()

            if result and bcrypt.checkpw(
                password.encode("utf-8"), result[0].encode("utf-8")
            ):
                DashboardWindow(self.root, username)
            else:
                messagebox.showerror(
                    "Login failed", "Invalid username or password."
                )
        except Exception as error:
            messagebox.showerror("Login error", str(error))
        finally:
            if cursor:
                cursor.close()
            connection.close()
