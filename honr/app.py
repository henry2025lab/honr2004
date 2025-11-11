from flask import Flask, render_template, request, redirect, url_for, session
import json
import os
import sqlite3
import uuid
from datetime import datetime
app = Flask(__name__)
app.secret_key = 'visual_experiment_secret_key_2024'

# 数据库存储文件
DB_FILE = 'experiment_data.db'


def get_db_connection():
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    return conn


def initialize_database():
    """初始化数据库并创建所需表结构"""
    os.makedirs(os.path.dirname(DB_FILE) or '.', exist_ok=True)
    conn = get_db_connection()
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
    finally:
        conn.close()

# 实验配置
EXPERIMENT_CONFIG = {
    'trials': [
        {
            'example_image': 'image1.png',
            'input_image': 'image2.png',
            'output_image': 'image3.png',
            'questions': [6, 7, 8, 9, 10, 11, 12, 13, 14, 15]
        },
        {
            'example_image': 'image4.png',
            'input_image': 'image5.png',
            'output_image': 'image6.png',
            'questions': [17, 18, 19, 20, 21, 22, 23, 24, 25, 26]
        },
        {
            'example_image': 'image7.png',
            'input_image': 'image7.png',
            'output_image': 'image8.png',
            'questions': [28, 29, 30, 31, 32, 33, 34, 35, 36, 37]
        },
        {
            'example_image': 'image9.png',
            'input_image': 'image9.png',
            'output_image': 'image10.jpeg',
            'questions': [39, 40, 41, 42, 43, 44, 45, 46, 47, 48]
        }
    ],
    'control_trials': [
        {
            'example_image': 'image1.png',
            'input_image': 'image2.png',
            'output_image': 'image3.png',
            'questions': [50, 51, 52, 53, 54, 55, 56, 57, 58, 59]
        },
        {
            'example_image': 'image4.png',
            'input_image': 'image4.png',
            'output_image': 'image6.png',
            'questions': [62, 63, 64, 65, 66, 67, 68, 69, 70, 71, 72]
        },
        {
            'example_image': 'image11.jpeg',
            'input_image': 'image11.jpeg',
            'output_image': 'image12.jpeg',
            'questions': [75, 76, 77, 78, 79, 80, 81, 82, 83, 84]
        },
        {
            'example_image': 'image13.jpeg',
            'input_image': 'image13.jpeg',
            'output_image': 'image10.jpeg',
            'questions': [87, 88, 89, 90, 91, 92, 93, 94, 95, 96]
        }
    ]
}

def load_experiment_data():
    """从数据库加载实验数据"""
    initialize_database()
    conn = get_db_connection()
    try:
        participants = []
        for row in conn.execute(
            """
            SELECT id, group_type, demographic, timestamp, instructions, evaluations
            FROM participants
            ORDER BY timestamp ASC
            """
        ):
            participants.append({
                'id': row['id'],
                'group': row['group_type'],
                'demographic': json.loads(row['demographic']) if row['demographic'] else {},
                'timestamp': row['timestamp'],
                'instructions': json.loads(row['instructions']) if row['instructions'] else [],
                'evaluations': json.loads(row['evaluations']) if row['evaluations'] else []
            })

        experiment_group_data = []
        for row in conn.execute(
            """
            SELECT participant_id, instructions, timestamp
            FROM experiment_instructions
            ORDER BY id ASC
            """
        ):
            experiment_group_data.append({
                'participant_id': row['participant_id'],
                'instructions': json.loads(row['instructions']) if row['instructions'] else [],
                'timestamp': row['timestamp']
            })

        return {
            'participants': participants,
            'experiment_group_data': experiment_group_data,
            'current_participant_id': len(participants)
        }
    finally:
        conn.close()

