"""Rasoi paid-growth analysis.

Run:
    python rasoi_analysis.py rasoi_growth_data.csv

The script uses simple sums, ratios and one stated planning assumption:
trials grow with spend to the power of 0.8. No machine learning is used.

Main steps:
1. Load and check the data
2. Find and flag the data-quality problem
3. Build day-D cohorts using day-D+1 renewals
4. Calculate campaign metrics and rankings
5. Allocate the next ₹1 crore
6. Run independent checks
7. Create the founder chart
"""

import os
import sys
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

# ----------------------------- settings -----------------------------
CSV_FILE = sys.argv[1] if len(sys.argv) > 1 else "rasoi_growth_data.csv"
OUTPUT_DIR = "analysis_outputs"
os.makedirs(OUTPUT_DIR, exist_ok=True)

BUDGET = 10_000_000                 # ₹1 crore
BETA = 0.8                          # planning assumption, not statistically estimated
KILL_CAMPAIGN = "sc_feed_video"
MIN_SPEND_MULTIPLIER = 0.60         # planning guardrail
MAX_SPEND_MULTIPLIER = 1.50         # planning guardrail
STEP = 1_000                         # allocate budget in ₹1,000 steps

CAMPAIGN_NAMES = {
    "mt_retarget_paywall": "Meta retargeting",
    "gg_uac_actions": "Google UAC (actions)",
    "mt_broad_aoa": "Meta broad",
    "gg_uac_installs": "Google UAC (installs)",
    "mt_lookalike_3pct": "Meta lookalike 3%",
    "sc_feed_video": "ShareChat video",
}


# ----------------------------- helpers -----------------------------
def load_data(path):
    """Load and sort the raw CSV. The raw values are never changed."""
    data = pd.read_csv(path, parse_dates=["date"])
    return data.sort_values(["campaign", "date"]).reset_index(drop=True)


def check_data(data):
    """Run simple data-quality checks and print the results."""
    print("STEP 1 — DATA CHECKS")
    print("Rows × columns:", data.shape)
    print("Date range:", data["date"].min().date(), "to", data["date"].max().date())
    print("Campaigns:", data["campaign"].nunique())
    print("Channels:", data["channel"].nunique())
    print("Missing cells:", int(data.isna().sum().sum()))
    print("Duplicate rows:", int(data.duplicated().sum()))
    print("Duplicate date + campaign:", int(data.duplicated(["date", "campaign"]).sum()))

    # Revenue identity from the brief's plan prices.
    monthly_renewals = data["renewals"] - data["annual_renewals"]
    expected_revenue = (
        data["trials"] * 1
        + monthly_renewals * 199
        + data["annual_renewals"] * 1199
    )
    print("Revenue identity failures:", int((data["revenue_inr"] != expected_revenue).sum()))

    # Funnel order checks.
    print("Clicks > impressions:", int((data["clicks"] > data["impressions"]).sum()))
    print("Installs > clicks:", int((data["installs"] > data["clicks"]).sum()))
    print("Trials > installs:", int((data["trials"] > data["installs"]).sum()))
    print("Renewals > trials:", int((data["renewals"] > data["trials"]).sum()))
    print("Annual renewals > renewals:", int((data["annual_renewals"] > data["renewals"]).sum()))

    numeric_columns = [
        "spend_inr", "impressions", "clicks", "installs", "trials",
        "renewals", "annual_renewals", "revenue_inr", "refunds_inr"
    ]
    print("Negative numeric values:", int((data[numeric_columns] < 0).sum().sum()))
    print("Refunds > revenue:", int((data["refunds_inr"] > data["revenue_inr"]).sum()))

    # Each campaign should have consecutive daily observations.
    gaps = data.groupby("campaign")["date"].diff().dt.days
    print("Calendar gaps > 1 day:", int((gaps > 1).sum()))

    print("Numeric min/max:")
    print(data[numeric_columns].agg(["min", "max"]).T)


