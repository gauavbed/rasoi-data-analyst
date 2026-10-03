# Task 6 — How I used AI

## Tools and what each was used for
**Claude (Anthropic), in one long working session. No other AI tool was used.**

| Use | Done with Claude? | Detail |
|---|---|---|
| Data exploration | Yes | Profiling in pandas: shape, ranges, missing values, duplicates, funnel-order checks, revenue identity (`revenue = trials×1 + monthly renewals×199 + annual renewals×1199`, holds on all 540 rows), per-campaign ratio ranges. |
| SQL / Python | Yes | One reproducible Python script (`rasoi_analysis.py`) plus a PDF builder. An explicit date-based cohort merge plus a plain-loop recomputation independently re-derives the cohort metrics. |
| Cleaning | Yes | The one data problem was flagged, not deleted or interpolated; raw data is never modified. |
| Calculations | Yes | Cohort-aligned metrics, rankings, ₹1 crore allocation, sensitivity to the diminishing-returns assumption. |
| Charting | Yes | One matplotlib chart, exported as PNG and placed in the one-pager. |
| Writing | Yes | Recommendation page and these notes. |
| Checking | Yes | Plain-loop recomputation of paying users and net ROAS for all 6 campaigns, explicit data-quality checks, budget assert (exactly ₹1,00,00,000), comparison with same-day renewal matching, and sensitivity to the diminishing-returns exponent (0.6 to 1.0). |

No machine learning was used.

## Who did what (my role versus Claude's)
Claude did most of the hands-on implementation: it wrote the initial Python, ran the profiling and calculations, proposed the diagnosis of the data problem, the choice of first-month net ROAS as the steering metric, the 0.8 diminishing-returns assumption, the allocation and the ShareChat pause, and drafted the documents.

My role was to set the analytical requirements and standards: I uploaded the brief and CSV and wrote the prompt below, constrained the work to the supplied sources, challenged the conclusions, asked for independent checks, reviewed the results, asked for the code to be simplified and made more robust, and decided what was defensible to submit.

I would rather be clear about the extent of AI assistance than overstate my implementation work. In the final review I asked for every number and claim in every document to be re-verified against the CSV, and that review produced the corrections described below.

## My single best prompt (exactly as sent)

