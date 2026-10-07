# Original visual style restored

User requested the original UI style, recovered from Git `09e5c0c` and the
preserved `app/legacy_streamlit_app.py`. The T3 frontend replacement at `bef1235`
had replaced that design with a minimal blue chat page.

Restored the MandiPulse / Quiet Exchange design: exact original palette/font
tokens, warm parchment/linen, oxblood accents, editorial serif masthead,
monospaced badges, thin borders, small radii and sidebar brand rail. The static
theme lives in `app/transit_theme.html`. Sidebar copy describes current supported
scope; the frozen T3 API and response rendering remain authoritative.

Verification:

- 37 focused frontend tests pass. App compilation and diff checks pass.
- Real localhost API replies visually covered all five statuses, including
  dated Deluxe stage-4 fare, live-GPS refusal, multi-stage clarification,
  out-of-scope and malformed-input error. Non-OK states have no success panels.
- Current desktop1440×1000 and narrow390×844 layouts checked. Body/document width
  equals viewport width; mobile sidebar expands/collapses without clipping.
- Corrected Streamlit's caption opacity0.6 to1, preserving legible source/date/
  status caveats. Current title size36px desktop/28px narrow matches original
  typography; mobile masthead clears the sticky header.
- Chat input, revised-question input and its submit button display2px oxblood
  focus outlines; revised controls verified with keyboard Tab.
- Temporary viewport reset and temporary QA tab closed; the existing user tab
  refreshed to the restored design. No backend, model, taxonomy, evaluator,
  canonical data or Phase21 report changes.

Evidence: [desktop](desktop.jpg), [mobile masthead](mobile-header.jpg),
[mobile sidebar](mobile-sidebar.jpg), [mobile fare](mobile-fare.jpg),
[clarification](mobile-clarification.jpg), [non-answer states](mobile-statuses.jpg).

Font loading uses the original Google Fonts URL with local serif/sans/monospace
fallbacks. The old model roster, prototype data, voice and debug features are
not reintroduced by this visual restoration.

Fresh GPT-6.1 Sol xhigh reviewer approved the restoration: zero unresolved
critical/high/medium/low findings. All62 theme tokens match the original values;
all six API/render functions are structurally unchanged. Reviewer verified final
desktop/mobile images, corrected caption contrast and responsive title sizes.