def find_data_problem(data):
    """Flag days where trials/install are less than 25% of that campaign's normal level."""
    data = data.copy()
    data["trials_per_install"] = data["trials"] / data["installs"]
    normal_ratio = data.groupby("campaign")["trials_per_install"].transform("median")
    data["trial_rate_vs_normal"] = data["trials_per_install"] / normal_ratio
    data["data_quality_flag"] = data["trial_rate_vs_normal"] < 0.25

    flagged = data[data["data_quality_flag"]].copy()
    flagged.to_csv(os.path.join(OUTPUT_DIR, "dq_flagged_rows.csv"), index=False)

    print("\nSTEP 2 — DATA PROBLEM")
    print("Flagged rows:", len(flagged))
    print("Campaigns:", list(flagged["campaign"].unique()))
    print("Dates:", flagged["date"].min().date(), "to", flagged["date"].max().date())
    print("Flagged rows are kept in raw data but excluded from cohort performance ratios.")
    print("No values are deleted, interpolated or silently replaced.")

    return data, flagged


def build_cohorts(data):
    """Attach day-D+1 outcomes to each day-D acquisition cohort."""
    next_day = data[[
        "campaign", "date", "trials", "renewals", "annual_renewals",
        "revenue_inr", "refunds_inr", "data_quality_flag"
    ]].copy()

    # Move tomorrow's row back one day, so it lines up with today's cohort.
    next_day["date"] = next_day["date"] - pd.Timedelta(days=1)
    next_day = next_day.rename(columns={
        "trials": "next_day_trials",
        "renewals": "paying_users",
        "annual_renewals": "annual_users",
        "revenue_inr": "next_day_revenue",
        "refunds_inr": "next_day_refunds",
        "data_quality_flag": "next_day_bad",
    })

    cohorts = data.merge(next_day, on=["campaign", "date"], how="left")

    # Tomorrow's revenue includes tomorrow's ₹1 trial fee. Remove it because
    # that trial belongs to tomorrow, not to today's acquisition cohort.
    cohorts["plan_revenue"] = cohorts["next_day_revenue"] - cohorts["next_day_trials"]

    # Use only mature cohorts where both day D and day D+1 are clean.
    usable = (
        cohorts["paying_users"].notna()
        & ~cohorts["data_quality_flag"].astype("boolean").fillna(False)
        & ~cohorts["next_day_bad"].astype("boolean").fillna(False)
    )

    return cohorts[usable].copy(), cohorts


def campaign_metrics(cohorts):
    """Aggregate cohort rows, then calculate the campaign economics."""
    summary = cohorts.groupby("campaign").agg(
        spend=("spend_inr", "sum"),
        impressions=("impressions", "sum"),
        clicks=("clicks", "sum"),
        installs=("installs", "sum"),
        trials=("trials", "sum"),
        paying_users=("paying_users", "sum"),
        annual_users=("annual_users", "sum"),
        plan_revenue=("plan_revenue", "sum"),
        refunds=("next_day_refunds", "sum"),
    )

    summary["net_revenue"] = summary["trials"] + summary["plan_revenue"] - summary["refunds"]
    summary["cpi"] = summary["spend"] / summary["installs"]
    summary["cost_per_trial"] = summary["spend"] / summary["trials"]
    summary["cac"] = summary["spend"] / summary["paying_users"]
    summary["trial_to_paid"] = summary["paying_users"] / summary["trials"]
    summary["annual_mix"] = summary["annual_users"] / summary["paying_users"]
    summary["net_roas"] = summary["net_revenue"] / summary["spend"]
    summary["net_revenue_per_trial"] = summary["net_revenue"] / summary["trials"]

    return summary


def rank_campaigns(summary):
    """Create the two requested campaign rankings."""
    summary = summary.copy()
    summary["rank_cost_per_trial"] = summary["cost_per_trial"].rank(method="min").astype(int)
    summary["rank_net_roas"] = summary["net_roas"].rank(ascending=False, method="min").astype(int)
    return summary


