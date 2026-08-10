import sqlite3
import datetime

DB_NAME = "tasks.db"

def init_db():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS tasks
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  filename TEXT,
                  source_url TEXT,
                  video_title TEXT,
                  thumbnail_url TEXT,
                  duration INTEGER,
                  whisper_model TEXT DEFAULT 'base',
                  status TEXT,
                  result TEXT,
                  created_at TIMESTAMP,
                  pinned BOOLEAN DEFAULT 0,
                  pinned_at TIMESTAMP)''')
    conn.commit()
    conn.close()

def create_task(filename, source_url=None, video_title=None, thumbnail_url=None, duration=None, whisper_model='base'):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    created_at = datetime.datetime.now()
    c.execute("""INSERT INTO tasks (filename, source_url, video_title, thumbnail_url, duration, whisper_model, status, created_at) 
                 VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
              (filename, source_url, video_title, thumbnail_url, duration, whisper_model, "queued", created_at))
    task_id = c.lastrowid
    conn.commit()
    conn.close()
    return task_id

def get_task(task_id):
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    c.execute("SELECT * FROM tasks WHERE id=?", (task_id,))
    row = c.fetchone()
    conn.close()
    if row:
        return dict(row)
    return None

def get_tasks(limit=50):
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    # 置顶项在前，按置顶时间倒序；普通项按创建时间倒序
    c.execute("""
        SELECT * FROM tasks 
        ORDER BY 
            pinned DESC,
            CASE WHEN pinned = 1 THEN pinned_at ELSE created_at END DESC
        LIMIT ?
    """, (limit,))
    rows = c.fetchall()
    conn.close()
    return [dict(row) for row in rows]

def update_task_status(task_id, status, result=None):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    if result is not None:
        c.execute("UPDATE tasks SET status=?, result=? WHERE id=?", (status, result, task_id))
    else:
        c.execute("UPDATE tasks SET status=? WHERE id=?", (status, task_id))
    conn.commit()
    conn.close()

def update_task_duration(task_id, duration):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("UPDATE tasks SET duration=? WHERE id=?", (duration, task_id))
    conn.commit()
    conn.close()

def pin_task(task_id):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("UPDATE tasks SET pinned=1, pinned_at=? WHERE id=?", (datetime.datetime.now(), task_id))
    conn.commit()
    conn.close()

def unpin_task(task_id):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("UPDATE tasks SET pinned=0, pinned_at=NULL WHERE id=?", (task_id,))
    conn.commit()
    conn.close()

def delete_task(task_id):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("DELETE FROM tasks WHERE id=?", (task_id,))
    conn.commit()
    conn.close()
