import sqlite3

def rebuild_fts(db_path: str):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    cursor.execute("""
        CREATE VIRTUAL TABLE IF NOT EXISTS m13_tw_med_device_db_fts USING fts5(
            licence_id UNINDEXED,
            device_name_c,
            device_name_e,
            applicant_name,
            manufacturer_name
        );
    """)

    cursor.execute("DELETE FROM m13_tw_med_device_db_fts;")

    cursor.execute("""
        INSERT INTO m13_tw_med_device_db_fts (licence_id, device_name_c, device_name_e, applicant_name, manufacturer_name)
        SELECT licence_id, device_name_c, device_name_e, applicant_name, manufacturer_name
        FROM m13_tw_med_device_db;
    """)

    conn.commit()
    conn.close()
