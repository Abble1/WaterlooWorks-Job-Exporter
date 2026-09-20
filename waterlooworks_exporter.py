#!/usr/bin/env python3
"""
WaterlooWorks Job Exporter.

How it works
------------
- Opens a temporary browser session that is discarded when the program closes.
- You log in normally and navigate to a WaterlooWorks job-results page.
- Reads each result row's real posting ID from input#resultRow_<id>.
- Uses WaterlooWorks' own in-page getPostingData/getPostingOverview functions,
  so it does not depend on fake javascript:void(0) links or hard-coded action tokens.
- Walks through result pages using the site's "Go to next page" control.
- Saves sanitized JSON + CSV, and checkpoints while it runs. Internal action/session tokens are not exported.
- Email addresses are redacted from exported text.

It does not bypass authentication, Duo, CAPTCHA, permissions, or access controls.
"""

from __future__ import annotations

import argparse
import csv
import json
import os
import re
import shutil
import subprocess
import sys
import time
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Tuple

from playwright.sync_api import (
    Error as PlaywrightError,
    TimeoutError as PlaywrightTimeoutError,
    sync_playwright,
)

PUBLIC_VERSION = "1.0-public"
BASE_URL = "https://waterlooworks.uwaterloo.ca/"
DEFAULT_OUT = Path(__file__).resolve().parent / "exports"

FIELD_LABELS: List[Tuple[str, str]] = [
    ("work_term", "Work Term"),
    ("job_type", "Job Type"),
    ("job_title", "Job Title"),
    ("employer_internal_job_number", "Employer Internal Job Number"),
    ("number_of_job_openings", "Number of Job Openings"),
    ("level", "Level"),
    ("region", "Region"),
    ("address_line_one", "Job - Address Line One"),
    ("address_line_two", "Job - Address Line Two"),
    ("city", "Job - City"),
    ("province_state", "Job - Province/State"),
    ("postal_zip", "Job - Postal/Zip Code"),
    ("country", "Job - Country"),
    ("job_location", "Job Location (If Exact Address Unknown or Multiple Locations)"),
    ("employment_location_arrangement", "Employment Location Arrangement"),
    ("additional_employment_location_info", "Additional Employment Arrangement Location Information"),
    ("work_term_duration", "Work Term Duration"),
    ("special_start_end", "Special Work Term Start/End Date Considerations"),
    ("special_job_requirements", "Special Job Requirements"),
    ("job_summary", "Job Summary"),
    ("job_responsibilities", "Job Responsibilities"),
    ("required_skills", "Required Skills"),
    ("additional_information", "Additional Information"),
    ("transportation_housing", "Transportation and Housing"),
    ("compensation_benefits", "Compensation and Benefits"),
    ("targeted_degrees", "Targeted Degrees and Disciplines"),
    ("application_deadline", "Application Deadline"),
    ("application_documents_required", "Application Documents Required"),
    ("additional_application_information", "Additional Application Information"),
    ("application_method", "Application Method"),
    ("organization", "Organization"),
    ("division", "Division"),
]

NOISE_LINES = {
    "job posting information",
    "company information",
    "application information",
    "view targeted degrees and disciplines",
    "service team",
}


def norm_label(s: str) -> str:
    return re.sub(r"\s+", " ", s.strip()).rstrip(":").strip().casefold()


LABEL_LOOKUP = {norm_label(label): key for key, label in FIELD_LABELS}
KNOWN_LABELS = set(LABEL_LOOKUP)


def clean_lines(text: str) -> List[str]:
    out: List[str] = []
    for raw in text.replace("\r", "\n").split("\n"):
        line = re.sub(r"[ \t]+", " ", raw).strip()
        if line:
            out.append(line)
    return out


def parse_posting_text(text: str) -> Dict[str, str]:
    lines = clean_lines(text)
    data: Dict[str, str] = {}
    current_key: Optional[str] = None
    buf: List[str] = []

    def flush() -> None:
        nonlocal current_key, buf
        if current_key:
            value = "\n".join(buf).strip()
            if value:
                if current_key in data and data[current_key] and value not in data[current_key]:
                    data[current_key] += "\n\n" + value
                else:
                    data[current_key] = value
        current_key = None
        buf = []

    for line in lines:
        normalized = norm_label(line)
        if normalized in KNOWN_LABELS:
            flush()
            current_key = LABEL_LOOKUP[normalized]
            continue
        if normalized in NOISE_LINES:
            flush()
            continue
        if current_key is not None:
            buf.append(line)
    flush()
    return data


