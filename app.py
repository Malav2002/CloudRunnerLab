from flask import Flask, jsonify
from google.cloud import storage, bigquery
import os
import json
from datetime import datetime

app = Flask(__name__)

HTML_STYLE = """
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap" rel="stylesheet">
<style>
  *, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }
  body {
    font-family: 'Inter', 'Segoe UI', sans-serif;
    background: #080811;
    color: #c9cfe8;
    min-height: 100vh;
  }
  /* top gradient bar */
  body::before {
    content: '';
    display: block;
    height: 3px;
    background: linear-gradient(90deg, #6c63ff, #a78bfa, #38bdf8);
  }
  .container { max-width: 920px; margin: 0 auto; padding: 48px 24px 80px; }

  /* hero */
  .hero { margin-bottom: 40px; }
  .hero h1 {
    font-size: 2.6rem; font-weight: 700; letter-spacing: -0.5px;
    background: linear-gradient(135deg, #a78bfa 0%, #38bdf8 100%);
    -webkit-background-clip: text; -webkit-text-fill-color: transparent;
    background-clip: text;
  }
  .hero p { color: #6b7280; margin-top: 10px; font-size: 1.05rem; line-height: 1.7; }

  /* cards */
  .card {
    background: #0e0e1c;
    border: 1px solid #1e1e35;
    border-radius: 16px;
    padding: 28px;
    margin: 20px 0;
    box-shadow: 0 4px 24px rgba(0,0,0,0.4);
    transition: border-color 0.2s;
  }
  .card:hover { border-color: #6c63ff44; }
  .card h2 {
    font-size: 1rem; font-weight: 600; text-transform: uppercase;
    letter-spacing: 1px; color: #6b7280;
    margin-bottom: 18px; padding-bottom: 12px;
    border-bottom: 1px solid #1e1e35;
  }

  /* stat grid */
  .grid { display: grid; grid-template-columns: repeat(3, 1fr); gap: 16px; margin: 24px 0; }
  .stat-card {
    background: #0e0e1c; border: 1px solid #1e1e35; border-radius: 14px;
    padding: 22px 18px; text-align: center;
    box-shadow: 0 2px 12px rgba(0,0,0,0.3);
  }
  .stat { font-size: 1.9rem; font-weight: 700; color: #a78bfa; line-height: 1.2; }
  .label { font-size: 0.72rem; color: #4b5563; text-transform: uppercase; letter-spacing: 1.2px; margin-top: 6px; }

  /* nav buttons */
  .nav { display: flex; flex-wrap: wrap; gap: 10px; margin-top: 4px; }
  .nav a {
    display: inline-flex; align-items: center; gap: 7px;
    background: linear-gradient(135deg, #6c63ff, #a78bfa);
    color: #fff; text-decoration: none;
    padding: 10px 20px; border-radius: 10px;
    font-weight: 600; font-size: 0.9rem;
    box-shadow: 0 2px 10px #6c63ff44;
    transition: opacity 0.2s, transform 0.15s;
  }
  .nav a:hover { opacity: 0.85; transform: translateY(-1px); }
  .nav a.secondary {
    background: #1a1a2e;
    box-shadow: none; border: 1px solid #2a2a45; color: #a78bfa;
  }

  /* badges */
  .badges { display: flex; flex-wrap: wrap; gap: 8px; }
  .badge {
    background: #13132a; border: 1px solid #2a2a45;
    color: #a78bfa; padding: 5px 13px;
    border-radius: 20px; font-size: 0.8rem; font-weight: 500;
  }

  /* table */
  .table-wrap { overflow-x: auto; border-radius: 10px; }
  table { width: 100%; border-collapse: collapse; }
  thead tr { background: #13132a; }
  th {
    padding: 13px 16px; text-align: left;
    font-size: 0.75rem; text-transform: uppercase; letter-spacing: 1px;
    color: #6b7280; font-weight: 600;
  }
  td { padding: 12px 16px; border-bottom: 1px solid #13132a; font-size: 0.9rem; }
  tbody tr:last-child td { border-bottom: none; }
  tbody tr:hover td { background: #111124; }
  td.rank { color: #4b5563; font-weight: 600; font-size: 0.8rem; width: 40px; }
  td.license-name { color: #e2e8f0; font-weight: 500; }
  td.count { color: #a78bfa; font-weight: 600; font-family: monospace; }

  /* bar */
  .bar-bg { background: #1a1a2e; border-radius: 6px; height: 8px; min-width: 80px; }
  .bar-fill {
    height: 8px; border-radius: 6px;
    background: linear-gradient(90deg, #6c63ff, #38bdf8);
    transition: width 0.6s ease;
  }

  /* footer */
  .ts { color: #374151; font-size: 0.75rem; margin-top: 16px; padding-top: 16px; border-top: 1px solid #13132a; }

  /* endpoint list */
  .endpoint-list { display: flex; flex-direction: column; gap: 10px; }
  .endpoint {
    display: flex; align-items: center; justify-content: space-between;
    background: #13132a; border-radius: 10px; padding: 12px 16px;
    border: 1px solid #1e1e35;
  }
  .endpoint-path { font-family: monospace; color: #38bdf8; font-size: 0.9rem; }
  .endpoint-desc { color: #4b5563; font-size: 0.82rem; }
  .endpoint-link {
    color: #a78bfa; font-size: 0.8rem; font-weight: 600;
    text-decoration: none; padding: 4px 12px;
    border: 1px solid #6c63ff44; border-radius: 6px;
  }
  .endpoint-link:hover { background: #6c63ff22; }
</style>
"""