```
You are helping me complete a real Data Analyst Intern take-home assignment.

I have uploaded two files:

1. `Propel_Spark_Data_Analyst_Intern_Assignment.pdf` — the official assignment brief.
2. `rasoi_growth_data.csv` — the dataset provided with the assignment.

Your job is to help me complete the assignment END-TO-END, but you must behave like a careful senior data analyst, not like a generic AI assistant.

IMPORTANT RULES:

- Use ONLY the information contained in the assignment PDF and CSV unless I explicitly ask for outside research.
- Do not invent facts, assumptions, campaign results, business context, or data.
- Do not use machine learning. The assignment explicitly says ML is unnecessary.
- Do not silently fix data problems.
- Every important conclusion must be traceable to the CSV and/or calculations.
- If something is ambiguous, explicitly identify the ambiguity and explain what clarification would be needed.
- Prefer transparent calculations over complicated methods.
- Check your own calculations independently.
- Be especially careful about the assignment's warning that renewals belong to the trial started the previous day.
- Do not calculate misleading same-day ratios when the correct cohort relationship is required.
- Do not simply agree with the data or with your own first conclusion. Actively look for errors and contradictions.
- The final recommendation must be understandable to a founder who does not see the SQL/Python code.

The assignment has six tasks. Complete them in this order.

==================================================
TASK 1 — DATA TRUST / PROFILING
==================================================

First inspect the CSV thoroughly.

Report:

- Number of rows
- Number of columns
- Date range
- Unique campaigns
- Unique channels
- Data types
- Missing values by column
- Duplicate rows
- Minimum / maximum / suspicious values
- Impossible or implausible relationships
- Any unexpected combinations
- Any suspicious dates or campaign records
- Basic consistency checks between spend, impressions, clicks, installs, trials, renewals, annual renewals, revenue and refunds.

The assignment says there is ONE real problem in the file.

Find it.

For the suspected problem:

1. Identify exactly what is wrong.
2. Explain what you think happened.
3. Identify the exact affected rows/date/campaign/channel.
4. Explain how you detected it.
5. Decide whether the affected records should be:
   - dropped,
   - flagged,
   - interpolated,
   - or left unchanged.
6. Explain why.
7. Show the before/after impact on the relevant analysis if applicable.

Do NOT manufacture a data-quality issue just because something looks unusual. Distinguish between a genuine error and a merely unusual but possible value.

Also list any additional information you would ask an engineer for before putting real money behind the recommendation.

==================================================
TASK 2 — SIX CAMPAIGN ANALYSIS
==================================================

Create one row per campaign covering the FULL 90-day period.

Calculate at minimum:

1. Cost per install
2. Cost per trial
3. CAC per paying user
4. Trial-to-paid %
5. Annual plan mix
6. First-month ROAS, net of refunds

Define every metric clearly.

Be extremely careful with denominators.

Important assignment rule:

A renewal on any given day belongs to the trial started the previous day.

Therefore, do NOT blindly divide same-day renewals by same-day trials.

Explain the correct logic and implement it correctly.

For each campaign calculate:

- Total spend
- Total impressions
- Total clicks
- Total installs
- Total trials
- Total renewals
- Total annual renewals
- Total revenue
- Total refunds
- Net revenue
- CPI
- Cost per trial
- Paying users
- CAC
- Trial-to-paid %
- Annual plan mix
- First-month net ROAS

Where appropriate, show the formulas.

Create a clean campaign summary table.

==================================================
TASK 3 — WHICH CAMPAIGNS ACTUALLY WORK?
==================================================

First rank all six campaigns by cost per trial.

Then rank them again using the metric you believe is actually more useful for business decision-making.

Do NOT automatically choose the metric that produces the most attractive ranking.

Explain:

- What cost per trial tells us.
- What it misses.
- What the better decision metric captures.
- Whether the campaign ranking changes.
- Why the ranking changes, if it does.
- Whether the cheap-looking campaign is a trap.
- Explain this in plain language suitable for a founder.

Then nominate ONE metric that the team should steer on week-to-week.

Defend that metric in exactly three concise sentences.

Do not assume what the company wants to hear. Make the argument from the data.

==================================================
TASK 4 — ₹1 CRORE BUDGET ALLOCATION
==================================================

The next month's total paid-media budget is:

₹1,00,00,000

Create a proposed allocation across all six campaigns.

The output must contain:

Campaign
- Proposed spend
- Expected trials
- Expected paying users
- Expected first-month revenue

The six campaign spends must add up exactly to:

₹1,00,00,000

Explain the allocation methodology.

Consider:

- Historical performance
- Trial efficiency
- Paying-user efficiency
- Revenue / ROAS
- Annual-plan mix
- Refunds
- Campaign differences
- Diminishing returns at higher spend

The assignment explicitly asks us to decide whether we believe diminishing returns exist.

Do NOT pretend we know the exact future response curve if the historical data cannot support it.

If the dataset does not contain enough evidence to estimate a reliable saturation curve, say so clearly and use a transparent assumption instead.

State every important assumption.

For expected trials, paying users and revenue, show the formulas/methodology.

Then:

1. Name ONE campaign you would kill.
2. Explain the evidence behind that decision.
3. State exactly what future evidence would prove you wrong.

Finally, choose ONE headline number for the entire budget plan.

Explain why that number is the most useful headline KPI.

==================================================
TASK 5 — ONE FOUNDER-FRIENDLY CHART
==================================================

Create exactly ONE chart.

It must be understandable within approximately 10 seconds.

The chart should directly support the main budget/recommendation decision.

Do NOT create a dashboard.

Choose the chart type based on the actual data.

Possible examples include:

- campaign efficiency comparison,
- historical efficiency vs proposed allocation,
- cost per trial vs revenue efficiency,
- spend allocation vs expected return,

but choose whichever is genuinely supported by the analysis.

Do not force a chart type.

The chart must:

- Have a clear title.
- Have readable labels.
- Use appropriate units.
- Avoid unnecessary decoration.
- Make the business implication obvious.
- Not mislead through inappropriate axes or scales.

Under the chart, write ONE sentence telling the founder what action/decision the chart supports.

Also save/export the chart as an image that can be submitted separately.

==================================================
TASK 6 — AI USAGE
==================================================

The assignment explicitly asks me to show how I used AI.

Create a concise AI-usage section containing:

1. Which AI tool(s) were used.
2. What each tool was used for.
3. Whether it was used for:
   - data exploration,
   - SQL/Python,
   - cleaning,
   - calculations,
   - charting,
   - writing,
   - checking.
4. My single best prompt.

IMPORTANT:

The "single best prompt" must be reproduced EXACTLY as I sent it to you.

Do not rewrite it.

Then identify ONE thing you got wrong during the analysis.

This is mandatory.

Find a genuine example such as:

- wrong data grain,
- wrong denominator,
- wrong cohort relationship,
- unsupported conclusion,
- incorrect calculation,
- misleading chart,
- incorrect assumption.

Explain:

1. What you initially got wrong.
2. Why it was wrong.
3. How I could catch it.
4. What was changed.

Do NOT invent a fake mistake simply to satisfy the assignment.

If you have not actually made a mistake, deliberately perform additional independent validation checks and identify a real weakness or potential failure mode in the initial analysis rather than falsely claiming an error.

==================================================
VALIDATION / SELF-CHECK
==================================================

Before producing the final answer, independently validate everything.

Check:

- Row counts
- Campaign counts
- Date range
- Missing values
- Duplicate rows
- The identified data-quality issue
- All metric denominators
- Trial-to-paid calculations
- Previous-day renewal relationship
- Revenue calculations
- Refund calculations
- ROAS calculations
- Campaign rankings
- Budget totals
- Proposed spend totals
- Expected trial calculations
- Expected paying-user calculations
- Expected revenue calculations
- ₹1 crore allocation
- Chart data
- Chart interpretation

Perform at least TWO independent sanity checks on the most important calculations.

If two methods disagree, stop and investigate before producing the final recommendation.

==================================================
FINAL DELIVERABLES
==================================================

I need the analysis structured so I can submit the assignment exactly according to the brief.

Produce these outputs:

DELIVERABLE 1 — WORKING ANALYSIS

Create a clean, reproducible Python analysis.

It should:

- Load `rasoi_growth_data.csv`
- Clean/process only where justified
- Perform the data-quality checks
- Calculate all required metrics
- Produce campaign rankings
- Produce the ₹1 crore allocation
- Generate the final chart
- Clearly separate raw data, cleaned data, calculations and outputs where practical.

Use clear variable names and comments.

The analysis must be rerunnable from the original CSV.

DELIVERABLE 2 — ONE-PAGE RECOMMENDATION

Draft a concise one-page recommendation document.

Follow the exact priority requested in the assignment:

1. RECOMMENDATION FIRST
2. EVIDENCE SECOND
3. CAVEATS LAST

The page should contain:

- Executive recommendation
- Proposed ₹1 crore allocation
- Key campaign decision
- One headline KPI
- Key evidence
- Main data-quality issue and treatment
- Key assumptions
- Important caveats
- One founder-friendly chart

Keep it concise enough to genuinely fit on one page.

Do not fill the page with technical explanations.

DELIVERABLE 3 — CHART

Provide the final chart as a separate image as well as a version that can be placed inside the one-page recommendation.

DELIVERABLE 4 — AI USAGE NOTES

Provide the Task 6 response separately so I can include it in the final submission if appropriate.

==================================================
IMPORTANT OUTPUT FORMAT
==================================================

First give me:

A. Data-quality finding
B. Campaign performance table
C. Campaign ranking by cost per trial
D. Campaign ranking by recommended decision metric
E. Recommended week-to-week metric
F. ₹1 crore allocation table
G. Campaign to kill + evidence
H. Headline KPI
I. Chart recommendation
J. AI usage + genuine model error

Then give me:

K. Complete reproducible Python code

Then:

L. One-page recommendation document text

Then:

M. Exact Task 6 AI-usage section

Then:

N. Final submission checklist

Do not skip any calculation.

Do not fabricate anything.

If the data does not support a conclusion, explicitly say:
"Not supported by the available data."

Most importantly, behave like a careful analyst whose work will be reviewed by another analyst. Accuracy, correct grain, correct denominators, transparent assumptions and independent validation are more important than producing a confident-looking answer.
```

