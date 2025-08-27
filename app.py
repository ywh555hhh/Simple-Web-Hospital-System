#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
校医院医务收费管理系统 - Flask后端API服务器
功能：提供RESTful API接口，支持用户认证、数据管理等功能
"""

from flask import Flask, request, jsonify, session
import sqlite3
import os
from datetime import datetime
from functools import wraps

app = Flask(__name__)
app.secret_key = 'hospital_management_system_secret_key_2024'

# 数据库连接函数
def get_db():
    """获取数据库连接"""
    conn = sqlite3.connect('database.db')
    conn.row_factory = sqlite3.Row  # 让查询结果可以像字典一样访问
    return conn

# 权限验证装饰器
def login_required(f):
    """登录验证装饰器"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return jsonify({'success': False, 'message': '请先登录'}), 401
        return f(*args, **kwargs)
    return decorated_function

def role_required(roles):
    """角色权限验证装饰器"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if 'user_id' not in session:
                return jsonify({'success': False, 'message': '请先登录'}), 401
            if session.get('role') not in roles:
                return jsonify({'success': False, 'message': '权限不足'}), 403
            return f(*args, **kwargs)
        return decorated_function
    return decorator

# 用户认证相关API
@app.route('/api/login', methods=['POST'])
def login():
    """用户登录"""
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')
    
    if not username or not password:
        return jsonify({'success': False, 'message': '用户名和密码不能为空'})
    
    conn = get_db()
    cursor = conn.cursor()
    
    cursor.execute('SELECT * FROM users WHERE username = ? AND password = ?', (username, password))
    user = cursor.fetchone()
    conn.close()
    
    if user:
        session['user_id'] = user['id']
        session['username'] = user['username']
        session['role'] = user['role']
        session['full_name'] = user['full_name']
        return jsonify({
            'success': True,
            'message': '登录成功',
            'user': {
                'id': user['id'],
                'username': user['username'],
                'role': user['role'],
                'full_name': user['full_name']
            }
        })
    else:
        return jsonify({'success': False, 'message': '用户名或密码错误'})

@app.route('/api/logout', methods=['GET'])
def logout():
    """用户登出"""
    session.clear()
    return jsonify({'success': True, 'message': '登出成功'})

@app.route('/api/current_user', methods=['GET'])
@login_required
def current_user():
    """获取当前登录用户信息"""
    return jsonify({
        'success': True,
        'user': {
            'id': session['user_id'],
            'username': session['username'],
            'role': session['role'],
            'full_name': session['full_name']
        }
    })

# 科室管理API (仅管理员)
@app.route('/api/departments', methods=['GET'])
@login_required
def get_departments():
    """获取所有科室"""
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM departments ORDER BY id')
    departments = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return jsonify({'success': True, 'data': departments})

@app.route('/api/departments', methods=['POST'])
@role_required(['admin'])
def create_department():
    """创建新科室"""
    data = request.get_json()
    name = data.get('name', '').strip()
    
    if not name:
        return jsonify({'success': False, 'message': '科室名称不能为空'})
    
    conn = get_db()
    cursor = conn.cursor()
    
    try:
        cursor.execute('INSERT INTO departments (name) VALUES (?)', (name,))
        conn.commit()
        return jsonify({'success': True, 'message': '科室创建成功'})
    except sqlite3.IntegrityError:
        return jsonify({'success': False, 'message': '科室名称已存在'})
    finally:
        conn.close()

@app.route('/api/departments/<int:dept_id>', methods=['DELETE'])
@role_required(['admin'])
def delete_department(dept_id):
    """删除科室"""
    conn = get_db()
    cursor = conn.cursor()
    
    # 检查是否有医生绑定到此科室
    cursor.execute('SELECT COUNT(*) as count FROM doctors WHERE department_id = ?', (dept_id,))
    count = cursor.fetchone()['count']
    
    if count > 0:
        conn.close()
        return jsonify({'success': False, 'message': '该科室下还有医生，无法删除'})
    
    cursor.execute('DELETE FROM departments WHERE id = ?', (dept_id,))
    if cursor.rowcount > 0:
        conn.commit()
        conn.close()
        return jsonify({'success': True, 'message': '科室删除成功'})
    else:
        conn.close()
        return jsonify({'success': False, 'message': '科室不存在'})

# 药品管理API (药房管理员和管理员)
@app.route('/api/drugs', methods=['GET'])
@role_required(['pharmacy', 'admin'])
def get_drugs():
    """获取所有药品"""
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM drugs ORDER BY id')
    drugs = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return jsonify({'success': True, 'data': drugs})

@app.route('/api/drugs', methods=['POST'])
@role_required(['pharmacy', 'admin'])
def create_drug():
    """新增药品"""
    data = request.get_json()
    name = data.get('name', '').strip()
    purchase_price = data.get('purchase_price')
    sale_price = data.get('sale_price')
    stock = data.get('stock', 0)
    min_threshold = data.get('min_threshold', 10)
    max_threshold = data.get('max_threshold', 100)
    
    if not name:
        return jsonify({'success': False, 'message': '药品名称不能为空'})
    
    if not purchase_price or not sale_price:
        return jsonify({'success': False, 'message': '进价和售价不能为空'})
    
    try:
        purchase_price = float(purchase_price)
        sale_price = float(sale_price)
        stock = int(stock)
        min_threshold = int(min_threshold)
        max_threshold = int(max_threshold)
    except ValueError:
        return jsonify({'success': False, 'message': '价格和库存必须为数字'})
    
    conn = get_db()
    cursor = conn.cursor()
    
    try:
        cursor.execute(
            'INSERT INTO drugs (name, purchase_price, sale_price, stock, min_threshold, max_threshold) VALUES (?, ?, ?, ?, ?, ?)',
            (name, purchase_price, sale_price, stock, min_threshold, max_threshold)
        )
        conn.commit()
        return jsonify({'success': True, 'message': '药品添加成功'})
    except sqlite3.IntegrityError:
        return jsonify({'success': False, 'message': '药品名称已存在'})
    finally:
        conn.close()

@app.route('/api/drugs/<int:drug_id>', methods=['PUT'])
@role_required(['pharmacy', 'admin'])
def update_drug(drug_id):
    """更新药品信息"""
    data = request.get_json()
    name = data.get('name', '').strip()
    purchase_price = data.get('purchase_price')
    sale_price = data.get('sale_price')
    min_threshold = data.get('min_threshold', 10)
    max_threshold = data.get('max_threshold', 100)
    
    if not name:
        return jsonify({'success': False, 'message': '药品名称不能为空'})
    
    try:
        purchase_price = float(purchase_price)
        sale_price = float(sale_price)
        min_threshold = int(min_threshold)
        max_threshold = int(max_threshold)
    except ValueError:
        return jsonify({'success': False, 'message': '价格和阈值必须为数字'})
    
    conn = get_db()
    cursor = conn.cursor()
    
    try:
        cursor.execute(
            'UPDATE drugs SET name = ?, purchase_price = ?, sale_price = ?, min_threshold = ?, max_threshold = ? WHERE id = ?',
            (name, purchase_price, sale_price, min_threshold, max_threshold, drug_id)
        )
        if cursor.rowcount > 0:
            conn.commit()
            return jsonify({'success': True, 'message': '药品信息更新成功'})
        else:
            return jsonify({'success': False, 'message': '药品不存在'})
    except sqlite3.IntegrityError:
        return jsonify({'success': False, 'message': '药品名称已存在'})
    finally:
        conn.close()

@app.route('/api/drugs/<int:drug_id>/add_stock', methods=['POST'])
@role_required(['pharmacy', 'admin'])
def add_drug_stock(drug_id):
    """增加药品库存"""
    data = request.get_json()
    quantity = data.get('quantity')
    
    if not quantity:
        return jsonify({'success': False, 'message': '增加数量不能为空'})
    
    try:
        quantity = int(quantity)
        if quantity <= 0:
            return jsonify({'success': False, 'message': '增加数量必须大于0'})
    except ValueError:
        return jsonify({'success': False, 'message': '增加数量必须为正整数'})
    
    conn = get_db()
    cursor = conn.cursor()
    
    cursor.execute('UPDATE drugs SET stock = stock + ? WHERE id = ?', (quantity, drug_id))
    if cursor.rowcount > 0:
        conn.commit()
        conn.close()
        return jsonify({'success': True, 'message': f'库存增加成功，增加了{quantity}个单位'})
    else:
        conn.close()
        return jsonify({'success': False, 'message': '药品不存在'})

# 挂号相关API (挂号员)
@app.route('/api/doctors_by_dept/<int:dept_id>', methods=['GET'])
@role_required(['registration'])
def get_doctors_by_department(dept_id):
    """根据科室获取医生列表"""
    conn = get_db()
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT d.id, d.user_id, d.status, u.full_name, dept.name as department_name
        FROM doctors d
        JOIN users u ON d.user_id = u.id
        JOIN departments dept ON d.department_id = dept.id
        WHERE d.department_id = ? AND d.status = 'on_duty'
        ORDER BY u.full_name
    ''', (dept_id,))
    
    doctors = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return jsonify({'success': True, 'data': doctors})

@app.route('/api/registrations', methods=['POST'])
@role_required(['registration'])
def create_registration():
    """创建挂号记录"""
    data = request.get_json()
    patient_name = data.get('patient_name', '').strip()
    department_id = data.get('department_id')
    doctor_id = data.get('doctor_id')
    fee = data.get('fee', 15.0)
    
    if not patient_name:
        return jsonify({'success': False, 'message': '患者姓名不能为空'})
    
    if not department_id or not doctor_id:
        return jsonify({'success': False, 'message': '请选择科室和医生'})
    
    try:
        department_id = int(department_id)
        doctor_id = int(doctor_id)
        fee = float(fee)
    except ValueError:
        return jsonify({'success': False, 'message': '参数格式错误'})
    
    conn = get_db()
    cursor = conn.cursor()
    
    # 验证医生是否属于指定科室
    cursor.execute('SELECT COUNT(*) as count FROM doctors WHERE id = ? AND department_id = ?', (doctor_id, department_id))
    if cursor.fetchone()['count'] == 0:
        conn.close()
        return jsonify({'success': False, 'message': '医生与科室不匹配'})
    
    # 创建挂号记录
    cursor.execute(
        'INSERT INTO registrations (patient_name, department_id, doctor_id, fee, status) VALUES (?, ?, ?, ?, ?)',
        (patient_name, department_id, doctor_id, fee, 'waiting')
    )
    
    conn.commit()
    conn.close()
    return jsonify({'success': True, 'message': '挂号成功'})

# 医生相关API
@app.route('/api/my_patients', methods=['GET'])
@role_required(['doctor'])
def get_my_patients():
    """获取当前医生的待诊患者"""
    conn = get_db()
    cursor = conn.cursor()
    
    # 获取当前用户对应的医生ID
    cursor.execute('SELECT id FROM doctors WHERE user_id = ?', (session['user_id'],))
    doctor_record = cursor.fetchone()
    
    if not doctor_record:
        conn.close()
        return jsonify({'success': False, 'message': '医生信息不存在'})
    
    doctor_id = doctor_record['id']
    
    # 获取待诊患者列表
    cursor.execute('''
        SELECT r.id, r.patient_name, r.fee, r.status, r.created_at,
               d.name as department_name
        FROM registrations r
        JOIN departments d ON r.department_id = d.id
        WHERE r.doctor_id = ? AND r.status IN ('waiting', 'finished')
        ORDER BY r.created_at ASC
    ''', (doctor_id,))
    
    patients = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return jsonify({'success': True, 'data': patients})

@app.route('/api/prescriptions', methods=['POST'])
@role_required(['doctor'])
def create_prescription():
    """医生开具处方"""
    data = request.get_json()
    registration_id = data.get('registration_id')
    drugs = data.get('drugs', [])  # 格式: [{'drug_id': 1, 'quantity': 2}, ...]
    
    if not registration_id:
        return jsonify({'success': False, 'message': '挂号记录ID不能为空'})
    
    if not drugs:
        return jsonify({'success': False, 'message': '处方药品不能为空'})
    
    # 获取当前医生ID
    conn = get_db()
    cursor = conn.cursor()
    
    cursor.execute('SELECT id FROM doctors WHERE user_id = ?', (session['user_id'],))
    doctor_record = cursor.fetchone()
    
    if not doctor_record:
        conn.close()
        return jsonify({'success': False, 'message': '医生信息不存在'})
    
    doctor_id = doctor_record['id']
    
    # 验证挂号记录是否属于当前医生且状态为waiting
    cursor.execute('SELECT * FROM registrations WHERE id = ? AND doctor_id = ? AND status = ?', 
                  (registration_id, doctor_id, 'waiting'))
    registration = cursor.fetchone()
    
    if not registration:
        conn.close()
        return jsonify({'success': False, 'message': '挂号记录不存在或已处理'})
    
    # 计算处方总金额
    total_amount = 0
    prescription_details = []
    
    for drug_item in drugs:
        drug_id = drug_item.get('drug_id')
        quantity = drug_item.get('quantity', 1)
        
        # 获取药品信息
        cursor.execute('SELECT sale_price FROM drugs WHERE id = ?', (drug_id,))
        drug = cursor.fetchone()
        
        if not drug:
            conn.close()
            return jsonify({'success': False, 'message': f'药品ID {drug_id} 不存在'})
        
        subtotal = drug['sale_price'] * quantity
        total_amount += subtotal
        prescription_details.append((drug_id, quantity, subtotal))
    
    try:
        # 创建处方主记录
        cursor.execute(
            'INSERT INTO prescriptions (registration_id, doctor_id, total_amount, status) VALUES (?, ?, ?, ?)',
            (registration_id, doctor_id, total_amount, 'pending_payment')
        )
        prescription_id = cursor.lastrowid
        
        # 创建处方明细
        for drug_id, quantity, subtotal in prescription_details:
            cursor.execute(
                'INSERT INTO prescription_details (prescription_id, drug_id, quantity, subtotal) VALUES (?, ?, ?, ?)',
                (prescription_id, drug_id, quantity, subtotal)
            )
        
        # 更新挂号状态为已就诊
        cursor.execute('UPDATE registrations SET status = ? WHERE id = ?', ('finished', registration_id))
        
        conn.commit()
        return jsonify({'success': True, 'message': '处方开具成功'})
    
    except Exception as e:
        conn.rollback()
        return jsonify({'success': False, 'message': f'处方开具失败: {str(e)}'})
    finally:
        conn.close()

# 收费相关API (收费员)
@app.route('/api/prescriptions/<int:prescription_id>', methods=['GET'])
@role_required(['cashier'])
def get_prescription_details(prescription_id):
    """获取处方详情"""
    conn = get_db()
    cursor = conn.cursor()
    
    # 获取处方基本信息
    cursor.execute('''
        SELECT p.id, p.registration_id, p.total_amount, p.status, p.created_at,
               r.patient_name, r.fee as registration_fee,
               u.full_name as doctor_name,
               d.name as department_name
        FROM prescriptions p
        JOIN registrations r ON p.registration_id = r.id
        JOIN doctors doc ON p.doctor_id = doc.id
        JOIN users u ON doc.user_id = u.id
        JOIN departments d ON r.department_id = d.id
        WHERE p.id = ?
    ''', (prescription_id,))
    
    prescription = cursor.fetchone()
    
    if not prescription:
        conn.close()
        return jsonify({'success': False, 'message': '处方不存在'})
    
    # 获取处方明细
    cursor.execute('''
        SELECT pd.quantity, pd.subtotal,
               dr.name as drug_name, dr.sale_price
        FROM prescription_details pd
        JOIN drugs dr ON pd.drug_id = dr.id
        WHERE pd.prescription_id = ?
    ''', (prescription_id,))
    
    details = [dict(row) for row in cursor.fetchall()]
    
    conn.close()
    
    result = dict(prescription)
    result['details'] = details
    
    return jsonify({'success': True, 'data': result})

@app.route('/api/prescriptions/<int:prescription_id>/pay', methods=['POST'])
@role_required(['cashier'])
def pay_prescription(prescription_id):
    """处方缴费"""
    conn = get_db()
    cursor = conn.cursor()
    
    # 获取处方信息
    cursor.execute('SELECT * FROM prescriptions WHERE id = ? AND status = ?', 
                  (prescription_id, 'pending_payment'))
    prescription = cursor.fetchone()
    
    if not prescription:
        conn.close()
        return jsonify({'success': False, 'message': '处方不存在或已缴费'})
    
    # 获取处方明细用于扣减库存
    cursor.execute('''
        SELECT pd.drug_id, pd.quantity, dr.stock
        FROM prescription_details pd
        JOIN drugs dr ON pd.drug_id = dr.id
        WHERE pd.prescription_id = ?
    ''', (prescription_id,))
    
    drug_details = cursor.fetchall()
    
    # 检查库存是否充足
    for detail in drug_details:
        if detail['stock'] < detail['quantity']:
            conn.close()
            return jsonify({'success': False, 'message': f'药品库存不足，当前库存：{detail["stock"]}'})
    
    try:
        # 扣减库存
        for detail in drug_details:
            cursor.execute('UPDATE drugs SET stock = stock - ? WHERE id = ?', 
                          (detail['quantity'], detail['drug_id']))
        
        # 更新处方状态
        cursor.execute('UPDATE prescriptions SET status = ? WHERE id = ?', ('paid', prescription_id))
        
        # 更新挂号状态
        cursor.execute('UPDATE registrations SET status = ? WHERE id = ?', 
                      ('paid', prescription['registration_id']))
        
        conn.commit()
        return jsonify({'success': True, 'message': '缴费成功'})
    
    except Exception as e:
        conn.rollback()
        return jsonify({'success': False, 'message': f'缴费失败: {str(e)}'})
    finally:
        conn.close()

# 统计查询API
@app.route('/api/stats/today', methods=['GET'])
@login_required
def get_today_stats():
    """获取今日统计数据"""
    conn = get_db()
    cursor = conn.cursor()
    
    today = datetime.now().strftime('%Y-%m-%d')
    
    # 今日挂号数
    cursor.execute("SELECT COUNT(*) as count FROM registrations WHERE DATE(created_at) = ?", (today,))
    today_registrations = cursor.fetchone()['count']
    
    # 今日收入 (挂号费 + 药品费)
    cursor.execute('''
        SELECT 
            COALESCE(SUM(r.fee), 0) as registration_income,
            COALESCE(SUM(p.total_amount), 0) as drug_income
        FROM registrations r
        LEFT JOIN prescriptions p ON r.id = p.registration_id AND p.status = 'paid'
        WHERE DATE(r.created_at) = ? AND r.status = 'paid'
    ''', (today,))
    
    income_data = cursor.fetchone()
    total_income = income_data['registration_income'] + income_data['drug_income']
    
    # 待缴费处方数
    cursor.execute("SELECT COUNT(*) as count FROM prescriptions WHERE status = 'pending_payment'")
    pending_prescriptions = cursor.fetchone()['count']
    
    # 库存告急药品数
    cursor.execute("SELECT COUNT(*) as count FROM drugs WHERE stock <= min_threshold")
    low_stock_drugs = cursor.fetchone()['count']
    
    conn.close()
    
    return jsonify({
        'success': True,
        'data': {
            'today_registrations': today_registrations,
            'total_income': total_income,
            'registration_income': income_data['registration_income'],
            'drug_income': income_data['drug_income'],
            'pending_prescriptions': pending_prescriptions,
            'low_stock_drugs': low_stock_drugs
        }
    })

@app.route('/api/stats/drug_inventory', methods=['GET'])
@role_required(['pharmacy', 'admin'])
def get_drug_inventory_stats():
    """获取药品库存统计"""
    conn = get_db()
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT name, stock, min_threshold, max_threshold,
               CASE 
                   WHEN stock <= min_threshold THEN 'low'
                   WHEN stock >= max_threshold THEN 'high'
                   ELSE 'normal'
               END as status
        FROM drugs
        ORDER BY stock ASC, name
    ''')
    
    drugs = [dict(row) for row in cursor.fetchall()]
    conn.close()
    
    return jsonify({'success': True, 'data': drugs})

# 静态文件服务
@app.route('/')
def index():
    """重定向到登录页面"""
    return app.send_static_file('login.html')

@app.route('/<path:filename>')
def serve_static(filename):
    """提供静态文件服务"""
    try:
        return app.send_static_file(filename)
    except:
        return "文件不存在", 404

if __name__ == '__main__':
    # 检查数据库是否存在
    if not os.path.exists('database.db'):
        print("数据库文件不存在，请先运行 python database.py 初始化数据库")
        exit(1)
    
    print("校医院医务收费管理系统后端服务启动中...")
    print("访问地址: http://127.0.0.1:5000")
    print("登录页面: http://127.0.0.1:5000/login.html")
    app.run(debug=True, host='127.0.0.1', port=5000)