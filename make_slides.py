from pptx import Presentation
from pptx.util import Inches, Pt, Emu
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN
from pptx.util import Inches, Pt
import copy

prs = Presentation()
prs.slide_width  = Inches(13.33)
prs.slide_height = Inches(7.5)

NAVY  = RGBColor(0x0B, 0x1C, 0x3E)
GOLD  = RGBColor(0xFD, 0xBB, 0x11)
WHITE = RGBColor(0xFF, 0xFF, 0xFF)
LIGHT = RGBColor(0xF8, 0xFA, 0xFC)
GRAY  = RGBColor(0x64, 0x74, 0x8B)
GREEN = RGBColor(0x10, 0xB9, 0x81)
RED   = RGBColor(0xDC, 0x26, 0x26)
BLUE  = RGBColor(0x25, 0x63, 0xEB)

BLANK = prs.slide_layouts[6]  # completely blank

# ── helpers ──────────────────────────────────────────────────────────────────

def bg(slide, color):
    fill = slide.background.fill
    fill.solid()
    fill.fore_color.rgb = color

def rect(slide, l, t, w, h, fill_color, alpha=None):
    shape = slide.shapes.add_shape(1, Inches(l), Inches(t), Inches(w), Inches(h))
    shape.line.fill.background()
    shape.fill.solid()
    shape.fill.fore_color.rgb = fill_color
    return shape

def label(slide, text, l, t, w, h, size, bold=False, color=WHITE, align=PP_ALIGN.LEFT, italic=False):
    txb = slide.shapes.add_textbox(Inches(l), Inches(t), Inches(w), Inches(h))
    tf  = txb.text_frame
    tf.word_wrap = True
    p   = tf.paragraphs[0]
    p.alignment = align
    run = p.add_run()
    run.text = text
    run.font.size  = Pt(size)
    run.font.bold  = bold
    run.font.color.rgb = color
    run.font.italic = italic
    return txb

def bullet_box(slide, items, l, t, w, h, size=16, color=NAVY, dot_color=GOLD, spacing=0.52):
    for i, item in enumerate(items):
        y = t + i * spacing
        # dot
        dot = slide.shapes.add_shape(1, Inches(l), Inches(y + 0.13), Inches(0.12), Inches(0.12))
        dot.line.fill.background()
        dot.fill.solid()
        dot.fill.fore_color.rgb = dot_color
        # text
        label(slide, item, l + 0.22, y, w - 0.22, spacing, size, color=color)

def chip(slide, text, l, t, fill=GOLD, text_color=NAVY, size=13):
    w = len(text) * 0.085 + 0.35
    r = slide.shapes.add_shape(1, Inches(l), Inches(t), Inches(w), Inches(0.33))
    r.fill.solid(); r.fill.fore_color.rgb = fill
    r.line.fill.background()
    txb = slide.shapes.add_textbox(Inches(l + 0.12), Inches(t + 0.04), Inches(w - 0.12), Inches(0.28))
    tf = txb.text_frame; p = tf.paragraphs[0]
    run = p.add_run(); run.text = text
    run.font.size = Pt(size); run.font.bold = True; run.font.color.rgb = text_color
    return w

def card(slide, l, t, w, h, fill=WHITE):
    r = slide.shapes.add_shape(1, Inches(l), Inches(t), Inches(w), Inches(h))
    r.fill.solid(); r.fill.fore_color.rgb = fill
    r.line.color.rgb = RGBColor(0xE2, 0xE8, 0xF0); r.line.width = Pt(1)
    return r

def section_header(slide, text):
    rect(slide, 0, 0, 13.33, 1.15, NAVY)
    label(slide, text, 0.5, 0.22, 12, 0.8, 32, bold=True, color=WHITE)
    rect(slide, 0, 1.15, 13.33, 0.06, GOLD)

# ── SLIDE 1 — Title ──────────────────────────────────────────────────────────
s = prs.slides.add_slide(BLANK)
bg(s, NAVY)
rect(s, 0, 5.8, 13.33, 1.7, RGBColor(0x07, 0x10, 0x22))
rect(s, 0, 5.8, 13.33, 0.07, GOLD)

