#!/usr/bin/env python3
"""
contact_manager.py
Author : Sadgyan Singh
Date   : 2025-11-20
Project: Contact Book - File Handling System (CSV & JSON)
Course : Programming for Problem Solving Using Python (ETCCPP171)

Features:
- Add, View, Search, Update, Delete contacts (CSV-backed)
- Export to / Import from JSON
- Error logging to error_log.txt with timestamps
- Robust exception handling and neat tabular display
"""

import csv
import json
import os
import sys
from datetime import datetime

CSV_FILE = "contacts.csv"
JSON_FILE = "contacts.json"
ERROR_LOG = "error_log.txt"
CSV_FIELDS = ["name", "phone", "email"]


# -------------------------
# Utility: Error logging
# -------------------------
def log_error(operation: str, err: Exception):
    """Append a structured error entry to ERROR_LOG"""
    try:
        with open(ERROR_LOG, "a", encoding="utf-8") as f:
            ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            f.write(f"[{ts}] Operation: {operation} | Error: {repr(err)}\n")
    except Exception:
        # If logging fails, print to stderr but don't crash program
        print("Failed to write to error log.", file=sys.stderr)


# -------------------------
# CSV I/O helpers
# -------------------------
def ensure_csv_exists():
    """Ensure CSV file exists and has header row."""
    if not os.path.exists(CSV_FILE):
        try:
            with open(CSV_FILE, "w", newline="", encoding="utf-8") as f:
                writer = csv.DictWriter(f, fieldnames=CSV_FIELDS)
                writer.writeheader()
        except Exception as e:
            log_error("ensure_csv_exists", e)
            raise


