import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

# ===================================================
# PAGE CONFIG
# ===================================================

st.set_page_config(
    page_title="Ryan Financial Intelligence System",
    layout="wide"
)

st.title("Ryan Financial Intelligence System")

# ===================================================
# ACCOUNTING FORMAT
# ===================================================

def acct_format(amount):

    return f"{amount:,.2f}"

# ===================================================
# LOAD DATA
# ===================================================

@st.cache_data
def load_data():

    df = pd.read_excel(
        "Interactive Project Data 01 vSafe.xlsx"
    )

    df["Date"] = pd.to_datetime(
        df["Date"]
    )

    df["YearMonth"] = df["Date"].dt.to_period("M").astype(str)
    
    return df
    


df = load_data()

month_options = sorted(df["YearMonth"].dropna().unique())


# ===================================================
# SANKEY BUILDER
# ===================================================

def build_pl_sankey(pl_df):

    pl_df = pl_df.copy()

    pl_df["Display Amount"] = (
        pl_df["RMB Amount"] * -1
    )

    def fsli_sum(fsli_name):

        return pl_df.loc[
            pl_df["FSLI"] == fsli_name,
            "Display Amount"
        ].sum()

    def section_sum(section_name):

        return pl_df.loc[
            pl_df["PL Section"] == section_name,
            "Display Amount"
        ].sum()

    def add_link(source, target, amount):

        if amount != 0:

            links.append({
                "Source": source,
                "Target": target,
                "Amount": abs(amount)
            })

    # ---------------------------------------------------
    # BASIC TOTALS
    # ---------------------------------------------------

    revenue = section_sum("Revenues")
    costs = section_sum("Costs")
    expenses = section_sum("Expenses")

    gross_profit = revenue + costs
    operating_income = gross_profit + expenses

    # ---------------------------------------------------
    # ITEM LISTS
    # ---------------------------------------------------

    revenue_items = [
        "Salaries & bonuses",
        "Subsidies",
        "H-Fund Take"
    ]

    cost_items = [
        "Food",
        "Apartment rental costs",
        "Utilities",
        "Studies",
        "Healthcare",
        "Haircut & Clothes"
    ]

    expense_items = [
        "Travel & Hotel",
        "Social & Entertainment",
        "Goods & Services",
        "Family"
    ]

    other_net_items = [
        "FinExp - general",
        "FinExp - exchange",
        "FinExp - unrealised exchange",
        "Investment income"
    ]

    oci_items = [
        "H-Fund keep",
        "Medical insurance keep"
    ]

    # ---------------------------------------------------
    # OTHER / OCI POSITIVE AND NEGATIVE PARTS
    # ---------------------------------------------------

    other_positive = 0
    other_negative = 0

    for item in other_net_items:

        amount = fsli_sum(item)

        if amount >= 0:
            other_positive += amount
        else:
            other_negative += abs(amount)

    net_income = (
        operating_income
        + other_positive
        - other_negative
    )

    oci_positive = 0
    oci_negative = 0

    for item in oci_items:

        amount = fsli_sum(item)

        if amount >= 0:
            oci_positive += amount
        else:
            oci_negative += abs(amount)

    comprehensive_income = (
        net_income
        + oci_positive
        - oci_negative
    )

    # ---------------------------------------------------
    # LINKS
    # ---------------------------------------------------

    links = []

    # ---------------------------------------------------
    # REVENUES → REVENUES NODE
    # ---------------------------------------------------

    for item in revenue_items:

        add_link(
            item,
            "Revenues",
            fsli_sum(item)
        )

    # ---------------------------------------------------
    # REVENUES → COSTS → COST ITEMS / GROSS PROFIT
    # ---------------------------------------------------

    add_link(
        "Revenues",
        "Costs",
        costs
    )

    for item in cost_items:

        add_link(
            "Costs",
            item,
            fsli_sum(item)
        )

    add_link(
        "Revenues",
        "Gross profit/(loss)",
        gross_profit
    )

    # ---------------------------------------------------
    # GROSS PROFIT → EXPENSES → EXPENSE ITEMS / OPERATING INCOME
    # ---------------------------------------------------

    add_link(
        "Gross profit/(loss)",
        "Expenses",
        expenses
    )

    for item in expense_items:

        add_link(
            "Expenses",
            item,
            fsli_sum(item)
        )

    add_link(
        "Gross profit/(loss)",
        "Operating income/(loss)",
        operating_income
    )

    # ---------------------------------------------------
    # OPERATING INCOME → OTHER EXPENSES / NET INCOME
    # OTHER INCOME → NET INCOME
    # ---------------------------------------------------

    for item in other_net_items:

        amount = fsli_sum(item)

        if amount >= 0:

            add_link(
                item,
                "Net income/(loss)",
                amount
            )

        else:

            add_link(
                "Operating income/(loss)",
                item,
                amount
            )

    add_link(
        "Operating income/(loss)",
        "Net income/(loss)",
        operating_income - other_negative
    )

    # ---------------------------------------------------
    # NET INCOME → OCI LOSSES / COMPREHENSIVE INCOME
    # OCI INCOME → COMPREHENSIVE INCOME
    # ---------------------------------------------------

    for item in oci_items:

        amount = fsli_sum(item)

        if amount >= 0:

            add_link(
                item,
                "Comprehensive income/(loss)",
                amount
            )

        else:

            add_link(
                "Net income/(loss)",
                item,
                amount
            )

    add_link(
        "Net income/(loss)",
        "Comprehensive income/(loss)",
        net_income - oci_negative
    )

    sankey_df = pd.DataFrame(links)

    return sankey_df

