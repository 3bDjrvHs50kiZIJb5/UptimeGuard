"""
monitor.py

监控与状态快照：周期性检查站点可用性，并将结果写入日志文件。
实现真实的 HTTP 请求检查，包括：
- HTTP 状态码检查
- 响应时间测量
- SSL 证书验证
- 内容关键字检测
- 详细的错误处理和日志记录
"""

import os
import time
import threading
import random
import requests
import ssl
import socket
from datetime import datetime, timezone
from urllib.parse import urlparse
from typing import Dict, List, Any, Optional
from log_manager import get_log_manager
from telegram_notifier import send_site_down_alert, send_site_recovery_alert, send_site_ssl_expiry_alert
from telegram_config import get_failure_threshold, is_telegram_configured


# 日志文件路径
LOG_DIR = os.path.join(os.path.dirname(__file__), "logs")
LOG_FILE_PATH = os.path.join(LOG_DIR, "uptime.log")


# 内存中的最近状态快照，供 UI 展示。
# 结构： {url: {"status": "up"|"down", "latency_ms": int, "timestamp": float}}
latest_status_snapshot: Dict[str, Dict[str, Any]] = {}


def ensure_log_file() -> None:
    """确保日志目录与文件存在。"""
    os.makedirs(LOG_DIR, exist_ok=True)
    if not os.path.exists(LOG_FILE_PATH):
        with open(LOG_FILE_PATH, "w", encoding="utf-8") as f:
            f.write("")


def write_log_line(line: str) -> None:
    """写一行到日志（通过 LogManager：文件 + 内存）。"""
    ensure_log_file()
    manager = get_log_manager(LOG_FILE_PATH)
    manager.log_message(line)


def _parse_cert_expiry(not_after_str: str) -> Optional[tuple]:
    """
    解析证书 notAfter 字符串，返回 (剩余天数, 剩余小时数)。
    格式通常为 "Mar  7 12:00:00 2026 GMT"（可能有多余空格）。
    若解析失败返回 None。
    """
    try:
        s = " ".join(not_after_str.split())
        expiry = datetime.strptime(s, "%b %d %H:%M:%S %Y GMT").replace(tzinfo=timezone.utc)
        now = datetime.now(timezone.utc)
        delta = expiry - now
        total_seconds = max(0, delta.total_seconds())
        days = int(total_seconds // 86400)
        hours = total_seconds / 3600  # 用于 48 小时阈值判断
        return (days, hours)
    except Exception:
        return None


def check_ssl_certificate(url: str) -> Dict[str, Any]:
    """
    检查 SSL 证书状态（仅对 HTTPS 网站），并计算证书剩余有效天数与小时数。
    返回: {"ssl_status", "ssl_error", "ssl_days_left": int|None, "ssl_hours_left": float|None}
    """
    try:
        parsed_url = urlparse(url)
        if parsed_url.scheme != 'https':
            return {"ssl_status": "not_applicable", "ssl_error": None, "ssl_days_left": None, "ssl_hours_left": None}
        
        context = ssl.create_default_context()
        context.check_hostname = True
        context.verify_mode = ssl.CERT_REQUIRED
        
        with socket.create_connection((parsed_url.hostname, parsed_url.port or 443), timeout=10) as sock:
            with context.wrap_socket(sock, server_hostname=parsed_url.hostname) as ssock:
                cert = ssock.getpeercert()
                days_left, hours_left = None, None
                if cert and "notAfter" in cert:
                    parsed = _parse_cert_expiry(cert["notAfter"])
                    if parsed:
                        days_left, hours_left = parsed
                return {"ssl_status": "up", "ssl_error": None, "ssl_days_left": days_left, "ssl_hours_left": hours_left}
                
    except ssl.SSLError as e:
        return {"ssl_status": "down", "ssl_error": f"SSL错误: {str(e)}", "ssl_days_left": None, "ssl_hours_left": None}
    except socket.timeout:
        return {"ssl_status": "down", "ssl_error": "SSL连接超时", "ssl_days_left": None, "ssl_hours_left": None}
    except Exception as e:
        return {"ssl_status": "down", "ssl_error": f"SSL检查异常: {str(e)}", "ssl_days_left": None, "ssl_hours_left": None}


def _resolve_domain_ip(url: str) -> Optional[str]:
    """解析 URL 中域名指向的 IP，解析失败返回 None。"""
    try:
        parsed = urlparse(url)
        hostname = parsed.hostname
        if not hostname:
            return None
        return socket.gethostbyname(hostname)
    except (socket.gaierror, socket.timeout, OSError):
        return None


def real_check(url: str, keywords: List[str] = None) -> Dict[str, Any]:
    """
    真实的网站检查，包括 HTTP 状态、响应时间、SSL 证书等。
    如果提供了关键词列表，将根据关键词判断网站状态。
    返回完整的检查结果字典。
    """
    start_time = time.time()
    error_message = None
    http_status = 0
    html_keyword = "-"
    # 解析域名指向的 IP（在请求前解析，失败不影响后续检查）
    resolved_ip = _resolve_domain_ip(url)
    
    try:
        # 设置请求头，模拟真实浏览器
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
        }
        
        # 发送 HTTP 请求，设置超时时间
        response = requests.get(
            url, 
            headers=headers, 
            timeout=10,  # 10秒超时
            allow_redirects=True,  # 允许重定向
            verify=True  # 验证 SSL 证书
        )
        
        # 记录响应时间（毫秒）
        latency_ms = int((time.time() - start_time) * 1000)
        
        # 获取 HTTP 状态码
        http_status = response.status_code
        
        # 检查响应内容中的关键字
        content = response.text.lower()
        
        # 如果提供了关键词列表，使用关键词判断状态
        if keywords:
            # 检查是否包含任何指定的关键词
            keyword_found = any(keyword.lower() in content for keyword in keywords)
            if keyword_found:
                html_keyword = "success"
                is_up = True  # 找到关键词则认为成功
            else:
                html_keyword = "error"
                is_up = False  # 没找到关键词则认为失败
        else:
            html_keyword = "-"
            
            # 判断网站是否可用（HTTP 状态码 200-399 通常表示成功）
            is_up = 200 <= http_status < 400
        
    except requests.exceptions.Timeout:
        latency_ms = int((time.time() - start_time) * 1000)
        error_message = "请求超时"
        is_up = False
        http_status = 408
        
    except requests.exceptions.ConnectionError:
        latency_ms = int((time.time() - start_time) * 1000)
        error_message = "连接失败"
        is_up = False
        http_status = 0
        
    except requests.exceptions.SSLError:
        latency_ms = int((time.time() - start_time) * 1000)
        error_message = "SSL证书错误"
        is_up = False
        http_status = 0
        
    except requests.exceptions.RequestException as e:
        latency_ms = int((time.time() - start_time) * 1000)
        error_message = f"请求异常: {str(e)}"
        is_up = False
        http_status = 0
        
    except Exception as e:
        latency_ms = int((time.time() - start_time) * 1000)
        error_message = f"未知错误: {str(e)}"
        is_up = False
        http_status = 0
    
    # 检查 SSL 证书状态（含到期剩余天数/小时数）
    ssl_result = check_ssl_certificate(url)
    
    return {
        "ip": resolved_ip,
        "http_status": http_status,
        "html_keyword": html_keyword,
        "ssl_status": ssl_result["ssl_status"],
        "ssl_days_left": ssl_result.get("ssl_days_left"),
        "ssl_hours_left": ssl_result.get("ssl_hours_left"),
        "status": "up" if is_up else "down",
        "latency_ms": latency_ms,
        "timestamp": time.time(),
        "error": error_message,
        "ssl_error": ssl_result["ssl_error"]
    }


