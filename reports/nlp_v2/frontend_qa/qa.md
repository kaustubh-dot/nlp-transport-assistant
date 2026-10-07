# Phase 22 frontend QA — verified

The frontend changes presentation only. Backend/API/contracts/model/evaluators,
canonical DB and research are unchanged from source freeze `8ee8917`.

Verified current code:

- Full suite: **611 passed in 15.01 seconds**. Compilation, dependency and diff
  checks pass; 37 focused frontend tests pass.
- Seven synthetic UI regressions reproduced red before status/candidate/partial
  metadata changes. Three review crash regressions reproduced red and were fixed
  with presentation-only type guards.
- Real API on localhost 8875 supplied fare, route stops, nearest metro,
  multi-stage clarification, live-GPS refusal, out-of-scope and malformed error.
  All seven current replies render through AppTest without exceptions. All five
  statuses retain labels and snapshot limitations. Non-OK replies render no
  successful metric/table panels. API HTTP 422 errors remain visible errors.
- Fresh GPT-6.1 Sol xhigh independently re-rendered seven real replies and five
  malformed optional metadata cases with no exceptions or private count strings.
  Unresolved critical/high/medium/low code findings: zero.

Browser observations before the final spacing correction:

- Real desktop 1280×900 fare panel displayed INR 17, Deluxe Services, recorded
  effective date 2018-01-29, MTC_OFFICIAL source and current-service caveat.
  [Desktop evidence](desktop-fare.jpg).
- At 390×844, the fare message/source/caveat wrapped within the screen. Read-only
  DOM inspection measured document/body scroll width 390 (no page overflow).
- Desktop inspection found the kicker at y=48 under the 60-pixel toolbar. CSS
  top padding was increased to 4.5rem at both widths. Browser access disappeared
  before post-change visual confirmation; current inventory has no browsers.
  Rebinding/reopening did not restore it. User restoration is requested.

The browser connection subsequently returned. Current code was refreshed and
verified at **1280×900 and390×844**. The header clears the toolbar at both widths;
all five real API statuses were visually checked at both widths. Fare message,
class, source, effective date and caveat wrap correctly. Clarification guidance
and revision controls remain usable; unavailable/out-of-scope/error states show
their appropriate notices without successful result panels or internal details.
Read-only DOM measurements report body/document width equal to viewport width
at both sizes, including the narrow accumulated chat. Temporary viewport override
was reset after testing.

Current evidence: [desktop fare](desktop-current.jpg),
[desktop non-answer states](desktop-statuses.jpg), [narrow header](mobile-header.jpg),
[narrow fare](mobile-current.jpg), [clarification](mobile-clarification.jpg),
[unavailable](mobile-unavailable.jpg), [out of scope](mobile-out-of-scope.jpg),
[error](mobile-error.jpg). The earlier desktop screenshot above remains identified
as preceding the spacing correction.

Fresh GPT-6.1 Sol xhigh inspected all eight current screenshots, verified the empty backend diff and granted final Phase22 signoff with zero unresolved findings. Phase22 visual acceptance is complete. Final project closure remains blocked by
a distinct medium backend finding from the final complete-project review.
No backend adjustment or historical evaluator rerun was made during frontend QA.
