# 使用阿里云镜像
FROM alibaba-cloud-linux-3-registry.cn-hangzhou.cr.aliyuncs.com/alinux3/python:3.11.1

# 设置工作目录
WORKDIR /app

# 安装系统依赖（阿里云 Linux 使用 yum）
RUN yum install -y \
    gcc \
    && yum clean all

# 安装 uv（使用国内镜像源）
RUN pip install --index-url https://pypi.tuna.tsinghua.edu.cn/simple uv

# 复制依赖文件
COPY pyproject.toml uv.lock ./

# 使用 uv 安装依赖（使用清华镜像源）
RUN uv pip install --system -e . --index-url https://pypi.tuna.tsinghua.edu.cn/simple/

# 复制应用代码
COPY app/ ./app/

# 创建数据目录
RUN mkdir -p /app/data

# 暴露端口
EXPOSE 8000

# 启动命令
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]