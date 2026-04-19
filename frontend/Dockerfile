# 构建阶段 - 使用国内镜像源
FROM registry.cn-hangzhou.aliyuncs.com/library/node:18-alpine AS builder

WORKDIR /app

# 配置 npm 使用国内镜像
RUN npm config set registry https://registry.npmmirror.com

# 复制依赖文件
COPY package*.json ./

# 安装依赖
RUN npm ci --only=production

# 复制源代码
COPY . .

# 构建生产版本
RUN npm run build

# 生产阶段 - 使用国内 nginx 镜像
FROM registry.cn-hangzhou.aliyuncs.com/library/nginx:alpine

# 复制 Nginx 配置
COPY nginx.conf /etc/nginx/conf.d/default.conf

# 复制构建产物
COPY --from=builder /app/dist /usr/share/nginx/html

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]