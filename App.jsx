import { useMemo, useState } from "react";
import axios from "axios";

const API = "http://127.0.0.1:8000";

function Severity({ value }) {
  return <span className={`badge ${value?.toLowerCase()}`}>{value}</span>;
}

export default function App() {
  const [targetUrl, setTargetUrl] = useState("http://127.0.0.1:8001");
  const [tokenA, setTokenA] = useState("riya-demo-token");
  const [tokenB, setTokenB] = useState("sheetal-demo-token");
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  async function scan() {
    setLoading(true);
    setError("");
    try {
      const response = await axios.post(`${API}/scan`, {
        target_url: targetUrl,
        auth_token: tokenA,
        second_auth_token: tokenB,
        enable_bola: true,
        enable_exposure: true,
        enable_rate_limit: true,
        enable_auth_checks: true,
      });
      setResult(response.data);
    } catch (err) {
      setError(err.response?.data?.detail || err.message);
    } finally {
      setLoading(false);
    }
  }

  const findings = result?.findings || [];
  const critical = result?.summary?.CRITICAL || 0;
  const high = result?.summary?.HIGH || 0;
  const medium = result?.summary?.MEDIUM || 0;
  const low = result?.summary?.LOW || 0;

  const risk = useMemo(() => {
    if (!findings.length) return "0.0";
    const weights = { CRITICAL: 10, HIGH: 7, MEDIUM: 4, LOW: 1, INFO: 0 };
    return Math.min(
      10,
      findings.reduce((sum, f) => sum + weights[f.severity] * f.confidence, 0) / findings.length
    ).toFixed(1);
  }, [findings]);

  return (
    <div className="app">
      <header>
        <div>
          <p className="eyebrow">ZERO-TRUST API SECURITY</p>
          <h1>Sentinel<span>API</span></h1>
          <p className="subtitle">Find the API vulnerability before the breach headline does.</p>
        </div>
        <div className="status">● Scanner MVP</div>
      </header>

      <section className="panel">
        <h2>Start a sandbox scan</h2>
        <p className="muted">Only scan APIs you own or are explicitly authorized to test.</p>

        <div className="form-grid">
          <label>
            Target API
            <input value={targetUrl} onChange={(e) => setTargetUrl(e.target.value)} />
          </label>
          <label>
            User A token
            <input value={tokenA} onChange={(e) => setTokenA(e.target.value)} />
          </label>
          <label>
            User B token
            <input value={tokenB} onChange={(e) => setTokenB(e.target.value)} />
          </label>
        </div>

        <button onClick={scan} disabled={loading}>
          {loading ? "Scanning..." : "Start Security Scan"}
        </button>

        {error && <div className="error">{error}</div>}
      </section>

      {result && (
        <>
          <section className="stats">
            <div className="stat"><span>Endpoints</span><strong>{result.scan.endpoints_scanned}</strong></div>
            <div className="stat"><span>Findings</span><strong>{result.scan.findings_count}</strong></div>
            <div className="stat"><span>Risk Score</span><strong>{risk}</strong></div>
            <div className="stat critical"><span>Critical</span><strong>{critical}</strong></div>
            <div className="stat high"><span>High</span><strong>{high}</strong></div>
            <div className="stat medium"><span>Medium</span><strong>{medium}</strong></div>
            <div className="stat low"><span>Low</span><strong>{low}</strong></div>
          </section>

          <section className="panel">
            <h2>Security Findings</h2>
            {findings.length === 0 ? (
              <p className="muted">No findings were produced by the enabled MVP detectors.</p>
            ) : (
              <div className="findings">
                {findings.map((f) => (
                  <article className="finding" key={f.id}>
                    <div className="finding-top">
                      <div>
                        <Severity value={f.severity} />
                        <h3>{f.title}</h3>
                      </div>
                      <span className="confidence">{Math.round(f.confidence * 100)}% confidence</span>
                    </div>
                    <code>{f.method} {f.endpoint}</code>
                    <p>{f.description}</p>
                    <div className="detail-grid">
                      <div><b>Impact</b><p>{f.impact}</p></div>
                      <div><b>Recommendation</b><p>{f.recommendation}</p></div>
                    </div>
                    <details>
                      <summary>Evidence & Proof of Concept</summary>
                      <pre>{JSON.stringify({ evidence: f.evidence, poc: f.poc }, null, 2)}</pre>
                    </details>
                  </article>
                ))}
              </div>
            )}
          </section>
        </>
      )}
    </div>
  );
}
