# ClickUp capture — ground truth for Hub v2·M1 (ClickUp visual + feature parity)

> **Captured 2026-07-01** (`/build-hub` session 020, v2·M1a) from the operator's **authenticated real
> ClickUp** via the chrome-devtools MCP. Workspace **Automatisierbar** (`90121860456`), Space
> **Team-Space**, **Free plan**, **light theme**, viewport 1440-wide. This is the durable capture the FE
> parity track (M1b–M1g) reshapes against — a **reshape, not a rebuild** of the existing Hub view
> components; keep the green-terminal "Leitstand" identity as a deliberate divergence.

## Environment notes (matter for parity)

- **UI language = German** (Liste / Board / Kalender / Gantt / Tabelle; TO DO / IN BEARBEITUNG /
  VOLLSTÄNDIG) — matches the Hub's German UI, so labels transfer almost 1:1.
- **Free plan gates:** **Gantt** shows an upgrade wall (captured as `05-gantt-view.png`) — no live bars
  to mirror; treat Hub's `gantt-view.tsx` as an extra-we-keep, not a parity target. List/Board/Calendar/
  Table are all fully available.
- **Two-tone chrome:** the far-left **icon rail is near-black** (`cu-black`) even in light theme; the
  nav panel + content are white. The Hub's single-green Leitstand rail is the deliberate divergence here.
- ClickUp base font = the **system stack** (`-apple-system, system-ui, "Segoe UI", roboto…`), 13–14px
  body. Hub keeps Inter(prose)/mono(machine-facts) — a divergence to preserve.

## Design tokens (extracted from ClickUp's live `--cu-*` system → `computed-css/00-root-css-variables.json`)

**Text (content):** primary `#202020` · secondary `rgb(100,100,100)` · tertiary `rgb(131,131,131)` ·
disabled `rgb(187,187,187)` · on-primary `#fff`.
**Surfaces:** page/menu white `#fff` · overlay `rgba(0,0,0,.6)` · primary(dark, used by filled buttons)
`#202020`.
**Border:** default `#e8e8e8` (=grey300) · hover `#bbb`.
**Neutral ramp:** grey25 `#fcfcfc` · grey100 `#f9f9f9` · grey200 `#f0f0f0` · grey300 `#e8e8e8` · grey400
`#e0e0e0` · grey500 `#d9d9d9` · grey700 `#bbb` · grey900 `#838383` · grey1100 `#202020`.
**Brand / accents:** link-primary **purple `#5A43D6`** (rgb 90,67,214) · notification **pink `#E93D82`**
(233,61,130) · success green `rgb(24,121,78)` · warning `rgb(145,89,48)` · danger `rgb(198,42,47)` ·
hyperlink blue `rgb(11,104,203)`.
**Elevation (shadows):** e1 `0 1px 2px rgba(0,0,0,.055)` · e2 `0 1px 3px rgba(0,0,0,.106)` · e3
`0 4px 6px -1px …` · e4 `0 10px 15px -3px …` · e5 `0 20px 25px -5px …` · **border-1** (cards)
`0 0 1px rgba(0,0,0,.267), 0 1px 2px rgba(0,0,0,.05)`.
**Radii (measured on rendered elements — ClickUp has no `--radius` token):** toolbar chips **12px** ·
buttons **6–7px** · inputs **6px** · **cards 10px** · status pill 6px.
**Type scale (measured):** task title **28px/600** · card title **14px/500** · row/label **12–13px/500** ·
body **13–14px/400**. Filled primary button = dark `#202020`, white, radius 7px, ~28px tall.

## Surfaces → Hub counterpart component (reshape target)

Hub paths relative to `automatisierbar-hub/apps/web/src/` (tokens in `packages/ui`). ✅ = captured this
session.

