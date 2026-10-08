# Gaming laptop setup: free AI video + emotional voice (one time, about 1 hour)

Everything here is free and runs on the laptop's NVIDIA GPU, with no limits and no subscription.

## 1. Check the GPU (2 min)
Task Manager → Performance → GPU. Write down the name and "Dedicated GPU memory".
- **6-8 GB** (RTX 3050/3060 laptop, 4060): AI video works at 480p, 5 s clips. Perfect for our ads.
- **12 GB+**: 720p and longer clips.

## 2. AI video clips: Wan2GP through Pinokio (one click)
Wan2GP is a free, open-source video generator made for gaming laptops ("GPU poor"). It runs Wan 2.2, LTX and more.
1. Install **Pinokio**: https://pinokio.co (download for Windows, install, open).
2. In Pinokio search **Wan2GP** → Install. It downloads everything by itself (needs about 30 GB free disk).
3. Start it. It opens in the browser.
4. Choose **Wan 2.2 image-to-video** (or LTX Video, which is faster on 6-8 GB).
5. Upload one of our book pictures (`books/<book>/art/NN.png`, or a colored page from Claude), write a short prompt:
   `gentle cartoon animation, the character waves and smiles, camera still, keep the exact art style, no new characters`
6. Generate a 5 s clip at 480p. Save it into the repo: `campaigns/<book>/clips/<page>-<what>.mp4`, then git push.
7. Tell Claude "new clips are pushed". Claude puts them into the ads (the renderer already has a "clip" scene).
Good first clips: Nico making the snow angel, Rocco flying off the ramp, Posy with the rainbow, Benny rolling down the hill.

## 3. Emotional voice: Chatterbox on the GPU (fast)
Chatterbox is the warm, expressive voice the ads now use (open source, MIT license, free for business).
On this school laptop it runs on the CPU (slow). On the gaming laptop it takes seconds per line.
1. Install **Python 3.12** (python.org, tick "Add to PATH") and **Git** (git-scm.com).
2. `git clone https://github.com/tobi190625-stack/kids-coloring-books` and open the folder.
3. `python -m venv %USERPROFILE%\cbvenv`
4. `%USERPROFILE%\cbvenv\Scripts\pip install chatterbox-tts`
   then (for the GPU): `%USERPROFILE%\cbvenv\Scripts\pip install torch torchaudio --index-url https://download.pytorch.org/whl/cu124 --force-reinstall`
5. `pip install -r requirements.txt imageio-ffmpeg soundfile scipy edge-tts gradio_client openpyxl` (the normal Python).
6. Make ads: `python tools/problem_ads.py all` → videos land in `campaigns/fresh/`.

## 4. Who does what
- Claude (any laptop): writes the ad scripts, colors, captions, schedule, posting board.
- Gaming laptop: AI clips (Wan2GP) + fast voice + fast rendering.
- Owner: schedules the posts from the posting board.
