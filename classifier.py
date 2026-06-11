"""
鏂囨湰鍒嗙被鍣?鈥?澶氫俊鍙疯鍒欒瘎鍒嗗紩鎿?绾湰鍦扮畻娉曪紝闆剁綉缁滆姹傦紝淇濇姢鐢ㄦ埛闅愮

鍒嗙被鐩爣锛?  - 'prompt'      鈫?AI 鎻愮ず璇?  - 'image'       鈫?鍥剧墖锛堢敱鍓创鏉跨洃鎺у眰鍒ゆ柇锛?  - 'other_text'  鈫?鍏朵粬鏂囨湰
"""

import re


# ============================================================
# 淇″彿瀹氫箟锛堥缂栬瘧姝ｅ垯锛屾彁鍗囨€ц兘锛?# ============================================================

# 1. 鎸囦护鎬у姩璇?鈥?鏉冮噸 4
INSTRUCTION_VERBS_CN = [
    "甯垜", "璇峰府鎴?, "璇蜂綘", "璇蜂綘甯?, "甯繖",
    "鍐欎竴涓?, "鍐欎竴娈?, "鍐欎竴绡?, "鍐欎竴浠?, "鍐?, "缂栧啓",
    "鐢熸垚", "鍒涘缓", "缈昏瘧", "鎬荤粨", "姒傛嫭",
    "鍒嗘瀽", "瑙ｉ噴", "鎻忚堪", "璇存槑", "闃愯堪",
    "淇敼", "浼樺寲", "閲嶆瀯", "鏀硅繘",
    "妫€鏌?, "淇", "璋冭瘯",
    "鏁欐垜", "鎺ㄨ崘", "寤鸿", "缁欏嚭",
    "璁捐", "瀹炵幇", "寮€鍙?,
    "璁＄畻", "杞崲", "姣旇緝", "瀵规瘮",
    "鏁寸悊", "瑙勫垝", "瀹夋帓", "鍒朵綔",
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

# 2. 瑙掕壊瀹氫箟妯″紡 鈥?鏉冮噸 5锛堥缂栬瘧锛?ROLE_PATTERNS_CN = [re.compile(p) for p in [
    r"浣犳槸涓€涓?, r"浣犳槸[涓€鍚嶇О浣峕",
    r"浣滀负[涓€涓€涓悕绉颁綅]", r"浣滀负涓€鍚?,
    r"鍋囪浣犳槸", r"鍋囪浣犳槸", r"浠庣幇鍦ㄥ紑濮嬩綘鏄?,
    r"浣犵殑瑙掕壊鏄?, r"浣犵殑韬唤鏄?,
    r"鎵紨", r"鍏呭綋", r"鎷呬换",
    r"浣犵幇鍦ㄦ槸", r"鎴戣浣犳壆婕?,
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

# 3. 缁撴瀯鍖栫壒寰?鈥?鏉冮噸 2-3锛堥缂栬瘧锛?STRUCTURE_PATTERNS_CN = [(re.compile(p), w) for p, w in [
    (r"(姝ラ|绗琜涓€浜屼笁鍥涗簲鍏竷鍏節鍗乗d]+姝?", 3),
    (r"(棣栧厛|鐒跺悗|鏈€鍚巪鎺ョ潃|鍏舵|鍐嶆)", 3),
    (r"(瑕佹眰|鏉′欢|瑙勫垯|闄愬埗|绾︽潫)", 2),
    (r"(鏍煎紡|鐢╩arkdown|鐢ㄨ〃鏍紎鐢ㄥ垪琛▅鐢ㄤ唬鐮亅鐢╦son|鐢▂aml)", 2),
    (r"(鍒哰鐐规]|鍒楀嚭|鍒椾妇|閫怺鏉￠」])", 2),
    (r"(璇?*[:锛歖)", 2),
    (r"(涓嶈|绂佹|閬垮厤|娉ㄦ剰|鍔″繀|蹇呴』)", 2),
    (r"(绀轰緥|渚嬪瓙|姣斿|渚嬪|鍙傝€?", 2),
]]

