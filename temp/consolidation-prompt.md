# Consolidation prompt (one-time harvest)

Paste this into an environment where the AI can read your architecture markdown files,
and point it at those files. It produces ONE consolidated map file meant to **outlive
both this prompt and the scattered source files**. Run it once, commit the output, then
bin this prompt and (if you wish) the sources.

Because this is the only moment all your scattered findings exist together, the run must
*harvest* everything the downstream skill will ever need -- not just draw a diagram. It
must capture, into the committed file: the edges, the evidence behind each solid edge
(provenance), an endpoint->service ownership table, and the weak spots (contradictions /
low-confidence / unclear). After this run, none of that is cheaply recoverable.

---

Read the architecture markdown files I am pointing you at. Produce ONE consolidated
markdown file with the sections below. The diagram is only the first section; the later
sections must be committed too, because the source files will be deleted.

## Arrow convention (this is the law -- follow it on every edge, never mix conventions)

    A --> B means "A depends on B". That is, A calls B and needs B to work.

Arrows pointing OUT of a service are what it depends on (what can break it); arrows
pointing IN are what depends on it (what it breaks if it goes down).

## Rules -- follow exactly

1. **Solid arrow (`-->`) requires provenance.** Use solid only for an edge a source file
   backs with a *named, real observation* (e.g. "Datadog showed checkout-api calling
   payment-gateway in live traffic"). For every solid edge you MUST record, in the
   Provenance table: the edge, the source file, and the observation. If a source merely
   asserts a dependency without naming an observation, it is NOT solid -- make it dashed.
2. **Dashed arrow (`-.->`)** for any edge only inferred (e.g. from repo config),
   unobserved, or uncertain. Dashed means "believed, not confirmed".
3. Datastores are nodes written like `db[(name)]`.
4. Normalize service names: lowercase, hyphenated, one canonical name per service. Record
   any rename in Contradictions.
5. Put the arrow-convention sentence as a `%%` comment at the top of the diagram.
6. Stamp today's date in the map header as the snapshot date.

## Worked example (solid vs dashed)

Datadog observed checkout-api calling payment-gateway in live traffic -> solid. The only
hint that checkout-api uses user-auth came from a config file that may be dead code ->
dashed:

    flowchart TD
        %% A --> B means "A depends on B" (A calls B and needs it to work)
        checkout-api --> payment-gateway
        checkout-api -.-> user-auth

## Output format -- produce EXACTLY this committed file

    # Architecture map -- snapshot YYYY-MM-DD
    %% A --> B means "A depends on B" (A calls B and needs it to work).
    %% Solid (-->) = observed/confirmed at snapshot date. Dashed (-.->) = inferred, unconfirmed.

    ## Diagram

    ```mermaid
    flowchart TD
        %% A --> B means "A depends on B"
        ...the single consolidated flowchart...
    ```

    ## Provenance (every SOLID edge -- its source file and the observation)
    | edge | source file | observation that justifies "solid" |
    |------|-------------|-------------------------------------|
    | checkout-api --> payment-gateway | investigation-3.md | Datadog live traffic, 2026-06 |

    ## Endpoint ownership (endpoint -> owning service)
    | endpoint | owning service | source file |
    |----------|----------------|-------------|
    | POST /checkout | checkout-api | investigation-1.md |

    ## Low-confidence edges (every DASHED edge, one line each on why)
    - checkout-api -.-> user-auth -- only a config reference, possibly dead code (investigation-2.md)

    ## Contradictions (where two files disagree about an edge or a name)
    - investigation-1.md says "orders-svc"; investigation-4.md says "order-service" -> normalized to order-svc

    ## Unclear (anything you could not place with confidence)
    - a "reporting job" with no caller/callee identified (investigation-5.md)

## Do not invent

Do not invent edges to make the graph look complete. If a connection is not supported by
something in my files, leave it out, or mark it dashed and list it under Unclear.
Reformatting and *harvesting* what I already gathered is the job. Filling gaps with
guesses is not.

---

## What to do with the output

Commit the whole file (not just the diagram) to git. The Provenance, Low-confidence,
Contradictions, and Unclear sections are the point -- they are your only surviving record
of where the map is weak once the sources are gone. Skim them, settle the contradictions
that matter, leave the rest dashed, and confirm those lazily as real incidents touch each
service. Then bin this prompt.