## One thing the model got wrong
**Confident claims in the drafted documents that the data did not support.** The model wrote them fluently and they read as plausible. I only found them when I asked for every number and claim in every document to be re-checked against the CSV.

**What it got wrong, with the correct version:**
- The one-pager said ShareChat would need “~75% more” revenue per trial to match Meta broad. The correct figure is about 70% (ROAS 0.588 ÷ 0.343 = 1.71).
- A draft defence of the weekly metric said net ROAS leads “persist week to week”. Weekly ROAS had never been computed. That claim was removed.
- The one-pager said retargeting’s ROAS “is likely partly non-incremental”. Nothing in the file measures incrementality, so it now says “may include people who would have bought anyway”.
- The write-up said cost per trial rising 8–20% “fits saturation”. When I checked, it rose by about the same amount where spend grew 8% (ShareChat, +18%) as where it grew 76% (lookalike, +20%), so the rise may be creative fatigue or price drift, not saturation. The text now says the data cannot tell which.
- Two ranges (“60–100 renewals”, “₹30,000–45,000”) were written from a rough impression of the data. I replaced them with the real figures: flagged days had 3–5 renewals and ₹608–2,009 revenue, against typical medians of about 73–80 renewals and ₹31,000–35,000.

**Why it was wrong.** The model produced numbers and explanations from memory of earlier results instead of recomputing them. Each one sounded reasonable, which is what makes this failure easy to miss.