STRUCTURE_PATTERNS_EN = [(re.compile(p, re.IGNORECASE), w) for p, w in [
    (r"(step\s*\d|first|then|finally|next)", 3),
    (r"(requirements?|constraints?|rules?|limitations?)", 2),
    (r"(format|markdown|table|bullet\s*points?|json|yaml|code)", 2),
    (r"(please\s.*[:锛歖)", 2),
    (r"(do not|don't|avoid|make sure|ensure|must|should)", 2),
    (r"(example|e\.g\.|for instance|sample)", 2),
]]

# 4. 鎻愰棶妯″紡 鈥?鏉冮噸 2锛堥缂栬瘧锛?QUESTION_PATTERNS_CN = [re.compile(p) for p in [
    r"濡備綍", r"鎬庝箞", r"鎬庢牱", r"涓轰粈涔?,
    r"浠€涔堟槸", r"浠€涔堝彨", r"鏄粈涔堟剰鎬?,
    r"鍖哄埆.*鏄粈涔?, r".*鍜?*鐨勫尯鍒?,
    r"璇峰憡璇塠鎴戞垜浠琞",
    r"鏈夋病鏈?*鏂规硶", r"鏄惁",
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

# 5. 浠ｇ爜鐩稿叧 鈥?鏉冮噸 2锛堥缂栬瘧锛?CODE_PATTERNS_CN = [re.compile(p) for p in [
    r"(鍐欎唬鐮亅鍐欒剼鏈瑋鍐欑▼搴弢缂栫▼|鑴氭湰|浠ｇ爜)",
    r"(Python|Java|JavaScript|C\+\+|Go|Rust|TypeScript|SQL|HTML|CSS)",
    r"(瀹炵幇[涓€涓])", r"(鍑芥暟|鏂规硶|绫粅鎺ュ彛|妯″潡)",
    r"(鐢╘w+璇█)", r"(鐢╘w+瀹炵幇)",
]]

CODE_PATTERNS_EN = [re.compile(p, re.IGNORECASE) for p in [
    r"(write\s*(a\s*)?(code|script|program|function|class))",
    r"(implement\s*(a\s*)?(function|class|method|algorithm))",
    r"(in\s*(python|javascript|java|c\+\+|go|rust|typescript))",
    r"(code\s*(snippet|example|sample))",
]]

