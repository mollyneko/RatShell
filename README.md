# RatShell

<div align="center">
  <img src="Rat.png" width="80" alt="RatShell Logo">
  <p><b>SSH / Serial / Telnet 终端模拟器</b></p>
  <p>Built with PySide6 — inspired by frtty (PuTTY fork)</p>
</div>

<img width="1274" height="820" alt="图片" src="https://github.com/user-attachments/assets/ec9e6a31-d5c7-4e60-b404-e5a5a7f0dc5d" />


## 功能

- **SSH** — 远程终端连接（paramiko）
- **Serial** — 串口终端连接（pyserial）
- **Telnet** — 纯 TCP Telnet 连接
- **多标签** — 彩色标签页区分连接类型
- **ANSI 终端** — 基于 pyte 的 VT100/xterm 终端模拟，支持 256 色、真彩色
- **CJK 支持** — 中文双宽字符正常显示
- **滚动回看** — 历史输出滚动 + 竖向滚动条
- **文本选择** — 鼠标拖拽选中、复制
- **命令行发送** — 支持多行命令、批量发送、间隔控制
- **快捷命令** — 可分组管理的快捷命令按钮栏
- **会话记忆** — 自动恢复上次连接
- **日志记录** — 每行带毫秒时间戳，按会话隔离文件夹
- **查找** — 实时搜索、上下跳转、大小写切换、黄色高亮
- **国际化** — 中文 / English 界面切换
- **深色/浅色主题** — Catppuccin Mocha / Latte
- **无边框窗口** — 自定义标题栏、拖拽、最大化、全屏

## 安装

```bash
pip install -r requirements.txt
```

国内用户可使用清华镜像加速：

```bash
pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple
```

## 运行

```bash
python main.py
```

## 打包

```bash
pip install pyinstaller
pyinstaller --onefile --add-data "Rat.png;." --name RatShell main.py
```

生成的可执行文件在 `dist/RatShell.exe`。

## 依赖

- PySide6 >= 6.5.0 — Qt 绑定
- paramiko >= 3.0.0 — SSH 协议
- pyserial >= 3.5 — 串口协议
- pyte >= 0.8.0 — 终端模拟
- wcwidth — CJK 字符宽度计算

## 项目结构

```
RatShell/
├── main.py                 # 入口
├── app/
│   ├── main_window.py      # 主窗口 + 标签 + 菜单
│   ├── terminal_widget.py  # 终端模拟器核心
│   ├── connection_dialog.py# 连接配置对话框
│   ├── session_panel.py    # 会话面板 + 历史
│   ├── send_panel.py       # 命令行发送面板
│   ├── quick_tags_bar.py   # 快捷命令栏
│   ├── title_bar.py        # 无边框标题栏
│   ├── options_dialog.py   # 选项对话框(主题/语言)
│   ├── session_manager.py  # 会话持久化
│   ├── log_manager.py      # 日志记录
│   ├── resources.py        # 样式表 + 常量
│   ├── i18n.py             # 国际化
│   ├── logger.py           # 调试日志
│   └── connections/        # 连接协议层
│       ├── ssh_connection.py
│       ├── serial_connection.py
│       └── telnet_connection.py
├── sessions/               # 保存的会话
├── logs/                   # 日志文件(自动创建)
├── Rat.png                 # 应用图标
├── requirements.txt
└── README.md
```

## 快捷键

| 快捷键 | 功能 |
|--------|------|
| `Ctrl+N` | 新建连接 |
| `Ctrl+W` | 关闭当前标签 |
| `Ctrl+S` | 保存会话 |
| `Ctrl+B` | 切换会话面板 |
| `Ctrl+T` | 选项 |
| `F11` | 全屏 |
| `Ctrl+Shift+D` | 断开所有连接 |

## 许可

LGPL

## 作者

Rat
