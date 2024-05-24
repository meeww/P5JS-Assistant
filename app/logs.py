import sqlite3

def create_connection(db_file):
    """ Create a database connection to the SQLite database specified by db_file """
    conn = None
    try:
        conn = sqlite3.connect(db_file)
        print(f"Connection to {db_file} successful")
    except sqlite3.Error as e:
        print(e)
    return conn

def create_table(conn):
    """ Create the logs table if it doesn't exist """
    try:
        c = conn.cursor()
        c.execute('''
        CREATE TABLE IF NOT EXISTS logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            level TEXT NOT NULL,
            message TEXT NOT NULL,
            source TEXT NOT NULL,
            timestamp INTEGER NOT NULL
        )
        ''')
        conn.commit()
        print("Table created successfully")
    except sqlite3.Error as e:
        print(f"Error creating table: {e}")

def insert_log(conn, level, message, source, timestamp):
    """ Insert a new log into the logs table """
    try:
        c = conn.cursor()
        c.execute('''
        INSERT INTO logs (level, message, source, timestamp) VALUES (?, ?, ?, ?)
        ''', (level, message, source, timestamp))
        conn.commit()
        print(f"Log inserted: {level}, {message}, {source}, {timestamp}")
    except sqlite3.Error as e:
        print(f"Error inserting log: {e}")


def insert_logs(conn, logs):
    """ Insert multiple logs into the logs table """
    try:
        c = conn.cursor()
        c.executemany('''
        INSERT INTO logs (level, message, source, timestamp) VALUES (?, ?, ?, ?)
        ''', logs)
        conn.commit()
        print("Successfully inserted logs")
    except sqlite3.Error as e:
        print(f"Error inserting logs: {e}")


def get_logs(conn, start=0, end=999999999999999999):
    """ Retrieve logs from the logs table within the specified timestamp range """
    try:
        c = conn.cursor()
        c.execute('''
        SELECT * FROM logs WHERE timestamp >= ? AND timestamp <= ?
        ''', (start, end))
        results = c.fetchall()
        print(f"Fetched logs between {start} and {end}")



        return results
    except sqlite3.Error as e:
        print(f"Error fetching logs: {e}")
        return []

def delete_logs(conn, start=0, end=999999999999999999):
    """ Delete logs from the logs table within the specified timestamp range """
    try:
        c = conn.cursor()
        c.execute('''
        DELETE FROM logs WHERE timestamp >= ? AND timestamp <= ?
        ''', (start, end))
        conn.commit()
        print(f"Logs deleted between {start} and {end}")
    except sqlite3.Error as e:
        print(f"Error deleting logs: {e}")

def close_connection(conn):
    """ Close the database connection """
    if conn:
        conn.close()
