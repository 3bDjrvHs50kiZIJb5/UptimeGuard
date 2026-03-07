"""
telegram_notifier.py

Telegram 通知发送模块。
负责向 Telegram 发送网站监控状态通知。
"""

import requests
import time
from typing import Optional, Dict, Any
from telegram_config import load_config, is_telegram_configured


def send_telegram_message(message: str) -> bool:
    """
    发送消息到 Telegram。
    
    Args:
        message: 要发送的消息内容
        
    Returns:
        bool: 发送是否成功
    """
    if not is_telegram_configured():
        print("⚠️  Telegram 未配置或未启用，跳过通知发送")
        return False
    
    config = load_config()
    bot_token = config["bot_token"]
    chat_id = config["chat_id"]
    
    # Telegram Bot API URL
    url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
    
    # 消息数据
    data = {
        "chat_id": chat_id,
        "text": message,
        "parse_mode": "HTML",  # 支持 HTML 格式
        "disable_web_page_preview": True
    }
    
    try:
        response = requests.post(url, data=data, timeout=10)
        response.raise_for_status()
        
        result = response.json()
        if result.get("ok"):
            print(f"✅ Telegram 通知发送成功: {message[:50]}...")
            return True
        else:
            print(f"❌ Telegram 发送失败: {result.get('description', '未知错误')}")
            return False
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Telegram 发送异常: {str(e)}")
        return False
    except Exception as e:
        print(f"❌ Telegram 发送未知错误: {str(e)}")
        return False


def format_site_down_message(site_name: str, site_url: str, 
                           consecutive_failures: int, 
                           error_info: str = None) -> str:
    """
    格式化网站故障通知消息。
    
    Args:
        site_name: 网站名称
        site_url: 网站URL
        consecutive_failures: 连续失败次数
        error_info: 错误信息
        
    Returns:
        str: 格式化的消息
    """
    timestamp = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
    
    message = f"""🚨 <b>网站监控警报</b>

📊 <b>网站信息:</b>
• 名称: {site_name}
• URL: {site_url}
• 连续失败: {consecutive_failures} 次

⏰ <b>检测时间:</b> {timestamp}

⚠️ <b>状态:</b> 网站不可访问"""

    if error_info and error_info != "None":
        message += f"\n\n🔍 <b>错误详情:</b> {error_info}"
    
    message += "\n\n请及时检查网站状态！"
    
    return message


def format_site_recovery_message(site_name: str, site_url: str, 
                               latency_ms: int) -> str:
    """
    格式化网站恢复通知消息。
    
    Args:
        site_name: 网站名称
        site_url: 网站URL
        latency_ms: 响应延迟（毫秒）
        
    Returns:
        str: 格式化的消息
    """
    timestamp = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
    
    message = f"""✅ <b>网站恢复通知</b>

📊 <b>网站信息:</b>
• 名称: {site_name}
• URL: {site_url}
• 响应延迟: {latency_ms} ms

⏰ <b>恢复时间:</b> {timestamp}

🎉 <b>状态:</b> 网站已恢复正常访问"""
    
    return message


def send_site_down_alert(site_name: str, site_url: str, 
                        consecutive_failures: int, 
                        error_info: str = None) -> bool:
    """
    发送网站故障警报。
    
    Args:
        site_name: 网站名称
        site_url: 网站URL
        consecutive_failures: 连续失败次数
        error_info: 错误信息
        
    Returns:
        bool: 发送是否成功
    """
    message = format_site_down_message(site_name, site_url, consecutive_failures, error_info)
    return send_telegram_message(message)


def send_site_recovery_alert(site_name: str, site_url: str, 
                           latency_ms: int) -> bool:
    """
    发送网站恢复通知。
    
    Args:
        site_name: 网站名称
        site_url: 网站URL
        latency_ms: 响应延迟（毫秒）
        
    Returns:
        bool: 发送是否成功
    """
    message = format_site_recovery_message(site_name, site_url, latency_ms)
    return send_telegram_message(message)


def format_site_ssl_expiry_message(site_name: str, site_url: str, hours_left: float) -> str:
    """
    格式化 SSL 证书即将到期（站点异常）通知消息。
    
    Args:
        site_name: 网站名称
        site_url: 网站 URL
        hours_left: 证书剩余有效小时数
        
    Returns:
        str: 格式化的消息
    """
    timestamp = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
    hours_str = f"{hours_left:.1f}"
    message = f"""🔐 <b>SSL 证书即将到期（站点异常）</b>

📊 <b>网站信息:</b>
• 名称: {site_name}
• URL: {site_url}
• 证书剩余: <b>{hours_str} 小时</b>（小于 48 小时）

⏰ <b>检测时间:</b> {timestamp}

⚠️ <b>状态:</b> 请尽快续期或更换 SSL 证书，避免访问异常。"""
    return message


def send_site_ssl_expiry_alert(site_name: str, site_url: str, hours_left: float) -> bool:
    """
    发送 SSL 证书即将到期（站点异常）通知。
    当证书剩余不足 48 小时时调用。
    
    Args:
        site_name: 网站名称
        site_url: 网站 URL
        hours_left: 证书剩余有效小时数
        
    Returns:
        bool: 发送是否成功
    """
    message = format_site_ssl_expiry_message(site_name, site_url, hours_left)
    return send_telegram_message(message)


