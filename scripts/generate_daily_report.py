import os
import json
import urllib.request
from datetime import datetime, timedelta, timezone
import re

TOKEN = os.getenv("GITHUB_TOKEN")

def check_recent_activity():
    print("Checking recent user activity on GitHub...")
    url = "https://api.github.com/users/vivekrana-031122/events?per_page=15"
    headers = {"User-Agent": "Python"}
    if TOKEN:
        headers["Authorization"] = f"token {TOKEN}"
    req = urllib.request.Request(url, headers=headers)
    
    try:
        with urllib.request.urlopen(req, timeout=10) as r:
            events = json.loads(r.read().decode())
            
        now = datetime.now(timezone.utc)
        one_day_ago = now - timedelta(days=1)
        
        activity_count = 0
        for event in events:
            created_at_str = event.get("created_at")
            if not created_at_str:
                continue
            # Parse created_at e.g. "2026-07-23T17:09:20Z"
            created_at = datetime.strptime(created_at_str, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc)
            
            if created_at > one_day_ago:
                if event.get("type") in ["PushEvent", "CreateEvent", "WorkflowRunEvent"]:
                    activity_count += 1
                    
        print(f"Found {activity_count} pushing/workflow events in the last 24 hours.")
        return activity_count > 0
    except Exception as e:
        print(f"Error checking user activity: {e}")
        # Default to True on network error to make sure we don't silence warnings
        return True

def get_latest_workflow_status(repo):
    url = f"https://api.github.com/repos/vivekrana-031122/{repo}/actions/runs?per_page=3"
    headers = {"User-Agent": "Python"}
    if TOKEN:
        headers["Authorization"] = f"token {TOKEN}"
    req = urllib.request.Request(url, headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=10) as r:
            data = json.loads(r.read().decode())
            runs = data.get("workflow_runs", [])
            for run in runs:
                # Skip CodeQL if we want, or just return the primary CI run
                if "CI" in run["name"] or "Live Profile" in run["name"]:
                    name = run["name"].encode("ascii", "ignore").decode("ascii")
                    return {
                        "name": name,
                        "status": run["status"],
                        "conclusion": run["conclusion"],
                        "html_url": run["html_url"]
                    }
    except Exception as e:
        print(f"Error getting workflow status for {repo}: {e}")
    return None

def extract_today_learning_log(log_path):
    print("Checking LEARNING_LOG.md for today's entry...")
    if not os.path.exists(log_path):
        print("Learning log file not found.")
        return None
        
    with open(log_path, "r", encoding="utf-8") as f:
        content = f.read()
        
    # Get today's date format: YYYY-MM-DD
    # We will search for today's or yesterday's entry to ensure we pick it up correctly
    today_str = datetime.now().strftime("%Y-%m-%d")
    yesterday_str = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")
    
    # We search for ## 📅 YYYY-MM-DD
    pattern = r"## 📅 ({today}|{yesterday})(.*?)(?=## 📅 |\Z)"
    match = re.search(pattern.format(today=today_str, yesterday=yesterday_str), content, re.DOTALL)
    
    if not match:
        print(f"No learning log entry found for {today_str} or {yesterday_str}.")
        return None
        
    log_content = match.group(0).strip()
    return log_content

def convert_md_to_html(md_text):
    if not md_text:
        return ""
    html = md_text
    # Convert headers (using multiline and anchoring to start of line)
    html = re.sub(r"^### (.*?)$", r"<h3 style='color:#f0f6fc; font-size:14px; margin-top:12px; margin-bottom:6px;'>\1</h3>", html, flags=re.MULTILINE)
    html = re.sub(r"^## (.*?)$", r"<h2 style='color:#58a6ff; font-size:18px; border-bottom:1px solid #30363d; padding-bottom:6px; margin-top:18px;'>\1</h2>", html, flags=re.MULTILINE)
    
    # Convert bold
    html = re.sub(r"\*\*(.*?)\*\*", r"<strong>\1</strong>", html)
    
    # Convert lists (must handle multiline list items cleanly)
    html = re.sub(r"^[*-] (.*?)$", r"<li style='margin-bottom:6px; font-size:13px; color:#c9d1d9;'>\1</li>", html, flags=re.MULTILINE)
    
    # Convert remaining newlines to br
    html = html.replace("\n", "<br/>")
    return f"<div style='background-color:#161b22; border:1px solid #30363d; border-radius:6px; padding:16px; font-family:-apple-system,BlinkMacSystemFont,sans-serif;'>{html}</div>"

