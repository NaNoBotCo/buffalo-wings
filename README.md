# Wing Country

**flats, drums, dips, and who fried the first one** — a directory of the chicken wing in
the United States, built the way [wichaa.net](https://wichaa.net) is built: one JSON
record per node of the tradition, every field carrying where it came from, every page
saying what its neighbours are to it.

**Live: https://nanobotco.github.io/buffalo-wings/**

158 records · 1,188 kin links · 33 places · 22 sauce labels read ·
28 recipes · 68 pictures · 292 sources · 85 tags on places

## What is in it

| | |
|---|---|
| **Styles** | Buffalo, Rochester, Atlanta lemon pepper, Chicago mild sauce, D.C. mumbo, Baltimore Old Bay, Nashville hot, Memphis dry rub, Korean American, jerk, Alabama white, the smoked wing, garlic parmesan |
| **Sauces and dips** | 22 records, each with its label read off the Nutrition Facts panel and its ingredients in the order the maker prints them |
| **On the side** | 18 — celery, fries, pizza logs, beef on weck, the garbage plate, boneless wings |
| **In the kitchen** | 15 — the cut, the dredge, the double fry, the toss, the oil |
| **Places** | 33 written up, from the Anchor Bar to Prince's to Wingstop |
| **People** | 18 — the Bellissimos, John Young, Thornton Prince, Drew Cerza, Calvin Trillin |
| **Words** | 18 with their roots: drumette, flat, flapper, party wing, weck, mumbo, atomic |
| **Stories** | who fried the first one · ranch against blue cheese · the flat and the drum · whether a boneless wing is a wing · what a wing costs · where all of this came from |

## Pages that answer a question

- **[/near/](https://nanobotco.github.io/buffalo-wings/near/)** — wings near you, sorted
  by distance, with filter chips for naked, breaded, smoked, wing night, open today,
  Black-owned, woman-owned and LGBTQ+ welcoming. Each tag carries the source it came from.
- **[/sauce/](https://nanobotco.github.io/buffalo-wings/sauce/)** — every bottle read off
  its own label: sodium and sugar per tablespoon, what comes first on the list, where the
  makers are.
- **[/wing/](https://nanobotco.github.io/buffalo-wings/wing/)** — drumette, flat, tip, and
  which pieces each style serves.
- **[/make/](https://nanobotco.github.io/buffalo-wings/make/)** — build a sauce, a rub or a
  dip. Every proportion names its own source, and says plainly where the proportions are
  this project's own.
- **[/numbers/](https://nanobotco.github.io/buffalo-wings/numbers/)** — distance to the
  nearest counter anywhere in the lower forty-eight, founding years, what the recipes call
  for, days open.
- **[/quiz/](https://nanobotco.github.io/buffalo-wings/quiz/)** — six questions, and a city
  hands you a plate.

## Provenance

Every field carries a tier: **cited** (a named source, linked) · **harvested** (fetched
from an open dataset, with its licence) · **tradition** (general knowledge, hedged in the
prose) · **inference** (this project reasoning from the above) · **field** (somebody stood
there). In a narrative, each stretch is marked inline: plain prose is cited,
*Tradition holds —* hedges, *Inference —* reasons.

Hours run on three states, never two: open, closed, and nobody published it. A day in
neither list is unknown and drops out of the filters.

## For machines

[`/api/nodes.json`](https://nanobotco.github.io/buffalo-wings/api/nodes.json) ·
[`/api/index.json`](https://nanobotco.github.io/buffalo-wings/api/index.json) ·
[`/api/places.json`](https://nanobotco.github.io/buffalo-wings/api/places.json) ·
[`/api/sauces.json`](https://nanobotco.github.io/buffalo-wings/api/sauces.json) ·
[`/api/kin.json`](https://nanobotco.github.io/buffalo-wings/api/kin.json) ·
[`/api/coverage.json`](https://nanobotco.github.io/buffalo-wings/api/coverage.json) ·
[`llms.txt`](https://nanobotco.github.io/buffalo-wings/llms.txt) ·
[`llms-full.txt`](https://nanobotco.github.io/buffalo-wings/llms-full.txt) ·
[CSV](https://nanobotco.github.io/buffalo-wings/nodes.csv) ·
[JSONL](https://nanobotco.github.io/buffalo-wings/nodes.jsonl)

## Running it

```bash
python3 tools/validate.py     # every record must pass
python3 tools/build.py        # records -> build/api + search tables
python3 tools/cards.py        # the 1200x630 share cards
python3 tools/site.py         # build/site
python3 tools/serve.py        # http://127.0.0.1:8796
python3 -m unittest discover -s tests
./publish.sh                  # build into docs/, which GitHub Pages serves
```

Stdlib only, plus Pillow for the cards. `README.txt` is the working guide;
`AUTHORING.txt` is the record spec.

## Licence

Records CC BY 4.0. Place points OpenStreetMap, ODbL 1.0 (share-alike). Pictures each
carry their own licence in a sidecar. Pre-1930 recipes are public domain; Wikibooks
recipes are CC BY-SA 4.0. Code MIT. See [LICENSE](LICENSE) and [NOTICE.txt](NOTICE.txt).

**Using it.** Attribution is the whole of the condition — copy it, adapt it,
sell it, index it, train on it, and say where it came from.
[Open an issue](https://github.com/NaNoBotCo/buffalo-wings/issues) if something is missing.

---

Contact: Nan · nan@motdang.net · Sponsor: [Ko-fi](https://ko-fi.com/defiantchiangmai) · [Patreon](https://www.patreon.com/nanobotco)

<!-- fleet-roster -->

## Elsewhere from the same publisher

- [Mot Dang](https://motdang.net/) — city directory for Chiang Mai and Chiang Rai
- [The Mae Hong Son Loop](https://nanobotco.github.io/mae-hong-son-loop/) — motorcycling the 600 km loop out of Chiang Mai — curves counted, air measured
- [Muay Thai](https://motdang.net/muay-thai/) — the eight limbs, the thirty named techniques, the ceremony, and every gym on the map
- [Roads of Chiang Mai](https://motdang.net/roads/) — the square of 1296, four rings, and what each one did to the city — counted from the map
- [wichaa](https://wichaa.net/) — Lanna manuscripts, the amulet market, and the traditions around them
- [Hand Poke](https://nanobotco.github.io/hand-poke/) — 28 traditions of marking skin by hand — the leg-tattoo zone of Burma, the Shan States and Lanna, counted
- [Black Holes, Drawn](https://nanobotco.github.io/black-holes/) — black holes modelled and drawn from the equations — generators, the past, present and future, the legends
- [Quantum Computing, plainly](https://nanobotco.github.io/quantum-computing/) — the history and theory of quantum computing in plain words, with demos; refreshed weekly
- [Goin' Fast](https://nanobotco.github.io/goin-fast/) — a dirt-simple explainer about speed — twenty measured speeds from the ground under the house to light, and what each one costs
- [The Three-Body Problem](https://nanobotco.github.io/three-body/) — the mathematics of the three-body problem in plain words, with the orbits found rather than copied
- [Exceptional Magic](https://nanobotco.github.io/exceptional-magic/) — the octonions, triality, the magic square and E8, computed and drawn — a plain-spoken reading of one paper
- [Amulet Atlas](https://nanobotco.github.io/amulet-atlas/) — amulets, charms and talismans worldwide
- [Carolina Barbecue](https://nanobotco.github.io/carolina-barbecue/) — barbecue in North and South Carolina
- [Pink Box](https://nanobotco.github.io/pink-box/) — the American mom-and-pop donut shop
- [Basque Tables](https://nanobotco.github.io/basque-tables/) — Basque dining rooms of California, Nevada and Idaho
- [Pinot Country](https://nanobotco.github.io/pinot-noir/) — pinot noir: the vine, the regions, the cellars
- [Care Abroad](https://nanobotco.github.io/care-abroad/) — treatment across borders, with published prices and their dates
- [Thai Roots](https://nanobotco.github.io/thairoots/) — a root dictionary of Thai, with a word decomposer
- [The index](https://nanobotco.github.io/index/) — every corpus, site and repository, counted
- [Uptake](https://nanobotco.github.io/uptake/) — a field manual on publishing for machines that copy
- [NaNoBotCo](https://nanobotco.github.io/) — the portal
- [ฮักฝรั่ง](https://hakfarang.net/) — เรื่องเงิน วีซ่า และชีวิตกับแฟนฝรั่ง
- [Offrampt](https://offrampt.net/) — turning crypto into spendable local money, Thailand first

All of it, counted: https://nanobotco.github.io/index/ · roster as JSON: https://nanobotco.github.io/index/fleet.json
