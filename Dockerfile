# 使用官方Python镜像作为基础镜像
FROM python:3.11-slim-bullseye

# 设置工作目录
WORKDIR /app

# 设置环境变量
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# 安装系统依赖
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    python3-dev \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# 复制requirements.txt文件
COPY requirements.txt .

# 安装Python依赖
RUN pip install --upgrade pip && pip install -r requirements.txt

# 复制整个项目代码
COPY . .

# 运行数据库迁移
RUN python manage.py makemigrations
RUN python manage.py migrate

# 暴露端口
EXPOSE 8000

# 使用uvicorn作为ASGI服务器运行应用
CMD ["uvicorn", "Process_Table.asgi:application", "--host", "0.0.0.0", "--port", "8000"]