def open_context(playwright, browser: str, headless: bool = False):
    """Open a temporary browser context. Nothing from the login session is persisted."""
    launch_kwargs = {"headless": headless}
    browser_process = None

    if browser == "chrome":
        try:
            browser_process = playwright.chromium.launch(channel="chrome", **launch_kwargs)
        except Exception:
            print("Could not launch installed Chrome. Falling back to Chromium.")

    if browser_process is None:
        browser_process = playwright.chromium.launch(**launch_kwargs)

    context = browser_process.new_context(
        viewport=None if not headless else {"width": 1440, "height": 1000}
    )
    return browser_process, context


def wait_for_user(message: str) -> None:
    try:
        input(message)
    except EOFError:
        print("Interactive input is required for login/navigation.", file=sys.stderr)
        raise SystemExit(2)


def choose_waterlooworks_page(context, fallback):
    for p in reversed(context.pages):
        if p.is_closed():
            continue
        try:
            if "waterlooworks.uwaterloo.ca" in p.url.casefold():
                return p
        except PlaywrightError:
            pass
    for p in reversed(context.pages):
        if not p.is_closed():
            return p
    return fallback


def find_results_frame(page, timeout_ms: int = 15000):
    """Return the frame containing the WaterlooWorks result rows."""
    deadline = time.time() + timeout_ms / 1000
    last_error: Optional[Exception] = None
    while time.time() < deadline:
        for frame in page.frames:
            try:
                if frame.locator("input[id^='resultRow_']").count() > 0:
                    return frame
            except Exception as exc:
                last_error = exc
        time.sleep(0.25)
    raise RuntimeError(
        "Could not find WaterlooWorks result rows. Make sure the filtered job table is visibly loaded in Table Mode."
    ) from last_error


def extract_result_rows(frame) -> List[Dict[str, str]]:
    """Extract exactly what is visible in the result table."""
    rows = frame.eval_on_selector_all(
        "tr.table__row--body",
        r"""rows => rows.map(tr => {
            const input = tr.querySelector("input[id^='resultRow_']");
            if (!input) return null;
            const cells = Array.from(tr.querySelectorAll('td')).map(td =>
                (td.innerText || td.textContent || '').replace(/\s+/g, ' ').trim()
            );
            const title = tr.querySelector('td a.overflow--ellipsis');
            return {
                job_id: String(input.value || input.id.replace('resultRow_', '')),
                job_title: title ? (title.innerText || title.textContent || '').trim() : (cells[0] || ''),
                organization: cells[1] || '',
                division: cells[2] || '',
                number_of_job_openings: cells[3] || '',
                city: cells[4] || '',
                level: cells[5] || '',
                application_count: cells[6] || '',
                application_deadline: cells[7] || ''
            };
        }).filter(Boolean)""",
    )
    return rows


def helper_exists(frame, name: str) -> bool:
    return bool(frame.evaluate("name => typeof window[name] === 'function'", name))


def call_site_helper(frame, helper_name: str, job_id: str, timeout_ms: int = 20000) -> Any:
    """Call a WaterlooWorks callback-style helper and return its value.

    We deliberately call the function already defined by the loaded WaterlooWorks
    page. This means the site's current action token/session handling is used,
    rather than hard-coding a token captured on another day.
    """
    return frame.evaluate(
        """({helperName, jobId, timeoutMs}) => new Promise((resolve, reject) => {
            const fn = window[helperName];
            if (typeof fn !== 'function') {
                reject(new Error(helperName + ' is not available on this page'));
                return;
            }
            let finished = false;
            const timer = setTimeout(() => {
                if (!finished) {
                    finished = true;
                    reject(new Error(helperName + ' timed out for posting ' + jobId));
                }
            }, timeoutMs);
            try {
                fn(jobId, value => {
                    if (finished) return;
                    finished = true;
                    clearTimeout(timer);
                    resolve(value);
                });
            } catch (err) {
                if (!finished) {
                    finished = true;
                    clearTimeout(timer);
                    reject(err);
                }
            }
        })""",
        {"helperName": helper_name, "jobId": str(job_id), "timeoutMs": timeout_ms},
    )


