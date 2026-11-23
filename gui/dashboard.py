import tkinter as tk
from tkinter import messagebox

from database.connection import get_connection
from gui.customers import CustomersWindow
from gui.drivers import DriversWindow
from gui.deliveries import DeliveriesWindow
from reports.generate_report import generate_weekly_report


class DashboardWindow:
    def __init__(self, root, username):
        self.root = root
        self.username = username
        for widget in self.root.winfo_children():
            widget.destroy()

        self.root.title("Delivery Tracking System")
        self.root.geometry("1080x700")
        self.root.minsize(900, 600)
        self.root.configure(bg="#F3F5F9")
        self.build()

    def build(self):
        header = tk.Frame(self.root, bg="#172B4D", height=75)
        header.pack(fill="x")
        header.pack_propagate(False)

        tk.Label(
            header, text="DELIVERY TRACKING SYSTEM",
            font=("Arial", 17, "bold"), fg="white", bg="#172B4D"
        ).pack(side="left", padx=25, pady=20)
        tk.Label(
            header, text=f"Signed in: {self.username}",
            fg="white", bg="#172B4D", font=("Arial", 10)
        ).pack(side="right", padx=25)

        body = tk.Frame(self.root, bg="#F3F5F9")
        body.pack(fill="both", expand=True)

        sidebar = tk.Frame(body, bg="white", width=220)
        sidebar.pack(side="left", fill="y")
        sidebar.pack_propagate(False)

        tk.Label(
            sidebar, text="MAIN MENU", bg="white", fg="#7A8495",
            font=("Arial", 11, "bold")
        ).pack(anchor="w", padx=20, pady=(25, 15))

        menu = [
            ("Dashboard", self.refresh_dashboard),
            ("Manage Customers", self.open_customers),
            ("Manage Drivers", self.open_drivers),
            ("Manage Deliveries", self.open_deliveries),
            ("Weekly Reports", self.open_report)
        ]
        for label, command in menu:
            tk.Button(
                sidebar, text=label, anchor="w", command=command,
                bg="white", fg="#172B4D", relief="flat",
                activebackground="#E8EEF8", padx=20, pady=14
            ).pack(fill="x", padx=8, pady=2)

        tk.Button(
            sidebar, text="Logout", command=self.logout,
            bg="#FCE8E8", fg="#9B2226", relief="flat",
            padx=20, pady=12
        ).pack(side="bottom", fill="x", padx=8, pady=15)

        self.main = tk.Frame(body, bg="#F3F5F9")
        self.main.pack(side="left", fill="both", expand=True, padx=30, pady=28)
        self.refresh_dashboard()

    def clear_main(self):
        for widget in self.main.winfo_children():
            widget.destroy()

    def count(self, sql, params=()):
        connection = get_connection()
        if connection is None:
            return 0
        cursor = None
        try:
            cursor = connection.cursor()
            cursor.execute(sql, params)
            return cursor.fetchone()[0]
        except Exception as error:
            print("Dashboard query error:", error)
            return 0
        finally:
            if cursor:
                cursor.close()
            connection.close()

    def refresh_dashboard(self):
        self.clear_main()
        tk.Label(
            self.main, text="Dashboard Overview",
            font=("Arial", 23, "bold"), fg="#172B4D", bg="#F3F5F9"
        ).pack(anchor="w")
        tk.Label(
            self.main, text="Monitor your delivery operations at a glance.",
            font=("Arial", 11), fg="#7A8495", bg="#F3F5F9"
        ).pack(anchor="w", pady=(5, 25))

        stats = [
            ("Total Deliveries", self.count("SELECT COUNT(*) FROM deliveries")),
            ("Pending Deliveries", self.count(
                "SELECT COUNT(*) FROM deliveries WHERE status='Pending'")),
            ("Delivered", self.count(
                "SELECT COUNT(*) FROM deliveries WHERE status='Delivered'")),
            ("Registered Drivers", self.count("SELECT COUNT(*) FROM drivers"))
        ]
        cards = tk.Frame(self.main, bg="#F3F5F9")
        cards.pack(fill="x")
        for index, (label, value) in enumerate(stats):
            card = tk.Frame(
                cards, bg="white", padx=16, pady=22,
                highlightbackground="#E0E5ED", highlightthickness=1
            )
            card.grid(row=0, column=index, padx=6, sticky="nsew")
            cards.grid_columnconfigure(index, weight=1)
            tk.Label(
                card, text=label, bg="white", fg="#7A8495"
            ).pack(anchor="w")
            tk.Label(
                card, text=str(value), bg="white", fg="#172B4D",
                font=("Arial", 23, "bold")
            ).pack(anchor="w", pady=(9, 0))

        tk.Label(
            self.main, text="Quick Actions", font=("Arial", 16, "bold"),
            bg="#F3F5F9", fg="#172B4D"
        ).pack(anchor="w", pady=(38, 15))

        actions = tk.Frame(self.main, bg="#F3F5F9")
        actions.pack(anchor="w")
        for label, command in [
            ("Customers", self.open_customers),
            ("Drivers", self.open_drivers),
            ("Deliveries", self.open_deliveries)
        ]:
            tk.Button(
                actions, text=label, command=command,
                bg="#2563A6", fg="white", relief="flat",
                padx=18, pady=12
            ).pack(side="left", padx=(0, 10))

    def open_customers(self):
        CustomersWindow(self.root)

    def open_drivers(self):
        DriversWindow(self.root)

    def open_deliveries(self):
        DeliveriesWindow(self.root, self.username)

    def open_report(self):
        try:
            path = generate_weekly_report()
            messagebox.showinfo(
                "Report generated",
                f"Weekly report saved to:\n{path}"
            )
        except Exception as error:
            messagebox.showerror("Report error", str(error))

    def logout(self):
        from gui.login import LoginWindow
        for widget in self.root.winfo_children():
            widget.destroy()
        LoginWindow(self.root)