def get_current_run_rate(cohorts):
    """Use the last 28 clean acquisition days and scale them to 30 days."""
    last_date = cohorts["date"].max()
    recent = cohorts[cohorts["date"] > last_date - pd.Timedelta(days=28)]
    recent = recent.groupby("campaign")[["spend_inr", "trials"]].sum()
    return recent["spend_inr"] * 30 / 28, recent["trials"] * 30 / 28


def expected_revenue(campaign, new_spend, current_spend, current_trials, summary):
    """Model first-month net revenue under the stated 0.8 response assumption."""
    if new_spend <= 0:
        return 0.0

    expected_trials = current_trials[campaign] * (
        new_spend / current_spend[campaign]
    ) ** BETA
    return expected_trials * summary.loc[campaign, "net_revenue_per_trial"]


def allocate_budget(summary, current_spend, current_trials):
    """Allocate ₹1 crore with transparent 0.6x–1.5x spend guardrails."""
    live = [c for c in summary.index if c != KILL_CAMPAIGN]

    proposed = {}
    for campaign in summary.index:
        if campaign == KILL_CAMPAIGN:
            proposed[campaign] = 0
        else:
            floor = MIN_SPEND_MULTIPLIER * current_spend[campaign]
            proposed[campaign] = round(floor / STEP) * STEP

    while sum(proposed.values()) < BUDGET:
        best_campaign = None
        best_incremental_revenue = -1

        for campaign in live:
            next_spend = proposed[campaign] + STEP
            cap = MAX_SPEND_MULTIPLIER * current_spend[campaign]
            if next_spend > cap:
                continue

            gain = (
                expected_revenue(campaign, next_spend, current_spend, current_trials, summary)
                - expected_revenue(campaign, proposed[campaign], current_spend, current_trials, summary)
            )

            if gain > best_incremental_revenue:
                best_incremental_revenue = gain
                best_campaign = campaign

        if best_campaign is None:
            raise ValueError("The budget cannot be allocated within the chosen spend guardrails.")

        proposed[best_campaign] += STEP

    allocation = pd.DataFrame({
        "current_spend": current_spend,
        "proposed_spend": pd.Series(proposed),
    })

    allocation["expected_trials"] = 0.0
    for campaign in allocation.index:
        if allocation.loc[campaign, "proposed_spend"] > 0:
            allocation.loc[campaign, "expected_trials"] = (
                current_trials[campaign]
                * (allocation.loc[campaign, "proposed_spend"] / current_spend[campaign]) ** BETA
            )

    allocation["expected_paying_users"] = (
        allocation["expected_trials"] * summary["trial_to_paid"]
    )
    allocation["expected_net_revenue"] = (
        allocation["expected_trials"] * summary["net_revenue_per_trial"]
    )

    assert allocation["proposed_spend"].sum() == BUDGET
    return allocation


