# -*- coding: utf-8 -*-
"""
Классификация вида объекта капитального строительства по логике п. 2 ПП РФ №87
(производственный / непроизводственный / линейный) по свободному тексту ТЗ.

Зависимостей нет — подходит для Google Colab.
"""

from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass, field
from typing import Iterable, Literal

PP87Kind = Literal["production", "non_production", "linear", "unknown"]


def _normalize(text: str) -> str:
    t = unicodedata.normalize("NFKC", text or "").lower()
    t = t.replace("ё", "е")
    t = re.sub(r"[^\w\s\-]+", " ", t, flags=re.UNICODE)
    t = re.sub(r"\s+", " ", t).strip()
    return t


def _contains_any(hay: str, needles: Iterable[str]) -> list[str]:
    found: list[str] = []
    for n in needles:
        if n and n in hay:
            found.append(n)
    return found


def _match_production_terms(n: str) -> list[str]:
    """Подбор производственных терминов без ложных вхождений в «непроизводственн…»."""
    found: list[str] = []
    for term in PRODUCTION_TERMS:
        if term == "производственн":
            if re.search(r"(?<!не)производственн", n):
                found.append(term)
        elif term in n:
            found.append(term)
    return found


def _match_non_production_terms(n: str) -> list[str]:
    """Непроизводственные термины; «отель» не цепляет «котельную»."""
    found: list[str] = []
    for term in NON_PRODUCTION_TERMS:
        if term == "отель":
            if re.search(r"(?<!к)отель", n):
                found.append(term)
        elif term in n:
            found.append(term)
    return found


# --- Линейные объекты (п. 2 в) ПП №87 и типичные формулировки ТЗ ---
LINEAR_TERMS = [
    "линейный объект",
    "линейные объекты",
    "магистральный газопровод",
    "магистральный нефтепровод",
    "магистральный продуктопровод",
    "нефтепровод",
    "продуктопровод",
    "водовод между",
    "канализационный коллектор",
    "канализационный сток",
    "трубопровод протяжен",
    "трасса газопровода",
    "трасса нефтепровода",
    "трасса трубопровода",
    "участок автомобильной дороги",
    "автомобильная дорога",
    "автомобильной дороги",
    "автомобильной дорог",
    "автодорога",
    "железнодорожная линия",
    "железная дорога",
    "вокзал комплекс",  # часто сопутствует, но не линейный сам по себе — уберём если мешает
    "линия электропередачи",
    "лэп",
    "вл ",
    "вл-",
    "вл110",
    "вл 110",
    "вл-110",
    "вл220",
    "вл 220",
    "вл-220",
    "вл330",
    "вл 330",
    "вл-330",
    "воздушная линия",
    "кабельная линия 110",
    "кабельная линия 220",
    "опора лэп",
    "протяженностью км",
    "протяженностью километр",
    "км трассы",
    "линия электропередач",
    "электропередач",
    "элетропередач",
    "элетропередачи",
]

# Уточнения: «вокзал» сам по себе не линейный — исключим из автоматического LINEAR
LINEAR_FALSE_POSITIVE = ["вокзал комплекс"]
LINEAR_TERMS = [t for t in LINEAR_TERMS if t not in LINEAR_FALSE_POSITIVE]

# Опечатки «элетро» и род. «электропередач»; однословное «дорога» (краткое ТЗ)
_RE_LINEAR_ELECTRO = re.compile(r"эле(?:кт|т)ропереда\w*")
_RE_LINEAR_LINE_ELECTRO = re.compile(r"линия\s+эле(?:кт|т)ропереда\w*")


def _match_linear_terms(n: str) -> list[str]:
    found = _contains_any(n, LINEAR_TERMS)
    if _RE_LINEAR_LINE_ELECTRO.search(n):
        found.append("линия электропередачи (regex)")
    elif _RE_LINEAR_ELECTRO.search(n):
        found.append("электропередача (regex)")
    if re.fullmatch(r"дорога|дороги", n):
        found.append("дорога (одно слово)")
    return list(dict.fromkeys(found))

