"""
Retrieval over the Markdown files in knowledge/.

Each "# heading" section is one chunk. A heading like "Project: FitScale" puts the
chunk in the "project" category. Retrieval runs in two steps:
1. Routing: if the question is about a category ("what are your projects"), every
   chunk in that category is included, so list questions never miss an item.
2. BM25: keyword ranking fills the remaining slots with the most relevant other chunks.
"""

import math
import os
import re
from collections import Counter

KNOWLEDGE_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "knowledge")

STOP_WORDS = set("""
a an the and or of to in on at for from by with about as is are was were be been
i me my you your he she they it its this that what which who how when where why do
does did can could would should tell please any some just give dont don't full info
detail details all list only also more much many have has had get got
""".split())

# Question words that mean "this category". Matched after stemming.
INTENTS = {
    "project": ["project", "github", "repo", "side"],
    "experience": ["experience", "intern", "internship", "job", "worked", "company",
                   "samsung", "prism", "role", "career"],
    "education": ["education", "college", "university", "degree", "study", "studying", "cgpa",
                  "gpa", "marks", "grade", "school", "srm", "srmist", "rgukt", "btech", "class"],
    "skills": ["skill", "stack", "techstack", "tech", "technology", "language", "framework",
               "tool", "know", "programming"],
    "awards": ["award", "achievement", "prize", "hackathon", "won", "win", "badge", "leetcode",
               "accomplishment"],
    "contact": ["contact", "email", "mail", "reach", "linkedin", "hire", "connect", "phone"],
    "activities": ["extracurricular", "club", "activity", "society", "volunteer"],
    "site": ["website", "site", "avatar", "bot", "chatbot", "portfolio", "lip", "voice"],
}

# Heading text before ":" (or the whole heading) -> category.
HEADING_CATEGORY = {
    "project": "project", "experience": "experience", "education": "education",
    "technical skills": "skills", "awards and achievements": "awards", "contact": "contact",
    "extracurricular activities": "activities", "about this website": "site",
}


def _stem(word):
    # Light stemming so "projects" matches "project" and "skills" matches "skill".
    for suffix in ("ies", "es", "s"):
        if len(word) > 4 and word.endswith(suffix) and not word.endswith("ss"):
            return word[: -len(suffix)] + ("y" if suffix == "ies" else "")
    return word


def _tokens(text):
    words = re.findall(r"[a-z0-9]+", text.lower())
    return [_stem(w) for w in words if w not in STOP_WORDS]


class Retriever:
    def __init__(self, k1=1.5, b=0.75):
        self.k1, self.b = k1, b
        self.chunks = []
        self._load()

    def _load(self):
        for name in sorted(os.listdir(KNOWLEDGE_DIR)):
            if not name.endswith(".md"):
                continue
            with open(os.path.join(KNOWLEDGE_DIR, name), encoding="utf-8") as f:
                text = f.read()
            for section in re.split(r"(?m)^# ", text):
                section = section.strip()
                if not section:
                    continue
                title, _, body = section.partition("\n")
                title = title.strip()
                key = title.split(":")[0].strip().lower()
                self.chunks.append({"title": title, "text": body.strip(),
                                    "category": HEADING_CATEGORY.get(key)})

        # Title words count twice, so the "Education" section wins education questions.
        self.docs = [Counter(_tokens(c["title"]) * 2 + _tokens(c["text"])) for c in self.chunks]
        self.lengths = [sum(d.values()) for d in self.docs]
        self.avg_len = sum(self.lengths) / max(len(self.lengths), 1)
        df = Counter(term for d in self.docs for term in d)
        n = len(self.docs)
        self.idf = {t: math.log(1 + (n - f + 0.5) / (f + 0.5)) for t, f in df.items()}
        self.intents = {cat: {_stem(w) for w in words} for cat, words in INTENTS.items()}

    def route(self, query):
        """Categories the question asks about, e.g. {"project"}."""
        terms = set(_tokens(query))
        return {cat for cat, words in self.intents.items() if terms & words}

    def bm25(self, query):
        terms = _tokens(query)
        scores = []
        for i, doc in enumerate(self.docs):
            score = 0.0
            for t in terms:
                tf = doc.get(t, 0)
                if tf:
                    norm = tf * (self.k1 + 1) / (tf + self.k1 * (1 - self.b + self.b * self.lengths[i] / self.avg_len))
                    score += self.idf.get(t, 0) * norm
            scores.append(score)
        return scores

    def search(self, query, top_k=3):
        cats = self.route(query)
        scores = self.bm25(query)
        ranked = sorted(range(len(self.chunks)), key=lambda i: scores[i], reverse=True)

        picked = [i for i in ranked if self.chunks[i]["category"] in cats]
        # BM25 adds a few more relevant chunks on top of the routed ones.
        extra = max(1, top_k - len(picked)) if picked else top_k
        picked += [i for i in ranked if i not in picked and scores[i] > 0][:extra]
        # Vague questions ("hi", "who are you") still get the intro section.
        return [self.chunks[i] for i in picked] or [self.chunks[0]]
