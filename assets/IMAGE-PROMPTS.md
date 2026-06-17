# BTF — Image generation prompts

One entry per real image slot wired into the live site. Generate each image,
keep the **exact filename and dimensions**, drop the file at the path noted, and
the placeholder it replaces will disappear with no layout shift (width/height are
already declared in the HTML). Feed each "Prompt body" to ChatGPT / your image
model together with the shared **Style guide** and **Negative guidance** below.

Brand context for every prompt: **Bezpieczeństwo Twojej Firmy (BTF)** — a Gdynia /
Trójmiasto fire-safety (ochrona ppoż.) and occupational-safety (BHP) company run
by mgr inż. pożarnictwa Kamil Skamarski. Imagery should feel like real, documented
field work in Polish industrial / commercial buildings — not generic stock.

---

## Slots

### hero — Home hero image (THE main visual)
- **Status:** Wired and live — `assets/img/hero.jpg` (art direction A is in place).
  To swap in a different take: generate it and save over `assets/img/hero.jpg`
  (width/height are already declared, so no layout shift). Three directions below.
- **Filename:** `assets/img/hero.jpg`
- **Dimensions:** shown in a tall-ish card ~720x560; a source ~1200px wide is plenty
- **Format:** JPEG (q~80) or WebP — keep files small (the live one is ~200 KB)
- **Alt:** Inżynier ochrony przeciwpożarowej kontroluje gaśnicę w obiekcie przemysłowym

- **Prompt body — option A (documentary photo, recommended):** Documentary-style
  photograph of a Polish fire-safety engineer in a plain dark work jacket inspecting
  a red powder fire extinguisher (gaśnica proszkowa) mounted on a clean industrial
  wall inside a modern Gdynia commercial building. Natural side light from a large
  window, calm professional mood, shallow depth of field with the red extinguisher
  and the engineer's hands in focus. Muted slate-grey surroundings so the single red
  extinguisher reads as the accent. Realistic textures, true-to-life proportions, no
  studio gloss. ppoż. / industrial context, eye-level, slightly off-centre.

- **Prompt body — option B (isometric illustration of an evacuation plan):** Clean
  modern isometric (3/4 top-down) illustration of a small office/industrial floor
  plan as an evacuation plan: simple rooms, a clear green evacuation route with
  arrows leading to a green ISO-7010 running-man EXIT door, small red fire-
  extinguisher markers and one amber warning triangle. Flat vector style, crisp
  thin lines, generous white space, restrained palette (slate ink, near-white, one
  ppoż-red accent, evacuation green, amber). Professional infographic look, not
  childish, no text labels. ppoż. / BHP context.

- **Prompt body — option C (clean 3D render):** Minimal, photoreal 3D render of a
  single red powder fire extinguisher and a glowing green evacuation sign on a matte
  slate-grey wall, soft studio-daylight, subtle floor reflection, lots of negative
  space on one side. Premium, restrained, industrial-product feel. One bold ppoż-red
  accent against neutral greys. No text, no busy background.

### og-default — Default social share / Open Graph card
- **Filename:** `assets/img/og-default.jpg`
- **Dimensions:** 1200x630 px (Open Graph standard)
- **Format:** JPEG (q~80) or WebP
- **Alt:** Bezpieczeństwo Twojej Firmy — ochrona przeciwpożarowa i BHP w Trójmieście
  (decorative social card; alt used as the descriptive caption)
- **Prompt body:** Wide documentary photograph for a social share card showing a
  fire-safety / ppoż. scene in a Polish industrial setting — a row of serviced red
  extinguishers and an illuminated green evacuation (ewakuacja) sign on a clean
  slate-grey wall, with generous empty space on the left third for an overlaid
  wordmark. Restrained palette, one bold ppoż.-red accent, soft even daylight,
  realistic and grounded. Industrial / fire-safety context, no text baked into the
  image (the title is overlaid by the site).

> Favicon (`assets/img/favicon.svg`) is hand-authored inline SVG (a slate rounded
> square with a single ppoż.-red flame) and is **not** AI-generated — no prompt is
> needed.

---

## Subpage imagery (optional)

All four subpage images below are **wired and live** (`uslugi.jpg`, `oferta.jpg`,
`cennik.jpg`, `kontakt.jpg`). To swap any of them, generate a new take and save
over the same file — width/height are declared so there is no layout shift. These
prompts are what produced them; all share the **Style guide** + **Negative
guidance** below.

