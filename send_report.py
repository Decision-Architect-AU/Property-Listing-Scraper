#!/usr/bin/env python3
"""
send_report.py — Email the scored listings as an HTML report via Gmail SMTP.

Usage:
    python send_report.py                        # send full report
    python send_report.py --suburb "Bendigo"     # filter to one suburb

Config:
    Reads credentials from email_config.json in the same directory:
    {
      "gmail_address": "you@gmail.com",
      "gmail_app_password": "xxxx xxxx xxxx xxxx",
      "to": "you@gmail.com"
    }
"""

import argparse
import json
import smtplib
import sys
from datetime import date
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from pathlib import Path


# ── Config ────────────────────────────────────────────────────────────────────

PROJECT_DIR = Path(__file__).parent
DATA_DIR    = Path(r"C:\DomainListingData")
SCORED_JSON = DATA_DIR / "scored_listings.json"
CONFIG_FILE = PROJECT_DIR / "email_config.json"


def load_config() -> dict:
    if not CONFIG_FILE.exists():
        print(f"ERROR: {CONFIG_FILE} not found. Create it with your Gmail credentials.", file=sys.stderr)
        sys.exit(1)
    return json.loads(CONFIG_FILE.read_text(encoding="utf-8"))


# ── Score helpers ─────────────────────────────────────────────────────────────

def combined_score(lst: dict) -> int:
    return (lst.get("growth_score") or 0) + (lst.get("deals_score") or 0) + (lst.get("cashflow_score") or 0)


# ── Colour helpers ────────────────────────────────────────────────────────────

def score_colour(val: int, thresholds=(5, 3)) -> str:
    """Return a hex colour for a score value."""
    hi, lo = thresholds
    if val >= hi:   return "#1B7A34"   # dark green
    if val >= lo:   return "#E85D04"   # amber
    return "#888888"                   # grey


def yield_colour(yld: float) -> str:
    if yld >= 9.0: return "#1B7A34"
    if yld >= 7.0: return "#40916C"
    if yld >= 5.0: return "#E8A000"
    return "#888888"


# ── HTML builder ──────────────────────────────────────────────────────────────

