import os
import json
import urllib.request
import urllib.error
from datetime import datetime, timedelta, timezone
import random

def fetch_hn_headlines():
    print("Fetching top stories from Hacker News...")
    top_stories_url = "https://hacker-news.firebaseio.com/v0/topstories.json"
    req = urllib.request.Request(top_stories_url, headers={"User-Agent": "Mozilla/5.0"})
    
    try:
        with urllib.request.urlopen(req, timeout=10) as response:
            story_ids = json.loads(response.read().decode())[:5]
    except Exception as e:
        print(f"Error fetching top stories list: {e}")
        return []

    stories = []
    for sid in story_ids:
        detail_url = f"https://hacker-news.firebaseio.com/v0/item/{sid}.json"
        d_req = urllib.request.Request(detail_url, headers={"User-Agent": "Mozilla/5.0"})
        try:
            with urllib.request.urlopen(d_req, timeout=5) as d_resp:
                item = json.loads(d_resp.read().decode())
                if item:
                    stories.append({
                        "title": item.get("title", "No Title"),
                        "url": item.get("url", f"https://news.ycombinator.com/item?id={sid}"),
                        "score": item.get("score", 0),
                        "by": item.get("by", "anonymous")
                    })
        except Exception as e:
            print(f"Error fetching item {sid}: {e}")
            continue
            
    return stories

def generate_svg(output_path):
    print("Generating custom Scraper Activity SVG...")
    
    # Generate mock page-crawl counts for the last 7 days to simulate a scraper monitor
    today = datetime.now()
    labels = []
    values = []
    
    # Deterministic values based on day of month + random seed for nice visualization
    random.seed(today.day)
    for i in range(6, -1, -1):
        day = today - timedelta(days=i)
        labels.append(day.strftime("%a"))
        values.append(random.randint(250, 680))
        
    max_val = max(values)
    
    # SVG Dimensions
    width = 480
    height = 200
    
    # Render SVG string with gradient and glassmorphism styling
    svg_content = f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width} {height}" width="100%" height="100%">
  <defs>
    <linearGradient id="barGrad" x1="0%" y1="100%" x2="0%" y2="0%">
      <stop offset="0%" stop-color="#8a2be2" stop-opacity="0.8"/>
      <stop offset="100%" stop-color="#00f2fe" stop-opacity="0.9"/>
    </linearGradient>
    <linearGradient id="bgGrad" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" stop-color="#0d1117"/>
      <stop offset="100%" stop-color="#161b22"/>
    </linearGradient>
    <filter id="shadow" x="-5%" y="-5%" width="110%" height="110%">
      <feDropShadow dx="0" dy="4" stdDeviation="4" flood-color="#00f2fe" flood-opacity="0.3"/>
    </filter>
  </defs>

  <!-- Background -->
  <rect width="{width}" height="{height}" rx="12" fill="url(#bgGrad)" stroke="#30363d" stroke-width="1.5"/>

  <!-- Header -->
  <text x="24" y="32" font-family="-apple-system, BlinkMacSystemFont, 'Segoe UI', Helvetica, Arial, sans-serif" font-size="14" font-weight="bold" fill="#f0f6fc" letter-spacing="1">SCRAPER ACTIVITY MONITOR</text>
  <text x="24" y="48" font-family="-apple-system, BlinkMacSystemFont, 'Segoe UI', Helvetica, Arial, sans-serif" font-size="10" fill="#8b949e">Asynchronous Crawler Load (Pages Scraped / Day)</text>
  <circle cx="430" cy="28" r="4" fill="#39d353" filter="url(#shadow)"/>
  <text x="440" y="31" font-family="-apple-system, BlinkMacSystemFont, 'Segoe UI', Helvetica, Arial, sans-serif" font-size="9" fill="#39d353" font-weight="bold">ONLINE</text>

  <!-- Grid Lines -->
  <line x1="50" y1="70" x2="440" y2="70" stroke="#21262d" stroke-dasharray="2 2"/>
  <line x1="50" y1="115" x2="440" y2="115" stroke="#21262d" stroke-dasharray="2 2"/>
  <line x1="50" y1="160" x2="440" y2="160" stroke="#30363d"/>

  <!-- Graph Plotting -->
  """
    
    # Draw Bars
    bar_width = 30
    gap = 22
    start_x = 75
    chart_bottom = 160
    chart_top = 70
    max_height = chart_bottom - chart_top
    
    for idx, (label, val) in enumerate(zip(labels, values)):
        x = start_x + idx * (bar_width + gap)
        bar_h = int((val / max_val) * max_height)
        y = chart_bottom - bar_h
        
        # Add bar, value text and label
        svg_content += f"""
  <!-- Bar {idx} -->
  <rect x="{x}" y="{y}" width="{bar_width}" height="{bar_h}" rx="4" fill="url(#barGrad)"/>
  <text x="{x + bar_width//2}" y="{y - 6}" font-family="monospace" font-size="8" fill="#58a6ff" text-anchor="middle" font-weight="bold">{val}</text>
  <text x="{x + bar_width//2}" y="{chart_bottom + 16}" font-family="-apple-system, BlinkMacSystemFont, sans-serif" font-size="10" fill="#8b949e" text-anchor="middle">{label}</text>
  """
        
    svg_content += "\n</svg>"
    
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(svg_content)
    print(f"Saved SVG to {output_path}")

def update_readme(readme_path, stories):
    print("Updating README.md with fresh scraped data...")
    if not os.path.exists(readme_path):
        print(f"Error: README.md not found at {readme_path}")
        return False
        
    with open(readme_path, "r", encoding="utf-8") as f:
        content = f.read()
        
    start_marker = "<!-- DASHBOARD_START -->"
    end_marker = "<!-- DASHBOARD_END -->"
    
    if start_marker not in content or end_marker not in content:
        print("Error: Dashboard markers not found in README.md.")
        return False
        
    # Generate the Markdown text to insert
    now_str = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
    
    dashboard_md = f"""
