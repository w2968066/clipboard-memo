# 粘贴问题分析 — 接力文档

> ## ✅ 已解决（2026-06-12）
>
> **下文的"根本原因推测"（OLE/COM 剪贴板格式）是错的**，保留仅供参考。实测验证：
> 程序写入剪贴板后手动 Ctrl+V 一切正常，Win+V 历史里内容完好可用——剪贴板格式没有任何问题。
>
> ### 真实根因 1：文字和图片走的注入路径不同
> `unicode_text_paste` 开启时，≤2000 字符的文本走 `_type_text_unicode()`——用
> `SendInput + KEYEVENTF_UNICODE` 逐字符"打字"，**根本没有按 Ctrl+V**；
> 而图片一直走模拟 Ctrl+V。微信/WebView2 等 Chromium 应用会丢弃注入式打字输入，
> 所以"图片可以、文字不行"。修复：`unicode_text_paste` 改为 `false`，文字统一走 Ctrl+V。
>
> ### 真实根因 2：WS_EX_NOACTIVATE 设错了窗口句柄
> 防抢焦点样式之前设在 `winfo_id()` 返回的句柄上——Tk 在 Windows 上那是客户区子窗口，
> 真正的顶层是其祖先 wrapper（`GetAncestor(GA_ROOT)`）。样式没生效，点击弹窗仍会抢焦点，
> 导致朋友圈评论框自动关闭、WebView2 输入框丢失光标。修复：新增 `_get_toplevel_hwnd()`。
>
> ### 连带调整（NOACTIVATE 生效后的配套）
> - 弹窗收不到 FocusOut → 改为轮询检测窗口外鼠标按下来关闭弹窗
> - 分类模式需要数字键 → 进入时 `_activate_popup()` 显式拿焦点
> - 新开的清理/设置窗口会被压在前台应用后面 → `_bring_window_to_front()`
>
> ### 顺手修复的老 bug
> - `storage.get_storage_size()` 未导入 `IMAGES_DIR`，一直 NameError → 清理窗口缓存占用显示 "--"
> - 清理窗口图片条目从未渲染缩略图
> - 清理窗口滚轮只绑了 Canvas，悬停在条目上无效 → 改绑窗口级

---

## 现象

在部分应用中（微信、WebView2 无限画布等），点击条目后文字无法粘贴，但图片可以正常粘贴。

Windows 11 自带的 **Win+V** 在这些应用中粘贴文字完全正常。

## 已尝试的修复方案（均未解决）

| 尝试 | 结果 |
|---|---|
| `keybd_event` → `SendInput` 模拟 Ctrl+V | 图片可以，文字不行 |
| `time.sleep` 阻塞 → `after()` 链式调用 | 无改善 |
| 延迟 100ms → 150ms → 400ms | 无改善 |
| `SetClipboardText(CF_UNICODETEXT)` | 文字不行 |
| `SetClipboardText` + `SetClipboardData(CF_TEXT)` | 文字不行 |
| 原生 `GlobalAlloc → wcscpy → SetClipboardData(CF_UNICODETEXT)` | 文字不行 |

## 关键线索

1. **图片粘贴正常**：图片用 `SetClipboardData(CF_DIB, dib_bytes)` 写入剪贴板 → `SendInput` 模拟 Ctrl+V
2. **文字粘贴异常**：文字用 `SetClipboardData(CF_UNICODETEXT, hMem)` 写入剪贴板 → `SendInput` 模拟 Ctrl+V
3. 两者用**完全相同的 `SendInput` 模拟按键**，所以问题不在按键注入
4. **Win+V 正常**：Windows 系统级的剪贴板历史使用的文本设置方式与我们的不同

## 根本原因推测

现代 Windows 应用（WebView2、微信等基于 Chromium/Electron 的应用）使用 **OLE/COM 剪贴板接口**（`OleGetClipboard` → `IDataObject`）来读取剪贴板内容，而不是传统的 `GetClipboardData` API。

