---
name: Cognitive Nexus
colors:
  surface: '#f7f9fb'
  surface-dim: '#d8dadc'
  surface-bright: '#f7f9fb'
  surface-container-lowest: '#ffffff'
  surface-container-low: '#f2f4f6'
  surface-container: '#eceef0'
  surface-container-high: '#e6e8ea'
  surface-container-highest: '#e0e3e5'
  on-surface: '#191c1e'
  on-surface-variant: '#42474f'
  inverse-surface: '#2d3133'
  inverse-on-surface: '#eff1f3'
  outline: '#727780'
  outline-variant: '#c2c7d0'
  surface-tint: '#2b6195'
  primary: '#003156'
  on-primary: '#ffffff'
  primary-container: '#00487a'
  on-primary-container: '#86b7f0'
  inverse-primary: '#9dcaff'
  secondary: '#6b38d4'
  on-secondary: '#ffffff'
  secondary-container: '#8455ef'
  on-secondary-container: '#fffbff'
  tertiary: '#003723'
  on-tertiary: '#ffffff'
  tertiary-container: '#005035'
  on-tertiary-container: '#33ca91'
  error: '#ba1a1a'
  on-error: '#ffffff'
  error-container: '#ffdad6'
  on-error-container: '#93000a'
  primary-fixed: '#d1e4ff'
  primary-fixed-dim: '#9dcaff'
  on-primary-fixed: '#001d35'
  on-primary-fixed-variant: '#03497b'
  secondary-fixed: '#e9ddff'
  secondary-fixed-dim: '#d0bcff'
  on-secondary-fixed: '#23005c'
  on-secondary-fixed-variant: '#5516be'
  tertiary-fixed: '#6ffbbe'
  tertiary-fixed-dim: '#4edea3'
  on-tertiary-fixed: '#002113'
  on-tertiary-fixed-variant: '#005236'
  background: '#f7f9fb'
  on-background: '#191c1e'
  surface-variant: '#e0e3e5'
  surface-glass: rgba(255, 255, 255, 0.7)
  text-rich: '#333333'
  accent-electric: '#A855F7'
typography:
  display-lg:
    fontFamily: Hanken Grotesk
    fontSize: 48px
    fontWeight: '700'
    lineHeight: 56px
    letterSpacing: -0.02em
  display-lg-mobile:
    fontFamily: Hanken Grotesk
    fontSize: 36px
    fontWeight: '700'
    lineHeight: 42px
    letterSpacing: -0.02em
  headline-md:
    fontFamily: Hanken Grotesk
    fontSize: 24px
    fontWeight: '600'
    lineHeight: 32px
  body-lg:
    fontFamily: Hanken Grotesk
    fontSize: 18px
    fontWeight: '400'
    lineHeight: 28px
  body-md:
    fontFamily: Hanken Grotesk
    fontSize: 16px
    fontWeight: '400'
    lineHeight: 24px
  label-caps:
    fontFamily: JetBrains Mono
    fontSize: 12px
    fontWeight: '500'
    lineHeight: 16px
    letterSpacing: 0.05em
  label-md:
    fontFamily: Hanken Grotesk
    fontSize: 14px
    fontWeight: '500'
    lineHeight: 20px
rounded:
  sm: 0.25rem
  DEFAULT: 0.5rem
  md: 0.75rem
  lg: 1rem
  xl: 1.5rem
  full: 9999px
spacing:
  base: 8px
  container-max: 1280px
  gutter: 24px
  margin-mobile: 16px
  margin-desktop: 40px
---

## Brand & Style

The design system is engineered for an AI-driven student job platform, blending academic authority with cutting-edge technological prowess. The brand personality is "The Intelligent Career Partner"—someone who is reliable and established, yet forward-thinking and innovative. 

The aesthetic follows a **High-Tech Minimalism** approach. It utilizes expansive whitespace and a structured grid to convey professional clarity, while incorporating subtle **Glassmorphism** and vibrant accents to signal the platform's AI-driven core. The goal is to evoke a sense of future-readiness and secure advancement for students entering the professional landscape.

## Colors

The color strategy uses a deep, institutional **Navy Blue** (#00487A) to establish an immediate sense of trust and academic rigor. This is contrasted by a secondary **Electric Purple** and a tertiary **Neon Green**, used exclusively for AI-driven features like "Match Scores" or "Smart Suggestions."

The background remains a crisp **Light Grey/White** (#F8FAFC) to ensure the interface feels breathable. Use the `surface-glass` variable for navigation bars and floating overlays to create a sense of depth and modern sophistication. Primary actions should utilize the Navy, while Purple is reserved for high-engagement "Smart" components.

## Typography

This design system utilizes **Hanken Grotesk** as the primary typeface for its sharp, contemporary geometry and exceptional readability. It bridges the gap between a corporate sans-serif and a modern tech font. 

To reinforce the high-tech narrative, **JetBrains Mono** is used for small labels, metadata, and AI-generated data points. This monospaced secondary font provides a "code-inspired" texture that signifies data precision. Headlines should maintain tight letter-spacing for a confident, editorial look, while body text uses a generous line-height to maintain a minimalist, airy feel.

## Layout & Spacing

The layout follows a **Fixed-Fluid Hybrid** model. On desktop, content is contained within a 1280px max-width container using a 12-column grid. On smaller devices, it transitions to a fluid layout with a 4-column structure for mobile.

The spacing rhythm is strictly based on an **8px linear scale**. Use larger 40px - 64px gaps between major sections to emphasize the minimalist aesthetic. Navigation elements are treated as "floating" glass containers with 24px internal padding, detached from the edges of the viewport on desktop to enhance the high-tech, layered feel.

## Elevation & Depth

Visual hierarchy is achieved through **Tonal Layering** and **Ambient Shadows**. Surfaces are categorized into three levels:
1. **Base:** The Light Grey background (#F8FAFC).
2. **Surface:** Solid white cards with a soft, diffused shadow (15% opacity, 20px blur, 4px Y-offset) tinted with the primary navy color.
3. **Overlay:** Glassmorphic navigation and modals using a 12px backdrop-blur and a subtle 1px white inner border to simulate a glass edge.

Avoid heavy dark shadows; depth should feel atmospheric and light, consistent with the minimalist goal.

## Shapes

The shape language is defined by "Soft Precision." A standard **8px to 12px corner radius** is applied to cards and containers to appear approachable yet professional. Interactive components like buttons use the higher end of the scale (12px) to feel more tactile. AI-specific elements, such as "Match Tokens," may utilize a full pill-shape to distinguish them from standard functional UI.

## Components

- **Buttons:** Primary buttons use the Deep Navy with white text and a subtle 4px elevation. "Smart" action buttons (e.g., "AI Match") use a linear gradient from Electric Purple to Deep Navy.
- **Glass Navigation:** A fixed-top header with `backdrop-blur: 12px` and `background: rgba(255, 255, 255, 0.7)`. Include a 1px bottom border in a semi-transparent Navy.
- **Job Cards:** White backgrounds, 12px border radius, and an 8px Navy-tinted shadow. Include a "Match Score" chip in the top right using the Neon Green.
- **Inputs:** Clean, 1px border (#E2E8F0) that transitions to a 2px Purple border on focus, signaling the AI's "attention" to user input.
- **Chips:** Small, pill-shaped tags for skills and industries. Use the Navy for standard tags and the Purple for "Recommended by AI" tags.
- **AI Status Indicator:** A pulsing, soft-glow component in Neon Green to indicate the engine is processing data.