label(s, "PriceNest", 1.0, 1.5, 12, 1.4, 72, bold=True, color=GOLD)
label(s, "Development Session Summary", 1.0, 3.0, 10, 0.8, 28, color=WHITE)
label(s, "Heatmap · Deployment · AI Valuation", 1.0, 3.75, 10, 0.6, 18, italic=True,
      color=RGBColor(0x94, 0xA3, 0xB8))

label(s, "Jake Beater  ·  Saketh Patibandla  ·  Aditya Dandamudi",
      1.0, 6.1, 11, 0.5, 14, color=RGBColor(0x94, 0xA3, 0xB8))
label(s, "April 2026", 1.0, 6.55, 4, 0.4, 13, color=GRAY)

# gold accent bar left
rect(s, 0, 0, 0.18, 7.5, GOLD)

# ── SLIDE 2 — Project Overview ───────────────────────────────────────────────
s = prs.slides.add_slide(BLANK)
bg(s, LIGHT)
section_header(s, "What is PriceNest?")

card(s, 0.4, 1.5, 5.8, 5.5)
label(s, "Core Purpose", 0.65, 1.65, 5.3, 0.45, 15, bold=True, color=NAVY)
bullet_box(s, [
    "AI-powered California home valuation tool",
    "Stacked ML ensemble: Random Forest + KNN meta-model",
    "Geocodes any CA address and predicts market value",
    "Interactive live map with pricing heatmap",
    "Built-in pipeline tracker and budget analyzer",
], 0.65, 2.18, 5.3, 4.5, size=14, color=NAVY)

card(s, 6.6, 1.5, 6.3, 5.5)
label(s, "Tech Stack", 6.85, 1.65, 5.8, 0.45, 15, bold=True, color=NAVY)
items = ["Flask (Python web server)", "scikit-learn (ML model)",
         "GeoPandas + Shapely (spatial data)", "Leaflet.js (interactive map)",
         "Tailwind CSS (UI)", "Nominatim (geocoding)", "Flask-Limiter (rate limiting)"]
bullet_box(s, items, 6.85, 2.18, 5.8, 4.5, size=14, color=NAVY)

# ── SLIDE 3 — Session Work Overview ─────────────────────────────────────────
s = prs.slides.add_slide(BLANK)
bg(s, LIGHT)
section_header(s, "What We Built This Session")

topics = [
    ("1", "Environment Setup",      "Installed all Python dependencies and got the Flask app running"),
    ("2", "Live Map Heatmap",       "Built a smooth heat-blur overlay using training dataset"),
    ("3", "Hexagon Heatmap",        "Replaced blur with precise, clickable hexagonal grid"),
    ("4", "Deployment Hardening",   "Fixed security issues and prepared for production"),
]
cols = [(0.35, 6.0), (6.85, 6.0)]
for i, (num, title, desc) in enumerate(topics):
    col = i % 2
    row = i // 2
    lx = cols[col][0]
    ty = 1.5 + row * 2.8
    card(s, lx, ty, 6.0, 2.4)
    rect(s, lx, ty, 0.55, 2.4, NAVY)
    label(s, num, lx + 0.08, ty + 0.7, 0.4, 0.9, 26, bold=True, color=GOLD, align=PP_ALIGN.CENTER)
    label(s, title, lx + 0.72, ty + 0.18, 5.1, 0.45, 15, bold=True, color=NAVY)
    label(s, desc,  lx + 0.72, ty + 0.7,  5.1, 1.4,  13, color=GRAY)

# ── SLIDE 4 — Environment Setup ──────────────────────────────────────────────
s = prs.slides.add_slide(BLANK)
bg(s, LIGHT)
section_header(s, "Environment Setup")

card(s, 0.4, 1.4, 7.5, 5.7)
label(s, "Packages Installed", 0.65, 1.55, 7, 0.4, 15, bold=True, color=NAVY)
pkgs = ["flask", "scikit-learn", "geopandas", "shapely",
        "geopy", "pandas", "numpy", "requests",
        "joblib", "flask-limiter", "python-dotenv", "gunicorn"]
for i, p in enumerate(pkgs):
    row, col = divmod(i, 2)
    lx = 0.72 + col * 3.55
    ty = 2.1 + row * 0.58
    chip(s, p, lx, ty)

card(s, 8.3, 1.4, 4.65, 2.6)
label(s, "Python Version", 8.55, 1.55, 4.2, 0.4, 15, bold=True, color=NAVY)
bullet_box(s, [
    "Python 3.9.6 (system)",
    "pip via python3 -m pip",
    "User-level install path",
], 8.55, 2.05, 4.2, 2.0, size=14, color=NAVY, spacing=0.55)

