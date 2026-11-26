#!/usr/bin/env python3
"""Compose docs/demo.mp4 (1080p H.264 + AAC, Piper narration) from real captures.

Inputs: docs/demo-logs/testnet.txt (real onyx-1 transactions), docs/demo-logs/gno-test.txt,
        screenshots of the live gnoweb pages and the sealer page (DEMO_SHOTS dir: g1..g6.png).
    PIPER=... VOICE=... DEMO_SHOTS=... python3 scripts/demo-video.py
"""
import os, re, subprocess, wave
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[1]
LOGS = ROOT / "docs" / "demo-logs"
SHOTS = Path(os.environ.get("DEMO_SHOTS", ROOT / "work" / "shots"))
WORK = Path(os.environ.get("DEMO_WORK", ROOT / "work" / "video")); WORK.mkdir(parents=True, exist_ok=True)
PIPER = os.environ.get("PIPER", "/workspace/tools-video/piper/piper")
VOICE = os.environ.get("VOICE", "/workspace/tools-video/en_US-lessac-medium.onnx")
OUT = ROOT / "docs" / "demo.mp4"
W, H = 1920, 1080
GF = "/usr/share/fonts/truetype/sand-box/google"
INTER = f"{GF}/Inter/Inter-VariableFont_opsz,wght.ttf"
MONO = f"{GF}/JetBrains Mono/JetBrainsMono-VariableFont_wght.ttf"
BG = (15, 17, 21); PANEL = (23, 26, 33); FG = (232, 230, 227); DIM = (154, 160, 170)
ACC = (242, 184, 75); GREEN = (75, 209, 139); RED = (255, 107, 107); CYAN = (88, 196, 220)

def F(path, size, w=None):
    f = ImageFont.truetype(path, size)
    try: f.set_variation_by_axes([w] if path == MONO else [14, w or 400])
    except Exception: pass
    return f

def card(title, lines, name, sub=None):
    im = Image.new("RGB", (W, H), BG); d = ImageDraw.Draw(im)
    d.rectangle([0, 0, 16, H], fill=ACC)
    d.text((120, 200), title, font=F(INTER, 110, 800), fill=FG)
    if sub: d.text((124, 340), sub, font=F(INTER, 46, 500), fill=ACC)
    y = 440
    for l in lines:
        d.text((124, y), l, font=F(INTER, 50, 400), fill=DIM if l.startswith("  ") else FG); y += 78
    im.save(WORK / name); return WORK / name

def color(l):
    s = l.strip()
    if s.startswith("$"): return CYAN
    if "OK!" in s or "PASS" in s or s.startswith("ok"): return GREEN
    if "Error" in s or "FAIL" in s: return RED
    if s.startswith(("TX HASH", "HEIGHT")): return ACC
    return FG

def term(lines, name, title):
    im = Image.new("RGB", (W, H), BG); d = ImageDraw.Draw(im)
    d.rounded_rectangle([90, 70, W - 90, H - 70], 18, fill=PANEL, outline=(44, 49, 59), width=2)
    d.text((130, 95), title, font=F(INTER, 34, 600), fill=DIM)
    fm = F(MONO, 34, 500); y = 165
    for l in lines:
        d.text((130, y), l, font=fm, fill=color(l)); y += 48
    im.save(WORK / name); return WORK / name

