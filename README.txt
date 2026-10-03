RASOI DATA ANALYST TAKE-HOME — REVISED PACKAGE

What was changed
----------------
1. rasoi_analysis.py was rewritten into a simpler, function-based script with clear names and comments.
2. Cohort matching now uses an explicit campaign + next-calendar-day merge instead of relying on row position.
3. Added explicit checks for negative values, refunds > revenue, calendar gaps, revenue identity, funnel order, duplicates and missing values.
4. Kept the same core business logic, campaign metrics, rankings and ₹1 crore allocation.
5. The budget model is now described explicitly as a scenario/planning model, not a statistically estimated forecast.
6. The 0.6x–1.5x spend guardrail is explained as a planning constraint because the data does not support extrapolation far outside observed spend.
7. ShareChat is described operationally as a pause pending evidence, while still answering the assignment's requested campaign decision.
8. The founder chart wording was tightened and the campaign action label is “pause”.
9. The one-page recommendation and supporting answers were updated to match these changes.
10. Task 6 was updated to describe the revised validation and simplified implementation while keeping the original best prompt exactly as supplied.

Submission files
----------------
submission/
- rasoi_analysis.py
- Rasoi_one_page_recommendation.pdf
- Rasoi_supporting_answers.pdf
- Rasoi_chart.png
- Task6_AI_usage_notes.md
- Email_to_Propel.txt

analysis_outputs/
- campaign_summary.csv
- allocation_1cr.csv
- campaign_raw_totals.csv
- before_after_data_fix.csv
- dq_flagged_rows.csv
- chart_roas_vs_allocation.png

