"""
CityPulse: The Live Civic Health Dashboard
One-click Application Launcher.

Usage:
    python run_citypulse.py
or:
    python -m uvicorn backend.app.main:app --port 8000 --reload
"""

import sys
import os
import webbrowser
import subprocess
import uvicorn


def main():
    print("=" * 72)
    print("   CITYPULSE — THE LIVE CIVIC HEALTH DASHBOARD (AMIHACKS TRACK B)")
    print("   'One glance should tell a resident what's really happening")
    print("    in their neighborhood — and why it matters.'")
    print("=" * 72)
    print("\n[+] Starting FastAPI civic data fusion & analytics engine...")
    print("[+] Ingesting 5 feeds: Weather, Transit, 311 Reports, AQI, Sentiment")
    print("[+] Real-time Anomaly Detection & Cross-Feed Spatio-Temporal Correlation active")
    print("[+] Plain-Language Resident Narrative Engine initialized")
    print("[+] Historical Replay Scenarios & Threshold Alert Center ready")
    print("\n>>> Open your browser at: http://127.0.0.1:8000")
    print(">>> Interactive API Documentation: http://127.0.0.1:8000/docs")
    print("=" * 72 + "\n")

    # Run Uvicorn server
    uvicorn.run(
        "backend.app.main:app",
        host="127.0.0.1",
        port=8000,
        reload=False,
        log_level="info",
    )


if __name__ == "__main__":
    main()
