#!/usr/bin/env python3
"""
test_status_report.py

测试状态报告功能的脚本。
"""

import time
from monitor import get_current_status_snapshot, get_sites_summary
from telegram_notifier import send_status_report, format_status_report_message


def test_status_report():
    """测试状态报告功能。"""
    print("🧪 测试状态报告功能...")
    print("=" * 50)
    
    # 获取当前状态快照
    print("📊 获取当前状态快照...")
    sites_status = get_current_status_snapshot()
    
    if not sites_status:
        print("⚠️  当前没有监控数据")
        print("💡 请先启动 UptimeGuard 并等待监控数据生成")
        return
    
    print(f"✅ 找到 {len(sites_status)} 个站点的监控数据")
    
    # 获取摘要信息
    summary = get_sites_summary()
    print(f"📈 摘要信息: 总计 {summary['total_sites']} 个站点")
    print(f"   - 正常: {summary['normal_sites']} 个")
    print(f"   - 异常: {summary['abnormal_sites']} 个")
    
    # 格式化状态报告消息
    print("\n📝 格式化状态报告消息...")
    message = format_status_report_message(sites_status)
    print("✅ 消息格式化完成")
    
    # 显示消息预览（前500字符）
    print(f"\n📋 消息预览（前500字符）:")
    print("-" * 50)
    print(message[:500])
    if len(message) > 500:
        print("...")
    print("-" * 50)
    
    # 询问是否发送测试消息
    print(f"\n📤 消息总长度: {len(message)} 字符")
    
    try:
        send_test = input("\n❓ 是否发送测试消息到 Telegram? (y/N): ").strip().lower()
        if send_test in ['y', 'yes']:
            print("📤 发送状态报告...")
            success = send_status_report(sites_status)
            if success:
                print("✅ 状态报告发送成功！")
            else:
                print("❌ 状态报告发送失败")
        else:
            print("⏭️  跳过发送测试")
    except KeyboardInterrupt:
        print("\n⏹️  测试已取消")
    
    print("\n🎉 测试完成！")


if __name__ == "__main__":
    test_status_report()
