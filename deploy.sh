#!/bin/bash
# 千广传媒主播智能问答助手 - 阿里云部署脚本
# 使用方法: sudo ./deploy.sh

set -e

echo "========================================="
echo "千广传媒主播智能问答助手 - 部署脚本"
echo "========================================="

# 配置变量
APP_DIR="/opt/ecommerce-assistant"
BACKEND_PORT=8000
FRONTEND_PORT=80

# 检查是否以 root 运行
if [ "$EUID" -ne 0 ]; then 
    echo "请使用 sudo 运行此脚本"
    exit 1
fi

# 1. 安装系统依赖
echo ""
echo "[1/6] 安装系统依赖..."

# 检测系统类型
if command -v apt &> /dev/null; then
    echo "检测到 Debian/Ubuntu 系统"
    apt update
    apt install -y python3 python3-pip python3-venv nodejs npm git curl
elif command -v yum &> /dev/null; then
    echo "检测到 CentOS/RHEL 系统"
    yum update -y
    yum install -y python3 python3-pip git curl
    # CentOS 可能需要安装 EPEL 源来获取 nodejs
    yum install -y epel-release
    yum install -y nodejs npm
else
    echo "不支持的系统，请手动安装依赖"
    exit 1
fi

# 2. 创建应用目录
echo ""
echo "[2/6] 创建应用目录..."
mkdir -p $APP_DIR
mkdir -p $APP_DIR/backend/data

# 3. 复制项目文件
echo ""
echo "[3/6] 复制项目文件..."
# 假设脚本在项目根目录运行
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cp -r $SCRIPT_DIR/backend/* $APP_DIR/backend/
cp -r $SCRIPT_DIR/frontend $APP_DIR/frontend-src/

# 4. 部署后端
echo ""
echo "[4/6] 部署后端..."
cd $APP_DIR/backend

# 创建虚拟环境
python3 -m venv .venv
source .venv/bin/activate
pip install -e . --quiet

# 5. 部署前端
echo ""
echo "[5/6] 部署前端..."
cd $APP_DIR/frontend-src

# 安装前端依赖并构建
npm install
npm run build

# 将构建产物移动到主目录
mkdir -p $APP_DIR/frontend
cp -r dist/* $APP_DIR/frontend/

# 6. 创建 systemd 服务
echo ""
echo "[6/6] 创建系统服务..."

# 后端服务
cat > /etc/systemd/system/ecommerce-backend.service << EOF
[Unit]
Description=千广传媒主播智能问答助手 - 后端
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=$APP_DIR/backend
Environment=PATH=$APP_DIR/backend/.venv/bin:/usr/bin
ExecStart=$APP_DIR/backend/.venv/bin/uvicorn app.main:app --host 0.0.0.0 --port $BACKEND_PORT
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
EOF

# 前端服务
cat > /etc/systemd/system/ecommerce-frontend.service << EOF
[Unit]
Description=千广传媒主播智能问答助手 - 前端
After=network.target ecommerce-backend.service

[Service]
Type=simple
User=root
WorkingDirectory=$APP_DIR/frontend
ExecStart=/usr/bin/python3 -m http.server $FRONTEND_PORT --directory $APP_DIR/frontend
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
EOF

# 启用并启动服务
systemctl daemon-reload
systemctl enable ecommerce-backend
systemctl enable ecommerce-frontend
systemctl start ecommerce-backend
systemctl start ecommerce-frontend

echo ""
echo "========================================="
echo "部署完成！"
echo "========================================="
echo ""
echo "后端服务: http://localhost:$BACKEND_PORT"
echo "前端访问: http://localhost:$FRONTEND_PORT"
echo ""
echo "服务管理命令:"
echo "  查看状态: systemctl status ecommerce-backend ecommerce-frontend"
echo "  重启服务: systemctl restart ecommerce-backend ecommerce-frontend"
echo "  查看日志: journalctl -u ecommerce-backend -f"
echo ""