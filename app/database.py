import psycopg2
from psycopg2.extras import RealDictCursor
from config.settings import DATABASE_URL
from datetime import datetime

def init_db():
    try:
        conn = psycopg2.connect(DATABASE_URL)
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS reports (
                id SERIAL PRIMARY KEY,
                user_id BIGINT NOT NULL,
                voice_file_path VARCHAR(255),
                transcript TEXT,
                summary TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """)
        conn.commit()
        cursor.close()
        conn.close()
        print("Database initialized successfully.")
    except Exception as e:
        print(f"Database initialization error: {str(e)}")
        raise

def save_report(user_id, voice_file_path, transcript, summary):
    try:
        conn = psycopg2.connect(DATABASE_URL)
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO reports (user_id, voice_file_path, transcript, summary)
            VALUES (%s, %s, %s, %s) RETURNING id;
        """, (user_id, voice_file_path, transcript, summary))
        report_id = cursor.fetchone()[0]
        conn.commit()
        cursor.close()
        conn.close()
        return report_id
    except Exception as e:
        print(f"Save report error: {str(e)}")
        raise

def get_reports_by_user(user_id):
    try:
        conn = psycopg2.connect(DATABASE_URL)
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        cursor.execute("SELECT * FROM reports WHERE user_id = %s ORDER BY created_at DESC;", (user_id,))
        reports = cursor.fetchall()
        cursor.close()
        conn.close()
        return reports
    except Exception as e:
        print(f"Get reports error: {str(e)}")
        raise