card(s, 8.3, 4.2, 4.65, 2.9)
label(s, "How to Run", 8.55, 4.35, 4.2, 0.4, 15, bold=True, color=NAVY)
bullet_box(s, [
    "Dev:  python3 app.py",
    "Prod: gunicorn -w 2 app:app",
    "URL:  http://127.0.0.1:8000",
], 8.55, 4.85, 4.2, 2.0, size=13, color=NAVY, spacing=0.58)

# ── SLIDE 5 — Heatmap v1 (blur) ──────────────────────────────────────────────
s = prs.slides.add_slide(BLANK)
bg(s, LIGHT)
section_header(s, "Heatmap Feature — Phase 1: Heat Blur")

card(s, 0.4, 1.4, 5.8, 5.7)
label(s, "Implementation", 0.65, 1.55, 5.3, 0.4, 15, bold=True, color=NAVY)
bullet_box(s, [
    "Added Leaflet.heat plugin",
    "Flask route /heatmap-data",
    "8,766 CA census tract centroids",
    "Intensities normalized to price",
    "Toggle button on Live Map tab",
    "Gradient: Blue → Cyan → Green → Yellow → Red",
], 0.65, 2.05, 5.3, 5.0, size=14, color=NAVY)

card(s, 6.6, 1.4, 6.3, 2.6)
label(s, "Problems Found", 6.85, 1.55, 5.8, 0.4, 15, bold=True, color=NAVY)
bullet_box(s, [
    "Only half of CA showed gradient",
    "Rural low-price areas invisible (intensity ≈ 0)",
    "Linear normalization $21K–$2M caused gaps",
], 6.85, 2.05, 5.8, 2.5, size=14, color=RED, dot_color=RED)

card(s, 6.6, 4.2, 6.3, 2.9)
label(s, "Fixes Applied", 6.85, 4.35, 5.8, 0.4, 15, bold=True, color=NAVY)
bullet_box(s, [
    "Switched to percentile normalization (p10–p90)",
    "All tracts guaranteed intensity ≥ 0.05",
    "minOpacity raised to 0.55",
    "Dense point sampling: up to 80 pts per tract",
], 6.85, 4.85, 5.8, 2.5, size=14, color=GREEN, dot_color=GREEN)

# ── SLIDE 6 — Heatmap v2 (hex) ───────────────────────────────────────────────
s = prs.slides.add_slide(BLANK)
bg(s, LIGHT)
section_header(s, "Heatmap Feature — Phase 2: Hexagon Grid")

card(s, 0.4, 1.4, 7.8, 5.7)
label(s, "How It Works", 0.65, 1.55, 7.3, 0.4, 15, bold=True, color=NAVY)
bullet_box(s, [
    "Pointy-top hexagonal grid, 0.08° circumradius (~9 km per hex)",
    "Grid spans full California bounding box",
    "Each hex centroid spatially joined to nearest census tract",
    "Price mapped to color via 5-stop gradient ($300K → $5M+)",
    "Rendered as L.geoJSON layer — not a blur overlay",
    "Click any hexagon → popup shows median home value",
    "Hover highlights hex in white with increased opacity",
    "Toggle button: yellow when active, glass when off",
    "Legend panel: gradient bar + color swatch key",
], 0.65, 2.05, 7.4, 5.0, size=14, color=NAVY)

card(s, 8.6, 1.4, 4.35, 2.5)
label(s, "Color Scale", 8.85, 1.55, 3.9, 0.4, 15, bold=True, color=NAVY)
color_items = [
    (BLUE,  "$300K and under"),
    (RGBColor(0x06,0xB6,0xD4), "$300K – $1M"),
    (GREEN, "$1M – $2M"),
    (RGBColor(0xF5,0x9E,0x0B), "$2M – $3.5M"),
    (RED,   "$3.5M – $5M+"),
]
for i, (clr, lbl) in enumerate(color_items):
    ty = 2.05 + i * 0.42
    dot = s.shapes.add_shape(1, Inches(8.85), Inches(ty + 0.08), Inches(0.22), Inches(0.22))
    dot.fill.solid(); dot.fill.fore_color.rgb = clr; dot.line.fill.background()
    label(s, lbl, 9.18, ty, 3.5, 0.38, 13, color=NAVY)

