# Paperclip — Team Intro Call (Patrik · Nico · Tej)

**Audience:** non-technical operators who will *use* Paperclip to build automations day-to-day.
**Goal of the call:** by the end they can (1) take a customer interview result and turn it into a shipped automation, and (2) build their own idea from scratch using the Internal Planner — without needing Joaquin to do it for them.
**Length:** ~35–40 min. Keep it hands-on. One live build beats ten slides.

> Language note: drafted in English. If the call runs in German/Swiss-German, say the word and I'll translate the leave-behind cheat sheet.

---

## PART 1 — Slides Outline (10 slides)

Keep slides as *anchors*, not scripts. One idea per slide. The real teaching happens in the live demo (Part 2).

**Slide 1 — Title**
> "Paperclip: your AI build team."
Subtitle: "From idea → working automation, without waiting on me."

**Slide 2 — Why this exists (the problem)**
- Today every automation goes through Joaquin → he's the bottleneck.
- Paperclip = a *company of AI specialists* you can delegate to directly.
- You describe what you want; the team plans, builds, tests, documents, and ships it to GitHub.

**Slide 3 — The mental model**
- Think of Paperclip as a **dev agency staffed by AI**, not a piece of software you operate.
- You're the *client*. You brief it, review what comes back, and ask for changes — like emailing an agency.
- You do **not** need to code. You need to *describe clearly* and *review honestly*.

