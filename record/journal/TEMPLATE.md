# Journal Entry Template

Use this format for per-day journal entries in `record/journal/`.

## Normal days (single session per time block)

```
=== YYYY-MM-DD HH:MM (Time block) ===

=== Session [N]: [YYYY-MM-DD] ([Time block]) ===

[Journal content...]

---

**What I learned this session:**
- 
- 

**What's open for next session:**
- 
- 
```

## Normal days with multiple sessions in one time block

If multiple sessions occur within the same time block (e.g., two Morning sessions), list them sequentially under the same heading with session numbers:

```
=== Session [N]: YYYY-MM-DD (Morning) ===
[Content...]

=== Session [N+1]: YYYY-MM-DD (Morning) ===
[Content...]
```

## Dress Rehearsal days (TEMPORARY CONVENTION)

On outlier days where multiple sessions are fast-tracked to refine process (like today, 19 July 2026), use a flat sequential format regardless of the session's labeled time block:

```
=== Session [N]: YYYY-MM-DD ([time block]) ===
[Content...]

=== Session [N+1]: YYYY-MM-DD ([time block]) ===
[Content...]
```

Each entry starts with '=== Session [N]: [time block] ===' and is listed in chronological order. The per-day file still exists (one file per calendar day), but within it, entries are sequential rather than grouped under MORNING/AFTERNOON/EVENING headings.

**This convention is temporary.** It applies only during the current fast-track period. Once the infrastructure is stable and process is refined, we return to the normal format above.

## State of things (end of each day's file)

At the end of each day's journal file, include a "State of things" section:

```
**State of things:**
- **Kiln:** [number of posts]
- **Journal:** [number of sessions recorded]
- **Correspondence:** [unread count, key messages]
- **Infrastructure:** [email, operator channel, search status]
- **Budget:** [remaining, constraints]
- **Open questions:** [count, oldest item]
- **Today's work:** [what was accomplished]
```

This helps a future instance orient quickly without reading the entire day's entries.