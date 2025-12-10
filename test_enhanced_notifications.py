#!/usr/bin/env python3
"""
test_enhanced_notifications.py

测试增强的通知功能：单个站点通知 + 整体状态报告
"""

import time
import os
from monitor import get_current_status_snapshot, get_sites_summary
from telegram_notifier import send_status_report, send_site_down_alert, send_site_recovery_alert
from telegram_config import load_config, get_send_status_report


def test_enhanced_notifications():
    """测试增强的通知功能。"""
    print("🧪 测试增强的通知功能...")
    print("=" * 60)
    
    # 检查配置
    config = load_config()
    print(f"📋 当前配置:")
    print(f"   - Telegram 启用: {config['enabled']}")
    print(f"   - 发送状态报告: {config['send_status_report']}")
    print(f"   - 失败阈值: {config['failure_threshold']}")
    print()
    
    if not config['enabled']:
        print("⚠️  Telegram 未启用，无法测试通知功能")
        print("💡 请设置环境变量: TELEGRAM_ENABLED=true")
        return
    
    # 获取当前状态
    sites_status = get_current_status_snapshot()
    if not sites_status:
        print("⚠️  当前没有监控数据")
        print("💡 请先启动 UptimeGuard 并等待监控数据生成")
        return
    
    print(f"📊 找到 {len(sites_status)} 个站点的监控数据")
    
    # 显示站点状态
    print("\n📋 当前站点状态:")
    for url, status_info in sites_status.items():
        name = status_info.get("name", "未知站点")
        status = status_info.get("status", "unknown")
        latency = status_info.get("latency_ms", 0)
        failures = status_info.get("consecutive_failures", 0)
        print(f"   - {name}: {status} (延迟: {latency}ms, 连续失败: {failures}次)")
    
    print("\n" + "=" * 60)
    print("🎯 测试场景选择:")
    print("1. 测试单个站点故障通知 + 整体状态报告")
    print("2. 测试单个站点恢复通知 + 整体状态报告")
    print("3. 仅测试整体状态报告")
    print("4. 测试配置开关功能")
    print("5. 退出")
    
    try:
        choice = input("\n请选择测试场景 (1-5): ").strip()
        
        if choice == "1":
            test_site_down_notification(sites_status)
        elif choice == "2":
            test_site_recovery_notification(sites_status)
        elif choice == "3":
            test_status_report_only(sites_status)
        elif choice == "4":
            test_config_toggle()
        elif choice == "5":
            print("👋 测试结束")
        else:
            print("❌ 无效选择")
            
    except KeyboardInterrupt:
        print("\n⏹️  测试已取消")


def test_site_down_notification(sites_status):
    """测试站点故障通知 + 整体状态报告。"""
    print("\n🚨 测试站点故障通知 + 整体状态报告")
    print("-" * 40)
    
    # 选择一个站点进行测试
    site_url = list(sites_status.keys())[0]
    site_info = sites_status[site_url]
    site_name = site_info.get("name", "测试站点")
    
    print(f"📊 测试站点: {site_name} ({site_url})")
    
    try:
        # 1. 发送单个站点故障通知
        print("📤 发送单个站点故障通知...")
        success1 = send_site_down_alert(
            site_name=site_name,
            site_url=site_url,
            consecutive_failures=5,
            error_info="测试故障 - 连接超时"
        )
        
        if success1:
            print("✅ 单个站点故障通知发送成功")
        else:
            print("❌ 单个站点故障通知发送失败")
        
        # 2. 发送整体状态报告
        print("📤 发送整体状态报告...")
        success2 = send_status_report(sites_status)
        
        if success2:
            print("✅ 整体状态报告发送成功")
        else:
            print("❌ 整体状态报告发送失败")
        
        print(f"\n🎉 测试完成！发送了 {'2' if success1 and success2 else '1' if success1 or success2 else '0'} 条消息")
        
    except Exception as e:
        print(f"❌ 测试异常: {str(e)}")


def test_site_recovery_notification(sites_status):
    """测试站点恢复通知 + 整体状态报告。"""
    print("\n✅ 测试站点恢复通知 + 整体状态报告")
    print("-" * 40)
    
    # 选择一个站点进行测试
    site_url = list(sites_status.keys())[0]
    site_info = sites_status[site_url]
    site_name = site_info.get("name", "测试站点")
    
    print(f"📊 测试站点: {site_name} ({site_url})")
    
    try:
        # 1. 发送单个站点恢复通知
        print("📤 发送单个站点恢复通知...")
        success1 = send_site_recovery_alert(
            site_name=site_name,
            site_url=site_url,
            latency_ms=150
        )
        
        if success1:
            print("✅ 单个站点恢复通知发送成功")
        else:
            print("❌ 单个站点恢复通知发送失败")
        
        # 2. 发送整体状态报告
        print("📤 发送整体状态报告...")
        success2 = send_status_report(sites_status)
        
        if success2:
            print("✅ 整体状态报告发送成功")
        else:
            print("❌ 整体状态报告发送失败")
        
        print(f"\n🎉 测试完成！发送了 {'2' if success1 and success2 else '1' if success1 or success2 else '0'} 条消息")
        
    except Exception as e:
        print(f"❌ 测试异常: {str(e)}")


def test_status_report_only(sites_status):
    """仅测试整体状态报告。"""
    print("\n📊 测试整体状态报告")
    print("-" * 40)
    
    try:
        print("📤 发送整体状态报告...")
        success = send_status_report(sites_status)
        
        if success:
            print("✅ 整体状态报告发送成功")
        else:
            print("❌ 整体状态报告发送失败")
        
    except Exception as e:
        print(f"❌ 测试异常: {str(e)}")


def test_config_toggle():
    """测试配置开关功能。"""
    print("\n⚙️  测试配置开关功能")
    print("-" * 40)
    
    current_config = get_send_status_report()
    print(f"📋 当前状态报告配置: {'启用' if current_config else '禁用'}")
    
    print("\n💡 配置说明:")
    print("   - 环境变量: TELEGRAM_SEND_STATUS_REPORT")
    print("   - 值: true/false")
    print("   - 默认值: true")
    print("   - 作用: 控制在故障/恢复时是否发送整体状态报告")
    
    print(f"\n🔧 当前环境变量值: {os.getenv('TELEGRAM_SEND_STATUS_REPORT', '未设置（默认true）')}")
    
    print("\n📝 修改方法:")
    print("   1. 设置环境变量: export TELEGRAM_SEND_STATUS_REPORT=false")
    print("   2. 或在 docker-compose.yml 中添加:")
    print("      environment:")
    print("        - TELEGRAM_SEND_STATUS_REPORT=false")


if __name__ == "__main__":
    test_enhanced_notifications()