card(s, 8.6, 4.1, 4.35, 3.0)
label(s, "Technical Stats", 8.85, 4.25, 3.9, 0.4, 15, bold=True, color=NAVY)
bullet_box(s, [
    "~3,200 hexagons over California",
    "8,766 census tracts as source data",
    "GeoJSON served via /heatmap-data",
    "Cached at server startup",
], 8.85, 4.75, 3.9, 2.5, size=14, color=NAVY)

# ── SLIDE 7 — Deployment ─────────────────────────────────────────────────────
s = prs.slides.add_slide(BLANK)
bg(s, LIGHT)
section_header(s, "Deployment Hardening")

issues = [
    (RED,   "FIXED",  "API Key Hardcoded",
     "Key was in source code\nMoved to .env via python-dotenv\nNever committed to git"),
    (RED,   "FIXED",  "Debug Mode On",
     "debug=True exposed stack traces\nSet to debug=False for production"),
    (RED,   "FIXED",  "No Rate Limiting",
     "Predict endpoint open to abuse\n10 req/min per IP via Flask-Limiter\nGlobal: 200/day, 60/hr"),
    (RED,   "FIXED",  "sklearn Version Mismatch",
     "Model trained on 1.8.0, running 1.6.1\nRetrained on current version\nR² = 0.79, MAE = $134K"),
    (RED,   "FIXED",  "No requirements.txt",
     "No reproducible installs\nAll 12 packages pinned by version"),
    (RED,   "FIXED",  "Dev Server in Production",
     "Flask dev server is single-threaded\nGunicorn installed for prod use\ngunicorn -w 2 app:app"),
]

for i, (badge_color, badge, title, desc) in enumerate(issues):
    col = i % 2
    row = i // 2
    lx = 0.35 + col * 6.55
    ty = 1.45 + row * 2.0
    card(s, lx, ty, 6.1, 1.85)
    chip(s, badge, lx + 0.18, ty + 0.18, fill=GREEN, text_color=WHITE, size=11)
    label(s, title, lx + 1.2, ty + 0.15, 4.7, 0.42, 14, bold=True, color=NAVY)
    label(s, desc,  lx + 0.22, ty + 0.62, 5.7, 1.1,  12, color=GRAY)

# ── SLIDE 8 — Model Performance ──────────────────────────────────────────────
s = prs.slides.add_slide(BLANK)
bg(s, LIGHT)
section_header(s, "AI Model — Retrained & Validated")

card(s, 0.4, 1.4, 5.8, 5.7)
label(s, "Training Pipeline", 0.65, 1.55, 5.3, 0.4, 15, bold=True, color=NAVY)
bullet_box(s, [
    "Dataset: 8,766 CA census tracts (GeoJSON)",
    "Outlier removal: bottom 1% and top 1% stripped",
    "Price range after cleaning: $154K – $2M",
    "80% train / 20% test split (random_state=42)",
    "Algorithm: Random Forest (200 trees, depth 15)",
    "Training uses all CPU cores (n_jobs=-1)",
], 0.65, 2.05, 5.3, 4.8, size=14, color=NAVY)

card(s, 6.6, 1.4, 3.0, 5.7)
label(s, "Performance", 6.85, 1.55, 2.6, 0.4, 15, bold=True, color=NAVY)
metrics = [("R² Score", "0.79"), ("MAE", "$134K"), ("Trees", "200"), ("Features", "10")]
for i, (name, val) in enumerate(metrics):
    ty = 2.15 + i * 1.2
    rect(s, 6.75, ty, 2.8, 1.0, NAVY)
    label(s, val,  6.75, ty + 0.08, 2.8, 0.55, 26, bold=True, color=GOLD, align=PP_ALIGN.CENTER)
    label(s, name, 6.75, ty + 0.6,  2.8, 0.35, 11, color=RGBColor(0x94,0xA3,0xB8), align=PP_ALIGN.CENTER)

card(s, 9.95, 1.4, 2.95, 5.7)
label(s, "Feature Set", 10.2, 1.55, 2.6, 0.4, 15, bold=True, color=NAVY)
feats = ["median_income", "median_house_age", "population",
         "housing_units", "pop_density", "dist_coast_km",
         "dist_city_km", "income_per_age*", "persons_per_unit*", "relative_density*"]
