#!/bin/bash
set -e

echo "🚀 启动闲鱼自动回复系统..."
echo "📊 数据库将在应用启动时自动初始化..."
echo "🎯 启动主应用..."

# 确保数据目录存在
mkdir -p /app/data /app/logs /app/backups /app/static/uploads/images

# 设置目录权限
chmod 777 /app/data /app/logs /app/backups /app/static/uploads /app/static/uploads/images

# 启动主应用
exec python Start.py
