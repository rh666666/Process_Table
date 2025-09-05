#!/bin/bash
# 文件已改为 unix 格式
# 只有当前目录不存在db.sqlite3时才会执行以下操作，即初始化
if [ ! -f "db.sqlite3" ]; then
    echo "初始化数据库……"

    # 运行数据库迁移
    python manage.py makemigrations app
    python manage.py migrate
fi

# 启动应用
uvicorn Process_Table.asgi:application --host 0.0.0.0 --port 8000
