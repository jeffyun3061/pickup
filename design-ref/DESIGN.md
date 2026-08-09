---
name: Project Neon-Tactical
colors:
  surface: '#131314'
  surface-dim: '#131314'
  surface-bright: '#39393a'
  surface-container-lowest: '#0e0e0f'
  surface-container-low: '#1c1b1c'
  surface-container: '#201F20'
  surface-container-high: '#2A2A2B'
  surface-container-highest: '#353436'
  on-surface: '#e5e2e3'
  on-surface-variant: '#d0c6ab'
  inverse-surface: '#e5e2e3'
  inverse-on-surface: '#313031'
  outline: '#999077'
  outline-variant: '#444933'
  surface-tint: '#e9c400'
  primary: '#fff6df'
  on-primary: '#3a3000'
  primary-container: '#ffd700'
  on-primary-container: '#705e00'
  inverse-primary: '#705d00'
  secondary: '#ecb1ff'
  on-secondary: '#520070'
  secondary-container: '#8e00bf'
  on-secondary-container: '#f0bbff'
  tertiary: '#fff4ea'
  on-tertiary: '#432c00'
  tertiary-container: '#ffd38e'
  on-tertiary-container: '#7f5700'
  error: '#ffb4ab'
  on-error: '#690005'
  error-container: '#93000a'
  on-error-container: '#ffdad6'
  primary-fixed: '#ffe16d'
  primary-fixed-dim: '#e9c400'
  on-primary-fixed: '#221b00'
  on-primary-fixed-variant: '#544600'
  secondary-fixed: '#f9d8ff'
  secondary-fixed-dim: '#ecb1ff'
  on-secondary-fixed: '#320046'
  on-secondary-fixed-variant: '#75009e'
  tertiary-fixed: '#ffdeac'
  tertiary-fixed-dim: '#ffba38'
  on-tertiary-fixed: '#281900'
  on-tertiary-fixed-variant: '#604100'
  background: '#131314'
  on-background: '#e5e2e3'
  surface-variant: '#353436'
  neon-yellow: '#FFD700'
  neon-purple: '#D05BFF'
  cyber-orange: '#FFB300'
  text-primary: '#E5E2E3'
  text-muted: '#C4C9AC'
typography:
  headline-xl:
    fontFamily: Space Grotesk
    fontSize: 48px
    fontWeight: '700'
    lineHeight: '1.1'
    letterSpacing: -0.02em
  headline-lg:
    fontFamily: Space Grotesk
    fontSize: 32px
    fontWeight: '700'
    lineHeight: '1.2'
  headline-lg-mobile:
    fontFamily: Space Grotesk
    fontSize: 28px
    fontWeight: '700'
    lineHeight: '1.2'
  headline-md:
    fontFamily: Space Grotesk
    fontSize: 24px
    fontWeight: '600'
    lineHeight: '1.2'
  body-lg:
    fontFamily: Manrope
    fontSize: 18px
    fontWeight: '400'
    lineHeight: '1.6'
  body-md:
    fontFamily: Manrope
    fontSize: 16px
    fontWeight: '400'
    lineHeight: '1.5'
  label-tactical:
    fontFamily: JetBrains Mono
    fontSize: 12px
    fontWeight: '500'
    lineHeight: '1.2'
    letterSpacing: 0.1em
  label-data:
    fontFamily: JetBrains Mono
    fontSize: 10px
    fontWeight: '400'
    lineHeight: '1.0'
spacing:
  base: 4px
  gutter: 16px
  margin-mobile: 20px
  margin-desktop: 40px
  section-gap: 24px
---

## Brand & Style

This design system establishes a **Tech-Noir** aesthetic, merging the precision of military-grade "Command Center" interfaces with the vibrant energy of cyberpunk subcultures. It is a high-density, utility-first system designed for users who value technical depth and futuristic flair.

The visual style is **Cyber-Tactical**, defined by:
- **High-Contrast Minimalism:** Deep charcoal surfaces contrasted against aggressive neon accents.
- **HUD-Inspired Geometry:** Frequent use of 45-degree chamfered edges, coordinate grid overlays, and framing brackets.
- **Layered Depth:** Utilizing glassmorphism and additive light glows rather than traditional shadows to create a multi-layered terminal feel.
- **Glitch & Scan Dynamics:** Controlled digital artifacts, scan-line animations, and hard-shadow "glitch" offsets for interactive states.

## Colors

The palette is optimized for a dark-first environment, utilizing high-luminance primary colors to guide the user's eye through technical data density.