# ===================================================
# CASH FLOW SANKEY BUILDER
# ===================================================

def build_cf_sankey(df, start_date, end_date):

    df = df.copy()
    df.columns = df.columns.astype(str).str.strip()

    cash_fsli = [
        "Cash at bank",
        "Monetary fund"
    ]

    cf_tier_1_col = "CF Sankey A"
    cf_tier_2_col = "CF Sankey B"

    opening_df = df[
        (df["Date"] < start_date) &
        (df["FSLI"].isin(cash_fsli))
    ]

    opening_savings = opening_df["RMB Amount"].sum()

    period_df = df[
        (df["Date"] >= start_date) &
        (df["Date"] <= end_date) &
        (df["FSLI"].isin(cash_fsli)) &
        (df[cf_tier_1_col].notna())
    ].copy()

    links = []

    def add_link(source, target, amount):

        if amount != 0:

            links.append({
                "Source": source,
                "Target": target,
                "Amount": abs(amount)
            })

    # ---------------------------------------------------
    # PERIOD CASH FLOW TOTALS
    # ---------------------------------------------------

    operating_cf = period_df.loc[
        period_df[cf_tier_1_col] == "Operating cash flow",
        "RMB Amount"
    ].sum()

    investing_cf = period_df.loc[
        period_df[cf_tier_1_col] == "Investing activities",
        "RMB Amount"
    ].sum()

    financing_cf = period_df.loc[
        period_df[cf_tier_1_col] == "Financing activities",
        "RMB Amount"
    ].sum()

    fx_effect = period_df.loc[
        period_df[cf_tier_1_col] == "Effect of foreign currency exchange on cash",
        "RMB Amount"
    ].sum()

    current_period_cash_change = (
        operating_cf
        + investing_cf
        + financing_cf
        + fx_effect
    )

    ending_savings = (
        opening_savings
        + current_period_cash_change
    )

    # ---------------------------------------------------
    # OPERATING CASH FLOW
    # ---------------------------------------------------

    if operating_cf >= 0:

        add_link(
            "Operating cash flow",
            "Current pool",
            operating_cf
        )

    else:

        add_link(
            "Current pool",
            "Operating cash flow",
            operating_cf
        )

    # ---------------------------------------------------
    # INVESTING / FINANCING ACTIVITIES
    # ---------------------------------------------------

    for tier1 in [
        "Investing activities",
        "Financing activities"
    ]:

        tier1_df = period_df[
            period_df[cf_tier_1_col] == tier1
        ]

        tier1_total = tier1_df["RMB Amount"].sum()

        if tier1_total >= 0:

            add_link(
                tier1,
                "Current pool",
                tier1_total
            )

        else:

            add_link(
                "Current pool",
                tier1,
                tier1_total
            )

        tier2_summary = (
            tier1_df
            .groupby(cf_tier_2_col)["RMB Amount"]
            .sum()
            .reset_index()
        )

        for _, row in tier2_summary.iterrows():

            tier2 = row[cf_tier_2_col]
            amount = row["RMB Amount"]

            if pd.isna(tier2):
                continue

            if amount >= 0:

                add_link(
                    tier2,
                    tier1,
                    amount
                )

            else:

                add_link(
                    tier1,
                    tier2,
                    amount
                )

    # ---------------------------------------------------
    # FX EFFECT
    # ---------------------------------------------------

    if fx_effect >= 0:

        add_link(
            "Effect of foreign currency exchange on cash",
            "Current pool",
            fx_effect
        )

    else:

        add_link(
            "Current pool",
            "Effect of foreign currency exchange on cash",
            fx_effect
        )

    # ---------------------------------------------------
    # SAVINGS FROM PRIOR PERIODS / ENDING SAVINGS
    # ---------------------------------------------------

    if current_period_cash_change < 0:

        # Current period consumed cash, so prior savings fund the shortfall
        add_link(
            "Savings from prior periods",
            "Current pool",
            abs(current_period_cash_change)
        )

        # Residual opening savings goes to ending savings
        residual_prior_savings = (
            opening_savings
            + current_period_cash_change
        )

        if residual_prior_savings > 0:

            add_link(
                "Savings from prior periods",
                "Savings at the end of the period",
                residual_prior_savings
            )

    else:

        # Current period generated positive cash.
        # Opening savings and current pool both contribute to ending savings.
        if opening_savings > 0:

            add_link(
                "Savings from prior periods",
                "Savings at the end of the period",
                opening_savings
            )

        add_link(
            "Current pool",
            "Savings at the end of the period",
            current_period_cash_change
        )

    return pd.DataFrame(links)



