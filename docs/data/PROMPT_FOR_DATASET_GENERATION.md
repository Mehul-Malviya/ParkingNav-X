# Reusable prompt: generating a realistic synthetic dataset for a campus system

Use this prompt (with an AI assistant that has code-execution ability)
whenever you need a "real-looking" dataset for a location where no public real-time
data feed exists.

---

**Prompt:**

> I'm building [PROJECT NAME], which currently runs on placeholder/mock data
> (see [list mock files / schema]). I need a synthetic dataset that is
> geographically and structurally realistic for [SPECIFIC REAL LOCATION],
> without me manually surveying it.
>
> 1. First, ground the entities in reality: look up (via web/maps search) the
>    actual named landmarks for this location — entry gates, buildings/blocks,
>    parking areas, road names — that a real user of this system would recognize.
>    Do not invent generic placeholder names if real ones are discoverable.
> 2. Tell me plainly which parts you could verify (real names, approximate
>    layout) versus which parts are necessarily fabricated because no public
>    data source exists (e.g. live occupancy, live congestion). Do not present
>    fabricated numbers as if they were measured.
> 3. Write a deterministic, seeded generator script (not hand-typed JSON) that
>    produces the dataset, matching my existing data schema exactly: [paste
>    schema/example]. The generator should encode believable domain patterns
>    (e.g. peak-hour congestion near classrooms/food courts, higher occupancy
>    near main entrances) rather than uniform random noise, and should support
>    generating multiple time-of-day snapshots.
> 4. Output the generated files in the same location/format the app already
>    reads from, plus a short README note stating the data is synthetic,
>    listing what's real-world-grounded vs. simulated, and how to regenerate
>    or later swap in real sensor data.
> 5. Run the project's existing test suite against the new dataset (or add a
>    smoke test) to confirm nothing breaks.

---

**Why this prompt works:** it forces the AI to (a) ground names in verifiable
reality instead of hallucinating, (b) admit which numbers can't be real, (c)
produce a reproducible generator instead of a one-off hand-written file, and
(d) tie the output back to your existing schema and tests so it's actually
usable, not just decorative.