def build_html(listings: list[dict], suburb_filter: str | None, today: str) -> str:
    if suburb_filter:
        listings = [l for l in listings if l.get("suburb", "").lower() == suburb_filter.lower()]

    # Sort by combined score desc, then cashflow desc
    listings = sorted(listings, key=lambda l: (combined_score(l), l.get("cashflow_score") or 0), reverse=True)

    total      = len(listings)
    avg_yield  = round(sum(l.get("gross_yield_pct") or 0 for l in listings) / max(total, 1), 1)
    top_growth = max((l.get("growth_score") or 0 for l in listings), default=0)
    top_deals  = max((l.get("deals_score") or 0 for l in listings), default=0)
    top_cash   = max((l.get("cashflow_score") or 0 for l in listings), default=0)

    suburb_label = suburb_filter or "All Suburbs"

    # ── Summary cards ────────────────────────────────────────────────────────
    cards_html = f"""
    <div style="display:flex;gap:16px;margin-bottom:24px;flex-wrap:wrap;">
      <div style="background:#16213E;color:#fff;padding:16px 24px;border-radius:8px;min-width:120px;text-align:center;">
        <div style="font-size:28px;font-weight:700;">{total}</div>
        <div style="font-size:12px;opacity:.7;">Listings</div>
      </div>
      <div style="background:#1B4332;color:#D8F3DC;padding:16px 24px;border-radius:8px;min-width:120px;text-align:center;">
        <div style="font-size:28px;font-weight:700;">{top_growth}</div>
        <div style="font-size:12px;opacity:.8;">Top Growth</div>
      </div>
      <div style="background:#7B2D00;color:#FFF3E0;padding:16px 24px;border-radius:8px;min-width:120px;text-align:center;">
        <div style="font-size:28px;font-weight:700;">{top_deals}</div>
        <div style="font-size:12px;opacity:.8;">Top Deals</div>
      </div>
      <div style="background:#0D3B66;color:#E3F2FD;padding:16px 24px;border-radius:8px;min-width:120px;text-align:center;">
        <div style="font-size:28px;font-weight:700;">{top_cash}</div>
        <div style="font-size:12px;opacity:.8;">Top Cashflow</div>
      </div>
      <div style="background:#2D2D2D;color:#fff;padding:16px 24px;border-radius:8px;min-width:120px;text-align:center;">
        <div style="font-size:28px;font-weight:700;">{avg_yield}%</div>
        <div style="font-size:12px;opacity:.7;">Avg Yield</div>
      </div>
    </div>
    """

    # ── Table rows ───────────────────────────────────────────────────────────
    rows_html = ""
    for i, lst in enumerate(listings):
        bg       = "#F8F9FA" if i % 2 == 0 else "#FFFFFF"
        g        = lst.get("growth_score") or 0
        d        = lst.get("deals_score") or 0
        c        = lst.get("cashflow_score") or 0
        total_sc = g + d + c
        yld      = lst.get("gross_yield_pct") or 0
        url      = lst.get("url", "")
        address  = lst.get("address") or lst.get("suburb", "")
        price    = lst.get("price", "—")
        beds     = lst.get("beds", "")
        baths    = lst.get("baths", "")
        land     = lst.get("land", "")
        rent_ass = lst.get("rent_assumptions", "")
        g_sig    = lst.get("growth_signals", "—")
        d_sig    = lst.get("deals_signals", "—")
        c_sig    = lst.get("cashflow_signals", "—")
        dom      = lst.get("days_on_market", "")
        delinq   = lst.get("delinquent", False)

        delinq_bg = "background:#FFE5E5;" if delinq else ""
        addr_cell = (f'<a href="{url}" style="color:#0D3B66;font-weight:600;">{address}</a>'
                     if url else f'<strong>{address}</strong>')

        beds_baths = " / ".join(filter(None, [f"{beds}bd" if beds else "", f"{baths}ba" if baths else "", land]))

        rows_html += f"""
        <tr style="background:{bg};{delinq_bg}">
          <td style="padding:8px 6px;text-align:center;color:#888;font-size:12px;">{i+1}</td>
          <td style="padding:8px 10px;">{addr_cell}<br>
              <span style="font-size:11px;color:#666;">{beds_baths}</span></td>
          <td style="padding:8px 10px;font-weight:600;">{price}</td>
          <td style="padding:8px 6px;text-align:center;font-weight:700;color:{score_colour(g, (5,2))};">{g}</td>
          <td style="padding:8px 6px;text-align:center;font-weight:700;color:{score_colour(d, (3,1))};">{d}</td>
          <td style="padding:8px 6px;text-align:center;font-weight:700;color:{score_colour(c, (5,3))};">{c}</td>
          <td style="padding:8px 6px;text-align:center;font-weight:700;font-size:14px;">{total_sc}</td>
          <td style="padding:8px 6px;text-align:center;font-weight:700;color:{yield_colour(yld)};">
              {f"{yld:.1f}%" if yld else "—"}</td>
          <td style="padding:8px 10px;font-size:11px;color:#555;max-width:280px;">
              <span style="color:#1B4332;">&#127807; {g_sig}</span><br>
              <span style="color:#7B2D00;">&#128176; {d_sig}</span><br>
              <span style="color:#0D3B66;">&#128181; {c_sig}</span>
              {f"<br><span style='font-size:10px;color:#888;'>{rent_ass}</span>" if rent_ass else ""}
              {f"<br><span style='color:#CC0000;font-size:10px;'>DOM: {dom}d</span>" if dom else ""}
          </td>
        </tr>
        """

    html = f"""<!DOCTYPE html>
<html>
<head><meta charset="UTF-8"></head>
<body style="font-family:Calibri,Arial,sans-serif;margin:0;padding:24px;background:#F0F2F5;color:#1A1A2E;">

  <div style="max-width:1100px;margin:0 auto;background:#fff;border-radius:12px;overflow:hidden;box-shadow:0 2px 12px rgba(0,0,0,.08);">

    <!-- Header -->
    <div style="background:#1A1A2E;padding:24px 32px;">
      <h1 style="margin:0;color:#E8C547;font-size:22px;letter-spacing:.5px;">
        Property Listings Report
      </h1>
      <p style="margin:6px 0 0;color:#aaa;font-size:13px;">
        {suburb_label} &nbsp;|&nbsp; {today} &nbsp;|&nbsp; Sorted by combined score
      </p>
    </div>

    <div style="padding:24px 32px;">

      {cards_html}

      <!-- Table -->
      <table style="width:100%;border-collapse:collapse;font-size:13px;">
        <thead>
          <tr style="background:#16213E;color:#fff;">
            <th style="padding:10px 6px;text-align:center;width:32px;">#</th>
            <th style="padding:10px 10px;text-align:left;">Address</th>
            <th style="padding:10px 10px;text-align:left;">Price</th>
            <th style="padding:10px 6px;text-align:center;">&#127807;<br>Growth</th>
            <th style="padding:10px 6px;text-align:center;">&#128176;<br>Deals</th>
            <th style="padding:10px 6px;text-align:center;">&#128181;<br>Cash</th>
            <th style="padding:10px 6px;text-align:center;background:#2D3A5A;">Total</th>
            <th style="padding:10px 6px;text-align:center;">Yield</th>
            <th style="padding:10px 10px;text-align:left;">Signals</th>
          </tr>
        </thead>
        <tbody>
          {rows_html}
        </tbody>
      </table>

      <p style="margin-top:20px;font-size:11px;color:#aaa;text-align:center;">
        Generated by Property Listing Scraper &nbsp;|&nbsp; {today}
      </p>
    </div>
  </div>
</body>
</html>"""

    return html


