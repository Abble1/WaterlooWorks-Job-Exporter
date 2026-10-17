# WaterlooWorks Job Exporter

Export the jobs in a filtered WaterlooWorks results table to structured JSON and CSV. Use the files to review postings in a spreadsheet or, optionally, compare them with your resume using an LLM and build a focused application shortlist.

> Unofficial student-built project. Not affiliated with or endorsed by the University of Waterloo.

## What it does

- Opens a temporary Chromium browser so you can sign in to WaterlooWorks and choose your own search and filters.
- Exports the visible result set across pages, including posting details such as role, employer, location, term, deadline, skills, responsibilities, and application requirements.
- Saves `waterlooworks_jobs.json` and `waterlooworks_jobs.csv` in the project's `exports/` folder.
- Supports an optional resume-matching workflow: give an LLM the JSON and your resume, then ask it to rank suitable roles and explain the fit. You decide which roles to apply to.

The exporter uses WaterlooWorks' in-page posting functions rather than hard-coded action tokens. Its launcher creates a project-local Python environment, installs the pinned dependency and Chromium on first run, and reuses that setup afterward. Exports are checkpointed as the scan proceeds.

## Setup

You need Python and an internet connection for the first-run dependency and browser installation. The commands below find the latest extracted project folder under **Downloads**, so they do not depend on a specific Windows username or folder path.

### Windows

1. Install [Python](https://www.python.org/downloads/) if needed.
2. On this GitHub page, select **Code → Download ZIP**. In Downloads, right-click the ZIP and select **Extract All... → Extract**.
3. Open **Windows PowerShell**, paste this command, and press **Enter**:

```powershell
Get-ChildItem "$HOME\Downloads" -Recurse -Filter run.py | Where-Object { $_.FullName -like "*waterlooworks-job-exporter*" } | Sort-Object LastWriteTime -Descending | Select-Object -First 1 | ForEach-Object { py "$($_.FullName)" }
```

### Mac

1. Install [Python](https://www.python.org/downloads/) if needed.
2. On this GitHub page, select **Code → Download ZIP**. Double-click the ZIP in Downloads to extract it, and leave the extracted folder there.
3. Open **Terminal**, paste this command, and press **Return**:

```bash
python3 -c 'from pathlib import Path; import runpy; p=max((x for x in (Path.home()/"Downloads").rglob("run.py") if "waterlooworks-job-exporter" in str(x)), key=lambda x:x.stat().st_mtime); runpy.run_path(str(p), run_name="__main__")'
```

### Export jobs

On either system:

1. Wait for the browser to open, then sign in to WaterlooWorks in that browser.
2. Open **Co-op Jobs** and choose **Full-Cycle Service** or **Employer Student Direct**.
3. Apply filters or open a saved search. Switch the results to **Table Mode** and wait for the job rows to load.
4. Return to PowerShell or Terminal and press **Enter** (Windows) or **Return** (Mac).
5. When the export finishes, open `exports/waterlooworks_jobs.json` or `exports/waterlooworks_jobs.csv`.

The same command can be used for later exports. Keep the extracted project folder in Downloads.

## Privacy

Login takes place directly in the temporary browser. The exporter does not ask for or store your WaterlooWorks username, email, password, or Duo code. When it closes, the browser session is discarded.

The export contains selected posting fields only. It excludes raw WaterlooWorks responses, session/action tokens, cookies, browser storage, application state, personal posting tags such as `Viewed`, and WaterlooWorks service-team contact details. Email addresses found in posting text are replaced with `[redacted-email]`.

Export files stay on your computer unless you choose to share them. If you upload an export or resume to an LLM, that service's privacy practices apply. See [SECURITY.md](SECURITY.md) for details.

## Troubleshooting

- **`py` or `python3` is not recognized:** Install Python, reopen PowerShell or Terminal, and try again.
- **The exporter cannot find `run.py`:** Extract the ZIP inside Downloads and leave the project folder there.
- **No jobs are found:** Confirm that the filtered results are loaded in **Table Mode** before pressing Enter or Return.
- **Setup or browser installation fails:** Keep the terminal open and check your internet connection, then run the command again.

If WaterlooWorks changes its page structure or responses, the exporter may need an update.

## About the author

Built by Afshal Fatima, a Computer Engineering student at the University of Waterloo. [Portfolio](https://afshal-fatima.abloomlynx5.chatgpt.site) · [GitHub](https://github.com/Abble1) · [LinkedIn](https://www.linkedin.com/in/afshal-fatima-309b361a9/)