@app.route('/')
def index():
    return f"""<!DOCTYPE html>
    <html lang="en"><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1">
    <title>Cloud Run Lab</title>{HTML_STYLE}</head>
    <body><div class="container">
      <div class="hero">
        <h1>Cloud Run Lab</h1>
        <p>A containerized Flask app deployed on Google Cloud Run,<br>
           integrated with Cloud Storage and BigQuery.</p>
      </div>

      <div class="card">
        <h2>Endpoints</h2>
        <div class="endpoint-list">
          <div class="endpoint">
            <div><div class="endpoint-path">GET /dashboard</div>
              <div class="endpoint-desc">Interactive GitHub license popularity dashboard</div></div>
            <a class="endpoint-link" href="/dashboard">Open →</a>
          </div>
          <div class="endpoint">
            <div><div class="endpoint-path">GET /query</div>
              <div class="endpoint-desc">Raw BigQuery results as JSON</div></div>
            <a class="endpoint-link" href="/query">Open →</a>
          </div>
          <div class="endpoint">
            <div><div class="endpoint-path">GET /upload</div>
              <div class="endpoint-desc">Upload metadata JSON to Cloud Storage</div></div>
            <a class="endpoint-link" href="/upload">Open →</a>
          </div>
          <div class="endpoint">
            <div><div class="endpoint-path">GET /health</div>
              <div class="endpoint-desc">Service health check</div></div>
            <a class="endpoint-link" href="/health">Open →</a>
          </div>
        </div>
      </div>

      <div class="card">
        <h2>Stack</h2>
        <div class="badges">
          <span class="badge">Python 3.9</span>
          <span class="badge">Flask</span>
          <span class="badge">Gunicorn</span>
          <span class="badge">Docker</span>
          <span class="badge">Cloud Run</span>
          <span class="badge">Cloud Storage</span>
          <span class="badge">BigQuery</span>
        </div>
      </div>
    </div></body></html>"""


BQ_QUERY = """
    SELECT
      license,
      COUNT(*) AS repo_count
    FROM `bigquery-public-data.github_repos.licenses`
    WHERE license IS NOT NULL AND license != ''
    GROUP BY license
    ORDER BY repo_count DESC
    LIMIT 15
"""


def run_query():
    client = bigquery.Client()
    return list(client.query(BQ_QUERY).result())


@app.route('/dashboard')
def dashboard():
    try:
        results = run_query()
    except Exception as e:
        return f"<p style='color:red'>Query error: {e}</p>", 500

    total = sum(r.repo_count for r in results)
    top_license = results[0].license if results else "N/A"
    ts = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC")

    rows_html = "".join(
        f"<tr>"
        f"<td class='rank'>{i+1}</td>"
        f"<td class='license-name'>{r.license}</td>"
        f"<td class='count'>{r.repo_count:,}</td>"
        f"<td><div class='bar-bg'><div class='bar-fill' style='width:{int(r.repo_count/results[0].repo_count*100)}%'></div></div></td>"
        f"</tr>"
        for i, r in enumerate(results)
    )

    return f"""<!DOCTYPE html>
    <html lang="en"><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1">
    <title>Dashboard — Cloud Run Lab</title>{HTML_STYLE}</head>
    <body><div class="container">
      <div class="hero">
        <h1>GitHub License Dashboard</h1>
        <p>Most popular open-source licenses across GitHub repos —
           sourced from <strong style="color:#a78bfa">bigquery-public-data.github_repos</strong>.</p>
      </div>

      <div class="grid">
        <div class="stat-card">
          <div class="stat">{len(results)}</div>
          <div class="label">Licenses Tracked</div>
        </div>
        <div class="stat-card">
          <div class="stat">{total:,}</div>
          <div class="label">Total Repos</div>
        </div>
        <div class="stat-card">
          <div class="stat" style="font-size:1.1rem;color:#38bdf8">{top_license}</div>
          <div class="label">Most Popular</div>
        </div>
      </div>

      <div class="card">
        <h2>Top Licenses by Repo Count</h2>
        <div class="table-wrap">
          <table>
            <thead><tr><th>#</th><th>License</th><th>Repos</th><th>Popularity</th></tr></thead>
            <tbody>{rows_html}</tbody>
          </table>
        </div>
        <div class="ts">&#128337; Last queried: {ts}</div>
      </div>

      <div class="nav">
        <a class="secondary" href="/">← Home</a>
        <a href="/query">JSON →</a>
      </div>
    </div></body></html>"""


@app.route('/query')
def query():
    try:
        results = [
            {"license": r.license, "repo_count": r.repo_count}
            for r in run_query()
        ]
        return jsonify({"status": "ok", "count": len(results), "data": results})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


@app.route('/upload')
def upload_file():
    bucket_name = os.environ.get('BUCKET_NAME')
    if not bucket_name:
        return jsonify({"status": "error", "message": "BUCKET_NAME not set"}), 500

    storage_client = storage.Client()
    bucket = storage_client.bucket(bucket_name)

    metadata = {
        "app": "cloud-run-lab",
        "uploaded_at": datetime.utcnow().isoformat() + "Z",
        "version": "1.0.0",
        "dataset": "bigquery-public-data.github_repos.licenses",
        "description": "GitHub repo license metadata snapshot"
    }

    blob = bucket.blob("metadata/run_metadata.json")
    blob.upload_from_string(
        json.dumps(metadata, indent=2),
        content_type="application/json"
    )
    return jsonify({
        "status": "ok",
        "message": f"Uploaded metadata/run_metadata.json to {bucket_name}",
        "metadata": metadata
    })


@app.route('/health')
def health():
    return jsonify({
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "service": "cloud-run-lab"
    })


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port)