def build_email_body(has_activity, chatbot_status, dashboard_status, learning_html):
    date_str = datetime.now().strftime("%Y-%m-%d")
    
    if not has_activity and not learning_html:
        # Short 'no activity today' email
        subject = f"📊 Daily GitHub Report — {date_str} [No Activity]"
        body = f"""
        <html>
        <body style="background-color:#0d1117; color:#c9d1d9; font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Helvetica,Arial,sans-serif; padding:20px;">
          <div style="max-width:600px; margin:0 auto; background-color:#161b22; border:1px solid #30363d; border-radius:8px; padding:20px; text-align:center;">
            <h2 style="color:#8b949e; margin-bottom:10px;">📊 Daily GitHub Report</h2>
            <p style="font-size:14px; color:#8b949e;">Date: {date_str}</p>
            <hr style="border:0; border-top:1px solid #30363d; margin:20px 0;"/>
            <p style="font-size:15px; color:#f0f6fc; font-weight:bold;">No developer activity or learning sessions logged today.</p>
            <p style="font-size:13px; color:#8b949e; margin-top:20px;">Keep coding! See you tomorrow.</p>
          </div>
        </body>
        </html>
        """
        return subject, body
        
    subject = f"📊 Daily GitHub Report — {date_str}"
    
    # Format operations status
    ops_html = ""
    for repo, status in [("RAG-PDF-CHATBOT", chatbot_status), ("vivekrana-031122", dashboard_status)]:
        if status:
            color = "#39d353" if status["conclusion"] == "success" else "#f85149"
            conclusion = status["conclusion"].upper() if status["conclusion"] else "RUNNING"
            ops_html += f"""
            <div style="margin-bottom:12px; padding:10px; background-color:#0d1117; border-left:4px solid {color}; border-radius:0 4px 4px 0;">
              <span style="font-weight:bold; color:#f0f6fc;">{repo}</span> — 
              <span style="color:{color}; font-weight:bold;">{conclusion}</span>
              <br/>
              <span style="font-size:11px; color:#8b949e;">Workflow: {status["name"]}</span> | 
              <a href="{status["html_url"]}" style="font-size:12px; color:#58a6ff; text-decoration:none;">View Logs</a>
            </div>
            """
        else:
            ops_html += f"""
            <div style="margin-bottom:12px; padding:10px; background-color:#0d1117; border-left:4px solid #8b949e; border-radius:0 4px 4px 0; color:#8b949e;">
              <span style="font-weight:bold; color:#f0f6fc;">{repo}</span> — No recent runs recorded.
            </div>
            """
            
    learning_log_section = ""
    if learning_html:
        learning_log_section = f"""
        <h3 style="color:#f0f6fc; border-bottom:1px solid #30363d; padding-bottom:6px; margin-top:24px;">📝 Learning Log Entry</h3>
        {learning_html}
        """
    else:
        learning_log_section = """
        <h3 style="color:#f0f6fc; border-bottom:1px solid #30363d; padding-bottom:6px; margin-top:24px;">📝 Learning Log Entry</h3>
        <p style="font-size:13px; color:#8b949e; font-style:italic;">No session logged in LEARNING_LOG.md today.</p>
        """

    body = f"""
    <html>
    <body style="background-color:#0d1117; color:#c9d1d9; font-family:-apple-system,BlinkMacSystemFont,sans-serif; padding:16px;">
      <div style="max-width:600px; margin:0 auto; background-color:#161b22; border:1px solid #30363d; border-radius:8px; padding:20px;">
        <!-- Header -->
        <div style="text-align:center; padding-bottom:15px; border-bottom:1px solid #30363d; margin-bottom:20px;">
          <h2 style="color:#f0f6fc; margin:0; font-size:20px;">📊 Daily GitHub Report</h2>
          <span style="font-size:12px; color:#8b949e;">{date_str} | Automated Delivery</span>
        </div>
        
        <!-- Operations Summary -->
        <h3 style="color:#f0f6fc; border-bottom:1px solid #30363d; padding-bottom:6px; margin-top:0;">🛠️ Operations Summary</h3>
        {ops_html}
        
        <!-- Learning Log -->
        {learning_log_section}
        
        <!-- Dashboard Link -->
        <h3 style="color:#f0f6fc; border-bottom:1px solid #30363d; padding-bottom:6px; margin-top:24px;">🔗 Profile Dashboard</h3>
        <p style="font-size:13px; color:#c9d1d9; margin-bottom:16px;">
          Your live profile dashboard is fully up-to-date and rendering fresh data.
        </p>
        <div style="text-align:center; margin-top:20px;">
          <a href="https://github.com/vivekrana-031122" style="background-color:#238636; color:#ffffff; padding:10px 20px; border-radius:6px; font-weight:bold; text-decoration:none; font-size:14px; display:inline-block;">View Live Profile</a>
        </div>
      </div>
    </body>
    </html>
    """
    return subject, body

def main():
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    log_path = os.path.join(base_dir, "LEARNING_LOG.md")
    
    # 1. Check if activity occurred
    has_activity = check_recent_activity()
    
    # 2. Extract learning log
    learning_md = extract_today_learning_log(log_path)
    learning_html = convert_md_to_html(learning_md)
    
    # 3. Fetch workflow statuses
    chatbot_status = get_latest_workflow_status("RAG-PDF-CHATBOT")
    dashboard_status = get_latest_workflow_status("vivekrana-031122")
    
    # 4. Generate subject and body
    subject, body = build_email_body(has_activity, chatbot_status, dashboard_status, learning_html)
    
    # 5. Output values for the workflow steps to read
    # We write subject and body to files so GitHub Actions can easily read them!
    with open("email_subject.txt", "w", encoding="utf-8") as f:
        f.write(subject)
    with open("email_body.html", "w", encoding="utf-8") as f:
        f.write(body)
        
    print(f"Report files generated successfully. Subject: {subject.encode('ascii', 'ignore').decode('ascii')}")

if __name__ == "__main__":
    main()
