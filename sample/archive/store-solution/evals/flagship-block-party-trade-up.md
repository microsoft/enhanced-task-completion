# Flagship Scenario — "The Block Party Trade-Up"

> **The kitchen-sink associate demo.** One customer, one visit, every pillar of the
> Modern Agent Experience firing together: **two parent MCPs**, **two connected
> agents — each with its own MCP underneath**, **three runtime-Python skills**, the
> **new `get_console_exclusives` upsell tool**, and a **generated settlement PDF**.
>
> A customer who runs a neighbourhood retro-gaming league walks up to the returns &
> service desk with a dead console and a shopping list. The **Store Associate
> Assistant** orchestrates the whole thing: rules the defect, prices the trade-up,
> closes the undecided customer with the MEGA-only AAA titles, reconciles his
> BlastPoints, and prints the settlement.

## Cast on stage

| Component | Kind | MCP / tools | Role in this run |
| --- | --- | --- | --- |
| **Store Associate Assistant** | Parent agent | **Membership MCP** (`get_membership`, `cancel_membership`), **Order Management MCP** (`get_order`, `request_return`) | Talks to the associate; owns the skills; relays Q&A between the connected agents and the associate. |
| **Store Policy Agent** | Connected agent | **Policy RAG MCP** (`search_policy`, `get_tier_refund_policy`) | Rules defective-vs-accidental; supplies the proration rule. Asks the defect-cause question first. |
| **Inventory & Fulfillment Agent** | Connected agent | **Warehouse MCP** (`check_stock`, `find_alternatives`, `get_restock_date`, `check_game_compatibility`, **`get_console_exclusives`** ← new) | Stock + transfer picture, game→model compatibility, and the **upsell** titles. |
| **prorated-refund-calculator** | Skill (Python) | — | Membership proration refund. |
| **points-reconciliation** | Skill (Python) | — | BlastPoints earn / promo / expiry. |
| **slip-pdf-generator** | Skill (Python) | — | Markdown slip → settlement **PDF** (reportlab). |
| **File generation** | Output | — | `blastbox_slip.pdf` (settlement). |

### Fixtures (all mock)

- **Customer:** Jordan Pixel, member **`MEGA-BLAST-1024`**, **BlastPass Plus Extra**
  ($129.99/yr), 8 unused months, $10 cancellation fee, outside the 14-day cooling-off.
  Runs the **"Pixel Block Party"** neighbourhood gaming league.
- **Hardware:** base **BlastBox Omega** $399.99 (**out of stock** locally, restock ~4
  days); **MEGA Edition** $499.99 (**5 in stock**, Seattle-WA1).
- **MEGA-only AAA titles** (from `get_console_exclusives("mega")`): *MEGA Lizards from
  Outer Space*, *Galactic Tax Evader VII: Audit Protocol*, *Mecha-Granny: Knitpocalypse*
  — none run on the base console.
- **Loyalty:** it's the week after **Triple BLAST Weekend** (3× base points). Jordan's
  prior balance 4,200 pts; 800 pts just expired.

## Expected headline numbers (verified against the bundled scripts)

- Membership prorated refund = **$76.66**  (8 × $10.8325 − $10)  ← `blastpass_refund.py`
- Upgrade difference = **$100.00**  ($499.99 − $399.99)
- **Net due from customer = $23.34**  ($100.00 − $76.66 store credit)
- BlastPoints after the weekend = **21,400 pts → $105.00** store credit
  (4,200 + 18,000 earned − 800 expired)  ← `points_reconciliation.py`

---

## Turn 1 — The request → the defect-cause question (round-trip)

### 🧑‍💼 Associate

> Customer's running a gaming-league block party this weekend and his main console
> just died about 10 days after he bought it — he's got the receipt. He wants a
> replacement if one's in stock, otherwise a refund, and while he's here he wants to
> cancel his BlastPass, member ID MEGA-BLAST-1024. Walk me through all of it.

### ⚙️ Orchestration

1. **Returns & Service Assistant** → **Store Policy Agent** → Policy RAG MCP ·
   `search_policy("defective console warranty vs accidental damage")`. The Policy
   Agent's rule is to **establish the defect cause first**, so it returns a *question*,
   not a ruling.
2. → **Membership MCP** · `get_membership("MEGA-BLAST-1024")` (read-only) — Jordan
   Pixel, Plus Extra, 8 months unused, $10 fee, cooling-off expired.
