---
name: hotels
description: Answer questions about the hotels EverFlow works with, put a hotel on the website, or turn a guest's request into an offer, always from the hotel library and with the source of every fact. Use when the user asks what a hotel offers, wants a hotel shown on the site, has received new material from a hotel, or has a request such as "four friends, 4 to 7 February, good skiing".
---

# Hotels: the library, the partner pages, the offers

This repository is public. Three things never enter it: what a hotel pays us, who we talk to
there, and any hotel that has not agreed to be shown. They live outside:

| What | Where | Used for |
|---|---|---|
| The material as the hotels sent it | Drive, one folder per hotel | photos, brochures, guides |
| The library: that material as searchable text | outside this repo, path in `library.local.json` | every answer |
| The permission register | a CSV outside this repo, path in `library.local.json` | what may go on the site |
| Terms, contacts, state of each deal | the partner Sheet and the mail threads | offers, never the site |

## Always first

```
uv run --with pypdf python scripts/library.py status
```

If it lists documents that are new or changed, rebuild before answering:
`uv run --with pypdf python scripts/library.py build --apply`. If `library.local.json` is
missing, copy `library.example.json` and ask Juan for the four paths.

## A question about a hotel

1. `python scripts/library.py search <words> [--in <part of the folder or file name>]`.
   All words must stand on the same page. Try the German word too: many guides are bilingual.
2. Read the pages that were found, in the library file, before answering.
3. Answer with the document and the page for every fact.
4. End with what could not be searched for that hotel (`status` lists scans and files that
   were left out). "Not found" is an answer; a guess is not. A price, a payment term or a
   bank detail that turns up in a document is not repeated in an answer.

## A partner on the website

1. `python scripts/library.py permissions`. Go on only if the partner's line says `site: yes`.
   `never` and `no` stop the work: tell Juan what is missing and offer to draft the request.
   The register records the basis (the partner's words in writing, or Juan's decision with its
   date); a decision that is not in the register is not a basis. A partner the register shows
   without its name (the chalets in Megève) is never named in the repository.
2. Write the facts as claim, quote, document and page into a facts file next to the library
   (`facts/<partner>.facts.json`) and run `python scripts/library.py verify <file>`. Every fact
   on the page must pass, or stand on the partner's official website, which the page links.
   Facts that change with the season, and prices, do not go on the page.
3. Add the partner to `content/partners.json`: `register` (its exact name in the register),
   `place` (a slug in `content/destinations.json`; add the place if it is new), our words for
   `card`, `lead`, `facts`, `why`, the partner's own programme under `arranges`, `provider`,
   `credit` exactly as the register writes it, and `photos`.
4. Photos only when the register says `photos: yes`:
   `uv run --with pillow python scripts/photos.py stay <partner> <name> "<original under the material folder>"`
   (a photo inside a zip: `"<zip>::<member>"`). Four to eight photos: outside, a room, food or
   spa, the surroundings. The script refuses what the register does not allow and writes WebP
   files without metadata into `assets/img/stays/<partner>/`; every photo is shown with
   "© <credit>". The Impressum lists the credit by itself: change `impressum_stand` in
   `content/site.json`.
5. No downloads of partner documents unless the register says `brochure: yes`.
6. `python scripts/build.py`, `python scripts/check.py`, a look at the pages in a browser at
   full and at phone width (`python -m http.server`), then a pull request. One partner, one
   pull request. Add the partner to `docs/HOTEL_MATERIAL.md`.

## An offer for a guest

Two steps.

1. Shortlist two or three hotels from the library and the Sheet, with the reason for each and
   its source. Draft the availability and rate request to each hotel. Juan sends it.
2. When the hotels have answered, draft the proposal for the guest: the hotel's quoted rate
   with its validity date, what is included, what the guest has to decide. The guest books
   through us; the contract is with the hotel.

An offer holds what the hotel quoted for those dates and what it includes; contacts at the
hotel and the terms of agreements stay internal. A rate comes from the hotel's answer for
those dates, never from a brochure or from memory. A hotel whose agreement has ended is not
offered.

## Never

- Send a mail, publish, merge, or change the partner Sheet. Drafts and pull requests only.
- Read folders outside the ones listed in `library.local.json`.
- Put the name or e-mail address of a contact at a hotel, a commission, a rate, a term of an
  agreement, a Drive path or a local path into a file of this repository, a commit message
  or a pull request.
- Invent a fact, a contact or a credit line. Ask.