def shot(src, name, caption):
    im = Image.new("RGB", (W, H), BG); s = Image.open(src).convert("RGB")
    sc = min((W - 160) / s.width, (H - 170) / s.height); s = s.resize((int(s.width * sc), int(s.height * sc)), Image.LANCZOS)
    im.paste(s, ((W - s.width) // 2, 110)); d = ImageDraw.Draw(im)
    d.text((80, 38), caption, font=F(INTER, 40, 700), fill=ACC)
    im.save(WORK / name); return WORK / name

# ---- real log excerpts
tn = (LOGS / "testnet.txt").read_text().split("\n")
def blocks():
    out, cur = [], None
    for l in tn:
        if l.startswith("$ "): cur = [l]; out.append(cur)
        elif l.startswith("== "): break
        elif cur is not None and l.strip(): cur.append(l)
    return out
B = blocks()
def clip(cmd, keep=("OK!", "HEIGHT", "TX HASH", "Error: p", "Error: a", "re-hash", "commitment")):
    res = []
    for l in cmd:
        if l.startswith("$ "):
            res.append(re.sub(r"^\$ scripts/receipts.sh (\w+) .*? (\d+)$", r"$ receipts.sh \1 ... \2", l) if l.split()[2] == "seal" else l.replace("scripts/", "").replace(".secrets/receipts/", "").replace(".secrets/", ""))
        elif l.startswith("commitment"): res.append("commitment " + l.split()[1][:20] + "...")
        elif l.startswith("re-hash"): res.append("re-hash " + l.split()[-1][:20] + "...")
        elif l.startswith("TX HASH"):
            if l.split()[-1] != "HASH:": res.append(l)
        elif l.startswith("HEIGHT") and l.split()[-1] == "0": continue
        elif l.startswith(("OK!", "HEIGHT")): res.append(l)
        elif l.startswith("Error: ") and "panic" not in l and "FmtError" not in l and "Error: errors" not in l: res.append(l)
    return res
seal = sum([clip(b) for b in B[:3]], [])
rev = clip(B[3]) + [""] + clip(B[4])
vd = [l for b in B[5:] for l in clip(b)]
tst = [l for l in (LOGS / "gno-test.txt").read_text().split("\n") if l and "GAS" not in l and "=== RUN" not in l]

SCENES = [
 (card("Receipts", ["Call it now. Prove it later.", "  Sealed predictions on Gno.land"], "s01.png", "Gnome Tavern hackathon entry"),
  "Receipts. Call it now, prove it later. A realm on the G N O dot land testnet for sealed predictions."),
 (card("The catch with hashes", ["Seal ten guesses, reveal only the winner.", "Receipts adds a reveal deadline.", "Miss it and your call is flagged ducked."], "s02.png"),
  "Posting a hash first proves you called it early. But you can seal ten guesses and only reveal the one that landed. In Receipts every call has a reveal deadline, and a call that stays sealed past it is flagged as ducked on your record."),
 (shot(SHOTS / "g6.png", "s03.png", "Step 1: hash your call in the browser, nothing leaves the page"),
  "First, hash your call. The sealer page does it in your browser with a random salt, so the text never touches the chain."),
 (term(seal, "s04.png", "Live on Onyx testnet: three calls sealed, only hashes on-chain"),
  "Then seal it. These are real transactions on the Onyx testnet. Three calls sealed, each with a topic, a deadline, and only the hash."),
 (shot(SHOTS / "g2.png", "s05.png", "Sealed call: the prediction is hidden"),
  "In the app, a sealed call displays only its commitment. Nobody can read it, and the author can no longer change it."),
 (term(rev, "s06.png", "Reveal: the realm re-hashes the text and salt"),
  "To reveal, the author sends the exact text and salt. Change one word and the realm rejects it. The right text is accepted on the first try."),
 (shot(SHOTS / "g3.png", "s07.png", "Revealed and verified on-chain"),
  "Now the call is public, stamped with the block where it was sealed, and verified against its hash."),
 (term(vd, "s08.png", "Verdicts: anyone but the author"),
  "Anyone except the author can say held or missed. The author's own vote is refused. Two other accounts vote held."),
 (shot(SHOTS / "g4.png", "s09.png", "Track records: kept word, held, ducked"),
  "Each author gets a track record: how many calls were revealed on time, how many held, and how many were ducked, meaning never revealed."),
 (term(tst, "s10.png", "Unit tests: lifecycle, validation, ducked after deadline"),
  "The realm is covered by unit tests, including the ducked and late states, wrong callers, and safe page rendering."),
 (card("Receipts", ["gno.land/r/nym-receipts001/receipts", "github.com/666Crypro/receipts", "  Call it now. Prove it later."], "s11.png", "Live on the Gno.land testnet"),
  "Receipts is live on the G N O dot land testnet. The code and docs are on GitHub. Call it now, prove it later."),
]

LEAD, TAIL = 0.05, 0.1
clips = []
for i, (img, text) in enumerate(SCENES, 1):
    raw = WORK / f"n{i:02d}.wav"
    subprocess.run([PIPER, "--model", VOICE, "--output_file", str(raw), "--length_scale", "1.0"], input=text.encode(), check=True, capture_output=True)
    wav = WORK / f"p{i:02d}.wav"
    subprocess.run(["ffmpeg", "-y", "-v", "error", "-i", str(raw), "-af", f"adelay={int(LEAD*1000)}:all=1,apad=pad_dur={TAIL}", "-ar", "44100", "-ac", "1", str(wav)], check=True)
    with wave.open(str(wav)) as w: dur = w.getnframes() / w.getframerate()
    mp4 = WORK / f"c{i:02d}.mp4"
    subprocess.run(["ffmpeg", "-y", "-v", "error", "-loop", "1", "-framerate", "30", "-i", str(img), "-i", str(wav), "-t", f"{dur:.3f}",
                    "-c:v", "libx264", "-pix_fmt", "yuv420p", "-preset", "medium", "-crf", "20", "-c:a", "aac", "-b:a", "128k", "-shortest", str(mp4)], check=True)
    clips.append(mp4); print(i, round(dur, 1), "s")
lst = WORK / "list.txt"; lst.write_text("".join(f"file '{c}'\n" for c in clips))
subprocess.run(["ffmpeg", "-y", "-v", "error", "-f", "concat", "-safe", "0", "-i", str(lst), "-c", "copy", "-movflags", "+faststart", str(OUT)], check=True)
print("wrote", OUT)
