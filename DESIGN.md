---
name: Nisarg AI Design System
description: Multi-portal GIS analytics, 3D WebGL GPU maps, and AI emergency incident response system for North East India.
colors:
  bg-deep: "#06111C"
  bg-dark: "#081522"
  forest-primary: "#0B3D2E"
  forest-hover: "#0E4D39"
  accent-teal: "#1B8377"
  teal-light: "#3FB6A6"
  accent-gold: "#D4B85C"
  accent-gold-hover: "#C6AA54"
  hazard-red: "#E14D3C"
  hazard-crit: "#C22B22"
  beacon-purple: "#D946EF"
  safe-green: "#2FA36B"
  text-main: "#F1F2EE"
  text-muted: "#9BB0A9"
  glass-border: "rgba(255, 255, 255, 0.12)"
typography:
  display:
    fontFamily: "Space Grotesk, sans-serif"
    fontSize: "clamp(28px, 4.6vw, 48px)"
    fontWeight: 700
    lineHeight: 1.12
    letterSpacing: "-0.01em"
  headline:
    fontFamily: "Outfit, Inter, sans-serif"
    fontSize: "1.2rem"
    fontWeight: 700
    lineHeight: 1.2
  body:
    fontFamily: "Inter, sans-serif"
    fontSize: "14px"
    fontWeight: 400
    lineHeight: 1.5
  mono:
    fontFamily: "IBM Plex Mono, monospace"
    fontSize: "12px"
    fontWeight: 600
    letterSpacing: "0.06em"
rounded:
  sm: "8px"
  md: "12px"
  lg: "16px"
  pill: "100px"
spacing:
  sm: "8px"
  md: "16px"
  lg: "24px"
  xl: "32px"
components:
  button-gold:
    backgroundColor: "{colors.accent-gold}"
    textColor: "#0B1C18"
    rounded: "{rounded.pill}"
    padding: "14px 26px"
  button-primary:
    backgroundColor: "{colors.forest-primary}"
    textColor: "#FFFFFF"
    rounded: "{rounded.md}"
    padding: "14px 26px"
  button-danger:
    backgroundColor: "{colors.hazard-red}"
    textColor: "#FFFFFF"
    rounded: "{rounded.sm}"
    padding: "12px 18px"
  card-glass:
    backgroundColor: "rgba(15, 32, 27, 0.72)"
    textColor: "{colors.text-main}"
    rounded: "{rounded.lg}"
    padding: "24px"
---

# Design System: Nisarg AI

## Overview

**Creative North Star: "The Alpine Guardian"**

Nisarg AI fuses atmospheric mountain glass aesthetics with high-contrast emergency command-center telemetry. Built for North East India’s rugged terrain, the interface projects authoritative disaster monitoring, real-time WebGL risk scoring, and field-response capabilities across 3 unified web portals (`/`, `/proto2`, `/chatbot`).

The design language pairs deep midnight navy (`#06111C`) and alpine forest greens (`#0B3D2E`) with luminous safety accents: gold CTA highlights (`#D4B85C`), emergency hazard reds (`#E14D3C`), and pulsing purple beacons (`#D946EF`). Blur-heavy glassmorphism panels create spatial hierarchy over live map canvases without compromising operational readability.

**Key Characteristics:**
- Deep dark backdrop with radial ambient glows and subtle terrain grid overlays.
- Multi-tier glassmorphism (`backdrop-filter: blur(16px-20px)`) over 3D WebGL map layers.
- High-visibility hazard coding (Green = Safe, Amber = Warning, Red = Danger, Crimson = Critical $\ge 0.75$).
- Monospaced telemetry tags (`IBM Plex Mono`) for coordinates, EXIF tags, and risk metrics.
- Tactile emergency controls with micro-hover lift and glowing focus borders.

## Colors

The color system relies on dark, atmospheric base tones punctuated by luminous emergency signal colors.