# --- Производственное назначение (п. 2 а), кроме линейных) ---
PRODUCTION_TERMS = [
    "производственн",
    "производство",
    "цех",
    "завод",
    "фабрик",
    "складск",
    "склад ",
    "логистическ",
    "промышленн",
    "промплощадк",
    "промзона",
    "энергообъект",
    "энергоустановк",
    "тэц",
    "грэс",
    "котельн",
    "котельная",
    "газовая котельная",
    "автоматизированная котельная",
    "котельная установк",
    "теплопункт",
    "тпу ",
    "насосная станция",  # часто производственная/коммунальная — ниже донастроим
    "компрессорная станция",
    "газораспределительн",
    "грс",
    "гис",
    "нефтегаз",
    "добыч",
    "переработк",
    "горнорудн",
    "шахт",
    "карьер",
    "обогатительн",
    "агрегатн",
    "ремонтн",
    "мастерск",
    "сто ",
    "сто,",
    "сто.",
    "сто ",
    "автосервис",
    "сто автомобил",
    "пищевое производство",
    "химическ",
    "металлург",
    "машиностроен",
    "сельхозпредприят",
    "ферм",
    "комбикорм",
    "элеватор",
    "объект оборон",
    "оборонн",
    "фсб",
    "мвд",
    "режимн",
]

# --- Непроизводственное назначение (п. 2 б)) ---
NON_PRODUCTION_TERMS = [
    "жил",
    "жилого комплекса",
    "жилой комплекс",
    "жилищн",
    "многоквартирн",
    "мкд",
    "квартир",
    "индивидуальн жил",
    "таунхаус",
    "жк ",
    "жк,",
    "жк.",
    "благоустройств",
    "школ",
    "детск сад",
    "дошкольн",
    "больниц",
    "поликлиник",
    "фельдшер",
    "медицинск",
    "культур",
    "театр",
    "музей",
    "библиотек",
    "спортивн",
    "стадион",
    "бассейн",
    "административн",
    "офисн",
    "бизнес-центр",
    "бизнес центр",
    "торгов",
    "тц ",
    "трц",
    "гостиниц",
    "отель",
    "религиозн",
    "храм",
    "церков",
    "мечет",
    "кладбищ",
    "коммунально-бытов",
    "коммунальн",
    "жкх",
    "многофункциональн комплекс",
    "мфк",
    "общественн",
    "образовательн",
    "вуз",
    "университет",
    "институт",
]

# Сигналы ОКС (объект капитального строительства) — для явной метки в ответе
OKS_POSITIVE = [
    "строительств",
    "реконструкц",
    "капитальн ремонт",
    "капремонт",
    "новое строительство",
    "проектирован",
    "проектн документац",
    "объект капитальн",
    "окс",
    "здани",
    "строени",
    "сооружени",
    "площадк",
    "участок",
    "генплан",
    "техническое задание",
    "тз ",
]

# Слабые / неоднозначные случаи
PRODUCTION_HINT_FOR_BOILER = [
    "котельн",
    "котельная",
    "газовая котельная",
    "автоматизированная котельная",
]


@dataclass
class PP87ObjectClassification:
    """Результат классификации по п. 2 ПП №87."""

    raw_text: str
    normalized: str
    is_likely_capital_construction: bool
    pp87_kind: PP87Kind
    scores: dict[str, float] = field(default_factory=dict)
    matched_terms: dict[str, list[str]] = field(default_factory=dict)
    rationale_ru: str = ""

    def as_dict(self) -> dict:
        return {
            "raw_text": self.raw_text,
            "is_likely_capital_construction": self.is_likely_capital_construction,
            "pp87_kind": self.pp87_kind,
            "scores": dict(self.scores),
            "matched_terms": {k: list(v) for k, v in self.matched_terms.items()},
            "rationale_ru": self.rationale_ru,
        }


