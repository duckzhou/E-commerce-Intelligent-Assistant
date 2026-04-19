# 阿里云 Docker 部署指南

## 前置条件

- 阿里云 ECS 服务器（Ubuntu 20.04/22.04 或 CentOS 7/8）
- 已安装 Docker 和 Docker Compose
- 已开放安全组端口：80、8000

## 安装 Docker（如未安装）

### Ubuntu/Debian
```bash
curl -fsSL https://get.docker.com | sh
sudo systemctl enable docker
sudo systemctl start docker
```

### CentOS/RHEL
```bash
curl -fsSL https://get.docker.com | sh
sudo systemctl enable docker
sudo systemctl start docker
```

### 安装 Docker Compose
```bash
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose
```

## 部署步骤

### 1. 上传项目代码

```bash
cd /opt
git clone https://github.com/duckzhou/E-commerce-Intelligent-Assistant.git
cd E-commerce-Intelligent-Assistant
```

### 2. 配置环境变量

```bash
nano backend/.env
```

确保配置正确：
```env
DASHSCOPE_API_KEY=your-api-key
DASHSCOPE_BASE_URL=https://dashscope.aliyuncs.com/compatible-mode/v1
LLM_MODEL=qwen-turbo
EMBEDDING_MODEL=text-embedding-v3
DATABASE_URL=sqlite:///./data/app.db
CHROMA_PATH=./data/chroma_db
```

### 3. 一键启动

```bash
docker-compose up -d
```

### 4. 查看服务状态

```bash
docker-compose ps
docker-compose logs -f
```

### 5. 访问应用

- 前端：`http://your-server-ip:80`
- 后端 API：`http://your-server-ip:8000`

## 常用管理命令

### 停止服务
```bash
docker-compose down
```

### 重启服务
```bash
docker-compose restart
```

### 查看日志
```bash
# 所有日志
docker-compose logs -f

# 后端日志
docker-compose logs -f backend

# 前端日志
docker-compose logs -f frontend
```

### 更新代码
```bash
git pull
docker-compose up -d --build
```

### 清理无用镜像
```bash
docker image prune -f
```

## 安全组配置

在阿里云控制台开放以下端口：

| 端口 | 协议 | 用途 |
|------|------|------|
| 80 | TCP | 前端 HTTP 访问 |
| 443 | TCP | HTTPS（可选） |
| 22 | TCP | SSH 远程管理 |

## 故障排查

### 容器启动失败
```bash
docker-compose logs backend
docker-compose logs frontend
```

### 进入容器调试
```bash
docker exec -it ecommerce-backend sh
docker exec -it ecommerce-frontend sh
```

### 检查后端 API
```bash
curl http://localhost:8000/docs/