### uslugi — Usługi (services) banner
- **Filename:** `assets/img/uslugi.jpg`
- **Dimensions:** 1280x520 px (wide banner)
- **Alt:** Serwis i przegląd sprzętu ppoż. — gaśnice i szafka hydrantowa w obiekcie
- **Prompt body:** Wide documentary photograph of a Polish fire-safety technician
  servicing a row of red powder extinguishers (gaśnice) and an internal hydrant
  cabinet mounted on a clean industrial wall, a small open service case with tools
  nearby. Slate-grey environment, soft natural daylight, the red ppoż. equipment as
  the single accent. Realistic, on-location, eye-level, room for a heading on one
  side. ppoż. / BHP industrial context.

### oferta — Oferta (free first review) image
- **Filename:** `assets/img/oferta.jpg`
- **Dimensions:** 960x640 px
- **Alt:** Bezpłatny przegląd ppoż. — inżynier z listą kontrolną podczas obchodu obiektu
- **Prompt body:** Documentary photograph of a Polish fire-safety engineer doing a
  building walkthrough, holding a clipboard or tablet checklist and noting items,
  calm and professional. A red fire extinguisher and a green evacuation sign visible
  in the background as accents. Modern commercial interior, slate-grey tones, soft
  daylight, shallow depth of field. Conveys a thorough, no-pressure inspection. No
  readable text on the checklist.

### cennik — Cennik (price list) header flat-lay (optional)
- **Filename:** `assets/img/cennik.jpg`
- **Dimensions:** 1280x420 px (slim header band)
- **Alt:** Sprzęt gaśniczy — gaśnice proszkowe, koc gaśniczy i znaki ewakuacyjne
- **Prompt body:** Clean top-down flat-lay of Polish fire-safety equipment neatly
  arranged on a matte slate-grey surface: several red powder extinguishers of
  different sizes, a fire blanket (koc gaśniczy) in its pouch, and a couple of
  evacuation / fire-equipment signs. Even soft daylight, generous spacing, one bold
  ppoż.-red accent across the gear, catalogue-like but realistic. No text.

### kontakt — Kontakt (local context) image (optional)
- **Filename:** `assets/img/kontakt.jpg`
- **Dimensions:** 960x640 px
- **Alt:** Bezpieczeństwo Twojej Firmy — obsługa ppoż. i BHP w Gdyni i Trójmieście
- **Prompt body:** Documentary photograph of a fire-safety engineer with a red
  equipment case by the entrance of a modern commercial building in a Gdynia /
  Trójmiasto industrial-port setting, approachable and professional, soft overcast
  daylight, slate-grey tones with a single red accent. No readable signage, no
  license plates, no fictional logos. Grounded local feel.

> Keep image slots few and purposeful; add a new entry here only when a new
> `<img>`/`og:image` slot is actually wired into the pages.

---

## Style guide

A cohesive visual system so every generated image looks like the same brand.

- **Palette (pin these exactly):**
  - ppoż.-red accent — `#D7261E` (the single bold accent; use sparingly, on the
    extinguisher / a sign / a stripe)
  - slate ink — `#1A1D21` (dark surfaces, work clothing, shadows)
  - surfaces — near-white `#FFFFFF` and light grey `#F4F5F7` for walls/backgrounds
  - optional BHP detail accents only where natural: amber caution `#F2B705`,
    evacuation green `#1E8E5A`
- **Imagery direction:** documentary, photojournalistic realism of real Polish
  industrial / commercial fire-safety work (gaśnice, hydranty, znaki ewakuacyjne,
  instrukcje bezpieczeństwa). Grounded, honest, "shot on location" — not concept art.
- **Lighting:** consistent soft, natural daylight (window or overcast), neutral
  white balance, gentle directional side light. The same calm lighting mood across
  every slot so a hero and an OG card feel like one shoot.
- **Composition:** intentional, slightly asymmetric framing; eye-level or just
  below; shallow-to-medium depth of field; clear negative space; the red accent as
  the single focal point. Consistent lighting and composition across all slots.
- **People:** realistic Polish trades/engineering people, correct hands and
  proportions, plain modest workwear, no model-glamour posing.

---

## Negative guidance (anti-"AI-slop")

Explicitly exclude the following from every generation:

- no generic stock / clip-art look
- no glassmorphism
- no warped text or fake logos
- no extra/melted fingers or distorted hands
- no oversaturated neon gradients
- no centred-everything symmetry, no lens-flare overload, no plastic 3D-render sheen
- no fictional or mislabeled equipment; extinguishers, signs and hydrants must look
  like real EU/Polish ppoż. gear
