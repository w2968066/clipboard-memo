"""
文本分类器 — 多信号规则评分引擎
纯本地算法，零网络请求，保护用户隐私

分类目标：
  - 'prompt'      → AI 提示词
  - 'image'       → 图片（由剪贴板监控层判断）
  - 'other_text'  → 其他文本
"""

import re


# ============================================================
# 信号定义（预编译正则，提升性能）
# ============================================================

# 1. 指令性动词 — 权重 4
INSTRUCTION_VERBS_CN = [
    "帮我", "请帮我", "请你", "请你帮", "帮忙",
    "写一个", "写一段", "写一篇", "写一份", "写", "编写",
    "生成", "创建", "翻译", "总结", "概括",
    "分析", "解释", "描述", "说明", "阐述",
    "修改", "优化", "重构", "改进",
    "检查", "修复", "调试",
    "教我", "推荐", "建议", "给出",
    "设计", "实现", "开发",
    "计算", "转换", "比较", "对比",
    "整理", "规划", "安排", "制作",
]

INSTRUCTION_VERBS_EN = [
    "help me", "please help", "could you",
    "write a", "write me", "generate", "create",
    "translate", "summarize", "summarise",
    "analyze", "analyse", "explain", "describe",
    "implement", "fix", "debug", "optimize", "refactor",
    "teach me", "recommend", "suggest",
    "design", "develop", "build",
    "convert", "compare", "calculate",
    "review", "check", "improve",
]

# 2. 角色定义模式 — 权重 5（预编译）
ROLE_PATTERNS_CN = [re.compile(p) for p in [
    r"你是一个", r"你是[一名称位]",
    r"作为[一一个名称位]", r"作为一名",
    r"假装你是", r"假设你是", r"从现在开始你是",
    r"你的角色是", r"你的身份是",
    r"扮演", r"充当", r"担任",
    r"你现在是", r"我要你扮演",
]]

ROLE_PATTERNS_EN = [re.compile(p, re.IGNORECASE) for p in [
    r"you are a", r"you are an",
    r"act as a", r"act as an",
    r"pretend you are", r"pretend to be",
    r"from now on you are",
    r"your role is", r"you are now",
    r"i want you to act as", r"i want you to be",
    r"you will act as",
]]

# 3. 结构化特征 — 权重 2-3（预编译）
STRUCTURE_PATTERNS_CN = [(re.compile(p), w) for p, w in [
    (r"(步骤|第[一二三四五六七八九十\d]+步)", 3),
    (r"(首先|然后|最后|接着|其次|再次)", 3),
    (r"(要求|条件|规则|限制|约束)", 2),
    (r"(格式|用markdown|用表格|用列表|用代码|用json|用yaml)", 2),
    (r"(分[点步]|列出|列举|逐[条项])", 2),
    (r"(请.*[:：])", 2),
    (r"(不要|禁止|避免|注意|务必|必须)", 2),
    (r"(示例|例子|比如|例如|参考)", 2),
]]

STRUCTURE_PATTERNS_EN = [(re.compile(p, re.IGNORECASE), w) for p, w in [
    (r"(step\s*\d|first|then|finally|next)", 3),
    (r"(requirements?|constraints?|rules?|limitations?)", 2),
    (r"(format|markdown|table|bullet\s*points?|json|yaml|code)", 2),
    (r"(please\s.*[:：])", 2),
    (r"(do not|don't|avoid|make sure|ensure|must|should)", 2),
    (r"(example|e\.g\.|for instance|sample)", 2),
]]

# 4. 提问模式 — 权重 2（预编译）
QUESTION_PATTERNS_CN = [re.compile(p) for p in [
    r"如何", r"怎么", r"怎样", r"为什么",
    r"什么是", r"什么叫", r"是什么意思",
    r"区别.*是什么", r".*和.*的区别",
    r"请告诉[我我们]",
    r"有没有.*方法", r"是否",
]]

QUESTION_PATTERNS_EN = [re.compile(p, re.IGNORECASE) for p in [
    r"how (to|do|can|should|would|does|are|is|about|could|might|will)",
    r"what is", r"what are", r"what's", r"what (do|does|should|would|can)",
    r"why (is|are|do|does|should|would)",
    r"tell me (about|how|what|why)",
    r"(is there|are there) (a |any )",
    r"(can you|could you) (tell|explain|show|help)",
    r"please (tell|explain|show|describe|provide|give)",
]]

# 5. 代码相关 — 权重 2（预编译）
CODE_PATTERNS_CN = [re.compile(p) for p in [
    r"(写代码|写脚本|写程序|编程|脚本|代码)",
    r"(Python|Java|JavaScript|C\+\+|Go|Rust|TypeScript|SQL|HTML|CSS)",
    r"(实现[一个段])", r"(函数|方法|类|接口|模块)",
    r"(用\w+语言)", r"(用\w+实现)",
]]

CODE_PATTERNS_EN = [re.compile(p, re.IGNORECASE) for p in [
    r"(write\s*(a\s*)?(code|script|program|function|class))",
    r"(implement\s*(a\s*)?(function|class|method|algorithm))",
    r"(in\s*(python|javascript|java|c\+\+|go|rust|typescript))",
    r"(code\s*(snippet|example|sample))",
]]