def html_to_text(frame, html: str) -> str:
    return frame.evaluate(
        r"""html => {
            const doc = new DOMParser().parseFromString(html || '', 'text/html');
            const blockTags = new Set([
                'DIV','P','SECTION','ARTICLE','HEADER','FOOTER','MAIN','ASIDE',
                'H1','H2','H3','H4','H5','H6','LI','TR','TD','TH','UL','OL'
            ]);
            const parts = [];
            const walk = node => {
                if (node.nodeType === Node.TEXT_NODE) {
                    parts.push(node.textContent || '');
                    return;
                }
                if (node.nodeType !== Node.ELEMENT_NODE) return;
                const tag = node.tagName;
                if (tag === 'SCRIPT' || tag === 'STYLE' || tag === 'NOSCRIPT') return;
                if (tag === 'BR') { parts.push('\n'); return; }
                if (blockTags.has(tag)) parts.push('\n');
                for (const child of node.childNodes) walk(child);
                if (blockTags.has(tag)) parts.push('\n');
            };
            walk(doc.body);
            return parts.join('').replace(/\r/g, '');
        }""",
        html or "",
    )


def extract_targeted_degrees(frame, html: str) -> str:
    """Extract hidden targeted-degree/cluster list items from the posting HTML."""
    try:
        values = frame.evaluate(
            r"""html => {
                const doc = new DOMParser().parseFromString(html || '', 'text/html');
                return Array.from(doc.querySelectorAll('.targetedClusters li'))
                    .map(li => (li.textContent || '').replace(/\s+/g, ' ').trim())
                    .filter(Boolean);
            }""",
            html or "",
        )
        return "\n".join(dict.fromkeys(str(v) for v in values if str(v).strip()))
    except Exception:
        return ""


def merge_site_data(parsed: Dict[str, Any], site_data: Any) -> None:
    """Copy stable high-value top-level fields from getPostingData when present."""
    if not isinstance(site_data, dict):
        return
    mapping = {
        "id": "job_id",
        "position": "job_title",
        "org": "organization",
        "div": "division",
    }
    for src, dest in mapping.items():
        value = site_data.get(src)
        if value not in (None, ""):
            parsed[dest] = str(value)


def scrape_one_job(frame, table_row: Dict[str, str]) -> Dict[str, Any]:
    job_id = table_row["job_id"]
    site_data: Any = None
    overview_html = ""

    # Data first, mirroring WaterlooWorks' own doc-viewer component.
    if helper_exists(frame, "getPostingData"):
        site_data = call_site_helper(frame, "getPostingData", job_id)
    else:
        raise RuntimeError("WaterlooWorks getPostingData() was not found on the results page.")

    if helper_exists(frame, "getPostingOverview"):
        overview_html = call_site_helper(frame, "getPostingOverview", job_id)
    else:
        raise RuntimeError("WaterlooWorks getPostingOverview() was not found on the results page.")

    overview_text = html_to_text(frame, overview_html if isinstance(overview_html, str) else str(overview_html))
    parsed: Dict[str, Any] = parse_posting_text(overview_text)

    # Result-table values are reliable for these fields, so use them as fallbacks.
    for key, value in table_row.items():
        if value not in (None, ""):
            parsed.setdefault(key, value)

    merge_site_data(parsed, site_data)
    parsed["job_id"] = str(parsed.get("job_id") or job_id)

    # Targeted degrees/clusters are hidden behind a toggle in WaterlooWorks, so
    # innerText alone can miss them. Extract those list items before discarding HTML.
    targeted = extract_targeted_degrees(
        frame, overview_html if isinstance(overview_html, str) else str(overview_html)
    )
    if targeted:
        parsed["targeted_degrees"] = targeted

    # SECURITY: Do not save WaterlooWorks' raw getPostingData payload. It can
    # contain an application form action/session token. High-value safe fields
    # were already copied by merge_site_data(). Also omit raw HTML to keep the
    # export compact and limited to the fields we intentionally collect.
    return parsed


