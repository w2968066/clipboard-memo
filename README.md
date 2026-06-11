# 剪贴板备忘录 (Clipboard Memo)

<p align="center">
  <img src="assets/icon.png" width="128" alt="Clipboard Memo">
</p>

<p align="center">
  <b>极简本地剪贴板管理工具，专为 AI 用户设计</b>
</p>

<p align="center">
  <img src="https://img.shields.io/badge/platform-Windows-blue?style=flat-square">
  <img src="https://img.shields.io/badge/python-3.8+-green?style=flat-square">
  <img src="https://img.shields.io/badge/license-MIT-yellow?style=flat-square">
  <img src="https://img.shields.io/badge/dependencies-3-lightgrey?style=flat-square">
  <img src="https://img.shields.io/badge/network-zero-red?style=flat-square">
</p>

---

## Why this exists

> "试过 7 款剪贴板工具后，我花了 3 个晚上，写了自己的。"

市面上大多数剪贴板工具太重了——几十 MB 安装包、注册账号、云同步、付费弹窗。作为 AI 用户，我只想存个提示词。

**剪贴板备忘录**是一个 Python 脚本体量的工具。3 个依赖、零网络、纯本地、完全开源。

---

## Features

| 功能 | 说明 |
|---|---|
| 🔍 **自动捕获** | 复制文本或截图自动保存，500ms 轮询检测 |
| 🧠 **智能分类** | 纯本地多信号评分引擎，自动识别 Prompt/图片/文本 |
| ⌨️ **热键呼出** | `Ctrl+Shift+V` 全局热键，鼠标跟随弹出 |
| 🏷️ **快速分类** | 悬停条目 + 数字键 1-4：收藏/Prompt/图片/删除 |
| 📖 **状态标识** | 已分类/未分类 📖 标识，收藏 ⭐️ 标识 |
| 📂 **子分类** | Prompt 和图片各 4 级可自定义子分类 |
| 🔄 **单条刷新** | 分类/收藏操作只刷新单条状态，不卡顿 |
| 💾 **软删除** | 已删除内容保留 7 天，随时恢复 |
| 🧹 **缓存管理** | 显示数据库+图片总占用，批量清理 |
| 🌐 **国际化** | 中文/英文双语支持 |
| 🚀 **开机自启** | 托盘菜单一键切换 |
| ⚙️ **设置** | 自定义热键、子分类名称、语言 |

---

## Quick Start

### 1. 安装依赖

```bash
pip install -r requirements.txt
```

3 个依赖：
- `pystray` — 系统托盘
- `Pillow` — 图片缩略图
- `pywin32` — 剪贴板读写、全局热键

### 2. 启动

```bash
python main.py
```

### 3. 使用

| 操作 | 说明 |
|---|---|
| `Ctrl+Shift+V` | 呼出/隐藏浮窗 |
| 点击条目 | 粘贴到当前光标位置 |
| 点击 `分类` 按钮 | 进入快速分类模式 |
| 悬停条目 + `1/2/3/4` | 收藏 / Prompt / 图片 / 删除 |
| `Backspace` / `Delete` | 删除当前悬停条目 |
| `Esc` | 关闭浮窗 |
| `↑↓` | 导航选择条目 |
| `Enter` | 粘贴选中条目 |
| 右键条目 | 复制/收藏/编辑标题/删除 |

### 4. 一键打包（可选）

```bash
pip install pyinstaller
pyinstaller --onefile --windowed --name ClipboardMemo main.py
```

---

## Architecture

```
clipboard-memo/
├── main.py              # 应用入口，启动流程编排
├── popup_window.py       # 弹窗 UI（浮窗 + 清理窗口）
├── clipboard_monitor.py  # 剪贴板轮询监控
├── classifier.py         # 文本分类引擎（多信号评分）
├── storage.py            # SQLite 数据层（WAL 模式）
├── hotkey_manager.py     # Windows 全局热键（RegisterHotKey）
├── tray_icon.py          # 系统托盘（pystray）
├── settings_window.py    # 设置窗口
├── config.py             # 配置管理（内存缓存）
├── utils.py              # 工具函数
├── i18n.py               # 国际化（zh/en）
├── config.json           # 运行时配置
├── data/clipboard.db     # SQLite 数据库（自动创建）
├── assets/images/        # 图片存储
└── requirements.txt      # 3 个依赖
```

### Classification Engine

```
classify_text(text) → (category, summary, subcategory)

多信号评分权重：
  指令性动词    权重 4  (上限 12)
  角色定义模式  权重 5  (命中即满分)
  结构化特征    权重 2-3 (上限 6)
  提问模式      权重 2  (上限 4)
  代码相关      权重 2  (上限 4)
  长度系数      ×0.5 ~ ×1.0
  → 总分 ≥ 5 → "prompt" | 否则 "other_text"
```

### Hotkey System

```
Windows RegisterHotKey + HWND_MESSAGE 消息窗口
→ PeekMessageW 非阻塞消息循环
→ 支持热切换（reregister 无需重启）
→ 64-bit 原生支持（显式声明 ctypes argtypes）
```

---

## Tech Stack

| 层 | 技术 |
|---|---|
| UI | tkinter (overrideredirect 无边框窗口) |
| 数据 | SQLite (WAL, threading.local 连接池) |
| 分类 | 纯本地正则规则引擎 |
| 热键 | Windows RegisterHotKey API (ctypes) |
| 托盘 | pystray + PIL 图标绘制 |
| 配置 | JSON 文件 + 内存缓存 |
| 音效 | (无 — 完全静默运行) |

---

## FAQ

**Q: 为什么只有 Windows 版？**
A: 目前使用了 Windows 原生 API（RegisterHotKey、剪贴板读写）。macOS/Linux 支持计划中。

**Q: 数据安全吗？**
A: 完全本地运行，零网络请求。SQLite 文件在 `data/clipboard.db`，图片在 `assets/images/`。

**Q: 怎么卸载？**
A: 删除文件夹即可。如果启用了开机自启，先在托盘菜单中关闭。

---

## License

MIT © 2026

---

<p align="center">
  <sub>Built with ❤️ for the vibecoding community. #vibecoding大赏</sub>
</p>
