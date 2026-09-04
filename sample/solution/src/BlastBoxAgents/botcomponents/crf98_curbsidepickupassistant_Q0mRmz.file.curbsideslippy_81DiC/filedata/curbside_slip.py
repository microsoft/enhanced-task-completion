#!/usr/bin/env python3
"""BlastBox Curb Delivery collection slip -> PDF renderer.

Bundled skill script: the agent passes already-confirmed reader-facing values as
CLI flags. This script only lays them out in a one-page PDF using reportlab; it
never calls an API, looks up data, or makes a delivery decision.

Usage:
    python3 curbside_slip.py \\
        --order ORD-10422 --customer "Sarah Mitchell" \\
        --store "BlastBox Springfield" --confirmation CURB-10422-1 --bay 1 \\
        --bay-covered yes --bay-lit yes --bay-facing 90 --bay-priority no \\
        --handoff COVERED --band WET --stage-at 15:54 --arrival-at 16:00 \\
        --items "BlastBox Omega MEGA Edition x1;USB-C Charging Cable (3-pack) x2" \\
        --conditions "Rain showers, feels 33C" \\
        --delivery-note "Covered handoff; remain in the vehicle on wet pavement." \\
        --conditions-source live --out blastbox_curbside_slip.pdf
"""

import argparse
from pathlib import Path
import sys


ACCENT = "#6b2fb5"
LIGHT_ACCENT = "#f3eefb"

HANDOFF_WORDING = {
    "COVERED": "Covered bay - stay in your car",
    "SHADED": "Shaded bay - stay in your car",
    "LIT": "Well-lit bay - stay in your car",
    "LEEWARD": "Sheltered bay - stay in your car",
    "STANDARD": "Standard bay - stay in your car",
    "EXPOSED": "Exposed bay - wait until an associate confirms the handoff",
    "NONE": "No bay assigned - please wait for instructions",
}


def _escape(text):
    return (
        str(text)
        .replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
    )


def parse_items(value):
    items = [item.strip() for item in value.split(";") if item.strip()]
    if not items:
        raise ValueError("--items must contain at least one semicolon-separated item")
    return items