# ===================================================
# SIDEBAR NAVIGATION
# ===================================================

st.sidebar.header(
    "Financial Statements"
)

page = st.sidebar.radio(
    "Navigate",
    [
        "Sankey Diagram",
        "Statement of Financial Position",
        "Statement of Comprehensive Income"
    ]
)



# ===================================================
# BALANCE SHEET
# ===================================================

if page == "Statement of Financial Position":

    st.header(
        "Statement of Financial Position"
    )

    # ===================================================
    # DATE FILTER
    # ===================================================

    selected_month = st.select_slider(
    "Select Reporting Month",
    options=month_options,
    value=month_options[-1]
    )

    selected_date = (
    pd.to_datetime(selected_month) 
    + pd.offsets.MonthEnd(0)
    )

    # ---------------------------------------------------
    # FILTER DATA
    # ---------------------------------------------------

    bs_df = df[
        df["Date"] <= selected_date
    ].copy()

    # ---------------------------------------------------
    # BUILD REPORT
    # ---------------------------------------------------

    bs_report = (
        bs_df
        .groupby(
            [
                "BS Report FSLI",
                "BS Sort",
                "BS Section A",
                "BS Section B"
            ]
        )["RMB Amount"]
        .sum()
        .reset_index()
    )

    bs_report = bs_report.sort_values(
        "BS Sort"
    )

    # ---------------------------------------------------
    # DISPLAY SIGN
    # ---------------------------------------------------

    bs_report["Display Amount"] = (
        bs_report["RMB Amount"]
    )

    bs_report.loc[
        bs_report["BS Section A"].isin(
            [
                "Liabilities",
                "Equity"
            ]
        ),
        "Display Amount"
    ] = (
        bs_report.loc[
            bs_report["BS Section A"].isin(
                [
                    "Liabilities",
                    "Equity"
                ]
            ),
            "Display Amount"
        ] * -1
    )

    # ===================================================
    # KPI SUMMARY
    # ===================================================

    total_assets = bs_report[
        bs_report["BS Section A"]
        == "Assets"
    ]["Display Amount"].sum()

    total_liabilities = bs_report[
        bs_report["BS Section A"]
        == "Liabilities"
    ]["Display Amount"].sum()

    total_equity = bs_report[
        bs_report["BS Section A"]
        == "Equity"
    ]["Display Amount"].sum()

    kpi1, kpi2, kpi3 = st.columns(3)

    with kpi1:

        st.metric(
            "Total Assets",
            acct_format(total_assets)
        )

    with kpi2:

        st.metric(
            "Total Liabilities",
            acct_format(total_liabilities)
        )

    with kpi3:

        st.metric(
            "Total Equity",
            acct_format(total_equity)
        )

    st.divider()

    # ===================================================
    # FORMATTED BS
    # ===================================================

    for section_a in [

        "Assets",
        "Liabilities",
        "Equity"

    ]:

        section_a_df = bs_report[
            bs_report["BS Section A"]
            == section_a
        ]

        st.markdown(
            f"## {section_a}"
        )

        for section_b in (

            section_a_df[
                "BS Section B"
            ]
            .dropna()
            .unique()

        ):

            section_b_df = section_a_df[
                section_a_df[
                    "BS Section B"
                ]
                == section_b
            ]

            st.markdown(
                f"### {section_b}"
            )

            for _, row in (
                section_b_df.iterrows()
            ):

                fsli_name = row[
                    "BS Report FSLI"
                ]

                fsli_amount = row[
                    "Display Amount"
                ]

                expander_title = (
                    f"{fsli_name}"
                    f" | "
                    f"{acct_format(fsli_amount)}"
                )

                with st.expander(
                    expander_title
                ):

                    fsli_detail_df = bs_df[
                        bs_df[
                            "BS Report FSLI"
                        ]
                        == fsli_name
                    ]

                    account_summary = (
                        fsli_detail_df
                        .groupby(
                            "Account Name CN"
                        )["RMB Amount"]
                        .sum()
                        .reset_index()
                    )

                    account_summary[
                        "Display Amount"
                    ] = account_summary[
                        "RMB Amount"
                    ]

                    if section_a in [
                        "Liabilities",
                        "Equity"
                    ]:

                        account_summary[
                            "Display Amount"
                        ] = (
                            account_summary[
                                "Display Amount"
                            ] * -1
                        )

                    # ---------------------------------------
                    # ACCOUNT BREAKDOWN
                    # ---------------------------------------

                    st.markdown(
                        "#### Account Breakdown"
                    )

                    for _, acc_row in (
                        account_summary
                        .iterrows()
                    ):

                        col1, col2 = st.columns(
                            [4, 1]
                        )

                        with col1:

                            st.write(
                                acc_row[
                                    "Account Name CN"
                                ]
                            )

                        with col2:

                            st.markdown(
                                f"""
                                <div style='text-align:right'>
                                {acct_format(acc_row['Display Amount'])}
                                </div>
                                """,
                                unsafe_allow_html=True
                            )

                    st.divider()

                    # ---------------------------------------
                    # TRANSACTION DETAILS
                    # ---------------------------------------

                    st.markdown(
                        "#### Transaction Details"
                    )

                    transaction_df = (
                        fsli_detail_df[
                            [
                                "Date",
                                "JE Number",
                                "Account Name CN",
                                "Abstract",
                                "Dimension",
                                "RMB Amount"
                            ]
                        ]
                        .sort_values(
                            "Date",
                            ascending=False
                        )
                        #.head(5)
                    )

                    st.dataframe(
                        transaction_df,
                        use_container_width=True,
                        hide_index=True
                    )

            subtotal = section_b_df[
                "Display Amount"
            ].sum()

            st.markdown(
                f"""
                <div style='text-align:right;
                            font-weight:bold'>
                Subtotal — {section_b}:
                {acct_format(subtotal)}
                </div>
                """,
                unsafe_allow_html=True
            )

        section_total = section_a_df[
            "Display Amount"
        ].sum()

        st.markdown(
            f"""
            <div style='text-align:right;
                        font-size:20px;
                        font-weight:bold'>
            Total {section_a}:
            {acct_format(section_total)}
            </div>
            """,
            unsafe_allow_html=True
        )

        st.divider()

    # ===================================================
    # TREEMAP
    # ===================================================

    st.subheader(
        "Balance Sheet Structure"
    )

    chart_df = bs_report.copy()

    chart_df["Chart Amount"] = (
        chart_df[
            "Display Amount"
        ].abs()
    )

    fig = px.treemap(
        chart_df,
        path=[
            "BS Section A",
            "BS Section B",
            "BS Report FSLI"
        ],
        values="Chart Amount",
        color="BS Section A"
    )

    fig.update_traces(
        textinfo="label+value"
    )

    st.plotly_chart(
        fig,
        use_container_width=True,
        key="bs_treemap"
    )


