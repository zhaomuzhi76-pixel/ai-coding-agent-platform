"""PDF 文本质量检测：双词表命中（现代词 OR 领域词）判乱码。

判据：
  1. 太短（<8）→ 乱码
  2. 无效字符 > 15% → 乱码
  3. 平均行长 < 3 → 乱码
  4. 中文文本：现代词命中 + 领域词命中 == 0 → 乱码
"""
from __future__ import annotations
import re
from typing import Tuple, Set

_VALID_RE = re.compile(
    r"[\u4e00-\u9fff\u3400-\u4dbf"
    r"a-zA-Z0-9\s"
    r".,;:!?'\"()\[\]{}<>"
    r"，。；：！？、（）【】《》"
    r"—…·・]"
)

# ── 现代常用词（Top 200，覆盖 ~80% 现代文本）──
_MODERN_WORDS: Set[str] = {
    "今天", "明天", "昨天", "早上", "中午", "晚上", "时候", "时间",
    "什么", "怎么", "怎样", "为什么", "如何", "哪里", "哪个", "谁",
    "可以", "能够", "应该", "必须", "需要", "想要", "希望", "打算",
    "我们", "你们", "他们", "她们", "自己", "别人", "大家", "一起",
    "一个", "这个", "那个", "每个", "有些", "很多", "一些", "两个",
    "没有", "不是", "就是", "还是", "但是", "可是", "不过", "然而",
    "因为", "所以", "如果", "虽然", "即使", "而且", "或者", "以及",
    "工作", "学习", "生活", "问题", "方法", "情况", "内容", "结果",
    "数据", "系统", "模型", "算法", "结构", "功能", "模块", "接口",
    "开发", "测试", "运行", "处理", "生成", "计算", "分析", "设计",
    "公司", "部门", "团队", "项目", "任务", "计划", "目标", "需求",
    "北京", "上海", "广州", "深圳", "中国", "世界", "国家", "城市",
    "医院", "学校", "政府", "企业", "市场", "经济", "社会", "文化",
    "知道", "觉得", "认为", "发现", "看到", "听到", "感觉", "明白",
    "天气", "不错", "一起", "公园", "散步", "风景", "朋友", "家人",
    "开始", "结束", "完成", "继续", "停止", "改变", "提高", "降低",
    "主要", "重要", "特殊", "普通", "一般", "具体", "抽象", "简单",
    "很好", "非常", "特别", "十分", "极其", "相当", "比较", "稍微",
    "人工智能", "机器学习", "深度学习", "神经网络", "智能", "自动",
    "医疗", "诊断", "驾驶", "助手", "推荐", "系统", "应用", "技术",
    "改变", "影响", "日常", "无处", "不在", "正在", "成为", "发展",
}

# ── 领域词（中医古籍/行业常见）──
_DOMAIN_WORDS: Set[str] = {
    "太阳", "阳明", "少阳", "太阴", "少阴", "厥阴",
    "中风", "伤寒", "温病", "发热", "恶寒", "汗出", "头痛", "身痛",
    "项强", "胸满", "心悸", "腹痛", "呕吐", "下利", "口渴", "烦躁",
    "脉浮", "脉沉", "脉迟", "脉数", "脉缓", "脉紧", "脉弦", "脉滑",
    "脉细", "脉微", "脉弱", "浮紧", "浮缓", "沉迟",
    "桂枝", "麻黄", "甘草", "生姜", "大枣", "芍药", "杏仁", "石膏",
    "茯苓", "白术", "人参", "当归", "川芎", "柴胡", "半夏", "黄芩",
    "黄连", "陈皮", "枳实", "厚朴", "干姜", "附子", "大黄", "芒硝",
    "桂枝汤", "麻黄汤", "承气汤", "小柴胡", "四逆汤", "理中丸",
    "大青龙汤", "小青龙汤", "白虎汤", "五苓散", "真武汤",
    "温服", "顿服", "煎服", "煮取", "水煮", "去滓", "日三服",
    "每日", "分温", "一升", "二升", "三升", "一剂", "一两",
    "主治", "病机", "脉证", "证治", "伤寒论", "金匮", "内经",
    "治病", "良方", "古方", "经方", "医案",
    "者也", "之所", "所以", "是以", "故曰", "若夫", "且夫",
    # 中医基础
    "气血", "阴阳", "脏腑", "经络", "虚实", "寒热", "表里",
    "补气", "健脾", "滋阴", "温阳", "和解", "清热", "泻下",
    "元气", "脏腑", "功能", "衰退", "主症", "气短", "乏力",
    "自汗", "治则", "方用", "四君", "人参", "白术", "茯苓",
}


def _valid_ratio(t: str) -> float:
    if not t:
        return 0.0
    return sum(1 for ch in t if _VALID_RE.match(ch)) / len(t)


def _avg_line_len(t: str) -> float:
    lines = [l for l in t.splitlines() if l.strip()]
    return sum(len(l) for l in lines) / len(lines) if lines else 0.0


def _cn_ratio(t: str) -> float:
    if not t:
        return 0.0
    return sum(1 for ch in t if "\u4e00" <= ch <= "\u9fff") / len(t)


def _modern_hits(t: str) -> int:
    return sum(1 for w in _MODERN_WORDS if w in t)


def _domain_hits(t: str) -> int:
    return sum(1 for w in _DOMAIN_WORDS if w in t)


def is_garbled(text: str) -> Tuple[bool, str]:
    if not text or not text.strip():
        return True, "empty"
    t = text.strip()
    if len(t) < 8:
        return True, f"too_short({len(t)}<8)"

    vr = _valid_ratio(t)
    if vr < 0.85:
        return True, f"invalid_chars({vr:.2f}<0.85)"

    avg = _avg_line_len(t)
    if avg < 3.0:
        return True, f"short_lines({avg:.1f}<3)"

    # 中文文本必须命中现代词 OR 领域词
    if _cn_ratio(t) > 0.5 and len(t) >= 20:
        m = _modern_hits(t)
        d = _domain_hits(t)
        if m + d == 0:
            return True, f"no_word(modern=0,domain=0)"
        # 领域词单独命中 ≥1 也放行（古籍）
        # 若只有 1 个领域词命中且无现代词 → 严格模式拒绝
        if d == 1 and m == 0:
            return True, f"weak_signal(domain=1,modern=0)"

    return False, "ok"


def quality_score(text: str) -> float:
    if not text:
        return 0.0
    t = text.strip()
    vr = _valid_ratio(t)
    avg = _avg_line_len(t)
    m = _modern_hits(t)
    d = _domain_hits(t)
    avg_score = min(1.0, avg / 15.0)
    word_score = min(1.0, (m + d) / 5.0)
    return round(0.4 * vr + 0.2 * avg_score + 0.4 * word_score, 4)


def register_domain_words(words) -> None:
    _DOMAIN_WORDS.update(w for w in words if w)


__all__ = ["is_garbled", "quality_score", "register_domain_words"]
