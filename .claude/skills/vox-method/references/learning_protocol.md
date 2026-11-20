# Learning protocol: how this skill keeps improving

The knowledge base is meant to grow. Each new video studied, each film we make and each owner correction should leave
it sharper. Reading alone doesn't count: a lesson has to be extracted, labelled and written into the right file.

## Three kinds of knowledge, always kept apart

| Label | Meaning | Allowed sources | Example |
|---|---|---|---|
| **[V] Verified observation** | Something a source states or shows: a transcript, an interview with the maker, credits, a companion article, frames we actually viewed | Cited URL or file, with what was accessed | "[V] The producer says the team posts sources in the description (interview URL)" |
| **[I] Informed interpretation** | A production inference reasoned from verified material, and not observed directly | Must say what it is inferred from | "[I] The transcript's question-per-chapter pattern suggests chapters are built as answers to sub-questions" |
| **[O] Our original technique** | A method we developed for our channels, inspired by but not copying the studied craft | Our own reasoning, tested in our films | "[O] The waterline device: one rising line repeated across chapter cards" |

Never promote [I] to [V] without new evidence. Never write a description of a frame that wasn't seen. If the evidence
is a transcript, describe what the words do, not what the picture did.

## When a new Vox video is analysed

1. Gather evidence honestly: a transcript or captions if accessible, the companion article, the description and
   chapters, interviews about the piece. Record in `evidence_basis` exactly what was and wasn't accessed.
2. Copy `assets/templates/case_study.md` to `case_studies/<slug>.md` and fill all twelve sections. Section 12 must
   give concrete, subject-independent moves phrased as our own equivalents.
3. Run `python3 scripts/case_study_check.py case_studies/` (it checks structure and honesty and rebuilds INDEX.md).
4. **Extract, don't pile up.** For each candidate lesson, ask:
   - Is it already in a reference file? Then add the case study as further support, and nothing else.
   - Does it contradict a reference file? Write the contradiction down in the learning log and resolve it with
     evidence (it may be a difference of era, series or subject, which is itself a lesson).
   - Is it new? Add it to the right reference file, in the right section, with its label and a link to the case
     study.
5. Append one entry to `references/learning_log.md`: date, what was studied, lessons added, files changed, and
   contradictions found.

## When one of our films is reviewed or corrected

- Each owner correction becomes a BRAIN_LOG patch (CreatorForge) and, if it is about craft, a learning-log entry.
  An entry names the rule that would have prevented the mistake and the file it now lives in.
- After each finished film, record what worked as an [O] technique, with the film and the evidence that it worked
  (owner reaction, retention, QC score). Record what failed as a rule.

## Learning from our own published films

Once a film is published, pull its numbers from the owner's connected analytics: the Windsor.ai YouTube connector, or
vidIQ channel analytics, read-only. Fetch the retention curve (`audience_retention`), the average view percentage
and the traffic sources. Record in the learning log:
- where viewers left (map each drop to its scene id in the blueprint);
- where they rewatched;
- how the first 30 s held.

A rule earns [O] status only when the numbers back it.

## Pruning

Every ten case studies, reread the reference files. Merge duplicates, cut rules nobody has used, and move anything
over about 300 lines into a sub-file with a table of contents. A short file that gets read beats a long one that
doesn't.