def get_previous_instructions():
    """获取之前试验组参与者的指令用于控制组"""
    conn = get_db_connection()
    try:
        row = conn.execute(
            """
            SELECT instructions
            FROM experiment_instructions
            ORDER BY id DESC
            LIMIT 1
            """
        ).fetchone()
        if row:
            return {
                'instructions': json.loads(row['instructions']) if row['instructions'] else []
            }
    finally:
        conn.close()

    # 如果没有试验组数据，返回示例数据
    return {
        'instructions': [
            "一个未来感十足的机器人，银色金属质感，面部有蓝色发光线条，背景是科技实验室",
            "卡通风格的可爱动物角色，毛茸茸的质感，大眼睛，温馨的森林背景",
            "抽象艺术风格的人形轮廓，混合了机械和生物元素，霓虹色彩",
            "简约设计的智能家居设备，白色光滑表面，柔和的室内灯光"
        ]
    }
@app.route('/')
def index():
    """知情同意书页面"""
    session.clear()
    session['participant_id'] = str(uuid.uuid4())[:8]
    return render_template('index.html')

@app.route('/demographic', methods=['POST'])
def demographic():
    """处理知情同意并跳转到基本信息页面"""
    return render_template('demographic.html')

@app.route('/start_experiment', methods=['POST'])
def start_experiment():
    """处理基本信息并开始实验"""
    demographic_data = {
        'gender': request.form.get('gender'),
        'age': request.form.get('age'),
        'major': request.form.get('major')
    }

    session['demographic'] = demographic_data

    # 显示分组选择页面
    return render_template('group_selection.html')

@app.route('/assign_group', methods=['POST'])
def assign_group():
    """分配实验组别"""
    group = request.form.get('group')
    session['group'] = group

    if group == 'experiment':
        return redirect(url_for('experiment_phase', trial=0))
    else:
        return redirect(url_for('control_group'))

@app.route('/experiment/<int:trial>')
def experiment_phase(trial):
    """试验组实验流程"""
    if trial >= len(EXPERIMENT_CONFIG['trials']):
        return redirect(url_for('thank_you'))

    current_trial = EXPERIMENT_CONFIG['trials'][trial]
    session['current_trial'] = trial

    return render_template('experiment.html',
                         trial=trial,
                         total_trials=len(EXPERIMENT_CONFIG['trials']),
                         config=current_trial)

@app.route('/submit_instruction', methods=['POST'])
def submit_instruction():
    """提交AI指令并跳转到加载页面"""
    trial = int(request.form.get('trial', 0))
    instruction = request.form.get('instruction', '')

    if 'instructions' not in session:
        session['instructions'] = []
    session['instructions'].append(instruction)

    return render_template('loading.html',
                         trial=trial,
                         next_url=url_for('evaluation_phase', trial=trial))

@app.route('/evaluation/<int:trial>')
def evaluation_phase(trial):
    """评估阶段"""
    if trial >= len(EXPERIMENT_CONFIG['trials']):
        return redirect(url_for('thank_you'))

    current_trial = EXPERIMENT_CONFIG['trials'][trial]

    return render_template('evaluation.html',
                         trial=trial,
                         total_trials=len(EXPERIMENT_CONFIG['trials']),
                         config=current_trial)

@app.route('/submit_evaluation', methods=['POST'])
def submit_evaluation():
    """提交评估数据"""
    trial = int(request.form.get('trial', 0))

    evaluation_data = {}
    current_trial = EXPERIMENT_CONFIG['trials'][trial]
    for q_num in current_trial['questions']:
        evaluation_data[f'q{q_num}'] = request.form.get(f'q{q_num}')

    if 'evaluations' not in session:
        session['evaluations'] = []
    session['evaluations'].append(evaluation_data)

    # 如果是最后一个trial，保存所有数据
    if trial == len(EXPERIMENT_CONFIG['trials']) - 1:
        save_participant_data()

    next_trial = trial + 1
    if next_trial < len(EXPERIMENT_CONFIG['trials']):
        return redirect(url_for('experiment_phase', trial=next_trial))
    else:
        return redirect(url_for('thank_you'))

@app.route('/control_group')
def control_group():
    """控制组流程"""
    session['group'] = 'control'
    previous_data = get_previous_instructions()
    session['previous_instructions'] = previous_data['instructions']

    return redirect(url_for('control_phase', trial=0))

