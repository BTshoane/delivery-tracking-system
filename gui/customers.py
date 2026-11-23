import tkinter as tk
from tkinter import ttk, messagebox
from database.connection import get_connection


class CustomersWindow:
    def __init__(self, parent):
        self.window = tk.Toplevel(parent)
        self.window.title("Manage Customers")
        self.window.geometry("850x560")
        self.window.transient(parent)

        form = tk.LabelFrame(self.window, text="Customer details", padx=10, pady=10)
        form.pack(fill="x", padx=12, pady=10)

        self.entries = {}
        fields = [("Full name", "full_name"), ("Email", "email"),
                  ("Phone", "phone"), ("Address", "address")]
        for row, (label, key) in enumerate(fields):
            tk.Label(form, text=label).grid(row=row, column=0, sticky="w", pady=4)
            entry = tk.Entry(form, width=55)
            entry.grid(row=row, column=1, sticky="w", pady=4)
            self.entries[key] = entry

        buttons = tk.Frame(self.window)
        buttons.pack(fill="x", padx=12)
        tk.Button(buttons, text="Add Customer", command=self.add_customer).pack(side="left", padx=4)
        tk.Button(buttons, text="Update Selected", command=self.update_customer).pack(side="left", padx=4)
        tk.Button(buttons, text="Delete Selected", command=self.delete_customer).pack(side="left", padx=4)
        tk.Button(buttons, text="Clear", command=self.clear_form).pack(side="left", padx=4)

        self.tree = ttk.Treeview(
            self.window, columns=("id", "name", "email", "phone", "address"),
            show="headings", height=12
        )
        for col, heading, width in [
            ("id", "ID", 45), ("name", "Full name", 150),
            ("email", "Email", 150), ("phone", "Phone", 100),
            ("address", "Address", 300)
        ]:
            self.tree.heading(col, text=heading)
            self.tree.column(col, width=width)
        self.tree.pack(fill="both", expand=True, padx=12, pady=10)
        self.tree.bind("<<TreeviewSelect>>", self.select_customer)
        self.load_customers()

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

    def load_customers(self):
        for item in self.tree.get_children():
            self.tree.delete(item)
        try:
            rows = self.db(
                """SELECT customer_id, full_name, email, phone, address
                   FROM customers ORDER BY customer_id DESC""",
                fetch=True
            )
            for row in rows:
                self.tree.insert("", "end", values=row)
        except Exception as error:
            messagebox.showerror("Database error", str(error), parent=self.window)

    def values(self):
        return {key: entry.get().strip() for key, entry in self.entries.items()}

    def add_customer(self):
        data = self.values()
        if not data["full_name"] or not data["phone"] or not data["address"]:
            messagebox.showwarning(
                "Required fields", "Name, phone and address are required.",
                parent=self.window
            )
            return
        try:
            self.db(
                """INSERT INTO customers (full_name, email, phone, address)
                   VALUES (%s, %s, %s, %s)""",
                (data["full_name"], data["email"] or None,
                 data["phone"], data["address"])
            )
            messagebox.showinfo("Success", "Customer added.", parent=self.window)
            self.clear_form()
            self.load_customers()
        except Exception as error:
            messagebox.showerror("Could not add customer", str(error), parent=self.window)

    def selected_id(self):
        selected = self.tree.selection()
        if not selected:
            messagebox.showwarning("Select customer", "Select a customer first.", parent=self.window)
            return None
        return self.tree.item(selected[0], "values")[0]

    def select_customer(self, event=None):
        selected = self.tree.selection()
        if not selected:
            return
        values = self.tree.item(selected[0], "values")
        for key, value in zip(self.entries, values[1:]):
            self.entries[key].delete(0, tk.END)
            self.entries[key].insert(0, value or "")

    def update_customer(self):
        customer_id = self.selected_id()
        if customer_id is None:
            return
        data = self.values()
        if not data["full_name"] or not data["phone"] or not data["address"]:
            messagebox.showwarning("Required fields", "Name, phone and address are required.", parent=self.window)
            return
        try:
            self.db(
                """UPDATE customers SET full_name=%s, email=%s, phone=%s,
                   address=%s WHERE customer_id=%s""",
                (data["full_name"], data["email"] or None, data["phone"],
                 data["address"], customer_id)
            )
            self.load_customers()
            messagebox.showinfo("Updated", "Customer updated.", parent=self.window)
        except Exception as error:
            messagebox.showerror("Update failed", str(error), parent=self.window)

    def delete_customer(self):
        customer_id = self.selected_id()
        if customer_id is None:
            return
        if not messagebox.askyesno(
            "Confirm deletion",
            "Delete this customer? Customers linked to deliveries cannot be deleted.",
            parent=self.window
        ):
            return
        try:
            self.db("DELETE FROM customers WHERE customer_id=%s", (customer_id,))
            self.load_customers()
            self.clear_form()
        except Exception as error:
            messagebox.showerror("Delete failed", str(error), parent=self.window)

    def clear_form(self):
        for entry in self.entries.values():
            entry.delete(0, tk.END)