我们用 `SetClipboardData(CF_UNICODETEXT, ...)` 设置的是传统剪贴板格式。：
- 传统 Win32 应用（记事本、Word 等）可以读取 `CF_UNICODETEXT`
- 现代 Chromium/Electron 应用需要剪贴板通过 COM `IDataObject` 暴露

**图片之所以能粘贴**，是因为 `CF_DIB` 格式比较特殊，Chromium 可能对它的兼容性处理更好，或者我们的 `CF_DIB` 设置被 Chromium 列入了白名单。

Win+V 使用 `OleSetClipboard` 设置剪贴板内容，所以它能被所有应用读取。

## 推荐解决方案（优先级从高到低）

### 方案 A：用 `pyperclip` 库替代自实现（最简单）

```bash
pip install pyperclip
```

```python
# config.py — 新增依赖
# requirements.txt — 新增 pyperclip

# popup_window.py
def _copy_to_clipboard(self, text):
    import pyperclip
    pyperclip.copy(text)  # pyperclip 内部用更高级的方式设置剪贴板
```

pyperclip 在 Windows 上尝试多种方式设置剪贴板，包括 fallback 到 `SetClipboardText`。可能它的实现更完善。

### 方案 B：用 `OleSetClipboard` 实现 COM 剪贴板

这是最正确的方案，和 Win+V 使用相同的 API。

```python
def _copy_to_clipboard_ole(self, text):
    """用 OLE 接口设置剪贴板，兼容 Chromium/Electron 应用"""
    import ctypes
    from ctypes import wintypes
    import pythoncom
    from win32com import storagecon
    import pywintypes
    
    # 创建 IDataObject
    pythoncom.CoInitialize()
    
    # 使用 SHCreateDataObject 或手动实现 IDataObject
    # 设置 FORMATETC → CF_UNICODETEXT
    # OleSetClipboard(data_object)
```

### 方案 C：添加 `CF_HTML` 格式到剪贴板

Chromium 优先读取剪贴板中的 HTML 格式。如果同时设置 `CF_UNICODETEXT` 和 `CF_HTML`，可能解决兼容性问题。

```python
# 注册 HTML 格式
CF_HTML = win32clipboard.RegisterClipboardFormat("HTML Format")

# 设置 HTML 内容
html = f"<html><body>{text}</body></html>"
win32clipboard.SetClipboardData(CF_HTML, html.encode('utf-8'))
```

### 方案 D：直接 `SendMessage(WM_PASTE)` 到目标窗口

放弃模拟按键，直接向目标窗口发送 `WM_PASTE` 消息。

```python
import win32gui
hwnd = win32gui.GetForegroundWindow()
# 获取焦点控件
focused = win32gui.GetFocus() or hwnd
win32gui.SendMessage(focused, 0x0302, 0, 0)  # WM_PASTE
```

但这对 Chromium 渲染的控件不一定有效（Chromium 自己管理渲染，不直接响应 WM_PASTE）。

### 方案 E：不自动粘贴，只复制到剪贴板

```python
# 复制后关闭窗口，用户手动 Ctrl+V
# 可以弹出托盘通知 "已复制到剪贴板"
```

这是最可靠的方案，但牺牲了使用体验。

## 当前剪贴板代码位置

- `popup_window.py:1080` — `_copy_to_clipboard(text)` — 文本剪贴板写入
- `popup_window.py:1097` — `_copy_image_to_clipboard(path)` — 图片剪贴板写入（**正常**）
- `popup_window.py:690` — `_paste_item(item_id)` — 粘贴入口
- `popup_window.py:1123` — `_simulate_paste()` — Ctrl+V 模拟

## 验证步骤

1. 在剪贴板备忘录中复制文本
2. 不要点击条目关闭窗口
3. 手动在目标应用中 Ctrl+V
4. 如果手动粘贴成功 → 问题在按键模拟
5. 如果手动粘贴也失败 → 问题在剪贴板格式

## 文件清单

所有核心文件都在 `C:\Users\Windows\clipboard-memo\` 目录下。
