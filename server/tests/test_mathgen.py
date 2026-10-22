import os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from app import mathgen


def _valid(qs, count):
    assert qs is not None and len(qs) == count
    stems = set()
    for q in qs:
        assert q["question"] and q["answer"] and q["explanation"] and q["knowledge_point"]
        assert q["type"] in ("fill", "choice")
        assert q["question"] not in stems
        stems.add(q["question"])
        if q["type"] == "choice":
            assert len(q["options"]) == 4 and len({o[0] for o in q["options"]}) == 4
            assert q["answer"] in "ABCD"
            # 答案字母必须指向非空选项
            assert q["options"]["ABCD".index(q["answer"])][3:].strip() != ""
        else:
            assert q["options"] == []


def test_all_grades():
    for g in range(1, 7):
        _valid(mathgen.generate(g, 20), 20)


def test_topic_match():
    qs = mathgen.generate(3, 5, "两位数乘法")
    _valid(qs, 5)
    assert all(q["knowledge_point"] == "两位数乘法" for q in qs)
    qs = mathgen.generate(2, 5, "表内乘法")
    assert all(q["knowledge_point"] == "表内乘法" for q in qs)


def test_topic_no_match_falls_back():
    assert mathgen.generate(1, 5, "鸡兔同笼") is None
    assert mathgen.generate(4, 5, "微积分") is None


def test_invalid_grade():
    assert mathgen.generate(0, 5) is None
    assert mathgen.generate(7, 5) is None


def test_golden_samples():
    # 答案必须精确正确：用正则从题干反解出题参数再独立验算
    import random
    import re
    from app.mathgen import _frac, _fmt
    assert _frac(4, 6) == "2/3" and _frac(4, 2) == "2" and _frac(0, 5) == "0"
    assert _fmt(2.50) == "2.5" and _fmt(3.14) == "3.14"
    rng = random.Random(7)
    for _ in range(50):
        q = mathgen._g1_add(rng)
        m = re.fullmatch(r"(\d+) \+ (\d+) = ___", q["question"])
        assert m and int(q["answer"]) == int(m.group(1)) + int(m.group(2))
    for _ in range(50):
        q = mathgen._g2_mult(rng)
        m = re.fullmatch(r"(\d+) × (\d+) = ___", q["question"])
        assert m and int(q["answer"]) == int(m.group(1)) * int(m.group(2))
    for _ in range(50):
        q = mathgen._g5_equation(rng)
        m = re.fullmatch(r"x \+ (\d+) = (\d+)，x = ___", q["question"])
        if m:
            assert int(q["answer"]) == int(m.group(2)) - int(m.group(1))
