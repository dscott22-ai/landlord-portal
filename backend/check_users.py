import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "landlord_portal.db")

print("Checking DB at:", DB_PATH)

conn = sqlite3.connect(DB_PATH)
cursor = conn.cursor()

cursor.execute("SELECT id, name, email, role FROM users")
users = cursor.fetchall()

print("\nUsers in database:\n")
for user in users:
    print(user)

conn.close()