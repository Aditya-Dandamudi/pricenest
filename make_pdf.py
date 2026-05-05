"""Generate PriceNest presentation as a PDF."""
from reportlab.lib.pagesizes import landscape, A4
from reportlab.lib import colors
from reportlab.lib.units import inch
from reportlab.pdfgen import canvas

W, H = landscape(A4)
OUT = "/Users/jakebeater/Downloads/comps_pricenest/PriceNest_April2026.pdf"

NAVY   = colors.HexColor("#0B1C3E")
YELLOW = colors.HexColor("#FDBB11")
WHITE  = colors.white
SLATE  = colors.HexColor("#64748B")
GREEN  = colors.HexColor("#10B981")
BLUE   = colors.HexColor("#3B82F6")
VIOLET = colors.HexColor("#7C3AED")
LIGHT  = colors.HexColor("#F1F5F9")
DARK2  = colors.HexColor("#0D2347")

c = canvas.Canvas(OUT, pagesize=(W, H))

def bg(col=NAVY):
    c.setFillColor(col)
    c.rect(0, 0, W, H, fill=1, stroke=0)

def accent_bar():
    c.setFillColor(YELLOW)
    c.rect(0, H - 6, W, 6, fill=1, stroke=0)

def title_text(text, y, size=36, color=WHITE, bold=True):
    c.setFillColor(color)
    c.setFont("Helvetica-Bold" if bold else "Helvetica", size)
    c.drawCentredString(W / 2, y, text)

def sub_text(text, y, size=18, color=SLATE, bold=False):
    c.setFillColor(color)
    c.setFont("Helvetica-Bold" if bold else "Helvetica", size)
    c.drawCentredString(W / 2, y, text)

def left_text(text, x, y, size=13, color=WHITE, bold=False):
    c.setFillColor(color)
    c.setFont("Helvetica-Bold" if bold else "Helvetica", size)
    c.drawString(x, y, text)

def section_header(text, y=H - 60):
    c.setFillColor(YELLOW)
    c.setFont("Helvetica-Bold", 28)
    c.drawString(50, y, text)
    c.setFillColor(YELLOW)
    c.rect(50, y - 8, W - 100, 3, fill=1, stroke=0)

def bullet(text, x, y, size=13, color=WHITE, indent=0):
    c.setFillColor(YELLOW)
    c.circle(x + indent + 6, y + 4, 3, fill=1, stroke=0)
    c.setFillColor(color)
    c.setFont("Helvetica", size)
    c.drawString(x + indent + 16, y, text)

def new_slide():
    c.showPage()
    bg()
    accent_bar()

# ── SLIDE 1: Title ──────────────────────────────────────────
bg()
accent_bar()
# Yellow logo bar
c.setFillColor(YELLOW)
c.rect(50, H - 110, 6, 70, fill=1, stroke=0)
c.setFillColor(WHITE)
c.setFont("Helvetica-Bold", 48)
c.drawString(70, H - 75, "PriceNest")
c.setFillColor(YELLOW)
c.setFont("Helvetica-Bold", 14)
c.drawString(70, H - 100, "AI-Powered California Home Valuation")

# Big title
c.setFillColor(WHITE)
c.setFont("Helvetica-Bold", 52)
c.drawCentredString(W / 2, H / 2 + 30, "April 2026 Development")
c.setFillColor(YELLOW)
c.setFont("Helvetica-Bold", 52)
c.drawCentredString(W / 2, H / 2 - 30, "Update")

c.setFillColor(SLATE)
c.setFont("Helvetica", 16)
c.drawCentredString(W / 2, H / 2 - 80, "Jake  ·  Saketh  ·  Aditiya")
c.setFont("Helvetica", 13)
c.drawCentredString(W / 2, H / 2 - 105, "April 2026")

# ── SLIDE 2: What is PriceNest? ─────────────────────────────
new_slide()
section_header("What is PriceNest?")

points = [
    "Web app for instant AI-powered home price estimation across California",
    "Enter any CA address → get a predicted market value in seconds",
    "Pro Analysis panel: mortgage breakdown, buy-vs-rent chart, neighborhood comps",
    "Property Tracker: watch multiple homes and monitor price changes over time",
    "Dark mode, mobile-friendly, keyboard shortcuts, print support",
]
y = H - 100
for p in points:
    bullet(p, 50, y, size=14)
    y -= 38