### 📊 Live Scraper Dashboard (Auto-updates every 12h)
This section is automatically updated by a **GitHub Actions runner** that executes a custom Python scraper to pull trending articles from public endpoints.

#### 📰 Trending Tech Headlines (Scraped from Hacker News)
| Headline | Score | Scraped By |
| :--- | :---: | :---: |
"""
    for s in stories:
        # Escape markdown symbols in titles
        safe_title = s['title'].replace('|', '\\|')
        dashboard_md += f"| [{safe_title}]({s['url']}) | `{s['score']} pts` | `@{s['by']}` |\n"
        
    dashboard_md += f"\n<p align=\"center\">\n  <img src=\"scraped_activity.svg\" alt=\"Scraper Activity Monitor\" width=\"480\"/>\n</p>\n\n*Last automated pipeline execution: `{now_str}`*"
    
    # Replace content between markers
    pattern = f"{start_marker}.*?{end_marker}"
    import re
    # Using flags=re.DOTALL to match newlines between markers
    replacement = f"{start_marker}\n{dashboard_md}\n{end_marker}"
    new_content = re.sub(pattern, replacement, content, flags=re.DOTALL)
    
    with open(readme_path, "w", encoding="utf-8") as f:
        f.write(new_content)
    print("README.md updated successfully.")
    return True

def log_activity(log_path, status, count):
    print("Logging script execution status...")
    now_str = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
    
    if not os.path.exists(log_path):
        # Create log header if it doesn't exist
        with open(log_path, "w", encoding="utf-8") as f:
            f.write("# Scraper Pipeline Activity Log\n\n| Timestamp | Pipeline Source | Status | Results |\n| :--- | :--- | :---: | :--- |\n")
            
    log_line = f"| {now_str} | Hacker News API | **{status}** | Scraped {count} top stories successfully |\n"
    with open(log_path, "a", encoding="utf-8") as f:
        f.write(log_line)
    print("Activity log appended.")

def main():
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    readme_path = os.path.join(base_dir, "README.md")
    svg_path = os.path.join(base_dir, "scraped_activity.svg")
    log_path = os.path.join(base_dir, "activity_log.md")
    
    stories = fetch_hn_headlines()
    if stories:
        generate_svg(svg_path)
        updated = update_readme(readme_path, stories)
        if updated:
            log_activity(log_path, "SUCCESS", len(stories))
        else:
            log_activity(log_path, "FAILED", 0)
    else:
        log_activity(log_path, "DEGRADED (No headlines fetched)", 0)

if __name__ == "__main__":
    main()
