# CityPulse Evaluator & Demo Guide

Follow these steps to experience and judge all 7 capabilities of **CityPulse: The Live Civic Health Dashboard**:

## 1. Launch the Application

```bash
python run_citypulse.py
```
Open **http://127.0.0.1:8000** in any modern web browser.

---

## 2. Evaluation Walkthrough

### Step 1: The 10-Second Resident Glance (Point 4 & Point 5)
- Notice the **Civic Pulse Heartbeat**: Animated EKG line and real-time score (`92/100 · Calm & Stable`, `68 BPM`).
- Read the **Plain-Language Summary Box**: Notice how quickly a non-technical resident understands:
  - *What's happening right now*
  - *Why it matters to you*
  - *What you should do*

### Step 2: Injecting an Emerging Compound Crisis (Points 1, 2, 3, 5)
- Click **"Inject Incident"** in the top navigation bar.
- Select District: `Downtown & Financial Core` and click **"Cloudburst & Flooding"**.
- Watch the live dashboard react:
  - Overall Civic Health drops immediately to ~45/100, BPM races to ~105 BPM (orange/red pulse).
  - The map highlights Downtown in orange with interactive flooding and transit delay markers.
  - A **Cross-Feed Correlation** card appears: *"Storm-Induced Drainage & Transit Cascade"* with **92% Confidence**.
  - The **Plain-Language Summary** updates instantly to explain in non-technical terms that the 4th Ave underpass is flooded, Bus 12 is delayed by 28 mins, and residents should avoid driving or use the subway.

### Step 3: Testing Graceful Degradation (Point 2 & Constraint 7)
- Click **"Feeds (5)"** in the top navigation bar.
- Toggle the **WEATHER** or **TRANSIT** switch to **OFF**.
- Observe how the dashboard marks the feed as `OFFLINE` and seamlessly continues calculating the city pulse with the remaining feeds without crashing.

### Step 4: Testing Historical Replay & Pattern Detection (Point 7)
- Click **"Historical Replay"** in the top navigation bar.
- Select *"The Flash Flood & Evening Rush Hour Cascade"*.
- Drag the timeline scrubber from Step 0 through Step 6 (or click **Play**).
- Observe the timeline of events from 16:30 to 18:00 demonstrating how anomalies emerge, cross-feed correlations trigger at the peak of the crisis, and plain-language guidance adapts over time.

### Step 5: Threshold Alerting Center (Point 6)
- Click the **"Alerts"** bell icon.
- Review active notifications, test acknowledging or dismissing alerts, and inspect the simulated Webhook / SMS dispatch log.
