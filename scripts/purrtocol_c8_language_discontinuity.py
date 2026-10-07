#!/usr/bin/env python3
"""C8 Purrtocol Civilization: language discontinuity and institutional mistranslation.

Fictional simulation/game-system design only.

After a civilization-ending discontinuity, surviving text does not preserve a language.
Successor Purrtocol cultures may fail to recognize writing, may recognize it without
deciphering it, or may confidently institutionalize a completely wrong translation.

Core rules:
- Text != meaning.
- Script detection != decipherment.
- Decipherment != technical recovery.
- Social confidence != translation accuracy.
- Lost negation can invert a safety instruction.
- Lost units can become sacred numbers.
- Contradictory evidence can be absorbed into doctrine instead of correcting it.
"""
from __future__ import annotations

import hashlib
import json
from collections import Counter
from typing import Any

SCHEMA = "purrtocol-c8-language-discontinuity/v0"
ORIGIN_CIVILIZATION_SEED = 57


def h01(seed: int, *parts: object) -> float:
    key = "|".join(map(str, (seed, *parts)))
    return int(hashlib.sha256(key.encode("utf-8")).hexdigest()[:16], 16) / 16**16


def clamp(x: float) -> float:
    return max(0.0, min(1.0, x))


TEXT_RELICS: tuple[dict[str, Any], ...] = (
    {
        "relic_id": "oxygen-label",
        "original_text": "OXYGEN",
        "context": "pressure-tank",
        "glyph_cues": 0.18,
        "icon_cues": 0.10,
        "misreads": (
            ("ANCESTOR_OXY_GENE", "genealogy", "ancestor-name-fragment"),
            ("BLUE_BREATH_DEITY", "ritual", "breath-ritual"),
            ("TANK_OWNER_NAME", "administrative", "ownership-labeling"),
            ("FERTILITY_WORD", "ritual", "fertility-lexeme"),
        ),
    },
    {
        "relic_id": "hot-surface-warning",
        "original_text": "WARNING HOT SURFACE",
        "context": "thermal-panel",
        "glyph_cues": 0.10,
        "icon_cues": 0.32,
        "misreads": (
            ("WARM_SUN_BLESSING", "ritual", "heat-material-attention"),
            ("PURIFICATION_INSTRUCTION", "ritual", "heat-exposure-ritual"),
            ("FIRE_PRIEST_TITLE", "status", "priestly-title"),
            ("SUMMER_FESTIVAL_MARK", "leisure", "seasonal-festival-marker"),
        ),
    },
    {
        "relic_id": "do-not-step",
        "original_text": "DO NOT STEP",
        "context": "maintenance-panel",
        "glyph_cues": 0.12,
        "icon_cues": 0.22,
        "misreads": (
            ("STEP_HERE_RITUAL", "ritual", "floor-location-marking"),
            ("DONTI_STEP_CLAN_NAME", "genealogy", "clan-name-fragment"),
            ("PROCESSION_START_MARK", "practical", "route-start-sign"),
            ("FLOOR_BLESSING", "ritual", "floor-ritual"),
        ),
    },
    {
        "relic_id": "open-hatch",
        "original_text": "OPEN",
        "context": "crew-capsule-hatch",
        "glyph_cues": 0.28,
        "icon_cues": 0.42,
        "misreads": (
            ("PROSPERITY_RUNE", "status", "door-sign-convention"),
            ("WELCOME_WORD", "practical", "entrance-sign-convention"),
            ("ROYAL_SEAL", "status", "door-authority-mark"),
            ("DOOR_SPIRIT_NAME", "ritual", "door-spirit-cult"),
        ),
    },
    {
        "relic_id": "max-pressure",
        "original_text": "MAX PRESSURE 300 KPA",
        "context": "pressure-tank",
        "glyph_cues": 0.20,
        "icon_cues": 0.22,
        "misreads": (
            ("SACRED_NUMBER_300", "ritual", "numeral-preservation"),
            ("THREE_HUNDRED_ANCESTORS", "genealogy", "numeral-preservation"),
            ("TAX_CAP_300", "administrative", "numeral-administration"),
            ("RITUAL_PRESSURE_DAY", "ritual", "calendar-number"),
        ),
    },
    {
        "relic_id": "manual-title",
        "original_text": "FLIGHT OPERATIONS MANUAL",
        "context": "archive-fragment",
        "glyph_cues": 0.08,
        "icon_cues": 0.05,
        "misreads": (
            ("SKY_LITURGY", "ritual", "ascent-myth"),
            ("FUNERAL_JOURNEY_BOOK", "ritual", "funeral-route"),
            ("ROYAL_GENEALOGY", "genealogy", "dynastic-record"),
            ("MUSIC_OF_ASCENT", "leisure", "song-cycle"),
        ),
    },
    {
        "relic_id": "emergency-exit",
        "original_text": "EMERGENCY EXIT",
        "context": "corridor-sign",
        "glyph_cues": 0.15,
        "icon_cues": 0.50,
        "misreads": (
            ("SPEAR_GOD_SHRINE", "ritual", "directional-symbol"),
            ("PILGRIMAGE_DIRECTION", "practical", "directional-signage"),
            ("VICTORY_ROUTE", "status", "procession-routing"),
            ("MARKET_EXIT_TAX", "administrative", "gate-administration"),
        ),
    },
    {
        "relic_id": "no-smoking",
        "original_text": "NO SMOKING",
        "context": "habitat-sign",
        "glyph_cues": 0.12,
        "icon_cues": 0.45,
        "misreads": (
            ("SMOKE_OFFERING_ZONE", "ritual", "smoke-ritual"),
            ("ANTI_SMOKE_TABOO", "ritual", "smoke-prohibition"),
            ("FOG_PRIEST_TITLE", "status", "priestly-title"),
            ("WINTER_HEARTH_MARK", "practical", "hearth-sign"),
        ),
    },
)