def classify_pp87_object_kind(text: str) -> PP87ObjectClassification:
    """
    Определяет вид объекта по п. 2 ПП №87: production | non_production | linear | unknown.

    Эвристики по ключевым словам (не LLM). Для сложных ТЗ лучше комбинировать с моделью.
    """
    n = _normalize(text)
    matched_linear = _match_linear_terms(n)
    matched_prod = _match_production_terms(n)
    matched_non = _match_non_production_terms(n)
    matched_oks = _contains_any(n, OKS_POSITIVE)

    scores = {"linear": 0.0, "production": 0.0, "non_production": 0.0}
    matched = {
        "linear": matched_linear,
        "production": matched_prod,
        "non_production": matched_non,
        "oks": matched_oks,
    }

    scores["linear"] += 3.0 * len(matched_linear)
    scores["production"] += 1.2 * len(matched_prod)
    scores["non_production"] += 1.2 * len(matched_non)

    if "жилого комплекса" in n or "жилой комплекс" in n:
        scores["non_production"] += 2.5

    # Котельная без жилого контекста — чаще производственная/энергетическая (как в вашем ТЗ)
    boilerish = any(k in n for k in PRODUCTION_HINT_FOR_BOILER)
    housingish = bool(matched_non) and any(
        x in n for x in ("жил", "мкд", "квартир", "жк ", "жк,", "жк.", "жилищн", "таунхаус")
    )
    if boilerish and not housingish and not matched_linear:
        scores["production"] += 2.5

    # Явное «для производственного здания» и т.п.
    if "производственн" in n and "здан" in n:
        scores["production"] += 2.0

    # Дорога + протяжённость — типичный линейный объект (п. 2в)
    if re.search(r"\bдорог", n) and re.search(r"\d+\s*км", n) and "подъезд" not in n:
        scores["linear"] += 2.5

    likely_oks = bool(matched_oks) or bool(
        re.search(
            r"\b(строю|строим|спроектир|возвод|возведен|здани|сооружен|котельн|трубопровод|дорог|лэп|линия|теплопункт)\b",
            n,
        )
    )

    kind: PP87Kind = "unknown"
    rationale_parts: list[str] = []

    # Два разных объекта в одном тексте без связки «котельная для …» — не классифицируем однозначно
    dual_housing_and_boiler = (
        not matched_linear
        and any(p in n for p in ("жилой комплекс", "жилого комплекса", "жк ", "жк,", "жк.", "мкд"))
        and any(p in n for p in ("котельн", "котельная", "газовая котельная", "автоматизированная котельная"))
    )
    boiler_for_housing = bool(
        re.search(r"котельн(ая|ой|ую)?\s+для\b", n) or re.search(r"котельн\w*\s+для\b", n)
    )

    if scores["linear"] > 0 and scores["linear"] >= max(scores["production"], scores["non_production"]):
        kind = "linear"
        rationale_parts.append("Обнаружены признаки линейного объекта (трубопроводы, дороги, ЛЭП и т.п.).")
    elif dual_housing_and_boiler and not boiler_for_housing:
        kind = "unknown"
        rationale_parts.append(
            "В тексте одновременно жилая застройка и котельная без явной формулировки «котельная для …» — уточните объект проектирования."
        )
    elif boilerish and housingish and not matched_linear:
        # Котельная в жилом контексте: без уточнения «что именно объект» остаёмся в unknown или непроизводственный
        diff = abs(scores["production"] - scores["non_production"])
        if diff < 1.6:
            kind = "unknown"
            rationale_parts.append(
                "Одновременно признаки котельной/энергообъекта и жилой застройки — уточните, что является объектом проектирования."
            )
        elif scores["non_production"] > scores["production"]:
            kind = "non_production"
            rationale_parts.append(
                "Котельная в явном жилом/социальном контексте — ближе к непроизводственной застройке (п. 2б ПП №87)."
            )
        else:
            kind = "production"
            rationale_parts.append("Преобладают производственные признаки даже при упоминании жилой инфраструктуры.")
    elif scores["production"] > scores["non_production"] + 0.5:
        kind = "production"
        rationale_parts.append("Преобладают признаки объекта производственного назначения (п. 2а ПП №87).")
    elif scores["non_production"] > scores["production"] + 0.5:
        kind = "non_production"
        rationale_parts.append("Преобладают признаки объекта непроизводственного назначения (п. 2б ПП №87).")
    elif scores["production"] > 0 and scores["non_production"] > 0:
        kind = "unknown"
        rationale_parts.append("Смешанные признаки производственного и непроизводственного назначения — нужно уточнение ТЗ.")
    elif scores["production"] > 0:
        kind = "production"
        rationale_parts.append("Есть признаки производственного назначения.")
    elif scores["non_production"] > 0:
        kind = "non_production"
        rationale_parts.append("Есть признаки непроизводственного назначения.")
    else:
        rationale_parts.append("Недостаточно ключевых слов для уверенной классификации по ПП №87.")

    if likely_oks:
        rationale_parts.append("Текст похож на описание объекта капитального строительства (ОКС).")
    else:
        rationale_parts.append("Признаки ОКС выражены слабо — возможно, это не полное ТЗ или не строительство.")

    return PP87ObjectClassification(
        raw_text=text,
        normalized=n,
        is_likely_capital_construction=likely_oks,
        pp87_kind=kind,
        scores=scores,
        matched_terms=matched,
        rationale_ru=" ".join(rationale_parts),
    )


