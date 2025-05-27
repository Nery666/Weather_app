import sqlite3

def init_db():
    conn = sqlite3.connect("weather.db")
    conn.execute('''CREATE TABLE IF NOT EXISTS search_history (
                        id INTEGER PRIMARY KEY,
                        city TEXT,
                        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
                    )''')
    conn.commit()
    conn.close()

def get_db():
    return sqlite3.connect("weather.db")