# ── Sender ────────────────────────────────────────────────────────────────────

def send_report(suburb_filter: str | None = None) -> dict:
    """
    Load scored listings, build HTML report, and send via Gmail SMTP.
    Returns {"success": bool, "message": str}.
    """
    if not SCORED_JSON.exists():
        return {"success": False, "message": f"{SCORED_JSON} not found — run the pipeline first."}

    cfg = load_config()
    gmail_addr    = cfg.get("gmail_address", "")
    app_password  = cfg.get("gmail_app_password", "")
    to_addr       = cfg.get("to", gmail_addr)

    if not gmail_addr or not app_password:
        return {"success": False, "message": "email_config.json is missing gmail_address or gmail_app_password."}

    listings = json.loads(SCORED_JSON.read_text(encoding="utf-8"))
    today    = str(date.today())

    suburb_label = suburb_filter or "All Suburbs"
    subject = f"Property Report — {suburb_label} — {today}"

    html_body = build_html(listings, suburb_filter, today)

    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"]    = gmail_addr
    msg["To"]      = to_addr
    msg.attach(MIMEText(html_body, "html", "utf-8"))

    try:
        with smtplib.SMTP("smtp.gmail.com", 587) as smtp:
            smtp.ehlo()
            smtp.starttls()
            smtp.login(gmail_addr, app_password)
            smtp.sendmail(gmail_addr, to_addr, msg.as_string())
        return {"success": True, "message": f"Report sent to {to_addr}"}
    except smtplib.SMTPAuthenticationError:
        return {"success": False,
                "message": "Gmail authentication failed. Check your App Password in email_config.json."}
    except Exception as e:
        return {"success": False, "message": f"SMTP error: {e}"}


# ── CLI ───────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--suburb", help="Filter report to a single suburb", default=None)
    args = parser.parse_args()

    result = send_report(suburb_filter=args.suburb)
    print(result["message"])
    if not result["success"]:
        sys.exit(1)