def validation_checks(data, cohorts, summary, allocation, current_spend, current_trials):
    """Run independent checks on the most important calculations."""
    print("\nSTEP 6 — INDEPENDENT CHECKS")

    # Check 1: explicit day-by-day cohort calculation.
    for campaign in summary.index:
        rows = data[data["campaign"] == campaign].set_index("date")
        paying = 0
        spend = 0
        net_revenue = 0

        for date in rows.index:
            next_date = date + pd.Timedelta(days=1)
            if next_date not in rows.index:
                continue
            if rows.loc[date, "data_quality_flag"] or rows.loc[next_date, "data_quality_flag"]:
                continue

            paying += rows.loc[next_date, "renewals"]
            spend += rows.loc[date, "spend_inr"]
            plan_revenue = rows.loc[next_date, "revenue_inr"] - rows.loc[next_date, "trials"]
            net_revenue += rows.loc[date, "trials"] + plan_revenue - rows.loc[next_date, "refunds_inr"]

        assert paying == summary.loc[campaign, "paying_users"]
        assert abs(net_revenue / spend - summary.loc[campaign, "net_roas"]) < 1e-9

    print("Check 1 passed: independent day-by-day cohort calculation matches summary.")

    # Check 2: compare with same-day matching as a diagnostic only.
    clean = data[~data["data_quality_flag"]].groupby("campaign").agg(
        spend=("spend_inr", "sum"),
        trials=("trials", "sum"),
        renewals=("renewals", "sum"),
        revenue=("revenue_inr", "sum"),
        refunds=("refunds_inr", "sum"),
    )
    same_day_t2p = clean["renewals"] / clean["trials"]
    same_day_roas = (clean["revenue"] - clean["refunds"]) / clean["spend"]

    print(
        "Check 2: same-day vs previous-day matching changes trial→paid by at most %.4f "
        "and ROAS by at most %.4f."
        % (
            (same_day_t2p - summary["trial_to_paid"]).abs().max(),
            (same_day_roas - summary["net_roas"]).abs().max(),
        )
    )
    print(
        "          ROAS ranking unchanged:",
        list(same_day_roas.rank(ascending=False).astype(int))
        == list(summary["rank_net_roas"]),
    )

    # Check 3: sensitivity to the planning exponent.
    old_split = summary["spend"] / summary["spend"].sum() * BUDGET
    print("Check 3: sensitivity to diminishing-returns exponent")
    for beta in [0.6, 0.8, 1.0]:
        new_revenue = 0
        old_revenue = 0
        for campaign in summary.index:
            if campaign != KILL_CAMPAIGN:
                new_trials = current_trials[campaign] * (
                    allocation.loc[campaign, "proposed_spend"] / current_spend[campaign]
                ) ** beta
                new_revenue += new_trials * summary.loc[campaign, "net_revenue_per_trial"]

            old_trials = current_trials[campaign] * (
                old_split[campaign] / current_spend[campaign]
            ) ** beta
            old_revenue += old_trials * summary.loc[campaign, "net_revenue_per_trial"]

        improvement = (new_revenue / old_revenue - 1) * 100
        print(f"  beta={beta:.1f}: new ₹{new_revenue/1e5:.1f}L vs old ₹{old_revenue/1e5:.1f}L ({improvement:+.1f}%)")

    assert allocation["proposed_spend"].sum() == BUDGET
    print("Check 4 passed: proposed spend totals exactly ₹1 crore.")


def make_chart(summary, allocation):
    """Create the single founder-facing chart."""
    order = summary.sort_values("net_roas").index

    colors = []
    for campaign in order:
        if campaign == KILL_CAMPAIGN:
            colors.append("#c0392b")
        elif allocation.loc[campaign, "proposed_spend"] > allocation.loc[campaign, "current_spend"]:
            colors.append("#1f7a4d")
        else:
            colors.append("#7f8c8d")

    fig, ax = plt.subplots(figsize=(8.6, 4.9), dpi=200)
    ax.barh(range(len(order)), summary.loc[order, "net_roas"], color=colors, height=0.6)
    ax.axvline(1.0, color="black", linestyle="--", linewidth=1)
    ax.text(1.0, len(order) - 0.45, " break-even", fontsize=8.5)

    ax.set_yticks(range(len(order)))
    ax.set_yticklabels([CAMPAIGN_NAMES[c] for c in order], fontsize=10.5)

    for i, campaign in enumerate(order):
        roas = summary.loc[campaign, "net_roas"]
        label = (
            f"₹{allocation.loc[campaign, 'current_spend']/1e5:.0f}L → "
            f"₹{allocation.loc[campaign, 'proposed_spend']/1e5:.0f}L"
        )
        if campaign == KILL_CAMPAIGN:
            label += "  (pause)"

        ax.text(roas + 0.02, i, f"₹{roas:.2f}", va="center", fontsize=10, fontweight="bold")
        ax.text(1.32, i, label, va="center", fontsize=10)

    ax.set_xlim(0, 2.0)
    ax.set_xticks([0, 0.5, 1.0])
    ax.set_xlabel(
        "First-month net revenue earned back per ₹1 of ad spend",
        loc="left",
    )
    ax.set_title(
        "Proposed budget shifts toward higher first-month net ROAS",
        loc="left", fontsize=12, fontweight="bold"
    )
    ax.text(
        0, 1.02,
        "Cost per trial alone gives a different ranking.",
        transform=ax.transAxes,
        fontsize=9,
    )
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    fig.text(
        0.01, 0.01,
        "Green = spend up, grey = spend down, red = pause. 90-day cohorts; ₹L = ₹ lakh. Source: rasoi_growth_data.csv",
        fontsize=7.5, color="#555555"
    )
    plt.tight_layout(rect=(0, 0.03, 1, 0.94))

    path = os.path.join(OUTPUT_DIR, "chart_roas_vs_allocation.png")
    fig.savefig(path, bbox_inches="tight")
    plt.close(fig)
    return path