def build_pdf(details, output):
    from reportlab.graphics.barcode.code128 import Code128
    from reportlab.lib import colors
    from reportlab.lib.pagesizes import LETTER
    from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
    from reportlab.lib.units import inch
    from reportlab.platypus import (
        HRFlowable,
        KeepTogether,
        Paragraph,
        SimpleDocTemplate,
        Spacer,
        Table,
        TableStyle,
    )

    styles = getSampleStyleSheet()
    title = ParagraphStyle(
        "CurbTitle",
        parent=styles["Title"],
        fontSize=19,
        leading=22,
        textColor=colors.HexColor(ACCENT),
        spaceAfter=4,
    )
    subtitle = ParagraphStyle(
        "CurbSubtitle",
        parent=styles["BodyText"],
        fontSize=10,
        textColor=colors.HexColor("#555555"),
        spaceAfter=10,
    )
    bay_style = ParagraphStyle(
        "Bay",
        parent=styles["Title"],
        fontSize=30,
        leading=34,
        alignment=1,
        textColor=colors.HexColor(ACCENT),
    )
    heading = ParagraphStyle(
        "Section",
        parent=styles["Heading2"],
        fontSize=12,
        leading=14,
        textColor=colors.HexColor(ACCENT),
        spaceBefore=8,
        spaceAfter=4,
    )
    body = ParagraphStyle(
        "CurbBody",
        parent=styles["BodyText"],
        fontSize=10,
        leading=14,
    )
    footer = ParagraphStyle(
        "Fallback",
        parent=styles["BodyText"],
        fontSize=9,
        leading=12,
        textColor=colors.HexColor("#6a4a00"),
        backColor=colors.HexColor("#fff4cc"),
        borderPadding=7,
        spaceBefore=10,
    )
    centered = ParagraphStyle(
        "Centered",
        parent=body,
        alignment=1,
    )

    doc = SimpleDocTemplate(
        output,
        pagesize=LETTER,
        leftMargin=0.65 * inch,
        rightMargin=0.65 * inch,
        topMargin=0.55 * inch,
        bottomMargin=0.55 * inch,
    )
    flow = [
        Paragraph("BlastBox Curb Delivery", title),
        Paragraph("Collection handoff slip", subtitle),
        HRFlowable(width="100%", color=colors.HexColor(ACCENT)),
        Spacer(1, 8),
    ]

    meta = Table(
        [
            [
                Paragraph(
                    f"<b>Order</b><br/>{_escape(details['order'])}<br/>"
                    f"{_escape(details['customer'])}",
                    body,
                ),
                Paragraph(
                    f"<b>Confirmation</b><br/>{_escape(details['confirmation'])}",
                    body,
                ),
                Paragraph(f"<b>Store</b><br/>{_escape(details['store'])}", body),
            ]
        ],
        colWidths=[1.6 * inch, 2.2 * inch, 2.5 * inch],
    )
    meta.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor(LIGHT_ACCENT)),
                ("BOX", (0, 0), (-1, -1), 0.5, colors.HexColor(ACCENT)),
                ("INNERGRID", (0, 0), (-1, -1), 0.25, colors.white),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("LEFTPADDING", (0, 0), (-1, -1), 8),
                ("RIGHTPADDING", (0, 0), (-1, -1), 8),
                ("TOPPADDING", (0, 0), (-1, -1), 7),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 7),
            ]
        )
    )
    flow.append(meta)
    flow.append(Spacer(1, 10))

    bay_panel = Table(
        [
            [
                Paragraph(f"BAY {_escape(details['bay'])}", bay_style),
                Paragraph(
                    f"<b>Expected customer arrival</b><br/>"
                    f"{_escape(details['arrival_at'])}<br/><br/>"
                    f"<b>Curbside staging begins</b><br/>"
                    f"{_escape(details['stage_at'])}<br/><br/>"
                    f"<b>{_escape(details['handoff_text'])}</b>",
                    body,
                ),
            ]
        ],
        colWidths=[2.3 * inch, 4.0 * inch],
    )
    bay_panel.setStyle(
        TableStyle(
            [
                ("BOX", (0, 0), (-1, -1), 1.0, colors.HexColor(ACCENT)),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("BACKGROUND", (0, 0), (0, 0), colors.HexColor(LIGHT_ACCENT)),
                ("LEFTPADDING", (0, 0), (-1, -1), 10),
                ("RIGHTPADDING", (0, 0), (-1, -1), 10),
                ("TOPPADDING", (0, 0), (-1, -1), 12),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 12),
            ]
        )
    )
    flow.append(bay_panel)

    bay_details = Table(
        [
            [
                Paragraph("<b>Covered</b>", body),
                Paragraph("<b>Lit</b>", body),
                Paragraph("<b>Facing</b>", body),
                Paragraph("<b>Priority</b>", body),
                Paragraph("<b>Status</b>", body),
            ],
            [
                Paragraph(_escape(details["bay_covered"]), body),
                Paragraph(_escape(details["bay_lit"]), body),
                Paragraph(f"{_escape(details['bay_facing'])}&deg;", body),
                Paragraph(_escape(details["bay_priority"]), body),
                Paragraph("Assigned", body),
            ],
        ],
        colWidths=[1.15 * inch, 1.0 * inch, 1.2 * inch, 1.2 * inch, 1.75 * inch],
    )
    bay_details.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor(LIGHT_ACCENT)),
                ("BOX", (0, 0), (-1, -1), 0.5, colors.HexColor(ACCENT)),
                ("INNERGRID", (0, 0), (-1, -1), 0.25, colors.lightgrey),
                ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("TOPPADDING", (0, 0), (-1, -1), 5),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
            ]
        )
    )
    flow.extend(
        [
            Paragraph("Assigned bay details", heading),
            bay_details,
        ]
    )

    item_rows = [[Paragraph("<b>Items</b>", body)]]
    item_rows.extend(
        [[Paragraph(f"{index}. {_escape(item)}", body)]]
        for index, item in enumerate(details["items"], start=1)
    )
    item_table = Table(item_rows, colWidths=[6.3 * inch])
    item_table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor(ACCENT)),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("BOX", (0, 0), (-1, -1), 0.5, colors.HexColor(ACCENT)),
                ("INNERGRID", (0, 1), (-1, -1), 0.25, colors.lightgrey),
                ("LEFTPADDING", (0, 0), (-1, -1), 8),
                ("RIGHTPADDING", (0, 0), (-1, -1), 8),
                ("TOPPADDING", (0, 0), (-1, -1), 5),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
            ]
        )
    )
    flow.extend(
        [
            Paragraph("Your collection", heading),
            item_table,
            KeepTogether(
                [
                    Paragraph("Delivery note", heading),
                    Paragraph(
                        f"<b>Weather:</b> {_escape(details['conditions'])} "
                        f"(planning band: {_escape(details['band'])})<br/>"
                        f"<b>Handling and precaution:</b> "
                        f"{_escape(details['delivery_note'])}",
                        body,
                    ),
                ]
            ),
        ]
    )

    if details["conditions_source"] == "fallback":
        flow.append(
            Paragraph(
                "<b>Conditions note:</b> Live weather was unavailable. This plan "
                "uses conditions that are typical for this store, not current "
                "conditions.",
                footer,
            )
        )

    flow.extend(
        [
            Spacer(1, 12),
            HRFlowable(width="100%", color=colors.HexColor(ACCENT)),
            Spacer(1, 5),
            Paragraph(
                "Please stay in your car unless a store associate asks you to "
                "step out. Have your order number ready.",
                body,
            ),
            Spacer(1, 10),
            Code128(
                details["confirmation"],
                barHeight=0.45 * inch,
                barWidth=0.9,
            ),
            Paragraph(_escape(details["confirmation"]), centered),
        ]
    )
    doc.build(flow)