# 鍏朵粬棰勭紪璇戞鍒?_RE_PURE_URL = re.compile(r'^(https?://|ftp://|file://|www\.)[^\s]*$', re.IGNORECASE)
_RE_COLON_END = re.compile(r'[锛?]\s*$')
_RE_ROLE_TITLE = re.compile(r'(?:浣犳槸|浣犳槸涓€涓獆浣滀负涓€涓獆鎵紨|鍏呭綋|act as an?|you are an?)\s*(.+?)(?:[锛?銆?\n]|璇穦甯垜|$)', re.IGNORECASE)
_RE_ROLE_TASK = re.compile(r'(?:璇穦甯垜|甯繖)(.+?)(?:[銆?\n]|$)')
_RE_CN_ACTION = re.compile(r'(?:甯垜|璇峰府鎴憒璇蜂綘|璇穦甯繖)\s*(鍐檤鐢熸垚|缈昏瘧|鎬荤粨|鍒嗘瀽|瑙ｉ噴|淇敼|浼樺寲|淇|鍒涘缓|璁捐|寮€鍙憒瀹炵幇|鏁寸悊|瑙勫垝|鍒朵綔|璁＄畻|杞崲|姣旇緝|妫€鏌鎺ㄨ崘|鏁??\s*(.+?)(?:[銆?\n锛?]|$)')
_RE_EN_ACTION = re.compile(r'(write|generate|create|translate|summarize|explain|analyze|implement|fix|optimize|refactor|design|develop|build|convert|compare|review|check|teach|recommend)\s*(?:a|an|the|me|this|some)?\s*(.+?)(?:[\.\n]|$)', re.IGNORECASE)
_RE_QUESTION = re.compile(r'(濡備綍|鎬庝箞|鎬庢牱|浠€涔堟槸|涓轰粈涔坾鍖哄埆|how to|what is|why|how do|how can)\s*(.+?)(?:[锛?\n]|$)', re.IGNORECASE)
_RE_CLEAN_START = re.compile(r'^(閭ｄ釜|杩欎釜|鍡瘄棰潀灏辨槸璇磡鎴戞兂|楹荤儲|鑳戒笉鑳絴鍙笉鍙互)\s*')
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
    瀵规枃鏈唴瀹硅繘琛屽垎绫?
    Args:
        text: 瑕佸垎绫荤殑鏂囨湰

    Returns:
        (category, summary, subcategory) 鍏冪粍
        category: 'prompt' | 'other_text'
        summary: 绠€鐭憳瑕佹弿杩?        subcategory: 瀛愬垎绫?key锛堜粎 prompt 鏈夊€硷級
    """
    if not text or not text.strip():
        return "other_text", "", ""

    text = text.strip()
    text_lower = text.lower()

    # ---- 璐熷悜淇″彿妫€娴?----
    if _is_pure_url(text):
        return "other_text", _make_summary(text, is_url=True), ""

    if _is_pure_code(text):
        return "other_text", _make_summary(text), ""

    if _is_trivial(text):
        return "other_text", _make_summary(text), ""

    # ---- 姝ｅ悜淇″彿璇勫垎 ----
    score = 0.0

    # 1. 鎸囦护鎬у姩璇嶆娴?(涓婇檺 12 鍒?
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

    # 2. 瑙掕壊瀹氫箟妯″紡妫€娴?(涓婇檺 5 鍒嗭紝鍛戒腑鍗虫弧鍒?
    for pattern in ROLE_PATTERNS_CN:
        if pattern.search(text):
            score += 5
            break
    else:
        for pattern in ROLE_PATTERNS_EN:
            if pattern.search(text_lower):
                score += 5
                break

    # 3. 缁撴瀯鍖栫壒寰佹娴?(涓婇檺 6 鍒?
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

    # 4. 鎻愰棶妯″紡妫€娴?(涓婇檺 4 鍒?
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

    # 5. 浠ｇ爜鐩稿叧妫€娴?(涓婇檺 4 鍒?
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

    # 6. 闀垮害绯绘暟
    text_len = len(text)
    if text_len < 10:
        score *= 0.5
    elif text_len <= 200:
        score *= 1.0
    elif text_len <= 2000:
        score *= 0.8
    else:
        score *= 0.5

    # 7. 棰濆鍔犲垎锛氬琛岀粨鏋勫寲鏂囨湰
    line_count = text.count("\n") + 1
    if line_count >= 3 and score >= 3:
        score += 1  # 澶氳涓旀湁鎸囦护鎬э紝寰堝彲鑳芥槸 prompt

    # 8. 鍐掑彿缁撳熬鐨勬寚浠ゅ彞
    if _RE_COLON_END.search(text.strip()):
        score += 1

    # ---- 鍒嗙被鍒ゅ畾 ----
    if score >= 5:
        category = "prompt"
    else:
        category = "other_text"

    summary = _make_summary(text)

    # 瀛愬垎绫绘帹鏂紙浠?prompt锛?    subcategory = ""
    if category == "prompt":
        subcategory = _infer_prompt_subcategory(text)

    return category, summary, subcategory


def _infer_prompt_subcategory(text):
    """鎺ㄦ柇 prompt 鐨勫瓙鍒嗙被"""
    text_lower = text.lower()
    # 浠ｇ爜鐩稿叧
    if any(kw in text for kw in ["浠ｇ爜", "鍐欎竴涓?, "鍑芥暟", "鑴氭湰", "bug", "debug", "缂栫▼",
                                   "python", "javascript", "function", "code", "api"]):
        return "prompt_sub2"  # 榛樿瀛愬垎绫? 鈫?浠ｇ爜
    # 鍐欎綔鐩稿叧
    if any(kw in text for kw in ["鍐欎竴绡?, "鍐欎竴娈?, "鏂囩珷", "缈昏瘧", "鎬荤粨", "姒傛嫭", "鏀瑰啓",
                                   "translate", "summarize", "write", "article"]):
        return "prompt_sub3"  # 榛樿瀛愬垎绫? 鈫?鍐欎綔
    # 閫氱敤
    return "prompt_sub1"  # 榛樿瀛愬垎绫? 鈫?閫氱敤


def _is_pure_url(text):
    """妫€鏌ユ槸鍚︿负绾?URL"""
    return bool(_RE_PURE_URL.match(text.strip()))


def _is_pure_code(text):
    """妫€鏌ユ槸鍚︿负绾唬鐮侊紙鏃犺嚜鐒惰瑷€鎴愬垎锛?""
    stripped = text.strip()
    for pattern, _ in _RE_CODE_INDICATORS:
        if pattern.search(stripped):
            if len(_RE_SYMBOLS.findall(text)) > 3:
                return True

    # 绗﹀彿瀵嗗害杩囬珮
    symbols = len(_RE_SYMBOLS.findall(text))
    total_chars = len(text)
    if total_chars > 10 and symbols / total_chars > 0.15:
        return True

    return False


