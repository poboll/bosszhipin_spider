# BOSS直聘 Spider Refresh Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Make the legacy BOSS直聘 crawler runnable from a Conda environment, portable across machines, diagnosable when BOSS requires security verification, and safe to use for local Excel merging.

**Architecture:** Keep Pyppeteer as the browser layer and preserve the existing Chinese output columns. Replace hard-coded Windows paths and brittle single selectors with CLI arguments, selector fallbacks, structured parsing helpers, explicit security-verification detection, and guaranteed browser cleanup. Keep Excel merging as an import-safe CLI function with validation and add focused parser/merge tests.

**Tech Stack:** Python 3.11, Pyppeteer 2.x, lxml, pandas, openpyxl, Conda, unittest.

---

### Task 1: Add regression tests for parsing and Excel merging

**Files:**
- Create: `tests/test_spider.py`
- Create: `tests/test_merge.py`

**Steps:**

1. Add a synthetic legacy/current job-card fixture and assert that the parser extracts position, salary, company, location, experience, education, benefits, skills, and company tags without raising on missing optional fields.
2. Add an Excel fixture test covering multiple sheets, differing headers, an empty input directory, and exclusion of the output file from its own input set.
3. Run `conda run -n bosszhipin_spider python -m unittest discover -s tests -v` and confirm the new tests fail against the legacy implementation where expected.

### Task 2: Refactor `p.py` into a portable crawler CLI

**Files:**
- Modify: `p.py`

**Steps:**

1. Add CLI arguments for city slug, city code, keyword, output path, page limit, headless mode, executable path, profile path, and timeout.
2. Register the browser initialization script before navigation, use a configurable browser executable, and close the browser in `finally`.
3. Use stable search selectors such as `input[name=query]` and `button.btn-search`, retain fallbacks for the legacy layout, and detect BOSS verification pages with an actionable error.
4. Parse both legacy `job-list-box` cards and current job-card/company-job structures through optional-field helpers; stop when no usable next-page control exists instead of clicking a fixed child index.
5. Return a non-zero exit code with a concise error for security verification, missing selectors, empty results, or invalid output paths.
6. Run parser tests and a `--help` smoke test.

### Task 3: Make `q.py` safe and repeatable

**Files:**
- Modify: `q.py`

**Steps:**

1. Move execution behind `if __name__ == '__main__'` and add `--input-dir`/`--output` arguments.
2. Validate that input files exist, ignore the output workbook when it is inside the input directory, close workbooks promptly, and concatenate sheets with unioned columns.
3. Run merge tests and a real merge against the repository's sample workbooks into `/tmp`.

### Task 4: Document reproducible use and project limits

**Files:**
- Create: `requirements.txt`
- Create: `environment.yml`
- Modify: `README.md`

**Steps:**

1. Document Conda setup, Chrome executable configuration, crawler/merge commands, output columns, and the fact that BOSS may require manual security verification.
2. Replace stale hard-coded code snippets and explain that the included XLSX files are historical analysis outputs.
3. Run syntax compilation, unit tests, and command help from the Conda environment.

### Task 5: Apply and verify repository metadata and Issue responses

**Files:**
- Remote GitHub repository metadata and Issues only.

**Steps:**

1. Set a concise Chinese/English-discoverable description and relevant Topics for Python, web scraping, Pyppeteer, pandas, Excel, job data, BOSS直聘, and FineBI.
2. Reply to Issue #1 with the supported contact channel and to Issue #2 with the public source/documentation location; close each only after the response resolves its request.
3. Verify the final GitHub metadata, issue states/comments, pushed commit, and Conda test results.
