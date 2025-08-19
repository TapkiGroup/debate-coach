# Debate-Coach — Product Brief (Hackathon MVP)

Type a claim or pitch → GPT-5 runs a live mini-debate, flags fallacies, harvests sources, and continuously updates three evidence columns: Sources, Pro, Con — while you chat in the bottom pane.

## Why it matters

- Doubles as a Pitch & Objection simulator for founders, sales, and comms.
  
- Teaches debate structure: detect fallacies, anticipate objections, and separate verified from unverifiable claims.

- Trains critical thinking 


## UI Layout (desktop, single screen)

### Top 2/3: three live columns (scrollable histories)

- Sources – citations & notes (with tags).

- Pro – refined user position & supporting arguments.

- Con – critiques, counter-arguments, weak spots.

### Bottom 1/3: Chat window (user ↔ coach dialogue).

### Right side narrow rail: Mode switcher (two buttons) + brief mode descriptions.

## Modes (for the hackathon MVP)
### 🛡 Debate Coach

1) Chat prompts user to paste a position/argument or snippet from a discussion.

2) User chooses actions (any or all):

- Evaluate my argument → critique + fallacy detection + 0–100 strength score.

- Generate counter-arguments → ranked list with brief rationale.

- Find sources about my position → gather+summarize for/against evidence; tag reliability.

3) Live updates

- PRO: coach refines the user’s claim (clearer, steel-manned) and lists strongest supporting points.

- CON: coach posts weaknesses, fallacies (with icons) and strongest counter-points.

- SOURCES: adds references with short notes and validation labels.

4) Learning loop

After each turn, coach suggests expected opponent moves and how to respond.

Fallacies labeled (examples): Strawman, Whataboutism, Ad hominem, False cause, Appeal to authority, Slippery slope.

### 🎤 Pitch & Objection Mode

1) Chat prompts user to paste a pitch (product/slide outline/value prop).

2) User picks one of three:

- Brutal first-impression (concise, critique from “ruthless listener”).

- Obvious objections (top 5 objections + suggested rebuttals).

- Reality check (quick research scan; summary PRO/CON of the pitch’s assumptions).

3) Live updates

- PRO: value props, traction signals, credible assumptions.

- CON: risks, weak claims, market/feasibility gaps.

- SOURCES: market stats, analogs, prior art, competitor notes.

4) Learning loop

## Data flow & pipeline

User input (claim/pitch) → Mode selector.

Pre-analysis (GPT-5):

Extract claims, detect stance, split into propositions.

Decide which actions are requested (evaluate / counters / research).

Research (if requested):

- Tavily: web search → top results with snippets.

- Wikipedia API: entity facts & overviews.

Light heuristics: dedupe, classify supports/undermines/neutral.

## Argument mapping (GPT-5):

Update PRO/CON with ranked bullets (strength 1–5), link to source IDs when applicable.

Detect fallacies with short explanations + emojis/icons.

## UI events:

Chat posts Updated PRO/CON/SOURCES.

Columns append entries with timestamps (no destructive edits; we keep evolution).

## Scoring & labels

Argument Strength (0–100): composite of clarity, evidence, relevance, logical soundness.

Fallacy Flags: list with counts; clicking opens a one-sentence “why.”

Source Reliability: High (peer-review/official), Medium (reputable media/industry), Low (blogs/forums/unknown).

Evidence Tag: ✅ corroborated, ❌ refuted, ⚠️ disputed, 🕳 unverifiable.

## Tech choices (MVP, free-friendly)

Frontend: Next.js (or Streamlit for speed).

Backend: FastAPI (single endpoint per action), Python.

LLM: GPT-5 API (coupon).

Search: Tavily API (free tier) + Wikipedia REST API.

State: in-memory store (session) for column histories; simple IDs for cross-links.
