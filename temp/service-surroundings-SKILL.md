---
name: service-surroundings
description: Look up how a service fits into the wider system -- its dependencies, its consumers, its datastore, and how big its blast radius is. Use this whenever a task involves a specific service or endpoint and needs to know what surrounds it, what it depends on, what depends on it, or what could be the cause or the impact of an incident. Use it even when the request does not say "architecture" out loud, for example "why is checkout failing", "what breaks if we take orders down", "what does this endpoint touch". Always consult this skill before reasoning about service relationships from memory, because the consolidated map is more reliable than guessing.
allowed-tools: Read Grep Glob
---

# Service surroundings

Returns the placement of a service in the system from a single consolidated map, so a task
starts from documented architecture instead of re-deriving it under pressure.

## The arrow convention (the law)

The map uses one fixed rule, stated at the top of the map file. Never reinterpret it:

    A --> B means "A depends on B". A calls B and needs B to work.

For any service:

- Arrows pointing OUT (its dependencies) are "what can break me". Look here for the cause.
- Arrows pointing IN (its consumers) are "what I break". Warn these about the blast radius.
- A solid arrow (-->) was confirmed by a named observation **at the map's snapshot date**.
- A dashed arrow (-.->) is inferred or unverified -- a lead, not a fact.

## The source of truth

One consolidated markdown file holds the whole map. **Set its path here once:**

    MAP_PATH = docs/architecture-map.md   <-- replace this placeholder

If MAP_PATH is still the literal placeholder above, or the file does not exist, STOP and
say the skill is not configured -- do not guess and do not fall back to memory. That is a
configuration error, and it is different from "service not found" (see below).

Read that file. It contains the diagram plus committed sections: Provenance, Endpoint
ownership, Low-confidence edges, Contradictions, Unclear. Use them. Do not read any older
scattered findings files; they were harvested into this one and may contradict it. The
tool that built this map no longer exists, so this file is the single durable record --
treat it accordingly.

## What this skill does (keep it this simple)

Given a service name or an endpoint:

1. If given an endpoint, resolve it via the **Endpoint ownership** table in the map. If the
   endpoint is not in that table, say so -- do not infer an owner.
2. Read the consolidated map file.
3. Find every edge touching that service.
4. Return its surroundings:
   - depends_on: the services it points to (what can break it)
   - consumed_by: the services that point to it (what it breaks)
   - datastores: any db nodes it connects to
5. For every edge, state whether it is solid (confirmed as of the snapshot date) or dashed
   (unverified). For solid edges, the Provenance table names the source and observation; cite
   it if the user is acting on it.

That is the whole job. No merging, no re-gathering, no live freshness checks. The map is a
snapshot; freshness is handled by humans confirming dashed edges lazily over time.

## The one rule that matters most

Always carry the solid-or-dashed status -- and the snapshot date -- through to the answer.
Never present a dashed, unverified edge as a confirmed fact, and never present a solid edge
as live truth without noting it was confirmed *as of the snapshot date*. During an incident
an engineer must be able to tell "we saw this dependency, on <date>" from "we think this
dependency exists". Collapsing that distinction is the failure this skill exists to avoid.

## Example answer shape

For a service called checkout-api, a reply should read roughly:

    checkout-api  (map snapshot: 2026-06-17)

    What can break it (its dependencies):
      - payment-gateway   [confirmed as of 2026-06-17]
      - inventory-svc     [confirmed as of 2026-06-17]
      - user-auth         [UNVERIFIED, inferred only]

    What it breaks (its consumers):
      - web-frontend      [confirmed as of 2026-06-17]
      - mobile-bff        [confirmed as of 2026-06-17]

    Datastore:
      - checkout_db

    Note: the user-auth dependency is unverified. Confirm against Datadog before
    treating it as a cause. Confirmed edges were last observed at the snapshot date.

## When the map is missing a service

If the requested service is not in the map, say so plainly. Do not invent its surroundings.
A missing entry is a real signal that the map needs extending -- a separate, deliberate
step, not something to paper over by guessing. (This is distinct from MAP_PATH being
unconfigured, above.)

## Extending the map by hand

The generator is gone, so edits are manual. Any edge you add by hand defaults to **dashed**
unless you personally observed it in a live source, in which case make it solid and add a
row to the Provenance table with the source and observation. Bump the snapshot date when
you do. This is what keeps the map trustworthy after the tool that built it is gone.

## Platform notes

- Place this file at `.claude/skills/service-surroundings/SKILL.md` for a project skill
  shared via git, or `~/.claude/skills/service-surroundings/SKILL.md` for a personal one.
  Set MAP_PATH in "The source of truth" section above.
- `allowed-tools` is read-only on purpose: this skill only reads the map, so it never needs
  write or execute access. `allowed-tools` is honored by the Claude Code CLI directly;
  through the Agent SDK it has no effect, so there you control access with the main allowed
  tools option instead.
- Keep this skill single-file. It is small, and splitting into reference files is only worth
  it once a SKILL.md grows unwieldy.
