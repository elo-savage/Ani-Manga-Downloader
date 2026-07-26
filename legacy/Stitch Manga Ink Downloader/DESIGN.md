---
name: Manga Neobrutalism
colors:
  surface: '#faf9f9'
  surface-dim: '#dadada'
  surface-bright: '#faf9f9'
  surface-container-lowest: '#ffffff'
  surface-container-low: '#f4f3f3'
  surface-container: '#eeeeed'
  surface-container-high: '#e9e8e8'
  surface-container-highest: '#e3e2e2'
  on-surface: '#1a1c1c'
  on-surface-variant: '#4c4546'
  inverse-surface: '#2f3131'
  inverse-on-surface: '#f1f0f0'
  outline: '#7e7576'
  outline-variant: '#cfc4c5'
  surface-tint: '#5e5e5e'
  primary: '#000000'
  on-primary: '#ffffff'
  primary-container: '#1b1b1b'
  on-primary-container: '#848484'
  inverse-primary: '#c6c6c6'
  secondary: '#5d5f5f'
  on-secondary: '#ffffff'
  secondary-container: '#dfe0e0'
  on-secondary-container: '#616363'
  tertiary: '#000000'
  on-tertiary: '#ffffff'
  tertiary-container: '#1b1c1c'
  on-tertiary-container: '#848484'
  error: '#ba1a1a'
  on-error: '#ffffff'
  error-container: '#ffdad6'
  on-error-container: '#93000a'
  primary-fixed: '#e2e2e2'
  primary-fixed-dim: '#c6c6c6'
  on-primary-fixed: '#1b1b1b'
  on-primary-fixed-variant: '#474747'
  secondary-fixed: '#e2e2e2'
  secondary-fixed-dim: '#c6c6c7'
  on-secondary-fixed: '#1a1c1c'
  on-secondary-fixed-variant: '#454747'
  tertiary-fixed: '#e3e2e2'
  tertiary-fixed-dim: '#c7c6c6'
  on-tertiary-fixed: '#1b1c1c'
  on-tertiary-fixed-variant: '#464747'
  background: '#faf9f9'
  on-background: '#1a1c1c'
  surface-variant: '#e3e2e2'
typography:
  headline-xl:
    fontFamily: Epilogue
    fontSize: 64px
    fontWeight: '900'
    lineHeight: '1.0'
    letterSpacing: -0.04em
  headline-lg:
    fontFamily: Epilogue
    fontSize: 40px
    fontWeight: '800'
    lineHeight: '1.1'
    letterSpacing: -0.02em
  body-lg:
    fontFamily: Work Sans
    fontSize: 18px
    fontWeight: '500'
    lineHeight: '1.5'
    letterSpacing: '0'
  body-md:
    fontFamily: Work Sans
    fontSize: 16px
    fontWeight: '400'
    lineHeight: '1.5'
    letterSpacing: '0'
  data-mono:
    fontFamily: Space Grotesk
    fontSize: 14px
    fontWeight: '600'
    lineHeight: '1.2'
    letterSpacing: 0.05em
spacing:
  unit: 4px
  xs: 4px
  sm: 8px
  md: 16px
  lg: 32px
  xl: 64px
  gutter: 24px
  margin: 32px
---

## Brand & Style

This design system is a high-impact, ink-on-paper aesthetic that merges the raw, structural aggression of Neobrutalism with the narrative energy of Japanese Manga. It is designed for creators, developers, and power users who demand high clarity and a distinctive, tactile interface.

The personality is unapologetically bold, mechanical, and "lo-fi high-tech." It evokes the feeling of a technical manual found inside a 90s cyberpunk manga. Every interaction should feel like a physical click or a page turn—deliberate, snappy, and high-contrast. The emotional response is one of focus, urgency, and precision.

## Colors

The palette is strictly monochromatic, relying on pure `#000000` and `#FFFFFF` to define hierarchy. Grayscale accents are used exclusively for screentone textures and disabled states.

- **Primary:** Pure Black for borders, shadows, and primary text.
- **Secondary:** Pure White for surfaces and high-contrast text.
- **Accents:** Mid-grays are reserved for halftone patterns (screentones) to simulate depth without using gradients or soft shadows.
- **Interaction:** State changes are represented by color inversion (White-on-Black becoming Black-on-White) rather than hue shifts.

## Typography

Typography functions as a structural element. Headlines use **Epilogue** at maximum weights to mimic the impact of manga sound effects (SFX). Body copy uses **Work Sans** for its neutral, legible, and slightly architectural feel. Technical data, labels, and metadata utilize **Space Grotesk** to provide a mechanical, monospaced aesthetic.

All headlines must be set in uppercase for maximum "Impact" styling. Letter spacing should be tight for headlines and slightly tracked out for monospaced data to enhance the "technical readout" vibe.

## Layout & Spacing

The layout is built on a rigid **Fixed Grid** system that mimics comic book panels. Elements are locked into 4px increments (the base stroke width). 

- **The Panel System:** Layouts should be divided into distinct "panels" using the 4px black border. 
- **Gutter Logic:** Use 24px gutters between panels to emphasize the separation of information, similar to the "white space" between manga frames.
- **Bleeds:** Full-bleed imagery is encouraged, but must always be contained within a 4px black frame.
- **Halftones:** Large empty areas should be filled with a subtle 45-degree halftone dot pattern (screentone) to prevent the UI from feeling "empty."

## Elevation & Depth

This system rejects all forms of "natural" depth. There are no blurs, no z-axis lighting, and no transparency.

- **Hard Shadows:** Depth is achieved via a solid 8px offset shadow (Black `#000000`). The shadow does not blur; it is a translated duplicate of the element's footprint.
- **Screentone Depth:** Lower layers can be filled with denser halftone patterns, while foreground elements remain pure white or black.
- **Z-Stacking:** Elements that are "above" others must have a 4px black border that cuts through underlying elements.
- **Action Balloons:** Tooltips and popovers should be styled as speech or thought bubbles with sharp, triangular pointers.

## Shapes

The geometry is strictly rectangular and sharp. There are no rounded corners (0px radius). 

The only exception to the "no curves" rule is when a shape is meant to look "Inked." For example, a call-to-action button might have a slightly irregular, hand-drawn stroke weight (thicker on one side), but the corners must remain mathematically sharp or resemble the stroke of a G-pen. All containers must use a 4px solid black stroke.

## Components

- **Buttons:** Rectangular with 4px borders and an 8px hard offset shadow. On hover, the shadow disappears and the button "depresses" (translates +8px X and Y). On active state, the colors invert.
- **Action Balloons:** Used for tooltips and floating actions. These are white boxes with 4px black borders and a sharp triangular "tail."
- **Input Fields:** Thick black bottom-border or full box. Monospace font for input text. No focus rings; instead, the border weight increases to 6px on focus.
- **Cards (Panels):** Pure white backgrounds. Use a 10% density halftone pattern for the "gutter" area behind the cards to make the panels pop.
- **Checkboxes:** Square boxes. When checked, they are filled with a solid black "X" or a dense halftone pattern rather than a checkmark.
- **Progress Bars:** Solid black fill within a 4px border. No smooth animation; the progress should jump in discrete, mechanical increments.
- **Animations:** Transitions must be "Snappy." Use a 0.1s duration with an `ease-in-out` or `steps()` timing function. Elements should feel like they are snapping into place with magnetic force.