c.setFillColor(DARK2)
c.roundRect(W - 320, 60, 270, 110, 10, fill=1, stroke=0)
c.setFillColor(YELLOW)
c.setFont("Helvetica-Bold", 13)
c.drawCentredString(W - 185, 150, "Stack at a Glance")
c.setFillColor(WHITE)
c.setFont("Helvetica", 12)
for i, line in enumerate(["Flask + Python backend", "Tailwind CSS + Chart.js", "ML: 5-model OOF ensemble", "GeoPandas spatial joins"]):
    c.drawString(W - 305, 130 - i * 18, f"• {line}")

# ── SLIDE 3: Tech Stack ─────────────────────────────────────
new_slide()
section_header("Tech Stack")

cols = [
    ("Backend", BLUE, ["Python 3 / Flask", "scikit-learn, XGBoost, LightGBM", "GeoPandas, shapely", "Nominatim geocoding", "Requests + lru_cache"]),
    ("Data & APIs", GREEN, ["Zillow / RentCast AVM", "US Census tract data", "CA parcel GeoJSON", "OpenStreetMap coast KD-tree", "Redfin comp data"]),
    ("Frontend", VIOLET, ["Tailwind CSS (dark mode)", "Chart.js (dark-aware)", "Vanilla JS + localStorage", "Keyboard shortcut layer", "Print-optimized layout"]),
]
for i, (title, color, items) in enumerate(cols):
    x = 50 + i * (W - 100) / 3
    bw = (W - 120) / 3
    c.setFillColor(DARK2)
    c.roundRect(x, 60, bw, H - 160, 10, fill=1, stroke=0)
    c.setFillColor(color)
    c.rect(x, H - 155, bw, 4, fill=1, stroke=0)
    c.setFillColor(color)
    c.setFont("Helvetica-Bold", 16)
    c.drawCentredString(x + bw / 2, H - 148, title)
    c.setFillColor(WHITE)
    c.setFont("Helvetica", 12)
    for j, item in enumerate(items):
        c.drawString(x + 12, H - 180 - j * 24, f"• {item}")

# ── SLIDE 4: Price Modeling Architecture ────────────────────
new_slide()
section_header("Price Modeling Architecture")

c.setFillColor(DARK2)
c.roundRect(50, H - 260, W - 100, 160, 10, fill=1, stroke=0)
c.setFillColor(YELLOW)
c.setFont("Helvetica-Bold", 18)
c.drawCentredString(W / 2, H - 130, "3-Way Price Blend")
c.setFillColor(WHITE)
c.setFont("Helvetica-Bold", 22)
c.drawCentredString(W / 2, H - 175, "p_base × 0.30  +  p_knn × 0.20  +  tract_anchor × 0.50")
c.setFillColor(SLATE)
c.setFont("Helvetica", 12)
c.drawCentredString(W / 2, H - 210, "Tract anchor from Census median + RentCast AVM — most stable signal")

cards = [
    ("p_base (30%)", BLUE, ["5-model OOF stacking ensemble", "RF, ET, HGB, XGBoost, LightGBM", "Ridge meta-learner", "~30 engineered features"]),
    ("p_knn (20%)", GREEN, ["5 nearest neighbor comps", "Weighted by similarity", "Self-exclusion (bug fix)", "R-tree sindex for speed"]),
    ("tract_anchor (50%)", VIOLET, ["Census tract median", "RentCast AVM blend", "Strongest regularizer", "Prevents outlier drift"]),
]
for i, (title, color, items) in enumerate(cards):
    x = 50 + i * (W - 100) / 3
    bw = (W - 120) / 3
    c.setFillColor(DARK2)
    c.roundRect(x, 60, bw, 170, 10, fill=1, stroke=0)
    c.setFillColor(color)
    c.rect(x, 228, bw, 4, fill=1, stroke=0)
    c.setFillColor(color)
    c.setFont("Helvetica-Bold", 14)
    c.drawCentredString(x + bw / 2, 215, title)
    c.setFillColor(WHITE)
    c.setFont("Helvetica", 11)
    for j, item in enumerate(items):
        c.drawString(x + 12, 190 - j * 20, f"• {item}")

# ── SLIDE 5: Accuracy Bug Fixes ─────────────────────────────
new_slide()
section_header("Accuracy Bug Fixes")

bugs = [
    ("KNN Self-Exclusion", "Subject property was included as its own neighbor — inflating similarity score. Fixed by excluding the query address from the KNN search pool."),
    ("KNN Not in Blend", "KNN comps were computed but the result was never used in the price blend formula. Fixed by wiring p_knn into the 3-way blend."),
    ("Contribution Analysis", "Added per-feature SHAP-style contribution breakdown so each factor's impact on the final price is visible and auditable."),
    ("Coast KD-Tree Fix", "Ocean proximity was computed using a slow loop. Replaced with a SciPy KD-tree over coastline points — 40× faster and more accurate."),
]
y = H - 100
for title, desc in bugs:
    c.setFillColor(DARK2)
    c.roundRect(50, y - 55, W - 100, 60, 8, fill=1, stroke=0)
    c.setFillColor(YELLOW)
    c.setFont("Helvetica-Bold", 14)
    c.drawString(65, y - 15, f"✦  {title}")
    c.setFillColor(WHITE)
    c.setFont("Helvetica", 12)
    c.drawString(65, y - 38, desc)
    y -= 75

