"""
剪贴板备忘录 — 短视频录屏脚本（抖音/B站/小红书版）
话题: #vibecoding大赏
"""

# ============================================================
# 视频规格建议
# ============================================================
# 分辨率: 1080x1920 (竖屏) 或 1920x1080 (横屏)
# 时长: 45-60 秒
# BGM: 快节奏电子/lo-fi beat，剪辑点配合操作
# 字幕: 大字幕，每句不超过10个字，关键词高亮
# ============================================================

class ShortVideoScript:
    def __init__(self):
        self.scenes = []
        self._build_scenes()

    def _build_scenes(self):

        # ---- 钩子（0-3秒）----
        self.scenes.append({
            "timestamp": "0:00-0:03",
            "duration": "3s",
            "title": "强钩子开场",
            "visual": [
                "黑屏 + 白色大字弹入: '你的提示词都去哪了？'",
                "紧接着弹入: '复制完就消失？'",
                "快速闪过3个消失的提示词片段"
            ],
            "subtitle": "你的提示词都去哪了？| 复制完就消失？",
            "narration": "",
            "bgm_beat": "重拍落下"
        })

        # ---- 问题共鸣（3-8秒）----
        self.scenes.append({
            "timestamp": "0:03-0:08",
            "duration": "5s",
            "title": "痛点共鸣",
            "visual": [
                "录屏: 用户在浏览器复制一段提示词",
                "复制后剪贴板被下一条内容覆盖",
                "用户表情懊恼（配表情包）"
            ],
            "subtitle": "剪贴板只能存一条 | 找不到了！",
            "narration": "",
            "bgm_beat": "快节奏切片"
        })

        # ---- 产品亮相（8-12秒）----
        self.scenes.append({
            "timestamp": "0:08-0:12",
            "duration": "4s",
            "title": "产品亮相",
            "visual": [
                "按 Ctrl+Shift+V，浮窗以缩放动画弹出",
                "黑色背景 + 蓝色强调色的窗口",
                "列表中已有多个历史条目"
            ],
            "subtitle": "按 Ctrl+Shift+V | 剪贴板历史全在这",
            "narration": "",
            "bgm_beat": "drop 落下"
        })

        # ---- 核心卖点1：智能分类（12-18秒）----
        self.scenes.append({
            "timestamp": "0:12-0:18",
            "duration": "6s",
            "title": "智能分类",
            "visual": [
                "复制一段提示词: '帮我写一个Python爬虫...'",
                "浮窗自动刷新，新条目出现在顶部",
                "📖 标识自动变亮（accent色）",
                "切换 2Prompt / 3图片 标签，内容自动归类"
            ],
            "subtitle": "自动识别提示词 | 一键分类 | 本地运行零上传",
            "narration": "",
            "bgm_beat": "连续切片"
        })

        # ---- 核心卖点2：快速分类模式（18-26秒）----
        self.scenes.append({
            "timestamp": "0:18-0:26",
            "duration": "8s",
            "title": "悬停分类",
            "visual": [
                "点击底部'分类'按钮",
                "鼠标悬停在未分类条目上，高亮显示",
                "按 2 → 条目分类为 Prompt",
                "📖 瞬间变亮（单条刷新，不卡顿）",
                "按 1 → ⭐️ 出现（收藏）",
                "按 Backspace → 条目删除"
            ],
            "subtitle": "悬停 + 数字键 | 1收藏 2Prompt 3图片 4删除 | Backspace直接删",
            "narration": "",
            "bgm_beat": "节奏加速"
        })

        # ---- 核心卖点3：图片捕获（26-32秒）----
        self.scenes.append({
            "timestamp": "0:26-0:32",
            "duration": "6s",
            "title": "图片捕获",
            "visual": [
                "按 PrintScreen 截图",
                "浮窗自动刷新，截图出现在顶部",
                "显示缩略图预览",
                "点击条目直接粘贴图片"
            ],
            "subtitle": "截图也能自动保存 | 缩略图一目了然 | 点击直接粘贴",
            "narration": "",
            "bgm_beat": "切片"
        })

        # ---- 核心卖点4：收藏与粘贴（32-38秒）----
        self.scenes.append({
            "timestamp": "0:32-0:38",
            "duration": "6s",
            "title": "收藏与粘贴",
            "visual": [
                "点击 ⭐️ 收藏常用提示词",
                "切换到 1收藏 标签查看",
                "点击任意条目",
                "切换到编辑器，内容自动粘贴到光标处"
            ],
            "subtitle": "⭐️ 收藏常用内容 | 点击即粘贴 | 不需要再复制",
            "narration": "",
            "bgm_beat": "切片"
        })

        # ---- 核心卖点5：缓存管理（38-44秒）----
        self.scenes.append({
            "timestamp": "0:38-0:44",
            "duration": "6s",
            "title": "缓存管理",
            "visual": [
                "点击'清理'按钮，打开清理窗口",
                "顶部显示: '缓存占用: 15.6 MB'",
                "勾选多条记录批量删除",
                "已删除保留7天自动清理"
            ],
            "subtitle": "缓存大小一目了然 | 批量清理 | 7天自动回收",
            "narration": "",
            "bgm_beat": "切片"
        })

        # ---- 结尾 CTA（44-50秒）----
        self.scenes.append({
            "timestamp": "0:44-0:50",
            "duration": "6s",
            "title": "结尾CTA",
            "visual": [
                "浮窗关闭，回到桌面",
                "托盘图标蓝色圆形闪烁",
                "大字弹入: 'Ctrl+Shift+V 开始体验'",
                "话题标签弹出: #vibecoding大赏"
            ],
            "subtitle": "完全本地运行 | 保护隐私 | Ctrl+Shift+V 开始体验",
            "narration": "",
            "bgm_beat": "drop 收尾"
        })

    def print_script(self):
        print("=" * 70)
        print("  剪贴板备忘录 — 短视频录屏脚本")
        print("  话题: #vibecoding大赏")
        print("  平台: 抖音 / B站 / 小红书")
        print("  建议时长: 45-50 秒")
        print("=" * 70)

        total = 0
        for scene in self.scenes:
            dur = int(scene["duration"].replace("s", ""))
            total += dur
            print(f"\n【{scene['timestamp']} | {scene['duration']}】{scene['title']}")
            print("-" * 50)
            print("画面:")
            for v in scene["visual"]:
                print(f"  ▸ {v}")
            print(f"字幕: {scene['subtitle']}")
            print(f"BGM节奏: {scene['bgm_beat']}")

        print(f"\n{'='*70}")
        print(f"总时长: {total} 秒")
        print(f"{'='*70}")

        print("\n" + "=" * 70)
        print("剪辑建议:")
        print("=" * 70)
        print("""
1. 前3秒必须抓住注意力，用大字+弹入动画
2. 每5秒一个节奏点，配合BGM的drop/切片
3. 操作录屏用1.2-1.5倍速播放，增加节奏感
4. 关键操作（按数字键、收藏）用放大特效+音效
5. 📖 和 ⭐️ 标识变亮时用闪光特效
6. 结尾托盘图标闪烁引导用户尝试
7. 字幕用白色粗体，关键词用 accent 色 #7eb8ff 高亮
8. 添加打字机音效配合操作
""")

        print("=" * 70)
        print("完整字幕稿（可直接复制到剪辑软件）:")
        print("=" * 70)
        for scene in self.scenes:
            print(f"\n[{scene['timestamp']}] {scene['subtitle']}")


if __name__ == "__main__":
    script = ShortVideoScript()
    script.print_script()
