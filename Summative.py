# app.py
# ----------------------------------------------------------
# FootLens – Injury Impact Analytics Dashboard
# ----------------------------------------------------------
# How to run:
#   1. Put this file (app.py) in the same folder as player_injuries_impact.csv
#   2. In terminal:  streamlit run app.py
# ----------------------------------------------------------

import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import re

# ----------------------------------------------------------
# Data Loading & Preprocessing
# ----------------------------------------------------------

@st.cache_data
def load_data(path: str = "player_injuries_impact_cleaned.csv") -> pd.DataFrame:
    df = pd.read_csv(path)

    # --- Convert dates ---
    if "Date of Injury" in df.columns:
        df["Date of Injury"] = pd.to_datetime(df["Date of Injury"], errors="coerce")
    if "Date of return" in df.columns:
        df["Date of return"] = pd.to_datetime(df["Date of return"], errors="coerce")

    # Rename main identity columns for consistency (only if present)
    rename_map = {}
    if "Name" in df.columns:
        rename_map["Name"] = "Player_Name"
    if "Team Name" in df.columns:
        rename_map["Team Name"] = "Team"
    if "FIFA rating" in df.columns:
        rename_map["FIFA rating"] = "FIFA_Rating"
    df = df.rename(columns=rename_map)

    # --- Add Injury Month / Year for heatmap ---
    if "Date of Injury" in df.columns:
        df["Injury_Month"] = df["Date of Injury"].dt.month_name()
        df["Injury_Year"] = df["Date of Injury"].dt.year
    else:
        df["Injury_Month"] = np.nan
        df["Injury_Year"] = np.nan

    # --- Helper function to clean rating / GD columns ---
    def clean_numeric(val):
        if pd.isna(val):
            return np.nan
        s = str(val).strip()
        if s in ["", "N.A.", "N.A", "NA", "n.a.", "-", "None"]:
            return np.nan
        # remove textual stuff like "(S)" etc.
        s = re.sub(r"\(.*?\)", "", s)
        s = s.replace(",", "").strip()
        try:
            return float(s)
        except:
            return np.nan

    # Guess rating and goal-diff columns from column names
    rating_cols = [c for c in df.columns if "Player_rating" in c]
    gd_cols = [c for c in df.columns if c.endswith("_GD")]

    # Clean numeric fields
    for c in rating_cols + gd_cols:
        df[c] = df[c].apply(clean_numeric)

    # --- Average ratings before / after injury ---
    before_rating_cols = [c for c in rating_cols if "before" in c.lower()]
    after_rating_cols = [c for c in rating_cols if "after" in c.lower()]

    if before_rating_cols:
        df["avg_rating_before"] = df[before_rating_cols].mean(axis=1, skipna=True)
    else:
        df["avg_rating_before"] = np.nan

    if after_rating_cols:
        df["avg_rating_after"] = df[after_rating_cols].mean(axis=1, skipna=True)
    else:
        df["avg_rating_after"] = np.nan

    df["rating_change"] = df["avg_rating_after"] - df["avg_rating_before"]

    # --- Team GD before injury vs during missed matches ---
    before_gd_cols = [c for c in gd_cols if "before" in c.lower()]
    missed_gd_cols = [c for c in gd_cols if "missed" in c.lower()]

    if before_gd_cols:
        df["team_gd_before"] = df[before_gd_cols].mean(axis=1, skipna=True)
    else:
        df["team_gd_before"] = np.nan

    if missed_gd_cols:
        df["team_gd_missed"] = df[missed_gd_cols].mean(axis=1, skipna=True)
    else:
        df["team_gd_missed"] = np.nan

    # Performance Drop Index: higher = team did worse during absence
    df["performance_drop_index"] = df["team_gd_before"] - df["team_gd_missed"]

    return df


# ----------------------------------------------------------
# Dashboard App
# ----------------------------------------------------------

