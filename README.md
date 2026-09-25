# CityPulse: The Live Civic Health Dashboard
> **AmiHacks Track B — Industry / Open Innovation (Problem Statement-2)**  
> *"One glance should tell a resident what's really happening in their neighborhood — and why it matters."*

---

## 🌟 Executive Overview

Local governments and residents rarely have a single, real-time view of how a neighborhood is actually doing. The data exists — traffic incidents, public transit delays, air quality readings, noise complaints, power outages, weather alerts — but it is scattered across a dozen disconnected feeds and dashboards. Residents find out about problems (a flooded underpass, a gas leak, a transit outage) only after they are stuck in it.

**CityPulse** fuses heterogeneous, noisy, differently paced feeds into a unified **Civic Health Pulse (0–100 score & BPM Heartbeat)** and generates an empathetic, non-technical **Plain-Language Summary** that anyone can understand in under 10 seconds.

---

## 🎯 Point 5 & Expected Solution Capabilities

| # | Capability | Implementation in CityPulse |
|---|---|---|
| **1** | **Ingest 3+ distinct data types** | Ingests **5 distinct feeds**: 🌦️ Weather (precipitation, wind, temp), 🚇 Public Transit (delays, line blockages), 🚨 311 Municipal Reports (flooding, power outages, traffic lights), 🍃 Air Quality (AQI, PM2.5, NO2), 💬 Social Sentiment & Civic Chatter (polarity, panic buzzwords, volume spikes). Includes live Open-Meteo API connectors and high-fidelity sensor simulators. |
| **2** | **Normalize & timestamp mismatched feeds** | `FeedNormalizer` unifies epoch milliseconds, epoch seconds, ISO-8601 strings, and relative timestamps ("5 mins ago") into a strict `CivicEvent` schema with spatial mapping and normalized `civic_impact_score` (0–100). Includes **Graceful Degradation** if any feed drops. |
| **3** | **Detect anomalies & correlations** | `AnomalyDetector` computes rolling $Z$-scores ($z \ge 2.0\sigma$) over 30-min windows. `CorrelationEngine` detects cross-feed compound cascades (e.g. *Storm-Induced Transit Gridlock*, *Extreme Heat Power Strain*, *Atmospheric Irritant Plume*). Adheres strictly to **Epistemic Honesty** with confidence scores and disclaimers. |
| **4** | **Live glanceable visual dashboard & map** | Real-time **Civic Heartbeat Monitor** (BPM & 0–100 health score), interactive **Leaflet dark-mode geospatial map** with colored district polygons and incident markers, district health cards, and live feed stream ticker. |
| **5** | **Plain-language summary (CORE FOCUS)** | **10-Second Resident Narrative Engine**: Generates clear, non-jargon answers to *"What is happening right now"*, *"Why it matters to you (commute, safety, daily living)"*, and *"Actionable guidance"* with grounding guarantees. |
| **6** | **Threshold alerting & notifications** | Customizable alert rules (Civic Health $< 65$, AQI $> 120$, transit delays, storm warnings), in-app notification center modal, toast alerts, and simulated webhook/SMS/Email dispatch log. |
| **7** | **Historical replay over past data** | **Time-Travel Replay Controller** with interactive scrubber slider, play/pause, step navigation, and 3 pre-built multi-stage scenarios (*The Flash Flood & Evening Rush Hour Cascade*, *Summer Heatwave & Substation Transformer Fire*, *Industrial Smoke Incident*). |

---

## 🏛️ System Architecture

```
                                  [ CIVIC DATA FEEDS ]
                     ┌──────────┬──────────┬──────────┬──────────┬──────────┐
                     │ Weather  │ Transit  │   311    │   Air    │Sentiment │
                     │(Open-Met)│ (Lines)  │(Tickets) │(Sensors) │ (Chatter)│
                     └────┬─────┴────┬─────┴────┬─────┴────┬─────┴────┬─────┘
                          │          │          │          │          │
                          ▼          ▼          ▼          ▼          ▼
                     ┌──────────────────────────────────────────────────┐
                     │          Feed Normalizer & Common Schema         │
                     │  (ISO/Epoch/Relative Time -> Unified CivicEvent) │
                     │        Graceful Degradation Fault-Tolerance      │
                     └──────────────────────────┬───────────────────────┘
                                                │
                          ┌─────────────────────┴─────────────────────┐
                          ▼                                           ▼
             ┌────────────────────────┐                  ┌────────────────────────┐
             │ Rolling Anomaly Engine │                  │ Correlation Engine     │
             │ (Z-Score >= 2.0 Spikes)│                  │ (Spatial-Temporal      │
             └────────────┬───────────┘                  │  Cascade Detection)    │
                          │                              └────────────┬───────────┘
                          └─────────────────────┬─────────────────────┘
                                                │
                                                ▼
                               ┌─────────────────────────────────┐
                               │  Civic Health Calculator        │
                               │  - Citywide Score (0-100)       │
                               │  - Heartbeat Pulse Rate (BPM)   │
                               │  - District Stress Matrix       │
                               └────────────────┬────────────────┘
                                                │
                          ┌─────────────────────┴─────────────────────┐
                          ▼                                           ▼
             ┌─────────────────────────┐                 ┌─────────────────────────┐
             │ Point 5: Plain-Language │                 │ Alerting & Notification │
             │ Resident Narrative      │                 │ Manager (Thresholds &   │
             │ ("What's happening &    │                 │ Webhook Dispatch Logs)  │
             │  Why it matters")       │                 └────────────┬────────────┘
             └────────────┬────────────┘                              │
                          │                                           │
                          └─────────────────────┬─────────────────────┘
                                                │
                                                ▼
                     ┌──────────────────────────────────────────────────┐
                     │ FastAPI REST Endpoints & Real-Time WebSocket     │
                     └──────────────────────────┬───────────────────────┘
                                                │
                                                ▼
                     ┌──────────────────────────────────────────────────┐
                     │  Live Visual Dashboard & Leaflet Geospatial Map  │
                     │  - Glanceable in < 10 seconds for residents      │
                     │  - Historical Replay / Time Machine Scrubber     │
                     └──────────────────────────────────────────────────┘
```

