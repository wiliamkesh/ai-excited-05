# The Sun That Opens

Entry for **make.fun `ai-excited-01`** — an image that should feel exciting
the moment you see it, even at thumbnail size.

## The image

A giant sun hangs over a dark cliff — and the sun is **cracked open like a
cosmic door**. Inside the fissure there is no fire. There is *night*: a
violet nebula, stars, a crescent moon, and one enormous glowing eye staring
out at the viewer.

Below, a tiny robot stands on the cliff edge, leaning back against the pull
of the opening — one hand shielding its face from the glare, the other
reaching toward the light. The cliff itself is breaking apart: rock
fragments, dust and embers stream upward into the crack, and the clouds
bend in arcs around the sun, dragged toward the opening. A warm pool of
light spills onto the cliff beneath the fissure.

One impossible thing, shown plainly: **a sun that contains the night.**

Palette: gold / amber / rose / violet, with a near-black cliff for scale
contrast. The robot is ~1/10th the height of the sun — the whole picture
is about that difference in scale.

## Files

| File | What it is |
| --- | --- |
| `main.ts` | Entry point. Node 22+, stdlib only. Writes the artwork deterministically to `out/entry.png`. |
| `generate.py` | The artwork generator (Python + Pillow, seeded, deterministic). Rebuilds `out/entry.png` and re-embeds it into `main.ts`. |
| `out/entry.png` | The finished image: 1024×1024 PNG, 700,039 bytes. |
| `package.json` | `npm start` runs `main.ts`. No dependencies. |
| `LICENSE` | MIT. |

## Run it

```sh
node main.ts        # writes out/entry.png
node main.ts        # run it again — byte-identical output
```

`main.ts` is self-contained: the finished PNG is embedded in it as base64,
so it needs no other files and no network. It verifies its own output
against the embedded SHA-256 and exits non-zero on mismatch.

To regenerate the artwork from scratch (same bytes, fixed seed):

```sh
python3 generate.py
```

## Verification

- `out/entry.png`: PNG magic bytes `89 50 4E 47`, 1024×1024, 700,039 bytes
  (< 1 MiB).
- `node main.ts` run twice → identical SHA-256:
  `0367a5ef3c516cd05fc9100662512757e7bf91af122be8803d6c4bbbe114bc31`.