| # | ClickUp surface | Screenshot | Key measurements (computed-css/) | Hub counterpart | Slice |
|---|---|---|---|---|---|
| 1 | Left nav / sidebar + black icon rail | ✅ `00-overview.png` | rail near-black; nav white, 12–13px rows | `components/sidebar.tsx` | M1f |
| 2 | Top chrome (workspace switch, ⌘K search, view tabs, Share/Automate) | ✅ `00-overview.png` | view tabs = icon+label, active underline | `components/view-switcher.tsx`, `list-workspace.tsx` | M1f |
| 3 | List view (grouped, status rows, columns Name/Assignee/Due/Priority/Status/Comments) | ✅ `01-list-view.png` | `01-list-view.json`: chip r12 `#e8e8e8`, AddTask dark r6, search inset-ring r6, row 29px, base 13px | `components/list-view.tsx` | M1c |
| 4 | Table view (Grid) | ✅ `03-table-view.png` | (see screenshot; same toolbar) | `components/table-view.tsx` | M1c |
| 5 | Board view (status columns + cards) | ✅ `02-board-view.png` | `02-board-view.json`: **card white r10 + elevation-border-1 shadow, 246×72**, title 14/500; header = status-colored count pill; toolbar adds **Sort** chip | `components/board-view.tsx` | M1d |
| 6 | Calendar view (Kalender, month grid) | ✅ `04-calendar-view.png` | month grid, event chips | `components/calendar-view.tsx` | M1d |
| 7 | Gantt / timeline | ✅ `05-gantt-view.png` (**free-plan upgrade wall**) | n/a — gated | `components/gantt-view.tsx` (keep as extra) | M1e |
| 8 | Task detail (full page: type badge, 28px title, 2-col field grid, description, right Activity panel) | ✅ `06-task-detail.png` | `06-task-detail.json`: title 28/600, status pill r6, field rows ~40px grey icon-labels, right panel ~470px, comment composer, filled btn `#202020` r7 | `components/task-slideover.tsx` | M1e |
| 9 | Comments / activity thread (right panel + composer) | ✅ `06-task-detail.png` (Activity panel) | composer w/ +, Comment select, attach/@/mic/send | `components/comment-thread.tsx` | M1e |
| 10 | Command palette / global search (⌘K modal) | ✅ `07-command-palette.png` | centered modal + dark overlay | `components/command-palette.tsx` | M1f |
| 11 | Filter menu (dropdown) | ✅ `08-filter-menu.png` | cdk-overlay dropdown off the Filter chip | `components/view-builder/filter-*.tsx` | M1f |
| 12 | Sort menu | ⬜ (same chip pattern as Filter; `Sort` chip present in Board toolbar) | — | `components/view-builder/sort-popover.tsx` | M1f |
| 13 | Group-by menu | ⬜ (toolbar shows `Group: Status` active chip in light-purple) | active chip = light-purple bg | `components/view-builder/group-select.tsx` | M1f |
| 14 | Multi-select bulk-action bar | ⬜ (not captured — appears on row-select; secondary) | — | `components/bulk-action-toolbar.tsx` | M1f |
| 15 | Custom fields | ⬜ (free-plan limited; fields shown in task grid captured in #8) | see task field grid | `components/custom-fields-panel.tsx`, `custom-field-input.tsx` | M1c |
| 16 | Attachments | ⬜ (attach affordance in composer, #8) | — | `components/attachment-list.tsx` | M1e |
| 17 | Settings surfaces | ⬜ (Hub `/app/settings` already exists; low parity priority) | — | `app/app/settings/`, `components/settings/` | M1f |
| 18 | Primitives — buttons/pills/inputs/menus | ✅ across all shots | filled btn `#202020` r7; chip white+`#e8e8e8` r12; input inset-ring r6; status pill r6 | `packages/ui/src/components/*` | M1b |

## Reshape guidance for M1b–M1g (from the capture)

- **M1b token reconciliation:** map ClickUp's radii (chips 12 / buttons 6–7 / cards 10 / inputs 6),
  the `#e8e8e8` hairline border, the elevation-border-1 card shadow, and the 13–14px system-font body
  onto `@hub/ui` tokens — **but keep** the green single-accent (ClickUp's accent is purple `#5A43D6`;
  Hub stays green as a deliberate divergence; borrow the *structure* not the hue).
- **M1c List/Table:** grouped sections with a status count header, compact 24–29px rows, the same
  column set (Name/Assignee/Due/Priority/Status/Comments), inline "Add Task" ghost row, split-button
  primary "Add Task".
- **M1d Board:** white cards r10 + subtle border-shadow, status-colored header count pills, card =
  title → icon row (assignee/date/priority) → color-coded due chip (overdue red, near orange) + priority
  flag; light-grey column body.
- **M1e task slide-over:** big emoji title, 2-column field grid with grey icon-labels + ~40px rows,
  description body, a right Activity panel (~470px) with a comment composer.
- **M1f chrome:** icon+label view tabs with an active underline, toolbar chips (Group/Sort/Filter/…),
  ⌘K centered modal, cdk-style dropdowns.

## Keep-our-extras audit (M1g)

- Green-terminal "Leitstand" identity (mono eyebrows, `// NN` accents, corner-brackets, single-green) — **keep.**
- MODULE nav section (Leads/Buchungen/Walk-in/Interview/Builds/Subdomains) — new in PRE-3, ClickUp has no equivalent.
- Gantt view (ClickUp gates it on free; Hub ships it) — keep.
- (append as found during M1b–M1f)

## Operator answers (resolved at the M1a login halt)

1. **Workspace to mirror:** Automatisierbar (`90121860456`), **Free plan** — capture everything available.
2. **Priority views:** all of them ("just get everything").
3. **Theme baseline:** **light** ✔ (captured light; Hub remains dark-first, so M1b maps structure/space, not the light palette).

## Not-yet-captured (secondary — grab on the next capture pass if M1b–M1g need them)

Sort menu · Group menu · multi-select bulk bar · a real custom-field editor · attachment thumbnails ·
full settings pages. All are minor variants of patterns already captured (dropdowns / chips / the task
grid), and each has an existing Hub component, so M1b–M1g can start now and backfill if a gap appears.