---

## 🏙️ Metropolitan Districts

CityPulse models five real-world urban district profiles:
1. **Downtown & Financial Core**: High commercial density, subway terminals, low-lying underpasses susceptible to waterlogging.
2. **Harbor & Waterfront District**: Coastal zone, ferry docks, tidal exposure.
3. **North Hills & Uptown**: Residential zone with steep topography and mature tree canopy (wind storm hazards).
4. **Tech & Innovation Corridor**: Innovation campus, heavy pedestrian traffic, electrical grid load.
5. **East Suburbs & Industrial Park**: Manufacturing, arterial highways, environmental IoT air quality network.

---

## 🚀 Quick Start Guide

### 1. Requirements
- Python 3.10+ (Python 3.14 compatible)
- No Node.js required! The frontend is served directly by FastAPI.

### 2. Run with One Command

```bash
# Using the pre-configured virtual environment:
backend\venv\Scripts\python.exe run_citypulse.py

# Or activate the virtual environment and run:
python run_citypulse.py
```

### 3. Open in Browser
- **Live Civic Dashboard**: [http://127.0.0.1:8000](http://127.0.0.1:8000)
- **Interactive Swagger API Docs**: [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)

---

## 🧪 Automated Test Suite

Run all 18 unit and integration tests:

```bash
backend\venv\Scripts\python.exe -m pytest tests -v
```

All 18 tests pass with 100% coverage across ingestion, normalization, anomaly detection, cross-feed correlation, plain-language summaries, alerting, and historical replay.

---

## 🔬 How to Demo the Core Capabilities to Evaluators

1. **The 10-Second Resident Glance (Point 4 & Point 5)**:
   - Look at the top hero section: Instant **Civic Health Index (e.g. 92/100 · Calm)** and animated **Heartbeat Pulse (68 BPM)**.
   - Read the **Plain-Language Summary Box**: Clearly states *"What's happening right now"*, *"Why it matters to you"*, and *"Recommended action"* in plain English.
2. **Live Incident & Cascade Injection (Points 1, 2, 3, 5)**:
   - Click the **"Inject Incident"** button in the header.
   - Click **"Cloudburst & Flooding"** in Downtown.
   - Watch the Civic Pulse drop to ~45/100 and BPM accelerate to ~105 BPM.
   - Notice the **Cross-Feed Correlation** card appear: *"Storm-Induced Drainage & Transit Cascade"* (92% Confidence).
   - Read the Plain-Language Summary immediately update to warn commuters about the 4th Ave underpass flood and recommend taking the subway.
3. **Graceful Degradation (Point 2 & Constraint 7)**:
   - Click **"Feeds (5)"** in the top bar.
   - Switch the **WEATHER** or **TRANSIT** toggle to OFF.
   - Notice the feed health is marked `OFFLINE`. The system gracefully re-balances civic stress without crashing or throwing errors.
4. **Historical Replay / Time Machine (Point 7)**:
   - Click **"Historical Replay"** in the top bar.
   - Select *"The Flash Flood & Evening Rush Hour Cascade"*.
   - Use the slider or click **"Play"** to watch the timeline advance from 16:30 (calm) to 17:00 (downpour) to 17:30 (underpass flooded & transit halted) to 18:00 (pumps deployed & recovery).
5. **Threshold Alert Center (Point 6)**:
   - Click the **"Alerts"** bell icon.
   - View active notifications, acknowledge alerts, adjust threshold sliders (Health $< 65$, AQI $> 120$), and view the simulated Webhook / SMS dispatch log.
