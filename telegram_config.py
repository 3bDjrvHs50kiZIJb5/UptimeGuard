"""
telegram_config.py

Telegram 通知配置管理模块。
负责管理 Telegram Bot Token 和 Chat ID 的配置，仅从环境变量读取。
"""

import os
from typing import Dict, Any


def load_config() -> Dict[str, Any]:
    """
    加载 Telegram 配置。
    仅从环境变量读取配置。
    
    返回配置字典，包含：
    - bot_token: Telegram Bot Token
    - chat_id: 目标聊天ID
    - enabled: 是否启用通知
    - failure_threshold: 连续失败阈值
    - send_status_report: 是否在故障/恢复时发送整体状态报告
    """
    # 从环境变量读取配置
    bot_token = os.getenv("TELEGRAM_BOT_TOKEN", "")
    chat_id = os.getenv("TELEGRAM_CHAT_ID", "")
    enabled = os.getenv("TELEGRAM_ENABLED", "false").lower() == "true"
    failure_threshold = int(os.getenv("TELEGRAM_FAILURE_THRESHOLD", "10"))
    send_status_report = os.getenv("TELEGRAM_SEND_STATUS_REPORT", "true").lower() == "true"
    
    return {
        "bot_token": bot_token,
        "chat_id": chat_id,
        "enabled": enabled,
        "failure_threshold": failure_threshold,
        "send_status_report": send_status_report
    }




def is_telegram_configured() -> bool:
    """检查 Telegram 是否已正确配置。"""
    config = load_config()
    return bool(config["bot_token"] and config["chat_id"] and config["enabled"])


def get_failure_threshold() -> int:
    """获取连续失败阈值。"""
    config = load_config()
    return config["failure_threshold"]


def get_send_status_report() -> bool:
    """获取是否发送整体状态报告的配置。"""
    config = load_config()
    return config["send_status_report"]
