"""
app.py

应用入口：启动监控后台线程并启动 Gradio 界面。
"""

import threading
from ui import build_interface
from storage import load_sites
from monitor import start_background_polling
from docker_utils import is_docker_environment


def main():
    # 启动后台轮询（模拟监控），默认 60s 一次
    start_background_polling(load_sites, interval_seconds=60)

    # 若已配置 Telegram Bot Token，在后台启动聊天机器人（便于在 Telegram 中发「站点」等获取回复）
    try:
        from telegram_config import load_config
        config = load_config()
        if config.get("bot_token"):
            from telegram_chat_bot import start_chat_bot
            t_bot = threading.Thread(target=start_chat_bot, daemon=True)
            t_bot.start()
            print("🤖 Telegram 聊天机器人已在后台启动，可发送「站点」「所有站点」等查询状态")
    except Exception as e:
        print(f"⚠️ 启动 Telegram 聊天机器人跳过: {e}")

    # 启动 UI
    demo = build_interface()
    
    # 根据环境设置端口
    if is_docker_environment():
        server_port = 7863
        print("🐳 检测到 Docker 环境，使用端口: 7863")
    else:
        server_port = 7864
        print("💻 检测到本地环境，使用端口: 7864")
    
    # 启动 Gradio 应用，传递端口配置
    demo.launch(
        server_name="0.0.0.0",  # 允许外部访问
        server_port=server_port, # 使用不同端口避免冲突
        share=False,            # 不创建公共链接
        debug=True,             # 开启调试模式
        show_error=True,        # 显示错误信息
        quiet=False             # 显示启动信息
    )


if __name__ == "__main__":
    main()