- **Background:** The base uses a near-black charcoal (`#131314`) to maintain high contrast without the "crushing" effect of pure black.
- **Primary (Electric Yellow):** The main functional color. Used for active navigation, critical CTAs, and primary "HUD" highlights.
- **Secondary (Neon Purple):** Reserved for "Epic" tier content, secondary decorative accents, and high-energy glows.
- **Tertiary (Cyber Orange):** Applied to warning states, "Hotfix" labels, and telemetry alerts.
- **Neutral Surface:** Surfaces are tiered using tonal stacking (Dim to High) to establish visual hierarchy in a flat-layered environment.

## Typography

This system uses a three-tier typographic stack to segregate narrative, interface, and technical data.

- **Display & Headlines:** Use **Space Grotesk**. Its geometric construction fits the cybernetic aesthetic. Tighten tracking for XL display titles to enhance the aggressive "Command" feel.
- **Body & Content:** Use **Manrope**. It provides a neutral, highly readable experience for descriptions and patch notes, balancing the high-octane display fonts.
- **Technical & UI Labels:** Use **JetBrains Mono**. All numerical data, timestamps, system codes, and micro-labels must use this monospaced font to reinforce the terminal aesthetic. Tactical labels are typically set in uppercase with tracking at 0.1em.

## Layout & Spacing

The layout philosophy follows a **Rigid Tactical Grid** with high information density.

- **Baseline Rhythm:** A strict 4px grid system governs all margins, padding, and component sizing.
- **Grid Pattern:** Backgrounds feature a 20x20px or 40x40px coordinate grid pattern (`rgba(255, 215, 0, 0.05)`) to simulate a HUD environment.
- **Density:** Mobile layouts prioritize a high-density 12-column grid. Components should use minimal internal padding to maximize data visibility.
- **Adaptation:** Breakpoints should maintain consistent vertical rhythm while scaling horizontal margins from 20px (mobile) to 40px (desktop).

## Elevation & Depth

Elevation is conveyed through **Tonal Stacking** and **Emissive Light**, strictly avoiding traditional soft-blur shadows.

- **Tonal Layers:** Deepest surfaces use `#131314`. Floating containers use `#201F20` or higher, increasing in brightness to indicate proximity to the user.
- **Glassmorphism:** Use `backdrop-filter: blur(12px)` on top-level panels (e.g., App Bars, Navigation) with a 60%–80% surface opacity to create "transparent terminal" depth.
- **Neon Glows:** Interactivity is indicated by additive glows (`box-shadow: 0 0 8px [color]`).
- **HUD Brackets:** Framing elements (L-shaped corner brackets) are used to "lift" specific data blocks without increasing the container's elevation.

## Shapes

The shape language is aggressive and industrial, prioritizing sharp angles over curves.

- **Tactical Chamfers:** Primary containers and interactive elements must utilize a 45-degree corner cut (Chamfer). Standard cuts are 8px or 12px diagonals, typically on the bottom-right or top-right corners.
- **Radius Rule:** Most UI elements have 0px roundedness. Softening (4px) is only permitted for micro-elements like status badges or profile tags.
- **Full Radius:** Reserved exclusively for notification pips and circular avatar frames.
- **HUD Brackets:** Decorative 1px or 2px lines should be used to frame component corners, creating a "bracketed" focus effect.

## Components

### Buttons (Tactical Triggers)
- **Primary:** Solid Electric Yellow background with black JetBrains Mono text. Must feature a right-side 8px chamfer cut.
- **Secondary:** Transparent background with 1px Neon Purple border. On hover, apply a `2px` translation glitch and a purple outer glow.

### Cards (Data Modules)
- **Structure:** Frosted glass background (`surface-container/80`) with `outline-variant` 1px border.
- **Details:** Every card must include a monospaced "Sector ID" (e.g., `SEC-01 // UPD`) in the header. Use a top-aligned color stripe (Yellow or Purple) to denote content rarity or priority.

### Toggles & Switches
- **Track:** High-contrast charcoal with a 1px border.
- **Thumb:** Electric Yellow. When active, the thumb should emit a 10px yellow glow.

### Inputs (Terminal Entry)
- **Styling:** Bottom-border only with L-bracket end-caps.
- **Active State:** Border glows Electric Yellow; label shifts to a "Scanning" state using JetBrains Mono.

### Navigation (Command Bar)
- **Bottom Nav:** Glassmorphic container (`xl` roundedness on top edge). Active items use a solid Electric Yellow background with an upward-facing neon glow.