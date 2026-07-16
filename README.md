# Frtty Pro

<div align="center">
  <img src="frtty.png" width="80" alt="Frtty Pro Logo">
  <p><b>SSH / Serial / Telnet 终端模拟器</b></p>
  <p>Built with PySide2 — inspired by frtty (PuTTY fork)</p>
  <p>v1.2.7 | 支持 Windows 7/10/11</p>
</div>

## 功能

- **SSH** — 远程终端连接（paramiko，支持密码认证）
- **Serial** — 串口终端连接（pyserial，支持波特率/数据位/校验位/停止位）
- **Telnet** — 纯 TCP Telnet 连接
- **多标签** — 彩色标签页区分连接类型，关闭按钮 hover 红色提示
- **ANSI 终端** — 基于 pyte 的 VT100/xterm 终端模拟，支持 256 色、真彩色
- **CJK 支持** — 中文双宽字符正常显示，中日韩文本对齐
- **滚动回看** — 历史输出滚动 + 竖向滚动条
- **文本选择** — 鼠标拖拽选中、复制，支持跨行选择
- **命令行发送** — 支持多行命令、批量发送（N 次 + 间隔控制）
- **快捷命令** — 可分组管理的快捷命令按钮栏，支持自定义颜色
- **会话管理** — 保存/加载会话、自动恢复上次连接、会话列表侧面板
- **历史命令** — 去重保存已发送命令，支持右键复制
- **日志记录** — 每行带毫秒时间戳，按会话隔离文件夹
- **查找** — 实时搜索、上下跳转、大小写切换、黄色高亮
- **国际化** — 中文 / English 界面切换
- **深色主题** — Catppuccin Mocha 风格
- **无边框窗口** — 自定义标题栏、拖拽、最大化、全屏
- **同级会话检测** — 打开同名连接时自动识别，断开/关闭一个不影响其他同名会话状态

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

## 打包（PyInstaller onefile，兼容 Win7）

```bash
pip install pyinstaller
"C:/Users/Y5354/AppData/Local/Programs/Python/Python38/python.exe" -m PyInstaller --onefile --noconsole --icon=./frtty.ico --name="FrttyPro" ^
  --add-data="./frtty.png;." --add-data="./Rat.png;." --add-data="./frtty.ico;." ^
  --add-data="./app/i18n.py;./app/" --add-data="./app/resources.py;./app/" ^
  --hidden-import=paramiko --hidden-import=pyserial --hidden-import=pyte ^
  --hidden-import=wcwidth --hidden-import=shiboken2 main.py
```

生成的可执行文件在 `dist/FrttyPro.exe`。

### Win7 兼容注意事项

PySide6 不支持 Windows 7，因此使用 **PySide2**（Qt 5.15）+ **Python 3.8** 构建。
部分 C 扩展包需降级以避免缺失 Rust 运行时和新版 VC++ 运行时：

| 包 | 推荐版本 | 原因 |
|---|---|---|
| PySide2 | 5.15.2.x | Qt6 不支持 Win7 |
| cryptography | < 3.5（推荐 3.4.8） | ≥3.5 需 Rust 编译的 _rust.pyd |
| bcrypt | < 4.1（推荐 4.0.1） | 新版用新版 MSVC 运行时 |
| cffi | < 1.16（推荐 1.15.1） | 同上 |

## 依赖

- PySide2 >= 5.15.2 — Qt 绑定（Win7 兼容）
- paramiko ~= 3.4.1 — SSH 协议
- pyserial >= 3.5 — 串口协议
- pyte >= 0.8.0 — 终端模拟
- wcwidth — CJK 字符宽度计算
- cryptography ~= 3.4.8 — 加密库（Win7 兼容）
- bcrypt ~= 4.0.1 — 密码哈希（Win7 兼容）

## 项目结构

```
Frtty Pro/
├── main.py                 # 入口
├── DESIGN.md               # 架构设计文档
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
│       ├── __init__.py     # create_connection 工厂
│       ├── base_connection.py
│       ├── ssh_connection.py
│       ├── serial_connection.py
│       └── telnet_connection.py
├── sessions/               # 保存的会话（旧路径）
├── frtty.png               # 应用图标
├── frtty.ico               # EXE 图标
├── Rat.png                 # 关于对话框作者图标
├── requirements.txt
└── README.md
```

运行时数据（会话列表、历史命令、快速命令、日志）自动存储在 `%LOCALAPPDATA%/RatStudio/FrttyPro/`。

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

**Rat** — RatStudio
