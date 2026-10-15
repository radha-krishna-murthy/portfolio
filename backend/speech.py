"""
Turn an answer into plain spoken words before text-to-speech.

The avatar's lip-sync builds mouth shapes from the same words the voice speaks.
If the text says "73,000" or "FAISS", the voice and the lip-sync read it differently
and the mouth drifts out of step. Spelling everything out keeps them identical.
"""

import re

# How each term is actually said. Letters separated by spaces are spelled out.
PRONOUNCE = {
    "FAISS": "face", "RAG": "rag", "BM25": "B M twenty five", "LLaMA-3": "llama three",
    "LLaMA": "llama", "SRMIST": "S R M I S T", "SRM": "S R M", "RGUKT": "R G U K T",
    "CGPA": "C G P A", "GPA": "G P A", "JWT": "J W T", "API": "A P I", "APIs": "A P I's",
    "REST": "rest", "LLM": "L L M", "LLMs": "L L Ms", "AI": "A I", "SQL": "sequel",
    "MySQL": "my sequel", "MongoDB": "mongo D B", "PDF": "P D F", "PDFs": "P D Fs",
    "HTML": "H T M L", "CSS": "C S S", "CSE": "C S E", "B.Tech": "B tech", "UI": "U I",
    "R&D": "R and D", "PRISM": "prism", "TTS": "T T S", "3D": "three D", "GitHub": "git hub",
    "LeetCode": "leet code", "LangChain": "lang chain", "HuggingFace": "hugging face",
    "RabbitMQ": "rabbit M Q", "Q&A": "Q and A", "e.g.": "for example", "i.e.": "that is",
    "vs": "versus", "ms": "milliseconds", "&": "and", "%": " percent", "~": "about ",
    "+": " plus", "XII": "twelve",
    "trkm212@gmail.com": "T R K M two one two at gmail dot com",
}

ONES = ["zero", "one", "two", "three", "four", "five", "six", "seven", "eight", "nine", "ten",
        "eleven", "twelve", "thirteen", "fourteen", "fifteen", "sixteen", "seventeen",
        "eighteen", "nineteen"]
TENS = ["", "", "twenty", "thirty", "forty", "fifty", "sixty", "seventy", "eighty", "ninety"]


def _under_thousand(n):
    words = []
    if n >= 100:
        words += [ONES[n // 100], "hundred"]
        n %= 100
        if n:
            words.append("and")
    if n >= 20:
        words.append(TENS[n // 10] + ("-" + ONES[n % 10] if n % 10 else ""))
    elif n or not words:
        words.append(ONES[n])
    return " ".join(words)


def number_words(n):
    if n >= 1_000_000_000:
        return " ".join(ONES[int(d)] for d in str(n))
    parts = []
    for value, name in ((1_000_000, "million"), (1000, "thousand")):
        if n >= value:
            parts.append(_under_thousand(n // value) + " " + name)
            n %= value
    if n or not parts:
        parts.append(_under_thousand(n))
    return " ".join(parts)


def _year(n):
    # 2026 -> "twenty twenty-six", 2005 -> "two thousand and five"
    hi, lo = divmod(n, 100)
    if 2000 <= n < 2010:
        return number_words(n)
    return _under_thousand(hi) + " " + ("hundred" if lo == 0 else ("oh " + ONES[lo] if lo < 10 else _under_thousand(lo)))


def _number(match):
    text = match.group(0).replace(",", "")
    if "." in text:
        whole, frac = text.split(".", 1)
        return number_words(int(whole or 0)) + " point " + " ".join(ONES[int(d)] for d in frac)
    n = int(text)
    if 1900 <= n <= 2099 and "," not in match.group(0):
        return _year(n)
    return number_words(n)


def speakable(text):
    # Ranges like "13–25" or "50-100" read as "13 to 25".
    text = re.sub(r"(\d)\s*[–-]\s*(\d)", r"\1 to \2", text)
    text = re.sub(r"(\d+(?:\.\d+)?)\s*[Kk]\b", lambda m: m.group(1) + " thousand", text)
    for term in sorted(PRONOUNCE, key=len, reverse=True):
        if term.isalnum() or re.fullmatch(r"[\w.\-]+", term):
            text = re.sub(r"(?<![\w])" + re.escape(term) + r"(?![\w])", PRONOUNCE[term], text)
        else:
            text = text.replace(term, " " + PRONOUNCE[term].strip() + " ")
    text = re.sub(r"\d[\d,]*(?:\.\d+)?", _number, text)
    text = re.sub(r"[*_#`/|\\<>\[\]{}()]", " ", text)
    text = re.sub(r"\s+", " ", text)
    return re.sub(r"\s+([.,!?;:])", lambda m: m.group(1), text).strip()