def successor_language_state(seed: int) -> dict[str, float]:
    """Post-collapse language continuity is deliberately near zero."""
    return {
        "script_continuity": 0.005 + 0.08 * h01(seed, "script"),
        "language_continuity": 0.003 + 0.06 * h01(seed, "language"),
        "archive_literacy": 0.02 + 0.22 * h01(seed, "archive"),
        "icon_literacy": 0.08 + 0.45 * h01(seed, "icons"),
        "comparative_method": 0.02 + 0.30 * h01(seed, "comparative"),
        "ritualization": 0.18 + 0.70 * h01(seed, "ritual"),
        "status_pressure": 0.10 + 0.75 * h01(seed, "status"),
        "institutional_trust": 0.10 + 0.70 * h01(seed, "trust"),
        "need_for_meaning": 0.20 + 0.75 * h01(seed, "meaning"),
    }


def choose_misread(seed: int, relic: dict[str, Any], k: dict[str, float]) -> tuple[str, str, str]:
    ranked: list[tuple[float, tuple[str, str, str]]] = []
    for name, category, echo in relic["misreads"]:
        score = h01(seed, relic["relic_id"], name) + 0.15 * k["need_for_meaning"]
        if category == "ritual":
            score += 0.28 * k["ritualization"] + 0.06 * k["institutional_trust"]
        elif category == "status":
            score += 0.25 * k["status_pressure"]
        elif category == "practical":
            score += 0.18 * k["icon_literacy"] + 0.08 * k["comparative_method"]
        elif category == "administrative":
            score += 0.16 * k["institutional_trust"] + 0.10 * k["status_pressure"]
        elif category == "genealogy":
            score += 0.13 * k["status_pressure"] + 0.10 * k["ritualization"]
        elif category == "leisure":
            score += 0.12 * k["need_for_meaning"]
        ranked.append((score, (name, category, echo)))
    return max(ranked, key=lambda row: row[0])[1]


def institution_for(interpretation: str) -> str | None:
    mapping = {
        "ANCESTOR_OXY_GENE": "OXY_GENE_ANCESTOR_CULT",
        "WARM_SUN_BLESSING": "WARM_SUN_PURIFICATION_ORDER",
        "STEP_HERE_RITUAL": "SACRED_STEP_PILGRIMAGE",
        "PROCESSION_START_MARK": "PROCESSION_ROUTE_OFFICE",
        "PROSPERITY_RUNE": "MERCHANT_PROSPERITY_SIGIL_NETWORK",
        "WELCOME_WORD": "STANDARD_ENTRANCE_MARK",
        "SACRED_NUMBER_300": "THREE_HUNDRED_CANON",
        "TAX_CAP_300": "THREE_HUNDRED_TAX_CODE",
        "SKY_LITURGY": "ASCENT_LITURGY_SCHOOL",
        "PILGRIMAGE_DIRECTION": "PILGRIM_DIRECTION_SIGN_SYSTEM",
        "MARKET_EXIT_TAX": "GATE_TAX_AUTHORITY",
        "SMOKE_OFFERING_ZONE": "SMOKE_OFFERING_GUILD",
        "ANTI_SMOKE_TABOO": "ANTI_SMOKE_TEMPLE_RULE",
    }
    return mapping.get(interpretation)


