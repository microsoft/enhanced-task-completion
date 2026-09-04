---
name: curbside-slip-pdf
description: Generate a reader-facing one-page BlastBox Curb Delivery note with the confirmed order, pickup time, complete assigned-bay details, weather-aware handling, safety precaution, barcode, and required fallback disclosure.
---

# Curb Delivery Slip PDF

This skill renders the customer's final collection instructions as a one-page
PDF. **Always run the bundled `curbside_slip.py` script. Never hand-draw the PDF
and never write your own rendering code.**

## When to use

Use this skill last, after the order, collection bay, staging time, handoff mode,
bay characteristics, weather-aware delivery handling, customer precaution, and
conditions disclosure are final. It only renders confirmed values; it does not
select a bay or calculate a staging window.

The staging time is when the already-picked order moves into curbside handoff
staging, not when picking or order preparation starts.

The order/store/bay facts originate from MCP tools, live conditions originate
from MSN Weather, and the staging time, band, and selected bay originate from the
bundled staging calculator. This PDF skill only renders that completed
orchestration.

## Workflow

### 1. Assemble the confirmed values

Pass the already-confirmed, reader-facing values:

- `--order`, `--customer`, `--store`, and assignment `--confirmation`
- `--bay` from the Curb Delivery assignment
- `--bay-covered`, `--bay-lit`, `--bay-facing`, and `--bay-priority` from the
  selected bay in the current Curb Delivery response
- `--handoff` from the staging calculator
- `--band`, `--stage-at`, and `--arrival-at` from the staging calculator
- `--items` as semicolon-separated item descriptions
- `--conditions` as a short customer-facing conditions summary
- `--delivery-note` using the calculator's delivery instruction and customer
  precaution
- `--conditions-source` as `live` or `fallback`
- `--out` as the PDF output path

Do not put internal paths, session IDs, tool names, or implementation details in
any value.

### Fallback disclosure

When `--conditions-source fallback` is used, the PDF includes a footer stating
that live weather was unavailable and the conditions are typical for the store,
not current. Do not remove, obscure, or contradict that disclosure.

### 2. Run the bundled script

```bash
python3 curbside_slip.py \
  --order ORD-10502 --customer "Jordan Pixel" \
  --store "BlastBox Pixel Heights" --confirmation "CURB-10502-1" --bay 1 \
  --bay-covered no --bay-lit yes --bay-facing 90 --bay-priority no \
  --handoff LIT --band DARK --stage-at "22:39" --arrival-at "22:44" \
  --items "BlastBox Omega Console x1" \
  --conditions "Partly cloudy, 13C, no rain expected before arrival" \
  --delivery-note "After-dark pickup requires a lit bay. Remain in your vehicle and use caution if stepping outside." \
  --conditions-source live --out blastbox_curbside_slip.pdf
```

The script prints:

```text
WROTE blastbox_curbside_slip.pdf
```

### 3. Report

Return the generated PDF to the customer and restate the bay number and plain
handoff instruction.

## Notes

- The barcode contains the confirmed curbside assignment reference.
- The script uses `reportlab`, matching the repository's existing PDF skill.
- The script makes no API or network calls.
