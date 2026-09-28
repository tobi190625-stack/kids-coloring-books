# AI line-art prompts for coloring pages

Use with Canva `generate-image`, Midjourney, Ideogram, GPT Image, Flux, etc.
Save results as PNG, at least 2400 px wide, into the book's `art/` folder.

## Base prompt (paste, then add the scene)

```
Children's coloring book page, black and white line art, thick clean bold outlines,
simple cute cartoon style for ages 3-6, large shapes, no shading, no gray, no color,
no crosshatching, pure white background, no text, no border, centered composition.
Scene: <SCENE>
```

Add for Midjourney: `--ar 4:3 --style raw --no color, shading, text, border`

## Scene examples
- a happy little lion cub with a fluffy mane sitting in the jungle, big sun in the sky
- a friendly baby elephant spraying water from its trunk
- a smiling monkey hanging from a tree branch by its tail
- a small dinosaur holding a flashlight in a dark bedroom, moon in the window
- a cute fire truck with a smiling face driving down a street

## Keep the character consistent across pages
1. Generate the main character once, pick the best one.
2. Reuse it as a reference image (Midjourney `--cref`, Ideogram/GPT Image "use this character").
3. Repeat the exact same character description in every prompt
   (e.g. "little lion cub named Leo, round face, big curly mane, small tail tuft").

## Fix bad outputs
- Gray shading → add "flat, no fills, no shadows" and increase line weight.
- Too detailed for toddlers → add "very simple, few large shapes, minimal details".
- Converting a PNG to crisp black & white: ask Claude to threshold it with Pillow.
