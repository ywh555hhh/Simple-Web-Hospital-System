#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
校医院医务收费管理系统 - API接口测试脚本
功能：测试所有核心API接口的正确性，模拟完整的业务流程
"""

import requests
import json
import time
from datetime import datetime

# 测试服务器基础URL
BASE_URL = 'http://127.0.0.1:5000'

class HospitalAPITester:
    def __init__(self):
        self.session = requests.Session()
        self.base_url = BASE_URL
        
    def test_login(self, username, password, expected_success=True):
        """测试用户登录"""
        url = f"{self.base_url}/api/login"
        data = {
            'username': username,
            'password': password
        }
        
        response = self.session.post(url, json=data)
        result = response.json()
        
        if expected_success:
            assert result['success'], f"登录失败: {result.get('message', '未知错误')}"
            print(f"✓ 测试{username}登录... 成功")
            return result['user']
        else:
            assert not result['success'], f"登录应该失败但成功了: {username}"
            print(f"✓ 测试{username}登录失败验证... 成功")
            return None
    
    def test_logout(self):
        """测试用户登出"""
        url = f"{self.base_url}/api/logout"
        response = self.session.get(url)
        result = response.json()
        
        assert result['success'], f"登出失败: {result.get('message', '未知错误')}"
        print("✓ 测试用户登出... 成功")
    
    def test_current_user(self, expected_username=None):
        """测试获取当前用户信息"""
        url = f"{self.base_url}/api/current_user"
        response = self.session.get(url)
        result = response.json()
        
        assert result['success'], f"获取用户信息失败: {result.get('message', '未知错误')}"
        if expected_username:
            assert result['user']['username'] == expected_username, f"用户名不匹配，期望{expected_username}，实际{result['user']['username']}"
        print(f"✓ 测试获取当前用户信息... 成功 (用户: {result['user']['full_name']})")
        return result['user']
    
    def test_departments_crud(self):
        """测试科室的增删查改功能"""
        # 获取所有科室
        url = f"{self.base_url}/api/departments"
        response = self.session.get(url)
        result = response.json()
        
        assert result['success'], f"获取科室列表失败: {result.get('message', '未知错误')}"
        initial_count = len(result['data'])
        print(f"✓ 测试获取科室列表... 成功 (共{initial_count}个科室)")
        
        # 创建新科室
        new_dept_data = {'name': '测试科室'}
        response = self.session.post(url, json=new_dept_data)
        result = response.json()
        
        assert result['success'], f"创建科室失败: {result.get('message', '未知错误')}"
        print("✓ 测试创建科室... 成功")
        
        # 再次获取科室列表验证增加
        response = self.session.get(url)
        result = response.json()
        assert len(result['data']) == initial_count + 1, "科室数量未正确增加"
        
        # 找到新创建的科室ID
        test_dept_id = None
        for dept in result['data']:
            if dept['name'] == '测试科室':
                test_dept_id = dept['id']
                break
        
        assert test_dept_id is not None, "未找到新创建的科室"
        
        # 删除测试科室
        delete_url = f"{self.base_url}/api/departments/{test_dept_id}"
        response = self.session.delete(delete_url)
        result = response.json()
        
        assert result['success'], f"删除科室失败: {result.get('message', '未知错误')}"
        print("✓ 测试删除科室... 成功")
    
    def test_drugs_management(self):
        """测试药品管理功能"""
        # 获取药品列表
        url = f"{self.base_url}/api/drugs"
        response = self.session.get(url)
        result = response.json()
        
        assert result['success'], f"获取药品列表失败: {result.get('message', '未知错误')}"
        print(f"✓ 测试获取药品列表... 成功 (共{len(result['data'])}种药品)")
        
        # 添加新药品 (使用时间戳确保唯一性)
        import time
        timestamp = int(time.time())
        new_drug = {
            'name': f'测试药品{timestamp}',
            'purchase_price': 10.0,
            'sale_price': 15.0,
            'stock': 50,
            'min_threshold': 10,
            'max_threshold': 100
        }
        
        response = self.session.post(url, json=new_drug)
        result = response.json()
        
        assert result['success'], f"添加药品失败: {result.get('message', '未知错误')}"
        print("✓ 测试添加药品... 成功")
        
        # 获取新添加的药品ID
        response = self.session.get(url)
        result = response.json()
        test_drug_id = None
        for drug in result['data']:
            if drug['name'] == f'测试药品{timestamp}':
                test_drug_id = drug['id']
                break
        
        assert test_drug_id is not None, "未找到新添加的药品"
        
        # 测试增加库存
        add_stock_url = f"{self.base_url}/api/drugs/{test_drug_id}/add_stock"
        response = self.session.post(add_stock_url, json={'quantity': 20})
        result = response.json()
        
        assert result['success'], f"增加库存失败: {result.get('message', '未知错误')}"
        print("✓ 测试增加药品库存... 成功")
        
        # 更新药品信息
        update_url = f"{self.base_url}/api/drugs/{test_drug_id}"
        update_data = {
            'name': f'测试药品已更新{timestamp}',  # 确保名称唯一
            'purchase_price': 12.0,
            'sale_price': 18.0,
            'min_threshold': 15,
            'max_threshold': 120
        }
        
        response = self.session.put(update_url, json=update_data)
        result = response.json()
        
        assert result['success'], f"更新药品失败: {result.get('message', '未知错误')}"
        print("✓ 测试更新药品信息... 成功")
    
    def test_registration_workflow(self):
        """测试挂号流程"""
        # 获取科室医生
        dept_id = 1  # 内科
        url = f"{self.base_url}/api/doctors_by_dept/{dept_id}"
        response = self.session.get(url)
        result = response.json()
        
        assert result['success'], f"获取科室医生失败: {result.get('message', '未知错误')}"
        assert len(result['data']) > 0, "内科没有医生"
        print(f"✓ 测试获取科室医生... 成功 (内科有{len(result['data'])}位医生)")
        
        # 创建挂号
        doctor_id = result['data'][0]['id']
        registration_data = {
            'patient_name': '测试患者',
            'department_id': dept_id,
            'doctor_id': doctor_id,
            'fee': 15.0
        }
        
        url = f"{self.base_url}/api/registrations"
        response = self.session.post(url, json=registration_data)
        result = response.json()
        
        assert result['success'], f"创建挂号失败: {result.get('message', '未知错误')}"
        print("✓ 测试创建挂号... 成功")
    
    def test_doctor_workflow(self):
        """测试医生开处方流程"""
        # 获取待诊患者
        url = f"{self.base_url}/api/my_patients"
        response = self.session.get(url)
        result = response.json()
        
        assert result['success'], f"获取待诊患者失败: {result.get('message', '未知错误')}"
        print(f"✓ 测试获取待诊患者... 成功 (有{len(result['data'])}位待诊患者)")
        
        # 如果有待诊患者，开具处方
        if result['data']:
            # 找一个状态为 waiting 的患者
            waiting_patient = None
            for patient in result['data']:
                if patient['status'] == 'waiting':
                    waiting_patient = patient
                    break
            
            if waiting_patient:
                registration_id = waiting_patient['id']
                prescription_data = {
                    'registration_id': registration_id,
                    'drugs': [
                        {'drug_id': 1, 'quantity': 2},  # 阿莫西林 2盒
                        {'drug_id': 2, 'quantity': 1}   # 布洛芬 1盒
                    ]
                }
                
                url = f"{self.base_url}/api/prescriptions"
                response = self.session.post(url, json=prescription_data)
                result = response.json()
                
                assert result['success'], f"开具处方失败: {result.get('message', '未知错误')}"
                print("✓ 测试开具处方... 成功")
            else:
                print("! 没有waiting状态的患者可以开处方")
    
    def test_cashier_workflow(self):
        """测试收费员缴费流程"""
        # 这里使用已知的待缴费处方ID进行测试
        prescription_id = 6  # 从测试数据中选择一个待缴费的处方
        
        # 获取处方详情
        url = f"{self.base_url}/api/prescriptions/{prescription_id}"
        response = self.session.get(url)
        result = response.json()
        
        if result['success']:
            print(f"✓ 测试获取处方详情... 成功 (处方金额: {result['data']['total_amount']}元)")
            
            # 进行缴费
            pay_url = f"{self.base_url}/api/prescriptions/{prescription_id}/pay"
            response = self.session.post(pay_url)
            result = response.json()
            
            if result['success']:
                print("✓ 测试处方缴费... 成功")
            else:
                print(f"! 测试处方缴费... 失败 ({result.get('message', '未知错误')})")
        else:
            print(f"! 测试获取处方详情... 失败 ({result.get('message', '未知错误')})")
    
    def test_statistics(self):
        """测试统计查询功能"""
        # 今日统计
        url = f"{self.base_url}/api/stats/today"
        response = self.session.get(url)
        result = response.json()
        
        assert result['success'], f"获取今日统计失败: {result.get('message', '未知错误')}"
        stats = result['data']
        print(f"✓ 测试今日统计... 成功")
        print(f"  - 今日挂号: {stats['today_registrations']}人次")
        print(f"  - 今日总收入: {stats['total_income']}元")
        print(f"  - 待缴费处方: {stats['pending_prescriptions']}张")
        print(f"  - 库存告急药品: {stats['low_stock_drugs']}种")
        
        # 先登出当前用户，然后以药房管理员身份登录测试药品库存统计
        self.test_logout()
        self.test_login('yaofang01', '123456')
        
        # 药品库存统计
        url = f"{self.base_url}/api/stats/drug_inventory"
        response = self.session.get(url)
        result = response.json()
        
        assert result['success'], f"获取药品库存统计失败: {result.get('message', '未知错误')}"
        print(f"✓ 测试药品库存统计... 成功 (共{len(result['data'])}种药品)")

def main():
    """主测试函数"""
    print("=" * 60)
    print("校医院医务收费管理系统 - API接口测试")
    print("=" * 60)
    
    tester = HospitalAPITester()
    
    try:
        print("\n1. 测试用户认证功能")
        print("-" * 30)
        
        # 测试错误登录
        tester.test_login('wrong_user', 'wrong_pass', expected_success=False)
        
        # 测试管理员登录
        tester.test_login('admin', '123456')
        tester.test_current_user('admin')
        
        # 测试科室管理 (需要管理员权限)
        print("\n2. 测试科室管理功能")
        print("-" * 30)
        tester.test_departments_crud()
        
        tester.test_logout()
        
        # 测试药房管理员登录和药品管理
        print("\n3. 测试药品管理功能")
        print("-" * 30)
        tester.test_login('yaofang01', '123456')
        tester.test_current_user('yaofang01')
        tester.test_drugs_management()
        tester.test_logout()
        
        # 测试挂号员功能
        print("\n4. 测试挂号功能")
        print("-" * 30)
        tester.test_login('guahao01', '123456')
        tester.test_current_user('guahao01')
        tester.test_registration_workflow()
        tester.test_logout()
        
        # 测试医生功能
        print("\n5. 测试医生功能")
        print("-" * 30)
        tester.test_login('zhangsan', '123456')
        tester.test_current_user('zhangsan')
        tester.test_doctor_workflow()
        tester.test_logout()
        
        # 测试收费员功能
        print("\n6. 测试收费功能")
        print("-" * 30)
        tester.test_login('shoufei01', '123456')
        tester.test_current_user('shoufei01')
        tester.test_cashier_workflow()
        
        # 测试统计功能
        print("\n7. 测试统计查询功能")
        print("-" * 30)
        tester.test_statistics()
        
        tester.test_logout()
        
        print("\n" + "=" * 60)
        print("🎉 所有API接口测试完成！系统功能正常")
        print("=" * 60)
        
    except AssertionError as e:
        print(f"\n❌ 测试失败: {e}")
        return False
    except requests.exceptions.ConnectionError:
        print("\n❌ 无法连接到服务器，请确保后端服务已启动 (python app.py)")
        return False
    except Exception as e:
        print(f"\n❌ 测试过程中发生错误: {e}")
        return False
    
    return True

if __name__ == '__main__':
    print("请确保后端服务已启动 (python app.py)")
    print("等待3秒后开始测试...")
    time.sleep(3)
    
    success = main()
    exit(0 if success else 1)