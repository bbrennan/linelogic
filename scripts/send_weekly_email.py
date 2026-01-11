import json
import os
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import sys


def build_weekly_email(date_str: str, report: dict) -> str:
    metrics = report.get("overall_metrics", {})
    by_tier = report.get("by_tier", [])

    html_lines = [
        "<html>",
        '  <body style="font-family: Arial, sans-serif; background-color: #f5f5f5; padding: 20px;">',
        '    <div style="max-width: 900px; margin: 0 auto; background-color: white; padding: 20px; border-radius: 8px;">',
        '      <h2 style="color: #333; border-bottom: 3px solid #007bff; padding-bottom: 10px;">',
        f"        📊 LineLogic Weekly Validation Report - Week Ending {date_str}",
        "      </h2>",
        "      ",
        '      <h3 style="color: #007bff; margin-top: 20px;">Overall Metrics</h3>',
        '      <table style="width: 100%; border-collapse: collapse; background-color: #f9f9f9;">',
        '        <tr style="border-bottom: 1px solid #ddd;">',
        '          <td style="padding: 10px; font-weight: bold;">Total Predictions</td>',
        f"          <td style=\"padding: 10px;\">{metrics.get('total_predictions', 'N/A')}"
        + "</td>",
        "        </tr>",
        '        <tr style="border-bottom: 1px solid #ddd;">',
        '          <td style="padding: 10px; font-weight: bold;">Overall Accuracy</td>',
        f"          <td style=\"padding: 10px; font-weight: bold; color: #28a745;\">{metrics.get('accuracy', 0)*100:.1f}%</td>",
        "        </tr>",
        '        <tr style="border-bottom: 1px solid #ddd;">',
        '          <td style="padding: 10px; font-weight: bold;">Log Loss</td>',
        f"          <td style=\"padding: 10px;\">{metrics.get('log_loss', 0):.4f}</td>",
        "        </tr>",
        "        <tr>",
        '          <td style="padding: 10px; font-weight: bold;">Baseline Home Win Rate</td>',
        f"          <td style=\"padding: 10px;\">{metrics.get('baseline_home_win_rate', 0)*100:.1f}%</td>",
        "        </tr>",
        "      </table>",
        "      ",
        '      <h3 style="color: #007bff; margin-top: 20px;">Accuracy by Confidence Tier</h3>',
        '      <table style="width: 100%; border-collapse: collapse;">',
        "        <thead>",
        '          <tr style="background-color: #007bff; color: white;">',
        '            <th style="padding: 12px; text-align: left;">Tier</th>',
        '            <th style="padding: 12px; text-align: center;">Accuracy</th>',
        '            <th style="padding: 12px; text-align: center;">Games</th>',
        '            <th style="padding: 12px; text-align: center;">Status</th>',
        "          </tr>",
        "        </thead>",
        "        <tbody>",
    ]

    tier_targets = {"TIER 1": 0.70, "TIER 2": 0.68, "TIER 3": 0.65, "TIER 4": 0.50}
    for tier_info in by_tier:
        tier = tier_info.get("tier", "N/A")
        accuracy = tier_info.get("accuracy", 0)
        n_games = tier_info.get("n_games", 0)
        target = tier_targets.get(tier, 0.65)
        status = "✅ On Target" if accuracy >= target else "⚠️ Below Target"
        status_color = "#28a745" if accuracy >= target else "#dc3545"

        html_lines.extend(
            [
                '          <tr style="border-bottom: 1px solid #eee;">',
                f'            <td style="padding: 12px; font-weight: bold;">{tier}</td>',
                f'            <td style="padding: 12px; text-align: center; font-weight: bold;">{accuracy*100:.1f}%</td>',
                f'            <td style="padding: 12px; text-align: center;">{n_games}</td>',
                f'            <td style="padding: 12px; text-align: center; color: {status_color}; font-weight: bold;">{status}</td>',
                "          </tr>",
            ]
        )

    html_lines.extend(
        [
            "        </tbody>",
            "      </table>",
            "      ",
            '      <div style="margin-top: 20px; padding: 15px; background-color: #f0f0f0; border-radius: 4px; font-size: 13px;">',
            "        <strong>📌 Target Accuracy by Tier:</strong><br/>",
            "        🟢 TIER 1: ≥70% (HIGH CONFIDENCE)<br/>",
            "        🟡 TIER 2: 68-70% (MEDIUM-HIGH)<br/>",
            "        🟡 TIER 3: 65-68% (MEDIUM)<br/>",
            "        🔴 TIER 4: <50% (CAUTION - Back-to-back games)<br/>",
            "      </div>",
            "      ",
            '      <p style="margin-top: 20px; font-size: 12px; color: #999; text-align: center;">',
            f"        LineLogic POC Weekly Validation | Data current through {date_str}",
            "      </p>",
            "    </div>",
            "  </body>",
            "</html>",
        ]
    )

    return "\n".join(html_lines)


def send_email(date_str: str) -> None:
    report_path = f"validation_report_{date_str}.json"
    try:
        with open(report_path, "r", encoding="utf-8") as f:
            report = json.load(f)
    except FileNotFoundError:
        print("⚠️  Validation report not found. Skipping email.")
        return

    smtp_user = os.getenv("SMTP_USER")
    smtp_pass = os.getenv("SMTP_PASS")
    from_email = os.getenv("FROM_EMAIL", smtp_user)

    if not (smtp_user and smtp_pass):
        print("⚠️  SMTP credentials not set. Skipping email.")
        return

    html = build_weekly_email(date_str, report)

    msg = MIMEMultipart("alternative")
    msg["Subject"] = f"LineLogic Weekly Validation - Week Ending {date_str}"
    msg["From"] = from_email
    msg["To"] = "bbrennan83@gmail.com"
    msg.attach(MIMEText(html, "html"))

    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
        server.login(smtp_user, smtp_pass)
        server.send_message(msg)

    print("✅ Validation email sent successfully!")


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: send_weekly_email.py <end_date>")
        sys.exit(1)
    send_email(sys.argv[1])
