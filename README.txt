WING COUNTRY
============

A directory of the chicken wing in the United States, built the way wichaa.net is
built: one JSON record per node of the tradition (a city's style, a sauce, a dip, a
dish, a kitchen practice, a place, a person, an organization, an event, a word), every
field carrying where it came from, every page saying what its neighbours are to it.
A static site for people and bots.

WHERE THINGS ARE
----------------
  data/nodes/<type>/<id>.json   the records. THE TRUTH. Edit these.
  data/sources/sources.json     every source a record may cite
  data/vocab/*.json             regions, the eleven types, facet keys, tags, recognizers,
                                the quiz, and the three builders behind /make/
  data/harvest/osm-places.json  every OpenStreetMap wing place in the fifty states
                                (tools/harvest_osm.py; ODbL; fetch date inside)
  data/geo/states.json          state outlines, Natural Earth, public domain
                                (tools/fetch_geo.py refetches them)
  data/images/<id>/             pictures with a .json sidecar each (licence, author)
  schema/node.schema.json       what a record must look like
  AUTHORING.txt                 how to write a record; the cast list
  BRIEF.txt                     the brief every drafting agent works from
  tools/                        the pipeline (below)
  build/                        generated. Never edit. Safe to delete.
  build/site/                   the website, ready for any static host
  docs/                         the published build (GitHub Pages serves this)
  vendor/                       generated copies of the fleet search core

THE PIPELINE (in order)
-----------------------
  python3 tools/validate.py     every record must pass
  python3 tools/build.py        records -> build/api, build/searchdocs.json,
                                data/search/wings.thesaurus.json
  python3 tools/cards.py        the 1200x630 share cards (draws only what is missing)
  python3 tools/site.py         build/site: pages, maps, glossary, search, JSON-LD,
                                sitemap, llms.txt, robots, CSV/JSONL
  python3 tools/serve.py        http://127.0.0.1:8796
  python3 -m unittest discover -s tests

  Or double-click "Wing Country.command" for a numbered menu.

  SITE_URL=https://example.org python3 tools/site.py   sets the canonical host.
  BUILD_DRAFT=1 python3 tools/build.py                  builds while records are still
                                being written (unwritten kin targets warn instead of
                                failing). Never for a publish.

MAPS
----
  Every national map is drawn in Albers equal-area conic — the projection the Census
  Bureau uses — by tools/usmap.py, with Alaska and Hawaii projected separately and set
  into the lower-left corner. Each map that shows them prints the scale they are drawn
  at, because an unlabelled inset lies about size.

THE PAGES THAT ANSWER A QUESTION
--------------------------------
  /near/    Find the wings. Your browser's own location, or a town you type, and every wing place in the country sorted by distance, with
            filter chips for naked, breaded, smoked, house sauce, wing night, open today,
            Black-owned, woman-owned and LGBTQ+ welcoming. Below it, "worth the drive":
            the places other people wrote down, counted by how many different people did.
  /sauce/   Read the bottle. Every sauce measured off its own label: sodium and sugar per
            tablespoon as strip plots, what comes first on the ingredient list as a
            stacked bar, and a little map per style showing where the makers are. Each
            chart has a table twin. Built from the `profile` block on the sauce records.
  /wing/    Which part of the bird. A drawn wing — drumette, flat, tip — and a small one
            per style showing which pieces it serves.
  /make/    Build a sauce, a rub or a dip. Every proportion names its own source.
  /numbers/ Count it up. Distance to the nearest counter anywhere in the lower 48,
            founding years, what the recipes call for, days open, kin by kind of page.
  /quiz/    Which wing claims you. Six questions, scored in the browser, no storage.
  /art/     Signs, neon, murals, labels.
  /stories/ Who fried the first one, ranch against blue cheese, the flat and the drum,
            whether a boneless wing is a wing, what a wing costs, and where all of this
            came from.

TAGS, AND THE RULE BEHIND THEM
------------------------------
  A place can carry tags: Black-owned, woman-owned, LGBTQ+ welcoming, naked, breaded,
  smoked, house sauce, all flats or all drums, bone-in only, wing night, open late,
  halal, cash only, closes when sold out, counter or window, bar, family-run, closed.
  A tag carries the source it came from — the owner's own words, a press profile that
  names the owner, a public directory, a certification list, or somebody who stood there.
  Ownership and welcome tags rest on one of those; the validator refuses them at the
  tradition and inference tiers. A place with no tag has
  not been read yet: that is a fact about this project, not about the place.
  data/vocab/tags.json holds the keys and what each one needs.

HOURS: THREE STATES, NEVER TWO
------------------------------
  open, closed, and nobody published it. A day in neither list is unknown, and it drops
  out of the filters rather than counting either way. Guessing a closure is worse than a
  blank, because a reader drives on it.

WHAT A PAGE CARRIES
-------------------
  The record's own text (what / story / how / today), the root of its name where it has
  one, a facts table, "Its kin" (this page's sentence about each neighbour) and "Pages
  that point here" (each neighbour's sentence about this page), pictures with licences,
  sources, and a provenance mark on each section: Cited, Harvested, Tradition,
  Inference, Field.

  /places/    every place on one map: the ones written up (sauce-coloured, linked) plus
              every OpenStreetMap row (grey), grouped by state and county.
  /words/     the vocabulary with its roots.
  /search/    fleet search core in the browser: fuzzy, thesaurus, tier reported.
  /coverage/  scope as an object: what is in, what is not, where rows come from.
  /api/       everything as JSON. llms.txt and llms-full.txt for machines.
  wander.html a page at random. Press r anywhere.

ADDING A RECORD
---------------
  Read AUTHORING.txt. Copy an exemplar, change every field, keep the id in the filename,
  cite only ids in sources.json, run validate.py.

PICTURES
--------
  python3 tools/harvest_commons.py --walk "Category:Buffalo wings"
  python3 tools/harvest_commons.py --search "chicken wings"
      -> data/images/_triage/*.json (nothing downloaded)
  Put chosen file titles in a record's x_commons_files, then
  python3 tools/harvest_commons.py --harvest <id> --apply
  Only CC0, public domain, CC BY, CC BY-SA and FAL are accepted.

REFRESHING THE HARVESTS
-----------------------
  python3 tools/harvest_osm.py            every state, one Overpass query each; saves
                                          after each state, so a kill keeps progress
  python3 tools/harvest_osm.py --resume    only the states not already on disk
  python3 tools/harvest_osm.py --states NY,PA
  python3 tools/harvest_osm.py --towns     reverse-geocode rows with no addr:city,
                                          one request a second, cached by osm_id

NOT HERE YET
------------
  A domain. Field observations. Pictures for most records. Menu prices with dates.
