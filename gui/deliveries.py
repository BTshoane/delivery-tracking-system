import tkinter as tk
from tkinter import ttk, messagebox
from datetime import date

from database.connection import get_connection


STATUSES = ["Pending", "Assigned", "In Transit", "Delivered", "Failed"]


class DeliveriesWindow:
    def __init__(self, parent, username):
        self.username = username
        self.window = tk.Toplevel(parent)
        self.window.title("Manage Deliveries")
        self.window.geometry("1050x650")
        self.window.transient(parent)

        form = tk.LabelFrame(self.window, text="Create / update delivery", padx=10, pady=10)
        form.pack(fill="x", padx=12, pady=10)

        tk.Label(form, text="Customer").grid(row=0, column=0, sticky="w", pady=4)
        self.customer = ttk.Combobox(form, state="readonly", width=35)
        self.customer.grid(row=0, column=1, sticky="w", pady=4)

        tk.Label(form, text="Driver").grid(row=1, column=0, sticky="w", pady=4)
        self.driver = ttk.Combobox(form, state="readonly", width=35)
        self.driver.grid(row=1, column=1, sticky="w", pady=4)

        tk.Label(form, text="Delivery address").grid(row=2, column=0, sticky="w", pady=4)
        self.address = tk.Entry(form, width=55)
        self.address.grid(row=2, column=1, sticky="w", pady=4)

        tk.Label(form, text="Delivery date (YYYY-MM-DD)").grid(row=3, column=0, sticky="w", pady=4)
        self.delivery_date = tk.Entry(form, width=38)
        self.delivery_date.insert(0, date.today().isoformat())
        self.delivery_date.grid(row=3, column=1, sticky="w", pady=4)

        tk.Label(form, text="Expected date (YYYY-MM-DD)").grid(row=4, column=0, sticky="w", pady=4)
        self.expected_date = tk.Entry(form, width=38)
        self.expected_date.grid(row=4, column=1, sticky="w", pady=4)

        tk.Label(form, text="Status").grid(row=5, column=0, sticky="w", pady=4)
        self.status = ttk.Combobox(form, values=STATUSES, state="readonly", width=35)
        self.status.set("Pending")
        self.status.grid(row=5, column=1, sticky="w", pady=4)

        buttons = tk.Frame(self.window)
        buttons.pack(fill="x", padx=12, pady=4)
        tk.Button(buttons, text="Create Delivery", command=self.create_delivery).pack(side="left", padx=4)
        tk.Button(buttons, text="Assign / Update Selected", command=self.update_delivery).pack(side="left", padx=4)
        tk.Button(buttons, text="Refresh", command=self.load_deliveries).pack(side="left", padx=4)
        tk.Button(buttons, text="Clear", command=self.clear_form).pack(side="left", padx=4)

        self.tree = ttk.Treeview(
            self.window,
            columns=("id", "customer", "driver", "address", "date", "status"),
            show="headings", height=13
        )
        for col, heading, width in [
            ("id", "Delivery ID", 75), ("customer", "Customer", 145),
            ("driver", "Driver", 145), ("address", "Delivery address", 300),
            ("date", "Delivery date", 110), ("status", "Status", 110)
        ]:
            self.tree.heading(col, text=heading)
            self.tree.column(col, width=width)
        self.tree.pack(fill="both", expand=True, padx=12, pady=10)
        self.tree.bind("<<TreeviewSelect>>", self.select_delivery)

        self.customer_map = {}
        self.driver_map = {}
        self.load_options()
        self.load_deliveries()

    def connection(self):
        connection = get_connection()
        if connection is None:
            raise RuntimeError("Database connection failed.")
        return connection

    def load_options(self):
        connection = self.connection()
        cursor = connection.cursor()
        try:
            cursor.execute("SELECT customer_id, full_name FROM customers ORDER BY full_name")
            customers = cursor.fetchall()
            self.customer_map = {f"{row[0]} - {row[1]}": row[0] for row in customers}
            self.customer["values"] = list(self.customer_map.keys())

            cursor.execute(
                """SELECT driver_id, full_name FROM drivers
                   WHERE availability='Available' ORDER BY full_name"""
            )
            drivers = cursor.fetchall()
            self.driver_map = {"Unassigned": None}
            self.driver_map.update({f"{row[0]} - {row[1]}": row[0] for row in drivers})
            self.driver["values"] = list(self.driver_map.keys())
            self.driver.set("Unassigned")
        except Exception as error:
            messagebox.showerror("Could not load options", str(error), parent=self.window)
        finally:
            cursor.close()
            connection.close()

    def load_deliveries(self):
        for item in self.tree.get_children():
            self.tree.delete(item)
        connection = self.connection()
        cursor = connection.cursor()
        try:
            cursor.execute(
                """SELECT d.delivery_id, c.full_name,
                          COALESCE(dr.full_name, 'Unassigned'),
                          d.delivery_address, d.delivery_date, d.status
                   FROM deliveries d
                   JOIN customers c ON d.customer_id=c.customer_id
                   LEFT JOIN drivers dr ON d.driver_id=dr.driver_id
                   ORDER BY d.delivery_id DESC"""
            )
            for row in cursor.fetchall():
                self.tree.insert("", "end", values=row)
        except Exception as error:
            messagebox.showerror("Could not load deliveries", str(error), parent=self.window)
        finally:
            cursor.close()
            connection.close()
        self.load_options()

    def form_values(self):
        customer_key = self.customer.get()
        if customer_key not in self.customer_map:
            raise ValueError("Select a customer.")
        driver_key = self.driver.get() or "Unassigned"
        if driver_key not in self.driver_map:
            raise ValueError("Select a valid driver.")
        address = self.address.get().strip()
        if not address:
            raise ValueError("Delivery address is required.")
        try:
            delivery_date = date.fromisoformat(self.delivery_date.get().strip())
            expected = self.expected_date.get().strip()
            expected_date = date.fromisoformat(expected) if expected else None
        except ValueError:
            raise ValueError("Dates must use YYYY-MM-DD format.")
        if self.status.get() not in STATUSES:
            raise ValueError("Select a valid status.")
        return (
            self.customer_map[customer_key], self.driver_map[driver_key],
            address, delivery_date, expected_date, self.status.get()
        )

    def create_delivery(self):
        try:
            customer_id, driver_id, address, delivery_date, expected, status = self.form_values()
            if driver_id is not None and status == "Pending":
                status = "Assigned"
            connection = self.connection()
            cursor = connection.cursor()
            try:
                cursor.execute(
                    """INSERT INTO deliveries
                       (customer_id, driver_id, delivery_address, delivery_date,
                        expected_delivery_date, status)
                       VALUES (%s, %s, %s, %s, %s, %s)""",
                    (customer_id, driver_id, address, delivery_date, expected, status)
                )
                delivery_id = cursor.lastrowid
                if driver_id is not None:
                    cursor.execute(
                        "UPDATE drivers SET availability='Unavailable' WHERE driver_id=%s",
                        (driver_id,)
                    )
                user_id = self.get_user_id(cursor)
                cursor.execute(
                    """INSERT INTO delivery_updates
                       (delivery_id, user_id, status, notes)
                       VALUES (%s, %s, %s, %s)""",
                    (delivery_id, user_id, status, "Delivery created")
                )
                connection.commit()
            except Exception:
                connection.rollback()
                raise
            finally:
                cursor.close()
                connection.close()
            self.load_deliveries()
            self.clear_form()
            messagebox.showinfo("Success", f"Delivery #{delivery_id} created.", parent=self.window)
        except Exception as error:
            messagebox.showerror("Could not create delivery", str(error), parent=self.window)

    def get_user_id(self, cursor):
        cursor.execute("SELECT user_id FROM users WHERE username=%s", (self.username,))
        row = cursor.fetchone()
        if not row:
            raise RuntimeError("The logged-in user was not found.")
        return row[0]

    def selected_delivery_id(self):
        selected = self.tree.selection()
        if not selected:
            messagebox.showwarning("Select delivery", "Select a delivery first.", parent=self.window)
            return None
        return int(self.tree.item(selected[0], "values")[0])

    def select_delivery(self, event=None):
        selected = self.tree.selection()
        if not selected:
            return
        values = self.tree.item(selected[0], "values")
        delivery_id = int(values[0])
        connection = self.connection()
        cursor = connection.cursor()
        try:
            cursor.execute(
                """SELECT customer_id, driver_id, delivery_address,
                          delivery_date, expected_delivery_date, status
                   FROM deliveries WHERE delivery_id=%s""",
                (delivery_id,)
            )
            row = cursor.fetchone()
            if not row:
                return
            customer_id, driver_id, address, delivery_date, expected, status = row
            for key, value in self.customer_map.items():
                if value == customer_id:
                    self.customer.set(key)
                    break
            self.driver.set("Unassigned")
            for key, value in self.driver_map.items():
                if value == driver_id:
                    self.driver.set(key)
                    break
            self.address.delete(0, tk.END)
            self.address.insert(0, address)
            self.delivery_date.delete(0, tk.END)
            self.delivery_date.insert(0, str(delivery_date))
            self.expected_date.delete(0, tk.END)
            self.expected_date.insert(0, str(expected) if expected else "")
            self.status.set(status)
        finally:
            cursor.close()
            connection.close()

    def update_delivery(self):
        delivery_id = self.selected_delivery_id()
        if delivery_id is None:
            return
        try:
            customer_id, driver_id, address, delivery_date, expected, status = self.form_values()
            connection = self.connection()
            cursor = connection.cursor()
            try:
                cursor.execute(
                    "SELECT driver_id FROM deliveries WHERE delivery_id=%s",
                    (delivery_id,)
                )
                old = cursor.fetchone()
                if not old:
                    raise ValueError("Delivery no longer exists.")
                old_driver = old[0]

                cursor.execute(
                    """UPDATE deliveries SET customer_id=%s, driver_id=%s,
                       delivery_address=%s, delivery_date=%s,
                       expected_delivery_date=%s, status=%s,
                       delivered_at=CASE WHEN %s='Delivered'
                           THEN COALESCE(delivered_at, NOW()) ELSE delivered_at END
                       WHERE delivery_id=%s""",
                    (customer_id, driver_id, address, delivery_date,
                     expected, status, status, delivery_id)
                )

                if old_driver and old_driver != driver_id:
                    cursor.execute(
                        "UPDATE drivers SET availability='Available' WHERE driver_id=%s",
                        (old_driver,)
                    )
                if driver_id:
                    cursor.execute(
                        "UPDATE drivers SET availability='Unavailable' WHERE driver_id=%s",
                        (driver_id,)
                    )

                user_id = self.get_user_id(cursor)
                cursor.execute(
                    """INSERT INTO delivery_updates
                       (delivery_id, user_id, status, notes)
                       VALUES (%s, %s, %s, %s)""",
                    (delivery_id, user_id, status, "Delivery details/status updated")
                )
                connection.commit()
            except Exception:
                connection.rollback()
                raise
            finally:
                cursor.close()
                connection.close()

            self.load_deliveries()
            messagebox.showinfo("Updated", f"Delivery #{delivery_id} updated.", parent=self.window)
        except Exception as error:
            messagebox.showerror("Update failed", str(error), parent=self.window)

    def clear_form(self):
        self.customer.set("")
        self.driver.set("Unassigned")
        self.address.delete(0, tk.END)
        self.delivery_date.delete(0, tk.END)
        self.delivery_date.insert(0, date.today().isoformat())
        self.expected_date.delete(0, tk.END)
        self.status.set("Pending")