# 其他预编译正则
_RE_PURE_URL = re.compile(r'^(https?://|ftp://|file://|www\.)[^\s]*$', re.IGNORECASE)
_RE_COLON_END = re.compile(r'[：:]\s*$')
_RE_ROLE_TITLE = re.compile(r'(?:你是|你是一个|作为一个|扮演|充当|act as an?|you are an?)\s*(.+?)(?:[，,。.\n]|请|帮我|$)', re.IGNORECASE)
_RE_ROLE_TASK = re.compile(r'(?:请|帮我|帮忙)(.+?)(?:[。.\n]|$)')
_RE_CN_ACTION = re.compile(r'(?:帮我|请帮我|请你|请|帮忙)\s*(写|生成|翻译|总结|分析|解释|修改|优化|修复|创建|设计|开发|实现|整理|规划|制作|计算|转换|比较|检查|推荐|教)?\s*(.+?)(?:[。.\n，,]|$)')
_RE_EN_ACTION = re.compile(r'(write|generate|create|translate|summarize|explain|analyze|implement|fix|optimize|refactor|design|develop|build|convert|compare|review|check|teach|recommend)\s*(?:a|an|the|me|this|some)?\s*(.+?)(?:[\.\n]|$)', re.IGNORECASE)
_RE_QUESTION = re.compile(r'(如何|怎么|怎样|什么是|为什么|区别|how to|what is|why|how do|how can)\s*(.+?)(?:[？?\n]|$)', re.IGNORECASE)
_RE_CLEAN_START = re.compile(r'^(那个|这个|嗯|额|就是说|我想|麻烦|能不能|可不可以)\s*')
_RE_SYMBOLS = re.compile(r'[{}();=<>&\[\]|!]')
_RE_CODE_INDICATORS = [
    (re.compile(r'^(import|from|require|const|let|var|function|def|class|public|private)\s'), True),
    (re.compile(r'^[{}\[\];]+$'), True),
    (re.compile(r'^[<>]=?\s*[\d.]+$'), True),
    (re.compile(r'^#include\s'), True),
    (re.compile(r'^package\s'), True),
    (re.compile(r'^SELECT\s.*FROM\s', re.IGNORECASE), True),
]


def classify_text(text):
    """
    对文本内容进行分类

    Args:
        text: 要分类的文本

    Returns:
        (category, summary, subcategory) 元组
        category: 'prompt' | 'other_text'
        summary: 简短摘要描述
        subcategory: 子分类 key（仅 prompt 有值）
    """
    if not text or not text.strip():
        return "other_text", "", ""

    text = text.strip()
    text_lower = text.lower()

    # ---- 负向信号检测 ----
    if _is_pure_url(text):
        return "other_text", _make_summary(text, is_url=True), ""

    if _is_pure_code(text):
        return "other_text", _make_summary(text), ""

    if _is_trivial(text):
        return "other_text", _make_summary(text), ""

    # ---- 正向信号评分 ----
    score = 0.0

    # 1. 指令性动词检测 (上限 12 分)
    verb_score = 0
    for verb in INSTRUCTION_VERBS_CN:
        if verb in text:
            verb_score += 4
            if verb_score >= 12:
                break
    if verb_score == 0:
        for verb in INSTRUCTION_VERBS_EN:
            if verb in text_lower:
                verb_score += 4
                if verb_score >= 12:
                    break
    score += verb_score

    # 2. 角色定义模式检测 (上限 5 分，命中即满分)
    for pattern in ROLE_PATTERNS_CN:
        if pattern.search(text):
            score += 5
            break
    else:
        for pattern in ROLE_PATTERNS_EN:
            if pattern.search(text_lower):
                score += 5
                break

    # 3. 结构化特征检测 (上限 6 分)
    struct_score = 0
    for pattern, weight in STRUCTURE_PATTERNS_CN:
        if pattern.search(text):
            struct_score += weight
            if struct_score >= 6:
                break
    if struct_score == 0:
        for pattern, weight in STRUCTURE_PATTERNS_EN:
            if pattern.search(text_lower):
                struct_score += weight
                if struct_score >= 6:
                    break
    score += struct_score

    # 4. 提问模式检测 (上限 4 分)
    q_score = 0
    for pattern in QUESTION_PATTERNS_CN:
        if pattern.search(text):
            q_score += 2
            if q_score >= 4:
                break
    if q_score == 0:
        for pattern in QUESTION_PATTERNS_EN:
            if pattern.search(text_lower):
                q_score += 2
                if q_score >= 4:
                    break
    score += q_score

    # 5. 代码相关检测 (上限 4 分)
    code_score = 0
    for pattern in CODE_PATTERNS_CN:
        if pattern.search(text):
            code_score += 2
            if code_score >= 4:
                break
    if code_score == 0:
        for pattern in CODE_PATTERNS_EN:
            if pattern.search(text_lower):
                code_score += 2
                if code_score >= 4:
                    break
    score += code_score

    # 6. 长度系数
    text_len = len(text)
    if text_len < 10:
        score *= 0.5
    elif text_len <= 200:
        score *= 1.0
    elif text_len <= 2000:
        score *= 0.8
    else:
        score *= 0.5

    # 7. 额外加分：多行结构化文本
    line_count = text.count("\n") + 1
    if line_count >= 3 and score >= 3:
        score += 1  # 多行且有指令性，很可能是 prompt

    # 8. 冒号结尾的指令句
    if _RE_COLON_END.search(text.strip()):
        score += 1

    # ---- 分类判定 ----
    if score >= 5:
        category = "prompt"
    else:
        category = "other_text"

    summary = _make_summary(text)

    # 子分类推断（仅 prompt）
    subcategory = ""
    if category == "prompt":
        subcategory = _infer_prompt_subcategory(text)

    return category, summary, subcategory


