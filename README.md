# My Space

This repository builds [famer.me](https://famer.me/) with Hugo 0.166.0 and PaperMod. PaperMod is an HTTPS Git submodule pinned to the commit recorded in this repository. Node.js, pnpm, Hexo, and Pandoc are no longer part of the build.

## Local use

Install Hugo 0.166.0 or later, then initialize the theme and start the preview server:

```sh
git submodule update --init --recursive
hugo server
```

Use `hugo server --buildDrafts` to preview drafts. Normal previews and production builds exclude them. Create a post with `hugo new content posts/my-post.md`, then set `draft: false` when it is ready to publish.

Build and check the production site with the same commands used by CI:

```sh
hugo --environment production --minify --panicOnWarning
python3 scripts/check_site.py
```

The checker follows local page links, fragment links, and asset references throughout `public/`. Unresolved Hugo `ref` and `relref` links and build warnings also fail CI.

## Content and rendering

Articles and drafts live in `content/posts/`. Existing articles have explicit `url` values that preserve their original date-based addresses, including case and Unicode characters. Keep those values when editing titles or moving files. Dates use the Asia/Shanghai timezone. Old archive URLs redirect to the unified archive.

The two legacy Reactive Stream tag URLs redirect to `/tags/reactive-streams/`. This keeps the aliases and canonical page from colliding on case-insensitive filesystems.

Images live in `static/images/` and are referenced as `/images/filename.png`. Use Hugo links such as `[another article]({{< relref "/posts/another-article.md" >}})` instead of hard-coded article dates. Private working material in `materials/` remains ignored and is not published.

Mathematics uses Hugo's native `transform.ToMath` through a Goldmark passthrough render hook. Write inline expressions as `\(O(n)\)` and display expressions between `\[` and `\]` or `$$` delimiters. The generated MathML needs no client-side math library or stylesheet. A single dollar sign remains ordinary text, so prices and code examples are not mistaken for formulas. Invalid mathematical markup fails the build. See [Hugo's native math documentation](https://gohugo.io/functions/transform/tomath/).

Mermaid uses [Hugo's documented code-block render hook](https://gohugo.io/content-management/diagrams/): use a fenced block with the `mermaid` language. Hugo does not itself render Mermaid diagrams. A local, pinned Mermaid 12.0.0 distribution renders them in the browser with strict security settings. The script loads only on diagram pages; the source remains available below each diagram. The vendored distribution and upstream MIT license are under `assets/js/diagrams/vendor/`; its SHA-256 is `28fca7ae6ebc7ed7bb63bde63136a74bfef14f296a57e403657eeb8b32836073`.

The local PaperMod overrides in `layouts/baseof.html`, `layouts/rss.xml`, and `layouts/_partials/templates/opengraph.html` use Hugo's current locale/direction APIs. The base template also includes the per-page Mermaid flag in the footer cache key. Review these overrides when updating the theme.

## Analytics and comments

Production pages use the existing Google Analytics property `G-1RGPQ0EFYL`. Normal `hugo server` previews do not include analytics or comments.

Giscus stores new comments in this repository's **Announcements** discussion category. It uses strict pathname mapping; old Utterances comments are not migrated. Repository and category IDs are configured in `hugo.yaml`. GitHub Discussions must stay enabled, and the Giscus GitHub App must retain access to this repository. The comment theme follows PaperMod's light/dark toggle. Visitors sign in with GitHub to comment.

## GitHub Pages

The repository's workflow is `.github/workflows/deploy.yml`. Pull requests build and check the site without deploying. Pushes to `master`, or a manual workflow run on `master`, build once and publish the resulting artifact to `gh-pages`.

Hugo and all referenced GitHub Actions are pinned. The workflow verifies the official Hugo release checksum before running it. It uses the existing `HEXO_DEPLOY_PRI` SSH deploy-key secret because pushes made with `GITHUB_TOKEN` do not trigger branch-based GitHub Pages builds. That secret's historical name does not require Hexo.

Keep GitHub Pages configured to publish the root of `gh-pages`, with HTTPS and the custom domain `famer.me`. `static/CNAME` and `static/.nojekyll` are included in the published output.