bullet_box(s, feats, 10.2, 2.05, 2.6, 4.8, size=12, color=NAVY, spacing=0.5)
label(s, "* engineered features", 10.2, 6.7, 2.6, 0.3, 10, italic=True, color=GRAY)

# ── SLIDE 9 — Files Created / Modified ───────────────────────────────────────
s = prs.slides.add_slide(BLANK)
bg(s, LIGHT)
section_header(s, "Files Created & Modified")

files = [
    ("MODIFIED", "app.py",               "Added hex grid, rate limiting, env vars, debug off"),
    ("MODIFIED", "templates/index.html", "Hex GeoJSON layer, toggle button, legend, popup styles"),
    ("RETRAINED","price_nest_model.joblib","Rebuilt on sklearn 1.6.1 — eliminates version warnings"),
    ("RETRAINED","model_features.joblib", "Feature list saved alongside model"),
    ("NEW",      ".env",                  "Stores RENTCAST_API_KEY — never committed to git"),
    ("NEW",      ".env.example",          "Template so collaborators know required env vars"),
    ("NEW",      ".gitignore",            "Excludes .env, __pycache__, *.joblib from version control"),
    ("NEW",      "requirements.txt",      "All 12 packages pinned to exact versions"),
    ("NEW",      "make_slides.py",        "This presentation — auto-generated via python-pptx"),
]

badge_colors = {"MODIFIED": RGBColor(0x25,0x63,0xEB), "NEW": GREEN, "RETRAINED": RGBColor(0xF5,0x9E,0x0B)}

for i, (badge, fname, desc) in enumerate(files):
    ty = 1.5 + i * 0.62
    card(s, 0.4, ty, 12.55, 0.56)
    clr = badge_colors.get(badge, NAVY)
    chip(s, badge, 0.58, ty + 0.12, fill=clr, text_color=WHITE, size=10)
    bw = len(badge) * 0.085 + 0.35
    label(s, fname, 0.58 + bw + 0.18, ty + 0.1, 3.2, 0.38, 13, bold=True, color=NAVY)
    label(s, desc,  4.8, ty + 0.1, 8.0, 0.38, 12, color=GRAY)

# ── SLIDE 10 — Next Steps ─────────────────────────────────────────────────────
s = prs.slides.add_slide(BLANK)
bg(s, NAVY)
rect(s, 0, 0, 0.18, 7.5, GOLD)
rect(s, 0, 6.8, 13.33, 0.7, RGBColor(0x07, 0x10, 0x22))

label(s, "Next Steps", 0.5, 0.4, 12, 0.9, 38, bold=True, color=WHITE)
rect(s, 0.5, 1.35, 1.8, 0.06, GOLD)

next_steps = [
    ("Geocoding",    "Replace Nominatim with Google Maps or Mapbox API for production-grade geocoding"),
    ("Expand Data",  "Add nationwide dataset (Census ACS) to cover all 50 states"),
    ("Hosting",      "Deploy to a cloud platform — Render, Railway, or AWS Elastic Beanstalk"),
    ("HTTPS",        "Add TLS certificate (Let's Encrypt) before going public"),
    ("Auth",         "Add user accounts so clients can save and revisit their valuations"),
    ("Mobile",       "Optimize responsive layout for iPhone and Android browsers"),
]

for i, (tag, text) in enumerate(next_steps):
    col = i % 2
    row = i // 2
    lx = 0.5 + col * 6.45
    ty = 1.6 + row * 1.6
    rect(s, lx, ty, 6.0, 1.42, RGBColor(0x13, 0x2A, 0x5E))
    rect(s, lx, ty, 6.0, 0.06, GOLD)
    label(s, tag,  lx + 0.22, ty + 0.15, 5.6, 0.38, 14, bold=True, color=GOLD)
    label(s, text, lx + 0.22, ty + 0.55, 5.6, 0.75, 13, color=RGBColor(0xCB, 0xD5, 0xE1))

label(s, "PriceNest  ·  April 2026", 0.5, 6.88, 12, 0.4, 12,
      color=RGBColor(0x64, 0x74, 0x8B), align=PP_ALIGN.CENTER)

# ── Save ─────────────────────────────────────────────────────────────────────
out = "PriceNest_Session_Summary.pptx"
prs.save(out)
print(f"Saved: {out}")
