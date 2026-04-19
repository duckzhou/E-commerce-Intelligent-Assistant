# 使用 Node.js 镜像
FROM alibaba-cloud-linux-3-registry.cn-hangzhou.cr.aliyuncs.com/alinux3/node:20.16

WORKDIR /app

# 配置 npm 使用国内镜像
RUN npm config set registry https://registry.npmmirror.com

# 只复制 package.json
COPY package.json ./

# 安装所有依赖
RUN npm install

# 复制源代码
COPY . .

# 暴露端口
EXPOSE 3000

# 使用 Vite 开发服务器启动
CMD ["npm", "run", "dev", "--", "--host", "0.0.0.0"]