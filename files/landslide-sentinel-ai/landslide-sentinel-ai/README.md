# Landslide Sentinel AI — Landing Page

AI-based early warning and landslide risk monitoring landing page for the
North Eastern Region of India.

## Structure

```
landslide-sentinel-ai/
├── index.html      → markup for all 14 page sections (nav, hero, monitoring,
│                      AI risk engine, GIS map, alerts, reporting, dashboard,
│                      how-it-works, capabilities, accessibility, stats,
│                      final CTA, footer)
├── css/
│   └── style.css   → all styling: design tokens (colors/fonts as CSS
│                      variables), layout, components, responsive rules
└── js/
    └── script.js   → nav scroll state, mobile menu, scroll-reveal
                       animations, live clock, mock telemetry jitter,
                       animated stat counters, GIS map marker interactions
```

## Running it

Just open `index.html` in a browser — everything is linked with relative
paths (`css/style.css`, `js/script.js`), so the three files need to stay
in this folder layout relative to each other. No build step or server
required.

All live data (rainfall, soil moisture, risk scores, alerts, dashboard
metrics) is mock/demo data for prototyping purposes.