**Slide 4 — Who's on the team (the agents)**
The two you'll talk to most:
- **🧭 Internal Planner** — turns a rough idea into a clean, buildable spec.
- **🧪 Test Data Generator** — gives you realistic fake data to test an automation safely.
The build crew (work behind the scenes, you don't trigger them by hand):
- **Engineer** builds → **QA** tests → **Product Reviewer** checks it solves the real problem → **Release** ships it to GitHub.

**Slide 5 — Two ways you'll use it**
- **Path A — From a customer interview** (warm start: spec already exists).
- **Path B — From your own idea** (cold start: you create the spec with the Internal Planner).
Both end the same way: a working automation on GitHub that you can review and iterate on.

**Slide 6 — Path A: Interview → Shipped**
1. Customer finishes the **workflow interview** → it produces a build spec.
2. That spec goes into Paperclip as a new job.
3. The build team builds + tests it → result lands on **GitHub**.
4. You review it, go back to the **chat to iterate** ("change X, add Y").
5. Need to test it? Ask the **Test Data Generator** for sample data.

**Slide 7 — Path B: Your idea → Built**
1. Open the **Internal Planner**, describe your idea in plain language.
2. It asks clarifying questions and writes a clean spec (a "prompt").
3. Hand that spec to the build team **inside Paperclip**.
4. Same as Path A from there: review on GitHub, iterate in chat, test with sample data.

**Slide 8 — How to iterate (the loop)**
- Building is a *conversation*, not a one-shot.
- Be specific: "The email subject is wrong, it should be X" beats "make it better."
- Re-review after each change. Small loops > big rewrites.

**Slide 9 — The 3 rules (so nothing breaks or burns money)**
1. **Don't un-pause agents you didn't pause.** If something's paused, there's a reason — ask first.
2. **Watch the cost signal.** A normal build is a few dollars. If something's been "running" for a long time with nothing to show, stop it and flag it.
3. **When in doubt, halt.** Anything touching *real* customer data or sending *real* messages → confirm with Joaquin first.

**Slide 10 — When you're stuck → ping**
- Paperclip will message **Telegram** when it needs a human decision. Answer it.
- If you're blocked, drop it in the team Telegram. Don't fight it for an hour.
- Next step: each of you builds one small automation this week. I'll watch the first one with you.

---

## PART 2 — Call Script (timed)

### 0:00–0:03 · Open with the "why"
> "Up to now, if you needed an automation, you came to me and waited. After today, you won't have to. Paperclip is basically an AI agency you can brief directly. You describe what you want, it builds it, tests it, and ships it to GitHub. You don't write code — you describe and you review. That's the whole job."

Set expectations: *"By the end of this call each of you will have kicked off one real build."*

### 0:03–0:07 · The mental model (Slide 3)
Hammer one analogy and reuse it all call:
> "Treat it like emailing a dev agency. You're the client. A vague brief gets you a vague result. A clear brief gets you something you can ship. The skill you're learning today isn't technical — it's *briefing clearly* and *reviewing honestly*."

Reassure them: they cannot "break" anything by *trying*. The safety rails (caps, halts, pauses) exist precisely so they can experiment.

### 0:07–0:12 · Meet the agents (Slides 4)
Introduce only the two they drive:
- **Internal Planner** — "your thinking partner. Give it a messy idea, it gives you back a clean plan."
- **Test Data Generator** — "your safety net. Want to test an automation without using real customer data? Ask it for realistic fake data."

Mention the build crew exists (Engineer → QA → Reviewer → Release) but frame it as: *"these run themselves — you don't poke them. They're why a build comes back already tested and documented, not just thrown over the wall."*

### 0:12–0:22 · LIVE DEMO — Path B (build your own idea)
> Do this live. This is the heart of the call. Pick a tiny, real example everyone understands — e.g. "when a new lead comes in, send me a Telegram summary."

Narrate each step out loud:
1. Open the **Internal Planner**. Type the idea in one or two plain sentences.
2. Let it ask its clarifying questions — answer them like a normal conversation. *Point out: "see how it's pulling the spec out of me? That's the work I used to do in my head."*
3. Show the spec it produces. "This is now buildable."
4. Hand it to the build team. Show that it's now *in progress* — and that you can walk away; it doesn't need babysitting.
5. (If a previous build is ready) open **GitHub** and show what a finished result looks like.

Keep saying: *"Notice I'm not writing any code."*

### 0:22–0:28 · Path A — the interview shortcut (Slide 6)
> "Path B is for your own ideas. Path A is even easier — when it's a *customer's* automation, the workflow interview already wrote the spec for you."

Walk the flow at the whiteboard level: interview → spec → build team → GitHub → you review → iterate in chat. Emphasize the **iteration loop** (Slide 8): building is a conversation. Show how to ask for a change in plain language, and how to use the **Test Data Generator** to verify it before it touches anything real.

### 0:28–0:33 · The 3 rules (Slide 9)
Slow down here — this is the part that protects the business.
1. Don't un-pause what you didn't pause.
2. Watch the cost — normal is a few dollars; "running all night with nothing to show" is a red flag, stop it.
3. Real customer data or real outbound messages → halt and check with me first.
> "These aren't bureaucracy. We've already burned money twice on agents looping on themselves. The rails are why you *can* experiment freely."

### 0:33–0:38 · When stuck + assignment (Slide 10)
- Paperclip pings **Telegram** when it needs you. Answer those.
- Stuck > a few minutes? Post in the team chat. Don't grind.
- **Homework:** each of you ships one small automation this week. I'll sit with you on the first one. Anyone want to claim an idea right now?

### 0:38–0:40 · Q&A / buffer
Catch questions. End on: *"You don't need to be technical. You need to be clear. The system handles the rest."*

---

## PART 3 — Leave-Behind Cheat Sheet

> Print this / paste into Notion. This is what they'll actually refer back to.

### What is Paperclip?
An AI build team. You brief it in plain language; it plans, builds, tests, documents, and ships automations to GitHub. **You don't code — you describe and review.**

### The two agents you drive
| Agent | Use it when… | What you do |
|---|---|---|
| 🧭 **Internal Planner** | You have an idea but no clear spec | Describe the idea, answer its questions, get a clean buildable plan |
| 🧪 **Test Data Generator** | You want to test without real data | Ask for realistic sample data for your automation |

### Build it: two paths
**Path A — From a customer interview (spec already exists)**
1. Customer finishes the **workflow interview** → spec is created automatically
2. Build team builds + tests it → lands on **GitHub**
3. Review it → ask for changes **in the chat**
4. Need to test? → ask the **Test Data Generator** for sample data

**Path B — From your own idea (you create the spec)**
1. Open the **Internal Planner** → describe your idea
2. Answer its clarifying questions → it writes the spec
3. Hand the spec to the build team **in Paperclip**
4. Review on GitHub → iterate in chat → test with sample data

### How to brief well (the only real skill)
- **Be specific.** "Email subject should be `New lead: {name}`" > "make the email nicer."
- **One change at a time** when iterating. Small loops beat big rewrites.
- **Review honestly.** If it's wrong, say exactly what's wrong. The system can't read your mind, but it responds well to clear feedback.

### The 3 rules
1. ⛔ **Don't un-pause agents you didn't pause** — ask first.
2. 💰 **Watch the cost** — normal build = a few dollars. "Running for ages, nothing to show" = stop it + flag it.
3. 🚦 **Real customer data or real outbound messages?** → halt and confirm with Joaquin first.

### When you're stuck
- Paperclip messages you on **Telegram** when it needs a decision — answer it.
- Blocked more than a few minutes? Post in the **team Telegram**. Don't grind alone.

---

## Appendix — Under the hood (optional, only if someone asks "how does it actually work?")

You probably won't need this on the call, but it's here so you're not caught out:

- **The build pipeline:** CEO routes the job → CTO plans → Engineer builds → QA tests (loops back if it fails, max ~8 times) → Product Reviewer checks it solves the real problem (max ~3 loops) → Release ships to GitHub. Hard caps mean a stuck job halts and pings Joaquin instead of looping forever.
- **Why agents don't auto-run:** earlier versions had agents wake themselves on their own comments → infinite loops → burned money. Now agents only run when explicitly triggered. That's the safety model, not a bug.
- **Telegram bridge:** team chat messages can trigger the CEO agent; agent replies come back to Telegram. One message = one run = bounded cost.
- **Where things live:** config + pipeline in [tools/paperclip/](.), live system on the VPS. Joaquin owns the technical operation (orchestrator, bootstrap, credentials) — the team doesn't touch that layer.

*Reference docs for Joaquin: [pipeline.config.json](pipeline.config.json), [orchestrator.js](orchestrator.js), [NEXT_SESSION_PLAN.md](NEXT_SESSION_PLAN.md), [scripts/bootstrap-new-agents.sh](scripts/bootstrap-new-agents.sh).*