**How it was caught.** A line-by-line re-verification of every figure in the documents against the CSV: dividing the ROAS figures, recomputing weekly spend and cost per trial for each campaign, and recomputing the flagged-day ranges.

**What changed.** All of the statements above were corrected in the one-page recommendation and the supporting answers, and the one-pager was rebuilt and checked to still fit on one page.

## A second, related weakness: an untested rule
The script’s cohort logic follows the brief’s rule that a renewal belongs to the previous day’s trial, and I first treated that rule as something visible in the file without testing it. When tested, renewals tracked same-day trials (correlation 0.83–0.94) and barely tracked previous-day trials (0.01–0.14; 0.54 for the ramping lookalike campaign). I kept the brief’s rule as the main method, because the brief says to treat it as true, and added a same-day comparison as a check: it changes trial-to-paid by at most 0.0014, CAC by at most ₹6 and ROAS by at most 0.004, and no ranking changes. The question for engineering is listed in the email.

## Smaller catches
The first chart draft had a clipped title and a break-even line running through the labels; I found it by viewing the PNG and rebuilt the layout. After simplifying the code, I also re-ran the full script from the original CSV and checked that the campaign metrics, allocation total and sensitivity outputs still matched the earlier validated results.

## A weakness in the analysis itself
The 19–24 July problem is not reliably detectable from trial-to-paid alone because both trials and next-day renewals collapse together. It is much clearer in installs→trials and the resulting cost metrics. The revised script now includes explicit funnel, revenue-identity, negative-value, refund, duplicate and calendar-gap checks so a conversion-ratio check is not the only data-quality defense.
