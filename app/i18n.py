_current_lang = "zh"

ZH = {}
EN = {}


def init():
    global ZH, EN
    ZH.update({
        "app.name": "Frtty Pro",
        "app.version": "1.0.0",

        "title_bar.title": "Frtty Pro",

        "menu.session": "会话",
        "menu.session.new": "新建连接",
        "menu.session.close": "关闭当前连接",
        "menu.session.save": "保存会话",
        "menu.session.disconnect_all": "全部断开",
        "menu.session.exit": "退出",
        "menu.edit": "编辑",
        "menu.edit.copy": "复制",
        "menu.edit.paste": "粘贴",
        "menu.edit.find": "查找",
        "menu.edit.select_all": "全选",
        "menu.view": "查看",
        "menu.view.session_panel": "会话面板",
        "menu.view.show_line_number": "显示行号",
        "menu.view.fullscreen": "全屏",
        "menu.tools": "工具",
        "menu.tools.options": "选项设置",
        "menu.tools.language": "切换语言",

        "options.lang_zh": "中文",
        "options.lang_en": "English",
        "menu.help": "帮助",
        "menu.help.about": "关于 Frtty Pro",

        "session_panel.title": "会话",
        "session_panel.filter": "筛选",
        "session_panel.clear": "清除会话",
        "session_panel.history": "历史命令",
        "session_panel.edit_session": "编辑会话",
        "session_panel.delete_session": "删除会话",
        "session_panel.delete_confirm": "确认删除 '{0}'？",

        "status.ready": "就绪",
        "status.remote": "远程模式",
        "status.disconnected": "已断开",
        "status.encoding": "Plain Text",
        "status.window": "窗口 {0}x{1}",
        "status.cursor": "行{0}  字符{1}",

        "dialog.new_connection": "新建连接",
        "dialog.edit_session": "编辑会话",
        "dialog.save": "保存",
        "dialog.connect": "Connect",
        "dialog.cancel": "Cancel",
        "dialog.save_session": "连接后保存为会话",
        "dialog.load_session": "加载已保存的会话...",
        "dialog.quick_actions": "快速操作",

        "ssh.host": "主机:",
        "ssh.port": "端口:",
        "ssh.username": "用户名:",
        "ssh.password": "密码:",
        "ssh.password_placeholder": "密码 (可选)",
        "ssh.host_placeholder": "例如 192.168.1.100",
        "ssh.username_placeholder": "用户名",

        "serial.port": "端口:",
        "serial.refresh_ports": "刷新串口列表",
        "serial.no_ports_found": "未发现串口",
        "serial.baud": "波特率:",
        "serial.data_bits": "数据位:",
        "serial.parity": "校验:",
        "serial.stop_bits": "停止位:",

        "telnet.host": "主机:",
        "telnet.port": "端口:",
        "telnet.host_placeholder": "例如 192.168.1.100",

        "send_panel.title": "发送面板",
        "send_panel.send": "发送",
        "send_panel.stop": "停止",
        "send_panel.sending": "发送中 ({0})",
        "send_panel.shell": "Shell",
        "send_panel.text": "文本",
        "send_panel.hex": "Hex",
        "send_panel.by_line": "行(L)",
        "send_panel.by_label": "按:",
        "send_panel.by_char": "字符(G)",
        "send_panel.count": "计数:",
        "send_panel.interval": "间隔:",
        "send_panel.target": "目标:",
        "send_panel.current_session": "当前会话",
        "send_panel.input_placeholder": "输入命令... (Ctrl+Enter 发送)",
        "send_panel.clear": "清空",

        "terminal.welcome_title": "Frtty Pro v1.0",
        "terminal.welcome_subtitle": "SSH / Serial / Telnet 终端",
        "terminal.welcome_hint": "文件 > 新建连接 开始使用",
        "terminal.connecting": "正在连接",
        "terminal.connected": "已连接",
        "terminal.closed": "连接已关闭",
        "terminal.error": "错误",

        "tab.new_connection_tooltip": "新建连接",
        "tab.close": "关闭",

        "status.reconnecting": "重新连接中...",
        "status.ssh_ended": "SSH 会话结束",
        "status.serial_closed": "串口连接已关闭",
        "status.telnet_ended": "Telnet 会话结束",

        "context.disconnect": "断开连接",
        "context.reconnect": "重新连接",
        "context.close": "关闭",

        "quick.edit_command": "编辑命令",
        "quick.delete_command": "删除命令",
        "quick.delete_confirm": "删除 '{0}'?",
        "quick.manage_groups": "管理分组...",
        "quick.add_command": "添加命令",
        "quick.new_group": "新建分组",
        "quick.rename_group": "重命名分组",
        "quick.delete_group": "删除分组",
        "quick.clear_all": "清除全部",
        "quick.remove_all": "删除所有分组和命令？",
        "quick.no_group": "无分组",
        "quick.create_group_first": "请先创建分组。",

        "dialog.display_name": "显示名称 (留空则自动)",
        "dialog.name": "名称:",
        "dialog.command_to_send": "发送命令:",
        "dialog.ok": "确定",
        "dialog.cancel": "取消",

        "error.host_required": "主机地址不能为空",
        "error.serial_port_required": "串口号不能为空",

        "log.menu": "日志",
        "log.start": "开始",
        "log.stop": "停止",
        "log.open_folder": "打开日志文件夹",
        "log.select_dir": "选择日志保存路径",
        "log.started": "日志记录已开始",
        "log.stopped": "日志记录已停止",
        "log.no_session": "无活动会话",
        "log.no_folder": "尚未开始记录日志",

        "search.placeholder": "查找...",
        "search.prev": "上一个",
        "search.next": "下一个",
        "search.close": "关闭",
    })

    EN.update({
        "app.name": "Frtty Pro",
        "app.version": "1.0.0",

        "title_bar.title": "Frtty Pro",

        "menu.session": "Session",
        "menu.session.new": "New Connection",
        "menu.session.close": "Close Current",
        "menu.session.save": "Save Session",
        "menu.session.disconnect_all": "Disconnect All",
        "menu.session.exit": "Exit",
        "menu.edit": "Edit",
        "menu.edit.copy": "Copy",
        "menu.edit.paste": "Paste",
        "menu.edit.find": "Find",
        "menu.edit.select_all": "Select All",
        "menu.view": "View",
        "menu.view.session_panel": "Session Panel",
        "menu.view.show_line_number": "Show Line Numbers",
        "menu.view.fullscreen": "Fullscreen",
        "menu.tools": "Tools",
        "menu.tools.options": "Options",
        "menu.tools.language": "Switch Language",

        "options.lang_zh": "中文",
        "options.lang_en": "English",
        "menu.help": "Help",
        "menu.help.about": "About Frtty Pro",

        "session_panel.title": "Sessions",
        "session_panel.filter": "Filter",
        "session_panel.clear": "Clear Sessions",
        "session_panel.history": "History",
        "session_panel.edit_session": "Edit Session",
        "session_panel.delete_session": "Delete Session",
        "session_panel.delete_confirm": "Delete '{0}'?",

        "status.ready": "Ready",
        "status.remote": "Remote Mode",
        "status.disconnected": "Disconnected",
        "status.encoding": "Plain Text",
        "status.window": "Win {0}x{1}",
        "status.cursor": "Row {0}  Col {1}",

        "dialog.new_connection": "New Connection",
        "dialog.edit_session": "Edit Session",
        "dialog.save": "Save",
        "dialog.connect": "Connect",
        "dialog.cancel": "Cancel",
        "dialog.save_session": "Save as session after connect",
        "dialog.load_session": "Load Saved Session...",
        "dialog.quick_actions": "Quick Actions",

        "ssh.host": "Host:",
        "ssh.port": "Port:",
        "ssh.username": "Username:",
        "ssh.password": "Password:",
        "ssh.password_placeholder": "password (optional)",
        "ssh.host_placeholder": "e.g. 192.168.1.100",
        "ssh.username_placeholder": "username",

        "serial.port": "Port:",
        "serial.refresh_ports": "Refresh COM ports",
        "serial.no_ports_found": "No serial ports found",
        "serial.baud": "Baud Rate:",
        "serial.data_bits": "Data Bits:",
        "serial.parity": "Parity:",
        "serial.stop_bits": "Stop Bits:",

        "telnet.host": "Host:",
        "telnet.port": "Port:",
        "telnet.host_placeholder": "e.g. 192.168.1.100",

        "send_panel.title": "Send Panel",
        "send_panel.send": "Send",
        "send_panel.stop": "Stop",
        "send_panel.sending": "Sending ({0})",
        "send_panel.shell": "Shell",
        "send_panel.text": "Text",
        "send_panel.hex": "Hex",
        "send_panel.by_line": "Line(L)",
        "send_panel.by_label": "By:",
        "send_panel.by_char": "Char(G)",
        "send_panel.count": "Count:",
        "send_panel.interval": "Interval:",
        "send_panel.target": "Target:",
        "send_panel.current_session": "Current Session",
        "send_panel.input_placeholder": "Enter command... (Ctrl+Enter to send)",
        "send_panel.clear": "Clear",

        "terminal.welcome_title": "Frtty Pro v1.0",
        "terminal.welcome_subtitle": "SSH / Serial / Telnet Terminal",
        "terminal.welcome_hint": "File > New Connection to start",
        "terminal.connecting": "Connecting",
        "terminal.connected": "Connected",
        "terminal.closed": "Connection closed",
        "terminal.error": "Error",

        "tab.new_connection_tooltip": "New Connection",
        "tab.close": "Close",

        "status.reconnecting": "Reconnecting...",
        "status.ssh_ended": "SSH session ended",
        "status.serial_closed": "Serial connection closed",
        "status.telnet_ended": "Telnet session ended",

        "context.disconnect": "Disconnect",
        "context.reconnect": "Reconnect",
        "context.close": "Close",

        "quick.edit_command": "Edit Command",
        "quick.delete_command": "Delete Command",
        "quick.delete_confirm": "Delete '{0}'?",
        "quick.manage_groups": "Manage Groups...",
        "quick.add_command": "Add Command",
        "quick.new_group": "New Group",
        "quick.rename_group": "Rename Group",
        "quick.delete_group": "Delete Group",
        "quick.clear_all": "Clear All",
        "quick.remove_all": "Remove all groups and commands?",
        "quick.no_group": "No Group",
        "quick.create_group_first": "Create a group first.",

        "dialog.display_name": "Display Name (optional, auto if empty)",
        "dialog.name": "Name:",
        "dialog.command_to_send": "Command to send:",
        "dialog.ok": "OK",
        "dialog.cancel": "Cancel",

        "error.host_required": "Host is required",
        "error.serial_port_required": "Serial port is required",

        "log.menu": "Log",
        "log.start": "Start",
        "log.stop": "Stop",
        "log.open_folder": "Open Log Folder",
        "log.select_dir": "Select log save path",
        "log.started": "Logging started",
        "log.stopped": "Logging stopped",
        "log.no_session": "No active session",
        "log.no_folder": "No log folder yet",

        "search.placeholder": "Find...",
        "search.prev": "< Prev",
        "search.next": "Next >",
        "search.close": "Close",
    })


def tr(key):
    d = ZH if _current_lang == "zh" else EN
    return d.get(key, key)


def set_language(lang):
    global _current_lang
    _current_lang = lang


def current_language():
    return _current_lang


init()
