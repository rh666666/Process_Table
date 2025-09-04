#!/bin/bash

# 只有当前目录不存在db.sqlite3时才会执行以下操作，即初始化
if [ ! -f "db.sqlite3" ]; then
    echo "初始化数据库……"

    # 运行数据库迁移
    python manage.py makemigrations app
    python manage.py migrate

    # 收集静态文件，建议使用nginx反向代理
    python manage.py collectstatic --no-input
fi

# 启动应用
uvicorn Process_Table.asgi:application --host 0.0.0.0 --port 8000