def format_status_report_message(sites_status: Dict[str, Dict[str, Any]]) -> str:
    """
    格式化整体状态报告消息，仅展示异常站点列表。
    
    Args:
        sites_status: 站点状态字典，格式为 {url: {name, status, latency_ms, timestamp, ...}}
        
    Returns:
        str: 格式化的状态报告消息
    """
    timestamp = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
    
    # 仅收集异常站点
    abnormal_sites = []
    
    for url, status_info in sites_status.items():
        site_name = status_info.get("name", "未知站点")
        site_status = status_info.get("status", "unknown")
        latency_ms = status_info.get("latency_ms", 0)
        consecutive_failures = status_info.get("consecutive_failures", 0)
        last_check_time = status_info.get("timestamp", 0)
        
        # 格式化最后检查时间
        if last_check_time > 0:
            last_check_str = time.strftime("%H:%M:%S", time.localtime(last_check_time))
        else:
            last_check_str = "未知"
        
        site_info = {
            "name": site_name,
            "url": url,
            "latency_ms": latency_ms,
            "last_check": last_check_str,
            "consecutive_failures": consecutive_failures
        }
        
        if site_status != "up":
            abnormal_sites.append(site_info)
    
    # 构建消息
    message = f"""📊 <b>UptimeGuard 状态报告</b>

⏰ <b>报告时间:</b> {timestamp}
📈 <b>总站点数:</b> {len(sites_status)}
✅ <b>正常站点:</b> {len(sites_status) - len(abnormal_sites)}
❌ <b>异常站点:</b> {len(abnormal_sites)}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

❌ <b>运行异常站点 ({len(abnormal_sites)} 个):</b>"""
    
    if abnormal_sites:
        for i, site in enumerate(abnormal_sites, 1):
            message += f"""
{i}. <b>{site['name']}</b>
   🔗 {site['url']}
   ⚡ 延迟: {site['latency_ms']} ms
   🕐 检查时间: {site['last_check']}
   🔥 连续失败: {site['consecutive_failures']} 次"""
    else:
        message += "\n   🎉 当前无异常站点"
    
    message += "\n\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    message += "\n\n💡 使用 /help 查看更多命令"
    
    return message


def format_full_sites_message(sites_status: Dict[str, Dict[str, Any]]) -> str:
    """
    格式化「所有站点」状态消息，列出全部站点的名称、URL、状态、延迟、最近检测时间等。
    用于在 Telegram 中回复「站点」「所有站点」等关键词时使用。
    
    Args:
        sites_status: 站点状态字典，格式为 {url: {name, status, latency_ms, timestamp, ...}}
        
    Returns:
        str: 格式化的消息（Telegram 单条消息上限 4096 字符，过多站点会截断说明）
    """
    timestamp = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
    max_len = 3800  # Telegram 单条上限 4096，留余量
    lines = [
        f"📊 <b>UptimeGuard 全部站点状态</b>",
        "",
        f"⏰ <b>报告时间:</b> {timestamp}",
        f"📈 <b>总站点数:</b> {len(sites_status)}",
        "",
        "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━",
        ""
    ]
    for url, status_info in sites_status.items():
        name = status_info.get("name", "未知站点")
        site_status = status_info.get("status", "unknown")
        latency_ms = status_info.get("latency_ms", 0)
        consecutive_failures = status_info.get("consecutive_failures", 0)
        last_check_time = status_info.get("timestamp", 0)
        if last_check_time > 0:
            last_check_str = time.strftime("%H:%M:%S", time.localtime(last_check_time))
        else:
            last_check_str = "未知"
        icon = "✅" if site_status == "up" else "❌"
        line = f"{icon} <b>{name}</b>\n   🔗 {url}\n   ⚡ {latency_ms} ms | 🕐 {last_check_str} | 连续失败 {consecutive_failures} 次"
        lines.append(line)
        lines.append("")
        if sum(len(s) for s in lines) >= max_len:
            lines.append("… 列表过长已截断，请使用 Web 界面查看完整列表。")
            break
    lines.append("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    lines.append("\n💡 使用 /help 查看更多命令")
    out = "\n".join(lines)
    if len(out) > 4096:
        out = out[:4090] + "\n…(已截断)"
    return out


def send_status_report(sites_status: Dict[str, Dict[str, Any]]) -> bool:
    """
    发送整体状态报告。
    
    Args:
        sites_status: 站点状态字典
        
    Returns:
        bool: 发送是否成功
    """
    message = format_status_report_message(sites_status)
    return send_telegram_message(message)


def test_telegram_connection() -> bool:
    """
    测试 Telegram 连接是否正常。
    
    Returns:
        bool: 连接是否成功
    """
    if not is_telegram_configured():
        print("❌ Telegram 未配置或未启用")
        return False
    
    test_message = "🧪 UptimeGuard Telegram 通知测试消息\n\n如果您收到此消息，说明配置正确！"
    return send_telegram_message(test_message)
