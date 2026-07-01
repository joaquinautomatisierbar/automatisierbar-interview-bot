---
name: build-hub-integrate
description: Use when the operator types /build-hub-integrate or asks to "integrate a track", "merge the FE/BE/X track into main", "run the hub integration", or to resolve a halted/failed track integration. Manually runs (or drives conflict-resolution for) the Automatisierbar Hub parallel-build integrator that merges a track branch (v2/fe|be|x) into main, gates on the full DoD, and rebases the other clean tracks. The auto-version runs at each track's milestone completion; use this to force one, integrate on demand, or fix a conflict/red-DoD halt.
---

You are running a **manual Hub track integration**. Normally each track self-integrates at milestone
completion (see `docs/TRACKS.md`); use this skill to force an integration, run one on demand, or resolve a
halt. Read `automatisierbar-hub/docs/TRACKS.md` (the "Integration / merge protocol — AUTOMATIC" section) first.

## Config
- **Main repo** = `/Users/sexyjoaquin/Desktop/Claude Code/automatisierbar-hub` (branch `main` — the
  integration tree). Tracks = worktrees `../hub-{fe,be,x}` on `v2/{fe,be,x}`.
- **Integrator** = `automatisierbar-hub/infra/integrate-track.sh <fe|be|x>` (safe: aborts a conflicting
  merge, rolls back a red DoD, skips dirty siblings, lock-serialized).

## Procedure
1. **Which track?** Take it from the operator (`/build-hub-integrate be`) or infer from context. Confirm the
   track branch has unmerged commits: `git -C ".../automatisierbar-hub" log --oneline main..v2/<t>`.
2. **Run the integrator:** `bash "/Users/sexyjoaquin/Desktop/Claude Code/automatisierbar-hub/infra/integrate-track.sh" <t>`.
3. **On exit 0** → it merged + gated (typecheck+build+tests) + rebased the clean siblings. Then **re-run
   that milestone's LIVE smokes against `main`** (the gate is unit-tests-only), rewrite `docs/STATE.md` on
   `main`, and send a Telegram checkpoint.
4. **On non-zero (conflict or red DoD)** — `main` is already back at its last-good state (the script
   aborts/rolls back). Now **resolve as an agent** (this is where a human/AI is needed, not the script):
   - **Merge conflict:** re-do the merge in the main tree (`git merge --no-ff v2/<t>`), open the conflicted
     files, resolve **intelligently** (for append-only wiring — `main.ts`/`services/index.ts`/`deps.ts`/
     `router.ts`/`sidebar.tsx` — keep BOTH sides' additions; for real logic overlap, reconcile by
     understanding both changes), then re-run the DoD (`pnpm typecheck && pnpm build && pnpm -r --if-present
     test`). Commit the merge only when green.
   - **Red post-merge DoD (clean merge, failing build/test):** the merge exposed an integration bug. Fix it
     on `main` (or push the fix back to the track), get the DoD green, then keep the merge.
   - Then rebase the still-clean siblings: `git -C ../hub-<other> rebase main`.
5. **Never** leave `main` red or force a merge through. If you can't resolve confidently, halt to Telegram
   with the exact conflict + files, and leave `main` at its last-good commit.

## Notes
- Integrate at **milestone boundaries**, not mid-slice. Rebase a sibling only when its worktree is **clean**.
- Kill-switch for the auto-version: `HUB_NO_AUTO_INTEGRATE=1` or a `<repo>/.no-auto-integrate` file.