def _required_text(value, flag):
    cleaned = value.strip()
    if not cleaned:
        raise ValueError(f"{flag} must not be empty")
    return cleaned


def main(argv):
    parser = argparse.ArgumentParser(
        description="Render a one-page BlastBox Curb Delivery collection slip PDF."
    )
    parser.add_argument("--order", required=True)
    parser.add_argument("--customer", required=True)
    parser.add_argument("--store", required=True)
    parser.add_argument("--confirmation", required=True)
    parser.add_argument("--bay", required=True)
    parser.add_argument("--bay-covered", choices=("yes", "no"), required=True)
    parser.add_argument("--bay-lit", choices=("yes", "no"), required=True)
    parser.add_argument("--bay-facing", required=True)
    parser.add_argument("--bay-priority", choices=("yes", "no"), required=True)
    parser.add_argument(
        "--handoff", choices=sorted(HANDOFF_WORDING), required=True
    )
    parser.add_argument("--band", required=True)
    parser.add_argument("--stage-at", required=True)
    parser.add_argument("--arrival-at", required=True)
    parser.add_argument(
        "--items",
        required=True,
        help="Semicolon-separated reader-facing item descriptions.",
    )
    parser.add_argument("--conditions", required=True)
    parser.add_argument("--delivery-note", required=True)
    parser.add_argument(
        "--conditions-source", choices=("live", "fallback"), required=True
    )
    parser.add_argument("--out", required=True)
    args = parser.parse_args(argv[1:])

    try:
        details = {
            "order": _required_text(args.order, "--order"),
            "customer": _required_text(args.customer, "--customer"),
            "store": _required_text(args.store, "--store"),
            "confirmation": _required_text(args.confirmation, "--confirmation"),
            "bay": _required_text(args.bay, "--bay"),
            "bay_covered": args.bay_covered.title(),
            "bay_lit": args.bay_lit.title(),
            "bay_facing": _required_text(args.bay_facing, "--bay-facing"),
            "bay_priority": args.bay_priority.title(),
            "handoff_text": HANDOFF_WORDING[args.handoff],
            "band": _required_text(args.band, "--band"),
            "stage_at": _required_text(args.stage_at, "--stage-at"),
            "arrival_at": _required_text(args.arrival_at, "--arrival-at"),
            "items": parse_items(args.items),
            "conditions": _required_text(args.conditions, "--conditions"),
            "delivery_note": _required_text(args.delivery_note, "--delivery-note"),
            "conditions_source": args.conditions_source,
        }
        output = _required_text(args.out, "--out")
    except ValueError as exc:
        parser.error(str(exc))

    try:
        build_pdf(details, output)
    except ImportError:
        print("Error: reportlab is required to render the curbside slip PDF.")
        return 1
    except OSError as exc:
        print(f"Error: could not write PDF ({exc}).")
        return 1

    if not Path(output).is_file():
        print("Error: PDF output was not created.")
        return 1
    print(f"WROTE {output}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