# ===================================================
# PROFIT & LOSS
# ===================================================

elif page == "Statement of Comprehensive Income":

    st.header(
        "Statement of Comprehensive Income"
    )

    # ===================================================
    # PL PERIOD SELECTION
    # ===================================================

    pl_start_month, pl_end_month = st.select_slider(
    "Select PL Period",
    options=month_options,
    value=(month_options[0], month_options[-1])
    )

    pl_start_date = pd.to_datetime(pl_start_month)
    pl_end_date = pd.to_datetime(pl_end_month) + pd.offsets.MonthEnd(0)

    # ---------------------------------------------------
    # FILTER PL DATA
    # ---------------------------------------------------

    pl_df = df[
        (
            df["Date"] >= pl_start_date
        )
        &
        (
            df["Date"] <= pl_end_date
        )
        &
        (
            df["PL Section"].notna()
        )
    ].copy()

    # ---------------------------------------------------
    # COUNTER ACCOUNT LOGIC
    # ---------------------------------------------------

    counter_mapping = []

    for je_number, je_group in (
        pl_df.groupby("JE Number")
    ):

        if len(je_group) == 2:

            row1 = je_group.iloc[0]
            row2 = je_group.iloc[1]

            counter_mapping.append({

                "Index": row1.name,

                "Counter Account":
                    row2["Account Name CN"]

            })

            counter_mapping.append({

                "Index": row2.name,

                "Counter Account":
                    row1["Account Name CN"]

            })

    counter_df = pd.DataFrame(
        counter_mapping
    )

    if not counter_df.empty:

        counter_df = counter_df.set_index(
            "Index"
        )

        pl_df["Counter Account"] = (
            counter_df[
                "Counter Account"
            ]
        )

    # ---------------------------------------------------
    # BUILD PL REPORT
    # ---------------------------------------------------

    pl_report = (

        pl_df

        .groupby(
            [
                "PL Section",
                "FSLI",
                "PL Sort"
            ]
        )["RMB Amount"]

        .sum()

        .reset_index()

    )

    pl_report = pl_report.sort_values(
        "PL Sort"
    )

    # ---------------------------------------------------
    # DISPLAY SIGN
    # ---------------------------------------------------

    pl_report["Display Amount"] = (
        pl_report["RMB Amount"] * -1
    )

    # ===================================================
    # KPI SUMMARY
    # ===================================================

    comprehensive_income = (

        pl_report[
            "Display Amount"
        ].sum()

    )

    revenue_total = (

        pl_report[
            pl_report[
                "PL Section"
            ] == "Revenues"
        ][
            "Display Amount"
        ].sum()

    )

    net_income = (

        pl_report[
            pl_report[
                "PL Section"
            ].isin(
                [
                    "Revenues",
                    "Costs",
                    "Expenses",
                    "Others"
                ]
            )
        ][
            "Display Amount"
        ].sum()

    )

    kpi1, kpi2, kpi3 = st.columns(3)

    with kpi1:

        st.metric(
            "Revenue",
            acct_format(
                revenue_total
            )
        )

    with kpi2:

        st.metric(
            "Net Income/(Loss)",
            acct_format(
                net_income
            )
        )

    with kpi3:

        st.metric(
            "Comprehensive Income/(Loss)",
            acct_format(
                comprehensive_income
            )
        )

    st.divider()

    # ===================================================
    # MONTHLY OPERATING PROFIT WATERFALL
    # ===================================================

    st.subheader(
        "Monthly Operating Profit/(Loss)"
    )

    operating_df = pl_df[
        pl_df["PL Section"].isin(
            [
                "Revenues",
                "Costs",
                "Expenses"
            ]
        )
    ].copy()

    operating_df["Display Amount"] = (
        operating_df["RMB Amount"] * -1
    )

    monthly_operating = (

        operating_df

        .groupby("Month")[
            "Display Amount"
        ]

        .sum()

        .reset_index()

    )

    waterfall_fig = go.Figure(

        go.Waterfall(

            x=monthly_operating["Month"],

            y=monthly_operating[
                "Display Amount"
            ],

            measure=[
                "relative"
            ] * len(monthly_operating),

            increasing={
                "marker": {
                    "color":
                    "rgb(153,255,255)"
                }
            },

            decreasing={
                "marker": {
                    "color":
                    "rgb(255,102,102)"
                }
            },

            connector={
                "line": {
                    "color": "gray"
                }
            }

        )

    )

    waterfall_fig.update_layout(

        title=
        "Monthly Operating Profit/(Loss)",

        yaxis_tickformat=",.2f",

        showlegend=False

    )

    waterfall_key = (

        f"operating_waterfall_"

        f"{pl_start_date.strftime('%Y%m%d')}_"

        f"{pl_end_date.strftime('%Y%m%d')}"

    )

    st.plotly_chart(

        waterfall_fig,

        use_container_width=True,

        key=waterfall_key

    )

    st.divider()

    # ===================================================
    # FORMATTED PL
    # ===================================================

    pl_sections = [

        "Revenues",
        "Costs",
        "Expenses",
        "Others",
        "OCI"

    ]

    running_total = 0

    for section in pl_sections:

        section_df = pl_report[
            pl_report[
                "PL Section"
            ] == section
        ]

        st.markdown(
            f"## {section}"
        )

        for _, row in (
            section_df.iterrows()
        ):

            fsli_name = row[
                "FSLI"
            ]

            fsli_amount = row[
                "Display Amount"
            ]

            running_total += (
                fsli_amount
            )

            expander_title = (
                f"{fsli_name}"
                f" | "
                f"{acct_format(fsli_amount)}"
            )

            with st.expander(
                expander_title
            ):

                # ---------------------------------------
                # DETAIL FILTER
                # ---------------------------------------

                fsli_detail_df = pl_df[
                    pl_df[
                        "FSLI"
                    ]
                    == fsli_name
                ].copy()

                # ---------------------------------------
                # WEEKDAY ANALYSIS
                # ---------------------------------------

                fsli_detail_df["Weekday No"] = (
                    fsli_detail_df["Date"]
                    .dt.weekday
                )

                fsli_detail_df["Weekday"] = (
                    fsli_detail_df["Date"]
                    .dt.day_name()
                )

                # ---------------------------------------
                # MONTHLY STACKED COLUMN CHART
                # ---------------------------------------

                monthly_chart_df = (

                    fsli_detail_df

                    .groupby(
                        [
                            "Month",
                            "Account Name CN"
                        ]
                    )["RMB Amount"]

                    .sum()

                    .reset_index()

                )

                monthly_chart_df[
                    "Display Amount"
                ] = (

                    monthly_chart_df[
                        "RMB Amount"
                    ] * -1

                )

                fig = px.bar(

                    monthly_chart_df,

                    x="Month",

                    y="Display Amount",

                    color="Account Name CN",

                    barmode="stack",

                    title=f"{fsli_name} Monthly Movement"

                )

                fig.update_layout(
                    yaxis_tickformat=",.2f"
                )

                st.plotly_chart(

                    fig,

                    use_container_width=True,

                    key=f"pl_chart_{fsli_name}"

                )

                # ---------------------------------------
                # ACCOUNT BREAKDOWN
                # ---------------------------------------

                st.markdown(
                    "#### Account Breakdown"
                )

                account_total = (

                    fsli_detail_df

                    .groupby(
                        "Account Name CN"
                    )["RMB Amount"]

                    .sum()

                    .reset_index()

                )

                account_total[
                    "Display Amount"
                ] = (

                    account_total[
                        "RMB Amount"
                    ] * -1

                )

                account_total = account_total.sort_values(

                    "Display Amount",

                    key=abs,

                    ascending=False

                )

                for _, acc_row in (
                    account_total.iterrows()
                ):

                    col1, col2 = st.columns(
                        [4, 1]
                    )

                    with col1:

                        st.write(
                            acc_row[
                                "Account Name CN"
                            ]
                        )

                    with col2:

                        st.markdown(
                            f"""
                            <div style='text-align:right'>
                            {acct_format(acc_row['Display Amount'])}
                            </div>
                            """,
                            unsafe_allow_html=True
                        )

                st.divider()

                # ---------------------------------------
                # ACTIVITY TREEMAP
                # ---------------------------------------

                if section in [
                    "Revenues",
                    "Costs",
                    "Expenses"
                ]:

                    st.markdown(
                        "#### Activity Treemap"
                    )

                    st.caption(
                        "*Excluded allowances, subsidies and net-off."
                    )

                    treemap_base_df = fsli_detail_df.copy()

                    # ---------------------------------------
                    # EXCLUDE NET-OFF / REVERSE DIRECTION
                    # ---------------------------------------

                    if section == "Revenues":

                        # Revenue is normally credit / negative
                        # Keep negative rows only
                        treemap_base_df = treemap_base_df[
                            treemap_base_df[
                                "RMB Amount"
                            ] < 0
                        ]

                    else:

                        # Costs and Expenses are normally debit / positive
                        # Keep positive rows only
                        treemap_base_df = treemap_base_df[
                            treemap_base_df[
                                "RMB Amount"
                            ] > 0
                        ]

                    if treemap_base_df.empty:

                        st.info(
                            "No normal-direction activity available for treemap."
                        )

                    else:

                        treemap_df = (

                            treemap_base_df

                            .groupby(
                                [
                                    "Account Name CN",
                                    "Dimension",
                                    "Weekday No"
                                ]
                            )["RMB Amount"]

                            .sum()

                            .reset_index()

                        )

                        # ---------------------------------------
                        # DISPLAY AMOUNT
                        # ---------------------------------------

                        if section == "Revenues":

                            treemap_df[
                                "Treemap Display Amount"
                            ] = (
                                treemap_df[
                                    "RMB Amount"
                                ] * -1
                            )

                        else:

                            treemap_df[
                                "Treemap Display Amount"
                            ] = (
                                treemap_df[
                                    "RMB Amount"
                                ]
                            )

                        # ---------------------------------------
                        # SIZE AMOUNT
                        # ---------------------------------------

                        treemap_df[
                            "ABS Amount"
                        ] = (
                            treemap_df[
                                "Treemap Display Amount"
                            ].abs()
                        )

                        treemap_df = treemap_df.sort_values(
                            "ABS Amount",
                            ascending=False
                        )

                        # ---------------------------------------
                        # TREEMAP
                        # ---------------------------------------

                        treemap_fig = px.treemap(

                            treemap_df,

                            path=[
                                "Account Name CN",
                                "Dimension"
                            ],

                            values="ABS Amount",

                            color="Weekday No",

                            color_continuous_scale="RdBu",

                            title=f"{fsli_name} Activity Distribution"

                        )

                        treemap_fig.update_traces(
                            textinfo="label+value"
                        )

                        treemap_fig.update_layout(

                            margin=dict(
                                t=50,
                                l=25,
                                r=25,
                                b=25
                            )

                        )

                        st.plotly_chart(

                            treemap_fig,

                            use_container_width=True,

                            key=f"treemap_{fsli_name}"

                        )

                

        # ------------------------------------------------
        # SECTION TOTAL
        # ------------------------------------------------

        section_total = section_df[
            "Display Amount"
        ].sum()

        st.markdown(
            f"""
            <div style='text-align:right;
                        font-size:18px;
                        font-weight:bold;
                        color:rgb(153,255,255)'>
            Total {section}:
            {acct_format(section_total)}
            </div>
            """,
            unsafe_allow_html=True
        )

        # ------------------------------------------------
        # PROFIT CALCULATION
        # ------------------------------------------------

        if section == "Costs":

            st.markdown(
                f"""
                <div style='text-align:right;
                            font-size:20px;
                            font-weight:bold;
                            color:rgb(153,255,255)'>
                Gross Profit/(Loss):
                {acct_format(running_total)}
                </div>
                """,
                unsafe_allow_html=True
            )

        elif section == "Expenses":

            st.markdown(
                f"""
                <div style='text-align:right;
                            font-size:20px;
                            font-weight:bold;
                            color:rgb(153,255,255)'>
                Operating Profit/(Loss):
                {acct_format(running_total)}
                </div>
                """,
                unsafe_allow_html=True
            )

        elif section == "Others":

            st.markdown(
                f"""
                <div style='text-align:right;
                            font-size:20px;
                            font-weight:bold;
                            color:rgb(153,255,255)'>
                Net Income/(Loss):
                {acct_format(running_total)}
                </div>
                """,
                unsafe_allow_html=True
            )

        elif section == "OCI":

            st.markdown(
                f"""
                <div style='text-align:right;
                            font-size:24px;
                            font-weight:bold;
                            color:rgb(153,255,255)'>
                Comprehensive Income/(Loss):
                {acct_format(running_total)}
                </div>
                """,
                unsafe_allow_html=True
            )

        st.divider()

