# **AI Tutor UI Style & Theming Guide**
_Evocative of the Young Lady’s Illustrated Primer (Neal Stephenson) — “neo‑Victorian minimalism.”_

> Goal: keep the app fast and modern while hinting at illuminated manuscripts, brass mechanisms, and fine paper. Use off‑the‑shelf assets. This guide defines tokens, components, motion, and platform notes for **Qt (PySide6)** and **Web (Tauri/React)**.

---

## 1) Brand Attributes
- **Tone:** patient, erudite, just a touch whimsical.
- **Aesthetic:** **parchment + brass + ink**, with teal/verdigris accents.
- **Density:** medium; generous line-heights; comfortable reading.
- **Texture:** subtle paper grain and micro-engraving* motifs (never busy).

> *Motifs = faint SVG corner filigree, not full frames.

---

## 2) Color System
Use the same semantic tokens in Light and Dark themes.

### Palette
| Token | Light | Dark | Usage |
|---|---|---|---|
| `--ink-900` | #111216 | #F5F6F8 | Primary text (“ink”) |
| `--parchment-50` | #F8F5EC | #0F0F0D | App background |
| `--parchment-100` | #F1EAD5 | #151512 | Surfaces |
| `--brass-600` | #B08D57 | #DBB976 | Accents, borders |
| `--verdigris-500` | #2A8F8A | #63C0B9 | Links, active states |
| `--navy-700` | #1F2C44 | #A7B7D3 | Emphasis backgrounds |
| `--garnet-600` | #8F1D2C | #D46570 | Destructive |
| `--smoke-300` | #D8D5CC | #49453F | Dividers |
| `--shadow` | rgba(20,18,16,.18) | rgba(0,0,0,.35) | Shadows |

### Example CSS variables (Web)
```css
:root {
  --ink-900:#111216; --parchment-50:#F8F5EC; --parchment-100:#F1EAD5;
  --brass-600:#B08D57; --verdigris-500:#2A8F8A; --navy-700:#1F2C44;
  --garnet-600:#8F1D2C; --smoke-300:#D8D5CC; --shadow:0 6px 18px rgba(20,18,16,.18);
}
[data-theme="dark"] {
  --ink-900:#F5F6F8; --parchment-50:#0F0F0D; --parchment-100:#151512;
  --brass-600:#DBB976; --verdigris-500:#63C0B9; --navy-700:#A7B7D3;
  --garnet-600:#D46570; --smoke-300:#49453F; --shadow:0 8px 22px rgba(0,0,0,.35);
}
```

### Qt (stylesheet) equivalents
```css
/* Assign via QPalette or style sheet */
QWidget { background: #F8F5EC; color: #111216; }
QFrame#Card { background: #F1EAD5; border: 1px solid #B08D57; border-radius: 12px; }
```

---

## 3) Typography
**Headlines (bookish serif with small caps):**
- Primary: **Spectral SC** (or IM Fell English SC for more “Primer” flavor); Fallbacks: "Spectral SC","IM Fell English SC","Georgia",serif.
- Weights: 400, 600.

**Body (high legibility serif):**
- **Source Serif 4** (or “Literata”); Fallbacks: "Source Serif 4","Georgia",serif.
- Size: 16–18px base (line-height 1.6).

**Mono (code/IDs):** **JetBrains Mono**, 13–14px.

**Micro-patterns**
- Use **small caps** for overlines/section labels.
- First paragraph in panels may use a **drop cap** (1–2 lines).

**Web example**
```html
<link href="https://fonts.googleapis.com/css2?family=Spectral+SC:wght@400;600&family=Source+Serif+4:opsz,wght@8..60,400;8..60,600&family=JetBrains+Mono:wght@400;600&display=swap" rel="stylesheet">
```

---

## 4) Spacing, Radius, Elevation
- **Spacing scale:** 4, 8, 12, 16, 24, 32, 48.
- **Radius:** 12px default, 20px for “feature” cards.
- **Shadows:** 0 1px 0 rgba(176,141,87,.35) **inner** (bevel hint) + var(--shadow) for elevation.
- **Borders:** 1px brass (`--brass-600`) on cards, 2px on interactive focus.

---

## 5) Iconography & Illustrations
- **Icons:** **Lucide** or **Phosphor** (thin weight). Tint to `--brass-600` on idle, `--verdigris-500` on hover.
- **Motifs:** Optional corner SVG filigree at 6–10% opacity on major panels. Keep subtle.
- **Status glyphs:** 
  - Success: verdigris ring.
  - Warning: brass dot/stripe.
  - Error: garnet underline (not full red fills).

