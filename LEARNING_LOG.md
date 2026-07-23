# 📝 Developer Learning & Automation Log

This log tracks my daily engineering sessions, concepts learned, systems built, and technical interview questions solved.

---

## 📅 2026-07-23 — Portfolio Automation, Sanitization, and Pathing

### 🛠️ What Was Built Today
*   **Developer Portfolio Deployment:** Structured, sanitized, and deployed 14 separate repositories to my GitHub profile, including web crawlers, AI tools, and predictive models.
*   **Self-Updating Profile Dashboard:** Developed a Python scraper running on a GitHub Actions cron schedule that queries the Hacker News REST API, updates my profile README, renders a custom neon SVG graph, and appends logs to `activity_log.md`.
*   **Anti-Conflict Push Flow:** Fixed remote push conflicts in the automated workflow by implementing a safe rebase loop (`git pull --rebase origin main`) before pushing.
*   **RAG Chatbot Restoration & CI Fix:** Overwrote chatbot placeholders with authentic FastAPI/Streamlit source files. Converted `requirements.txt` from UTF-16 to UTF-8 to fix pip installation, and moved optional `PineconeVectorStore` imports inside function bodies so that the FAISS-based CI test suite executes successfully.

### 🧠 Concepts Learned
1.  **Python 3.12+ Timezones:** Transitioned from the deprecated `datetime.utcnow()` to timezone-aware UTC representations using `datetime.now(timezone.utc)`.
2.  **GitHub Actions Permissions:** Learned that modifying GitHub Actions workflow files (`.github/workflows/`) via Personal Access Tokens requires checking the **`workflow`** scope permission.
3.  **CI Pathing with PYTHONPATH:** Configured `PYTHONPATH: .` in GitHub Action runners so that pytest can resolve root-level Python modules (like `api.py` and `core/`) during remote test runs.

### ❓ Interview-Style Technical Question
**Question:** *Explain how Python's import system resolves modules from the filesystem, and why `ModuleNotFoundError` can occur in CI runners even when the code runs fine locally.*

**Answer:** 
When Python executes an import statement (e.g., `import api`), it searches through the list of directories stored in `sys.path`. 
1.  **Local Execution:** When you run python locally (e.g., `python tests/test_api.py`), Python automatically appends the directory containing the script (`tests/`) to `sys.path`. If the user is running from the root with `python -m pytest`, the current directory is added.
2.  **CI Runners:** In headless CI environments (like Ubuntu runners in GitHub Actions), the current working directory is the repository root `/home/runner/work/...`. Pytest runs tests from `tests/` but does not automatically add the root folder to the import paths. This results in `ModuleNotFoundError` when the test scripts attempt to import modules in the root folder (like `api.py`).
3.  **Resolution:** Setting the `PYTHONPATH` environment variable to `.` (the root directory) explicitly instructs the Python interpreter to search the repository root for modules, allowing imports like `from api import app` to resolve correctly.
