# Frtty Pro — 设计文档

> v1.2.7 | PySide2 + Python 3.8 | 兼容 Windows 7/10/11

---

## 目录

1. [架构概览](#架构概览)
2. [模块职责](#模块职责)
3. [数据流](#数据流)
4. [连接协议层](#连接协议层)
5. [终端模拟](#终端模拟)
6. [会话与持久化](#会话与持久化)
7. [UI 组件](#ui-组件)
8. [同名字检测](#同名字检测)
9. [打包与兼容性](#打包与兼容性)

---

## 架构概览

Frtty Pro 是一个面向专业用户的 SSH/Serial/Telnet 终端模拟器，采用 **MVC 风格的模块化架构**：

```
┌─────────────────────────────────────────────────────────┐
│                     main.py (入口)                       │
├─────────────────────────────────────────────────────────┤
│                   MainWindow (主窗口)                     │
│  ┌────────────┐  ┌──────────┐  ┌──────────────────────┐  │
│  │ ColorTab   │  │Terminal  │  │   SendPanel          │  │
│  │ Bar (标签)  │  │Widget    │  │   (命令输入 + 发送)   │  │
│  └────────────┘  └──────────┘  └──────────────────────┘  │
│  ┌──────────────────────────────────────────────────┐   │
│  │  Dock Widget                                      │   │
│  │  ┌─────────────────┐  ┌──────────────────────┐   │   │
│  │  │ SessionTreePanel │  │   HistoryPanel       │   │   │
│  │  │ (会话列表)       │  │   (历史命令)         │   │   │
│  │  └─────────────────┘  └──────────────────────┘   │   │
│  └──────────────────────────────────────────────────┘   │
│  ┌──────────────────────┐  ┌────────────────────┐       │
│  │   QuickTagsBar        │  │   TitleBar          │       │
│  │   (快捷命令)          │  │   (自定义标题栏)    │       │
│  └──────────────────────┘  └────────────────────┘       │
├─────────────────────────────────────────────────────────┤
│                Connections (协议层)                       │
│  ┌──────────────────────────────────────────────────┐   │
│  │  BaseConnection (QObject + 信号基类)              │   │
│  │  ├── SSHConnection    (paramiko)                  │   │
│  │  ├── SerialConnection  (pyserial)                 │   │
│  │  └── TelnetConnection  (socket)                   │   │
│  └──────────────────────────────────────────────────┘   │
├─────────────────────────────────────────────────────────┤
│                Core 库                                    │
│  ┌─────────┐  ┌────────┐  ┌───────┐  ┌──────────────┐  │
│  │  pyte   │  │wcwidth │  │ i18n  │  │ session_     │  │
│  │(终端模拟)│  │ (CJK宽) │  │(国际化)│  │ manager     │  │
│  └─────────┘  └────────┘  └───────┘  └──────────────┘  │
│  ┌─────────┐  ┌────────┐  ┌──────────────┐            │
│  │ logger  │  │log_    │  │  resources    │            │
│  │         │  │manager │  │  (主题/常量)  │            │
│  └─────────┘  └────────┘  └──────────────┘            │
└─────────────────────────────────────────────────────────┘
```

### 设计原则

1. **信号驱动** — 连接层通过 Qt Signal 异步通知 UI 层，后台线程无锁通信
2. **工厂模式** — `connections/__init__.py` 的 `create_connection()` 按 type 创建对应连接
3. **数据隔离** — 运行时数据存 `%LOCALAPPDATA%`，打包数据通过 `get_app_dir()` 解析
4. **组合优先** — TerminalWidget 不直接操作连接，通过 `set_connection()` 注入

---

## 模块职责

### main.py — 应用入口

```python
def main():
    # 设置高 DPI 支持（Qt.AA_EnableHighDpiScaling）
    # 创建 QApplication
    # 应用主题（resources.apply_theme）
    # 创建 MainWindow、显示
    # app.exec_()
```

功能：
- 初始化 Qt 应用程序
- 加载主题样式表
- 设置应用图标（frtty.png）
- 进入事件循环

### app/main_window.py — 主窗口（核心协调器）

`MainWindow` 是应用的中央协调器，负责：

- **初始化** — 创建无边框窗口、标题栏、标签栏、侧面板、发送面板、状态栏
- **标签管理** — `add_tab()/remove_tab()/close_tab()/disconnect_tab()/reconnect_tab()`
- **连接生命周期** — `_start_connection()` → `_create_tab()` → start → `_on_tab_connected()` / `_on_tab_disconnected()` / `_on_tab_error()`
- **状态追踪** — `_sid_refcount`（sid 引用计数）、`_name_refcount`（同名标签计数）
- **菜单** — 文件/会话/视图/工具/帮助菜单、标签右键菜单、会话面板右键菜单

关键子组件：

**ColorTabButton** — 自定义渲染的标签按钮，绘制彩色圆点、连接状态（绿/红）、关闭叉号

**TabBarWidget** — 标签栏容器，维护标签列表，处理选中/关闭/右键信号

**SessionTab** — 包装 `TerminalWidget` + 连接对象的 tab 页

### app/terminal_widget.py — 终端模拟器

基于 `pyte` 的 VT100/xterm 终端模拟实现：

- **pyte.Screen** — 维护 24-bit 真彩色的字符矩阵
- **pyte.Stream** — 解析 ANSI 转义序列，驱动 Screen 更新
- **行号面板** — 左侧灰色行号，跟随滚动
- **光标** — 闪烁方块光标，可定位
- **选择** — 鼠标拖拽选择文本，复制到剪贴板
- **搜索** — 黄色高亮匹配文字，上下跳转
- **日志** — 毫秒级时间戳，按会话隔离文件夹

### app/connections/ — 连接协议层

#### base_connection.py — 抽象基类

```python
class BaseConnection(QObject):
    output_received = Signal(str)   # 收到数据
    connected = Signal()            # 已连接
    disconnected = Signal(str)      # 已断开（含原因）
    error_occurred = Signal(str)    # 发生错误
```

- 所有连接类型继承此类
- 后台线程通过 `_emit_output(text)` / `_emit_signal(signal)` 安全发射信号
- `start()` — 启动后台线程（抽象方法）
- `send(data)` — 发送数据（抽象方法）
- `disconnect()` — 断开连接（抽象方法）

#### ssh_connection.py

- 基于 paramiko 的 SSH 连接
- 后台线程：`_run()` → `client.connect()` → `channel.invoke_shell()` → 循环 `recv()`
- 支持自动接受主机密钥（AutoAddPolicy）

#### serial_connection.py

- 基于 pyserial 的串口连接
- 支持配置波特率、数据位、校验位、停止位
- 后台线程轮询 `in_waiting` 读取数据

#### telnet_connection.py

- 基于 socket 的纯 Telnet 连接
- 后台线程 `recv()` 循环，处理 timeouts/BlockingIOError

### app/session_panel.py — 会话面板 + 历史命令

**SessionTreePanel** — 左侧会话列表：
- 显示活动会话（绿色圆点 + 名称 + 类型）
- 保存的会话（灰色三角形）
- 右键菜单：断开/重连/编辑/关闭
- 搜索过滤

**HistoryPanel** — 历史命令面板：
- 去重存储最近 200 条命令
- 点击发送到当前终端
- 右键复制
- 持久化到 `history.json`

### app/send_panel.py — 命令发送面板

- 多行命令输入（语法高亮行号）
- 单次/循环发送（N 次 + 间隔毫秒）
- 停止按钮中断循环

### app/quick_tags_bar.py — 快捷命令栏

- 命令分组管理（默认组 + 自定义组）
- 每个命令按钮显示自定义名称和颜色
- 右键编辑/删除命令，菜单管理分组
- 持久化到 `quick_commands.json`

### app/title_bar.py — 无边框标题栏

- 自定义 QLinearGradient 背景
- 窗口标题 + 最小化/最大化/关闭按钮（hover 变色）
- 拖拽移动窗口
- 双击最大化

### app/options_dialog.py — 选项对话框

- 语言切换（中文/English，即时生效 + 持久化）
- 主题切换（深色/浅色 Catppuccin）

### app/connection_dialog.py — 连接配置对话框

- SSH：主机/端口/用户名/密码
- Serial：端口/波特率/数据位/校验位/停止位
- Telnet：主机/端口
- 自定义显示名称
- 保存会话按钮

### app/resources.py — 常量 + 工具函数

```python
APP_NAME = "Frtty Pro"
APP_VERSION = "1.2.7"
ORG_NAME = "RatStudio"

get_data_dir()  # → %LOCALAPPDATA%/RatStudio/FrttyPro/
get_app_dir()   # → 开发时项目根，打包后 sys._MEIPASS
DARK_THEME      # → Catppuccin Mocha 样式表
apply_theme()   # → 应用样式表到 QApplication
```

### app/i18n.py — 国际化

- 中英文双语言支持
- 所有用户可见文本通过 `tr(key)` 查找
- 当前语言持久化到 `%LOCALAPPDATA%/RatStudio/FrttyPro/lang.json`

---

## 数据流

### 连接 → 终端 数据流

```
SSH/Serial/Telnet 远程主机
    ↓ 原始字节
后台线程 recv()
    ↓ decode("utf-8") / ("latin-1")
_emit_output(text) 
    ↓ output_received Signal
TerminalWidget._on_data(text)
    ↓ pyte.Stream.feed(text)
pyte.Screen (字符矩阵更新)
    ↓ self.update()
paintEvent() → 渲染到 QPainter
```

### 命令 数据流

```
SendPanel/QuickTagsBar/HistoryPanel
    ↓ command_sent Signal
MainWindow._on_send_command()
    ↓
TerminalWidget._connection.send(data.encode())
    ↓
SSH: channel.send() / Serial: ser.write() / Telnet: sock.sendall()
    ↓
远程主机
```

### 会话生命周期

```
ConnectionDialog
    ↓ connection_requested Signal
MainWindow._start_connection(config)
    ↓ create_connection(config)
Connection 对象
    ↓ conn.start() (启动后台线程)
后台线程 → 连接成功 → connected Signal
    ↓
MainWindow._on_tab_connected()
    → 更新标签颜色为绿
    → 更新会话面板状态为 connected
    → 更新状态栏

断开（用户操作 / 连接异常）→ disconnected Signal
    ↓
MainWindow._on_tab_disconnected()
    → 检查有无同名会话仍连接（_name_refcount）
    → 无 → 会话面板变红
    → 有 → 保持绿色
```

---

## 连接协议层

### 信号体系

```
BaseConnection (QObject)
├── output_received = Signal(str)    — 收到终端输出
├── connected = Signal()             — 连接已建立
├── disconnected = Signal(str)       — 连接已关闭（含原因）
└── error_occurred = Signal(str)     — 错误发生

TerminalWidget (QWidget)
├── output_received = Signal(str)    — 转发自连接
├── connected = Signal()             — 终端就绪
├── disconnected = Signal(str)       — 终端断开
├── connection_error = Signal(str)   — 终端错误
└── command_sent = Signal(str)       — 用户发送了命令
```

### 线程模型

每个连接在**独立的后台 daemon 线程**中运行：

```
Main/UI Thread             Background Thread
    │                           │
    │  start()                  │
    │ ─────────────────────►    │
    │                           │── connect (blocking)
    │                           │── loop: recv()
    │   output_received(text)   │
    │ ◄─────────────────────    │
    │                           │
    │          send(data)       │
    │ ─────────────────────►    │── channel.send()
    │                           │
    │                           │── break (on error/close)
    │   disconnected(msg)       │
    │ ◄─────────────────────    │
```

- 后台线程设置 `daemon=True`，主线程退出时自动终止
- 所有 UI 更新通过 Qt Signal 跨线程安全传递
- `_emit_output` / `_emit_signal` 使用 try/except 防止 RuntimeError

---

## 终端模拟

### pyte 集成

```
TerminalWidget.__init__()
  ├── self._screen = pyte.Screen(columns, lines)
  ├── self._stream = pyte.Stream(self._screen)
  └── pyte 配置:
      ├── set_mode(pyte.modes.LNM)     — 换行模式
      ├── set_mode(pyte.modes.IRM)     — 插入模式
      ├── set_mode(pyte.modes.DECSCNM) — 屏幕模式
      ├── set_mode(pyte.modes.DECRCKM) — 光标键应用模式
      └── define_charset()             — 字符集

_on_data(text):
  self._stream.feed(text)        ← pyte 解析转义序列
  self._update_scrollbar()       ← 更新滚动条
  self.update()                  ← 触发 paintEvent
```

### 自定义渲染

`paintEvent` 使用 `QPainter` 逐字符绘制：

1. 填充背景色（`self._bg`）
2. 遍历屏幕行，跳过 scroll_offset 之外的行
3. 对每个字符位置：
   - 如果在选择范围内，画选中背景色
   - 如果有搜索匹配，画黄色高亮
   - 获取字符的 `fg`/`bg` 颜色（支持 256 色 / 真彩色）
   - 如果字符反转（reverse video），交换 fg/bg
   - 绘制背景矩形 → 设置画笔颜色 → `drawText()`
5. 绘制光标（方块闪烁，每 500ms toggle）
6. 更新行号面板宽度

### 搜索实现

在内存中构建完整屏幕文本 → `re.finditer()` 匹配所有位置 → 黄色高亮绘制匹配区域。

---

## 会话与持久化

### 数据存储路径

```
开发模式：项目根目录下的相对路径
打包后：  %LOCALAPPDATA%/RatStudio/FrttyPro/

%LOCALAPPDATA%/RatStudio/FrttyPro/
├── sessions/              ← 保存的会话配置（.json）
├── logs/                  ← 终端日志（按会话名分文件夹）
├── quick_commands.json    ← 快捷命令数据
├── history.json           ← 历史命令
├── lang.json              ← 语言设置
└── last_session.json      ← 上次连接（自动恢复用）
```

### 会话保存格式

```json
{
  "type": "ssh",
  "host": "example.com",
  "port": 22,
  "username": "admin",
  "display_name": "My Server"
}
```

### 会话面板状态

- **活动会话** — 由 `_items` 列表维护，sid = 列表索引
- **已保存会话** — 由 `_saved_items` 列表维护，显示为灰色三角
- **同名引用计数** — `_name_refcount[label]` 统计同一显示名的活动 tab 数量
- **会话 ID 引用** — `_sid_refcount[sid]` 统计同一 sid 的引用数

---

## UI 组件

### 无边框窗口

```
MainWindow (FramelessWindowHint)
  └── TitleBar (自定义 QWidget)
  └── TabBarWidget (自定义标签栏)
  └── QStackedWidget (终端标签内容)
  └── QDockWidget (侧面板)
  │   ├── SessionTreePanel
  │   └── HistoryPanel
  ├── SendPanel (底部命令面板)
  ├── QuickTagsBar (顶部快捷命令)
  └── StatusBar (底部状态栏)
```

### 标签栏渲染

`ColorTabButton.paintEvent()` 绘制顺序：
1. 选中背景色（#252639）+ 底部颜色指示线
2. 左侧彩色圆点（SSH绿 / Serial黄 / Telnet蓝）
3. 标签文字
4. 右侧关闭叉号（hover → 红色圆形背景 + 白色叉号）
5. 自动宽度计算（文字 + 间距 + 圆点 + 叉号）

### 颜色方案

基于 Catppuccin Mocha 调色板：

| 用途 | 颜色 |
|------|------|
| SSH 圆点 | `#a6e3a1` (绿) |
| Serial 圆点 | `#f9e2af` (黄) |
| Telnet 圆点 | `#89b4fa` (蓝) |
| 背景 | `#1a1b2e` |
| 表面 | `#1e1e2e` |
| 文字 | `#cdd6f4` |
| 强调 | `#89b4fa` |
| 悬停 | `#45475a` |
| 错误 | `#f38ba8` |

---

## 同名字检测

当用户打开多个同名的已保存会话时，断开或关闭其中一个不应影响其他同名会话的连接状态。

### 实现

```python
_name_refcount = defaultdict(int)
```

- **新增连接** → `_name_refcount[label] += 1`
- **关闭 tab** → 断开连接后 `_name_refcount[label] -= 1`
- **断开信号处理** → 检查 `_name_refcount[name] <= 1` 才更新会话面板为 disconnected
- **Stale 信号防护** → `_sid_refcount` 中无对应 sid 时忽略延迟到达的 disconnected 信号

---

## 打包与兼容性

### 构建命令

```bash
pyinstaller --onefile --noconsole --icon=./frtty.ico --name="FrttyPro" \
  --add-data="./frtty.png;." --add-data="./Rat.png;." --add-data="./frtty.ico;." \
  --add-data="./app/i18n.py;./app/" --add-data="./app/resources.py;./app/" \
  --hidden-import=paramiko --hidden-import=pyserial --hidden-import=pyte \
  --hidden-import=wcwidth --hidden-import=shiboken2 main.py
```

### 一键制构建注意事项

| 挑战 | 解决方案 |
|---|---|
| `__file__` = 临时目录 | `get_data_dir()` → `%LOCALAPPDATA%` |
| 资源文件路径 | `get_app_dir()` → `sys._MEIPASS` |
| PySide6 不支持 Win7 | 使用 PySide2 (Qt 5.15) |
| cryptography _rust.pyd | 降级至 3.4.8（纯 C 扩展） |
| bcrypt _bcrypt.pyd | 降级至 4.0.1 |
| cffi VC++ 运行时 | 降级至 1.15.1 |
| PySide6 `QAction` 位置 | PySide2 中从 QtGui → QtWidgets |
| PySide6 `menu.exec()` | PySide2 中改为 `menu.exec_()` |
| PySide6 `event.position()` | PySide2 中改为 `event.pos()` |
| PySide6 `event.globalPosition()` | PySide2 中改为 `event.globalPos()` |
| 信号名 `connect` 冲突 | 基类方法改为 `start()` |

---

## 版本历史

| 版本 | 变更 |
|------|------|
| 1.2.7 | 修复 PySide2 兼容性、连接状态追踪、同名字检测；增加 Win7 支持 |
| 1.2.6 | 首次发布（PySide6 版） |