def public_reply_ru(c: PP87ObjectClassification) -> str:
    """
    Короткий ответ пользователю: без баллов, совпавших слов и пояснений алгоритма.
    """
    if c.pp87_kind == "linear":
        return "Считаю: это линейный объект капитального строительства (п. 2в ПП №87)."
    if c.pp87_kind == "production":
        return (
            "Считаю: это объект капитального строительства производственного назначения "
            "(п. 2а ПП №87), не линейный."
        )
    if c.pp87_kind == "non_production":
        return (
            "Считаю: это объект капитального строительства непроизводственного назначения "
            "(п. 2б ПП №87), не линейный."
        )
    return "Считаю: по этому тексту нельзя однозначно отнести объект к виду по п. 2 ПП №87."


def run_interactive_cli() -> None:
    """Простой диалог в консоли: запрос — один ответ (public_reply_ru)."""
    print("Определение вида объекта по п. 2 ПП №87. Пустая строка — выход.")
    while True:
        try:
            line = input("ТЗ> ").strip()
        except EOFError:
            break
        if not line:
            break
        c = classify_pp87_object_kind(line)
        print(public_reply_ru(c))
        print()


def _demo_assertions() -> None:
    """Проверки на нескольких формулировках (для Colab: просто запустите скрипт)."""
    cases: list[tuple[str, PP87Kind, bool]] = [
        ("строю котельную", "production", True),
        ("Нужно спроектировать автоматизированную газовую котельную для производственного здания", "production", True),
        ("МКД, 12 этажей, жилой дом", "non_production", True),
        ("магистральный газопровод протяженностью 15 км", "linear", True),
        ("ЛЭП 110 кВ, воздушная линия, 8 км", "linear", True),
        ("школа на 550 мест, непроизводственное назначение", "non_production", True),
        ("цех механообработки, реконструкция", "production", True),
        ("торговый центр с парковкой", "non_production", True),
        ("внутриплощадочные сети теплоснабжения от котельной", "production", True),
        ("жилой комплекс, котельная на крыше", "unknown", True),  # смешанный контекст
        ("котельная для отопления жилого комплекса", "non_production", True),
        ("линия элетропередач", "linear", True),
        ("дорога", "linear", True),
        ("теплопункт", "production", True),
    ]
    for text, expected_kind, _ in cases:
        r = classify_pp87_object_kind(text)
        assert r.pp87_kind == expected_kind, (
            f"FAIL\n  text: {text!r}\n  expected: {expected_kind}\n  got: {r.pp87_kind}\n  scores: {r.scores}\n  matched: {r.matched_terms}"
        )
        assert public_reply_ru(r).startswith("Считаю:")
    print("pp87_object_kind: все встроенные проверки прошли.")


if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1 and sys.argv[1] in ("-t", "--test", "--self-test"):
        _demo_assertions()
    elif len(sys.argv) > 1 and sys.argv[1] in ("-d", "--dict"):
        _demo_assertions()
        samples = [
            "строю котельную",
            "котельная для отопления жилого комплекса",
            "реконструкция автомобильной дороги участок 5 км",
        ]
        for s in samples:
            print("---")
            print(s)
            print(classify_pp87_object_kind(s).as_dict())
    else:
        run_interactive_cli()
