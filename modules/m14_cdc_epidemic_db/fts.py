import sqlite3

def rebuild_fts(db_path: str):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    cursor.execute("""
        CREATE VIRTUAL TABLE IF NOT EXISTS m14_cdc_epidemic_db_fts USING fts5(
            point_id UNINDEXED,
            facility_name,
            service_type,
            city,
            district
        );
    """)

    cursor.execute("DELETE FROM m14_cdc_epidemic_db_fts;")

    cursor.execute("""
        INSERT INTO m14_cdc_epidemic_db_fts (point_id, facility_name, service_type, city, district)
        SELECT point_id, facility_name, service_type, city, district
        FROM m14_cdc_epidemic_db;
    """)

    conn.commit()
    conn.close()
