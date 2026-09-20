# Security and privacy

This tool does not ask for or store WaterlooWorks usernames, email addresses, passwords, or Duo codes.

Login happens directly in the browser window opened by the tool. The browser session is temporary and is discarded when the program closes.

The exporter only saves selected job-posting fields. It does not save the raw WaterlooWorks data response, session/action tokens, cookies, browser storage, user-specific application state, user-specific posting tags (such as `Viewed`), or WaterlooWorks service-team contact details. Email addresses found in exported posting text are replaced with `[redacted-email]`.

Do not add browser profiles, authentication state, cookies, exported job files, or `.env` files to the repository. The included `.gitignore` blocks the common forms of these files.

No software can guarantee complete security. If WaterlooWorks changes its page structure or API responses, review the exporter again before relying on it.
