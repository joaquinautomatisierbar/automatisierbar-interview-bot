# Revenue Lab — Learnings (read on every wake via recall-learnings)

Operational lessons learned the hard way. Every agent reads this before working so we do not
repeat mistakes. Newest first.

---

## 2026-06-14 — Two failures on the first build (brand bleed + no visual QA)

**What happened:** The first Prozess-Audit Bericht PDF reached the operator (a) fully branded as
*Automatisierbar* (its name, violet "Theme 02", `joaquin@automatisierbar.ch`), and (b) visually
broken — the before/after diagram rendered as a tiny dark box with microscopic, overlapping,
illegible text. The operator (correctly) rejected it.

**Why it happened:**
1. **Brand bleed:** the build reused Automatisierbar's brand assets + scripts (`visual_process_diagram.py`
   Theme 02, its PDF themes, its business-context) and its email. Revenue Lab is a SEPARATE
   business and must never carry Automatisierbar's identity.
2. **No QA:** no agent rendered the PDF and looked at it before it shipped. A defect a human
   spots in two seconds went out untouched.

**Binding rules (do not violate):**
- **Zero Automatisierbar in any artifact.** Use ONLY the Revenue Lab brand guide
  (`brand/BRAND_GUIDE.md`). No AUT name/colors/Theme-02/`@automatisierbar.ch`, no reuse of AUT
  script styling. If the brand guide is still TBD, run the brand-proposal cycle first.
- **Never ship a deliverable nobody has observed.** Builder marks `READY_FOR_REVIEW`; QA renders
  it (`render_pdf.py` → Read the PNGs) and checks it before anything reaches the operator. A
  "looks fine" without rendering is not a review. (See `verify-deliverable`, `handoff-protocol`.)
- **Honesty:** no "100% automation"; show human-residual time separately; ground every number.

**Why this matters:** the whole point of this experiment is to get *smarter* each cycle. A
mistake that isn't written down here will be repeated. If you catch a new class of defect, add it.
