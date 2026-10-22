"""小学数学出题生成器（1-6 年级）。

设计原则：
- 全部题目由程序按年级大纲生成，答案直接由出题参数算出，保证正确；
- 讲解写清分步思路，语言贴合小学生；
- 返回结构与题库/AI 出题完全一致：{question, type, options, answer, explanation, knowledge_point}；
- 选择题 options 固定为 "A. xx" 格式，answer 为选项字母（小程序按首字母取值）。

generate(grade, count, topic) -> list[dict] | None
  topic 为空或能匹配到某类知识点时返回题目列表；
  topic 指定了但没有任何一类知识点匹配时返回 None，调用方回退到题库/AI。
"""
import math
import random

FILL, CHOICE = "fill", "choice"
LETTERS = ["A", "B", "C", "D"]


def _fmt(x):
    """小数格式化：去掉浮点噪音和多余的 0。"""
    if isinstance(x, float):
        x = round(x, 3)
        s = f"{x:.3f}".rstrip("0").rstrip(".")
        return s if s else "0"
    return str(x)


def _frac(n, d):
    """约分后以 a/b 形式返回；能整除时直接返回整数；d>0。"""
    if n % d == 0:
        return str(n // d)
    g = math.gcd(n, d)
    return f"{n // g}/{d // g}"


def _choice_q(stem, answer_text, distract_texts, explanation, kp):
    """组装选择题：answer 存字母，options 为 'A. xx' 形式。"""
    cands, seen = [], {answer_text}
    for t in distract_texts:
        if t not in seen:
            seen.add(t)
            cands.append(t)
        if len(cands) == 3:
            break
    # 兜底：干扰项不够时用答案±1/±2 补齐
    k = 1
    try:
        base = float(answer_text)
        while len(cands) < 3:
            for delta in (k, -k, k + 0.5, -k - 0.5):
                v = _fmt(base + delta)
                if v not in seen:
                    seen.add(v)
                    cands.append(v)
                    break
            k += 1
    except ValueError:
        while len(cands) < 3:
            v = f"{answer_text}({k})"
            if v not in seen:
                seen.add(v)
                cands.append(v)
            k += 1
    opts = [answer_text] + cands[:3]
    rng = random.Random(hash(stem) & 0xFFFFFFFF)
    rng.shuffle(opts)
    letter = LETTERS[opts.index(answer_text)]
    return {"question": stem, "type": CHOICE,
            "options": [f"{L}. {o}" for L, o in zip(LETTERS, opts)],
            "answer": letter, "explanation": explanation, "knowledge_point": kp}


def _fill_q(stem, answer, explanation, kp):
    return {"question": stem, "type": FILL, "options": [],
            "answer": _fmt(answer), "explanation": explanation, "knowledge_point": kp}


# ---------------- 一年级：20以内加减 ----------------
def _g1_add(r):
    a, b = r.randint(1, 9), r.randint(1, 9)
    if a + b > 20:
        b = r.randint(1, 20 - a)
    return _fill_q(f"{a} + {b} = ___", a + b,
                   f"先算 {a}+{b}，{'个位相加' if a + b < 10 else '满十进一'}，答案是 {a + b}。", "20以内加减法")


def _g1_sub(r):
    a = r.randint(5, 20)
    b = r.randint(1, a)
    return _fill_q(f"{a} - {b} = ___", a - b,
                   f"{a} 减去 {b}，数一数还剩多少，答案是 {a - b}。", "20以内加减法")


def _g1_carry(r):
    a = r.choice([x for x in range(11, 30) if x % 10])  # 个位不能为 0，否则 randint 越界
    b = r.randint(10 - (a % 10), 9)  # 保证进位
    c, d = a % 10, b
    return _fill_q(f"{a} + {b} = ___", a + b,
                   f"先算个位 {c}+{d}={c + d}，写 {c + d - 10} 进 1；"
                   f"再算十位 {a // 10}+1={a // 10 + 1}；答案是 {a + b}。", "进位加法")


def _g1_borrow(r):
    a = r.choice([x for x in range(21, 40) if x % 10 != 9])  # 个位为 9 时无法退位
    b = r.randint((a % 10) + 1, 9)  # 保证退位
    return _fill_q(f"{a} - {b} = ___", a - b,
                   f"个位 {a % 10} 不够减 {b}，向十位借 1 当 10，"
                   f"{a % 10 + 10}-{b}={a % 10 + 10 - b}，十位少了 1 还剩 {a // 10 - 1}；"
                   f"答案是 {a - b}。", "退位减法")


def _g1_compare(r):
    a, b = r.randint(1, 20), r.randint(1, 20)
    if a == b:
        b = b + 1 if b < 20 else b - 1
    ans = ">" if a > b else "<"
    return _fill_q(f"{a} ○ {b}（填 >、< 或 =）", ans,
                   f"{a} 和 {b} 比大小，{a} 更{'大' if a > b else '小'}，所以填 {ans}。", "数的大小比较")


def _g1_word(r):
    a = r.randint(3, 12)
    b = r.randint(2, 9)
    thing = r.choice(["颗糖", "个苹果", "支铅笔", "本书"])
    if r.random() < 0.5:
        return _fill_q(f"小明有 {a}{thing}，妈妈又给了他 {b}{thing}，现在一共有 ___{thing}。", a + b,
                       f"原来 {a}{thing}，又多了 {b}{thing}，{a}+{b}={a + b}。", "加减法应用题")
    b = min(b, a - 1)
    return _fill_q(f"盘子里有 {a}{thing}，小明吃了 {b}{thing}，还剩 ___{thing}。", a - b,
                   f"原来 {a}{thing}，吃掉 {b}{thing}，{a}-{b}={a - b}。", "加减法应用题")


# ---------------- 二年级：100以内加减、表内乘除 ----------------
def _g2_add100(r):
    a = r.randint(25, 85)
    b = r.randint(11, 99 - a)  # 和不超过 99
    return _fill_q(f"{a} + {b} = ___", a + b,
                   f"个位 {a % 10}+{b % 10}={a % 10 + b % 10}"
                   f"{'，写 ' + str((a % 10 + b % 10) % 10) + ' 进 1' if a % 10 + b % 10 >= 10 else ''}；"
                   f"十位相加{'再加进位的 1' if a % 10 + b % 10 >= 10 else ''}；答案是 {a + b}。", "100以内加减法")


def _g2_sub100(r):
    a = r.randint(40, 99)
    b = r.randint(15, a - 5)
    need = (a % 10) < (b % 10)
    return _fill_q(f"{a} - {b} = ___", a - b,
                   f"{'个位不够减，向十位借 1 当 10 再减；' if need else '个位够减，直接减；'}"
                   f"答案是 {a - b}。", "100以内加减法")


def _g2_mult(r):
    a, b = r.randint(2, 9), r.randint(2, 9)
    return _fill_q(f"{a} × {b} = ___", a * b,
                   f"想乘法口诀：{a}×{b}={a * b}。", "表内乘法")


def _g2_div(r):
    b = r.randint(2, 9)
    c = r.randint(2, 9)
    a = b * c
    return _fill_q(f"{a} ÷ {b} = ___", c,
                   f"想口诀：{b}×{c}={a}，所以 {a}÷{b}={c}。", "表内除法")


def _g2_mult_choice(r):
    a, b = r.randint(3, 9), r.randint(3, 9)
    ans = a * b
    return _choice_q(f"{a} × {b} = ？", str(ans),
                     [str(ans + a), str(ans - b), str(ans + 10)],
                     f"口诀：{a}×{b}={ans}。", "表内乘法")


def _g2_word(r):
    if r.random() < 0.5:
        a, b = r.randint(2, 5), r.randint(3, 9)
        return _fill_q(f"教室里每排坐 {a} 人，一共 {b} 排，一共有 ___ 人。", a * b,
                       f"每排 {a} 人，{b} 排就是 {b} 个 {a}，{a}×{b}={a * b}。", "乘除法应用题")
    b = r.randint(2, 9)
    c = r.randint(2, 6)
    a = b * c
    return _fill_q(f"{a} 块饼干，平均分给 {b} 个小朋友，每人分 ___ 块。", c,
                   f"{a}÷{b}，想口诀 {b}×{c}={a}，每人 {c} 块。", "乘除法应用题")


# ---------------- 三年级：万以内、两位数乘法、分数初步 ----------------
def _g3_addw(r):
    a = r.randint(234, 9876)
    b = r.randint(123, 9876)
    return _fill_q(f"{a} + {b} = ___", a + b,
                   f"相同数位对齐，从个位算起，注意进位；答案是 {a + b}。", "万以内加减法")


def _g3_subw(r):
    a = r.randint(1000, 9999)
    b = r.randint(234, a - 100)
    return _fill_q(f"{a} - {b} = ___", a - b,
                   f"相同数位对齐从个位减起，不够减就向前一位借 1；答案是 {a - b}。", "万以内加减法")


def _g3_mult2(r):
    a = r.randint(12, 98)
    b = r.randint(3, 9)
    return _fill_q(f"{a} × {b} = ___", a * b,
                   f"先算 {a}×{b}：{a % 10}×{b}={a % 10 * b}，{a // 10 * 10}×{b}={a // 10 * 10 * b}，"
                   f"加起来是 {a * b}。", "两位数乘法")


def _g3_div(r):
    b = r.randint(3, 9)
    c = r.randint(12, 99)
    a = b * c
    if r.random() < 0.4:  # 有余数的除法
        a += r.randint(1, b - 1)
        return _fill_q(f"{a} ÷ {b} = ___（填：商余余数，如 6余4）", f"{c}余{a - b * c}",
                       f"想 {b} 的口诀，{b}×{c}={b * c} 最接近 {a} 且不超过，"
                       f"余 {a - b * c}；答案是 {c}余{a - b * c}。", "有余数的除法")
    return _fill_q(f"{a} ÷ {b} = ___", c,
                   f"{b}×{c}={a}，所以 {a}÷{b}={c}。", "除法")


def _g3_frac(r):
    d = r.choice([4, 5, 6, 7, 8])
    a = r.randint(1, d - 2)
    b = r.randint(1, d - a - 1) or 1
    if a + b >= d:
        b = d - a - 1 or 1
    if r.random() < 0.5:
        return _fill_q(f"{a}/{d} + {b}/{d} = ___（填分数，如 5/7）", _frac(a + b, d),
                       f"分母不变，分子相加：{a}+{b}={a + b}，答案是 {_frac(a + b, d)}。", "分数初步")
    b = min(b, a - 1) or 1
    if b >= a:
        a, b = b + 1, b
    return _fill_q(f"{a}/{d} - {b}/{d} = ___（填分数）", _frac(a - b, d),
                   f"分母不变，分子相减：{a}-{b}={a - b}，答案是 {_frac(a - b, d)}。", "分数初步")


def _g3_word(r):
    a = r.randint(12, 60)
    b = r.randint(3, 9)
    price = r.randint(2, 15)
    return _fill_q(f"文具店一支笔 {price} 元，小红买了 {b} 支，又买了一本 {a} 元的本子，一共花了 ___ 元。", price * b + a,
                   f"先算笔：{price}×{b}={price * b} 元；再加本子 {a} 元；"
                   f"一共 {price * b}+{a}={price * b + a} 元。", "两步应用题")


# ---------------- 四年级：大数、四则混合、小数 ----------------
def _g4_mixed(r):
    kind = r.randint(0, 2)
    if kind == 0:
        a, b, c = r.randint(10, 99), r.randint(2, 9), r.randint(10, 99)
        ans = a + b * c
        return _fill_q(f"{a} + {b} × {c} = ___", ans,
                       f"先算乘法 {b}×{c}={b * c}，再算加法 {a}+{b * c}={ans}。", "四则混合运算")
    if kind == 1:
        b, c = r.randint(2, 9), r.randint(2, 9)
        a = b * c + r.randint(5, 30)
        ans = a - b * c
        return _fill_q(f"{a} - {b} × {c} = ___", ans,
                       f"先算乘法 {b}×{c}={b * c}，再算减法 {a}-{b * c}={ans}。", "四则混合运算")
    a = r.randint(20, 80)
    b, c = r.randint(2, 9), r.randint(2, 9)
    ans = (a + b) * c
    return _fill_q(f"({a} + {b}) × {c} = ___", ans,
                   f"有括号先算括号：{a}+{b}={a + b}，再算 {a + b}×{c}={ans}。", "四则混合运算")


def _g4_decimal(r):
    a = round(r.randint(10, 99) / 10, 1)
    b = round(r.randint(10, 99) / 10, 1)
    if r.random() < 0.5:
        ans = round(a + b, 1)
        return _fill_q(f"{_fmt(a)} + {_fmt(b)} = ___", _fmt(ans),
                       f"小数点对齐再相加：{_fmt(a)}+{_fmt(b)}={_fmt(ans)}。", "小数加减法")
    if a < b:
        a, b = b, a
    ans = round(a - b, 1)
    return _fill_q(f"{_fmt(a)} - {_fmt(b)} = ___", _fmt(ans),
                   f"小数点对齐再相减：{_fmt(a)}-{_fmt(b)}={_fmt(ans)}。", "小数加减法")


def _g4_bigmult(r):
    a = r.randint(123, 987)
    b = r.randint(12, 98)
    return _fill_q(f"{a} × {b} = ___", a * b,
                   f"列竖式：先算 {a}×{b % 10}={a * (b % 10)}，再算 {a}×{b // 10 * 10}={a * (b // 10 * 10)}，"
                   f"相加得 {a * b}。", "三位数乘除法")


def _g4_mixed_choice(r):
    a, b, c = r.randint(6, 20), r.randint(2, 6), r.randint(6, 20)
    ans = a * b + c
    return _choice_q(f"{a} × {b} + {c} = ？", str(ans),
                     [str(a * (b + c)), str(ans + b), str(ans - 10)],
                     f"先乘后加：{a}×{b}={a * b}，{a * b}+{c}={ans}。", "四则混合运算")


def _g4_word(r):
    v = r.randint(40, 70)
    t = r.randint(2, 5)
    return _fill_q(f"一辆汽车每小时行 {v} 千米，{t} 小时一共行了 ___ 千米。", v * t,
                   f"速度×时间=路程：{v}×{t}={v * t} 千米。", "行程应用题")


# ---------------- 五年级：小数乘除、分数、方程 ----------------
def _g5_decmult(r):
    at = r.randint(12, 95)  # 代表 at/10，用整数避免浮点误差
    b = r.randint(2, 9)
    prod = at * b
    a_s = f"{at // 10}.{at % 10}"
    return _fill_q(f"{a_s} × {b} = ___", _fmt(prod / 10),
                   f"先不看小数点算 {at}×{b}={prod}，因数里有一位小数，"
                   f"积也点一位小数：{_fmt(prod / 10)}。", "小数乘除法")


def _g5_decdiv(r):
    b = r.randint(2, 9)
    c = round(r.randint(11, 99) / 10, 1)
    a = round(b * c, 1)
    return _fill_q(f"{_fmt(a)} ÷ {b} = ___", _fmt(c),
                   f"{b}×{_fmt(c)}={_fmt(a)}，所以 {_fmt(a)}÷{b}={_fmt(c)}。", "小数乘除法")


def _g5_fracadd(r):
    pairs = [(2, 3), (2, 4), (3, 4), (2, 5), (3, 5), (4, 5), (2, 6), (3, 6), (5, 6)]
    for _ in range(30):  # 重试，保证减法被减数大、加法尽量是真分数
        d1, d2 = r.choice(pairs)
        a = r.randint(1, d1 - 1)
        b = r.randint(1, d2 - 1)
        lcm = d1 * d2 // math.gcd(d1, d2)
        n1, n2 = a * (lcm // d1), b * (lcm // d2)
        if r.random() < 0.5:
            if n1 + n2 >= lcm:
                continue
            return _fill_q(f"{a}/{d1} + {b}/{d2} = ___（填最简分数）", _frac(n1 + n2, lcm),
                           f"先通分：{a}/{d1}={n1}/{lcm}，{b}/{d2}={n2}/{lcm}；"
                           f"相加得 {_frac(n1 + n2, lcm)}。", "分数加减法")
        if n1 <= n2:
            continue
        return _fill_q(f"{a}/{d1} - {b}/{d2} = ___（填最简分数）", _frac(n1 - n2, lcm),
                       f"先通分：{a}/{d1}={n1}/{lcm}，{b}/{d2}={n2}/{lcm}；"
                       f"相减得 {_frac(n1 - n2, lcm)}。", "分数加减法")
    # 兜底：同分母
    d = 7
    return _fill_q(f"3/{d} + 2/{d} = ___（填最简分数）", _frac(5, d),
                   f"分母不变，分子相加：3+2=5，答案是 {_frac(5, d)}。", "分数加减法")


def _g5_equation(r):
    b = r.randint(3, 20)
    x = r.randint(2, 30)
    a = x + b
    kind = r.randint(0, 2)
    if kind == 0:
        return _fill_q(f"x + {b} = {a}，x = ___", x,
                       f"想：几加 {b} 等于 {a}？{a}-{b}={x}，所以 x={x}。", "简易方程")
    if kind == 1:
        a2 = x - b
        return _fill_q(f"x - {b} = {a2}，x = ___", x,
                       f"被减数 = 差 + 减数：{a2}+{b}={x}，所以 x={x}。", "简易方程")
    m = r.randint(2, 9)
    prod = m * x
    return _fill_q(f"{m}x = {prod}，x = ___", x,
                   f"{m} 乘几等于 {prod}？{prod}÷{m}={x}，所以 x={x}。", "简易方程")


def _g5_factor_choice(r):
    n = r.choice([12, 16, 18, 20, 24, 30])
    facs = [i for i in range(1, n + 1) if n % i == 0]
    ans = len(facs)
    return _choice_q(f"{n} 的因数一共有几个？", str(ans),
                     [str(ans + 1), str(ans - 1), str(ans + 2)],
                     f"{n} 的因数有：{facs}，共 {ans} 个。", "因数与倍数")


def _g5_word(r):
    total = r.randint(30, 100)
    eat = r.choice([2, 3, 4, 5])
    per = total // eat
    total = per * eat
    return _fill_q(f"一袋大米 {total} 千克，吃了它的 1/{eat}，吃了 ___ 千克。", per,
                   f"{total}÷{eat}={per} 千克。", "分数应用题")


# ---------------- 六年级：分数乘除、百分数、比、圆 ----------------
def _g6_fracmult(r):
    a, b = r.randint(1, 8), r.randint(2, 9)
    c, d = r.randint(1, 8), r.randint(2, 9)
    return _fill_q(f"{a}/{b} × {c}/{d} = ___（填最简分数）", _frac(a * c, b * d),
                   f"分子乘分子，分母乘分母：{a * c}/{b * d}，约分得 {_frac(a * c, b * d)}。", "分数乘除法")


def _g6_fracdiv(r):
    a, b = r.randint(1, 6), r.randint(2, 8)
    c = r.randint(2, 9)
    # (a/b) ÷ c
    return _fill_q(f"{a}/{b} ÷ {c} = ___（填最简分数）", _frac(a, b * c),
                   f"除以一个数等于乘它的倒数：{a}/{b}×1/{c}={_frac(a, b * c)}。", "分数乘除法")


def _g6_percent(r):
    kind = r.randint(0, 2)
    if kind == 0:
        p = r.choice([10, 20, 25, 50, 75])
        return _fill_q(f"{p}% = ___（填最简分数）", _frac(p, 100),
                       f"{p}% 就是 {p}/100，约分得 {_frac(p, 100)}。", "百分数")
    if kind == 1:
        base = r.choice([40, 50, 80, 100, 200])
        p = r.choice([10, 20, 25, 50])
        ans = base * p // 100
        return _fill_q(f"{base} 的 {p}% 是 ___", ans,
                       f"{base}×{p}%={base}×{p}/100={ans}。", "百分数")
    orig = r.choice([50, 80, 100, 120, 200])
    off = r.choice([20, 25, 30, 50])
    sale = 100 - off  # 实际按百分之几算
    ans = orig * sale // 100
    return _fill_q(f"一件原价 {orig} 元的衣服打 {sale // 10} 折，现价是 ___ 元。", ans,
                   f"打 {sale // 10} 折就是按原价的 {sale}% 算：{orig}×{sale}%={ans} 元。", "百分数应用题")


def _g6_ratio(r):
    a = r.randint(2, 9)
    b = r.randint(2, 9)
    g = math.gcd(a, b)  # 先约成最简比，避免答案本身还能约分
    a, b = a // g, b // g
    k = r.randint(2, 5)
    A, B = a * k, b * k
    if r.random() < 0.5:
        return _fill_q(f"化简比：{A}:{B} = ___（填最简整数比，如 2:3）", f"{a}:{b}",
                       f"{A} 和 {B} 同时除以 {k}，得 {a}:{b}。", "比和比例")
    return _fill_q(f"{a}:{b} 的前项是 ___", a,
                   f"比号前面的数叫前项，{a}:{b} 的前项是 {a}。", "比和比例")


def _g6_circle(r):
    rad = r.randint(2, 10)
    if r.random() < 0.5:
        ans = _fmt(2 * 3.14 * rad)
        return _fill_q(f"一个圆的半径是 {rad} 厘米，它的周长是 ___ 厘米（π 取 3.14）。", ans,
                       f"周长 = 2πr = 2×3.14×{rad}={ans} 厘米。", "圆")
    ans = _fmt(3.14 * rad * rad)
    return _fill_q(f"一个圆的半径是 {rad} 厘米，它的面积是 ___ 平方厘米（π 取 3.14）。", ans,
                   f"面积 = πr² = 3.14×{rad}×{rad}={ans} 平方厘米。", "圆")


def _g6_word(r):
    total = r.choice([200, 240, 300, 400, 500])
    p = r.choice([10, 20, 25, 30, 40])
    done = total * p // 100
    return _fill_q(f"修路队要修 {total} 米的路，已经修了 {p}%，还剩 ___ 米没修。", total - done,
                   f"已修 {total}×{p}%={done} 米；还剩 {total}-{done}={total - done} 米。", "百分数应用题")


# ---------------- 题库组织 ----------------
POOLS = {
    1: [("20以内加减法", 3, _g1_add), ("20以内加减法", 3, _g1_sub), ("进位加法", 2, _g1_carry),
        ("退位减法", 2, _g1_borrow), ("数的大小比较", 1, _g1_compare), ("加减法应用题", 2, _g1_word)],
    2: [("100以内加减法", 3, _g2_add100), ("100以内加减法", 3, _g2_sub100), ("表内乘法", 3, _g2_mult),
        ("表内除法", 2, _g2_div), ("表内乘法", 1, _g2_mult_choice), ("乘除法应用题", 2, _g2_word)],
    3: [("万以内加减法", 2, _g3_addw), ("万以内加减法", 2, _g3_subw), ("两位数乘法", 3, _g3_mult2),
        ("除法", 2, _g3_div), ("有余数的除法", 1, _g3_div), ("分数初步", 2, _g3_frac),
        ("两步应用题", 2, _g3_word)],
    4: [("四则混合运算", 4, _g4_mixed), ("小数加减法", 3, _g4_decimal), ("三位数乘除法", 2, _g4_bigmult),
        ("四则混合运算", 1, _g4_mixed_choice), ("行程应用题", 2, _g4_word)],
    5: [("小数乘除法", 3, _g5_decmult), ("小数乘除法", 3, _g5_decdiv), ("分数加减法", 3, _g5_fracadd),
        ("简易方程", 3, _g5_equation), ("因数与倍数", 1, _g5_factor_choice), ("分数应用题", 2, _g5_word)],
    6: [("分数乘除法", 3, _g6_fracmult), ("分数乘除法", 3, _g6_fracdiv), ("百分数", 2, _g6_percent),
        ("比和比例", 2, _g6_ratio), ("圆", 2, _g6_circle), ("百分数应用题", 2, _g6_word)],
}


def _match(topic, kp):
    t = (topic or "").strip()
    if not t:
        return True
    return t in kp or kp in t or any(k in kp for k in t.replace("，", ",").split(",") if k)


def generate(grade, count=5, topic=""):
    """生成 count 道题。topic 匹配不到任何知识点时返回 None（调用方回退题库/AI）。"""
    grade = int(grade)
    pools = POOLS.get(grade)
    if not pools:
        return None
    if topic and not any(_match(topic, kp) for kp, _, _ in pools):
        return None
    cands = [(kp, w, fn) for kp, w, fn in pools if _match(topic, kp)]
    total_w = sum(w for _, w, _ in cands)
    out, seen, rng = [], set(), random.Random()
    guard = 0
    while len(out) < count and guard < count * 40:
        guard += 1
        pick = rng.uniform(0, total_w)
        acc = 0
        for kp, w, fn in cands:
            acc += w
            if pick <= acc:
                try:
                    q = fn(rng)
                except Exception:
                    break
                if q["question"] not in seen:
                    seen.add(q["question"])
                    out.append(q)
                break
    return out


if __name__ == "__main__":
    # 自检：每个年级各生成 300 道，校验结构与基本正确性
    for g in range(1, 7):
        qs = generate(g, 300)
        assert qs and len(qs) == 300, f"grade {g}: 生成数量不足"
        assert len({q["question"] for q in qs}) == 300, f"grade {g}: 有重复题"
        for q in qs:
            assert q["question"] and q["answer"] and q["explanation"] and q["knowledge_point"]
            assert q["type"] in ("fill", "choice")
            if q["type"] == "choice":
                assert len(q["options"]) == 4 and q["answer"] in "ABCD"
                assert q["options"]["ABCD".index(q["answer"])][3:] != ""
                assert len({o[0] for o in q["options"]}) == 4
            else:
                assert q["options"] == []
        print(f"grade {g}: OK ({len(qs)} 题)")
    print("自检通过")
