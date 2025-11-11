import json
import os

def create_initial_data():
    """创建初始数据文件"""
    initial_data = {
        "participants": [],
        "experiment_group_data": [],
        "current_participant_id": 0
    }
    
    with open('experiment_data.json', 'w', encoding='utf-8') as f:
        json.dump(initial_data, f, ensure_ascii=False, indent=2)
    
    print("初始数据文件创建成功！")

if __name__ == '__main__':
    create_initial_data()