# Crustates brand kit

The crab logo, product icons, badges, banners and colours of [Crustates](https://crustates.eu).

![Crustates](svg/logo-horizontal-light.svg)

## What's here

| Folder | Contents |
|---|---|
| `svg/` | Every asset as SVG: mark, logos, wordmarks, product icons, badges, emblems, banners, favicon, app icon, avatar |
| `png/` | PNG exports for places that can't use SVG (favicons, app icons, avatars, social images, badges) |
| `generator/` | `build_brand.py`, the script that draws everything from code, and the fonts it needs |

Download the latest kit as a zip from the [Releases page](https://github.com/crustates/brand/releases/latest).

## Product icons

| Tide | Reef | Current | Molt | Cast | Barnacle | Spawn |
|:---:|:---:|:---:|:---:|:---:|:---:|:---:|
| <img src="svg/icon-tide.svg" width="80" alt="Tide"> | <img src="svg/icon-reef.svg" width="80" alt="Reef"> | <img src="svg/icon-current.svg" width="80" alt="Current"> | <img src="svg/icon-molt.svg" width="80" alt="Molt"> | <img src="svg/icon-cast.svg" width="80" alt="Cast"> | <img src="svg/icon-barnacle.svg" width="80" alt="Barnacle"> | <img src="svg/icon-spawn.svg" width="80" alt="Spawn"> |

## Badges

Show that your project runs on or integrates with Crustates:

![Runs on Crustates](svg/badge-runs-on.svg)

```md
[![Runs on Crustates](https://raw.githubusercontent.com/crustates/brand/main/svg/badge-runs-on.svg)](https://crustates.eu)
```

![Powered by Crustates](svg/badge-powered-by.svg)

```md
[![Powered by Crustates](https://raw.githubusercontent.com/crustates/brand/main/svg/badge-powered-by.svg)](https://crustates.eu)
```

More badges (products, open source, self-hosted) are in `svg/badge-*.svg`.

## Products and colours

| Name | Area | Colour | Text on it |
|---|---|---|---|
| Crustates | The platform | Rust `#E8552D` | ink |
| Tide | Compute | Blue `#1F3FD1` | cream |
| Reef | Storage | Rust `#E8552D` | ink |
| Current | Networking | Teal `#0B7A70` | cream |
| Molt | OS and upgrades | Yellow `#FFD23F` | ink |
| Cast | Clusters | Brown `#8B5E3C` | cream |
| Barnacle | Plugins | Violet `#A77BFF` | ink |
| Spawn | GitOps and deploys | Pink `#FF7AA8` | ink |
| Assistant | AI assistant | Green `#3DDC84` | ink |

Base colours: ink `#111111`, cream `#FFF6E5`. Fonts: Space Grotesk (headings and UI) and JetBrains Mono (code and labels).

## Regenerate

```sh
pip install -r generator/requirements.txt
python generator/build_brand.py generator/fonts out
```

CI checks that `svg/` matches the generator output, so change the code, not the SVGs. The reference is Linux: on macOS the two emblem SVGs can differ in the last digit of some coordinates.

## Using the brand

Write about Crustates, show the logo unmodified and add the badges to projects that run on it. Don't ship a fork or a product under the name or the crab. [TRADEMARK.md](TRADEMARK.md) has the details.

## Licence

The files are licensed under [CC BY 4.0](LICENSE). The name "Crustates" and the crab are trademarks: see [TRADEMARK.md](TRADEMARK.md). The fonts in `generator/fonts` are under the [SIL Open Font License 1.1](generator/fonts/OFL.txt).
