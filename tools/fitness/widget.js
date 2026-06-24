// ============================================================================
//  COMEBACK — Wochen-Widget (Scriptable, GROSS / large)
//  B&W-/Graustufen-/Tint-tauglich: SF Symbols (monochrome Vektor-Icons, bleiben
//  in Schwarz-Weiss scharf — anders als Emojis) + ausgeschriebene Wörter.
//  Oben rechts: Countdown-/Fortschritts-Ring (Bogen weiss → übernimmt den System-Tint).
//
//  Datenquelle: n8n  GET /webhook/fitness-widget  (von fitness_sync.py gefüttert)
//  SETUP: Scriptable → Script "Comeback" ersetzen → ▶ → Home-Screen → + →
//         Scriptable → **Large** → Edit Widget → Script: Comeback
//
//  STATUS:  ✓ erledigt · ▶ heute · ○ geplant · ◑ teilweise · ✕ verpasst
//  TYP:     Laufen=Cardio · Hantel=Kraft · Dehnen=Mobility · Koffer=Cuff
// ============================================================================

const WIDGET_URL = "https://oojoaquin.app.n8n.cloud/webhook/fitness-widget";

const INK    = new Color("#FFFFFF");
const DIM    = new Color("#A7AEB8");
const FAINT  = new Color("#62686F");
const LINE   = new Color("#3C4049");
const HILITE = new Color("#23303A");
const ACCENT = new Color("#34C759"); // decorative only — meaning never depends on color
const BG0    = new Color("#0A0B0D");
const BG1    = new Color("#16181D");

const TYPE_SF = { cardio: "figure.run", strength: "dumbbell.fill",
                  mobility: "figure.flexibility", cuff: "cross.case.fill", rest: "moon.stars.fill" };
const STATUS_SF = { done: "checkmark.circle.fill", today: "arrowtriangle.right.circle.fill",
                    planned: "circle", partial: "circle.lefthalf.filled", missed: "xmark.circle", rest: "moon.zzz.fill" };
const STATUS_TXT = { done: "✓", today: "▶", planned: "○", partial: "◑", missed: "✕", rest: "·" };
const VERDICT_SYM = { GO: "▲", EASY: "◐", REST: "○" };

async function load() {
  try {
    const r = new Request(WIDGET_URL); r.timeoutInterval = 12;
    const d = await r.loadJSON();
    if (d && (d.week || d.progress)) return d;
  } catch (e) {}
  return { week: [], progress: { done: 0, planned: 0, pct: 0 }, hrv: {}, streak_days: 0,
           starts_in_days: null, week_no: null, headline: "Keine Verbindung — kommt beim nächsten Sync" };
}

function sfimg(name, size) {
  try { const s = SFSymbol.named(name); if (!s) return null; s.applyFont(Font.systemFont(size)); return s.image; }
  catch (e) { return null; }
}
function addSF(stack, name, size, color) {
  const img = sfimg(name, size);
  if (img) { const wi = stack.addImage(img); wi.imageSize = new Size(size, size); wi.tintColor = color; return true; }
  return false;
}

// ---- ring (white arc → adopts the system tint) ----
function arcPts(cx, cy, r, a0, a1, steps) {
  const p = [];
  for (let i = 0; i <= steps; i++) { const t = (a0 + (a1 - a0) * i / steps) * Math.PI / 180; p.push(new Point(cx + r * Math.cos(t), cy + r * Math.sin(t))); }
  return p;
}
function dialImage(data) {
  const S = 230, lw = 17;
  const ctx = new DrawContext(); ctx.size = new Size(S, S); ctx.opaque = false; ctx.respectScreenScale = true;
  const cx = S / 2, cy = S / 2, r = S / 2 - lw / 2 - 3;
  const bg = new Path(); bg.addLines(arcPts(cx, cy, r, -90, 270, 80));
  ctx.setStrokeColor(LINE); ctx.setLineWidth(lw); ctx.addPath(bg); ctx.strokePath();
  let pct, big, small;
  const prog = data.progress || {};
  if (data.starts_in_days && data.starts_in_days > 0) { pct = Math.max(0.04, 1 - data.starts_in_days / 14); big = String(data.starts_in_days); small = "TAGE"; }
  else if (prog.planned > 0) { pct = prog.pct || 0; big = `${prog.done}/${prog.planned}`; small = "WOCHE"; }
  else { pct = (data.hrv && data.hrv.ms) ? Math.min(1, data.hrv.ms / 120) : 0.5; big = (data.hrv && data.hrv.ms) ? String(data.hrv.ms) : "—"; small = "HRV"; }
  if (pct > 0) { const fg = new Path(); fg.addLines(arcPts(cx, cy, r, -90, -90 + 360 * Math.min(1, pct), Math.max(2, Math.round(80 * pct)))); ctx.setStrokeColor(INK); ctx.setLineWidth(lw); ctx.addPath(fg); ctx.strokePath(); }
  ctx.setTextAlignedCenter();
  ctx.setTextColor(INK); ctx.setFont(Font.boldMonospacedSystemFont(64)); ctx.drawTextInRect(big, new Rect(0, cy - 52, S, 70));
  ctx.setTextColor(DIM); ctx.setFont(Font.mediumSystemFont(20)); ctx.drawTextInRect(small, new Rect(0, cy + 22, S, 26));
  return ctx.getImage();
}

