import re
import json
from datetime import datetime
from typing import List, Dict, Any, Optional, Tuple
from jinja2 import Template


class UpdateTool:
    """
    Суммаризатор обновлений для колонок PRO/CON.

    Ключевые отличия от исходной версии:
    - Устойчивый парс ответа LLM: принимает dict либо строку, вырезает первый {...} блок,
      убирает ```json``` ограждения, чинит мелкий мусор.
    - Жёсткая валидация схемы: обязательные ключи, длины (PRO ≤150, CON ≤300), strength ∈ [0,100],
      impression 2–6 слов. Автотрим.
    - Аккуратный фолбэк: используется только если кратко (не раздувает апдейты).
    - Возвращён блок fallacy_hint в шаблон, чтобы LLM мог кратко отразить фаллации в CON.
    """

    # Ограничения длины сводок
    _MAX_PRO_CHARS = 150
    _MAX_CON_CHARS = 300
    # Ограничение на объём контекста (ASSISTANT_MD_SECTIONS),
    # чтобы модель не обрубала закрывающую скобку JSON.
    _MAX_CTX_CHARS = 2000

    def __init__(self, llm_provider=None) -> None:
        self.llm = llm_provider

        self.tpl = Template(
            """
            You are a debate summarizer. Read USER and ASSISTANT content.

            Return ONE valid JSON object ONLY (no markdown, no prose, no code fences).
            The JSON MUST have exactly these four keys, always present:

            {
            "pro_summary": "...",
            "pro_strength": 0,
            "pro_impression": "...",
            "con_summary": "..."
            }

            Rules:
            - pro_summary: one concise paragraph (≤{{ max_pro }} chars) capturing the USER's stance (steel-manned). No copy-paste.
            - con_summary: one concise paragraph (≤{{ max_con }} chars) with strongest objections/weak spots; briefly mention fallacies if given.
            - pro_strength: integer 0-100; based on clarity, evidence, logical soundness.
            - pro_impression: 2-6 words, e.g., "clear but under-evidenced".
            - If there is no content for a side, use "" for the summary and 0 for strength.
            - Never output anything except the JSON object.

            USER:
            {{ user_text }}

            ASSISTANT_MD_SECTIONS:
            {{ chat_md }}

            FALLACIES (optional, brief; e.g., TUQ: "span"):
            {{ fallacy_hint }}
            """
        )

    # ---------- public API ----------

    def summarize_and_make_updates(
        self,
        *,
        mode: str,
        user_text: str,
        chat_md: str,
        fallacies: Optional[Dict[str, Any]],
        ts: datetime,
    ) -> List[Dict[str, Any]]:
        # Источники для фолбэка (краткие, если потребуется)
        pro_src, con_src = self._extract_sources(user_text, chat_md, fallacies)

        # Основной прогон LLM
        pro_text, pro_strength, pro_impr, con_text = self._summarize_with_llm(
            user_text=user_text,
            chat_md=self._shrink(chat_md or "", self._MAX_CTX_CHARS),
            fallacy_hint=self._fallacy_hint(fallacies),
        )

        updates: List[Dict[str, Any]] = []
        if pro_text:
            body = f"{pro_text} — Strength: {pro_strength}/100; Impression: {pro_impr}".strip()
            updates.append(self._single_text_update("PRO", body, ts))
        if con_text:
            updates.append(self._single_text_update("CON", con_text, ts))

        # Осторожный фолбэк: только если НЕТ обновлений и есть короткие заготовки
        if not updates and (pro_src or con_src):
            if pro_src:
                safe_pro = self._truncate(pro_src, self._MAX_PRO_CHARS)
                body = f"{safe_pro} — Strength: 0/100; Impression: —"
                updates.append(self._single_text_update("PRO", body, ts))
            if con_src:
                safe_con = self._truncate(con_src, self._MAX_CON_CHARS)
                updates.append(self._single_text_update("CON", safe_con, ts))

        return updates

    # ---------- helpers ----------

    def _single_text_update(self, column: str, body: str, ts: datetime) -> Dict[str, Any]:
        _id = f"{column}_{self._hash('Summary', body)}"
        item = {"id": _id, "title": "Summary", "body": body, "tag": "summary"}
        return {"column": column, "items": [item], "timestamp": ts.isoformat()}

    def _hash(self, title: str, body: str) -> str:
        import hashlib
        return hashlib.sha256(f"{title}|{body}".encode("utf-8")).hexdigest()[:12]

    def _extract_sources(
        self, user_text: str, chat_md: str, fallacies: Optional[Dict[str, Any]]
    ) -> Tuple[str, str]:
        """
        Сбор кратких источников из USER/ASSISTANT/FALLACIES для безопасного фолбэка.
        """
        blocks = self._split_sections(chat_md)

        # PRO-источники
        pro_sections = [
            "refined claim",
            "refined value prop",
            "pros",
            "rebuttals",
            "improvements",
            "recommendations",
            "value prop",
        ]
        pro_frag: List[str] = []
        if user_text:
            pro_frag.append(user_text.strip())
        for name in pro_sections:
            if name in blocks:
                pro_frag.extend(self._bullets(blocks[name]))

        # CON-источники
        con_sections = ["critique", "objections", "risks", "weaknesses"]
        con_frag: List[str] = []
        for name in con_sections:
            if name in blocks:
                con_frag.extend(self._bullets(blocks[name]))

        # Краткий список кодов фаллаций
        if fallacies:
            hints = []
            for edu in fallacies.get("edus", []):
                for f in edu.get("fallacies", []):
                    code = str(f.get("code", "fallacy"))
                    hints.append(code.replace("_", " "))
            if hints:
                con_frag.append("fallacies: " + ", ".join(sorted(set(hints)))[:180])

        # Собираем строки; они всё равно будут подрезаны в фолбэке
        return ("; ".join(x for x in pro_frag if x).strip(),
                "; ".join(x for x in con_frag if x).strip())

    def _fallacy_hint(self, fallacies: Optional[Dict[str, Any]]) -> str:
        if not fallacies:
            return ""
        out = []
        for edu in fallacies.get("edus", []):
            for f in edu.get("fallacies", []):
                code = str(f.get("code", "fallacy"))
                span = str(f.get("span", ""))
                # Короткий токен-подсказка для компоновки CON
                if span:
                    out.append(f'{code}: "{span}"')
                else:
                    out.append(f"{code}")
        return "; ".join(out)

    def _split_sections(self, md: str) -> Dict[str, str]:
        sections: Dict[str, str] = {}
        cur = None
        for line in (md or "").splitlines():
            m = re.match(r"^#+\s+(.*)$", line.strip())
            if m:
                cur = m.group(1).strip().lower()
                sections[cur] = ""
            elif cur is not None:
                sections[cur] += line + "\n"
        return sections

    def _bullets(self, block: str) -> List[str]:
        out = []
        for line in (block or "").splitlines():
            s = line.strip()
            if s.startswith("- ") or s.startswith("• ") or s.startswith("*"):
                s = s.lstrip("-*• ").strip()
                if s:
                    out.append(s)
        if not out:
            # Если нет явных буллетов — берём абзац одной строкой
            para = (block or "").strip().replace("\n", " ")
            if para:
                out.append(para)
        return out

    def _summarize_with_llm(
        self,
        *,
        user_text: str,
        chat_md: str,
        fallacy_hint: str,
    ) -> Tuple[str, int, str, str]:
        """
        1 вызов LLM + строгий парс + жёсткая валидация.
        """
        prompt = self.tpl.render(
            user_text=user_text or "",
            chat_md=chat_md or "",
            fallacy_hint=fallacy_hint or "",
            max_pro=self._MAX_PRO_CHARS,
            max_con=self._MAX_CON_CHARS,
        )

        if not self.llm:
            # offline fallback (минимальный)
            pro_text = (user_text or "").strip()
            con_text = "Critique summary"
            return (
                self._truncate(pro_text, self._MAX_PRO_CHARS),
                60,
                "baseline",
                self._truncate(con_text, self._MAX_CON_CHARS),
            )

        # Основной ответ
        raw = self.llm.chat_json(prompt, temperature=0.0, max_tokens=360)
        data = self._parse_json_strict(raw)

        # Валидация и привод к контракту
        data = self._validate_summary_payload(data)

        pro_text = data["pro_summary"]
        con_text = data["con_summary"]
        pro_strength = data["pro_strength"]
        pro_impr = data["pro_impression"]

        return pro_text, pro_strength, pro_impr, con_text

    # ---------- low-level utilities ----------

    def _parse_json_strict(self, raw: Any) -> Dict[str, Any]:
        """
        Принимает dict или строку. Для строки:
        - снимает ```json / ``` ограждения
        - вырезает первый сбалансированный {...} блок
        - парсит json.loads
        Возвращает {} при любой ошибке.
        """
        if isinstance(raw, dict):
            return raw

        if not isinstance(raw, str):
            return {}

        s = raw.strip()
        # снять markdown-ограждения, если модель всё же их вставила
        s = re.sub(r"^```(?:json)?\s*", "", s)
        s = re.sub(r"\s*```$", "", s)

        # вырезать первый {...} блок
        i = s.find("{")
        j = s.rfind("}")
        if i == -1 or j == -1 or j < i:
            return {}
        s = s[i : j + 1]

        try:
            return json.loads(s)
        except Exception:
            return {}

    def _validate_summary_payload(self, d: Dict[str, Any]) -> Dict[str, Any]:
        """
        Гарантирует наличие ключей, корректные типы и длины.
        """
        # Обязательные ключи
        for k in ("pro_summary", "pro_strength", "pro_impression", "con_summary"):
            if k not in d:
                d[k] = "" if k.endswith("_summary") else 0

        # Типы и значения
        d["pro_summary"] = str(d.get("pro_summary", "") or "").strip()
        d["con_summary"] = str(d.get("con_summary", "") or "").strip()

        try:
            strength = int(d.get("pro_strength", 0))
        except Exception:
            strength = 0
        d["pro_strength"] = max(0, min(100, strength))

        d["pro_impression"] = str(d.get("pro_impression", "") or "").strip()
        words = d["pro_impression"].split()
        if not (2 <= len(words) <= 6):
            d["pro_impression"] = "under-specified"

        # Длины (жёстко обрезаем)
        if len(d["pro_summary"]) > self._MAX_PRO_CHARS:
            d["pro_summary"] = self._truncate(d["pro_summary"], self._MAX_PRO_CHARS)
        if len(d["con_summary"]) > self._MAX_CON_CHARS:
            d["con_summary"] = self._truncate(d["con_summary"], self._MAX_CON_CHARS)

        return d

    def _truncate(self, s: str, limit: int) -> str:
        """
        Короткий, безопасный триммер с попыткой обрезать по слову.
        """
        s = (s or "").strip()
        if len(s) <= limit:
            return s
        cut = s[:limit].rstrip()
        # мягко отрезать до ближайшего пробела/знака
        m = re.search(r"[ \t,.;:!?]\S*$", cut)
        if m:
            cut = cut[: m.start()].rstrip()
        return cut or s[:limit].rstrip()

    def _shrink(self, s: str, limit: int) -> str:
        """
        Простой усечитель длинного контента (например, chat_md).
        """
        s = s or ""
        if len(s) <= limit:
            return s
        # оставляем начало и конец, чтобы сохранить заголовки и свежие пункты
        head = s[: int(limit * 0.6)]
        tail = s[-int(limit * 0.3) :]
        return head + "\n...\n" + tail
