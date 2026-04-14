import sqlite3

def crea_tabelle():
    conn = sqlite3.connect("volley.db")
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS atleti (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT,
            cognome TEXT,
            data_nascita TEXT
        )
    """)

    conn.commit()
    conn.close()
