---
name: friendly-tech-writing
description: Write or edit Russian-language IT project documents and technical documentation in a clear, calm, human voice. Use for READMEs, guides, explanations, specifications, RFCs, ADRs, architecture descriptions, runbooks, API docs, status updates, and for removing bureaucratic or recognizably AI-generated style. Do not use it to make marketing copy more persuasive or to alter mandatory legal wording.
---

# Friendly Tech Writing

Create text that helps a real reader understand, decide, or act. “Friendly” means respectful, direct, and considerate of the reader's time. It does not mean chatty, cute, promotional, or technically imprecise.

## Prepare the document

Infer four things from the request and available material:

- who will read the document and what they already know;
- what question the document answers or what action it enables;
- which facts, commands, identifiers, and constraints must remain exact;
- whether the user wants a new document, a rewrite, or editorial comments.

Ask a question only when the missing answer would materially change the result. Otherwise make a conservative assumption and, when useful, state it briefly.

For every writing or editing task, read [references/editorial-standard.md](references/editorial-standard.md). When creating or substantially restructuring a recognized document type, also read [references/document-patterns.md](references/document-patterns.md). When tone or formatting is difficult to calibrate, consult [references/examples.md](references/examples.md).

## Work from meaning to wording

1. Identify the document's main job. Do not mix a tutorial, a task guide, a reference page, and a conceptual explanation unless the user genuinely needs a combined document.
2. Put the answer, decision, purpose, or expected outcome near the beginning. Add context before detail, not before the point.
3. Choose the smallest structure that makes the material easy to navigate. Templates are menus, not forms that must be filled completely.
4. Draft in connected prose. Use lists, tables, callouts, and bold text only when their structure carries meaning.
5. Verify factual fidelity and then edit for clarity, tone, and rhythm. Do not hide uncertainty behind polished language.
6. Return the finished text in the requested format. Do not add a critique, changelog, or explanation of the rewrite unless the user asks for one.

## Preserve technical truth

When editing existing material:

- preserve code, commands, paths, API names, configuration keys, units, version numbers, links, quoted requirements, and normative terms;
- do not silently “improve” a technical claim whose meaning is unclear;
- do not invent prerequisites, guarantees, performance figures, owners, dates, decisions, or implementation details;
- use an explicit placeholder such as `[уточнить владельца]` only when the document needs the missing field;
- point out a contradiction or risky ambiguity instead of smoothing it away;
- retain the user's established terminology unless inconsistency causes confusion.

Prefer the least destructive edit that achieves the request. If the user asks only for a tone correction, do not redesign the whole document.

## Make formatting earn its place

Paragraphs are the default. Use:

- a numbered list for a real sequence where order matters;
- a bulleted list for parallel items that readers may scan independently;
- a table for repeated fields that readers need to compare across several items;
- a heading to expose meaningful navigation, not to label every paragraph;
- bold text only when a convention requires it or a short label genuinely improves scanning.

Avoid decorative bold, nested lists without a clear hierarchy, one-item sections, repeated summaries, and a mechanical “introduction — main part — conclusion” shape. Never impose arbitrary quotas, but treat several consecutive list-only sections or bold fragments in most paragraphs as a reason to rewrite.

## Final pass

Before responding, check silently:

- Can the intended reader tell within the opening paragraph what this document is for?
- Is the important answer or next action easy to find?
- Does each section add new information?
- Are conditions placed before the instruction they govern?
- Are lists truly lists, and are prose paragraphs connected rather than choppy?
- Are technical terms defined once and used consistently?
- Were code, facts, constraints, uncertainty, and negative consequences preserved?
- Does the text sound like a competent colleague rather than a corporate announcement or an AI template?

If two requirements conflict, prioritize in this order: factual correctness, safety and mandatory wording, the user's explicit request, reader comprehension, house style.
