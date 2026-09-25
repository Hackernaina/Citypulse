# Anomaly Detection & Cross-Feed Correlation Methodology

CityPulse fuses heterogeneous civic streams and detects compound incidents through a multi-stage analytical pipeline:

## 1. Rolling Window Statistical Anomaly Detection

For each zone $z \in \text{Districts}$ and metric $m$ (311 complaint count, transit delays, precipitation, AQI, sentiment polarity), the system computes rolling statistics over window $W = 30$ minutes:

$$\mu = \frac{1}{N} \sum_{i=1}^N x_i, \quad \sigma = \sqrt{\frac{1}{N} \sum_{i=1}^N (x_i - \mu)^2}$$

The standardized anomaly score is calculated as:

$$z = \frac{x_{\text{current}} - \mu}{\sigma + \epsilon}$$

An anomaly is surfaced whenever $z \ge 2.0\sigma$ or when critical domain thresholds are breached:
- 311 Complaints: $z \ge 2.0$ with count $\ge 3$
- Transit Delays: Average delay $\ge 18.0$ minutes
- Weather: Rainfall intensity $\ge 15.0$ mm/hr
- Air Quality: $\text{AQI} \ge 120$
- Sentiment: Polarity $\le -0.40$

---

## 2. Spatio-Temporal Cross-Feed Correlation Rules

Isolated anomalies occur routinely in city operations. Compound crises occur when multiple disparate feeds co-occur within the same geographical zone and temporal window:

$$E_{\text{compound}} = \{e \in \text{Events} \mid \text{Zone}(e) = z \land t_{\text{now}} - t_e \le \Delta t\}$$

CityPulse correlates:
1. **Storm-Induced Drainage & Transit Cascade**: Heavy precipitation ($\ge 12$ mm/hr) + 311 waterlogging/drainage calls + transit delay surges ($\ge 15$ mins).
2. **Extreme Heat & Grid Overload Cascade**: Ambient temperature ($\ge 34^\circ\text{C}$) + 311 power/signal outage reports + resident sentiment drop.
3. **Atmospheric Irritant & Smoke Plume**: AQI spike ($\ge 110$) + 311 citizen odor/fume complaints + social chatter volume spike.
4. **Transit Bottleneck & Commuter Outcry**: Transit delays ($\ge 20$ mins) + sharp negative sentiment plunge ($\le -0.50$).

---

## 3. Epistemic Honesty Guarantee

In accordance with responsible smart-city civic communication (Constraint 7), CityPulse never asserts direct causality without physical verification. Every correlation surfaces:
- A calculated confidence score ($0.0 \le c \le 1.0$)
- An explicit Epistemic Disclaimer:  
  *"Probable link based on spatial and temporal co-occurrence. Presented as an emerging pattern, not confirmed direct causation."*
- Complete trace of involved event IDs for municipal auditability.