def _infer_prompt_subcategory(text):
    """推断 prompt 的子分类"""
    text_lower = text.lower()
    # 代码相关
    if any(kw in text for kw in ["代码", "写一个", "函数", "脚本", "bug", "debug", "编程",
                                   "python", "javascript", "function", "code", "api"]):
        return "prompt_sub2"  # 默认子分类2 → 代码
    # 写作相关
    if any(kw in text for kw in ["写一篇", "写一段", "文章", "翻译", "总结", "概括", "改写",
                                   "translate", "summarize", "write", "article"]):
        return "prompt_sub3"  # 默认子分类3 → 写作
    # 通用
    return "prompt_sub1"  # 默认子分类1 → 通用


def _is_pure_url(text):
    """检查是否为纯 URL"""
    return bool(_RE_PURE_URL.match(text.strip()))


def _is_pure_code(text):
    """检查是否为纯代码（无自然语言成分）"""
    stripped = text.strip()
    for pattern, _ in _RE_CODE_INDICATORS:
        if pattern.search(stripped):
            if len(_RE_SYMBOLS.findall(text)) > 3:
                return True

    # 符号密度过高
    symbols = len(_RE_SYMBOLS.findall(text))
    total_chars = len(text)
    if total_chars > 10 and symbols / total_chars > 0.15:
        return True

    return False


def _is_trivial(text):
    """检查是否为简单/琐碎文本"""
    text_stripped = text.strip()

    # 纯数字
    if re.match(r'^[\d\s\-+.,]+$', text_stripped) and len(text_stripped) < 30:
        return True

    # 单个单词
    if len(text_stripped.split()) == 1 and len(text_stripped) < 20:
        return True

    # 纯特殊字符
    if re.match(r'^[^\w\s]+$', text_stripped):
        return True

    return False


def _make_summary(text, is_url=False):
    """为所有文本类型生成摘要"""
    if not text:
        return ""
    text = text.strip()

    if is_url:
        match = _RE_PURE_URL.search(text)
        if match:
            domain = match.group(0).replace("https://", "").replace("http://", "").replace("www.", "").split("/")[0]
            return f"链接: {domain}"
        return "链接"

    return _make_title(text)


def _make_title(text):
    """为文本生成简短标题（10-30字符），提炼核心意图"""
    if not text:
        return ""

    text = text.strip()
    first_line = text.split("\n")[0].strip()

    # ---- 模式1: 角色定义 → "角色: 任务" ----
    role_match = _RE_ROLE_TITLE.search(text)
    if role_match:
        role = role_match.group(1).strip()
        task_match = _RE_ROLE_TASK.search(text)
        task = task_match.group(1).strip()[:12] if task_match else ""
        if task:
            return f"{_shorten(role, 10)}：{_shorten(task, 12)}"
        return _shorten(role, 22)

    # ---- 模式2: "帮我/请 + 动词 + 宾语" ----
    action_match = _RE_CN_ACTION.search(text)
    if action_match:
        verb = action_match.group(1) or ""
        obj = action_match.group(2).strip()
        return _shorten(f"{verb}{obj}", 24)

    # ---- 模式3: 英文指令动词 ----
    en_action = _RE_EN_ACTION.search(first_line)
    if en_action:
        verb = en_action.group(1).strip()
        obj = (en_action.group(2) or "").strip()
        result = f"{verb} {obj}".strip()
        return _shorten(result, 26)

    # ---- 模式4: 问题类 → 提取主题 ----
    question = _RE_QUESTION.search(first_line)
    if question:
        topic = (question.group(2) or "").strip()
        qword = question.group(1).strip()
        return _shorten(f"{qword}{topic}", 22)

    # ---- 模式5: 结构化长文本 → 取第一句的主干 ----
    if len(text) > 60:
        cleaned = _RE_CLEAN_START.sub('', first_line)
        return _shorten(cleaned, 24)

    # ---- 通用: 清理后取前20字 ----
    cleaned = re.sub(r'\s+', ' ', first_line).strip()
    return _shorten(cleaned, 22)


def _shorten(s, max_len):
    """截断文本，确保在 max_len 以内"""
    if len(s) <= max_len:
        return s
    return s[:max_len-2] + "…"
