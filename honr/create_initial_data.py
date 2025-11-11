import sqlite3


def create_initial_data():
    """创建初始数据库文件"""
    conn = sqlite3.connect('experiment_data.db')
    try:
        with conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS participants (
                    id TEXT PRIMARY KEY,
                    group_type TEXT,
                    demographic TEXT,
                    timestamp TEXT,
                    instructions TEXT,
                    evaluations TEXT
                )
                """
            )
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS experiment_instructions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    participant_id TEXT,
                    instructions TEXT,
                    timestamp TEXT
                )
                """
            )
        print("初始数据库创建成功！")
    finally:
        conn.close()
if __name__ == '__main__':
    create_initial_data()