# ===================================================
# SANKEY DIAGRAM
# ===================================================

else:

    st.header("Sankey Diagram")

    sankey_start_month, sankey_end_month = st.select_slider(
    "Select Sankey Period",
    options=month_options,
    value=(month_options[0], month_options[-1])
    )

    sankey_start_date = pd.to_datetime(sankey_start_month)
    sankey_end_date = pd.to_datetime(sankey_end_month) + pd.offsets.MonthEnd(0)

    sankey_base_df = df[
        (df["Date"] >= sankey_start_date) &
        (df["Date"] <= sankey_end_date) &
        (df["PL Section"].notna())
    ].copy()

    sankey_df = build_pl_sankey(sankey_base_df)

    if sankey_df is None:
        st.error(
            "Sankey builder returned None. Please check that build_pl_sankey() ends with 'return sankey_df'."
        )
        st.stop()

    st.subheader("PL Flow Sankey")

    if not sankey_df.empty:

        labels = pd.unique(
            sankey_df[["Source", "Target"]].values.ravel()
        ).tolist()

        label_map = {
            label: i
            for i, label in enumerate(labels)
        }

        # ---------------------------------------------------
        # LINK COLORS
        # ---------------------------------------------------

        link_colors = []

        for _, row in sankey_df.iterrows():

            source = row["Source"]
            target = row["Target"]

            # -----------------------------------
            # REVENUES
            # -----------------------------------

            if (

                source in [
                    "Salaries & bonuses",
                    "Subsidies",
                    "H-Fund Take"
                ]

                or

                target == "Revenues"

            ):

                link_colors.append(
                    "rgba(153,255,255,0.50)"
                )

            # -----------------------------------
            # COSTS
            # -----------------------------------

            elif source == "Costs":

                link_colors.append(
                    "rgba(204,153,255,0.50)"
                )
            elif target == "Costs":

                link_colors.append(
                    "rgba(204,153,255,0.50)"
                )

            # -----------------------------------
            # EXPENSES
            # -----------------------------------

            elif source == "Expenses":

                link_colors.append(
                    "rgba(255,153,204,0.50)"
                )
            elif target == "Expenses":

                link_colors.append(
                    "rgba(255,153,204,0.50)"
                )

            # -----------------------------------
            # OTHERS
            # -----------------------------------

            elif (

                "FinExp" in source

                or

                "Investment income" in source

                or

                "FinExp" in target

                or

                "Investment income" in target

            ):

                link_colors.append(
                    "rgba(153,204,255,0.50)"
                )

            # -----------------------------------
            # OCI
            # -----------------------------------

            elif (

                "H-Fund keep" in source

                or

                "Medical insurance keep" in source

                or

                "H-Fund keep" in target

                or

                "Medical insurance keep" in target

            ):

                link_colors.append(
                    "rgba(153,255,255,0.50)"
                )

            # -----------------------------------
            # DEFAULT
            # -----------------------------------

            else:

                link_colors.append(
                    "rgba(153,255,255,0.35)"
                )

        sankey_fig = go.Figure(
            data=[
                go.Sankey(
                    node=dict(
                        pad=20,
                        thickness=18,
                        line=dict(
                            color="black",
                            width=0.5
                        ),
                        label=labels,
                        color="rgb(153,255,255)"
                    ),
                    link=dict(
                        source=sankey_df["Source"].map(label_map),
                        target=sankey_df["Target"].map(label_map),
                        value=sankey_df["Amount"],
                        color=link_colors
                    )
                )
            ]
        )

        sankey_fig.update_layout(
            title_text="Statement of Comprehensive Income Flow",
            font_size=12,
            height=750
        )

        st.plotly_chart(
            sankey_fig,
            use_container_width=True,
            key="standalone_sankey_chart"
        )

        st.subheader("PL Flow Sankey Source Data")

        sankey_display_df = sankey_df.copy()

        sankey_display_df["Amount"] = (
            sankey_display_df["Amount"]
            .map(acct_format)
        )

        st.dataframe(
            sankey_display_df,
            use_container_width=True,
            hide_index=True
        )

    else:

        st.info(
            "No Sankey data available for the selected period."
        )


