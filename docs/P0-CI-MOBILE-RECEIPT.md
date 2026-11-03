# Targeted CI and mobile category fix — 2026-11-03

Local verification only. HEAD: `73f033307e550a0bef661f774b444c5f12f68a1e`.
The supplied remote commit `fb26ed3c1d19581e7ae5ef23f4854fa08da8f725` is not
available in this local object database; remote tree equality was not verified.
No pull, reset, staging, commit, push or deployment was performed. The sandbox
grants read access to `.git`; changes are left for the manager to commit.

## Changes

- `scripts/build_store.py`: read CSS/JS once with universal newline normalization;
  hash their normalized UTF-8 bytes and publish those same contents.
- `tests/test_build_store.py`: build separate temporary LF and CRLF source roots;
  compare every generated file including the receipt byte for byte, verify emitted
  CSS/JS bytes, full asset hashes and version queries in every generated HTML page.
- `static/store.css`: category images use `height:auto` and 4:3 desktop boxes;
  mobile uses `clamp(210px,58vw,240px)` and `object-fit:contain` for full products.
- `scripts/visual_qa.cjs`: reject image decode errors; assert three mobile category
  cards below 420px, photos below 260px, and 13 product images. Add category
  screenshots and optional `VISUAL_QA_OUTPUT` to keep evidence outside the repo.
- Regenerated all publishable output: 27 HTML pages, `assets/store.css` and
  `build-receipt.json` changed. Other generated files remain byte-identical.

## Verification

- Python 3.12.14: `-m unittest discover -s tests -v` — **25 passed**, including
  `test_publishable_files_equal_generator` and LF/CRLF equivalence.
- Node v24.19.0: `--test workers/order-gateway/test/*.test.mjs tests/*.test.mjs`
  — **23 passed**. Payment tests use mocks, not provider transactions.
- `node --check`: `static/store.js`, `workers/order-gateway/src/index.mjs`,
  `scripts/visual_qa.cjs` — passed. `git diff --check` — passed.
- `node scripts/visual_qa.cjs . after`: Chrome 156.0.8078.74, **22 local route /
  viewport checks passed**, no missing resources, JS errors, decode failures or
  horizontal overflow. All 13 homepage product images loaded.
- At width 390px: category photo/image heights **226.1875px** each; full card
  heights **340.9375 / 370.046875 / 340.9375px**.
- Inspected actual Chrome screenshots of mobile homepage and mobile/desktop
  categories: compact tiles, full cable organizer and FurOff images visible.
- Published LF stylesheet SHA-256:
  `0bc6caa1f08b2f80ce590da85477239f0d70355625e4cf9566d53a057946ea30`.
- Published LF script SHA-256:
  `92842260ea0a5d14a643768f12931c653fe7565dbdf7509fde371872396b3291`.

Evidence directory (outside repository):
`C:\Users\askgs\AppData\Local\Temp\verveliving-p0-ci-mobile-20261103`.
Contains `after-browser.json`, `after-home-390.png`,
`after-categories-390.png`, `after-categories-1440.png` and other QA screenshots.
Existing untracked media in `receipts/visual-recovery` was left untouched.

Catalog, pricing, stock, source images/videos, settings, Worker, D1, accounts and
secrets were not changed. Checkout remains disabled. Remaining: manager commit
and connected GitHub CI rerun; no hosted CI or production success is claimed.
