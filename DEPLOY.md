# 阿里云部署指南

## 前置条件

- 阿里云 ECS 服务器（推荐 Ubuntu 20.04/22.04）
- 已开放安全组端口：80、8000
- 已获取服务器 SSH 访问权限

## 部署步骤

### 1. 连接服务器

```bash
ssh root@your-server-ip
```

### 2. 上传项目代码

**方式一：使用 Git（推荐）**

```bash
cd /opt
git clone https://github.com/duckzhou/E-commerce-Intelligent-Assistant.git
cd E-commerce-Intelligent-Assistant
```

**方式二：使用 SCP 上传**

在本地执行：
```bash
scp -r /path/to/project root@your-server-ip:/opt/ecommerce-assistant
```

### 3. 修改后端配置

```bash
cd /opt/ecommerce-assistant/backend
nano .env
```

确保 `.env` 文件中的配置正确：
```env
# 通义千问API配置
DASHSCOPE_API_KEY=your-api-key
DASHSCOPE_BASE_URL=https://dashscope.aliyuncs.com/compatible-mode/v1
LLM_MODEL=qwen-turbo
EMBEDDING_MODEL=text-embedding-v3

# 数据库
DATABASE_URL=sqlite:///./data/app.db

# ChromaDB
CHROMA_PATH=./data/chroma_db
```

### 4. 修改前端 API 地址

```bash
cd /opt/ecommerce-assistant/frontend
nano .env.production
```

修改为实际的后端地址：
```env
VITE_API_BASE_URL=http://your-server-ip:8000
```

### 5. 执行部署脚本

```bash
cd /opt/ecommerce-assistant
chmod +x deploy.sh
sudo ./deploy.sh
```

### 6. 检查服务状态

```bash
# 查看后端服务状态
systemctl status ecommerce-backend

# 查看前端服务状态
systemctl status ecommerce-frontend

# 查看后端日志
journalctl -u ecommerce-backend -f
```

### 7. 访问应用

- 前端：`http://your-server-ip:80`
- 后端 API：`http://your-server-ip:8000`

## 常用管理命令

### 重启服务

```bash
sudo systemctl restart ecommerce-backend
sudo systemctl restart ecommerce-frontend
```

### 停止服务

```bash
sudo systemctl stop ecommerce-backend
sudo systemctl stop ecommerce-frontend
```

### 更新代码

```bash
cd /opt/ecommerce-assistant
git pull

# 重新部署后端
cd backend
source .venv/bin/activate
pip install -e .
sudo systemctl restart ecommerce-backend

# 重新构建前端
cd ../frontend-src
npm install
npm run build
cp -r dist/* /opt/ecommerce-assistant/frontend/
sudo systemctl restart ecommerce-frontend
```

## 安全组配置

在阿里云控制台开放以下端口：

| 端口 | 协议 | 用途 |
|------|------|------|
| 80 | TCP | 前端 HTTP 访问 |
| 8000 | TCP | 后端 API（可选，仅调试时开放） |
| 22 | TCP | SSH 远程管理 |

## 故障排查

### 后端启动失败

```bash
# 查看详细日志
journalctl -u ecommerce-backend -n 50 --no-pager

# 手动启动测试
cd /opt/ecommerce-assistant/backend
source .venv/bin/activate
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

### 前端无法访问

```bash
# 检查前端服务
systemctl status ecommerce-frontend

# 检查文件是否存在
ls -la /opt/ecommerce-assistant/frontend/
```

### API 请求失败

```bash
# 测试后端 API
curl http://localhost:8000/docs/

# 检查防火墙
sudo ufw status