def load_contacts_from_csv():
    """Return list of contacts (each is a dict) from CSV file."""
    ensure_csv_exists()
    contacts = []
    try:
        with open(CSV_FILE, newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                if row and any(row.values()):
                    contacts.append({k: (v or "").strip() for k, v in row.items()})
    except Exception as e:
        log_error("load_contacts_from_csv", e)
        raise
    return contacts


def save_contacts_to_csv(contacts):
    """Overwrite CSV with contacts list."""
    try:
        with open(CSV_FILE, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=CSV_FIELDS)
            writer.writeheader()
            for c in contacts:
                writer.writerow({k: c.get(k, "") for k in CSV_FIELDS})
    except Exception as e:
        log_error("save_contacts_to_csv", e)
        raise


# -------------------------
# Core CRUD operations
# -------------------------
def add_contact():
    """Add a new contact (asks user for input)."""
    try:
        name = input("Enter name: ").strip()
        if not name:
            print("Name cannot be empty.")
            return
        phone = input("Enter phone number: ").strip()
        email = input("Enter email address: ").strip()

        contacts = load_contacts_from_csv()
        # prevent duplicate name (case-insensitive)
        if any(c["name"].lower() == name.lower() for c in contacts):
            print(f"A contact with name '{name}' already exists. Use update option instead.")
            return

        contact = {"name": name, "phone": phone, "email": email}
        contacts.append(contact)
        save_contacts_to_csv(contacts)
        print(f"Contact '{name}' added successfully.")
    except Exception as e:
        log_error("add_contact", e)
        print("Failed to add contact. Check error log.")


def display_contacts():
    """Read and display all contacts in neat table format."""
    try:
        contacts = load_contacts_from_csv()
        if not contacts:
            print("No contacts found.")
            return

        # Determine column widths
        name_w = max(len("Name"), *(len(c["name"]) for c in contacts))
        phone_w = max(len("Phone"), *(len(c["phone"]) for c in contacts))
        email_w = max(len("Email"), *(len(c["email"]) for c in contacts))

        # Header
        print(f"\n{'Name'.ljust(name_w)}\t{'Phone'.ljust(phone_w)}\t{'Email'.ljust(email_w)}")
        print("-" * (name_w + phone_w + email_w + 8))
        for c in contacts:
            print(f"{c['name'].ljust(name_w)}\t{c['phone'].ljust(phone_w)}\t{c['email'].ljust(email_w)}")
        print()
    except Exception as e:
        log_error("display_contacts", e)
        print("Unable to display contacts. Check error log.")


def search_contact():
    """Search for a contact by name (case-insensitive) and display details."""
    try:
        key = input("Enter name to search: ").strip()
        if not key:
            print("Search term cannot be empty.")
            return

        contacts = load_contacts_from_csv()
        found = [c for c in contacts if c["name"].lower() == key.lower()]
        if not found:
            print(f"No contact found with name '{key}'.")
            return

        print("\nFound contact(s):")
        for c in found:
            print(f"Name : {c['name']}")
            print(f"Phone: {c['phone']}")
            print(f"Email: {c['email']}")
            print("-" * 30)
    except Exception as e:
        log_error("search_contact", e)
        print("Search failed. Check error log.")


def update_contact():
    """Update phone and/or email of a contact identified by name."""
    try:
        key = input("Enter name of contact to update: ").strip()
        if not key:
            print("Name cannot be empty.")
            return

        contacts = load_contacts_from_csv()
        updated = False
        for c in contacts:
            if c["name"].lower() == key.lower():
                print(f"Current phone: {c['phone']}")
                new_phone = input("Enter new phone (press Enter to keep current): ").strip()
                if new_phone:
                    c["phone"] = new_phone

                print(f"Current email: {c['email']}")
                new_email = input("Enter new email (press Enter to keep current): ").strip()
                if new_email:
                    c["email"] = new_email

                updated = True
                break

        if not updated:
            print(f"No contact found with name '{key}'.")
            return

        save_contacts_to_csv(contacts)
        print(f"Contact '{key}' updated successfully.")
    except Exception as e:
        log_error("update_contact", e)
        print("Failed to update contact. Check error log.")


def delete_contact():
    """Delete a contact by name."""
    try:
        key = input("Enter name of contact to delete: ").strip()
        if not key:
            print("Name cannot be empty.")
            return

        contacts = load_contacts_from_csv()
        new_contacts = [c for c in contacts if c["name"].lower() != key.lower()]

        if len(new_contacts) == len(contacts):
            print(f"No contact found with name '{key}'.")
            return

        save_contacts_to_csv(new_contacts)
        print(f"Contact '{key}' deleted successfully.")
    except Exception as e:
        log_error("delete_contact", e)
        print("Failed to delete contact. Check error log.")


# -------------------------
# JSON export/import
# -------------------------
def export_to_json():
    """Export CSV contacts to contacts.json with pretty formatting."""
    try:
        contacts = load_contacts_from_csv()
        if not contacts:
            print("No contacts to export.")
            return
        with open(JSON_FILE, "w", encoding="utf-8") as f:
            json.dump(contacts, f, indent=4, ensure_ascii=False)
        print(f"Exported {len(contacts)} contact(s) to '{JSON_FILE}'.")
    except Exception as e:
        log_error("export_to_json", e)
        print("Failed to export to JSON. Check error log.")


def import_from_json():
    """Load contacts from JSON and show them (does not automatically overwrite CSV)."""
    try:
        if not os.path.exists(JSON_FILE):
            print(f"JSON file '{JSON_FILE}' not found.")
            return
        with open(JSON_FILE, "r", encoding="utf-8") as f:
            contacts = json.load(f)
        if not contacts:
            print("JSON file is empty.")
            return

        # Show loaded contacts
        print(f"Loaded {len(contacts)} contact(s) from '{JSON_FILE}':")
        name_w = max(len("Name"), *(len(c.get("name", "")) for c in contacts))
        phone_w = max(len("Phone"), *(len(c.get("phone", "")) for c in contacts))
        email_w = max(len("Email"), *(len(c.get("email", "")) for c in contacts))
        print(f"\n{'Name'.ljust(name_w)}\t{'Phone'.ljust(phone_w)}\t{'Email'.ljust(email_w)}")
        print("-" * (name_w + phone_w + email_w + 8))
        for c in contacts:
            print(f"{c.get('name','').ljust(name_w)}\t{c.get('phone','').ljust(phone_w)}\t{c.get('email','').ljust(email_w)}")
        print()
    except Exception as e:
        log_error("import_from_json", e)
        print("Failed to import JSON. Check error log.")


# -------------------------
# Menu & main
# -------------------------
def print_welcome():
    print("========================================")
    print("   Contact Book — CSV & JSON Manager")
    print("   (Add / View / Search / Update / Delete)")
    print("========================================\n")
    print("This tool stores contacts in 'contacts.csv'. You can also export to/import from 'contacts.json'.")
    print("All exceptions are logged in 'error_log.txt'.\n")


def print_menu():
    print("Menu:")
    print("1. Add contact")
    print("2. View all contacts")
    print("3. Search contact by name")
    print("4. Update contact")
    print("5. Delete contact")
    print("6. Export contacts to JSON")
    print("7. Load & display contacts from JSON")
    print("8. Exit")


def main():
    try:
        ensure_csv_exists()
    except Exception as e:
        print("Fatal: cannot initialize CSV file. Exiting.")
        return

    print_welcome()
    while True:
        print_menu()
        choice = input("Choose an option (1-8): ").strip()
        if choice == "1":
            add_contact()
        elif choice == "2":
            display_contacts()
        elif choice == "3":
            search_contact()
        elif choice == "4":
            update_contact()
        elif choice == "5":
            delete_contact()
        elif choice == "6":
            export_to_json()
        elif choice == "7":
            import_from_json()
        elif choice == "8":
            print("Goodbye!")
            break
        else:
            print("Invalid choice. Please choose a number between 1 and 8.")

        # small spacer after each operation
        print("\n" + "=" * 50 + "\n")


if __name__ == "__main__":
    main()