def main():
    st.set_page_config(
        page_title="FootLens – Injury Impact Analytics",
        layout="wide"
    )

    st.title("📊 FootLens – Injury Impact Analytics Dashboard")
    st.markdown(
        """
        This dashboard helps technical directors and sports managers understand  
        how **player injuries** affect **team performance**, **match outcomes**, and **player comebacks**.
        """
    )

    # Load data
    df = load_data()

    # ------------------------------------------------------
    # Sidebar Filters
    # ------------------------------------------------------
    st.sidebar.header("Filters")

    # Season filter (if Season column exists)
    if "Season" in df.columns:
        seasons = sorted([s for s in df["Season"].dropna().unique()])
        season_filter = st.sidebar.multiselect(
            "Season",
            seasons,
            default=seasons
        )
    else:
        season_filter = []
        st.sidebar.write("No 'Season' column found in dataset.")

    # Team filter
    if "Team" in df.columns:
        teams = sorted([t for t in df["Team"].dropna().unique()])
        team_filter = st.sidebar.multiselect(
            "Team",
            teams,
            default=[]
        )
    else:
        team_filter = []

    # Player filter
    if "Player_Name" in df.columns:
        players = sorted([p for p in df["Player_Name"].dropna().unique()])
        player_filter = st.sidebar.multiselect(
            "Player",
            players,
            default=[]
        )
    else:
        player_filter = []

    # Apply filters on a copy
    filtered = df.copy()

    if "Season" in df.columns and season_filter:
        filtered = filtered[filtered["Season"].isin(season_filter)]
    if team_filter:
        filtered = filtered[filtered["Team"].isin(team_filter)]
    if player_filter:
        filtered = filtered[filtered["Player_Name"].isin(player_filter)]

    # ------------------------------------------------------
    # High-level Metrics
    # ------------------------------------------------------
    st.subheader("📌 High-Level Injury & Performance Overview")

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        total_injuries = filtered.shape[0]
        st.metric("Total Injury Records", total_injuries)

    with col2:
        unique_players = filtered["Player_Name"].nunique() if "Player_Name" in filtered.columns else 0
        st.metric("Players Affected", unique_players)

    with col3:
        unique_teams = filtered["Team"].nunique() if "Team" in filtered.columns else 0
        st.metric("Teams Involved", unique_teams)

    with col4:
        avg_drop = filtered["performance_drop_index"].mean()
        st.metric("Avg Performance Drop Index", f"{avg_drop:.2f}" if pd.notna(avg_drop) else "N/A")

    st.markdown("---")

    # ------------------------------------------------------
    # Visual 1: Bar Chart – Top 10 injuries by team performance drop
    # ------------------------------------------------------
    st.subheader("1️⃣ Top 10 Injuries by Team Performance Drop")

    if filtered["performance_drop_index"].notna().sum() > 0:
        top_drops = (
            filtered.sort_values("performance_drop_index", ascending=False)
                    .head(10)
        )

        fig1 = px.bar(
            top_drops,
            x="Player_Name",
            y="performance_drop_index",
            color="Team" if "Team" in top_drops.columns else None,
            hover_data=[
                col for col in ["Season", "Injury", "team_gd_before", "team_gd_missed"]
                if col in top_drops.columns
            ],
            title="Top 10 Injury Spells by Performance Drop Index (Higher = Worse)"
        )
        fig1.update_layout(
            xaxis_title="Player",
            yaxis_title="Performance Drop Index"
        )
        st.plotly_chart(fig1, use_container_width=True)
    else:
        st.info("No valid performance_drop_index values found to display this chart.")

    st.markdown("---")

    # ------------------------------------------------------
    # Visual 2: Line Chart – Player performance timeline (before vs after injury)
    # ------------------------------------------------------
    st.subheader("2️⃣ Player Performance Timeline (Before vs After Injury)")

    if "Player_Name" in filtered.columns and not filtered["Player_Name"].dropna().empty:
        player_for_timeline = st.selectbox(
            "Select a player for timeline",
            sorted(filtered["Player_Name"].dropna().unique())
        )

        player_df = filtered[filtered["Player_Name"] == player_for_timeline].copy()

        timeline_rows = []

        for _, row in player_df.iterrows():
            # Before injury point
            if pd.notna(row["avg_rating_before"]):
                timeline_rows.append({
                    "Player_Name": row.get("Player_Name", ""),
                    "Team": row.get("Team", ""),
                    "Season": row.get("Season", ""),
                    "Phase": "Before injury",
                    "Phase_Order": -1,
                    "Avg_Rating": row["avg_rating_before"]
                })
            # After injury point
            if pd.notna(row["avg_rating_after"]):
                timeline_rows.append({
                    "Player_Name": row.get("Player_Name", ""),
                    "Team": row.get("Team", ""),
                    "Season": row.get("Season", ""),
                    "Phase": "After injury",
                    "Phase_Order": 1,
                    "Avg_Rating": row["avg_rating_after"]
                })

        timeline_df = pd.DataFrame(timeline_rows).dropna(subset=["Avg_Rating"])

        if not timeline_df.empty:
            fig2 = px.line(
                timeline_df.sort_values("Phase_Order"),
                x="Phase",
                y="Avg_Rating",
                markers=True,
                color="Season" if "Season" in timeline_df.columns else None,
                title=f"Average Rating Before vs After Each Injury – {player_for_timeline}"
            )
            fig2.update_layout(
                xaxis_title="Phase around Injury",
                yaxis_title="Average Rating"
            )
            st.plotly_chart(fig2, use_container_width=True)
        else:
            st.info("No rating information available for this player.")
    else:
        st.info("Player information not available in the dataset.")

    st.markdown("---")

    # ------------------------------------------------------
    # Visual 3: Heatmap – Injury frequency across months and clubs
    # ------------------------------------------------------
    st.subheader("3️⃣ Injury Frequency Heatmap – Month vs Club")

    if "Team" in filtered.columns and "Injury_Month" in filtered.columns:
        heat_df = (
            filtered.groupby(["Team", "Injury_Month"])
                    .size()
                    .reset_index(name="Injury_Count")
        )

        if not heat_df.empty:
            heat_pivot = heat_df.pivot(
                index="Team",
                columns="Injury_Month",
                values="Injury_Count"
            ).fillna(0)

            # Sort months in calendar order if present
            month_order = [
                "January", "February", "March", "April", "May", "June",
                "July", "August", "September", "October", "November", "December"
            ]
            heat_pivot = heat_pivot.reindex(columns=[m for m in month_order if m in heat_pivot.columns])

            fig3 = px.imshow(
                heat_pivot,
                labels=dict(x="Month", y="Team", color="Injury Count"),
                title="Injury Frequency by Month and Club"
            )
            st.plotly_chart(fig3, use_container_width=True)
        else:
            st.info("No injury month data available to display the heatmap.")
    else:
        st.info("Required columns 'Team' and 'Injury_Month' not found.")

    st.markdown("---")

    # ------------------------------------------------------
    # Visual 4: Scatter Plot – Age vs Performance Drop Index
    # ------------------------------------------------------
    st.subheader("4️⃣ Age vs Performance Drop Index")

    if "Age" in filtered.columns and filtered["Age"].notna().sum() > 0:
        scatter_df = filtered.dropna(subset=["Age", "performance_drop_index"])
        if not scatter_df.empty:
            fig4 = px.scatter(
                scatter_df,
                x="Age",
                y="performance_drop_index",
                color="Team" if "Team" in scatter_df.columns else None,
                hover_data=[
                    col for col in ["Player_Name", "Season", "Injury"]
                    if col in scatter_df.columns
                ],
                title="Does Age Influence Injury Impact on Team Performance?"
            )
            fig4.update_layout(
                xaxis_title="Age",
                yaxis_title="Performance Drop Index"
            )
            st.plotly_chart(fig4, use_container_width=True)
        else:
            st.info("Not enough non-null data points to draw the scatter plot.")
    else:
        st.info("Column 'Age' not available or empty in dataset.")

    st.markdown("---")

    # ------------------------------------------------------
    # Visual 5: Leaderboard – Comeback players ranked by rating improvement
    # ------------------------------------------------------
    st.subheader("5️⃣ Comeback Leaderboard – Rating Improvement After Injury")

    if "Player_Name" in filtered.columns and "rating_change" in filtered.columns:
        leaderboard = (
            filtered.groupby(["Player_Name", "Team"])
                    .agg(
                        Injuries_Count=("Injury", "count") if "Injury" in filtered.columns else ("Player_Name", "count"),
                        Avg_Rating_Before=("avg_rating_before", "mean"),
                        Avg_Rating_After=("avg_rating_after", "mean"),
                        Avg_Rating_Change=("rating_change", "mean")
                    )
                    .reset_index()
        )

        leaderboard = leaderboard.sort_values("Avg_Rating_Change", ascending=False).head(15)

        st.dataframe(
            leaderboard.style.format({
                "Avg_Rating_Before": "{:.2f}",
                "Avg_Rating_After": "{:.2f}",
                "Avg_Rating_Change": "{:.2f}"
            }),
            use_container_width=True
        )

        st.caption(
            "Higher **Avg_Rating_Change** means the player improved more after returning from injury – a stronger comeback."
        )
    else:
        st.info("Not enough information to build the comeback leaderboard.")

    st.markdown("---")

    # ------------------------------------------------------
    # Optional: Show raw data
    # ------------------------------------------------------
    with st.expander("🔎 Show Raw Data (After Preprocessing)"):
        st.dataframe(filtered, use_container_width=True)


if __name__ == "__main__":
    main()
