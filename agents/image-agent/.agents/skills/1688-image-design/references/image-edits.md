# Edit Workflow

Use this short workflow for all edits; use [edit-patterns.md](edit-patterns.md) only for the selected operation. The slots below support prompt construction inside the existing generation workflow, not a new API or mandatory extra model call.

## 1. Select the operation

| Requested change | Pattern section |
|---|---|
| Color, finish or texture | Attribute |
| Literal replacement or text removal | Text |
| Translate commerce graphics into another language | [Ecommerce localization](image-translation.md); use its full workflow |
| Move, resize, reshape, attach or change interaction | Structure and placement |
| Rotate the object or change the camera | Viewpoint |
| Background, lighting or visual style | Environment and style |
| Remove an object or insert from another image | Removal and compositing |

Multiple requested changes may use multiple patterns in one call. Select by user intent, not product category. A short instruction may require spatial work; a long instruction does not automatically require a complex model mode.

Localization uses its specialized text-region map instead of loading all edit patterns.

## 2. Fill a small edit specification

Inspect the actual sources. Identify each input's role and order. Fill four items using the selected pattern's questions: **target**, **desired end state**, **protected properties**, **necessary dependent changes**. Use concrete observations and the user's requirements, not an inventory of the whole image. Keep unknown facts explicitly unknown. Do not infer hidden ports, unreadable text or measured dimensions as product facts.

The user's requested change overrides the original state of that property. Preserve unrelated identity and content; allow necessary changes to projection, contact, shadows or layout. An attribute donor supplies only that attribute. An explicit concept redesign can change designated structure but is not proof of existing inventory. If requirements materially conflict, resolve the conflict rather than silently changing the target.

For a clear request, answer the pattern questions internally and proceed. Ask only when missing evidence or conflicting cues prevent a faithful result. If a necessary source is inaccessible, report that limitation instead of claiming visual grounding.

## Canvas overlay marks

Distinguish marks printed, embossed, woven or engraved on the product from flat canvas overlays. Preserve existing marks outside the requested edit by default. Follow explicit keep/remove instructions without asking again. Ask only when the requested change creates a material ambiguity about a mark; do not turn each visible logo into a mandatory questionnaire.

A retained canvas mark remains a canvas element: preserve its artwork, relative position, scale and count. Do not duplicate it per product, attach it to the product surface or add perspective/shadows. If a verified destination requirement conflicts with an explicit preservation request, explain that conflict without silently deleting the mark or claiming upload compliance.

## 3. Write and check the actual prompt

Fill the chosen sentence pattern, then place the sentences in the existing prompt labels. Carry every decisive slot value into the final `prompt`; do not compress a resolved relationship back into vague wording. Omit irrelevant slots and placeholders. Do not add template example facts to the current product. Use coordinates only when useful and grounded in the actual source dimensions and coordinate system; retain semantic landmarks and account for cropping/resizing.

Apply the main Skill's coverage, consistency, binding and fidelity checks. In particular, test each preservation clause against the desired end state: replace a conflicting freeze of pose, silhouette or shadows with protection of the underlying identity and permission for the required change. Preserve reference features used to locate the target unless changing them is requested. Keep execution-critical instructions in `prompt` even when supported auxiliary fields repeat them.

For prompt-only review use [prompt-review.md](prompt-review.md); otherwise execute through the Codex adapter in generation-runtime.md without adding an approval step.

## 4. Inspect the result against the same specification

Check the requested change first, then the protected properties and dependent changes. Use the operation's acceptance cue. Compare to original sources and target relations, not merely the latest generated image. A brief whole-image check catches collateral changes. Inspect actual text and file properties when required. If the result or a detail cannot be inspected, label it unverified rather than claiming success. When a mark was confirmed to keep, verify it in every output: present, exactly one, at the source's relative position and scale, with unchanged artwork and opacity.

For a failure, identify the observed discrepancy. Fix source interpretation, missing evidence or conflicting prompt clauses before retrying; for execution error, make one focused correction. Re-state critical invariants. Use the latest output only if identity and protected content remain sound; otherwise return to the original. Preserve source roles and order. After one targeted repair fails, explain the limitation unless more iteration is authorized. Report concise verified status in the user's language, keeping diagnostic records internal unless requested.