def interpret_text(seed: int, relic: dict[str, Any], k: dict[str, float]) -> dict[str, Any]:
    writing_score = clamp(
        0.08
        + 0.34 * k["archive_literacy"]
        + 0.16 * k["comparative_method"]
        + relic["glyph_cues"]
        + 0.10 * (h01(seed, relic["relic_id"], "writing") - 0.5)
    )
    recognized_writing = writing_score >= 0.30

    decode_score = clamp(
        0.30 * k["script_continuity"]
        + 0.30 * k["language_continuity"]
        + 0.18 * k["comparative_method"]
        + 0.12 * k["archive_literacy"]
        + 0.10 * relic["icon_cues"]
        + 0.05 * (h01(seed, relic["relic_id"], "decode") - 0.5)
    )
    exact_translation = recognized_writing and decode_score >= 0.30

    if exact_translation:
        interpretation = "PARTIAL_LITERAL_DECIPHERMENT"
        category = "linguistic"
        functional_echo = "original-meaning-fragment"
    else:
        interpretation, category, functional_echo = choose_misread(seed, relic, k)

    functional_hint = (
        recognized_writing
        and not exact_translation
        and relic["icon_cues"] + 0.35 * k["icon_literacy"] >= 0.46
    )

    confidence = clamp(
        0.26
        + 0.34 * k["institutional_trust"]
        + 0.26 * k["ritualization"]
        + 0.12 * k["status_pressure"]
        + 0.08 * h01(seed, relic["relic_id"], "confidence")
    )
    correction_resistance = clamp(
        0.28
        + 0.30 * k["institutional_trust"]
        + 0.30 * k["ritualization"]
        + 0.18 * k["status_pressure"]
        - 0.30 * k["comparative_method"]
        + 0.08 * (h01(seed, relic["relic_id"], "resist") - 0.5)
    )

    if exact_translation:
        contradiction_response = "CORRECTION_ACCEPTED"
    elif correction_resistance >= 0.57:
        contradiction_response = "DOCTRINE_ABSORBS_CONTRADICTION"
    elif recognized_writing:
        contradiction_response = "COMPETING_TRANSLATION_SCHOOL"
    else:
        contradiction_response = "MARKS_NOT_ACCEPTED_AS_LANGUAGE"

    negation_inverted = (
        relic["relic_id"] == "do-not-step" and interpretation == "STEP_HERE_RITUAL"
    ) or (
        relic["relic_id"] == "no-smoking" and interpretation == "SMOKE_OFFERING_ZONE"
    )
    unknown_unit_sacralized = (
        relic["relic_id"] == "max-pressure"
        and interpretation in {"SACRED_NUMBER_300", "THREE_HUNDRED_ANCESTORS", "RITUAL_PRESSURE_DAY"}
    )

    institution = institution_for(interpretation)
    semantic_drift_chain = [
        "ORIGINAL_MEANING_HIDDEN_FROM_SUCCESSOR",
        interpretation,
    ]
    if institution:
        semantic_drift_chain.append(institution)

    return {
        "relic_id": relic["relic_id"],
        "historical_ledger_original_text": relic["original_text"],
        "original_text_visible_in_world_as_meaning": False,
        "successor_interpretation": interpretation,
        "interpretation_category": category,
        "recognized_as_writing": recognized_writing,
        "writing_recognition_score": round(writing_score, 6),
        "decipherment_score": round(decode_score, 6),
        "exact_translation": exact_translation,
        "functional_hint_without_decipherment": functional_hint,
        "functional_echo": functional_echo,
        "social_confidence": round(confidence, 6),
        "contradiction_response": contradiction_response,
        "negation_inverted": negation_inverted,
        "unknown_unit_sacralized": unknown_unit_sacralized,
        "institution": institution,
        "semantic_drift_chain": semantic_drift_chain,
    }


