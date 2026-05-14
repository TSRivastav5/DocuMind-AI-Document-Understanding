---
name: DocuMind
colors:
  surface: '#fff8f6'
  surface-dim: '#f1d4cc'
  surface-bright: '#fff8f6'
  surface-container-lowest: '#ffffff'
  surface-container-low: '#fff1ed'
  surface-container: '#ffe9e4'
  surface-container-high: '#ffe2da'
  surface-container-highest: '#fadcd4'
  on-surface: '#271813'
  on-surface-variant: '#5b4039'
  inverse-surface: '#3e2c27'
  inverse-on-surface: '#ffede8'
  outline: '#907067'
  outline-variant: '#e4beb4'
  surface-tint: '#af3000'
  primary: '#ab2f00'
  on-primary: '#ffffff'
  primary-container: '#d63c00'
  on-primary-container: '#fffbff'
  inverse-primary: '#ffb59f'
  secondary: '#5d5e64'
  on-secondary: '#ffffff'
  secondary-container: '#dfdfe6'
  on-secondary-container: '#616269'
  tertiary: '#005ab4'
  on-tertiary: '#ffffff'
  tertiary-container: '#0072e1'
  on-tertiary-container: '#fefcff'
  error: '#ba1a1a'
  on-error: '#ffffff'
  error-container: '#ffdad6'
  on-error-container: '#93000a'
  primary-fixed: '#ffdbd1'
  primary-fixed-dim: '#ffb59f'
  on-primary-fixed: '#3a0a00'
  on-primary-fixed-variant: '#862200'
  secondary-fixed: '#e2e2e9'
  secondary-fixed-dim: '#c6c6cd'
  on-secondary-fixed: '#1a1b21'
  on-secondary-fixed-variant: '#45474c'
  tertiary-fixed: '#d6e3ff'
  tertiary-fixed-dim: '#aac7ff'
  on-tertiary-fixed: '#001b3e'
  on-tertiary-fixed-variant: '#00458d'
  background: '#fff8f6'
  on-background: '#271813'
  surface-variant: '#fadcd4'
typography:
  display-lg:
    fontFamily: Instrument Serif
    fontSize: 48px
    fontWeight: '400'
    lineHeight: '1.1'
    letterSpacing: -0.02em
  headline-md:
    fontFamily: Instrument Serif
    fontSize: 32px
    fontWeight: '400'
    lineHeight: '1.2'
  headline-sm:
    fontFamily: Instrument Serif
    fontSize: 24px
    fontWeight: '400'
    lineHeight: '1.3'
  body-lg:
    fontFamily: Geist Sans
    fontSize: 18px
    fontWeight: '400'
    lineHeight: '1.6'
  body-md:
    fontFamily: Geist Sans
    fontSize: 16px
    fontWeight: '400'
    lineHeight: '1.5'
  label-md:
    fontFamily: Geist Sans
    fontSize: 14px
    fontWeight: '500'
    lineHeight: '1'
    letterSpacing: 0.01em
  label-sm:
    fontFamily: Geist Sans
    fontSize: 12px
    fontWeight: '600'
    lineHeight: '1'
  code-md:
    fontFamily: Geist Mono
    fontSize: 14px
    fontWeight: '400'
    lineHeight: '1.6'
rounded:
  sm: 0.125rem
  DEFAULT: 0.25rem
  md: 0.375rem
  lg: 0.5rem
  xl: 0.75rem
  full: 9999px
spacing:
  container-max: 1024px
  gutter: 24px
  margin-mobile: 16px
  margin-desktop: 64px
  section-gap: 48px
---

## Brand & Style
This design system embodies an **Editorial SaaS** aesthetic—a marriage of high-end publishing sophistication and high-performance software utility. The brand personality is authoritative yet approachable, prioritizing clarity and "results-first" document intelligence. 