---

## 6) Component Patterns

### 6.1 Card (base surface)
**Use for:** chat bubbles, summaries, graph tooltips.
```css
.card {
  background: var(--parchment-100);
  border: 1px solid var(--brass-600);
  border-radius: 12px;
  box-shadow: var(--shadow);
  padding: 16px;
}
.card--subtle { background: color-mix(in srgb, var(--parchment-100) 80%, white); }
```

### 6.2 Button
- Default: parchment fill, brass border, ink text.
- Hover: lighten background + brass glow.
- Focus: 2px verdigris outline (inside).
```css
.button {
  border:1px solid var(--brass-600); border-radius:12px; padding:8px 14px;
  background: var(--parchment-100); color: var(--ink-900);
  transition: transform .12s ease, box-shadow .2s ease;
}
.button:hover { transform: translateY(-1px); box-shadow: 0 4px 10px rgba(176,141,87,.25); }
.button:active { transform: translateY(0); }
.button--primary { background: var(--verdigris-500); color:white; border-color: transparent; }
.button--danger { background: color-mix(in srgb, var(--garnet-600) 92%, black); color:white; }
```

### 6.3 Input / Select
- Brass border, 12px radius, parchment fill. Focus outline verdigris.
```css
.input {
  background: var(--parchment-100); border:1px solid var(--smoke-300);
  border-radius:12px; padding:10px 12px;
}
.input:focus { outline:2px solid var(--verdigris-500); outline-offset:0; border-color: var(--brass-600); }
```

### 6.4 Tabs
- Underline indicator in brass; active tab text slightly larger (1.02x).
- In dark mode, use verdigris underline.

### 6.5 Tooltip (hover card)
- Use `.card` + 12px padding; arrow triangle 8px; max-width 360px.

### 6.6 Chat
- **AI bubble:** parchment card + left filigree stripe (2px brass at 20% opacity).
- **User bubble:** navy background (`--navy-700`) with ink‑on‑navy text set to white at 92% opacity.
- **Context pane:** list of snippet chips (brass border, condensed font).

### 6.7 Panels: Command Console / Inspector
- Two-column layout: list on left (256–320px), detail on right.
- Detail uses `.card` with optional drop‑cap first paragraph.

---

## 7) Knowledge Tree Styling (Cytoscape)
**Node shapes:**
- Topic = rounded rectangle; Skill = circle; Artifact = hexagon.
- Size by centrality or evidence count.

**Colors:**
- Topic fill: parchment; border: brass.
- Skill fill: white; ring shows `p_mastery`:  
  - 0–0.4: garnet ring  
  - 0.4–0.7: brass ring  
  - 0.7–1.0: verdigris ring
- Artifact fill: pale navy.

**Edges:**
- `contains` = brass solid 1.5px.
- `prereq` = navy dashed 2px with arrow.
- `applies_in` = verdigris dotted 1.5px.

**Cytoscape snippet**
```js
const style = [
  { selector: 'node[type="topic"]', style: {
      'shape':'round-rectangle', 'background-color':'#F1EAD5', 'border-color':'#B08D57', 'border-width':1.5,
      'label':'data(label)', 'font-family':'"Source Serif 4","Georgia",serif', 'font-size':14, 'text-wrap':'wrap', 'text-max-width':120
  }},
  { selector: 'node[type="skill"]', style: {
      'shape':'ellipse', 'background-color':'#FFFFFF', 'border-color':'#B08D57', 'border-width':1,
      'label':'data(label)'
  }},
  { selector: 'node[type="artifact"]', style: {
      'shape':'hexagon', 'background-color':'#E6EAF4', 'border-color':'#1F2C44', 'border-width':1,
      'label':'data(label)'
  }},
  { selector: 'edge[rel="contains"]', style: { 'line-color':'#B08D57', 'width':1.5 } },
  { selector: 'edge[rel="prereq"]', style: { 'line-color':'#1F2C44', 'width':2, 'line-style':'dashed', 'target-arrow-shape':'triangle', 'target-arrow-color':'#1F2C44' } },
  { selector: 'edge[rel="applies_in"]', style: { 'line-color':'#2A8F8A', 'width':1.5, 'line-style':'dotted' } },
  // mastery ring
  { selector: 'node[type="skill"][p_mastery < 0.4]', style: { 'border-color':'#8F1D2C', 'border-width':3 } },
  { selector: 'node[type="skill"][p_mastery >= 0.7]', style: { 'border-color':'#2A8F8A', 'border-width':3 } },
];
```

