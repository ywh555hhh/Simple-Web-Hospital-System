#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
校医院医务收费管理系统 - 数据库初始化脚本
功能：创建数据库表结构并填充测试数据
"""

import sqlite3
import os
from datetime import datetime, timedelta

def create_database():
    """创建数据库和所有表结构"""
    # 如果数据库文件已存在，删除它以确保重新创建
    if os.path.exists('database.db'):
        os.remove('database.db')
        print("已删除现有数据库文件")
    
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    
    # 操作员表 (users)
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE NOT NULL,
        password TEXT NOT NULL,
        role TEXT NOT NULL CHECK(role IN ('admin', 'registration', 'doctor', 'cashier', 'pharmacy')),
        full_name TEXT NOT NULL
    )
    ''')
    
    # 科室表 (departments)
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS departments (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT UNIQUE NOT NULL
    )
    ''')
    
    # 医生表 (doctors)
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS doctors (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER UNIQUE NOT NULL,
        department_id INTEGER NOT NULL,
        status TEXT NOT NULL DEFAULT 'on_duty',
        FOREIGN KEY (user_id) REFERENCES users (id),
        FOREIGN KEY (department_id) REFERENCES departments (id)
    )
    ''')
    
    # 药品表 (drugs)
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS drugs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT UNIQUE NOT NULL,
        purchase_price REAL NOT NULL,
        sale_price REAL NOT NULL,
        stock INTEGER NOT NULL,
        min_threshold INTEGER DEFAULT 10,
        max_threshold INTEGER DEFAULT 100
    )
    ''')
    
    # 挂号记录表 (registrations)
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS registrations (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        patient_name TEXT NOT NULL,
        department_id INTEGER NOT NULL,
        doctor_id INTEGER NOT NULL,
        fee REAL NOT NULL,
        status TEXT NOT NULL DEFAULT 'waiting',
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (department_id) REFERENCES departments (id),
        FOREIGN KEY (doctor_id) REFERENCES doctors (id)
    )
    ''')
    
    # 处方主表 (prescriptions)
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS prescriptions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        registration_id INTEGER NOT NULL,
        doctor_id INTEGER NOT NULL,
        total_amount REAL NOT NULL,
        status TEXT NOT NULL DEFAULT 'pending_payment',
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (registration_id) REFERENCES registrations (id),
        FOREIGN KEY (doctor_id) REFERENCES doctors (id)
    )
    ''')
    
    # 处方明细表 (prescription_details)
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS prescription_details (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        prescription_id INTEGER NOT NULL,
        drug_id INTEGER NOT NULL,
        quantity INTEGER NOT NULL,
        subtotal REAL NOT NULL,
        FOREIGN KEY (prescription_id) REFERENCES prescriptions (id),
        FOREIGN KEY (drug_id) REFERENCES drugs (id)
    )
    ''')
    
    conn.commit()
    print("数据库表结构创建完成")
    return conn

def insert_initial_data(conn):
    """插入初始测试数据"""
    cursor = conn.cursor()
    
    # 插入用户数据
    users_data = [
        ('admin', '123456', 'admin', '系统管理员'),
        ('guahao01', '123456', 'registration', '王芳'),
        ('shoufei01', '123456', 'cashier', '李静'),
        ('yaofang01', '123456', 'pharmacy', '刘伟'),
        ('zhangsan', '123456', 'doctor', '张三'),
        ('lisi', '123456', 'doctor', '李四'),
        ('wangwu', '123456', 'doctor', '王五'),
    ]
    
    cursor.executemany('INSERT INTO users (username, password, role, full_name) VALUES (?, ?, ?, ?)', users_data)
    print("用户数据插入完成")
    
    # 插入科室数据
    departments_data = [
        ('内科',),
        ('外科',),
        ('口腔科',),
        ('皮肤科',),
    ]
    
    cursor.executemany('INSERT INTO departments (name) VALUES (?)', departments_data)
    print("科室数据插入完成")
    
    # 插入医生数据 (张三和王五分配至内科，李四分配至外科)
    doctors_data = [
        (5, 1, 'on_duty'),  # 张三 -> 内科
        (6, 2, 'on_duty'),  # 李四 -> 外科
        (7, 1, 'on_duty'),  # 王五 -> 内科
    ]
    
    cursor.executemany('INSERT INTO doctors (user_id, department_id, status) VALUES (?, ?, ?)', doctors_data)
    print("医生数据插入完成")
    
    # 插入药品数据
    drugs_data = [
        # 库存充足 (>100)
        ('阿莫西林', 8.50, 12.00, 150, 10, 200),
        ('布洛芬', 5.20, 8.50, 120, 10, 200),
        ('维生素C', 3.00, 5.00, 180, 10, 200),
        # 库存正常 (50-100)
        ('云南白药', 25.00, 35.00, 75, 10, 100),
        ('碘伏', 6.80, 10.00, 60, 10, 100),
        # 库存告急 (<10)
        ('999感冒灵', 12.00, 18.00, 8, 10, 100),
    ]
    
    cursor.executemany('INSERT INTO drugs (name, purchase_price, sale_price, stock, min_threshold, max_threshold) VALUES (?, ?, ?, ?, ?, ?)', drugs_data)
    print("药品数据插入完成")
    
    # 插入挂号记录 - 创建测试数据
    now = datetime.now()
    
    # 5条已完成全流程的记录 (已挂号 -> 已就诊 -> 已缴费)
    completed_registrations = [
        ('张明', 1, 1, 15.00, 'paid', (now - timedelta(days=2)).strftime('%Y-%m-%d %H:%M:%S')),
        ('李华', 2, 2, 20.00, 'paid', (now - timedelta(days=1)).strftime('%Y-%m-%d %H:%M:%S')),
        ('王丽', 1, 3, 15.00, 'paid', (now - timedelta(hours=6)).strftime('%Y-%m-%d %H:%M:%S')),
        ('赵强', 1, 1, 15.00, 'paid', (now - timedelta(hours=4)).strftime('%Y-%m-%d %H:%M:%S')),
        ('刘红', 2, 2, 20.00, 'paid', (now - timedelta(hours=2)).strftime('%Y-%m-%d %H:%M:%S')),
    ]
    
    # 3条已开方但待缴费的记录
    pending_registrations = [
        ('陈伟', 1, 1, 15.00, 'finished', now.strftime('%Y-%m-%d %H:%M:%S')),
        ('孙敏', 1, 3, 15.00, 'finished', (now - timedelta(minutes=30)).strftime('%Y-%m-%d %H:%M:%S')),
        ('周杰', 2, 2, 20.00, 'finished', (now - timedelta(minutes=15)).strftime('%Y-%m-%d %H:%M:%S')),
    ]
    
    # 2条刚挂号待就诊的记录
    waiting_registrations = [
        ('吴琼', 1, 1, 15.00, 'waiting', (now + timedelta(minutes=5)).strftime('%Y-%m-%d %H:%M:%S')),
        ('黄磊', 1, 3, 15.00, 'waiting', (now + timedelta(minutes=10)).strftime('%Y-%m-%d %H:%M:%S')),
    ]
    
    all_registrations = completed_registrations + pending_registrations + waiting_registrations
    
    for reg in all_registrations:
        cursor.execute('INSERT INTO registrations (patient_name, department_id, doctor_id, fee, status, created_at) VALUES (?, ?, ?, ?, ?, ?)', reg)
    
    print("挂号记录插入完成")
    
    # 为已完成的记录和待缴费记录创建处方
    prescriptions_data = []
    prescription_details_data = []
    
    # 已完成记录的处方 (状态为paid)
    for i in range(1, 6):  # registration_id 1-5
        doctor_id = 1 if i % 2 == 1 else 2  # 交替分配医生
        total_amount = 45.50 if i % 2 == 1 else 38.00
        prescriptions_data.append((i, doctor_id, total_amount, 'paid', (now - timedelta(days=2-i*0.4)).strftime('%Y-%m-%d %H:%M:%S')))
    
    # 待缴费记录的处方 (状态为pending_payment)
    for i in range(6, 9):  # registration_id 6-8
        doctor_id = 1 if i % 2 == 0 else 3
        total_amount = 52.00 if i % 2 == 0 else 28.50
        prescriptions_data.append((i, doctor_id, total_amount, 'pending_payment', now.strftime('%Y-%m-%d %H:%M:%S')))
    
    for prescription in prescriptions_data:
        cursor.execute('INSERT INTO prescriptions (registration_id, doctor_id, total_amount, status, created_at) VALUES (?, ?, ?, ?, ?)', prescription)
    
    print("处方主表数据插入完成")
    
    # 创建处方明细
    prescription_details = [
        # 处方1的明细
        (1, 1, 2, 24.00),  # 阿莫西林 2盒
        (1, 2, 3, 25.50),  # 布洛芬 3盒
        # 处方2的明细
        (2, 4, 1, 35.00),  # 云南白药 1盒
        (2, 5, 1, 10.00),  # 碘伏 1瓶
        # 处方3的明细
        (3, 1, 3, 36.00),  # 阿莫西林 3盒
        (3, 3, 2, 10.00),  # 维生素C 2盒
        # 处方4的明细
        (4, 2, 4, 34.00),  # 布洛芬 4盒
        (4, 6, 1, 18.00),  # 999感冒灵 1盒
        # 处方5的明细
        (5, 4, 1, 35.00),  # 云南白药 1盒
        (5, 5, 1, 10.00),  # 碘伏 1瓶
        # 处方6的明细 (待缴费)
        (6, 1, 3, 36.00),  # 阿莫西林 3盒
        (6, 2, 2, 17.00),  # 布洛芬 2盒
        # 处方7的明细 (待缴费)
        (7, 3, 3, 15.00),  # 维生素C 3盒
        (7, 5, 1, 10.00),  # 碘伏 1瓶
        # 处方8的明细 (待缴费)
        (8, 2, 2, 17.00),  # 布洛芬 2盒
        (8, 6, 1, 18.00),  # 999感冒灵 1盒
    ]
    
    cursor.executemany('INSERT INTO prescription_details (prescription_id, drug_id, quantity, subtotal) VALUES (?, ?, ?, ?)', prescription_details)
    print("处方明细数据插入完成")
    
    conn.commit()
    print("所有测试数据插入完成")

def main():
    """主函数"""
    print("开始初始化校医院管理系统数据库...")
    
    # 创建数据库和表结构
    conn = create_database()
    
    # 插入初始数据
    insert_initial_data(conn)
    
    # 关闭数据库连接
    conn.close()
    
    print("\n数据库初始化完成！")
    print("数据库文件：database.db")
    print("\n内置测试账号：")
    print("- 管理员: admin / 123456")
    print("- 挂号员: guahao01 / 123456")
    print("- 收费员: shoufei01 / 123456")
    print("- 药房管理员: yaofang01 / 123456")
    print("- 医生(张三): zhangsan / 123456")
    print("- 医生(李四): lisi / 123456")
    print("- 医生(王五): wangwu / 123456")

if __name__ == '__main__':
    main()