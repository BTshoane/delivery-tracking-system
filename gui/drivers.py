import tkinter as tk
from tkinter import ttk, messagebox
from database.connection import get_connection


class DriversWindow:
    def __init__(self, parent):
        self.window = tk.Toplevel(parent)
        self.window.title("Manage Drivers")
        self.window.geometry("820x540")
        self.window.transient(parent)

        form = tk.LabelFrame(self.window, text="Driver details", padx=10, pady=10)
        form.pack(fill="x", padx=12, pady=10)

        self.entries = {}
        for row, (label, key) in enumerate([
            ("Full name", "full_name"),
            ("Phone", "phone"),
            ("Licence number", "licence_number")
        ]):
            tk.Label(form, text=label).grid(row=row, column=0, sticky="w", pady=4)
            entry = tk.Entry(form, width=40)
            entry.grid(row=row, column=1, sticky="w", pady=4)
            self.entries[key] = entry

        tk.Label(form, text="Availability").grid(row=3, column=0, sticky="w")
        self.availability = ttk.Combobox(
            form, values=["Available", "Unavailable"],
            state="readonly", width=37
        )
        self.availability.set("Available")
        self.availability.grid(row=3, column=1, sticky="w")

        buttons = tk.Frame(self.window)
        buttons.pack(fill="x", padx=12)
        tk.Button(buttons, text="Add Driver", command=self.add_driver).pack(side="left", padx=4)
        tk.Button(buttons, text="Update Selected", command=self.update_driver).pack(side="left", padx=4)
        tk.Button(buttons, text="Delete Selected", command=self.delete_driver).pack(side="left", padx=4)
        tk.Button(buttons, text="Clear", command=self.clear_form).pack(side="left", padx=4)

        self.tree = ttk.Treeview(
            self.window, columns=("id", "name", "phone", "licence", "availability"),
            show="headings", height=12
        )
        for col, heading, width in [
            ("id", "ID", 45), ("name", "Full name", 180),
            ("phone", "Phone", 130), ("licence", "Licence number", 150),
            ("availability", "Availability", 120)
        ]:
            self.tree.heading(col, text=heading)
            self.tree.column(col, width=width)
        self.tree.pack(fill="both", expand=True, padx=12, pady=10)
        self.tree.bind("<<TreeviewSelect>>", self.select_driver)
        self.load_drivers()

    def db(self, query, params=(), fetch=False):
        connection = get_connection()
        if connection is None:
            raise RuntimeError("Database connection failed.")
        cursor = None
        try:
            cursor = connection.cursor()
            cursor.execute(query, params)
            result = cursor.fetchall() if fetch else None
            if not fetch:
                connection.commit()
            return result
        except Exception:
            connection.rollback()
            raise
        finally:
            if cursor:
                cursor.close()
            connection.close()

    def load_drivers(self):
        for item in self.tree.get_children():
            self.tree.delete(item)
        try:
            rows = self.db(
                """SELECT driver_id, full_name, phone, licence_number, availability
                   FROM drivers ORDER BY driver_id DESC""",
                fetch=True
            )
            for row in rows:
                self.tree.insert("", "end", values=row)
        except Exception as error:
            messagebox.showerror("Database error", str(error), parent=self.window)

    def values(self):
        return {key: entry.get().strip() for key, entry in self.entries.items()}

    def add_driver(self):
        data = self.values()
        if not all(data.values()):
            messagebox.showwarning("Required fields", "Complete all driver fields.", parent=self.window)
            return
        try:
            self.db(
                """INSERT INTO drivers
                   (full_name, phone, licence_number, availability)
                   VALUES (%s, %s, %s, %s)""",
                (data["full_name"], data["phone"], data["licence_number"],
                 self.availability.get())
            )
            self.load_drivers()
            self.clear_form()
            messagebox.showinfo("Success", "Driver added.", parent=self.window)
        except Exception as error:
            messagebox.showerror("Could not add driver", str(error), parent=self.window)

    def selected_id(self):
        selected = self.tree.selection()
        if not selected:
            messagebox.showwarning("Select driver", "Select a driver first.", parent=self.window)
            return None
        return self.tree.item(selected[0], "values")[0]

    def select_driver(self, event=None):
        selected = self.tree.selection()
        if not selected:
            return
        values = self.tree.item(selected[0], "values")
        for key, value in zip(self.entries, values[1:4]):
            self.entries[key].delete(0, tk.END)
            self.entries[key].insert(0, value)
        self.availability.set(values[4])

    def update_driver(self):
        driver_id = self.selected_id()
        if driver_id is None:
            return
        data = self.values()
        if not all(data.values()):
            messagebox.showwarning("Required fields", "Complete all driver fields.", parent=self.window)
            return
        try:
            self.db(
                """UPDATE drivers SET full_name=%s, phone=%s,
                   licence_number=%s, availability=%s WHERE driver_id=%s""",
                (data["full_name"], data["phone"], data["licence_number"],
                 self.availability.get(), driver_id)
            )
            self.load_drivers()
            messagebox.showinfo("Updated", "Driver updated.", parent=self.window)
        except Exception as error:
            messagebox.showerror("Update failed", str(error), parent=self.window)

    def delete_driver(self):
        driver_id = self.selected_id()
        if driver_id is None:
            return
        if not messagebox.askyesno(
            "Confirm deletion",
            "Delete this driver? Drivers assigned to deliveries cannot be deleted.",
            parent=self.window
        ):
            return
        try:
            self.db("DELETE FROM drivers WHERE driver_id=%s", (driver_id,))
            self.load_drivers()
            self.clear_form()
        except Exception as error:
            messagebox.showerror("Delete failed", str(error), parent=self.window)

    def clear_form(self):
        for entry in self.entries.values():
            entry.delete(0, tk.END)
        self.availability.set("Available")
