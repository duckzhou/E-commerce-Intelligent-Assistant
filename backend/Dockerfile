FROM python:3.10-slim

WORKDIR /app

# 安装依赖
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# 安装 uv
RUN pip install --no-cache-dir uv

# 复制依赖文件
COPY pyproject.toml uv.lock ./

# 使用 uv 安装 Python 依赖
RUN uv pip install --system --no-cache-dir -e .

# 复制应用代码
COPY app/ ./app/

# 创建数据目录
RUN mkdir -p /app/data

# 暴露端口
EXPOSE 8000

# 启动命令
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]