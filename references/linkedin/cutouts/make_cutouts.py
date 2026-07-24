#!/usr/bin/env python3
"""Master-Cutouts der 4 Gruender aus den Greenscreen-Originalen.

Quelle: ~/Desktop/Automatisierbar/automatisierbar bilder/IMG_{3256,3258,3263,3264}.JPG
Output: <name>-natural.png (Cutout, echte Farben) + <name>-duotone.png (Banner-Grade)
Regel: Fuer ALLE kuenftigen Banner/Karten/Posts DIESE Master verwenden, nie neu keyen.
Run: .venv/bin/python3 references/linkedin/cutouts/make_cutouts.py
"""
import numpy as np
from PIL import Image, ImageFilter
import os

SRC = os.path.expanduser("~/Desktop/Automatisierbar/automatisierbar bilder/")
OUT = os.path.dirname(os.path.abspath(__file__))

# safe crop inside the greenscreen (x0,y0,x1,y1) on the 90deg-CCW-rotated frame (2848x4272)
CROPS = {
  "tej":     ("IMG_3256.JPG", (0,   700, 2400, 4272)),
  "nico":    ("IMG_3258.JPG", (0,   640, 2848, 4272)),
  "patrik":  ("IMG_3263.JPG", (0,   580, 2780, 4272)),
  "joaquin": ("IMG_3264.JPG", (60,  900, 2820, 4272)),
}

def bottom_connected(solid):
    small = Image.fromarray((solid*255).astype(np.uint8)).resize(
        (solid.shape[1]//8, solid.shape[0]//8), Image.NEAREST)
    m = np.array(small) > 0
    seed = np.zeros_like(m); seed[-1,:] = m[-1,:]
    prev = 0
    while True:
        grown = seed.copy()
        grown[:-1,:] |= seed[1:,:]; grown[1:,:] |= seed[:-1,:]
        grown[:,:-1] |= seed[:,1:]; grown[:,1:] |= seed[:,:-1]
        seed = grown & m
        s = seed.sum()
        if s == prev: break
        prev = s
    up = Image.fromarray((seed*255).astype(np.uint8)).resize(
        (solid.shape[1], solid.shape[0]), Image.NEAREST)
    return np.array(up.filter(ImageFilter.MaxFilter(31))) > 0

def duotone(rgb):
    L = (0.299*rgb[...,0] + 0.587*rgb[...,1] + 0.114*rgb[...,2]) / 255
    L = np.clip(L**1.06, 0, 1)
    shadow = np.array([9,16,13], float); highlight = np.array([242,243,236], float)
    out = shadow[None,None,:] + (highlight-shadow)[None,None,:] * L[...,None]
    out[...,1] += 10*np.sin(np.pi*L)
    return np.clip(out, 0, 255)

for name,(f,(x0,y0,x1,y1)) in CROPS.items():
    im = Image.open(SRC+f).transpose(Image.ROTATE_90).crop((x0,y0,x1,y1))
    a = np.asarray(im).astype(float)
    r,g,b = a[...,0], a[...,1], a[...,2]
    d = g - np.maximum(r,b)
    t0,t1 = 8.0, 45.0
    alpha = np.clip((t1 - d)/(t1 - t0), 0, 1) * 255
    g2 = np.minimum(g, np.maximum(r,b))
    rgb = np.stack([r,g2,b], axis=-1)
    # keep only the figure (connected to bottom), zero residual haze
    keep = bottom_connected(alpha > 160)
    alpha[~keep] = 0
    alpha[alpha < 12] = 0
    # smooth ramp stays (NO hard floor, NO erosion) -> natural edges; light AA blur
    alpha = np.array(Image.fromarray(alpha.astype(np.uint8)).filter(ImageFilter.GaussianBlur(1.2)), float)
    alpha[~keep] = 0
    ys,xs = np.where(alpha > 10)
    yA = max(0, ys.min()-30); xA = max(0, xs.min()-30); xB = min(alpha.shape[1]-1, xs.max()+30)
    nat = np.dstack([rgb, alpha]).astype(np.uint8)[yA:, xA:xB+1]
    duo = np.dstack([duotone(rgb), alpha]).astype(np.uint8)[yA:, xA:xB+1]
    for arr, suffix in [(nat,"natural"), (duo,"duotone")]:
        img = Image.fromarray(arr)
        if img.height > 2400:
            sc = 2400/img.height
            img = img.resize((int(img.width*sc), 2400), Image.LANCZOS)
        img.save(os.path.join(OUT, f"{name}-{suffix}.png"))
    print(name, "->", img.size)

# --- Tej: Tommy-Hilfiger-Print entfernen (Marken-Verbot auf Karten) ---
def remove_print(path):
    im = Image.open(path)
    a = np.array(im)
    h,w = a.shape[:2]
    lum = a[...,:3].astype(float).mean(axis=2)
    m = np.zeros((h,w), bool)
    # Print sitzt auf der Brust: mittleres Drittel, ~36-56% der Hoehe (NICHT tiefer — dort sind die Unterarme)
    m[int(h*0.36):int(h*0.58), int(w*0.14):int(w*0.86)] = True
    pm = m & (a[...,3]>150) & (lum>36)
    if pm.sum() == 0: return
    pm = np.array(Image.fromarray((pm*255).astype(np.uint8)).filter(ImageFilter.MaxFilter(17))) > 0
    shirt = m & (a[...,3]>150) & (lum<=35) & ~pm
    med = np.median(a[shirt][:,:3], axis=0)
    rng = np.random.default_rng(7)
    a[pm,:3] = np.clip(med + rng.normal(0,3.5,(pm.sum(),3)), 0, 255).astype(np.uint8)
    im2 = Image.fromarray(a)
    ys,xs = np.where(pm)
    y0,y1,x0,x1 = ys.min(),ys.max(),xs.min(),xs.max()
    box = im2.crop((x0-10,y0-10,x1+10,y1+10)).filter(ImageFilter.GaussianBlur(3))
    mask = Image.fromarray((pm*255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(2)).crop((x0-10,y0-10,x1+10,y1+10))
    im2.paste(box, (x0-10,y0-10), mask)
    im2.save(path)
    print("print removed:", path, pm.sum(), "px")

for s in ["natural","duotone"]:
    remove_print(os.path.join(OUT, f"tej-{s}.png"))
