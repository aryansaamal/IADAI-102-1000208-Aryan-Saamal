---

# 📊 FootLens Injury Impact Analytics Dashboard

This project analyzes **how player injuries influence football team performance** using match records, injury timelines, and player performance indicators.
It provides a visual dashboard for **technical directors, sports managers, and analysts** to understand how key players affect match outcomes when injured.

---

## 🎯 Objectives

* Identify **injuries causing major performance decline**
* Compare **player performance before vs after injury**
* Measure **team performance drop** during player absence
* Detect **injury clusters (months, teams)**
* Highlight **comeback players** with improvements after recovery

---

## 🏆 Business Questions

The dashboard is built around five core sports-analytics questions:

1. **Which injuries resulted in the biggest drop in team performance?**
2. **What was the team’s win/loss pattern during player absence?**
3. **How did individual players perform after returning from injury?**
4. **Are there specific months or clubs with more injury clusters?**
5. **Which clubs suffered the most from injuries overall?**

---

## 📂 Dataset Description

The dataset contains multiple seasons of football injury records with match-level performance metrics.

**Main Columns:**

* Player name, age, position
* Team name, season
* Injury type, injury start & return dates
* Match performance before injury (3 matches)
* Missed match performance (during absence)
* Match performance after injury (3 matches)
* Player ratings and team goal difference (GD)

---

## 🧮 Feature Engineering

To quantify injury impact, the following metrics are calculated:

### **Player Rating Metrics**

```
avg_rating_before = mean(ratings in 3 matches before injury)
avg_rating_after  = mean(ratings in 3 matches after return)
rating_change     = avg_rating_after - avg_rating_before
```

### **Team Performance Drop Index**

```
team_gd_before = avg(goal difference before injury)
team_gd_missed = avg(goal difference in missed matches)

performance_drop_index = team_gd_before - team_gd_missed
```

Higher value = the team suffered more without the player.

---

## 🧠 Tools & Tech Stack

* **Python**
* **Streamlit** for dashboard UI
* **Pandas** for data cleaning and aggregation
* **Plotly** for interactive charts
* **Matplotlib** for distribution plots
* **Jupyter Notebook** for EDA

---

## 📊 Core Insights Visualized

The dashboard provides **five key visuals**:

1. **Bar Chart** – Top 10 injuries with highest performance drop
2. **Line Chart** – Player rating timeline (before vs after injury)
3. **Heatmap** – Injury frequency across clubs and months
4. **Scatter Plot** – Player age vs performance drop index
5. **Leaderboard Table** – Top comeback players by rating improvement

---
