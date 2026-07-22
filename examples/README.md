# Examples

Copy-paste starting points for a new screenshot-cropper project.
Full documentation of every option: [../README.md](../README.md).

## Files

- `minimal/screenshot-cropper.json` — smallest valid config: crop only.
- `full/screenshot-cropper.json` — every supported section: `crop`, `background`,
  `overlay`, `text` (with per-locale fonts from the repo `fonts/` directory), `export`
  (WebP output). Remove the sections you don't need — `background`, `overlay`, `text`
  and `export` are all optional.
- `locales/en.json`, `locales/de.json` — locale file format. Keys `Text_1`, `Text_2`, …
  map to screenshot numbers (`01.png` → `Text_1`). `\n` in values creates line breaks.

## Expected project layout

```
my-project/
├── input/
│   ├── bg.png                # only if config has "background"
│   ├── overlay.png           # only if config has "overlay"
│   ├── locales/              # only if config has "text"
│   │   ├── en.json
│   │   └── de.json
│   └── screenshots/
│       ├── 01.png
│       └── 02.png
└── screenshot-cropper.json
```

## Run

```
uv run python main.py --directory path/to/my-project
```

Output lands in `my-project/output/`. See the main README for `--screenshot`,
`--language`, `--skip-existing` and `--editor` flags.
