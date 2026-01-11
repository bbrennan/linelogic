# Recent Picks Table Design — Showing the Actual Pick

**Date:** January 10, 2026  
**Enhancement:** Added market type and improved pick visibility

---

## The Problem: Missing Pick Details

**User Question:** "What did I bet on?"

**Current Table Response:** "Lakers"  
**User Confusion:** "Lakers what? Moneyline? Spread? Over/Under?"

**Better Response:** "Lakers -5.5" or "Over 215.5" or "Jayson Tatum O28.5 PTS"

---

## New Table Structure

### Column Order (Reading Left to Right)

```
Date | Market | 📍 Pick | Result | Model% | Market% | Edge | Tier | Stake | P&L
```

**Rationale:**
1. **Date** — When was this picked? (temporal context)
2. **Market** — What type? (decision context)
3. **📍 Pick** — WHAT DID WE PICK? (primary question)
4. **Result** — How did it go? (immediate outcome)
5. **Model%** — Why did we pick it? (model reasoning)
6. **Market%** — What does the market think? (comparison)
7. **Edge** — How much edge? (decision confidence)
8. **Tier** — How confident? (visual confidence badge)
9. **Stake** — How much $ at risk? (bet sizing)
10. **P&L** — What's the money impact? (outcome)

---

## Example Data (Showing Real Picks)

### Moneyline Pick
```
Date  | Market | 📍 Pick        | Result | Model% | Market% | Edge  | Tier     | Stake  | P&L
01/10 | ML     | Lakers         | ✅ Win | 62%    | 54%     | +8.2% | 🏆 TIER 1| $25.00 | +$23.50
```

### Spread Pick
```
Date  | Market | 📍 Pick        | Result | Model% | Market% | Edge  | Tier     | Stake  | P&L
01/10 | Spread | Heat -5.5      | ❌Loss | 58%    | 52%     | +6.1% | 🥇 TIER 2| $20.00 | -$20.00
```

### Total Pick
```
Date  | Market | 📍 Pick        | Result | Model% | Market% | Edge  | Tier     | Stake  | P&L
01/10 | Total  | Over 215.5     | ⏳Pend | 55%    | 50%     | +5.0% | 🥇 TIER 2| $15.00 | -
```

### Prop Bet
```
Date  | Market | 📍 Pick              | Result | Model% | Market% | Edge  | Tier     | Stake  | P&L
01/10 | Prop   | Jalen Green O27.5 PTS| ✅ Win | 64%    | 55%     | +9.0% | 🏆 TIER 1| $30.00 | +$27.00
```

---

## Column Details

### Market Column (Market Type)
```
ML       = Moneyline (Team to win)
Spread   = Point spread (Team -/+ X points)
Total    = Over/Under points
Prop     = Player props (points, assists, rebounds, etc.)
```

### Pick Column (📍 The Actual Pick)
**This is the MOST IMPORTANT column**

**Examples:**
- Moneyline: `"Lakers"`, `"Boston Celtics"`, `"Denver Nuggets"`
- Spread: `"Lakers -5.5"`, `"Heat +3.5"`, `"Suns -7.0"`
- Total: `"Over 215.5"`, `"Under 210.0"`, `"Over 103.5"` (if lower-scoring game)
- Prop: `"Jayson Tatum O28.5 PTS"`, `"Luka Doncic O10.5 AST"`, `"Anthony Davis U11.5 REB"`

**Key feature:** Clearly shows WHAT was picked, not just team name

### Result Column (Outcome - VISUALLY PROMINENT)
```
✅ Win      — Pick won (green background)
❌ Loss     — Pick lost (red background)
⏳ Pending  — Not yet settled (blue background)
```

### Model%, Market%, Edge (Analysis Columns)
```
Model%   = Model's predicted probability
Market%  = Market's implied probability
Edge     = Model% - Market% (our predicted edge)
```

### Tier Column (Confidence Badge)
```
🏆 TIER 1  = High confidence (>5% edge, strong features)
🥇 TIER 2  = Medium confidence (3-5% edge)
🥈 TIER 3  = Low confidence (2-3% edge)
🥉 TIER 4  = Very low confidence (<2% edge)
```

### Stake & P&L (Sizing & Outcome)
```
Stake = Amount wagered (e.g., $25.00)
P&L   = Profit/Loss if settled, "-" if pending
```

---

## Visual Design Details

### Row Coloring (Visual Hierarchy)

**Win rows (✅):**
- Background: `rgba(16, 185, 129, 0.15)` (soft green)
- Instant visual feedback: "This one won"