### Primary
- **Alpine Forest** (`#0B3D2E` / `rgb(11, 61, 46)`): Core branding accent, primary buttons, and hero card structure.
- **Nisarg Gold** (`#D4B85C` / `rgb(212, 184, 92)`): High-priority action buttons, key metrics, and gold dot accents.

### Secondary
- **Teal Horizon** (`#1B8377` / `#3FB6A6`): Navigation highlights, active status badges, and interactive sliders.

### Tertiary
- **Pulsing Purple Beacon** (`#D946EF` / `rgb(217, 70, 239)`): Dynamic pinpoint marker color reserved exclusively for reported field incidents.

### Neutral
- **Midnight Deep** (`#06111C` / `#081522`): Base application and control room canvas background.
- **Glass Panel Surface** (`rgba(15, 32, 27, 0.72)` / `rgba(15, 23, 42, 0.75)`): Translucent glass containers.
- **Text Main** (`#F1F2EE`): High-legibility light body copy.
- **Text Muted** (`#9BB0A9` / `#8FA396`): Secondary metadata, captions, and labels.

### Named Rules
**The Critical Red Threshold Rule.** Pure crimson (`#C22B22`) and hazard red (`#E14D3C`) are strictly reserved for critical landslide risk ($\ge 0.75$) and emergency alert banners. Never use red for decorative UI details.

**The Beacon Exclusivity Rule.** Pulsing purple (`#D946EF`) is used solely for live user-submitted incident pins on the WebGL map to ensure zero confusion during crisis response.

## Typography

**Display Font:** `Space Grotesk` (with `sans-serif` fallback)
**Headline Font:** `Outfit` (for map headers) & `Inter`
**Body Font:** `Inter` (with system-ui fallbacks)
**Mono/Telemetry Font:** `IBM Plex Mono` (monospace)

**Character:** Technical, confident, and crisp. `Space Grotesk` delivers bold authority for titles, while `IBM Plex Mono` provides industrial precision for spatial telemetry.

### Hierarchy
- **Display** (Bold 700, `clamp(28px, 4.6vw, 48px)`, line-height 1.12): Hero headers and portal title cards.
- **Headline** (SemiBold/Bold 600–700, `16px–24px`, line-height 1.2): Section titles and card headers.
- **Title** (SemiBold 600, `15px–18px`, line-height 1.3): Control panel headers and drawer titles.
- **Body** (Regular/Medium 400–500, `14px`, line-height 1.5): Descriptive copy, instructions, and messages.
- **Label / Telemetry** (Mono 500–600, `10.5px–12px`, letter-spacing `0.06em–0.14em`, Uppercase): Risk badges, tags, coordinates, and EXIF attributes.

### Named Rules
**The Telemetry Monospace Rule.** All numerical scores, latitude/longitude coordinates, timestamps, and hazard metrics must use `IBM Plex Mono`.

## Layout

The spatial model uses responsive grid layouts and floating glass panels overlaid on a full-viewport WebGL canvas.

- **Global Wrap**: `max-width: 1280px` (Landing), `max-width: 1650px` (Chatbot split-view), full 100vh canvas (`/proto2`).
- **Connected Hero Grid**: 4-column connected card grid (`1fr 1fr 1fr .82fr`) with subtle gold border separators (`rgba(198,170,84,.16)`).
- **Floating Controls**: Left-aligned glass panel (`width: 340px` or `width: 380px`) floating above 3D map viewport.
- **Spacing Rhythm**: 8px / 16px / 24px / 32px / 48px baseline increments.

## Elevation & Depth

Nisarg AI avoids standard solid drop-shadows, using multi-layer glassmorphism, glowing borders, and backdrop blurs to establish spatial depth.

