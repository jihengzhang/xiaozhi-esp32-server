#!/bin/bash
# MR MCP Server 管理脚本
# 用法: ./mr_mcp_server.sh [--start|--stop|--status]

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
LOG_DIR="$SCRIPT_DIR/logs"
PID_DIR="$SCRIPT_DIR/.pids"

mkdir -p "$LOG_DIR" "$PID_DIR"

# 服务配置
# CONDA_PYTHON="/home/tester/miniconda3/envs/audio_env/bin/python"  #this is env for Z8G4-H
# CONDA_PYTHON="/home/tester/miniconda3/envs/audio_env/bin/python"  #this is env for Z8G4-H
CONDA_PYTHON="/home/tester/anaconda3/envs/env_asr/bin/python"  #this is env for Z8G4-M

declare -A SERVICES=(
    ["ai_server"]="$CONDA_PYTHON -u app.py|$SCRIPT_DIR|ai_server"
    ["http_server"]="$CONDA_PYTHON -u start_https_server.py|$SCRIPT_DIR/MR_MCP_Tool|http_server"
    ["mr_mcp"]="$CONDA_PYTHON -u mcp_http_bridge.py|$SCRIPT_DIR/MR_MCP_Tool/py|mr_mcp"
)

start_service() {
    local name=$1
    local config=${SERVICES[$name]}
    IFS='|' read -r cmd dir log_name <<< "$config"
    
    local pid_file="$PID_DIR/${log_name}.pid"
    local log_file="$LOG_DIR/${log_name}.log"
    
    if [ -f "$pid_file" ] && ps -p $(cat "$pid_file") > /dev/null 2>&1; then
        echo "[$name] 已运行 (PID: $(cat $pid_file))"
        return
    fi
    
    cd "$dir"
    nohup $cmd > "$log_file" 2>&1 & echo $! > "$pid_file"
    sleep 1
    
    if ps -p $(cat "$pid_file") > /dev/null 2>&1; then
        echo "[$name] 启动成功 (PID: $(cat $pid_file))"
    else
        echo "[$name] 启动失败，查看: $log_file"
        rm -f "$pid_file"
    fi
}

stop_service() {
    local name=$1
    local config=${SERVICES[$name]}
    IFS='|' read -r cmd dir log_name <<< "$config"
    local pid_file="$PID_DIR/${log_name}.pid"
    
    # 根据脚本名精确匹配
    local script_name=""
    if [[ "$cmd" == *"app.py"* ]]; then
        script_name="app.py"
    elif [[ "$cmd" == *"start_https_server.py"* ]]; then
        script_name="start_https_server.py"
    elif [[ "$cmd" == *"mcp_http_bridge.py"* ]]; then
        script_name="mcp_http_bridge.py"
    fi
    
    local pids=$(pgrep -f "$script_name")
    if [ -n "$pids" ]; then
        for pid in $pids; do
            kill "$pid" 2>/dev/null
        done
        sleep 1
        pids=$(pgrep -f "$script_name")
        if [ -n "$pids" ]; then
            for pid in $pids; do
                kill -9 "$pid" 2>/dev/null
            done
        fi
        echo "[$name] 已停止"
    else
        echo "[$name] 未运行"
    fi
    rm -f "$pid_file"
}

status_service() {
    local name=$1
    local config=${SERVICES[$name]}
    IFS='|' read -r cmd dir log_name <<< "$config"
    local pid_file="$PID_DIR/${log_name}.pid"
    local log_file="$LOG_DIR/${log_name}.log"
    
    echo -n "[$name] "
    if [ -f "$pid_file" ] && ps -p $(cat "$pid_file") > /dev/null 2>&1; then
        local pid=$(cat "$pid_file")
        echo "运行中 (PID: $pid)"
        echo "  日志: $log_file"
        [ -f "$log_file" ] && echo "  最新: $(tail -1 $log_file)"
    else
        echo "未运行"
        [ -f "$pid_file" ] && rm -f "$pid_file"
    fi
}

case "${1:-}" in
    --start)
        echo "启动所有服务..."
        for name in "${!SERVICES[@]}"; do
            start_service "$name"
        done
        ;;
    --stop)
        echo "停止所有服务..."
        for name in "${!SERVICES[@]}"; do
            stop_service "$name"
        done
        ;;
    --restart)
        echo "重启所有服务..."
        for name in "${!SERVICES[@]}"; do
            stop_service "$name"
        done
        sleep 1
        for name in "${!SERVICES[@]}"; do
            start_service "$name"
        done
        ;;
    --status)
        echo "服务状态:"
        for name in "${!SERVICES[@]}"; do
            status_service "$name"
        done
        ;;
    *)
        echo "用法: $0 [--start|--stop|--restart|--status]"
        return 1
        ;;
esac
