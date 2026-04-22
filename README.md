# UptimeGuard

一个简单而强大的网站在线状态监控工具，使用 Python 和 Gradio 构建，提供实时监控、状态展示和 Telegram 通知功能。

## ✨ 功能特性

### 🔍 网站监控
- **实时状态检测**：HTTP/HTTPS 状态码检查
- **响应时间测量**：精确到毫秒的延迟监控
- **SSL 证书验证**：自动检查 HTTPS 网站证书状态
- **内容关键字检测**：智能识别网站内容状态
- **连续失败跟踪**：记录连续失败次数，避免误报

### 📊 可视化界面
- **现代化 UI**：基于 Gradio 的响应式界面
- **实时数据展示**：网站列表和状态信息实时更新
- **日志查看**：可滚动的日志信息展示
- **站点管理**：支持添加、编辑、删除监控站点

### 🔔 智能通知
- **Telegram 集成**：支持 Telegram Bot 通知
- **故障警报**：网站故障时自动发送通知
- **恢复通知**：网站恢复时发送恢复消息
- **阈值控制**：可配置连续失败阈值
- **聊天机器人**：支持通过 Telegram 与系统交互

### 🐳 容器化支持
- **Docker 环境检测**：自动识别运行环境
- **端口自适应**：Docker 和本地环境使用不同端口
- **外部访问**：支持外部网络访问

## 🚀 快速开始

### 环境要求
- Python 3.8+
- 虚拟环境（推荐）

### 安装步骤

1. **克隆项目**
```bash
git clone <repository-url>
cd UptimeGuard
```

2. **创建虚拟环境**
```bash
python3 -m venv .venv
source .venv/bin/activate  # Linux/Mac
# 或
.venv\Scripts\activate     # Windows
```

3. **安装依赖**
```bash
pip install -r requirements.txt
```

4. **配置监控站点**
编辑 `sites.json` 文件，添加要监控的网站：
```json
[
  {
    "name": "示例网站",
    "url": "https://example.com"
  },
  {
    "name": "GitHub",
    "url": "https://github.com"
  }
]
```

5. **启动应用**
```bash
python app.py
```

6. **访问界面**
- 本地环境：http://localhost:7864
- Docker 环境：http://localhost:7863

## 📁 项目结构

```
UptimeGuard/
├── app.py                    # 应用入口
├── monitor.py               # 监控逻辑核心
├── ui.py                    # Gradio 界面定义
├── storage.py               # 数据存储管理
├── telegram_config.py       # Telegram 配置管理
├── telegram_notifier.py     # Telegram 通知发送
├── telegram_chat_bot.py     # Telegram 聊天机器人
├── log_manager.py           # 日志管理
├── docker_utils.py          # Docker 环境检测
├── sites.json               # 监控站点配置
├── requirements.txt         # Python 依赖
├── logs/                    # 日志文件目录
│   └── uptime.log          # 监控日志
└── README.md               # 项目说明
```

## ⚙️ 配置说明

### 监控站点配置
在 `sites.json` 中配置要监控的网站：
```json
[
  {
    "name": "网站名称",
    "url": "https://example.com"
  }
]
```

### Telegram 通知配置
在 `docker-compose.yml` 中配置 Telegram 通知：
```json
{
  "enabled": true,
  "bot_token": "YOUR_BOT_TOKEN",
  "chat_id": "YOUR_CHAT_ID",
  "failure_threshold": 10
}
```

#### 获取 Telegram 配置
1. **Bot Token**：
   - 在 Telegram 中搜索 @BotFather
   - 发送 `/newbot` 命令创建机器人
   - 复制获得的 Token

2. **Chat ID**：
   - 使用聊天机器人功能（推荐）
   - 或通过 API 获取：`https://api.telegram.org/bot<YOUR_BOT_TOKEN>/getUpdates`

### 环境变量配置
```bash
# Telegram 配置
export TELEGRAM_BOT_TOKEN="your_bot_token"
export TELEGRAM_CHAT_ID="your_chat_id"
export TELEGRAM_ENABLED="true"
export TELEGRAM_FAILURE_THRESHOLD="10"
```

## 🔧 使用说明

### 监控界面
- **网站列表**：显示所有监控网站的状态信息
- **实时更新**：每 5 秒自动刷新状态
- **状态信息**：HTTP 状态、SSL 状态、响应时间等

### 日志查看
- **实时日志**：每 2 秒自动刷新日志
- **手动刷新**：点击"刷新日志"按钮
- **日志内容**：详细的监控记录和错误信息

### Telegram 功能
- **故障通知**：连续失败达到阈值时发送
- **恢复通知**：网站从故障状态恢复时发送
- **聊天机器人**：支持通过 Telegram 与系统交互

## 📊 监控数据

### 状态信息
- **HTTP 状态**：HTTP 响应状态码
- **SSL 状态**：SSL 证书验证结果
- **关键字**：页面内容关键字检测
- **响应时间**：请求响应延迟（毫秒）
- **连续失败**：连续失败次数统计

### 日志格式
```
[2024-01-01 12:00:00] name=示例网站 url=https://example.com status=up http=200 ssl=up keyword=success latency_ms=150
```

## 🐳 Docker 部署

### 构建镜像
```bash
docker build -t uptimeguard .
```

### 运行容器
```bash
docker run -d \
  --name uptimeguard \
  -p 7863:7863 \
  -v $(pwd)/sites.json:/app/sites.json \
  -v $(pwd)/logs:/app/logs \
  uptimeguard
```

## 🔍 故障排除

### 常见问题

1. **端口被占用**
   - 检查端口 7863/7864 是否被占用
   - 修改代码中的端口配置

2. **Telegram 通知不工作**
   - 检查 Bot Token 和 Chat ID 是否正确
   - 确认机器人已添加到对话中
   - 查看日志中的错误信息

3. **网站监控异常**
   - 检查网络连接
   - 确认目标网站可访问
   - 查看日志中的详细错误信息

4. **依赖安装失败**
   - 确保 Python 版本 >= 3.8
   - 使用虚拟环境
   - 更新 pip：`pip install --upgrade pip`

### 日志分析
查看 `logs/uptime.log` 文件获取详细的监控和错误信息。

## 🤝 贡献指南

欢迎提交 Issue 和 Pull Request！

1. Fork 项目
2. 创建功能分支
3. 提交更改
4. 推送到分支
5. 创建 Pull Request

## 📄 许可证

本项目采用 MIT 许可证。详见 [LICENSE](LICENSE) 文件。

## 🙏 致谢

感谢所有贡献者和开源社区的支持！

---

**UptimeGuard** - 让网站监控变得简单而可靠！