def visible_page_range(frame) -> str:
    try:
        texts = frame.locator(".table--view__pagination--data div").all_inner_texts()
        return " | ".join(t.strip() for t in texts if t.strip())
    except Exception:
        return ""


def click_next_page(frame, previous_first_id: str, timeout_ms: int = 15000) -> bool:
    next_link = frame.locator("a.pagination__link[aria-label='Go to next page']")
    if next_link.count() == 0:
        return False
    cls = next_link.first.get_attribute("class") or ""
    if "disabled" in cls.split():
        return False

    next_link.first.click()
    deadline = time.time() + timeout_ms / 1000
    while time.time() < deadline:
        try:
            rows = extract_result_rows(frame)
            if rows and rows[0]["job_id"] != previous_first_id:
                return True
        except PlaywrightError:
            pass
        time.sleep(0.25)
    raise RuntimeError("Clicked next page, but the WaterlooWorks result table did not update in time.")


EMAIL_RE = re.compile(r"[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}", re.IGNORECASE)


def redact_sensitive_text(value: Any) -> Any:
    """Recursively redact email addresses from exported values."""
    if isinstance(value, str):
        return EMAIL_RE.sub("[redacted-email]", value)
    if isinstance(value, list):
        return [redact_sensitive_text(v) for v in value]
    if isinstance(value, dict):
        return {k: redact_sensitive_text(v) for k, v in value.items()}
    return value


def json_safe_row(row: Dict[str, Any]) -> Dict[str, Any]:
    # Playwright values are already JSON-serializable, but normalize exotic leftovers.
    return json.loads(json.dumps(redact_sensitive_text(row), ensure_ascii=False, default=str))


