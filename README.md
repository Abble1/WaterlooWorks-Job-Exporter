# WaterlooWorks Job Exporter

WaterlooWorks Job Exporter saves the jobs from your current WaterlooWorks results page as JSON and CSV files.

You can upload the JSON file to an LLM such as ChatGPT, Claude, Gemini, or another model that supports file uploads to help compare jobs, find the best matches for your resume, or sort through a large number of postings.

> Unofficial student-built project. Not affiliated with or endorsed by the University of Waterloo.

## First Time

### 1. Install Python

If you already have Python installed, skip this step.

[Download Python](https://www.python.org/downloads/), install it, then continue below.

### 2. Download and Extract the Exporter

On this GitHub page, click **Code → Download ZIP**.

In your **Downloads** folder:

- **Windows:** right-click `waterlooworks-job-exporter-main.zip` → **Extract All...** → **Extract**.
- **Mac:** double-click `waterlooworks-job-exporter-main.zip` to extract it.

Leave the extracted `waterlooworks-job-exporter-main` folder in Downloads.

### 3. Open PowerShell or Terminal

- **Windows:** search **Windows PowerShell** and open it.
- **Mac:** open **Terminal**.

### 4. Start the Exporter

**Windows:** copy and paste both lines below into PowerShell, then press **Enter**.

```powershell
cd "$HOME\Downloads\waterlooworks-job-exporter-main"
py run.py
```

**Mac:** copy and paste both lines below into Terminal, then press **Return**.

```bash
cd "$HOME/Downloads/waterlooworks-job-exporter-main"
python3 run.py
```

The first time you use the exporter, it will automatically install the extra files it needs. Keep PowerShell or Terminal open and wait for the browser to open.

### 5. Choose and Export Your Jobs

In the browser:

1. Log into WaterlooWorks.
2. Go to **Co-op Jobs → Full-Cycle Service** or **Co-op Jobs → Employer Student Direct**.
3. Apply the filters you want, or open a saved filter/search.
4. Make sure the jobs are showing in **Table Mode**.
5. Go back to PowerShell or Terminal and press **Enter/Return**.

The exporter will go through the jobs in the results you currently have open.

### 6. Use Your Export

When the export finishes, File Explorer or Finder will open with `waterlooworks_jobs.json` selected.

Upload that JSON file to any LLM that supports file uploads. You can also attach your resume and ask it to find the jobs that fit you best.

For example:

> I attached my resume and my WaterlooWorks jobs. Find the jobs that fit me best and explain why.

A `waterlooworks_jobs.csv` file is also created if you want to view the jobs in Excel or another spreadsheet app.

## Using It Again Later

You do **not** need to reinstall Python or download the exporter again.

### 1. Open PowerShell or Terminal

- **Windows:** search **Windows PowerShell** and open it.
- **Mac:** open **Terminal**.

### 2. Start the Exporter

**Windows:**

```powershell
cd "$HOME\Downloads\waterlooworks-job-exporter-main"
py run.py
```

**Mac:**

```bash
cd "$HOME/Downloads/waterlooworks-job-exporter-main"
python3 run.py
```

### 3. Choose and Export Your Jobs

Open **Full-Cycle Service** or **Employer Student Direct**, apply your filters or open a saved filter/search, and make sure the jobs are showing in **Table Mode**.

Go back to PowerShell or Terminal and press **Enter/Return**. Your JSON file will open automatically when the export finishes.

## Privacy

The exporter does not save your WaterlooWorks password, Waterloo account email, cookies, browser session, application state, or `Viewed` status. Email addresses found inside job postings are replaced with `[redacted-email]` in the exported files.

See [SECURITY.md](SECURITY.md) for more details.

## Troubleshooting

**`py` or `python3` is not recognized:** Install Python using the link in Step 1, reopen PowerShell or Terminal, and try again.

**The folder cannot be found:** Make sure the ZIP was extracted and `waterlooworks-job-exporter-main` is still in your Downloads folder.

**The exporter cannot find the jobs:** Make sure the WaterlooWorks results are showing in **Table Mode** before pressing Enter/Return.
