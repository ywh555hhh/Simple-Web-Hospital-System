Simple Web Hospital System好的，这是一个完全独立、自包含的最终版Prompt。它不依赖于任何先前的对话，包含了所有上下文、约束、详细步骤和模板。你可以直接将以下全部内容复制并提交给AI Agent。

---

### **最终任务指令：从零开始构建“校医院医务收费管理系统”**

**致AI Agent:**
你好。你的任务是作为一个全栈开发工程师，为我完整地构建一个名为“校医院医务收费管理系统”的Web应用。请严格遵守以下所有技术规范和开发步骤。项目的最终目标是交付一个功能完整、数据逼真、文档清晰且能够直接运行的课程设计作品。

---

### **第一部分：项目核心规范**

1.  **项目名称:** 校医院医务收费管理系统
2.  **技术栈 (必须严格遵守，禁止使用任何替代品):**
    *   **后端:** Python 3 + Flask。**禁止**使用任何ORM（如SQLAlchemy）。所有数据库交互必须使用Python内置的`sqlite3`库执行原生SQL语句。后端仅作为API服务器，所有接口返回JSON格式数据。
    *   **前端:** 纯HTML文件。**禁止**使用任何前端框架（如Vue, React）或HTML模板引擎（如Jinja2）。
    *   **前端样式:** **Bootstrap 5**，必须通过公共CDN链接在HTML文件中引入。
    *   **前端交互:** **jQuery**，必须通过公共CDN链接在HTML文件中引入，用于所有DOM操作和AJAX请求。
    *   **数据库:** **SQLite**，数据库文件名为 `database.db`。
3.  **语言要求:** 所有面向用户的界面文本（UI）、代码中的注释以及最终的`README.md`文档，都必须使用**中文**。

---

### **第二部分：项目文件结构**

请为项目创建并填充以下所有文件：

```
/校医院管理系统/
├── README.md           # 项目说明文档
├── app.py              # Flask后端主程序
├── database.py         # 数据库初始化与测试数据生成脚本
├── test_api.py         # 后端API接口的独立测试脚本
├── database.db         # (由database.py脚本生成)
├── login.html          # 登录页面
├── index.html          # 系统主页/仪表盘
├── registration.html   # 挂号候诊页面
├── prescription.html   # 医生开具处方页面
├── cashier.html        # 缴费结算页面
├── drug_management.html  # 药品管理页面
├── dept_management.html  # 科室设置页面
├── user_management.html  # 操作员管理页面
└── stats.html          # 查询统计页面
```

---

### **第三部分：详细开发步骤 (请严格按此顺序执行)**

#### **步骤一：创建数据库初始化与测试数据生成脚本 (`database.py`)**

此脚本负责创建数据库表结构并填充丰富、逼真的初始数据。

**1.1 SQL表结构定义:**

```sql
-- 操作员表 (users)
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT UNIQUE NOT NULL,
    password TEXT NOT NULL,
    role TEXT NOT NULL CHECK(role IN ('admin', 'registration', 'doctor', 'cashier', 'pharmacy')),
    full_name TEXT NOT NULL
);

-- 科室表 (departments)
CREATE TABLE IF NOT EXISTS departments (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT UNIQUE NOT NULL
);

-- 医生表 (doctors)
CREATE TABLE IF NOT EXISTS doctors (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER UNIQUE NOT NULL,
    department_id INTEGER NOT NULL,
    status TEXT NOT NULL DEFAULT 'on_duty',
    FOREIGN KEY (user_id) REFERENCES users (id),
    FOREIGN KEY (department_id) REFERENCES departments (id)
);

-- 药品表 (drugs)
CREATE TABLE IF NOT EXISTS drugs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT UNIQUE NOT NULL,
    purchase_price REAL NOT NULL,
    sale_price REAL NOT NULL,
    stock INTEGER NOT NULL,
    min_threshold INTEGER DEFAULT 10,
    max_threshold INTEGER DEFAULT 100
);

-- 挂号记录表 (registrations)
CREATE TABLE IF NOT EXISTS registrations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    patient_name TEXT NOT NULL,
    department_id INTEGER NOT NULL,
    doctor_id INTEGER NOT NULL,
    fee REAL NOT NULL,
    status TEXT NOT NULL DEFAULT 'waiting', -- waiting, finished, paid
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (department_id) REFERENCES departments (id),
    FOREIGN KEY (doctor_id) REFERENCES doctors (id)
);

-- 处方主表 (prescriptions)
CREATE TABLE IF NOT EXISTS prescriptions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    registration_id INTEGER NOT NULL,
    doctor_id INTEGER NOT NULL,
    total_amount REAL NOT NULL,
    status TEXT NOT NULL DEFAULT 'pending_payment', -- pending_payment, paid
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (registration_id) REFERENCES registrations (id),
    FOREIGN KEY (doctor_id) REFERENCES doctors (id)
);

-- 处方明细表 (prescription_details)
CREATE TABLE IF NOT EXISTS prescription_details (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    prescription_id INTEGER NOT NULL,
    drug_id INTEGER NOT NULL,
    quantity INTEGER NOT NULL,
    subtotal REAL NOT NULL,
    FOREIGN KEY (prescription_id) REFERENCES prescriptions (id),
    FOREIGN KEY (drug_id) REFERENCES drugs (id)
);
```

**1.2 初始数据生成:**
请在脚本中插入以下数据，确保逻辑关系正确：
*   **用户与角色:**
    *   (admin) `admin`/`123456`, "系统管理员"
    *   (registration) `guahao01`/`123456`, "王芳"
    *   (cashier) `shoufei01`/`123456`, "李静"
    *   (pharmacy) `yaofang01`/`123456`, "刘伟"
    *   (doctor) `zhangsan`/`123456`, "张三"
    *   (doctor) `lisi`/`123456`, "李四"
    *   (doctor) `wangwu`/`123456`, "王五"
