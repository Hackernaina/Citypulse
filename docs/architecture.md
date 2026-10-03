# CityPulse Architecture & Data Flow

```text
[ Multi-Feed Ingestion Layer ]
  ├── Weather Ingestor (Open-Meteo API + Barometric/Precipitation Sensors)
  ├── Transit Ingestor (MTA-GTFS Realtime + Subway/Bus Line Delays)
  ├── 311 Municipal Reports (Citizen Tickets, Flooding, Power Outages)
  ├── Air Quality Ingestor (EPA AQI, PM2.5, PM10 IoT Sensor Grid)
  └── Social Sentiment Ingestor (Anonymized Hyperlocal Civic Chatter)
                          │
                          ▼
[ Normalization & Common Civic Event Schema ]
  ├── Timestamp parsing (ISO-8601, Epoch ms/s, Relative times)
  ├── Geospatial District Mapping (Downtown, Waterfront, Hills, Tech, Suburbs)
  ├── 0-100 Standardized Civic Disruption Scoring
  └── Graceful Degradation Engine (Tolerates missing/lagging feeds)
                          │
                          ▼
[ Real-Time Analytics & Correlation Engine ]
  ├── Rolling Window Anomaly Detector (Z-score >= 2.0σ Spikes)
  ├── Spatio-Temporal Cross-Feed Correlation (Cascade Compound Detection)
  └── Epistemic Honesty Evaluator (Probable Links vs Verified Causation)
                          │
                          ▼
[ Health Calculator & Narrative Synthesis (Point 5 Focus) ]
  ├── Civic Health Index (0-100) & Heartbeat Pulse BPM (65-135 BPM)
  ├── 10-Second Executive Resident Headline
  ├── "What Is Happening Right Now" (Plain English)
  ├── "Why It Matters To You" (Everyday Commute, Safety, Property)
  └── "Actionable Advice" (Recommended Actions)
                          │
                          ▼
[ Delivery & Visualization Layer ]
  ├── FastAPI REST & High-Performance WebSocket (/ws/pulse)
  ├── Leaflet Geospatial Dark Map (Color-Coded Districts & Event Halos)
  ├── Real-Time Alert Center & Notification Webhook Dispatcher
  └── Historical Replay Engine (Timeline Scrubber & Incident Playback)
```