def _is_trivial(text):
    """妫€鏌ユ槸鍚︿负绠€鍗?鐞愮鏂囨湰"""
    text_stripped = text.strip()

    # 绾暟瀛?    if re.match(r'^[\d\s\-+.,]+$', text_stripped) and len(text_stripped) < 30:
        return True

    # 鍗曚釜鍗曡瘝
    if len(text_stripped.split()) == 1 and len(text_stripped) < 20:
        return True

    # 绾壒娈婂瓧绗?    if re.match(r'^[^\w\s]+$', text_stripped):
        return True

    return False


def _make_summary(text, is_url=False):
    """涓烘墍鏈夋枃鏈被鍨嬬敓鎴愭憳瑕?""
    if not text:
        return ""
    text = text.strip()

    if is_url:
        match = _RE_PURE_URL.search(text)
        if match:
            domain = match.group(0).replace("https://", "").replace("http://", "").replace("www.", "").split("/")[0]
            return f"閾炬帴: {domain}"
        return "閾炬帴"

    return _make_title(text)


def _make_title(text):
    """涓烘枃鏈敓鎴愮畝鐭爣棰橈紙10-30瀛楃锛夛紝鎻愮偧鏍稿績鎰忓浘"""
    if not text:
        return ""

    text = text.strip()
    first_line = text.split("\n")[0].strip()

    # ---- 妯″紡1: 瑙掕壊瀹氫箟 鈫?"瑙掕壊: 浠诲姟" ----
    role_match = _RE_ROLE_TITLE.search(text)
    if role_match:
        role = role_match.group(1).strip()
        task_match = _RE_ROLE_TASK.search(text)
        task = task_match.group(1).strip()[:12] if task_match else ""
        if task:
            return f"{_shorten(role, 10)}锛歿_shorten(task, 12)}"
        return _shorten(role, 22)

    # ---- 妯″紡2: "甯垜/璇?+ 鍔ㄨ瘝 + 瀹捐" ----
    action_match = _RE_CN_ACTION.search(text)
    if action_match:
        verb = action_match.group(1) or ""
        obj = action_match.group(2).strip()
        return _shorten(f"{verb}{obj}", 24)

    # ---- 妯″紡3: 鑻辨枃鎸囦护鍔ㄨ瘝 ----
    en_action = _RE_EN_ACTION.search(first_line)
    if en_action:
        verb = en_action.group(1).strip()
        obj = (en_action.group(2) or "").strip()
        result = f"{verb} {obj}".strip()
        return _shorten(result, 26)

    # ---- 妯″紡4: 闂绫?鈫?鎻愬彇涓婚 ----
    question = _RE_QUESTION.search(first_line)
    if question:
        topic = (question.group(2) or "").strip()
        qword = question.group(1).strip()
        return _shorten(f"{qword}{topic}", 22)

    # ---- 妯″紡5: 缁撴瀯鍖栭暱鏂囨湰 鈫?鍙栫涓€鍙ョ殑涓诲共 ----
    if len(text) > 60:
        cleaned = _RE_CLEAN_START.sub('', first_line)
        return _shorten(cleaned, 24)

    # ---- 閫氱敤: 娓呯悊鍚庡彇鍓?0瀛?----
    cleaned = re.sub(r'\s+', ' ', first_line).strip()
    return _shorten(cleaned, 22)


def _shorten(s, max_len):
    """鎴柇鏂囨湰锛岀‘淇濆湪 max_len 浠ュ唴"""
    if len(s) <= max_len:
        return s
    return s[:max_len-2] + "鈥?
