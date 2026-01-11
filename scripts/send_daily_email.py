import csv
import os
import smtplib
import sys
from datetime import datetime
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText


def build_daily_email(today: str, predictions: list[dict]) -> str:
    html = f"""
    <html>
      <body style="font-family: Arial, sans-serif; background-color: #f5f5f5; padding: 20px;">
        <div style="max-width: 800px; margin: 0 auto; background-color: white; padding: 20px; border-radius: 8px;">
          <h2 style="color: #333; border-bottom: 3px solid #007bff; padding-bottom: 10px;">
            📊 LineLogic Daily Predictions - {today}
          </h2>
          <p style="color: #666; font-size: 14px;">
            Generated at {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')}
          </p>
          <table style="width: 100%; border-collapse: collapse; margin-top: 20px;">
            <thead>
              <tr style="background-color: #007bff; color: white;">
                <th style="padding: 12px; text-align: left;">Home</th>
                <th style="padding: 12px; text-align: left;">Away</th>
                <th style="padding: 12px; text-align: center;">Pred %</th>
                <th style="padding: 12px; text-align: center;">Rest</th>
                <th style="padding: 12px; text-align: left;">Tier</th>
                <th style="padding: 12px; text-align: left;">Recommendation</th>
              </tr>
            </thead>
            <tbody>
    """

    if predictions:
        tier_colors = {"1": "#28a745", "2": "#ffc107", "3": "#fd7e14", "4": "#dc3545"}
        for pred in predictions:
            prob = float(pred["pred_home_win_prob"]) * 100
            tier = pred["confidence_tier"].replace("TIER ", "").split()[0]
            tier_color = tier_colors.get(tier, "#6c757d")
            html += f"""
              <tr style=\"border-bottom: 1px solid #eee;\">
                <td style=\"padding: 12px; font-weight: bold;\">{pred['home_team']}</td>
                <td style=\"padding: 12px;\">{pred['away_team']}</td>
                <td style=\"padding: 12px; text-align: center; font-weight: bold;\">{prob:.0f}%</td>
                <td style=\"padding: 12px; text-align: center;\">{pred.get('home_team_rest_days', '-')}d</td>
                <td style=\"padding: 12px; background-color: {tier_color}; color: white; border-radius: 4px; text-align: center;\">TIER {tier}</td>
                <td style=\"padding: 12px; font-size: 13px;\">{pred['recommendation']}</td>
              </tr>
            """
    else:
        html += '<tr><td colspan="6" style="padding: 20px; text-align: center; color: #999;">No games scheduled for today</td></tr>'

    html += """
            </tbody>
          </table>
          <div style="margin-top: 20px; padding: 15px; background-color: #f0f0f0; border-radius: 4px; font-size: 13px; color: #666;">
            <strong>📌 Decision Guide:</strong><br/>
            🟢 <strong>TIER 1:</strong> Use model predictions directly (≥70% expected accuracy)<br/>
            🟡 <strong>TIER 2:</strong> Use with external validation (68-70%)<br/>
            🔴 <strong>TIER 4:</strong> Cross-check externally - back-to-back weakness<br/>
          </div>
          <p style="margin-top: 20px; font-size: 12px; color: #999; text-align: center;">
            LineLogic POC | All predictions with confidence tiers
          </p>
        </div>
      </body>
    </html>
    """

    return html


def send_email(today: str) -> None:
    csv_path = f"predictions_{today}.csv"
    try:
        with open(csv_path, "r", encoding="utf-8") as f:
            predictions = list(csv.DictReader(f))
    except FileNotFoundError:
        predictions = []

    smtp_user = os.getenv("SMTP_USER")
    smtp_pass = os.getenv("SMTP_PASS")
    from_email = os.getenv("FROM_EMAIL", smtp_user)

    if not (smtp_user and smtp_pass):
        print("⚠️  SMTP credentials not set. Skipping email.")
        return

    html = build_daily_email(today, predictions)

    msg = MIMEMultipart("alternative")
    msg["Subject"] = f"LineLogic Daily Predictions - {today}"
    msg["From"] = from_email
    msg["To"] = "bbrennan83@gmail.com"
    msg.attach(MIMEText(html, "html"))

    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
        server.login(smtp_user, smtp_pass)
        server.send_message(msg)

    print("✅ Email sent successfully!")


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: send_daily_email.py <today>")
        sys.exit(1)
    send_email(sys.argv[1])
