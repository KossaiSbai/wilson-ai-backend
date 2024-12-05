import sqlite3
from contextlib import contextmanager


class SQLiteDatabase:
    def __init__(self, db_path):
        self.db_path = db_path

    @contextmanager
    def get_connection(self):
        conn = sqlite3.connect(self.db_path)
        try:
            yield conn
        finally:
            conn.close()

    def get_file_by_name(self, name):
        with self.get_connection() as conn:
            cur = conn.cursor()
            cur.execute("SELECT * FROM file_metadata WHERE name=?", (name,))
            return cur.fetchone()
        
    def get_all_files(self):
        with self.get_connection() as conn:
            cur = conn.cursor()
            cur.execute("SELECT * FROM file_metadata")
            return cur.fetchall()

    def add_file(self, file_metadata):
        with self.get_connection() as conn:
            sql = '''INSERT INTO file_metadata(id, name)
                     VALUES(?, ?)'''
            cur = conn.cursor()
            cur.execute(sql, file_metadata)
            conn.commit()
            return cur.lastrowid

    def create_file_table(self):
        with self.get_connection() as conn:
            try:
                conn.execute(
                    "CREATE TABLE IF NOT EXISTS file_metadata ("
                    "id TEXT PRIMARY KEY, "
                    "name TEXT, "
                    "created_at DATE DEFAULT (datetime('now', 'localtime')))"
                )
            except sqlite3.OperationalError as e:
                print("Failed to create table:", e)