### Shadow & Glow Vocabulary
- **Glass Layer**: `backdrop-filter: blur(16px)`, `background: rgba(15, 32, 27, 0.72)`, `border: 1px solid rgba(255, 255, 255, 0.12)`.
- **Gold Hover Glow**: `box-shadow: 0 0 44px -8px rgba(212, 184, 92, 0.28)`, `border-color: rgba(212, 184, 92, 0.4)`.
- **Beacon Pulse Ring**: Keyframe animation `purple-beacon-glow` (`box-shadow: 0 0 0 32px rgba(217, 70, 239, 0), 0 0 40px rgba(217, 70, 239, 1)`).

### Named Rules
**The Layered Glass Rule.** Elevation is expressed through backdrop blur depth (`blur(12px)` to `blur(20px)`) and subtle border highlights (`rgba(255,255,255,.12)`), never flat black shadows.

## Shapes

Form language emphasizes soft rectangular containers (`12px–20px` radius) paired with fully rounded pill chips (`100px` radius).

- **Cards & Drawers**: `16px–20px` border-radius with `1px` translucent stroke.
- **Buttons**: `11px` border-radius (primary/danger) or `100px` full pill (gold CTA).
- **Tags & Badges**: `100px` pill radius with uppercase monospace text.
- **Map Beacons**: `50%` circular markers with 3px solid white borders.

## Components

### Buttons
- **Shape:** `11px` radius (standard) or `100px` pill (gold CTA).
- **Primary (Forest):** `background: #0B3D2E; color: #fff; padding: 14px 26px; box-shadow: 0 8px 24px -8px rgba(11,61,46,.55)`.
- **Gold CTA:** `background: linear-gradient(135deg, #D4B85C, #C6AA54); color: #0B1C18; font-weight: 700`.
- **Outline Glass:** `background: rgba(255,255,255,.06); border: 1px solid rgba(255,255,255,.35); backdrop-filter: blur(6px)`.

### Chips & Badges
- **Tag Style:** Monospace, `11.5px`, uppercase, `6px 12px` padding, pill shape.
- **Risk Chips:**
  - Low (`<0.25`): `background: rgba(47,163,107,.1); color: #1E7C51; border: 1px solid rgba(47,163,107,.3)`
  - Moderate (`0.25–0.50`): `background: rgba(232,162,58,.12); color: #8A5F14; border: 1px solid rgba(232,162,58,.35)`
  - High (`0.50–0.75`): `background: rgba(225,77,60,.1); color: #A6321F; border: 1px solid rgba(225,77,60,.32)`
  - Critical ($\ge 0.75$): `background: rgba(194,43,34,.12); color: #8C1B12; border: 1px solid rgba(194,43,34,.4)`

### Search Pill
- **Style:** Pill shape (`100px`), `background: rgba(15,32,27,.55)`, `backdrop-filter: blur(16px)`, `border: 1px solid rgba(255,255,255,.14)`.
- **Focus:** `border-color: rgba(76,128,106,.8); box-shadow: 0 0 0 4px rgba(76,128,106,.18)`.

### Incident Beacon
- **Style:** `26px x 26px` circle, `background: #D946EF`, `border: 3px solid #FFFFFF`.
- **Animation:** Continuous purple pulsing ring expanding up to `32px`.

## Do's and Don'ts

### Do:
- **Do** maintain translucent glass backdrop filters (`blur(16px)`) on all floating map panels and overlay drawers.
- **Do** highlight route segments with continuous risk $\ge 0.75$ in glowing red (`#E14D3C`).
- **Do** format all telemetry data (coordinates, risk scores, timestamps) in `IBM Plex Mono`.
- **Do** use gold gradient buttons (`#D4B85C`) for top-level portal actions.

### Don't:
- **Don't** use opaque solid white backgrounds on map drawers or control panels.
- **Don't** use hazard red (`#E14D3C`) for non-critical interface elements.
- **Don't** remove the pulsing animation from field incident map beacons.
- **Don't** mix non-monospace fonts in telemetry tables or coordinate readouts.