3. **Reasoning:** *"I can't rule on the console until I know the cause. Relay the Policy
   Agent's question before touching anything."*

### 🤖 Returns & Service Assistant

> Happy to handle the whole visit. One thing decides how the console is treated:
>
> - a **manufacturing defect** (won't power on, no physical damage) → **free warranty
>   swap, no restocking fee**, vs.
> - **accidental / physical / liquid damage** → standard return, possible fee.
>
> **Which is it — a manufacturing fault, or could it be accidental damage?**

> **Pillar:** connected-agent → parent → associate **question round-trip**. Nothing is
> ruled or changed yet.

---

## Turn 2 — Ruling + stock + the refund math

### 🧑‍💼 Associate

> Manufacturing fault — just won't power on, no physical or liquid damage.

### ⚙️ Orchestration

1. → **Store Policy Agent** · confirms **defective within 30 days = free warranty swap,
   no restocking fee**.
2. → **Inventory & Fulfillment Agent** → Warehouse MCP · `check_stock` (base = **0
   local**), `get_restock_date` (~4 days), `find_alternatives` (**MEGA Edition, $499.99,
   5 in stock, Seattle-WA1**).
3. → **prorated-refund-calculator** skill — runs Python →
   `$129.99 ÷ 12 = $10.8325; × 8 = $86.66; − $10 =` **$76.66**.

### 🤖 Store Associate Assistant

> Confirmed — **manufacturing defect inside 30 days → free warranty swap, no restocking
> fee.** 👍
>
> - The **base console is out of stock** here (restock ~4 days).
> - The **MEGA Edition is in stock now** at **$499.99** (base was $399.99).
>
> On the membership: Plus Extra, 8 unused months, $10 fee → prorated refund **$76.66**.
>
> So he can **wait ~4 days** for a like-for-like swap, **upgrade to MEGA now**, or take
> a **refund**. If he upgrades, I can put the $76.66 toward it. Which way is he leaning?

> **Pillars:** second connected agent (Inventory) with its own MCP; first **Python skill**
> run (the prorated refund).

---

## Turn 3 — "He can't decide" → the exclusives close it

### 🧑‍💼 Associate

> He's torn — he likes the idea of the MEGA Edition but he's not sure it's worth the
> extra hundred bucks over just waiting the four days for the base console to come back
> in stock. Give me something I can tell him to help him decide.

### ⚙️ Orchestration

1. → **Inventory & Fulfillment Agent** → Warehouse MCP · `get_console_exclusives("mega")`
   — returns the three MEGA-only AAA titles, each with a ready-to-say associate pitch.
2. **Reasoning:** *"The block party is this weekend — waiting four days means he misses
   it entirely. The deciding factor isn't the $100, it's the three games that physically
   won't run on the base console."*

### 🤖 Store Associate Assistant

> Easy one to make for him. Two things settle it:
>
> 1. **Timing** — the base console is ~4 days out, and his block party is **this
>    weekend**. The MEGA Edition is in stock *now*, so it's the only option that gets him
>    a working console in time.
> 2. **The games** — the MEGA Edition unlocks three AAA titles the base console **can't
>    load at all**:
>    - **MEGA Lizards from Outer Space** — *"200 neon space-lizards on screen at once
>      with a co-op buddy screaming next to you; the year's #1 couch-chaos shooter, and
>      it physically won't run on the base console."*
>    - **Galactic Tax Evader VII: Audit Protocol** — *"You're an interstellar accountant
>      dodging audits in real time across a living galaxy — critics call it 'Grand Theft
>      Spreadsheet.'"*
>    - **Mecha-Granny: Knitpocalypse** — *"A battle-mech granny knitting the apocalypse
>      back together in 4K. Hilarious, brutal, and the yarn engine only spins up on MEGA."*
>
> For a block-party host running a gaming league, those three exclusives plus same-day
> availability are the whole pitch — and remember the $76.66 membership refund can go
> straight toward the upgrade, so the real gap is small.

> **Pillar:** the **new `get_console_exclusives` upsell tool** doing the persuasion work —
> a connected agent surfacing demo-built content to close an undecided customer.

---

## Turn 4 — Execute → settle → loyalty → PDF

### 🧑‍💼 Associate

> Do it: warranty-swap him into the MEGA Edition, cancel the BlastPass and apply the
> $76.66 as store credit toward the upgrade, and tell me what he owes. Also — after
> Triple BLAST Weekend, what are his BlastPoints worth, in case he wants to knock down
> the balance? Then print me the slip as a PDF.

### ⚙️ Orchestration

1. → **Inventory & Fulfillment Agent** · `check_game_compatibility` confirms all three
   titles **require the MEGA Edition**.
2. → **Order Management MCP** · `request_return` (defective console, warranty exchange).
3. → **Membership MCP** · `cancel_membership("MEGA-BLAST-1024", 76.66)` — cancels
   BlastPass; refund issued as **store credit**.
4. → **points-reconciliation** skill — runs Python:
   prior 4,200; earn $499.99 × 3× (Triple BLAST) × 1.2 (Plus Extra) = **18,000**;
   expired **−800** → **21,400 pts → 21 × $5 = $105.00** store credit.
5. → **slip-pdf-generator** skill — runs reportlab → **`blastbox_slip.pdf`**.

### 🤖 Store Associate Assistant

> All done — here's the breakdown:
>
> - **Defective console** (manufacturing warranty) credited at **$399.99**, no fee.
> - **MEGA Edition** $499.99 → **upgrade difference $100.00**.
> - **BlastPass Plus Extra cancelled** → prorated refund **$76.66** applied as store
>   credit.
> - **Net due from customer: $23.34.**
>
> 🎮 **BlastPoints after the weekend: 21,400** (worth **$105.00**). He can redeem
> **$23.34** of that to walk out owing **$0** and keep ~**$81.66** in points — or pay
> the $23.34 and keep all 21,400.
>
> 🧾 Slip generated as a **PDF** — `blastbox_slip.pdf` — with the swap, the cancellation,
> the settlement math, and the three MEGA-exclusive titles noted as suggested add-ons.

> **Pillars:** parent **MCP** state changes (`request_return`, `cancel_membership`); two
> more **Python-resource skills** (points + PDF); **file generation** (PDF).

---

## How this scenario maps to the pillars

| Pillar | Where it fires |
| --- | --- |
| **Connected agents (each with its own MCP)** | Store Policy Agent · Policy RAG MCP (T1–T2); Inventory & Fulfillment Agent · Warehouse MCP (T2–T4) |
| **Multiple MCP servers** | Membership + Order Management (parent) · Policy RAG · Warehouse — **four MCPs** |
| **Connected-agent → parent → user round-trip** | Defect-cause question (T1) |
| **Skill runs Python** | prorated refund (T2), points reconciliation (T4), slip PDF (T4) |
| **New tool built for this demo** | `get_console_exclusives` on the Warehouse MCP (T3) |
| **File generation** | `blastbox_slip.pdf` (T4) |
| **Complex, multi-turn request** | 4 turns: rule → price → close the undecided customer → settle + loyalty + file |

## Why it's the flagship

- **Two connected agents, two MCPs under them** — Policy *rules*, Inventory *stocks and
  upsells* — plus two parent MCPs. The orchestration genuinely fans out and comes back.
- **The upsell closes a real decision:** when the customer can't choose between waiting
  for the restock and upgrading, `get_console_exclusives` gives the associate the exact
  words — three AAA titles that physically won't run on the base console — and same-day
  availability for a block party that's *this weekend*.
- **Every skill runs Python for the math** — the agent passes MCP results to a skill that
  computes the exact figures; it never hand-rolls arithmetic.
- **It ends with an artifact a real associate keeps:** a settlement PDF — and a loyalty
  twist that lets the customer walk out owing nothing.

## Notes

- All data is mock; serials, prices, game titles, and confirmation numbers are
  illustrative. Headline numbers ($76.66 / $100.00 / **$23.34**; **21,400 pts → $105.00**)
  are reproduced by the bundled scripts `blastpass_refund.py` and
  `points_reconciliation.py`.
- This is the **associate-facing** agent (separate from the self-serve card-reissue
  scenario on the Returns & Service Assistant). It reuses the associate skills/connected agents
  packaged in the solution source (`sample/solution/src/`) plus the new `get_console_exclusives` tool.
- Build order: (1) add `get_console_exclusives` to the Warehouse MCP, (2) attach the three
  Python skills to the parent, (3) wire the two connected agents with their MCPs, (4) run
  the 4-turn transcript in Preview and capture actuals.
