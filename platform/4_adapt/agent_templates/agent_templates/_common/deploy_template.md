# DLV 部署模板
# 用途: 内阁项目标准部署配置
# 支持: Docker / 直接运行

# ============================================================
# 方式一: Docker 部署
# ============================================================
# 复制此段到项目根目录 Dockerfile

# ---- Dockerfile 模板 ----
# FROM python:3.11-slim
# WORKDIR /app
# COPY requirements.txt .
# RUN pip install --no-cache-dir -r requirements.txt
# COPY . .
# EXPOSE 8000
# CMD ["python", "src/engine.py"]

# ---- docker-compose.yml 模板 ----
# version: "3.9"
# services:
#   app:
#     build: .
#     ports:
#       - "8000:8000"
#     volumes:
#       - ./config:/app/config
#       - ./output:/app/output
#     environment:
#       - LOG_LEVEL=INFO

# ============================================================
# 方式二: 直接运行 (Windows)
# ============================================================

# ---- run.bat 模板 ----
# @echo off
# echo Starting {{PROJECT_NAME}}...
# pip install -r requirements.txt 2>nul
# python src/engine.py
# pause

# ============================================================
# 方式三: systemd 服务 (Linux)
# ============================================================

# ---- /etc/systemd/system/{{PROJECT_NAME}}.service 模板 ----
# [Unit]
# Description={{PROJECT_NAME}} Service
# After=network.target
#
# [Service]
# Type=simple
# User=app
# WorkingDirectory=/opt/{{PROJECT_NAME}}
# ExecStart=/usr/bin/python3 src/engine.py
# Restart=on-failure
# RestartSec=10
#
# [Install]
# WantedBy=multi-user.target
