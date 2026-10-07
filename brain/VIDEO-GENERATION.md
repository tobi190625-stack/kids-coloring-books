# How we generate real animated ads (not just slides)

Problem: our videos are mostly still pages with zoom, a color sweep and subtitles. The strategy says the top format
for kids' books is the **animated story moment** (characters move, snow falls, the truck jumps). We need motion at scale.

## Decision: hybrid pipeline
**AI image-to-video makes short "alive" clips (3-5 s) from OUR book art. Our code (`tools/render_script.py`) assembles
the ad around them:** hook caption on frame 1, coloring sweep, word-by-word subtitles, voice + music, end card.
- AI gives motion. Our code gives consistency, branding, subtitles, and speed (one script → many variations).
- Image-to-video from our own page/cover keeps the characters on-model (no random new style).
- One book = ~10 clips (key pages) → reused in dozens of ads.

## Options compared (prices checked Oct 2026, verify before buying)
| Option | Cost | Quality / fit | Verdict |
|---|---|---|---|
| **Kling** (klingai.com) | free plan with daily credits; Standard ~$8.80/mo, Pro ~$33/mo | Strong image-to-video, good with cartoon characters, "Elements" keeps a character consistent from reference images | **Start here.** Test free credits on 3 pages first; Standard is enough for ~1 book/week of clips |
| **Higgsfield** | Starter $19/mo (270 credits), Plus $47-59/mo; one 5 s Seedance clip ≈ 17-45 credits | An all-in-one hub of many models (Kling, Seedance, Veo...), extra tools | Good but ~2-3× the price per clip of Kling direct; only if we want many models in one place. Try the $3 two-day pass first |
| **Local GPU: Wan 2.2 (5B) in ComfyUI** | free (electricity) | Open source, image-to-video, first-frame-to-last-frame; 5B runs on **8-12 GB VRAM NVIDIA** (RTX 3060 12GB / 4060 Ti / 4070+). 14B needs 24 GB+ | **Best long-term if the home PC has an NVIDIA GPU with 12 GB+.** Slower (minutes per clip), unlimited |
| **Local GPU: LTX-2** | free | Open source, fast, needs ~12-16 GB VRAM | Alternative to Wan on a 16 GB card |
| **Code-only upgrade (free, now)** | free | Cut characters out of the page (rembg), animate bounce/blink/wiggle, falling snow, parallax, page-turn transitions in our renderer | Do it anyway: cheap motion for every ad, no AI label issues beyond the art itself |
| Remotion / HyperFrames | free / open | Polished motion graphics as code (React/HTML) | Later, for nicer text/transition templates |

AMD or laptop/integrated GPUs: local AI video is impractical → use Kling.

## Recommendation (in order)
1. **This week (free):** upgrade our renderer: character cut-outs that bounce/blink, falling snow/sparkles, page turns. Claude can do this in the cloud session.
2. **Test Kling free credits:** 3 clips (Nico snow angel, Rocco jump, Posy rainbow). Prompt = "gentle cartoon animation, character waves/jumps, camera still, keep the exact art style, no new characters". Judge: does it stay on-model?
3. If good → **Kling Standard (~$9/mo)**: ~10 clips per book, saved in `campaigns/<book>/clips/`.
4. **Check the home GPU** (Windows: Task Manager → Performance → GPU, or `nvidia-smi`). If NVIDIA 12 GB+: install ComfyUI + Wan 2.2 5B and generate clips for free; keep Kling as backup.
5. Higgsfield only if we outgrow Kling and want many models.

## How a clip becomes an ad
`campaigns/<book>/scripts/*.json` gets a new scene type `"clip"` (path to the AI clip): the renderer places it in the
frame, adds the hook caption and subtitles, mixes voice + music → TikTok/Reels/Shorts versions in one command.

## Rules
- Always start from our own book art (image-to-video), never text-only prompts; keep faces/proportions on-model.
- Turn on the "AI-generated" label on TikTok/Meta/YouTube when posting.
- No real children, no brand characters, check every clip frame by frame before using it.

Sources: Higgsfield pricing https://www.blotato.com/blog/higgsfield-pricing · https://www.krea.ai/blog/higgsfield-pricing-explained-2026-unlimited-credits-and-real-monthly-costs ·
Kling pricing https://framesurfer.com/blogs/kling-ai-pricing · https://www.photonpay.com/hk/blog/article/kling-ai-pricing?lang=en ·
Wan 2.2 VRAM https://willitrunai.com/blog/wan-2-2-vram-requirements · https://github.com/Wan-Video/Wan2.2 ·
LTX-2 https://www.stevenvideo.com/blog/ltx-2-open-source-ai-video-guide · https://ltx.io/blog/hardware-for-ai-video-models
