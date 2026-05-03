import json
import os
import datetime
from typing import Dict, Any, List
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.application import MIMEApplication
import smtplib
from collections import defaultdict

# --- Configuration (Should be consistent with conftest.py) ---
REPORT_DIR = "test_reports"
HTML_REPORT_FILE = os.path.join(REPORT_DIR, "latest_report.html")


# --- Status Indicator Logic ---

def get_overall_status(pass_percentage: float) -> tuple:
    """
    Determines the overall status based on pass percentage.
    Returns: (status_label, status_color, status_icon)
    - Pass: > 90%
    - Warning: 70% - 90%
    - Failure: < 70%
    """
    if pass_percentage > 90:
        return ("PASS", "#28a745", "✓")
    elif pass_percentage >= 70:
        return ("WARNING", "#ffc107", "⚠")
    else:
        return ("FAILURE", "#dc3545", "✗")
    
            color: #f8fafc;
            margin: 32px 0 20px;
            font-size: clamp(1.2rem, 2vw, 1.6rem);
            border-bottom: 2px solid rgba(96, 165, 250, 0.2);
            padding-bottom: 12px;
            letter-spacing: -0.02em;
        }}

        .status-container {{
            background: linear-gradient(135deg, rgba(15, 23, 42, 0.98), rgba(30, 41, 59, 0.95));
            border: 2px solid {status_color};
            border-left: 6px solid {status_color};
            padding: 32px;
            margin-bottom: 28px;
            border-radius: 20px;
            box-shadow: var(--shadow);
            display: grid;
            gap: 16px;
        }}

        .status-badge {{
            display: inline-flex;
            align-items: center;
            justify-content: center;
            gap: 0.75rem;
            background: linear-gradient(135deg, {status_color}, {status_color}dd);
            color: #ffffff;
            padding: 16px 32px;
            border-radius: 999px;
            font-size: 1.15rem;
            font-weight: 800;
            letter-spacing: 0.02em;
            box-shadow: 0 20px 50px rgba(0, 0, 0, 0.3);
            width: fit-content;
            text-transform: uppercase;
        }}

        .status-icon {{
            font-size: 1.8rem;
        }}

        .status-container p {{
            color: var(--muted);
            margin: 0;
            font-size: 0.96rem;
        }}

        .metadata {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
            gap: 16px;
            margin-bottom: 28px;
        }}

        .metadata-item {{
            background: rgba(255, 255, 255, 0.05);
            border: 2px solid rgba(96, 165, 250, 0.2);
            border-radius: 18px;
            padding: 22px;
            text-align: center;
            box-shadow: var(--shadow-inset);
            transition: all 0.3s ease;
        }}

        .metadata-item:hover {{
            border-color: rgba(96, 165, 250, 0.5);
            background: rgba(255, 255, 255, 0.08);
        }}

        .metadata-item strong {{
            display: block;
            font-size: 1.25rem;
            color: #60a5fa;
            margin-bottom: 8px;
            font-weight: 800;
        }}

        .metadata-item span {{
            font-size: 0.9rem;
            color: var(--muted);
            text-transform: uppercase;
            letter-spacing: 0.05em;
        }}

        .summary-cards {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(160px, 1fr));
            gap: 18px;
            margin-bottom: 28px;
        }}

        .card {{
            background: linear-gradient(135deg, rgba(255, 255, 255, 0.06), rgba(255, 255, 255, 0.02));
            border: 2px solid rgba(255, 255, 255, 0.1);
            border-radius: 20px;
            padding: 24px;
            text-align: center;
            box-shadow: var(--shadow-soft), var(--shadow-inset);
            min-height: 150px;
            transition: all 0.3s ease;
        }}

        .card:hover {{
            border-color: rgba(255, 255, 255, 0.2);
            background: linear-gradient(135deg, rgba(255, 255, 255, 0.08), rgba(255, 255, 255, 0.04));
            transform: translateY(-4px);
        }}

        .card h3 {{
            font-size: 0.85rem;
            text-transform: uppercase;
            letter-spacing: 0.1em;
            color: var(--muted);
            margin-bottom: 14px;
            font-weight: 700;
        }}

        .card p {{
            font-size: 2.8rem;
            font-weight: 900;
            margin: 0;
            color: #edf2f7;
            letter-spacing: -0.03em;
        }}

        .card small {{
            display: block;
            margin-top: 10px;
            color: var(--muted);
            font-size: 0.9rem;
        }}

        .card-total p {{ color: #60a5fa; }}
        .card-pass p {{ color: #4ade80; }}
        .card-fail p {{ color: #f87171; }}
        .card-skip p {{ color: #fbbf24; }}

        .progress-bar-container {{
            height: 50px;
            background: rgba(255, 255, 255, 0.05);
            border: 2px solid rgba(255, 255, 255, 0.1);
            border-radius: 999px;
            overflow: hidden;
            margin-bottom: 30px;
            display: flex;
            box-shadow: var(--shadow-soft);
        }}

        .progress-bar {{
            height: 100%;
            display: flex;
            align-items: center;
            justify-content: center;
            color: #ffffff;
            font-size: 0.95rem;
            font-weight: 800;
            transition: width 0.6s cubic-bezier(0.4, 0, 0.2, 1);
            white-space: nowrap;
            min-width: 60px;
            letter-spacing: 0.02em;
        }}

        .progress-pass {{ background: linear-gradient(90deg, #22c55e, #16a34a); }}
        .progress-fail {{ background: linear-gradient(90deg, #ef4444, #dc2626); }}
        .progress-skip {{ background: linear-gradient(90deg, #f59e0b, #d97706); }}

        .test-results-container {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(320px, 1fr));
            gap: 20px;
            margin-bottom: 28px;
        }}

        .test-group {{
            background: linear-gradient(135deg, rgba(15, 23, 42, 0.95), rgba(30, 41, 59, 0.90));
            border: 2px solid rgba(255, 255, 255, 0.08);
            border-radius: 20px;
            overflow: hidden;
            box-shadow: var(--shadow);
            transition: all 0.3s ease;
        }}

        .test-group:hover {{
            border-color: rgba(255, 255, 255, 0.15);
        }}

        .test-group-header {{
            background: linear-gradient(90deg, rgba(96, 165, 250, 0.15), rgba(139, 92, 246, 0.1));
            padding: 16px 24px;
            cursor: pointer;
            display: flex;
            justify-content: space-between;
            align-items: center;
            user-select: none;
            transition: all 0.3s ease;
            border-bottom: 1px solid rgba(255, 255, 255, 0.08);
        }}

        .test-group-header:hover {{
            background: linear-gradient(90deg, rgba(96, 165, 250, 0.2), rgba(139, 92, 246, 0.15));
        }}

        .test-group-header h3 {{
            margin: 0;
            font-size: 1.1rem;
            font-weight: 700;
            color: #f8fafc;
        }}

        .test-count {{
            background: rgba(96, 165, 250, 0.2);
            padding: 6px 14px;
            border-radius: 999px;
            font-size: 0.85rem;
            font-weight: 700;
            color: #60a5fa;
        }}

        .toggle-icon {{
            font-size: 1.2rem;
            transition: transform 0.3s ease;
        }}

        .test-group-header.collapsed .toggle-icon {{
            transform: rotate(-90deg);
        }}

        .test-list {{
            padding: 16px 24px;
            max-height: 400px;
            overflow-y: auto;
            transition: all 0.3s ease;
        }}

        .test-list.collapsed {{
            max-height: 0;
            padding: 0 24px;
            overflow: hidden;
        }}

        .test-item {{
            list-style: none;
            padding: 12px;
            margin-bottom: 8px;
            border-radius: 12px;
            font-size: 0.95rem;
            font-weight: 500;
            display: flex;
            align-items: center;
            gap: 10px;
            transition: all 0.2s ease;
            word-break: break-word;
        }}

        .test-item:hover {{
            transform: translateX(6px);
            background: rgba(255, 255, 255, 0.06);
        }}

        .test-pass {{
            background: rgba(34, 197, 94, 0.1);
            color: #86efac;
            border-left: 4px solid #22c55e;
        }}

        .test-fail {{
            background: rgba(239, 68, 68, 0.1);
            color: #fca5a5;
            border-left: 4px solid #ef4444;
        }}

        .test-skip {{
            background: rgba(245, 158, 11, 0.1);
            color: #fde68a;
            border-left: 4px solid #f59e0b;
        }}

        .test-name {{
            font-weight: 600;
            font-family: 'Courier New', monospace;
            font-size: 0.9rem;
        }}

        .table-wrapper {{
            overflow-x: auto;
            margin-bottom: 28px;
            border-radius: 22px;
            border: 2px solid rgba(255, 255, 255, 0.08);
            background: rgba(255, 255, 255, 0.03);
            box-shadow: var(--shadow);
            backdrop-filter: blur(16px);
        }}

        table {{
            width: 100%;
            min-width: 720px;
            border-collapse: collapse;
            color: var(--text);
        }}

        th {{
            background: linear-gradient(90deg, rgba(15, 23, 42, 0.98), rgba(30, 41, 59, 0.95));
            color: #60a5fa;
            padding: 18px 20px;
            text-align: left;
            font-weight: 800;
            letter-spacing: 0.05em;
            font-size: 0.95rem;
            position: sticky;
            top: 0;
            z-index: 1;
            text-transform: uppercase;
        }}

        td {{
            padding: 16px 20px;
            border-bottom: 1px solid rgba(255, 255, 255, 0.06);
            font-size: 0.95rem;
            color: #d1d5db;
        }}

        tr:nth-child(even) {{ background: rgba(255, 255, 255, 0.03); }}
        tr:hover {{ background: rgba(255, 255, 255, 0.07); }}

        .badge {{
            display: inline-flex;
            align-items: center;
            justify-content: center;
            padding: 8px 14px;
            border-radius: 999px;
            font-weight: 800;
            font-size: 0.82rem;
            white-space: nowrap;
            letter-spacing: 0.02em;
        }}

        .badge-pass {{ background: rgba(34, 197, 94, 0.18); color: #4ade80; }}
        .badge-fail {{ background: rgba(239, 68, 68, 0.18); color: #f87171; }}
        .badge-skip {{ background: rgba(245, 158, 11, 0.18); color: #fbbf24; }}

        @media (max-width: 768px) {{
            body {{ padding: 0; }}
            .header-content {{ flex-direction: column; align-items: flex-start; }}
            .header h1 {{ font-size: 1.3rem; }}
            .report-selector {{ width: 100%; }}
            .report-selector select {{ width: 100%; }}
            .container {{ padding: 0 16px; margin: 16px auto; }}
            h2 {{ font-size: 1.3rem; }}
            .metadata {{ grid-template-columns: 1fr; }}
            .summary-cards {{ grid-template-columns: repeat(2, minmax(0, 1fr)); }}
            .card {{ padding: 18px; min-height: 130px; }}
            .card p {{ font-size: 2rem; }}
            .progress-bar-container {{ height: 40px; }}
            .test-results-container {{ grid-template-columns: 1fr; }}
            th, td {{ padding: 12px 14px; }}
            table {{ min-width: 560px; font-size: 0.9rem; }}
        }}

        @media (max-width: 520px) {{
            h2 {{ font-size: 1.15rem; }}
            .summary-cards {{ grid-template-columns: 1fr; }}
            .card p {{ font-size: 1.6rem; }}
            table {{ min-width: 100%; font-size: 0.85rem; }}
            th, td {{ padding: 10px 12px; }}
            .progress-bar-container {{ height: 36px; }}
            .status-badge {{ font-size: 0.95rem; padding: 12px 24px; }}
            .test-item {{ font-size: 0.9rem; }}
        }}

        .footer {{
            text-align: center;
            margin: 40px 0 28px;
            padding-top: 24px;
            border-top: 2px solid rgba(255, 255, 255, 0.08);
            color: var(--muted);
            font-size: 0.92rem;
        }}

        .footer p {{
            margin: 6px 0;
        }}

        ::-webkit-scrollbar {{
            width: 8px;
            height: 8px;
        }}

        ::-webkit-scrollbar-track {{
            background: rgba(255, 255, 255, 0.05);
        }}

        ::-webkit-scrollbar-thumb {{
            background: rgba(96, 165, 250, 0.3);
            border-radius: 999px;
        }}

        ::-webkit-scrollbar-thumb:hover {{
            background: rgba(96, 165, 250, 0.5);
        }}
    </style>
    <script>
        function toggleTestGroup(element) {{
            const header = element;
            const list = header.nextElementSibling;
            header.classList.toggle('collapsed');
            list.classList.toggle('collapsed');
        }}

        function loadReport(reportName) {{
            if (reportName && reportName !== 'current') {{
                window.location.href = reportName;
            }}
        }}

        document.addEventListener('DOMContentLoaded', function() {{
            const testHeaders = document.querySelectorAll('.test-group-header');
            testHeaders.forEach(header => {{
                header.addEventListener('click', function() {{
                    toggleTestGroup(this);
                }});
            }});
        }});
    </script>
</head>
<body>
    <div class="header">
        <div class="header-content">
            <h1>🧪 Pytest Report</h1>
            <div class="report-selector">
                <label for="report-select">Previous Reports:</label>
                <select id="report-select" onchange="loadReport(this.value)">
                    <option value="current">Current Report</option>
                </select>
            </div>
        </div>
    </div>

    <div class="container">
        <!-- Overall Status Section -->
        <div class="status-container">
            <div class="status-badge">
                <span class="status-icon">{status_icon}</span>
                {status_label} - {pass_percent:.1f}% Pass Rate
            </div>
            <p>Overall test execution status for current run</p>
        </div>

        <!-- Metadata Section -->
        <div class="metadata">
            <div class="metadata-item">
                <strong>{current_env}</strong>
                <span>Environment</span>
            </div>
            <div class="metadata-item">
                <strong style="word-break: break-word;">{current_date}</strong>
                <span>Execution Date</span>
            </div>
            <div class="metadata-item">
                <strong style="word-break: break-word;">{current_timestamp}</strong>
                <span>Execution Time</span>
            </div>
            <div class="metadata-item">
                <strong style="word-break: break-word;">{execution_time}</strong>
                <span>Total Duration</span>
            </div>
        </div>

        <h2>Current Run Summary</h2>
        <div class="summary-cards">
            <div class="card card-total">
                <h3>Total Tests</h3>
                <p>{total_tests}</p>
            </div>
            <div class="card card-pass">
                <h3>Passed</h3>
                <p>{passed}</p>
                <small>{pass_percent:.1f}%</small>
            </div>
            <div class="card card-fail">
                <h3>Failed</h3>
                <p>{failed}</p>
                <small>{fail_percent:.1f}%</small>
            </div>
            <div class="card card-skip">
                <h3>Skipped</h3>
                <p>{skipped}</p>
                <small>{skip_percent:.1f}%</small>
            </div>
        </div>

        <div class="progress-bar-container">
            <div class="progress-bar progress-pass" style="width: {pass_percent:.1f}%;">{passed if passed > 0 else ''}</div>
            <div class="progress-bar progress-fail" style="width: {fail_percent:.1f}%;">{failed if failed > 0 else ''}</div>
            <div class="progress-bar progress-skip" style="width: {skip_percent:.1f}%;">{skipped if skipped > 0 else ''}</div>
        </div>

        <h2>Test Details</h2>
        <div class="test-results-container">
            <div class="test-group">
                <div class="test-group-header">
                    <h3>✓ Passed Tests</h3>
                    <div style="display: flex; gap: 10px; align-items: center;">
                        <span class="test-count">{len(passed_tests)}</span>
                        <span class="toggle-icon">▼</span>
                    </div>
                </div>
                <ul class="test-list">
                    {passed_rows if passed_rows else '<li style="color: #94a3b8; padding: 12px;">No passed tests</li>'}
                </ul>
            </div>

            <div class="test-group">
                <div class="test-group-header">
                    <h3>✗ Failed Tests</h3>
                    <div style="display: flex; gap: 10px; align-items: center;">
                        <span class="test-count">{len(failed_tests)}</span>
                        <span class="toggle-icon">▼</span>
                    </div>
                </div>
                <ul class="test-list">
                    {failed_rows if failed_rows else '<li style="color: #94a3b8; padding: 12px;">No failed tests</li>'}
                </ul>
            </div>

            <div class="test-group">
                <div class="test-group-header">
                    <h3>⊘ Skipped Tests</h3>
                    <div style="display: flex; gap: 10px; align-items: center;">
                        <span class="test-count">{len(skipped_tests)}</span>
                        <span class="toggle-icon">▼</span>
                    </div>
                </div>
                <ul class="test-list">
                    {skipped_rows if skipped_rows else '<li style="color: #94a3b8; padding: 12px;">No skipped tests</li>'}
                </ul>
            </div>
        </div>

        <h2>Package-wise Results</h2>
        <div class="table-wrapper">
            <table>
                <thead>
                    <tr>
                        <th>Package</th>
                        <th>Passed</th>
                        <th>Failed</th>
                        <th>Skipped</th>
                        <th>Total</th>
                        <th>Pass Rate</th>
                    </tr>
                </thead>
                <tbody>
                    {package_rows if package_rows else '<tr><td colspan="6" style="text-align: center; color: #999;">No test packages found</td></tr>'}
                </tbody>
            </table>
        </div>

        <h2>Historical Trend (Last 7 Days) - {current_env}</h2>
        <div class="table-wrapper">
            <table>
                <thead>
                    <tr>
                        <th>Date</th>
                        <th>Passed</th>
                        <th>Failed</th>
                        <th>Skipped</th>
                        <th>Total</th>
                        <th>Pass Rate</th>
                    </tr>
                </thead>
                <tbody>
                    {history_rows if history_rows else '<tr><td colspan="6" style="text-align: center; color: #999;">No historical data available</td></tr>'}
                </tbody>
            </table>
        </div>

        <div class="footer">
            <p>Report generated on {datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")}</p>
            <p>This is an automated test report. For more details, please contact your QA team.</p>
        </div>
    </div>
</body>
</html>
    """

    # Save report with timestamp for history
    timestamp_filename = datetime.datetime.now().strftime("report_%Y%m%d_%H%M%S.html")
    timestamped_report_path = os.path.join(REPORT_DIR, timestamp_filename)

    with open(HTML_REPORT_FILE, 'w', encoding='utf-8') as f:
        f.write(html_content)

    print(f"✓ HTML report generated: {HTML_REPORT_FILE}")
            text-align: center;
            margin-bottom: 24px;
            font-size: clamp(2rem, 4vw, 2.8rem);
            letter-spacing: -0.04em;
        }}

        h2 {{
            color: #f8fafc;
            margin: 0 24px 16px;
            font-size: clamp(1.2rem, 2vw, 1.6rem);
            border-bottom: 1px solid rgba(148, 163, 184, 0.18);
            padding-bottom: 10px;
        }}

        .status-container {{
            padding: 26px 28px;
            margin: 0 24px 28px;
            background: linear-gradient(180deg, rgba(15, 23, 42, 0.96), rgba(15, 23, 42, 0.90));
            border-left: 5px solid {status_color};
            border-radius: 18px;
            box-shadow: var(--shadow-soft);
            display: grid;
            gap: 14px;
        }}

        .status-badge {{
            display: inline-flex;
            align-items: center;
            justify-content: center;
            gap: 0.75rem;
            background: {status_color};
            color: #ffffff;
            padding: 14px 28px;
            border-radius: 999px;
            font-size: 1rem;
            font-weight: 700;
            letter-spacing: 0.02em;
            box-shadow: 0 16px 40px rgba(0, 0, 0, 0.2);
            width: fit-content;
            margin-bottom: 0;
        }}

        .status-icon {{
            font-size: 1.4rem;
        }}

        .status-container p {{
            color: var(--muted);
            margin: 0;
            font-size: 0.96rem;
        }}

        .metadata {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(160px, 1fr));
            gap: 16px;
            margin: 0 24px 28px;
        }}

        .metadata-item {{
            background: rgba(255, 255, 255, 0.04);
            border: 1px solid rgba(255, 255, 255, 0.08);
            border-radius: 18px;
            padding: 20px;
            text-align: center;
            box-shadow: inset 0 0 0 1px rgba(255, 255, 255, 0.02);
        }}

        .metadata-item strong {{
            display: block;
            font-size: 1.1rem;
            color: #f8fafc;
            margin-bottom: 8px;
        }}

        .metadata-item span {{
            font-size: 0.9rem;
            color: var(--muted);
        }}

        .summary-cards {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(140px, 1fr));
            gap: 18px;
            margin: 0 24px 28px;
        }}

        .card {{
            background: rgba(255, 255, 255, 0.04);
            border: 1px solid rgba(255, 255, 255, 0.08);
            border-radius: 20px;
            padding: 20px;
            text-align: center;
            box-shadow: var(--shadow-soft);
            min-height: 140px;
        }}

        .card h3 {{
            font-size: 0.86rem;
            text-transform: uppercase;
            letter-spacing: 0.1em;
            color: var(--muted);
            margin-bottom: 14px;
        }}

        .card p {{
            font-size: 2.3rem;
            font-weight: 800;
            margin: 0;
            color: #edf2f7;
        }}

        .card small {{
            display: block;
            margin-top: 8px;
            color: var(--muted);
            font-size: 0.9rem;
        }}

        .card-total p {{ color: #f8fafc; }}
        .card-pass p {{ color: #86efac; }}
        .card-fail p {{ color: #fca5a5; }}
        .card-skip p {{ color: #fcd34d; }}

        .progress-bar-container {{
            height: 44px;
            background: rgba(255, 255, 255, 0.05);
            border: 1px solid rgba(255, 255, 255, 0.08);
            border-radius: 999px;
            overflow: hidden;
            margin: 0 24px 30px;
            display: flex;
            box-shadow: inset 0 2px 10px rgba(0, 0, 0, 0.18);
        }}

        .progress-bar {{
            height: 100%;
            display: flex;
            align-items: center;
            justify-content: center;
            color: #ffffff;
            font-size: 0.95rem;
            font-weight: 700;
            transition: width 0.45s ease;
            white-space: nowrap;
            min-width: 50px;
        }}

        .progress-pass {{ background: linear-gradient(90deg, #22c55e, #16a34a); }}
        .progress-fail {{ background: linear-gradient(90deg, #ef4444, #dc2626); }}
        .progress-skip {{ background: linear-gradient(90deg, #f59e0b, #d97706); }}

        .table-wrapper {{
            overflow-x: auto;
            margin: 0 24px 28px;
            border-radius: 22px;
            border: 1px solid rgba(255, 255, 255, 0.08);
            background: rgba(255, 255, 255, 0.03);
            box-shadow: 0 24px 80px rgba(0, 0, 0, 0.08);
            backdrop-filter: blur(16px);
        }}

        table {{
            width: 100%;
            min-width: 720px;
            border-collapse: collapse;
            color: var(--text);
        }}

        th {{
            background: rgba(15, 23, 42, 0.92);
            color: #ffffff;
            padding: 16px 18px;
            text-align: left;
            font-weight: 700;
            letter-spacing: 0.02em;
            font-size: 0.95rem;
            position: sticky;
            top: 0;
        }}

        td {{
            padding: 14px 18px;
            border-bottom: 1px solid rgba(255, 255, 255, 0.06);
            font-size: 0.95rem;
            color: #d1d5db;
        }}

        tr:nth-child(even) {{
            background: rgba(255, 255, 255, 0.03);
        }}

        tr:hover {{
            background: rgba(255, 255, 255, 0.06);
        }}

        .badge {{
            display: inline-flex;
            align-items: center;
            justify-content: center;
            padding: 6px 12px;
            border-radius: 999px;
            font-weight: 700;
            font-size: 0.82rem;
            white-space: nowrap;
        }}

        .badge-pass {{ background: rgba(34, 197, 94, 0.18); color: #86efac; }}
        .badge-fail {{ background: rgba(239, 68, 68, 0.18); color: #fca5a5; }}
        .badge-skip {{ background: rgba(245, 158, 11, 0.18); color: #fde68a; }}

        @media (max-width: 768px) {{
            body {{ padding: 14px; }}
            .container {{ padding: 18px; }}
            h1 {{ font-size: 1.9rem; }}
            h2 {{ font-size: 1.15rem; }}
            .metadata {{ grid-template-columns: 1fr; }}
            .summary-cards {{ grid-template-columns: repeat(2, minmax(0, 1fr)); }}
            .card {{ padding: 16px; }}
            .card p {{ font-size: 1.8rem; }}
            .progress-bar-container {{ height: 32px; }}
            th, td {{ padding: 12px 14px; }}
            table {{ min-width: 540px; }}
        }}

        @media (max-width: 520px) {{
            h1 {{ font-size: 1.6rem; }}
            h2 {{ font-size: 1rem; }}
            .summary-cards {{ grid-template-columns: 1fr; }}
            .card p {{ font-size: 1.5rem; }}
            table {{ min-width: 100%; font-size: 0.9rem; }}
            th, td {{ padding: 10px 12px; }}
            .progress-bar-container {{ height: 28px; }}
        }}

        .footer {{
            text-align: center;
            margin: 0 24px 28px;
            padding-top: 20px;
            border-top: 1px solid rgba(255, 255, 255, 0.08);
            color: var(--muted);
            font-size: 0.92rem;
        }}
    </style>
</head>
<body>
    <div class="container">
        <h1>Automation Test Report</h1>

        <!-- Overall Status Section -->
        <div class="status-container">
            <div class="status-badge">
                <span class="status-icon">{status_icon}</span>
                {status_label} - {pass_percent:.1f}% Pass Rate
            </div>
            <p style="color: #666; margin-top: 10px;">Overall test execution status for current run</p>
        </div>

        <!-- Metadata Section -->
        <div class="metadata">
            <div class="metadata-item">
                <strong>{current_env}</strong>
                <span>Environment</span>
            </div>
            <div class="metadata-item">
                <strong style="word-break: break-word;">{current_date}</strong>
                <span>Execution Date</span>
            </div>
            <div class="metadata-item">
                <strong style="word-break: break-word;">{execution_time}</strong>
                <span>Total Execution Time</span>
            </div>
        </div>

        <h2>Current Run Summary</h2>
        <div class="summary-cards">
            <div class="card card-total">
                <h3>Total Tests</h3>
                <p>{total_tests}</p>
            </div>
            <div class="card card-pass">
                <h3>Passed</h3>
                <p>{passed}</p>
                <small>{pass_percent:.1f}%</small>
            </div>
            <div class="card card-fail">
                <h3>Failed</h3>
                <p>{failed}</p>
                <small>{fail_percent:.1f}%</small>
            </div>
            <div class="card card-skip">
                <h3>Skipped</h3>
                <p>{skipped}</p>
                <small>{skip_percent:.1f}%</small>
            </div>
        </div>

        <div class="progress-bar-container">
            <div class="progress-bar progress-pass" style="width: {pass_percent:.1f}%;">{passed if passed > 0 else ''}</div>
            <div class="progress-bar progress-fail" style="width: {fail_percent:.1f}%;">{failed if failed > 0 else ''}</div>
            <div class="progress-bar progress-skip" style="width: {skip_percent:.1f}%;">{skipped if skipped > 0 else ''}</div>
        </div>

        <h2>Package-wise Results</h2>
        <div class="table-wrapper">
            <table>
                <thead>
                    <tr>
                        <th>Package</th>
                        <th>Passed</th>
                        <th>Failed</th>
                        <th>Skipped</th>
                        <th>Total</th>
                        <th>Pass Rate</th>
                    </tr>
                </thead>
                <tbody>
                    {package_rows if package_rows else '<tr><td colspan="6" style="text-align: center; color: #999;">No test packages found</td></tr>'}
                </tbody>
            </table>
        </div>

        <h2>Historical Trend (Last 7 Days) - {current_env}</h2>
        <div class="table-wrapper">
            <table>
                <thead>
                    <tr>
                        <th>Date</th>
                        <th>Passed</th>
                        <th>Failed</th>
                        <th>Skipped</th>
                        <th>Total</th>
                        <th>Pass Rate</th>
                    </tr>
                </thead>
                <tbody>
                    {history_rows if history_rows else '<tr><td colspan="6" style="text-align: center; color: #999;">No historical data available</td></tr>'}
                </tbody>
            </table>
        </div>

        <div class="footer">
            <p>Report generated on {datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")}</p>
            <p>This is an automated test report. For more details, please contact your QA team.</p>
        </div>
    </div>
</body>
</html>
    """

    with open(HTML_REPORT_FILE, 'w', encoding='utf-8') as f:
        f.write(html_content)

    print(f"✓ HTML report generated: {HTML_REPORT_FILE}")


# --- Email Functionality ---

def send_email_report(report_path: str, recipients: str, current_run: Dict[str, Any]):
    """Sends the HTML report as an attachment via email."""

    if not recipients:
        print("No email recipients specified. Skipping email.")
        return

    # --- IMPORTANT: Configure your SMTP settings here ---
    SMTP_SERVER = "smtp.example.com"
    SMTP_PORT = 587
    SMTP_USERNAME = "your_email@example.com"
    SMTP_PASSWORD = "your_email_password"
    SENDER_EMAIL = "your_email@example.com"

    if SMTP_SERVER == "smtp.example.com":
        print(
            "⚠ WARNING: SMTP configuration is using placeholder values. Please update report_utils.py with your actual SMTP details to enable email functionality.")
        return

    try:
        msg = MIMEMultipart('alternative')
        msg['From'] = SENDER_EMAIL
        msg['To'] = recipients
        msg['Subject'] = f"🧪 Pytest Report - {current_run.get('date', 'N/A')} - {current_run.get('timestamp', 'N/A')}"

        # Create a text version for email clients that don't support HTML
        text_body = f"""
Pytest Automation Report
========================

Execution Date: {current_run.get('date', 'N/A')}
Execution Time: {current_run.get('timestamp', 'N/A')}

SUMMARY:
--------
Total Tests: {current_run.get('total', 0)}
Passed: {current_run.get('passed', 0)}
Failed: {current_run.get('failed', 0)}
Skipped: {current_run.get('skipped', 0)}

Pass Rate: {(current_run.get('passed', 0) / current_run.get('total', 1) * 100):.1f}%

Please see the attached HTML report for detailed information.
        """

        msg.attach(MIMEText(text_body, 'plain'))

        # Attach the HTML report file
        with open(report_path, "rb") as f:
            html_part = MIMEText(f.read(), 'html')
            msg.attach(html_part)

        # Connect to the SMTP server
        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
            server.starttls()
            server.login(SMTP_USERNAME, SMTP_PASSWORD)
            server.sendmail(SENDER_EMAIL, recipients.split(','), msg.as_string())

        print(f"✓ Successfully sent report to {recipients}")

    except Exception as e:
        print(f"✗ ERROR: Failed to send email report. Check SMTP configuration and credentials. Error: {e}")