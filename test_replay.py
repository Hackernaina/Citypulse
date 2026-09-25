"""
Tests for Historical Replay Mode (Point 7).
"""

from backend.app.replay.replay_controller import ReplayController
from backend.app.analytics.anomaly_detector import AnomalyDetector
from backend.app.analytics.correlation_engine import CorrelationEngine


def test_historical_replay_scenario_loading_and_navigation():
    controller = ReplayController()
    scenarios = controller.get_available_scenarios()
    assert len(scenarios) >= 3

    # Load Flash Flood Scenario
    assert controller.load_scenario("flash_flood") is True
    assert controller.is_active is True
    assert controller.current_step_index == 0

    # Step 0: Baseline events
    events_step_0 = controller.get_events_for_current_step()
    assert len(events_step_0) > 0

    # Step forward to peak disruption step (step 4)
    controller.seek_step(4)
    assert controller.current_step_index == 4
    events_peak = controller.get_events_for_current_step()
    assert len(events_peak) > len(events_step_0)

    # Run anomaly detector & correlation engine on replayed events
    detector = AnomalyDetector(z_threshold=2.0, rolling_minutes=30)
    engine = CorrelationEngine(time_window_minutes=30)

    anomalies = detector.detect_anomalies(events_peak)
    correlations = engine.correlate(events_peak, anomalies)

    # At peak step of flash flood scenario, correlation should be detected!
    assert len(correlations) >= 1
    assert correlations[0].pattern_type == "STORM_TRANSIT_CASCADE"

    # Step back
    controller.step_back()
    assert controller.current_step_index == 3

    # Exit replay
    controller.exit_replay()
    assert controller.is_active is False
