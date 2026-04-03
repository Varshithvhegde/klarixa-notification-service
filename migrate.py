import sqlite3

def upgrade_schema():
    print("Upgrading database schema for Step 7...")
    conn = sqlite3.connect('sql_app.db')
    cursor = conn.cursor()
    try:
        cursor.execute("ALTER TABLE notifications ADD COLUMN retry_count INTEGER DEFAULT 0")
        print("Added retry_count column.")
    except sqlite3.OperationalError:
        print("retry_count column already exists.")

    try:
        cursor.execute("ALTER TABLE notifications ADD COLUMN error_message VARCHAR")
        print("Added error_message column.")
    except sqlite3.OperationalError:
        print("error_message column already exists.")

    try:
        cursor.execute("ALTER TABLE notifications ADD COLUMN sent_at DATETIME")
        print("Added sent_at column.")
    except sqlite3.OperationalError:
        print("sent_at column already exists.")

    conn.commit()
    conn.close()
    print("Upgrade complete.")

if __name__ == "__main__":
    upgrade_schema()
