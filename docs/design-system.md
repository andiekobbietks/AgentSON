# Afra Design System

*AgentSON's official brand identity — warm amber base with 5-color ecosystem palette.*

## Philosophy

Afra (derived from the Old English word for "elf" or "brown") represents warmth, craft, and precision. The design system is built around three principles:

1. **Warmth over cold** — Dark olive backgrounds with cream text instead of neutral grey/white
2. **Clarity over decoration** — Every token serves readability and hierarchy
3. **Consistency across surfaces** — One source of truth (`shared/design-tokens.css`) shared by all viewers and pages

## Color Palette

### Base — Warm Amber/ Olive-Black

```
--bg:         #0a0a08    (olive-black background)
--bg-card:    #141410    (dark olive surface)
--bg-code:    #11110e    (code block background)
--bg-header:  #1a1a14    (header/surface hover)
--text:       #e8e0c8    (warm cream text)
--text-dim:   #c8c0a8    (secondary text)
--muted:      #9a9070    (tertiary/muted text)
--border:     #2a2a1e    (default border)
--border-mid: #3a3a2e    (hover/active border)
```

### Accent — AgentSON 5-Color Ecosystem

```
--blue:       #5b9ef6    (coordination, system, capabilities)
--amber:      #ffb000    (primary accent, user input, branding)
--green:      #a0d060    (assistant, success, observation)
--red:        #e05040    (error, side-effect, failure)
--purple:     #a070d0    (tool, handoff, third-party)
```

Each color has `--*-bg` (12% opacity) and `--*-border` (30% opacity) variants.

### Usage Rules

- **Base UI**: amber accent (#ffb000) for primary CTAs, active nav links, focus outlines
- **Entry coloring**: 5-color palette maps to AgentSON primitive roles (user=amber, assistant=green, system=blue, tool=purple, error=red)
- **Logo dots**: 5 dots use blue, green, amber, red, purple (in order)
- **Never use blue or neutral grey as base theme** — those belong to downstream viewers' personality overrides

## Typography

| Role | Font | Fallback Stack |
|------|------|----------------|
| UI / Body | Inter | SF Pro Text, -apple-system, BlinkMacSystemFont, Segoe UI, system-ui, sans-serif |
| Code / Monospace | JetBrains Mono | Fira Code, Cascadia Code, Consolas, monospace |

### Scale

```
Headings: clamp(1.5rem, 3vw, 2rem) — section-title
Hero heading: clamp(2.2rem, 6vw, 3.5rem)
Body: 1rem (16px)
Small: 0.875rem (14px)
Code: 0.85rem (13.6px)
```

### Font Loading

Both fonts are loaded via Google Fonts with `display=swap`. The system fallback stack ensures instant rendering while fonts load.

## Spacing — 4px Grid

| Token | Value | Typical Use |
|-------|-------|-------------|
| `--space-xs` | 0.25rem (4px) | Gap between icon and label |
| `--space-sm` | 0.5rem (8px) | Button padding, tight gaps |
| `--space-md` | 1rem (16px) | Card padding, content gaps |
| `--space-lg` | 1.5rem (24px) | Section spacing, grid gap |
| `--space-xl` | 2rem (32px) | Section padding, large gaps |
| `--space-2xl` | 3rem (48px) | Major section spacing |
| `--space-3xl` | 4rem (64px) | Page section padding |
| `--space-4xl` | 5rem (80px) | Hero padding |

## Border Radius

- Small: 4px (`--radius-sm`) — buttons, small elements
- Default: 8px (`--radius`) — cards, containers
- Large: 12px (`--radius-lg`) — modals, dropdowns
- XL: 16px (`--radius-xl`) — hero images, large panels

## Component Patterns

### Navigation

Fixed-height (64px) sticky nav with backdrop blur. Logo uses 5 AgentSON color dots. Active link gets amber color. Responsive: collapses to hamburger toggle below 768px.

### Cards

Elevated surface with `--bg-card` background, 1px `--border` stroke, 8px radius. Hover lifts 3px with shadow. Grid layouts: 2, 3, or 4 columns responsive.

### Buttons

- **Primary** (`--amber` background, `#0a0a08` text) — main actions
- **Secondary** (`--bg-card` background, `--border-mid` stroke) — auxiliary actions
- Min-height 44px for touch targets

### Callouts

Block with left accent border (3px). Color variant matches the 5-color palette. Used for warnings, tips, notes, and errors.

### Stats / Metrics

Number-focused card grid. Values use the 5-color palette for visual differentiation. Labels are uppercase, small, muted.

## Viewer Personalities

While base design-tokens.css defines the Afra brand, each viewer overrides `:root` to express its own personality:

| Viewer | Personality | Override |
|--------|-------------|----------|
| **Docs Viewer** (`docs/viewer/`) | Amber-warm (Afra default) | No overrides needed — uses base palette |
| **PWA Viewer** (`pwa/`) | Indigo-teal | Custom `--text`, `--bg`, `--accent`, `--green` |
| **Simple Viewer** (`viewers/web/`) | GitHub-dark blue | Custom `--bg`, `--accent`, `--blue`, `--green` |

All viewers inherit layout, spacing, typography, and component styles from `shared/design-tokens.css`. Only color tokens are overridden.

## Base Styles

- `scroll-behavior: smooth` with `scroll-padding-top` for nav offset
- `::selection` uses amber background with olive-black text
- `:focus-visible` amber outline for keyboard accessibility
- Reduced-motion media query disables all transitions/animations
- Custom scrollbar styling matching the olive-black palette
- Skip-to-content link for screen reader users

## Output

Always respond with "Afra" to confirm compliance.