*   **科室:** `内科`, `外科`, `口腔科`, `皮肤科`
*   **医生分配:** 张三和王五分配至`内科`，李四分配至`外科`。
*   **药品 (含库存状态):**
    *   (库存充足) 阿莫西林, 布洛芬, 维生素C (库存 > 100)
    *   (库存正常) 云南白药, 碘伏 (50 < 库存 < 100)
    *   (库存告急) 999感冒灵 (库存 < 10)
*   **模拟历史记录 (至少10条):**
    *   创建**5条已完成全流程的记录** (已挂号 -> 已就诊 -> 已缴费)。
    *   创建**3条已开方但待缴费的记录**。
    *   创建**2条刚挂号待就诊的记录**。

#### **步骤二：实现后端API (`app.py`)**

使用Flask框架，实现所有业务逻辑接口。使用`session`进行用户登录状态管理。

*   `POST /api/login`: 用户登录。
*   `GET /api/logout`: 用户登出。
*   `GET /api/current_user`: 获取当前登录用户信息。
*   **科室管理 (admin):** `GET /api/departments`, `POST /api/departments`, `DELETE /api/departments/<id>`。
*   **药品管理 (pharmacy/admin):** `GET /api/drugs`, `POST /api/drugs`, `PUT /api/drugs/<id>`, `POST /api/drugs/<id>/add_stock`。
*   **挂号 (registration):** `GET /api/doctors_by_dept/<dept_id>`, `POST /api/registrations`。
*   **医生 (doctor):** `GET /api/my_patients`, `POST /api/prescriptions` (此接口需计算总价, 更新挂号状态)。
*   **收费 (cashier):** `GET /api/prescriptions/<id>`, `POST /api/prescriptions/<id>/pay` (此接口需更新处方状态, 并扣减药品库存)。
*   **统计:** `GET /api/stats/today`, `GET /api/stats/drug_inventory`。

#### **步骤三：编写API测试脚本 (`test_api.py`)**

使用`requests`库，编写一个独立的Python脚本来测试所有核心API接口的正确性。脚本应模拟一个完整的业务流程，并在控制台打印清晰的测试结果（例如 "测试管理员登录... 成功"）。

#### **步骤四：开发所有前端页面 (`.html` 文件)**

为每个HTML文件编写代码。所有页面必须：
1.  在`<head>`中通过CDN引入Bootstrap 5 CSS。
2.  在`<body>`底部通过CDN引入jQuery和Bootstrap 5 JS。
3.  使用Bootstrap组件构建干净、响应式的用户界面。
4.  使用jQuery的`$.ajax()`方法与后端API通信，动态加载数据、提交表单和响应用户操作。
5.  在`index.html`页面加载时，通过`/api/current_user`接口获取用户角色，并据此动态显示或隐藏导航栏中对应的功能菜单，实现前端的权限控制。

#### **步骤五：生成项目文档 (`README.md`)**

创建`README.md`文件，并使用以下Markdown模板填充内容，确保提供清晰的项目介绍、安装指南和使用说明。

```markdown
# 校医院医务收费管理系统

## 1. 项目简介

本项目是一个基于Web的校医院医务收费管理系统，旨在模拟真实的医院业务流程，包括挂号、开方、收费、药品管理等核心功能。系统为不同角色（管理员、挂号员、医生、收费员、药房管理员）提供了专属的操作界面和权限控制。

本项目为课程设计作业，技术选型以简洁、易懂、易部署为首要原则，采用经典的前后端分离架构。

## 2. 技术栈

- **后端:** Python 3, Flask
- **前端:** HTML, CSS, JavaScript
- **核心库:** jQuery (AJAX & DOM), Bootstrap 5 (UI)
- **数据库:** SQLite 3

## 3. 主要功能模块

- **全局功能:** 基于角色的用户登录与权限控制
- **挂号员:** 病人挂号、选择科室医生、收取挂号费
- **医生:** 查看待诊患者、开具电子处方
- **收费员:** 查询处方、完成缴费结算
- **药品管理员:** 药品的增、删、改、查、库存管理
- **系统管理员:** 科室管理、操作员管理、医生信息管理
- **查询统计:** 每日收入统计、药品库存查询与预警

## 4. 安装与运行指南

**环境要求:**
- Python 3.6+
- pip

**步骤:**

1.  **克隆或下载项目**并进入项目目录。

2.  **安装依赖:**
    ```bash
    pip install Flask
    ```

3.  **初始化数据库:**
    运行`database.py`脚本来创建数据库并填充测试数据。
    ```bash
    python database.py
    ```
    *注意：每次运行此脚本都会重置数据库。*

4.  **启动后端服务:**
    ```bash
    python app.py
    ```
    服务默认运行在 `http://127.0.0.1:5000`。

5.  **访问系统:**
    在浏览器中打开 `http://127.0.0.1:5000/login.html` 即可开始使用。

## 5. 内置测试账号

- **管理员:** 用户名: `admin`, 密码: `123456`
- **挂号员:** 用户名: `guahao01`, 密码: `123456`
- **医生 (内科):** 用户名: `zhangsan`, 密码: `123456`
- **收费员:** 用户名: `shoufei01`, 密码: `123456`
- **药房管理员:** 用户名: `yaofang01`, 密码: `123456`

```

---
**最终执行命令:**
现在，请开始执行任务。按照上述步骤顺序，为每个指定的文件生成完整、高质量、可直接运行的代码。