def save_outputs(rows: List[Dict[str, Any]], out_dir: Path, checkpoint: bool = False) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)
    suffix = "_checkpoint" if checkpoint else ""
    json_path = out_dir / f"waterlooworks_jobs{suffix}.json"
    safe_rows = [json_safe_row(r) for r in rows]
    json_path.write_text(json.dumps(safe_rows, indent=2, ensure_ascii=False), encoding="utf-8")

    if checkpoint:
        return

    preferred = [
        "job_id", "job_title", "organization", "division", "number_of_job_openings",
        "level", "region", "city", "province_state", "country",
        "employment_location_arrangement", "work_term_duration", "application_count",
        "application_deadline", "application_documents_required", "application_method",
        "job_summary", "job_responsibilities", "required_skills",
        "compensation_benefits", "additional_application_information",
    ]

    keys = set()
    for row in safe_rows:
        keys.update(row.keys())
    fieldnames = [k for k in preferred if k in keys] + sorted(keys - set(preferred))

    csv_path = out_dir / "waterlooworks_jobs.csv"
    with csv_path.open("w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for row in safe_rows:
            writer.writerow({k: row.get(k, "") for k in fieldnames})

    print(f"\nSaved {len(rows)} posting(s):")
    print(f"  JSON: {json_path}")
    print(f"  CSV : {csv_path}")


def batch_scrape(page, out_dir: Path, delay: float, max_jobs: Optional[int]) -> List[Dict[str, Any]]:
    frame = find_results_frame(page)

    if not helper_exists(frame, "getPostingData") or not helper_exists(frame, "getPostingOverview"):
        raise RuntimeError(
            "The result rows are visible, but WaterlooWorks' posting helper functions are missing. "
            "Refresh the results page once and try again."
        )

    all_rows: List[Dict[str, Any]] = []
    seen: set[str] = set()
    page_number = 1

    while True:
        table_rows = extract_result_rows(frame)
        if not table_rows:
            raise RuntimeError("No result rows found on the current WaterlooWorks page.")

        print(f"\nResults page {page_number}: {visible_page_range(frame) or f'{len(table_rows)} visible jobs'}")

        for meta in table_rows:
            job_id = meta["job_id"]
            if job_id in seen:
                continue
            if max_jobs is not None and len(all_rows) >= max_jobs:
                save_outputs(all_rows, out_dir, checkpoint=True)
                return all_rows

            print(f"[{len(all_rows)+1}] {job_id} — {meta.get('job_title','')} — {meta.get('organization','')}")
            try:
                row = scrape_one_job(frame, meta)
                all_rows.append(row)
                seen.add(job_id)
                print("    OK")
            except Exception as exc:
                # Save a useful stub instead of losing the entire batch.
                stub: Dict[str, Any] = dict(meta)
                stub["scrape_error"] = "Could not export this posting."
                all_rows.append(stub)
                seen.add(job_id)
                print(f"    ERROR: {type(exc).__name__}")

            if len(all_rows) % 10 == 0:
                save_outputs(all_rows, out_dir, checkpoint=True)
            if delay > 0:
                time.sleep(delay)

        if max_jobs is not None and len(all_rows) >= max_jobs:
            break

        first_id = table_rows[0]["job_id"]
        if not click_next_page(frame, first_id):
            break
        page_number += 1

    save_outputs(all_rows, out_dir, checkpoint=True)
    return all_rows


def run_self_test(browser: str) -> None:
    """Test the exact selectors + helper-calling path using a local mock page."""
    fixture = r"""
    <!doctype html><html><body>
      <table><tbody>
        <tr class="table__row--body">
          <th><input id="resultRow_488373" value="488373"></th>
          <td><a class="overflow--ellipsis" href="javascript:void(0)">Software Development Research Assistant</a></td>
          <td>University of Calgary</td><td>McCaig Institute</td><td>1</td><td>Calgary</td>
          <td>Junior, Intermediate, Senior</td><td>13</td><td>Sep 17, 2026 9:00 AM</td>
        </tr>
      </tbody></table>
      <div class="table--view__pagination--data"><div>1 results</div><div>1 - 1</div></div>
      <script>
        function getPostingData(postingId, cb) {
          cb({id: postingId, position: 'Software Development Research Assistant', org: 'University of Calgary', div: 'McCaig Institute', applicationData: {canApply:true, website:'https://example.com/apply'}, tags:['Software']});
        }
        function getPostingOverview(postingId, cb) {
          cb(`<section>
            <div>Job Title</div><div>Software Development Research Assistant</div>
            <div>Job Summary</div><div>Build research software.</div>
            <div>Required Skills</div><div>Python and C++</div>
            <div>Application Deadline</div><div>Sep 17, 2026 9:00 AM</div>
            <div>Application Documents Required</div><div>Resume, Cover Letter</div>
            <div>Organization</div><div>University of Calgary</div>
            <div>Division</div><div>McCaig Institute</div>
            <div>SERVICE TEAM</div><div>Example Staff</div><div>(519-555-0100)</div>
            <ul class='targetedClusters' style='display:none'><li>- Theme - Computing: Software Development</li></ul>
          </section>`);
        }
      </script>
    </body></html>
    """

    with sync_playwright() as p:
        # Self-test should not touch the user's persistent profile.
        if browser == "chrome":
            try:
                b = p.chromium.launch(channel="chrome", headless=True)
            except Exception:
                exe = shutil.which("chromium") or shutil.which("chromium-browser") or shutil.which("google-chrome")
                if exe:
                    b = p.chromium.launch(executable_path=exe, headless=True)
                else:
                    b = p.chromium.launch(headless=True)
        else:
            exe = shutil.which("chromium") or shutil.which("chromium-browser") or shutil.which("google-chrome")
            if exe:
                b = p.chromium.launch(executable_path=exe, headless=True)
            else:
                b = p.chromium.launch(headless=True)
        page = b.new_page()
        page.set_content(fixture)
        frame = page.main_frame
        rows = extract_result_rows(frame)
        assert len(rows) == 1, rows
        assert rows[0]["job_id"] == "488373", rows
        assert rows[0]["application_count"] == "13", rows
        scraped = scrape_one_job(frame, rows[0])
        assert scraped["job_id"] == "488373", scraped
        assert scraped["job_title"] == "Software Development Research Assistant", scraped
        assert scraped["organization"] == "University of Calgary", scraped
        assert scraped["application_count"] == "13", scraped
        assert scraped["job_summary"] == "Build research software.", scraped
        assert scraped["required_skills"] == "Python and C++", scraped
        assert "Cover Letter" in scraped["application_documents_required"], scraped
        assert "Computing: Software Development" in scraped.get("targeted_degrees", ""), scraped
        assert "has_application" not in scraped, scraped
        assert "can_cancel_application" not in scraped, scraped
        assert "qualifiers" not in scraped, scraped
        assert "tags" not in scraped, scraped
        assert "service_team" not in scraped, scraped
        assert scraped.get("division") == "McCaig Institute", scraped
        assert "raw_text" not in scraped, scraped
        assert "site_data" not in scraped, scraped
        assert "overview_html" not in scraped, scraped
        b.close()

    print("SELF-TEST PASSED")
    print("- result-row selector")
    print("- job ID extraction")
    print("- applicant-count extraction")
    print("- getPostingData callback bridge")
    print("- getPostingOverview callback bridge")
    print("- overview HTML -> text -> field parser")
    print("- hidden targeted-degree extraction")
    print("- raw site_data/action tokens excluded from export")
    print("- user-specific application state excluded")
    print("- user-specific posting tags excluded")
    print("- WaterlooWorks service-team contact details excluded")
    print("- raw full-page posting text is not retained")
    print("- email addresses redacted from exports")



def reveal_export_file(path: Path) -> None:
    """Best-effort: open the output location and highlight the JSON file when possible."""
    try:
        resolved = path.resolve()
        if os.name == "nt":
            subprocess.Popen(["explorer", f"/select,{resolved}"])
        elif sys.platform == "darwin":
            subprocess.Popen(["open", "-R", str(resolved)])
        else:
            subprocess.Popen(["xdg-open", str(resolved.parent)])
    except Exception:
        # Opening the file manager is only a convenience; exporting still succeeded.
        pass


def main() -> None:
    print(f"WaterlooWorks Job Exporter {PUBLIC_VERSION}")
    parser = argparse.ArgumentParser(description="Export WaterlooWorks filtered co-op postings to JSON/CSV.")
    parser.add_argument("--out", type=Path, default=DEFAULT_OUT, help="Output directory")
    parser.add_argument("--browser", choices=["chrome", "chromium"], default="chromium")
    parser.add_argument("--delay", type=float, default=0.5, help="Seconds between posting requests (default: 0.5)")
    parser.add_argument("--max-jobs", type=int, default=None, help="Optional cap for testing, e.g. --max-jobs 5")
    parser.add_argument("--self-test", action="store_true", help="Run local selector/helper/parser test and exit")
    args = parser.parse_args()

    if args.self_test:
        run_self_test(args.browser)
        return

    with sync_playwright() as p:
        browser_process, context = open_context(p, args.browser, headless=False)
        pages = context.pages
        page = pages[0] if pages else context.new_page()
        try:
            page.goto(BASE_URL, wait_until="domcontentloaded", timeout=30000)
        except PlaywrightTimeoutError:
            pass

        print("\nA browser window is open.")
        print("1) Log into WaterlooWorks.")
        print("2) Open Co-op Jobs -> Full-Cycle Service or Employer Student Direct.")
        print("3) Apply filters or open a saved filter/search, then use Table Mode.")
        print("4) Wait until the job rows are visibly loaded.")
        wait_for_user("\nWhen the job table is visible, return here and press Enter... ")

        page = choose_waterlooworks_page(context, page)
        rows = batch_scrape(page, args.out, args.delay, args.max_jobs)
        save_outputs(rows, args.out, checkpoint=False)

        json_path = args.out / "waterlooworks_jobs.json"
        print(f"\nFinished. Your JSON file is here:\n  {json_path.resolve()}")
        print("\nThe folder should open automatically with waterlooworks_jobs.json highlighted.")
        print("You can drag that JSON file directly into ChatGPT.")
        print("Your login session is temporary and is discarded when this browser closes.")
        reveal_export_file(json_path)
        wait_for_user("\nPress Enter to close the browser... ")
        context.close()
        browser_process.close()


if __name__ == "__main__":
    main()
