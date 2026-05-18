import sqlite3
import random
from datetime import datetime, timedelta

if __name__ == "__main__":
    conn = sqlite3.connect('factory_log.db')
    cursor = conn.cursor()

    cursor.execute('DROP TABLE IF EXISTS logs')
    cursor.execute('''
        CREATE TABLE logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT,
            status TEXT,
            sensor_data TEXT,
            img_filename TEXT
        )
    ''')

    statuses = ['PASS', 'PASS', 'PASS', 'PASS', 'RED_DETECTED', 'ERROR_CONNECTION']

    for _ in range(30):
        random_minutes = random.randint(1, 60)
        ts = (datetime.now() - timedelta(minutes=random_minutes)).strftime('%Y-%m-%d %H:%M:%S')
        status = random.choice(statuses)

        if status == 'ERROR_CONNECTION':
            sensor_val = "Ping Timeout"
        else:
            sensor_val = f"Motor Load: {random.randint(40, 80)}%"

        cursor.execute("INSERT INTO logs (timestamp, status, sensor_data) VALUES (?, ?, ?)", (ts, status, sensor_val))

    conn.commit()
    conn.close()

    print("성공적으로 가상 데이터베이스가 생성되었습니다!")