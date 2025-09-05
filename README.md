# 工序表管理系统api接口

## 项目简介
这是一个基于Django和Django REST Framework开发的工序表管理系统后端API，提供完整的工艺路线、工单和任务管理功能，适用于制造业生产流程管理场景。本项目是作者的第一个django练手项目。

## 技术栈
- Django 5.2.5
- Django REST Framework
- SQLite3

## 功能模块

### 1. 工序管理 (Process)
- 创建、查询、更新和删除工序信息
- 工序包含名称和描述等基本信息

### 2. 工艺路线管理 (Route)
- 创建、查询、更新和删除工艺路线
- 工艺路线包含多个工序，通过中间表RouteProcess维护工序顺序
- 支持工序在工艺路线中的顺序管理

### 3. 工单管理 (WorkOrder)
- 创建、查询、更新和删除工单
- 工单状态流转管理：草稿(draft) → 已提交(submitted) → 已审核(approved) | 已排产(scheduled)
- 工单与工艺路线一对一关联
- 已排产工单的工艺路线修改限制

### 4. 任务管理 (Task)
- 任务是工单和工序的具体执行实例
- 支持任务状态管理：未生产(pending) → 未报工(unreported) → 进行中(in_progress) → 已完成(completed)
- 已排产工单的任务状态变更约束
  - 当前置所有工序已完成且后置所有工序为未生产状态时，才能修改该工序的状态
  - 已完成或进行中的任务不允许修改

### 5. 工单拆分功能
- 将已审核工单按照工艺路线自动拆分为多个任务
- 支持同一工艺路线中重复工序的处理，每个重复工序创建一个独立的任务

## API接口文档

### 1. 工序管理 (Process)
- **GET /api/processes/** - 获取所有工序列表
- **POST /api/processes/** - 创建新工序
- **GET /api/processes/{id}/** - 获取特定工序详情
- **PUT/PATCH /api/processes/{id}/** - 更新特定工序
- **DELETE /api/processes/{id}/** - 删除特定工序

### 2. 工艺路线管理 (Route)
- **GET /api/routes/** - 获取所有工艺路线列表
- **POST /api/routes/** - 创建新工艺路线
- **GET /api/routes/{id}/** - 获取特定工艺路线详情
- **PUT/PATCH /api/routes/{id}/** - 更新特定工艺路线
- **DELETE /api/routes/{id}/** - 删除特定工艺路线

### 3. 工单管理 (WorkOrder)
- **GET /api/workorders/** - 获取所有工单列表
- **POST /api/workorders/** - 创建新工单
- **GET /api/workorders/{id}/** - 获取特定工单详情
- **PUT/PATCH /api/workorders/{id}/** - 更新特定工单
- **DELETE /api/workorders/{id}/** - 删除特定工单

### 4. 任务管理 (Task)
- **GET /api/tasks/** - 获取所有任务列表
- **POST /api/tasks/** - 创建新任务
- **GET /api/tasks/{id}/** - 获取特定任务详情
- **PUT/PATCH /api/tasks/{id}/** - 更新特定任务
- **DELETE /api/tasks/{id}/** - 删除特定任务

### 5. 工单拆分接口
- **POST /api/workorders/{id}/split/** - 拆分工单，将已审核工单拆分为多个任务并更新状态为已排产

## 安装与运行

### 本地开发环境

#### 前提条件
- Python 3.8+ 已安装
- pip 包管理器

### 安装步骤

1. 克隆项目代码
```bash
git clone https://github.com/rh666666/Process_Table.git
cd Process_Table
```

2. 创建虚拟环境
```bash
python -m venv .venv
```

3. 激活虚拟环境
```bash
# Windows
.venv\Scripts\activate

# macOS/Linux
source .venv/bin/activate
```

4. 安装依赖
```bash
pip install -r requirements.txt
```

5. 运行数据库迁移
```bash
python manage.py migrate
```

6. 启动开发服务器
```bash
python manage.py runserver
```

API服务将在 http://127.0.0.1:8000/api/ 上运行

## 数据模型关系图

```
Process (工序)
    |
    | 多对多 (通过RouteProcess中间表)
    |
Route (工艺路线) <-- 一对一 --> WorkOrder (工单)
    |                             |
    |                             | 一对多
    |                             |
RouteProcess (工艺路线工序关系) <-- 一对多 -- Task (任务)
```

## 关键业务规则

1. **工单状态流转规则**
   - 已审核的工单需要反审核后才能修改
   - 只有草稿状态的工单才能被修改
   - 已排产的工单不可删除

2. **任务状态变更约束**
   - 已排产工单的进行中或已完成任务不允许修改
   - 只有当前置所有工序已完成且后置所有工序为未生产状态时，才能修改该工序的状态

3. **已排产工单修改限制**
   - 已排产的工单只能修改未生产和未报工状态的工序

## Docker部署

除了本地开发环境外，项目还支持使用Docker容器化部署，简化环境配置和部署流程。

### 前提条件
- Docker 已安装
- Docker Compose 已安装

### 部署步骤

1. 确保项目根目录下有以下Docker相关文件：
   - `Dockerfile`
   - `docker-compose.yml`

2. 构建并启动容器：

```bash
docker compose up -d
```

3. 查看容器运行状态：

```bash
docker ps
```

4. API服务将在 http://localhost:8000/api/ 上运行

### 常用Docker命令

- 停止容器：
```bash
docker compose down
```

- 查看容器日志：
```bash
docker compose logs -f
```

- 进入容器内部：
```bash
docker exec -it process_table_web_1 /bin/bash
```

## 测试

运行项目测试套件：
```bash
python manage.py test
```

当前包含10个测试用例，覆盖工序顺序管理、工单状态流转、任务状态变更约束等核心功能。

## 注意事项

1. 本项目默认使用SQLite数据库，适用于开发和测试环境，生产环境建议使用PostgreSQL或MySQL等专业数据库

2. Docker部署模式下，已默认设置`DEBUG=False`和`ALLOWED_HOSTS=*`，适合生产环境使用

3. 目前API没有实现身份验证和授权机制，生产环境应添加适当的安全措施

4. 日志系统已配置，关键操作会记录日志信息

5. 使用Docker部署时，SQLite数据库文件会保存在容器内部，如需持久化存储，可在`docker-compose.yml`中添加卷映射

6. 如需使用PostgreSQL数据库，请取消`docker-compose.yml`中相关配置的注释，并在`.env`文件中配置数据库连接信息

## 开发指南

1. 创建新的模型后，运行以下命令生成迁移文件并应用：
```bash
python manage.py makemigrations app
python manage.py migrate
```

2. 如需添加新的API端点，请在views.py中创建相应的视图，并在urls.py中注册路由

3. 所有功能变更应添加相应的测试用例，确保代码质量和功能稳定性