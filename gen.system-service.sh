#!/bin/bash

# 定义变量
SERVICE_NAME="mosdns"
USER="root"
WORKDIR=$(dirname $(readlink -f $0))
CONFIG_FILE="$WORKDIR/config_custom.yaml"
EXEC_START="$WORKDIR/bin/mosdns start -c $CONFIG_FILE -d $WORKDIR"
SERVICE_FILE="./$SERVICE_NAME.service"
SYSTEMD_DIR="/etc/systemd/system"

# 生成 service 文件
gen() {
    # 生成 service 文件内容
    SERVICE_CONTENT="[Unit]
Description=MosDNS Service
After=network.target

[Service]
Type=simple
User=$USER
WorkingDirectory=$WORKDIR
ExecStart=$EXEC_START
Restart=always
RestartSec=3

[Install]
WantedBy=multi-user.target"

    # 写入 service 文件
    echo "$SERVICE_CONTENT" > $SERVICE_FILE
    echo "Service file created at $SERVICE_FILE"
}

# 安装 service 文件到系统目录
install() {
    if [ ! -f $SERVICE_FILE ]; then
        echo "Service file not found. Please run 'gen' first."
        exit 1
    fi

    mv $SERVICE_FILE $SYSTEMD_DIR/
    systemctl daemon-reload
    echo "Service file installed to $SYSTEMD_DIR/"
}

# 启用并启动服务
enable() {
    systemctl enable $SERVICE_NAME
    systemctl start $SERVICE_NAME
    echo "Service $SERVICE_NAME enabled and started"
}

# 主逻辑
case "$1" in
    gen)
        gen
        ;;
    install)
        install
        ;;
    enable)
        enable
        ;;
    *)
        echo "Usage: $0 {gen|install|enable}"
        echo "  gen     - Generate service file"
        echo "  install - Install service to system"
        echo "  enable  - Enable and start service"
        exit 1
        ;;
esac