# ===================================================
# CASH FLOW SANKEY
# ===================================================

    st.subheader("Cash Flow Sankey")

    cf_sankey_df = build_cf_sankey(
        df,
        sankey_start_date,
        sankey_end_date
    )

    if not cf_sankey_df.empty:

        cf_labels = pd.unique(
            cf_sankey_df[["Source", "Target"]].values.ravel()
        ).tolist()

        cf_label_map = {
            label: i
            for i, label in enumerate(cf_labels)
        }

        cf_link_colors = []

        for _, row in cf_sankey_df.iterrows():

            source = row["Source"]
            target = row["Target"]

            if "Operating cash flow" in [source, target]:

                cf_link_colors.append(
                    "rgba(153,255,255,0.50)"
                )

            elif "Investing activities" in [source, target]:

                cf_link_colors.append(
                    "rgba(204,153,255,0.50)"
                )

            elif "Financing activities" in [source, target]:

                cf_link_colors.append(
                    "rgba(153,204,255,0.50)"
                )

            elif "Savings from prior periods" in [source, target]:

                cf_link_colors.append(
                    "rgba(200,200,200,0.45)"
                )

            else:

                cf_link_colors.append(
                    "rgba(180,180,180,0.35)"
                )

        cf_fig = go.Figure(
            data=[
                go.Sankey(
                    node=dict(
                        pad=20,
                        thickness=18,
                        line=dict(
                            color="black",
                            width=0.5
                        ),
                        label=cf_labels,
                        color="rgb(153,255,255)"
                    ),
                    link=dict(
                        source=cf_sankey_df["Source"].map(cf_label_map),
                        target=cf_sankey_df["Target"].map(cf_label_map),
                        value=cf_sankey_df["Amount"],
                        color=cf_link_colors
                    )
                )
            ]
        )

        cf_fig.update_layout(
            title_text="Cash Flow Sankey",
            font_size=12,
            height=650
        )

        st.plotly_chart(
            cf_fig,
            use_container_width=True,
            key="cash_flow_sankey_chart"
        )

        st.subheader("Cash Flow Sankey Source Data")

        cf_display_df = cf_sankey_df.copy()

        cf_display_df["Amount"] = (
            cf_display_df["Amount"]
            .map(acct_format)
        )

        st.dataframe(
            cf_display_df,
            use_container_width=True,
            hide_index=True
        )

    else:

        st.info(
            "No Cash Flow Sankey data available for the selected period."
        )
