# Visual release acceptance

Passing code tests or Pages build alone never accepts a storefront release.

For every material visual change:

1. Archive the previous catalog and media references in Git before modifying them. Never delete additional products or assets without an explicit commercial decision.
2. Capture the public baseline before editing. Review relevant history as a separate reference; it is not permission to restore unsupported claims or checkout.
3. Capture home, all three categories, real product preview, a sourcing page, and all five policy/contact pages at 390, 768 and 1440 CSS pixels. Include focused before/after captures of altered icons, navigation, featured images and gallery.
4. Use an isolated browser with loaded fonts/images. Inspect actual screenshots for distortion, missing content, poor alignment, text readability, unwanted crops and overlaps. Geometry checks assist this review; they do not replace it.
5. Click category navigation, each gallery image, the original video, return-to-image controls and product accordions. Check essential link responses. No financial submission is part of visual QA.
6. Reject any severe visible defect, basic broken link, or unsupported commercial claim. Keep both payment gates disabled while commercial acceptance remains incomplete.
7. Publish only after local visual review passes; repeat screenshots and interactions on the public domain. Record code revision, browser widths, screenshot hashes, observed results and remaining limitations in a receipt.

Run the browser capture tool with a separately installed Playwright runtime:

```powershell
python audits/visual_gate.py --runtime <runtime-directory> --base <preview-or-live-url> --output <evidence-directory> --interactions
```

`browser-receipt.json` deliberately records that screenshot review is required. A zero-overflow metric alone cannot accept a release. Visual approval is limited to the tested Chromium widths and listed pages, not every device or browser.

The original three-product catalog, nine JPGs and three video references are preserved by tag `archive/verveliving-original-20261103`, pointing at `403f0e596fb20e8c955ef778b30c169e9f73f7cd`. Excluded medical media remain in the archive, not the active product catalog. FurOff's three original photos retain their original bytes. Restoration of the original FurOff video follows the owner's explicit instruction on 3 November 2026; it is not represented as an independently verified transfer of supplier copyright.