def poll_once(sites: List[Dict[str, Any]]) -> None:
    """对所有站点执行一次真实检测，写日志并更新快照。"""
    # 获取连续失败阈值
    failure_threshold = get_failure_threshold()
    
    for site in sites:
        url = site.get("url", "")
        name = site.get("name", "")
        keywords = site.get("keywords", [])  # 获取关键词列表
        
        result = real_check(url, keywords)

        # 更新状态快照
        previous = latest_status_snapshot.get(url, {})
        previous_failures = int(previous.get("consecutive_failures", 0) or 0)
        previous_status = previous.get("status", "unknown")
        previous_alert_sent = bool(previous.get("alert_sent", False))
        previous_ssl_expiry_alert_sent = bool(previous.get("ssl_expiry_alert_sent", False))
        new_failures = previous_failures + 1 if result["status"] == "down" else 0
        alert_sent = previous_alert_sent if result["status"] == "down" else False

        ssl_hours_left = result.get("ssl_hours_left")
        # 证书剩余 >= 48 小时时重置“已发 SSL 到期告警”标记，以便再次进入 <48h 时能再次告警
        if ssl_hours_left is not None and ssl_hours_left >= 48:
            previous_ssl_expiry_alert_sent = False
        ssl_expiry_alert_sent = previous_ssl_expiry_alert_sent

        latest_status_snapshot[url] = {
            "name": name,
            "ip": result.get("ip"),
            "http_status": result["http_status"],
            "html_keyword": result["html_keyword"],
            "ssl_status": result["ssl_status"],
            "ssl_days_left": result.get("ssl_days_left"),
            "ssl_hours_left": ssl_hours_left,
            "status": result["status"],
            "consecutive_failures": new_failures,
            "alert_sent": alert_sent,
            "ssl_expiry_alert_sent": ssl_expiry_alert_sent,
            "latency_ms": result["latency_ms"],
            "timestamp": result["timestamp"],
        }

        # 记录日志（详细格式，包含所有检查结果）
        ts_str = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(result["timestamp"]))
        error_info = result.get('error', 'None')
        ssl_error_info = result.get('ssl_error', 'None')
        
        # 构建详细的日志行（SSL 到期天数仅对 HTTPS 有效时输出）
        ip_display = result.get("ip") or "-"
        log_parts = [
            f"[{ts_str}]",
            f"name={name}",
            f"url={url}",
            f"ip={ip_display}",
            f"status={result['status']}",
            f"http={result['http_status']}",
            f"ssl={result['ssl_status']}",
            f"keyword={result['html_keyword']}",
            f"latency_ms={result['latency_ms']}"
        ]
        ssl_days = result.get("ssl_days_left")
        if ssl_days is not None:
            log_parts.append(f"ssl_days_left={ssl_days}")
        
        # 添加错误信息（如果有）
        if error_info and error_info != 'None':
            log_parts.append(f"error={error_info}")
        if ssl_error_info and ssl_error_info != 'None':
            log_parts.append(f"ssl_error={ssl_error_info}")
            
        log_line = " ".join(log_parts)
        write_log_line(log_line)
        
        # Telegram 通知逻辑：仅发送单个站点故障/恢复通知，不发送整体状态报告
        if is_telegram_configured():
            # 发送故障警报：同一轮故障周期内只发送一次
            if result["status"] == "down" and new_failures >= failure_threshold and not alert_sent:
                try:
                    # 发送单个站点故障警报
                    send_site_down_alert(
                        site_name=name,
                        site_url=url,
                        consecutive_failures=new_failures,
                        error_info=error_info if error_info != 'None' else None
                    )
                    # 标记该站点本轮故障已发送过警报
                    latest_status_snapshot[url]["alert_sent"] = True
                    write_log_line(f"[TELEGRAM] 发送故障警报: {name} ({url}) - 连续失败 {new_failures} 次")
                except Exception as e:
                    write_log_line(f"[TELEGRAM ERROR] 发送故障通知失败: {str(e)}")
            
            # 发送恢复通知（当从故障状态恢复到正常状态时）
            elif result["status"] == "up" and previous_status == "down" and previous_alert_sent:
                try:
                    send_site_recovery_alert(
                        site_name=name,
                        site_url=url,
                        latency_ms=result["latency_ms"]
                    )
                    write_log_line(f"[TELEGRAM] 发送恢复通知: {name} ({url}) - 响应延迟 {result['latency_ms']} ms")
                except Exception as e:
                    write_log_line(f"[TELEGRAM ERROR] 发送恢复通知失败: {str(e)}")

            # SSL 证书剩余不足 48 小时时发送站点异常通知（同一“进入 <48h”周期内只发一次）
            elif (
                ssl_hours_left is not None
                and ssl_hours_left < 48
                and not previous_ssl_expiry_alert_sent
            ):
                try:
                    send_site_ssl_expiry_alert(
                        site_name=name,
                        site_url=url,
                        hours_left=ssl_hours_left
                    )
                    latest_status_snapshot[url]["ssl_expiry_alert_sent"] = True
                    write_log_line(f"[TELEGRAM] 发送 SSL 即将到期警报: {name} ({url}) - 剩余 {ssl_hours_left:.1f} 小时")
                except Exception as e:
                    write_log_line(f"[TELEGRAM ERROR] 发送 SSL 到期通知失败: {str(e)}")