@app.route('/control/<int:trial>')
def control_phase(trial):
    """控制组评估流程"""
    if trial >= len(EXPERIMENT_CONFIG['control_trials']):
        return redirect(url_for('thank_you'))

    current_trial = EXPERIMENT_CONFIG['control_trials'][trial]
    previous_instructions = session.get('previous_instructions', [])

    instruction = previous_instructions[trial] if trial < len(previous_instructions) else "示例指令"

    return render_template('control.html',
                         trial=trial,
                         total_trials=len(EXPERIMENT_CONFIG['control_trials']),
                         config=current_trial,
                         instruction=instruction)

@app.route('/submit_control_evaluation', methods=['POST'])
def submit_control_evaluation():
    """提交控制组评估数据"""
    trial = int(request.form.get('trial', 0))

    evaluation_data = {}
    current_trial = EXPERIMENT_CONFIG['control_trials'][trial]
    for q_num in current_trial['questions']:
        evaluation_data[f'q{q_num}'] = request.form.get(f'q{q_num}')

    if 'evaluations' not in session:
        session['evaluations'] = []
    session['evaluations'].append(evaluation_data)

    # 如果是最后一个trial，保存所有数据
    if trial == len(EXPERIMENT_CONFIG['control_trials']) - 1:
        save_participant_data()

    next_trial = trial + 1
    if next_trial < len(EXPERIMENT_CONFIG['control_trials']):
        return redirect(url_for('control_phase', trial=next_trial))
    else:
        return redirect(url_for('thank_you'))

def save_participant_data():
    """保存参与者数据"""
    timestamp = datetime.now().isoformat()
    participant_id = session.get('participant_id')
    participant_group = session.get('group')
    demographic = session.get('demographic', {})
    instructions = session.get('instructions', [])
    evaluations = session.get('evaluations', [])

    initialize_database()
    conn = get_db_connection()
    try:
        with conn:
            conn.execute(
                """
                INSERT INTO participants (id, group_type, demographic, timestamp, instructions, evaluations)
                VALUES (?, ?, ?, ?, ?, ?)
                ON CONFLICT(id) DO UPDATE SET
                    group_type=excluded.group_type,
                    demographic=excluded.demographic,
                    timestamp=excluded.timestamp,
                    instructions=excluded.instructions,
                    evaluations=excluded.evaluations
                """,
                (
                    participant_id,
                    participant_group,
                    json.dumps(demographic, ensure_ascii=False),
                    timestamp,
                    json.dumps(instructions, ensure_ascii=False),
                    json.dumps(evaluations, ensure_ascii=False)
                )
            )

            if participant_group == 'experiment' and instructions:
                conn.execute(
                    """
                    INSERT INTO experiment_instructions (participant_id, instructions, timestamp)
                    VALUES (?, ?, ?)
                    """,
                    (
                        participant_id,
                        json.dumps(instructions, ensure_ascii=False),
                        timestamp
                    )
                )
        print("参与者数据保存成功")
    except sqlite3.DatabaseError as e:
        print(f"保存参与者数据时出错: {e}")
    finally:
        conn.close()

@app.route('/thank_you')
def thank_you():
    """感谢页面"""
    return render_template('thank_you.html')

@app.route('/debug')
def debug():
    """调试页面 - 查看数据"""
    data = load_experiment_data()
    return f"""
    <h1>调试信息</h1>
    <p>参与者数量: {len(data.get('participants', []))}</p>
    <p>试验组数据数量: {len(data.get('experiment_group_data', []))}</p>
    <pre>{json.dumps(data, ensure_ascii=False, indent=2)}</pre>
    """

def initialize_data_file():
    """初始化数据文件"""
    initialize_database()
    print("数据库初始化完成")

if __name__ == '__main__':
    # 确保必要的文件夹存在
    os.makedirs('static/images', exist_ok=True)
    os.makedirs('templates', exist_ok=True)
    
    # 初始化数据文件
    initialize_data_file()
    
    app.run(debug=True, host='0.0.0.0', port=5000)