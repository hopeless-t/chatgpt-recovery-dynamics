#!/usr/bin/env python3
"""Build the repository's paper-style PDF from published reference JSON.

The output is intentionally generated from public derived data. No network I/O,
HAR parsing, or private data access occurs here.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import (
    BaseDocTemplate,
    Frame,
    KeepTogether,
    PageTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
    PageBreak,
    HRFlowable,
)
from reportlab.pdfbase.pdfmetrics import stringWidth


BG = colors.HexColor("#FFFFFF")
INK = colors.HexColor("#172033")
MUTED = colors.HexColor("#59677A")
CYAN = colors.HexColor("#1B9AAA")
GREEN = colors.HexColor("#258A52")
AMBER = colors.HexColor("#A66A00")
RED = colors.HexColor("#B23A48")
BLUE = colors.HexColor("#3859A6")
GRID = colors.HexColor("#D7DFEA")
PANEL = colors.HexColor("#F4F7FB")


def load(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def fmt(x, digits=3):
    if x is None:
        return "-"
    if isinstance(x, int):
        return str(x)
    return f"{x:.{digits}f}"


class ReportDocTemplate(BaseDocTemplate):
    def __init__(self, filename, **kwargs):
        super().__init__(filename, pagesize=A4, **kwargs)
        frame = Frame(
            18 * mm,
            18 * mm,
            A4[0] - 36 * mm,
            A4[1] - 34 * mm,
            id="normal",
            leftPadding=0,
            rightPadding=0,
            topPadding=0,
            bottomPadding=0,
        )
        self.addPageTemplates(PageTemplate(id="paper", frames=[frame], onPage=self._on_page))

    def _on_page(self, canvas, doc):
        canvas.saveState()
        page = canvas.getPageNumber()
        canvas.setStrokeColor(GRID)
        canvas.line(18 * mm, 14 * mm, A4[0] - 18 * mm, 14 * mm)
        canvas.setFont("Helvetica", 8)
        canvas.setFillColor(MUTED)
        canvas.drawString(18 * mm, 9.5 * mm, "ChatGPT Conversation Recovery Dynamics")
        canvas.drawRightString(A4[0] - 18 * mm, 9.5 * mm, f"Page {page}")
        canvas.restoreState()


def styles():
    s = getSampleStyleSheet()
    s.add(ParagraphStyle(
        name="PaperTitle",
        parent=s["Title"],
        fontName="Helvetica-Bold",
        fontSize=23,
        leading=26,
        textColor=INK,
        alignment=TA_CENTER,
        spaceAfter=10,
    ))
    s.add(ParagraphStyle(
        name="Subtitle",
        parent=s["Normal"],
        fontName="Helvetica",
        fontSize=11,
        leading=15,
        textColor=MUTED,
        alignment=TA_CENTER,
        spaceAfter=16,
    ))
    s.add(ParagraphStyle(
        name="H1x",
        parent=s["Heading1"],
        fontName="Helvetica-Bold",
        fontSize=16,
        leading=19,
        textColor=INK,
        spaceBefore=14,
        spaceAfter=7,
    ))
    s.add(ParagraphStyle(
        name="H2x",
        parent=s["Heading2"],
        fontName="Helvetica-Bold",
        fontSize=12,
        leading=15,
        textColor=BLUE,
        spaceBefore=9,
        spaceAfter=5,
    ))
    s.add(ParagraphStyle(
        name="Bodyx",
        parent=s["BodyText"],
        fontName="Helvetica",
        fontSize=9.3,
        leading=13.2,
        textColor=INK,
        spaceAfter=6,
    ))
    s.add(ParagraphStyle(
        name="Smallx",
        parent=s["BodyText"],
        fontName="Helvetica",
        fontSize=8,
        leading=10.7,
        textColor=MUTED,
        spaceAfter=4,
    ))
    s.add(ParagraphStyle(
        name="Eq",
        parent=s["BodyText"],
        fontName="Courier",
        fontSize=8.6,
        leading=12,
        textColor=INK,
        leftIndent=8 * mm,
        rightIndent=8 * mm,
        backColor=PANEL,
        borderColor=GRID,
        borderWidth=0.5,
        borderPadding=6,
        spaceBefore=5,
        spaceAfter=8,
    ))
    s.add(ParagraphStyle(
        name="Callout",
        parent=s["BodyText"],
        fontName="Helvetica-Bold",
        fontSize=9,
        leading=13,
        textColor=INK,
        backColor=colors.HexColor("#EEF7F8"),
        borderColor=CYAN,
        borderWidth=0.8,
        borderPadding=7,
        spaceBefore=5,
        spaceAfter=8,
    ))
    return s


def para(text, st):
    return Paragraph(text, st)


def table(data, widths=None, header=True):
    t = Table(data, colWidths=widths, repeatRows=1 if header else 0, hAlign="LEFT")
    cmds = [
        ("FONTNAME", (0, 0), (-1, -1), "Helvetica"),
        ("FONTSIZE", (0, 0), (-1, -1), 7.5),
        ("TEXTCOLOR", (0, 0), (-1, -1), INK),
        ("GRID", (0, 0), (-1, -1), 0.35, GRID),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING", (0, 0), (-1, -1), 5),
        ("RIGHTPADDING", (0, 0), (-1, -1), 5),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
    ]
    if header:
        cmds += [
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#EAF0F7")),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ]
    t.setStyle(TableStyle(cmds))
    return t


def section_title(text, st):
    return [para(text, st["H1x"]), HRFlowable(width="100%", thickness=0.6, color=GRID, spaceAfter=6)]


def build_story(summary, biopsy, deep, congestion):
    st = styles()
    story = []

    story += [
        Spacer(1, 14 * mm),
        para("ChatGPT Conversation Recovery Dynamics", st["PaperTitle"]),
        para("A client-side failure study, history-aware recovery model, and provider-friendly congestion design", st["Subtitle"]),
        para("<b>Repository technical report - generated from public derived data</b>", st["Subtitle"]),
        Spacer(1, 4 * mm),
        para(
            "<b>Abstract.</b> This report analyzes a sanitized client-side capture of a ChatGPT conversation-loading failure. "
            "It characterizes paired Accessible/Blocked regimes, transition history, cycle timing, residual temporal dependence, "
            "change points, and local recovery/congestion stress models. The resulting architecture emphasizes duplicate suppression, "
            "cheap observation, start-anchored retry spacing, recovery hysteresis, bounded admission, and one expensive materialization "
            "only after evidence of stable recovery. The report does not identify OpenAI's internal root cause or production topology.",
            st["Bodyx"],
        ),
        para("<b>Keywords:</b> conversation recovery; retry amplification; congestion control; hysteresis; change point; AR(1); client-side reliability", st["Smallx"]),
        para("<b>Evidence rule:</b> Visualization != Evidence.", st["Callout"]),
        PageBreak(),
    ]

    story += section_title("1. Scope and evidence discipline", st)
    story += [
        para(
            "The repository is a client-side case study. Raw authenticated HAR files are intentionally excluded. "
            "Only sanitized derivative events and aggregate measurements are published. Claims are separated into direct observations, "
            "recomputed facts, within-capture model evidence, compatible but unproven mechanisms, design proposals, weak historical "
            "external evidence, and explicitly unestablished claims.",
            st["Bodyx"],
        ),
        para(
            "The objective is constructive: recover readable conversation state while minimizing unnecessary provider work and avoiding "
            "diagnostic behavior that can itself create retry traffic.",
            st["Bodyx"],
        ),
    ]

    story += section_title("2. Public trace", st)
    ev = summary["relevant_events"]
    po = summary["paired_observations"]
    story += [
        table([
            ["Quantity", "Value"],
            ["Capture B entries", str(summary["capture_relationship"]["capture_b_entries"])],
            ["Relevant derived events", str(ev["total"])],
            ["Paired observations", str(po["total"])],
            ["Accessible pairs", str(po["accessible"])],
            ["Blocked pairs", str(po["blocked"])],
            ["Mixed pairs", str(po["mixed"])],
        ], [80 * mm, 70 * mm]),
        Spacer(1, 4 * mm),
        para(
            "Within the canonical pairing window, the trace contains no mixed stream/snapshot pairs. "
            "The Blocked state is also persistent across adjacent active observations.",
            st["Bodyx"],
        ),
        para(
            f"P(Blocked next | Blocked) = {po['p_blocked_given_blocked']:.6f}",
            st["Eq"],
        ),
    ]

    story += section_title("3. Transition biopsy and recovery hysteresis", st)
    rc = biopsy["reentry_contingency"]
    story += [
        table([
            ["Current Accessible history", "Next B", "Next A", "Total"],
            ["Immediately after B (E)", str(rc["reentry_to_blocked"]), "0", str(rc["reentry_n"])],
            ["Other Accessible (H)", str(rc["non_reentry_to_blocked"]), str(rc["non_reentry_n"] - rc["non_reentry_to_blocked"]), str(rc["non_reentry_n"])],
        ], [80 * mm, 25 * mm, 25 * mm, 25 * mm]),
        Spacer(1, 4 * mm),
        para(
            f"Observed Fisher one-sided p ~= {rc['fisher_exact_one_sided']:.3e}. "
            "This is strong within-capture evidence that the first success after Blocked is not equivalent to established Healthy state.",
            st["Bodyx"],
        ),
        para(
            "Blocked --success--> Recovering (E)\nRecovering --stable confirmation--> Healthy (H)\nRecovering --failure--> Blocked",
            st["Eq"],
        ),
    ]

    story.append(PageBreak())

    story += section_title("4. Cycle timing and latent residual memory", st)
    tm = deep["timing_residual_dynamics"]
    story += [
        para(
            f"Base cycle law: Delta ~= {tm['base_cycle_law']['intercept_s']:.4f} + "
            f"{tm['base_cycle_law']['service_coefficient']:.4f} * service_time",
            st["Eq"],
        ),
        para(
            f"The best BIC residual model is AR(1) with phi ~= {tm['best_bic_residual_model']['phi']:.3f}. "
            f"Delta BIC relative to independent residuals is {tm['delta_bic_ar1_minus_independent']:.2f}; "
            f"residual SSE falls by {100*tm['sse_reduction_fraction']:.1f}%.",
            st["Bodyx"],
        ),
        para(
            f"Post-completion wait itself has lag-1 phi ~= {tm['post_completion_wait_ar1_phi']:.3f}. "
            "The physical origin of this memory is not identified by the public trace.",
            st["Bodyx"],
        ),
        para(
            "Delta_n = S_n + mu + z_n + epsilon_n\nz_n = phi * z_(n-1) + eta_n",
            st["Eq"],
        ),
    ]

    story += section_title("5. Change points and robustness", st)
    cp_rows = [["Epoch", "First B index", "Best CP", "SSE reduction", "Permutation p"]]
    for row in deep["change_points"]:
        cp_rows.append([
            str(row["epoch"]),
            str(row["first_blocked_index"]),
            str(row["best_service_change_point_index"]),
            f"{100*row['sse_reduction_fraction']:.1f}%",
            f"{row['permutation_p_max_reduction_ge_observed']:.4g}",
        ])
    story += [
        table(cp_rows, [25 * mm, 35 * mm, 28 * mm, 35 * mm, 35 * mm]),
        Spacer(1, 4 * mm),
        para(
            "The independently fitted service-time change point coincides with the first Blocked observation in both active epochs.",
            st["Bodyx"],
        ),
        para(
            "Pairing counts remain unchanged across a 10-100 ms window plateau, and the active transition matrix remains unchanged "
            "for epoch-gap thresholds from 20 s through 600 s.",
            st["Bodyx"],
        ),
    ]

    story += section_title("6. History-free posterior predictive check", st)
    pp = deep["history_free_markov_posterior_predictive"]
    story += [
        para(
            f"Under a history-free A/B transition model, the posterior-predictive probability of the observed 8/8 reentry rebound pattern is approximately {pp['probability']:.3e}.",
            st["Callout"],
        ),
        para(
            "This complements the contingency analysis and motivates retaining E / Recovering as a separate state in the design model.",
            st["Bodyx"],
        ),
    ]

    story.append(PageBreak())

    story += section_title("7. Recovery architecture", st)
    story += [
        para(
            "many local triggers\n -> single-flight owner\n -> cheap state/version observation\n -> start-anchored retry if blocked\n"
            " -> Recovering / E on first success\n -> stable confirmation\n -> snapshot or delta once\n -> atomic reconcile\n -> optional realtime reattach",
            st["Eq"],
        ),
        para(
            "The transport layer is intentionally secondary to application recovery semantics. The proposed profile uses HTTP/2 as a baseline, "
            "HTTP/1.1 as a correctness-preserving fallback, HTTP/3 as optional path-survival acceleration, and WebSocket as optional realtime observation.",
            st["Bodyx"],
        ),
    ]

    story += section_title("8. Provider-friendly congestion design", st)
    c90 = congestion["selected_results"]["rho_0.90"]
    story += [
        table([
            ["Policy", "Retry amplification", "Recovery payload", "Recovery rejects"],
            ["Naive completion", f"{c90['naive_completion']['retry_amplification']:.2f}x", f"{c90['naive_completion']['recovery_payload_mib']:.1f} MiB", f"{c90['naive_completion']['recovery_rejected']:.1f}"],
            ["Retry-After + jitter", f"{c90['retry_after_jitter']['retry_amplification']:.2f}x", f"{c90['retry_after_jitter']['recovery_payload_mib']:.1f} MiB", f"{c90['retry_after_jitter']['recovery_rejected']:.1f}"],
            ["Single-flight + observe", f"{c90['singleflight_observe']['retry_amplification']:.2f}x", f"{c90['singleflight_observe']['recovery_payload_mib']:.1f} MiB", f"{c90['singleflight_observe']['recovery_rejected']:.1f}"],
            ["Server-friendly stack", f"{c90['server_friendly_stack']['retry_amplification']:.2f}x", f"{c90['server_friendly_stack']['recovery_payload_mib']:.1f} MiB", f"{c90['server_friendly_stack']['recovery_rejected']:.1f}"],
        ], [52 * mm, 35 * mm, 38 * mm, 35 * mm]),
        Spacer(1, 4 * mm),
        para(
            "These are abstract local simulation results at base rho=0.90, not OpenAI production telemetry. "
            "The qualitative mechanism is that avoidable recovery work consumes the same headroom needed by useful foreground work.",
            st["Bodyx"],
        ),
        para(
            "When sustained foreground offered work already equals or exceeds nominal capacity, retry control cannot create missing capacity. "
            "The problem becomes graceful degradation, bounded admission, and load shedding.",
            st["Callout"],
        ),
    ]

    story += section_title("9. Trace-preserving materialization accounting", st)
    tr = deep["trace_preserving_replay"]
    story += [
        table([
            ["Accounting quantity", "Value"],
            ["Transient recovery-tail Accessible observations", str(tr["transient_accessible_observations"])],
            ["Actual rounded successful snapshot payload", f"{tr['actual_success_snapshot_payload_mib']:.3f} MiB"],
            ["Conceptual probe-only payload", f"{tr['probe_only_payload_mib']:.3f} MiB"],
            ["Stable 2A materializations", str(tr["stable_2A_full_materializations"])],
            ["Accounting reduction", f"{100*tr['accounting_payload_reduction_fraction']:.2f}%"],
        ], [95 * mm, 55 * mm]),
        Spacer(1, 4 * mm),
        para(
            "This is fixed-trace accounting, not a causal production estimate. Suppressing real requests could change the trajectory.",
            st["Smallx"],
        ),
    ]

    story.append(PageBreak())

    story += section_title("10. Limitations and falsification priorities", st)
    for item in [
        "The analysis does not identify OpenAI internal root cause, capacity, queue structure, plan-level traffic share, or rate-limit scope.",
        "The H/E/B result is based on one capture with eight reentry samples.",
        "The AR-like residual state is descriptive; its physical implementation is unknown.",
        "External public reports are historical weak evidence, not IID telemetry.",
        "The strongest next step is an independent capture reproducing or rejecting the cycle law, reentry rebound, change point, and residual memory.",
    ]:
        story.append(para("- " + item, st["Bodyx"]))

    story += section_title("11. Responsible testing", st)
    story += [
        para(
            "This repository does not recommend active load testing, synthetic retry storms, deliberate 429 generation, or rate-limit bypass "
            "against production OpenAI services. Congestion experiments are local simulations. Real-service investigation should prefer passive "
            "observation of naturally occurring failures.",
            st["Callout"],
        ),
    ]

    story += section_title("12. Conclusion", st)
    story += [
        para(
            "The public trace supports a history-aware recovery view: a first success after Blocked is provisional, cycle timing contains a strong "
            "service-time component plus residual temporal memory, and the onset of Blocked aligns with a large latency change point in both active epochs. "
            "The resulting recovery architecture aims to improve user recovery while reducing duplicate provider work.",
            st["Bodyx"],
        ),
        para("<b>Recover. Don't amplify.</b>", st["PaperTitle"]),
        para("Visualization != Evidence.", st["Subtitle"]),
    ]
    return story


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--output", default="docs/paper/chatgpt-recovery-dynamics-paper.pdf")
    ap.add_argument("--summary", default="data/summary.json")
    ap.add_argument("--biopsy", default="data/transition_biopsy_reference.json")
    ap.add_argument("--deep", default="data/deep_validation_reference.json")
    ap.add_argument("--congestion", default="data/server_congestion_reference.json")
    args = ap.parse_args()

    summary = load(args.summary)
    biopsy = load(args.biopsy)
    deep = load(args.deep)
    congestion = load(args.congestion)

    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)

    doc = ReportDocTemplate(
        str(output),
        title="ChatGPT Conversation Recovery Dynamics",
        author="hopeless-t / repository-generated technical report",
        subject="Client-side recovery dynamics and provider-friendly congestion control",
        leftMargin=18 * mm,
        rightMargin=18 * mm,
        topMargin=18 * mm,
        bottomMargin=18 * mm,
    )
    doc.build(build_story(summary, biopsy, deep, congestion))
    print(output)


if __name__ == "__main__":
    main()