**Layout**: ELK/Dagre for hierarchy; physics (COSE) for mixed graphs. Use animated pan/zoom 120–180ms.

**Hover**: Debounce 150–200ms; use Tooltip `.card` with title + 2–3 stats + “Open in Inspector” link.

---

## 8) Motion & Feedback
- **Durations:** 120–200ms (enter/exit), 240ms for overlays.
- **Easing:** `cubic-bezier(0.2, 0.0, 0.2, 1)` (standard material-ish) or `easeOutCubic`.
- **Micro‑interactions:** brass glow on hover, subtle lift (translateY(-1px)).
- **No parallax** in core content (OK for hero/empty states only).

---

## 9) Accessibility
- Contrast AA minimum (prefer AAA for body text).
- Focus outlines: **verdigris** 2px, offset 2px.
- All filigree purely decorative (aria-hidden).
- Motion‑reduced mode: disable lifts/glows; keep color changes.

---

## 10) Theming Tokens (Tailwind optional)
```js
// tailwind.config.js (excerpt)
theme: {
  extend: {
    colors: {
      ink: { 900: '#111216' },
      parchment: { 50:'#F8F5EC', 100:'#F1EAD5' },
      brass: { 600:'#B08D57' },
      verdigris: { 500:'#2A8F8A' },
      navy: { 700:'#1F2C44' },
      garnet: { 600:'#8F1D2C' }
    },
    borderRadius: { xl:'12px', '2xl':'20px' },
    boxShadow: {
      brass: '0 6px 18px rgba(20,18,16,.18)',
    },
  }
}
```

---

## 11) Qt Notes (PySide6)
- Use **QPropertyAnimation** for fades (120ms).
- Prefer **QSplitter** with handle styled as thin brass line.
- Common card: `QFrame#Card` with brass border + radius 12.
- WebEngine for Knowledge Tree; bridge fonts via `QFontDatabase.addApplicationFont()`.

---

## 12) Sample Screens

**Tutor Chat**
- Left: message stack of `.card` bubbles.
- Right: Context pane with snippet chips and “Sources” list.
- Footer: input, Send (primary/verdigris), “/commands” hint.

**Command Console**
- Toolbar: DB, Index, AI groups (buttons).
- Body: result table in `.card`, JSON view toggle.
- Footer: status + last run time.

**Knowledge Tree**
- Full-width canvas; search box top-left.
- Hover card at pointer; click → Inspector (right tab).

---

## 13) Voice & Microcopy
- **Encouraging, precise, concise.**
- Examples:  
  - “Let’s revisit chain rule—three quick checks.”  
  - “Indexed 1,204 chunks. Fresh as of today.”  
  - “No worries—I saved your session and queued a review.”

---

## 14) Assets (off‑the‑shelf)
- Fonts: Spectral SC, Source Serif 4, JetBrains Mono (Google Fonts).
- Icons: Lucide or Phosphor.
- SVG filigree: search “corner filigree svg” (thin-line), reduce opacity to 6–10%.
- Paper textures: subtle, tileable (e.g., 2–4% overlay multiply).

---

## 15) Do/Don’t
**Do**
- Keep surfaces light and airy; use brass sparingly.
- Limit textures to 1 per view.
- Keep hover tooltips compact and responsive.

**Don’t**
- Full ornamental frames.
- Heavy drop shadows or saturated reds.
- Low-contrast text on parchment backgrounds.

---

## 16) Ready‑to‑Paste Snippets

### Web Chat Bubble
```css
.chat-ai { composes: card; border-left: 3px solid rgba(176,141,87,.45); }
.chat-user { background:#1F2C44; color:#fff; border-color:#1F2C44; }
```

### Qt Card
```css
QFrame#Card {
  background:#F1EAD5; border:1px solid #B08D57; border-radius:12px;
  box-shadow: 0 6px 18px rgba(20,18,16,.18);
}
QPushButton#Primary { background:#2A8F8A; color:white; border:0; border-radius:12px; padding:8px 14px; }
QPushButton#Primary:hover { box-shadow: 0 4px 10px rgba(42,143,138,.35); }
```

---

### Final Notes
- Favor **readability** over decoration. The “Primer” feeling should come from **material hints** (paper, brass, verdigris), **not** literal Victorian UI.  
- Keep components swappable between Qt and Web with the same tokens.