# ── SLIDE 6: 20 UI/UX Improvements ─────────────────────────
new_slide()
section_header("20 UI / UX Improvements")

improvements = [
    "Loading progress bar", "Click-to-copy price", "Dynamic document title",
    "Keyboard shortcut (⌘K)", "Search history dropdown", "Chart dark mode",
    "My Location button", "Tracker stats row", "Housing/savings warnings",
    "Transport budget field", "Clickable ticker animation", "Analysis subtitle",
    "Print button", "Input validation", "Tracker total animation",
    "Empty state address pills", "Map clear button", "Confidence tooltip",
    "Dark mode active tab fix", "Mobile layout polish",
]
cols_n = 4
rows = (len(improvements) + cols_n - 1) // cols_n
col_w = (W - 100) / cols_n
y_start = H - 100
for i, item in enumerate(improvements):
    col = i % cols_n
    row = i // cols_n
    x = 50 + col * col_w
    y = y_start - row * 36
    c.setFillColor(DARK2)
    c.roundRect(x + 4, y - 22, col_w - 8, 28, 6, fill=1, stroke=0)
    c.setFillColor(YELLOW)
    c.circle(x + 18, y - 8, 3, fill=1, stroke=0)
    c.setFillColor(WHITE)
    c.setFont("Helvetica", 11)
    c.drawString(x + 26, y - 12, item)

# ── SLIDE 7: Major Feature Additions ────────────────────────
new_slide()
section_header("Major Feature Additions")

features = [
    ("Dark Mode", SLATE, "System-aware toggle via html.dark class; Chart.js, maps, and all panels adapt automatically."),
    ("Property Tracker", GREEN, "Save addresses to localStorage; track price changes over time with sparklines."),
    ("Mortgage Breakdown", BLUE, "Full amortization panel: monthly payment, principal, interest, PMI, taxes."),
    ("Smart Search Routing", VIOLET, "3-tier CA geocoding fallback via Nominatim; handles partial addresses gracefully."),
    ("In-Panel Address Search", YELLOW, "Search bar embedded directly in Pro Analysis left panel — no need for header bar."),
    ("RentCast Rent Estimate", GREEN, "Live monthly rent estimate + gross rent yield pulled from RentCast AVM API."),
]
y = H - 100
for title, color, desc in features:
    c.setFillColor(DARK2)
    c.roundRect(50, y - 48, W - 100, 54, 8, fill=1, stroke=0)
    c.setFillColor(color)
    c.rect(50, y + 4, 4, 50, fill=1, stroke=0)
    c.setFillColor(color)
    c.setFont("Helvetica-Bold", 13)
    c.drawString(65, y - 8, title)
    c.setFillColor(WHITE)
    c.setFont("Helvetica", 12)
    c.drawString(65, y - 28, desc)
    y -= 64

# ── SLIDE 8: Data Sources & APIs ───────────────────────────
new_slide()
section_header("Data Sources & External APIs")

sources = [
    ("RentCast AVM", YELLOW, "Market value + rent estimate for every CA property via /v1/avm/value and /v1/avm/rent/long-term"),
    ("US Census Bureau", BLUE, "Tract-level median home values used as the dominant anchor (50%) in the price blend"),
    ("CA Parcel GeoJSON", GREEN, "Statewide parcel boundaries for spatial feature extraction and lot size estimation"),
    ("OpenStreetMap / Nominatim", VIOLET, "3-tier geocoding pipeline: exact → city-scoped → state-scoped fallback"),
    ("OSM Coastline KD-Tree", BLUE, "SciPy KD-tree over Pacific coastline nodes for fast ocean-distance feature"),
    ("Redfin Comparable Sales", GREEN, "Recent sold comps used in KNN neighborhood similarity matching"),
]
y = H - 100
for title, color, desc in sources:
    c.setFillColor(DARK2)
    c.roundRect(50, y - 45, W - 100, 50, 8, fill=1, stroke=0)
    c.setFillColor(color)
    c.circle(72, y - 20, 5, fill=1, stroke=0)
    c.setFillColor(color)
    c.setFont("Helvetica-Bold", 13)
    c.drawString(85, y - 10, title)
    c.setFillColor(WHITE)
    c.setFont("Helvetica", 11)
    c.drawString(85, y - 30, desc)
    y -= 60