async function build() {
  const data = await load();
  const w = new ListWidget();
  const g = new LinearGradient(); g.colors = [BG1, BG0]; g.locations = [0, 1];
  g.startPoint = new Point(0, 0); g.endPoint = new Point(0, 1); w.backgroundGradient = g;
  w.setPadding(14, 15, 11, 15);

  // ---- top: title/headline/verdict (left) + ring (right) ----
  const top = w.addStack(); top.layoutHorizontally(); top.centerAlignContent();
  const tl = top.addStack(); tl.layoutVertically(); tl.spacing = 2;
  const t = tl.addText("COMEBACK  PROTOKOLL"); t.font = Font.boldSystemFont(11); t.textColor = DIM;
  const hl = tl.addText(data.headline || ""); hl.font = Font.mediumSystemFont(11); hl.textColor = DIM; hl.lineLimit = 2;
  tl.addSpacer(6);
  const v = (data.hrv && data.hrv.verdict) || "—";
  const hrvms = (data.hrv && data.hrv.ms) ? `${data.hrv.ms}${data.hrv.arrow ? " " + data.hrv.arrow : ""}` : "—";
  const vr = tl.addText(`${VERDICT_SYM[v] || "·"} ${v}   ·   HRV ${hrvms}`); vr.font = Font.boldSystemFont(15); vr.textColor = INK;
  top.addSpacer();
  const ring = top.addImage(dialImage(data)); ring.imageSize = new Size(82, 82);
  w.addSpacer(9);

  // ---- week rows ----
  const days = (data.week && data.week.length) ? data.week : [];
  const list = w.addStack(); list.layoutVertically(); list.spacing = 1;
  for (const d of days) {
    const st = d.state || "planned";
    const today = st === "today";
    const row = list.addStack(); row.layoutHorizontally(); row.centerAlignContent();
    row.setPadding(4, 8, 4, 8); row.cornerRadius = 8;
    if (today) row.backgroundColor = HILITE;
    const wdc = row.addStack(); wdc.size = new Size(30, 0);
    const wd = wdc.addText(d.day || ""); wd.font = today ? Font.boldSystemFont(15) : Font.semiboldSystemFont(15);
    wd.textColor = today ? INK : DIM;
    const tcol = today ? INK : (st === "missed" ? FAINT : DIM);
    if (!addSF(row, TYPE_SF[d.type] || "circle", 17, tcol)) { const f = row.addText("•"); f.textColor = tcol; }
    row.addSpacer(9);
    const lab = row.addText(d.label || ""); lab.font = today ? Font.semiboldSystemFont(14) : Font.regularSystemFont(14);
    lab.textColor = st === "missed" ? FAINT : INK; lab.lineLimit = 1;
    row.addSpacer();
    const scol = st === "done" ? ACCENT : (today ? INK : (st === "missed" ? FAINT : DIM));
    if (!addSF(row, STATUS_SF[st] || "circle", 17, scol)) { const sx = row.addText(STATUS_TXT[st] || "○"); sx.font = Font.boldSystemFont(15); sx.textColor = scol; }
  }
  if (!days.length) { const e = w.addText("Programm startet bald — Daten folgen."); e.font = Font.mediumSystemFont(13); e.textColor = DIM; }

  // ---- footer ----
  w.addSpacer();
  const foot = w.addStack(); foot.layoutHorizontally(); foot.centerAlignContent();
  const legend = foot.addText("✓ erledigt   ▶ heute   ○ geplant   ✕ verpasst");
  legend.font = Font.systemFont(9); legend.textColor = FAINT;
  foot.addSpacer();
  if (data.streak_days && data.streak_days > 0) { const stk = foot.addText(`${data.streak_days}-Tage-Streak`); stk.font = Font.boldSystemFont(10); stk.textColor = DIM; }

  w.refreshAfterDate = new Date(Date.now() + 30 * 60 * 1000);
  return w;
}

const widget = await build();
if (config.runsInWidget) Script.setWidget(widget);
else await widget.presentLarge();
Script.complete();
