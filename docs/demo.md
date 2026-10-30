# Five-minute demonstration

Start both services, open FINN, and use Demo replay for the synthetic PUSH scenarios. Research is independent of replay and always uses actual dated issuer documents. Keep this distinction explicit to evaluators.

## 1. A management change deserves attention

Open Overview. The synthetic TCS CFO-resignation scenario appears at high priority. Expand **See the reasoning**: the rule assigns 85 base points for management change and 10 more for departure language. Read **Why it matters**, then explain that review urgency is not a predicted investment return. The card is labelled **Simulated disclosure** and does not invent a source URL.

Switch the window to Last 7 days. Filter High priority or a company/category. Clear filters and expand routine filings to demonstrate information triage.

## 2. A volume event the investor defines

Open Signals & alerts. Under default rules (5% price, 2x volume, 20 sessions), the replay includes three unusual-volume crossings and two price moves. Expand a volume alert: it compares the latest simulated session with exactly the preceding 20 sessions. The current day's volume is not part of the baseline.

Open Monitoring preferences and raise volume to 3.5x. Save; volume alerts disappear while price alerts remain. Restore 2x. The UI saves to SQLite and recalculates in Python; these are not frontend-only controls.

Switch to Sourced data and Refresh sources to demonstrate the real path. Inspect original dates and source links. Latest returned sessions can be older than today. Do not promise a particular stock move or current alert; actual thresholds may produce none.

## 3. A results table that can be checked

Open Research desk → INFY → Financial snapshot. The historical Q4 FY25 comparison shows revenue of INR 40,925 crore, compared with INR 41,764 crore in Q3 FY25 and INR 37,923 crore in Q4 FY24. QoQ is -2.01%; YoY is +7.92%. PAT attributable to owners is INR 7,033 crore. Source links go to page 6 of the original company releases.

EBITDA is unavailable rather than invented or confused with operating profit. Percentages are calculated deterministically. These are historical reports, not current-quarter claims.

## 4. A question, with evidence

Choose Research & evidence and **How strong is cash conversion?**. Without a model key, FINN returns labelled extractive passages. Expand a citation, inspect the document period and physical page, and open the original company source. With a valid configured key, the same evidence is used for structured AI synthesis; do not claim this was live-verified unless you have actually configured and exercised the key.

Prepared examples:

| Company | Example question | Evidence |
| --- | --- | --- |
| INFY | How strong is cash conversion? | Annual report, results releases and earnings calls |
| TCS | What does the company say about demand and order wins? | Original Q4 FY25 issuer results release |
| PERSISTENT | What business does the company operate and what risks are disclosed? | Original FY25 annual report |
| POLYCAB | What does management say about the business and risks? | Generic discovery/import of an October 2026 BSE-hosted issuer transcript, verified outside the seeded portfolio |

To prove generalisation, enter a different NSE ticker. Find company resolves it; Source library → Discover offers primary report/transcript links. Import a permitted document. Missing evidence produces a refusal, not a profile invented from model memory. Unseen-ticker availability depends on the sources at demo time.

## 5. Promise versus reality

Select INFY → Promise vs. reality. The target is FY25 constant-currency revenue growth throughout. Actual is 4.2%.

| Statement date | Range | Outcome | Deviation from nearest bound |
| --- | --- | --- | --- |
| 18 April 2024 | 1–3% | Exceeded | +1.2 pp |
| 18 July 2024 | 3–4% | Exceeded | +0.2 pp |
| 17 October 2024 | 3.75–4.5% | Achieved | 0.0 pp |
| 16 January 2025 | 4.5–5% | Missed | -0.3 pp |

Expand Evidence on the last revision. Open the original earnings-call page and the final results page. Explain why these are four revisions of **one annual forecast**, not four independent quarters or a trustworthy statistical management-credibility score. A vague optimistic comment is never converted into a numeric promise.

## Mobile check

Try a phone or narrow browser: use the bottom navigation, horizontally scroll the research tab strip and financial table, and inspect the stacked guidance rows. No essential interaction depends on hover. In-app links open original source documents in a new tab.
