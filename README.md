# WaterlooWorks Job Exporter

WaterlooWorks Job Exporter saves the jobs from your current WaterlooWorks results page as JSON and CSV files.

You can upload the JSON file to an LLM such as ChatGPT, Claude, Gemini, or another model that supports file uploads to help compare jobs, find the best matches for your resume, or sort through a large number of postings.

> Unofficial student-built project. Not affiliated with or endorsed by the University of Waterloo.

## Get Started

Choose your computer:

- [Windows](#windows)
- [Mac](#mac)

---

# Windows

## First Time

### 1. Install Python

If you already have Python installed, skip this step.

[Download Python](https://www.python.org/downloads/)

### 2. Download the Exporter

1. Click **Code → Download ZIP** on this GitHub page.
2. Open your **Downloads** folder.
3. Right-click `waterlooworks-job-exporter-main.zip`.
4. Click **Extract All → Extract**.

Leave the extracted `waterlooworks-job-exporter-main` folder in Downloads.

### 3. Start the Exporter

1. Search **Windows PowerShell** and open it.
2. Copy and paste both lines below into PowerShell.
3. Press **Enter**.

```powershell
cd "$HOME\Downloads\waterlooworks-job-exporter-main"
py run.py
```

The first time you run the exporter, it will automatically install the extra files it needs. The browser may take a few seconds to open, so keep PowerShell open and wait for it to appear.

### 4. Choose Your Jobs

1. A browser window should open automatically. In that browser, log into **WaterlooWorks**.
2. Open **Co-op Jobs**.
3. Choose **Full-Cycle Service** or **Employer Student Direct**.
4. Apply the filters you want, or open a saved filter.
5. Make sure the jobs are showing in **Table Mode**.
6. Go back to PowerShell and press **Enter**.

The exporter will go through the jobs currently shown in your results. When it finishes, File Explorer will open with `waterlooworks_jobs.json` selected.

You can now upload `waterlooworks_jobs.json` to any LLM that supports file uploads. Tell it what kinds of jobs you are looking for, give it any requirements you care about, or attach your resume and ask it to find the best matches for you.

For example:

> I attached my resume and my WaterlooWorks jobs. Find the jobs that fit me best. Prioritize software roles, 4-month positions, and jobs that match my current experience. Explain why each one is a good fit.

The exporter also creates `waterlooworks_jobs.csv` if you want to view the jobs in Excel or another spreadsheet app.

## Using It Again

1. Search **Windows PowerShell** and open it.
2. Copy and paste both lines below, then press **Enter**:

```powershell
cd "$HOME\Downloads\waterlooworks-job-exporter-main"
py run.py
```

3. Choose your WaterlooWorks jobs the same way as before, then go back to PowerShell and press **Enter** to export them.

---

# Mac

## First Time

### 1. Install Python

If you already have Python installed, skip this step.

[Download Python](https://www.python.org/downloads/)

### 2. Download the Exporter

1. Click **Code → Download ZIP** on this GitHub page.
2. Open your **Downloads** folder.
3. Double-click `waterlooworks-job-exporter-main.zip` to extract it.

Leave the extracted `waterlooworks-job-exporter-main` folder in Downloads.

### 3. Start the Exporter

1. Open **Terminal**.
2. Copy and paste both lines below into Terminal.
3. Press **Return**.

```bash
cd "$HOME/Downloads/waterlooworks-job-exporter-main"
python3 run.py
```

The first time you run the exporter, it will automatically install the extra files it needs. The browser may take a few seconds to open, so keep Terminal open and wait for it to appear.

### 4. Choose Your Jobs

1. A browser window should open automatically. In that browser, log into **WaterlooWorks**.
2. Open **Co-op Jobs**.
3. Choose **Full-Cycle Service** or **Employer Student Direct**.
4. Apply the filters you want, or open a saved filter.
5. Make sure the jobs are showing in **Table Mode**.
6. Go back to Terminal and press **Return**.

The exporter will go through the jobs currently shown in your results. When it finishes, Finder will open with `waterlooworks_jobs.json` selected.

You can now upload `waterlooworks_jobs.json` to any LLM that supports file uploads. Tell it what kinds of jobs you are looking for, give it any requirements you care about, or attach your resume and ask it to find the best matches for you.

For example:

> I attached my resume and my WaterlooWorks jobs. Find the jobs that fit me best. Prioritize software roles, 4-month positions, and jobs that match my current experience. Explain why each one is a good fit.

The exporter also creates `waterlooworks_jobs.csv` if you want to view the jobs in Excel or another spreadsheet app.

## Using It Again

1. Open **Terminal**.
2. Copy and paste both lines below, then press **Return**:

```bash
cd "$HOME/Downloads/waterlooworks-job-exporter-main"
python3 run.py
```

3. Choose your WaterlooWorks jobs the same way as before, then go back to Terminal and press **Return** to export them.

---

# Privacy

The exporter does not save your WaterlooWorks password, Waterloo account email, cookies, browser session, application state, or `Viewed` status.

Email addresses found inside job postings are replaced with `[redacted-email]`.

See [SECURITY.md](SECURITY.md) for more details.

# Troubleshooting

**`py` or `python3` is not recognized:** Install Python using the link above, reopen PowerShell or Terminal, and try again.

**The folder cannot be found:** Make sure the ZIP was extracted and `waterlooworks-job-exporter-main` is still in your Downloads folder.

**The exporter cannot find the jobs:** Make sure the WaterlooWorks results are showing in **Table Mode** before pressing Enter/Return.
