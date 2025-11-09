import sqlite3

DATABASE_FILE = "flowpilot.db"

def init_db():
    """Initializes the database and creates tables if they don't exist."""
    try:
        con = sqlite3.connect(DATABASE_FILE)
        cur = con.cursor()
        cur.execute("PRAGMA foreign_keys = ON;")

        # Create users table
        cur.execute('''
            CREATE TABLE IF NOT EXISTS users(
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                email TEXT UNIQUE NOT NULL,
                full_name TEXT
            );
        ''')

        # Create user_credentials table
        cur.execute('''
            CREATE TABLE IF NOT EXISTS user_credentials (
                user_email TEXT PRIMARY KEY,
                token_json TEXT NOT NULL,
                FOREIGN KEY (user_email) REFERENCES users (email)
            );
        ''')

        con.commit()
        print("Database initialized successfully.")
    except Exception as e:
        print(f"Error initializing database: {e}")
    finally:
        con.close()

if __name__ == '__main__':
    init_db()