def get_current_status_snapshot() -> Dict[str, Dict[str, Any]]:
    """
    获取当前所有站点的状态快照。
    
    Returns:
        Dict[str, Dict[str, Any]]: 站点状态字典，格式为 {url: {name, status, latency_ms, timestamp, ...}}
    """
    return latest_status_snapshot.copy()


def get_sites_summary() -> Dict[str, Any]:
    """
    获取站点监控摘要信息。
    
    Returns:
        Dict[str, Any]: 包含总站点数、正常站点数、异常站点数等信息的字典
    """
    total_sites = len(latest_status_snapshot)
    normal_sites = sum(1 for status in latest_status_snapshot.values() if status.get("status") == "up")
    abnormal_sites = total_sites - normal_sites
    
    return {
        "total_sites": total_sites,
        "normal_sites": normal_sites,
        "abnormal_sites": abnormal_sites,
        "last_update": max((status.get("timestamp", 0) for status in latest_status_snapshot.values()), default=0)
    }


def start_background_polling(get_sites_callable, interval_seconds: int = 30) -> threading.Thread:
    """
    启动后台线程，按固定间隔轮询站点。
    get_sites_callable: 一个可调用对象，返回当前站点列表（例如 storage.load_sites）。
    返回线程对象，以便在 app 退出时进行控制。
    """
    ensure_log_file()

    def _loop():
        while True:
            try:
                sites = get_sites_callable()
                poll_once(sites)
            except Exception as e:
                # 任何异常写日志但不中断线程
                write_log_line(f"[ERROR] polling exception: {e}")
            time.sleep(interval_seconds)

    t = threading.Thread(target=_loop, daemon=True)
    t.start()
    return t