# ----------------------------- main analysis -----------------------------
print("Loading:", CSV_FILE)
data = load_data(CSV_FILE)
check_data(data)

data, flagged = find_data_problem(data)
cohorts, all_cohorts = build_cohorts(data)
summary = campaign_metrics(cohorts)
summary = rank_campaigns(summary)

print("\nSTEP 3 — CAMPAIGN METRICS")
print(summary[[
    "spend", "installs", "trials", "paying_users", "cpi",
    "cost_per_trial", "cac", "trial_to_paid", "annual_mix", "net_roas"
]].round(3))

print("\nSTEP 4 — RANKINGS")
print(summary[[
    "cost_per_trial", "rank_cost_per_trial", "cac", "net_roas", "rank_net_roas"
]].sort_values("rank_cost_per_trial").round(3))

current_spend, current_trials = get_current_run_rate(cohorts)
allocation = allocate_budget(summary, current_spend, current_trials)

print("\nSTEP 5 — ₹1 CRORE ALLOCATION")
print(allocation.round(0))
print("Total proposed spend:", allocation["proposed_spend"].sum())

validation_checks(data, cohorts, summary, allocation, current_spend, current_trials)
chart_path = make_chart(summary, allocation)

# ----------------------------- save outputs -----------------------------
summary.round(4).to_csv(os.path.join(OUTPUT_DIR, "campaign_summary.csv"))

raw_totals = data.groupby("campaign")[[
    "spend_inr", "impressions", "clicks", "installs", "trials", "renewals",
    "annual_renewals", "revenue_inr", "refunds_inr"
]].sum()
raw_totals["net_revenue"] = raw_totals["revenue_inr"] - raw_totals["refunds_inr"]
raw_totals.to_csv(os.path.join(OUTPUT_DIR, "campaign_raw_totals.csv"))

allocation.round(1).to_csv(os.path.join(OUTPUT_DIR, "allocation_1cr.csv"))

# Show how much the flagged Google days change the main metrics.
with_bad = all_cohorts[all_cohorts["paying_users"].notna()].groupby("campaign").agg(
    spend=("spend_inr", "sum"),
    trials=("trials", "sum"),
    paying_users=("paying_users", "sum"),
    plan_revenue=("plan_revenue", "sum"),
    refunds=("next_day_refunds", "sum"),
)
before_after = pd.DataFrame(index=summary.index)
before_after["cost_per_trial_with_bad_days"] = with_bad["spend"] / with_bad["trials"]
before_after["cost_per_trial_clean"] = summary["cost_per_trial"]
before_after["cac_with_bad_days"] = with_bad["spend"] / with_bad["paying_users"]
before_after["cac_clean"] = summary["cac"]
before_after["roas_with_bad_days"] = (
    with_bad["trials"] + with_bad["plan_revenue"] - with_bad["refunds"]
) / with_bad["spend"]
before_after["roas_clean"] = summary["net_roas"]
before_after.round(4).to_csv(os.path.join(OUTPUT_DIR, "before_after_data_fix.csv"))

print("\nSaved outputs to:", OUTPUT_DIR)
print("Chart:", chart_path)
