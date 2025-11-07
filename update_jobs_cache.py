import os
import json
from datetime import datetime
from connection import get_connection
import config

# Paths
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CACHE_DIR = os.path.join(BASE_DIR, "static", "cache")
CACHE_FILE = os.path.join(CACHE_DIR, "job_data.json")
TEMP_FILE = CACHE_FILE + ".tmp"
LOG_FILE = os.path.join(BASE_DIR, "job_cache.log")

os.makedirs(CACHE_DIR, exist_ok=True)


def log(message):
    """Append messages to log file with timestamp."""
    with open(LOG_FILE, "a") as f:
        f.write(f"[{datetime.now()}] {message}\n")


def update_job_cache():
    conn = get_connection(config.DB_NAME)
    if not conn:
        log("❌ Database connection failed.")
        return

    try:
        with conn.cursor() as cursor:
            cursor.execute("""
                SELECT 
                    j.id AS job_id,
                    j.job_name,
                    j.crew_cell,
                    j.district,
                    j.session_user,
                    j.status,
                    c.roh,
                    c.top_rubber,
                    c.middle_rubber,
                    c.low_rubber,
                    c.shot,
                    c.remain,
                    c.total,
                    c.asset_1,
                    c.asset_2,
                    c.asset_3,
                    c.asset_4,
                    c.asset_5,
                    c.asset_6, 
                    c.asset_1_name,
                    c.asset_2_name,
                    c.asset_3_name,
                    c.asset_4_name,
                    c.asset_5_name,
                    c.asset_6_name
                FROM jobs j
                JOIN counters c ON j.id = c.job_id
                WHERE j.status = 'active'
            """)
            jobs = cursor.fetchall()

        # Write to temp file first
        with open(TEMP_FILE, "w") as f:
            json.dump(jobs, f, default=str, indent=2)

        # Atomically replace the old file
        os.replace(TEMP_FILE, CACHE_FILE)

        log(f"✅ Updated job cache with {len(jobs)} active jobs.")
    except Exception as e:
        log(f"❌ Error updating job cache: {e}")
    finally:
        conn.close()


if __name__ == "__main__":
    update_job_cache()