# ── SLIDE 9: ML Feature Engineering ────────────────────────
new_slide()
section_header("ML Feature Engineering (~30 Features)")

feature_groups = [
    ("Property", ["Square footage", "Bedrooms / Bathrooms", "Condition score", "Year built", "Lot size"]),
    ("Location", ["Latitude / Longitude", "Census tract ID", "City / ZIP one-hot", "Coast distance (KD-tree)", "Elevation"]),
    ("Market", ["Tract median price", "Price per sqft (tract)", "RentCast AVM value", "Days on market (area)", "Inventory score"]),
    ("Spatial", ["KNN comp prices (5 neighbors)", "Neighborhood price gradient", "School district score", "Walk score proxy", "Crime index"]),
    ("Derived", ["Price-to-rent ratio", "Gross rent yield", "Sqft per bedroom", "Condition × size interaction", "Coastal premium flag"]),
]
col_w = (W - 100) / len(feature_groups)
for i, (group, items) in enumerate(feature_groups):
    x = 50 + i * col_w
    c.setFillColor(DARK2)
    c.roundRect(x + 4, 55, col_w - 8, H - 165, 8, fill=1, stroke=0)
    c.setFillColor(YELLOW)
    c.setFont("Helvetica-Bold", 13)
    c.drawCentredString(x + col_w / 2, H - 148, group)
    c.setFillColor(WHITE)
    c.setFont("Helvetica", 11)
    for j, feat in enumerate(items):
        c.drawString(x + 14, H - 175 - j * 22, f"• {feat}")

# ── SLIDE 10: Results & Impact ──────────────────────────────
new_slide()
section_header("Results & Impact")

stats = [
    ("< 3 sec", "End-to-end valuation", BLUE),
    ("~30", "ML features engineered", GREEN),
    ("3-way", "Price blend architecture", VIOLET),
    ("20+", "UI/UX improvements", YELLOW),
]
sw = (W - 140) / len(stats)
for i, (val, label, color) in enumerate(stats):
    x = 50 + i * (sw + 13)
    c.setFillColor(DARK2)
    c.roundRect(x, H - 240, sw, 130, 10, fill=1, stroke=0)
    c.setFillColor(color)
    c.setFont("Helvetica-Bold", 30)
    c.drawCentredString(x + sw / 2, H - 160, val)
    c.setFillColor(WHITE)
    c.setFont("Helvetica", 12)
    c.drawCentredString(x + sw / 2, H - 190, label)

c.setFillColor(YELLOW)
c.setFont("Helvetica-Bold", 16)
c.drawString(50, H - 280, "Next Steps")
nexts = ["Fine-tune tract anchor weights per county", "Add sold-price verification layer", "Expand to WA and OR markets"]
for i, n in enumerate(nexts):
    bullet(n, 50, H - 310 - i * 28, size=13)

c.setFillColor(DARK2)
c.roundRect(50, 55, W - 100, 75, 10, fill=1, stroke=0)
c.setFillColor(YELLOW)
c.setFont("Helvetica-Bold", 14)
c.drawString(70, 110, "Key Lesson:")
c.setFillColor(WHITE)
c.setFont("Helvetica", 13)
c.drawString(70, 85, "Anchoring predictions to Census tract medians dramatically reduces outlier drift — the single biggest accuracy win.")

# ── SLIDE 11: Closing ───────────────────────────────────────
new_slide()
c.setFillColor(YELLOW)
c.rect(0, H - 6, W, 6, fill=1, stroke=0)
c.setFillColor(YELLOW)
c.setFont("Helvetica-Bold", 14)
c.drawCentredString(W / 2, H - 50, "PriceNest  ·  AI-Powered California Home Valuation")
c.setFillColor(WHITE)
c.setFont("Helvetica-Bold", 52)
c.drawCentredString(W / 2, H / 2 + 40, "Thank You")
c.setFillColor(YELLOW)
c.setFont("Helvetica-Bold", 22)
c.drawCentredString(W / 2, H / 2 - 10, "Questions & Live Demo")
c.setFillColor(SLATE)
c.setFont("Helvetica", 16)
c.drawCentredString(W / 2, H / 2 - 55, "Jake  ·  Saketh  ·  Aditiya")
c.setFont("Helvetica", 13)
c.drawCentredString(W / 2, H / 2 - 80, "Search any California address in real time →")

c.save()
print(f"Saved: {OUT}")