The visual style is defined by **Minimalism with a Tactile Twist**. It avoids the trend of glassmorphism and gradients in favor of structural integrity, generous whitespace, and precise typography. Depth is achieved through layered, sharp shadows and subtle perspective transforms that suggest physical sheets of paper or data cards, creating a workspace that feels fast, intentional, and built with exceptional taste.

## Colors
The palette is anchored by a warm, paper-like white (`#F8F7F4`) which reduces eye strain during long reading sessions. The primary interface interaction point is a vibrant **Burnt Orange** (`#E5450A`), used sparingly for focus actions and critical metrics. 

The sidebar and primary navigation utilize a **Near-Black** (`#111318`) to create a strong architectural frame for the content. Functional grays are pulled from a warm-neutral scale to maintain the "Editorial" feel, ensuring that borders and secondary text do not feel cold or clinical.

## Typography
The typographic system uses a high-contrast pairing to distinguish between "Content" and "Interface." 

**Instrument Serif** is used for logos, page headings, and significant pull-quotes. Its grounded, literary feel provides the editorial soul of the product. **Geist Sans** handles the functional heavy lifting—UI labels, navigation, and body copy—offering a precise, technical clarity. **Geist Mono** is strictly reserved for OCR outputs, data structures, and developer-centric information, ensuring that raw data is easily distinguishable from interpreted insights.

## Layout & Spacing
The design system employs a **Single-Column Fluid Grid** for the main content area, optimized for readability and focus. Rather than filling the screen horizontally, content is centered within a maximum-width container to mimic the proportions of a printed folio or professional report.

- **Desktop:** Generous 64px outer margins and 48px vertical section gaps to allow the UI to "breathe."
- **Tablet:** Margins scale down to 32px; the sidebar may collapse into an icon-only rail.
- **Mobile:** Single column with 16px margins. Metric cards stack vertically.

Layout rhythm is strictly 8px-based. Consistency in padding within cards and panels is critical to maintaining the "built with taste" precision.

## Elevation & Depth
This design system eschews "fluff" in favor of structural depth. It uses a three-tier elevation model:
1. **Base:** The `#F8F7F4` canvas.
2. **Flat Surfaces:** Cards and panels with a 1px border (`#E2E1DE`) and no shadow, used for secondary information.
3. **Elevated Elements:** Active cards or focused documents use a "Stacked Shadow"—a sharp 1px offset shadow followed by a soft, diffused 12px ambient shadow.

**Perspective Transforms:** When an element is hovered or "picked up," a subtle 0.5-degree rotation and scale-up (1.02x) are applied to simulate the handling of physical paper.
**Inset Shadows:** Used exclusively for output panels (OCR results, code blocks) to signify that they are "etched" into the page.

## Shapes
In line with the professional, editorial aesthetic, shapes are kept **Soft** (0.25rem default). This maintains a crisp, geometric rigor while removing the "stinging" sharpness of 0px corners. 

Buttons and input fields follow this 4px standard. Large containers like metric cards or main content panels use `rounded-lg` (8px). Circles are used only for status indicators and user avatars.

## Components
- **Metric Cards:** Features a white background, 1px neutral border, and a 2px solid **Burnt Orange** bottom-border accent. Titles use `label-sm` (uppercase).
- **Buttons:** Primary buttons are Solid Near-Black with White text. Secondary buttons are Ghost-style with a 1px border. No gradients; state changes are handled via opacity or subtle fills.
- **Underline Tabs:** Navigation within panels uses `label-md` text. Active states are indicated by a 2px Burnt Orange underline that spans the width of the label, rather than a background pill.
- **Input Fields:** Minimalist design with a bottom-border only in the resting state, transitioning to a full 1px border on focus.
- **Output Panels:** These use the `Geist Mono` font and a subtle `#F1F0ED` background with an `inset` shadow to distinguish them from the editable "Paper" UI.
- **Checkboxes:** Square with a 1px radius. When checked, they fill with Burnt Orange and use a white checkmark.