def successor_culture(seed: int) -> dict[str, Any]:
    k = successor_language_state(seed)
    rows = [interpret_text(seed, relic, k) for relic in TEXT_RELICS]
    institutions = sorted({row["institution"] for row in rows if row["institution"]})
    return {
        "successor_seed": seed,
        "evidence_status": "simulation",
        "language_state": {key: round(value, 6) for key, value in k.items()},
        "text_interpretations": rows,
        "recognized_as_writing": sum(row["recognized_as_writing"] for row in rows),
        "exact_translations": sum(row["exact_translation"] for row in rows),
        "institutions": institutions,
    }


def reference_suite() -> dict[str, Any]:
    successors = [successor_culture(seed) for seed in range(32)]
    rows = [row for culture in successors for row in culture["text_interpretations"]]
    interpretations = Counter(row["successor_interpretation"] for row in rows)
    by_relic: dict[str, set[str]] = {relic["relic_id"]: set() for relic in TEXT_RELICS}
    for row in rows:
        by_relic[row["relic_id"]].add(row["successor_interpretation"])

    recognized = sum(row["recognized_as_writing"] for row in rows)
    exact = sum(row["exact_translation"] for row in rows)
    functional_hints = sum(row["functional_hint_without_decipherment"] for row in rows)
    confident_wrong = sum(
        not row["exact_translation"] and row["social_confidence"] >= 0.60 for row in rows
    )
    absorbed = sum(
        row["contradiction_response"] == "DOCTRINE_ABSORBS_CONTRADICTION" for row in rows
    )
    negation_inversions = sum(row["negation_inverted"] for row in rows)
    unit_sacralizations = sum(row["unknown_unit_sacralized"] for row in rows)

    total = len(rows)
    if exact > 1:
        raise RuntimeError(f"C8 ancient language was deciphered too easily: {exact}/{total}")
    if not (40 <= recognized <= 160):
        raise RuntimeError(f"C8 writing recognition balance collapsed: {recognized}/{total}")
    if len(interpretations) < 24:
        raise RuntimeError("C8 translation diversity collapsed")
    if min(len(values) for values in by_relic.values()) < 3:
        raise RuntimeError("C8 same corpus no longer yields divergent translation schools")
    if functional_hints < 20:
        raise RuntimeError("C8 lost wrong-but-locally-useful sign interpretation")
    if confident_wrong < 80:
        raise RuntimeError("C8 lost confident mistranslation")
    if absorbed < 40:
        raise RuntimeError("C8 evidence too easily corrects established doctrine")
    if negation_inversions < 2:
        raise RuntimeError("C8 lost safety-negation inversion")
    if unit_sacralizations < 2:
        raise RuntimeError("C8 lost unknown-unit sacralization")

    return {
        "schema": SCHEMA,
        "evidence_status": "simulation",
        "origin_civilization_seed": ORIGIN_CIVILIZATION_SEED,
        "reference_bank": {
            "successor_cultures": len(successors),
            "text_relics_per_culture": len(TEXT_RELICS),
            "total_text_interpretations": total,
            "recognized_as_writing": recognized,
            "unrecognized_as_writing": total - recognized,
            "exact_translations": exact,
            "unique_successor_interpretations": len(interpretations),
            "functional_hints_without_decipherment": functional_hints,
            "confident_wrong_translations": confident_wrong,
            "doctrinal_absorptions_of_contradiction": absorbed,
            "negation_inversions": negation_inversions,
            "unknown_unit_sacralizations": unit_sacralizations,
            "interpretation_counts": dict(sorted(interpretations.items())),
        },
        "examples": successors[:8],
        "world_laws": {
            "text_is_not_meaning": True,
            "script_detection_is_not_decipherment": True,
            "decipherment_is_not_technical_recovery": True,
            "social_confidence_does_not_prove_translation_accuracy": True,
            "lost_negation_can_invert_safety_instruction": True,
            "unknown_units_can_become_sacred_numbers": True,
            "contradictory_evidence_can_be_absorbed_into_doctrine": True,
            "same_corpus_can_generate_multiple_translation_schools": True,
            "post_extinction_semantic_reset_is_default": True,
            "no_rosetta_stone_is_guaranteed": True,
            "no_final_civilization": True,
        },
    }


if __name__ == "__main__":
    print(json.dumps(reference_suite(), ensure_ascii=False, indent=2, sort_keys=True))