**Loss rows (❌):**
- Background: `rgba(239, 68, 68, 0.15)` (soft red)
- Instant visual feedback: "This one lost"

**Pending rows (⏳):**
- Background: `rgba(99, 102, 241, 0.1)` (soft blue)
- Instant visual feedback: "Waiting for result"

### Column Widths (Visual Emphasis)

```
Date:     small   (8% width) — Just need timestamp
Market:   small   (8% width) — Just the type
Pick:     large   (25% width) — PRIMARY: What we bet on
Result:   small   (8% width) — Just the icon
Model%:   small   (10% width) — Right-aligned number
Market%:  small   (10% width) — Right-aligned number
Edge:     small   (10% width) — Right-aligned number
Tier:     small   (8% width) — Badge icon
Stake:    small   (8% width) — Right-aligned $ amount
P&L:      small   (10% width) — Right-aligned $
Total:    ~100%
```

### Typography (Data-Focused)

```
All numbers in JetBrains Mono (monospace)
- Easier column scanning
- Professional Bloomberg Terminal aesthetic
- Tabular figures align vertically

Pick column in Inter (sans-serif)
- More readable for text selections
- Distinguishes picks from metrics
```

---

## User Journey with Enhanced Table

**Scenario: User reviews picks from yesterday**

1. Opens dashboard
2. Scrolls to "Recent Picks" section
3. **Sees immediately:**
   - "01/10 | Spread | Lakers -5.5 | ✅ Win" — Green row
   - User knows: "I picked Lakers to beat the spread. It worked."
   
4. **Can dive deeper:**
   - Model: 58% | Market: 52% | Edge: +6.1%
   - Tier: 🥇 TIER 2 | Stake: $20 | P&L: +$18.50
   - User understands: "Model favored Lakers 6.1% over market. Medium confidence. Made $18.50."

5. **Compares to other picks:**
   - "01/10 | ML | Celtics | ❌ Loss" — Red row
   - Different market type, different outcome
   - Can see pattern: "Spread picks working better than moneyline"

---

## Implementation Changes

### Database Query (Enhanced)
```sql
SELECT 
    r.created_at,
    r.market,              -- NEW: market type
    r.selection,           -- EXISTING: the pick details
    ROUND(r.model_prob * 100, 1) as model_prob_pct,
    ROUND(r.market_prob * 100, 1) as market_prob_pct,
    ROUND(r.edge * 100, 2) as edge_pct,
    r.confidence_tier,
    r.stake_suggested as stake,
    CASE
        WHEN res.outcome_win_bool = 1 THEN '✅ Win'
        WHEN res.outcome_win_bool = 0 THEN '❌ Loss'
        ELSE '⏳ Pending'
    END as result,
    COALESCE(ROUND(res.profit_loss, 2), 0) as pnl
FROM recommendations r
LEFT JOIN results res ON r.id = res.recommendation_id
ORDER BY r.created_at DESC
```

### Column Configuration (Streamlit)
```python
column_config={
    "created_at": st.column_config.TextColumn("Date", width="small"),
    "market": st.column_config.TextColumn("Market", width="small"),
    "selection": st.column_config.TextColumn("📍 Pick", width="large"),
    "result": st.column_config.TextColumn("Result", width="small"),
    "model_prob_pct": st.column_config.NumberColumn("Model%", format="%.1f%%", width="small"),
    "market_prob_pct": st.column_config.NumberColumn("Market%", format="%.1f%%", width="small"),
    "edge_pct": st.column_config.NumberColumn("Edge", format="%.2f%%", width="small"),
    "confidence_tier": st.column_config.TextColumn("Tier", width="small"),
    "stake": st.column_config.NumberColumn("Stake", format="$%.2f", width="small"),
    "pnl": st.column_config.NumberColumn("P&L", format="$%.2f", width="small"),
}
```

---

## Why This Matters

**Current:** Shows only "Lakers" → User must check database to see if it was ML, spread, or prop  
**Enhanced:** Shows "Lakers -5.5" → User instantly knows exactly what was picked

**Current:** All 10 columns equal importance → User confused about what to focus on  
**Enhanced:** Pick column is 25% width → User immediately sees what was bet on

**Current:** Result buried in middle → User scrolls right to find outcome  
**Enhanced:** Result in column 4 → User sees outcome immediately after pick

**This is the core of decision support:** Clear, actionable information that shows:
- ✅ WHAT we picked
- ✅ HOW we picked it (probability)
- ✅ HOW it worked out (result)
- ✅ HOW MUCH it mattered ($)

---

**Status:** ✅ IMPLEMENTED in streamlit_app_enhanced.py  
**Version:** 1.0  
**Date:** January 10, 2026
