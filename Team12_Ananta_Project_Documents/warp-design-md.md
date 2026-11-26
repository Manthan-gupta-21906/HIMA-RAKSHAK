# Design Language: Warp — The Agentic Development Environment

> Extracted from `https://warp.dev` on May 28, 2026
> 1235 elements analyzed

This document describes the complete design language of the website. It is structured for AI/LLM consumption — use it to faithfully recreate the visual design in any framework.

## Color Palette

### Primary Colors

| Role | Hex | RGB | HSL | Usage Count |
|------|-----|-----|-----|-------------|
| Primary | `#f0e8d9` | rgb(240, 232, 217) | hsl(39, 43%, 90%) | 1255 |
| Secondary | `#c7aeff` | rgb(199, 174, 255) | hsl(259, 100%, 84%) | 34 |
| Accent | `#bda6f7` | rgb(189, 166, 247) | hsl(257, 84%, 81%) | 4 |

### Neutral Colors

| Hex | HSL | Usage Count |
|-----|-----|-------------|
| `#605d57` | hsl(40, 5%, 36%) | 475 |
| `#000000` | hsl(0, 0%, 0%) | 319 |
| `#121212` | hsl(0, 0%, 7%) | 155 |
| `#1d1c1a` | hsl(40, 5%, 11%) | 98 |
| `#ffffff` | hsl(0, 0%, 100%) | 75 |

### Background Colors

Used on large-area elements: `#121212`, `#ffffff`, `#020202`, `#030302`, `#000000`, `#cbb0f7`

### Text Colors

Text color palette: `#f0e8d9`, `#000000`, `#ffffff`, `#1d1c1a`, `#c7aeff`, `#111111`, `#605d57`, `#121212`, `#020202`

### Gradients

```css
background-image: linear-gradient(to top, oklab(0 0 0 / 0.25) 0%, rgba(0, 0, 0, 0) 50%, rgba(0, 0, 0, 0) 100%);
```

### Full Color Inventory

| Hex | Contexts | Count |
|-----|----------|-------|
| `#f0e8d9` | text, border, background | 1255 |
| `#605d57` | text, border | 475 |
| `#000000` | background, text, border | 319 |
| `#121212` | background, text, border | 155 |
| `#1d1c1a` | text, border, background | 98 |
| `#ffffff` | background, text, border | 75 |
| `#c7aeff` | text, border, background | 34 |
| `#bda6f7` | background | 4 |
| `#0e8a15` | background | 1 |

## Typography

### Font Families

- **Inter** — used for body (1173 elements)
- **DM Mono** — used for all (42 elements)
- **Matter** — used for all (20 elements)

### Type Scale

| Size (px) | Size (rem) | Weight | Line Height | Letter Spacing | Used On |
|-----------|------------|--------|-------------|----------------|---------|
| 72px | 4.5rem | 400 | 75.6px | -1.8px | blockquote, p |
| 64px | 4rem | 400 | 70.4px | -1.6px | h1 |
| 44.8px | 2.8rem | 400 | 51.52px | -1.12px | h2 |
| 36px | 2.25rem | 400 | 44px | -0.9px | h3 |
| 30px | 1.875rem | 500 | 40px | normal | summary, svg, path |
| 24px | 1.5rem | 400 | 28.8px | -0.6px | h3 |
| 18px | 1.125rem | 400 | 28.8px | normal | div, p, figcaption, span |
| 16px | 1rem | 400 | 24px | normal | html, head, script, meta |
| 14px | 0.875rem | 400 | 20px | normal | div, p, a, button |
| 12px | 0.75rem | 500 | 16px | 0.6px | span, div, a, h3 |
| 11px | 0.6875rem | 600 | 28px | normal | kbd |
| 10px | 0.625rem | 400 | 11.5px | 0.25px | span, a |

### Heading Scale

```css
h1 { font-size: 64px; font-weight: 400; line-height: 70.4px; }
h2 { font-size: 44.8px; font-weight: 400; line-height: 51.52px; }
h3 { font-size: 36px; font-weight: 400; line-height: 44px; }
h3 { font-size: 24px; font-weight: 400; line-height: 28.8px; }
h3 { font-size: 12px; font-weight: 500; line-height: 16px; }
```

### Body Text

```css
body { font-size: 14px; font-weight: 400; line-height: 20px; }
```

### Font Weights in Use

`400` (1066x), `500` (112x), `600` (52x), `700` (5x)

## Spacing

**Base unit:** 2px

| Token | Value | Rem |
|-------|-------|-----|
| spacing-2 | 2px | 0.125rem |
| spacing-80 | 80px | 5rem |
| spacing-112 | 112px | 7rem |
| spacing-216 | 216px | 13.5rem |

## Border Radii

| Label | Value | Count |
|-------|-------|-------|
| xs | 2px | 48 |
| md | 6px | 4 |
| lg | 16px | 10 |

## Box Shadows

**sm** — blur: 0px
```css
box-shadow: rgba(0, 0, 0, 0) 0px 0px 0px 0px, rgba(0, 0, 0, 0) 0px 0px 0px 0px, rgba(0, 0, 0, 0) 0px 0px 0px 0px, oklch(0.39 0.006 84.6) 0px 0px 0px 1px, rgba(0, 0, 0, 0.1) 0px 10px 15px -3px, rgba(0, 0, 0, 0.1) 0px 4px 6px -4px;
```

**sm (inset)** — blur: 0px
```css
box-shadow: rgb(31, 31, 31) 0px 0px 0px 1px inset;
```

**sm (inset)** — blur: 0px
```css
box-shadow: rgb(55, 50, 69) 0px 0px 0px 1px inset;
```

**sm (inset)** — blur: 0px
```css
box-shadow: rgba(0, 0, 0, 0) 0px 0px 0px 0px, rgba(0, 0, 0, 0) 0px 0px 0px 0px, rgba(0, 0, 0, 0) 0px 0px 0px 0px, oklch(0.39 0.006 84.6) 0px 0px 0px 1px inset, rgba(0, 0, 0, 0) 0px 0px 0px 0px;
```

**sm (inset)** — blur: 0px
```css
box-shadow: rgba(0, 0, 0, 0) 0px 0px 0px 0px, oklch(0.39 0.006 84.6) 0px 0px 0px 0px inset, rgba(0, 0, 0, 0) 0px 0px 0px 0px, rgba(0, 0, 0, 0) 0px 0px 0px 0px, rgba(0, 0, 0, 0) 0px 0px 0px 0px;
```

**sm** — blur: 0px
```css
box-shadow: rgba(0, 0, 0, 0) 0px 0px 0px 0px, rgba(0, 0, 0, 0) 0px 0px 0px 0px, rgba(0, 0, 0, 0) 0px 0px 0px 0px, rgba(0, 0, 0, 0) 0px 0px 0px 0px, rgba(0, 0, 0, 0.1) 0px 1px 3px 0px, rgba(0, 0, 0, 0.1) 0px 1px 2px -1px;
```

**sm** — blur: 0px
```css
box-shadow: rgba(0, 0, 0, 0) 0px 0px 0px 0px, rgba(0, 0, 0, 0) 0px 0px 0px 0px, rgba(0, 0, 0, 0) 0px 0px 0px 0px, rgba(0, 0, 0, 0) 0px 0px 0px 0px, rgba(0, 0, 0, 0.1) 0px 20px 25px -5px, rgba(0, 0, 0, 0.1) 0px 8px 10px -6px;
```

**sm (inset)** — blur: 0px
```css
box-shadow: rgba(0, 0, 0, 0) 0px 0px 0px 0px, oklch(0.39 0.006 84.6) 0px 0px 0px 1px inset, rgba(0, 0, 0, 0) 0px 0px 0px 0px, rgba(0, 0, 0, 0) 0px 0px 0px 0px, rgba(0, 0, 0, 0) 0px 0px 0px 0px;
```

**xl** — blur: 30px
```css
box-shadow: rgba(0, 0, 0, 0.4) 0px 8px 30px 0px;
```

## CSS Custom Properties

### Colors

```css
--color-primary-yellow: lab(79.2935% 13.5666 82.2486);
--color-violet-50: lab(96.2416% 2.28849 -5.51657);
--color-amber-400: lab(80.1641% 16.6016 99.2089);
--tw-ring-shadow: 0 0 #0000;
--color-indigo-400: lab(59.866% 22.4834 -64.4485);
--card-border: none;
--color-purple-500: lab(52.0183% 66.11 -78.2316);
--section-bg-alt: transparent;
--color-violet-600: lab(41.088% 68.9966 -91.995);
--color-blue-700: lab(36.9089% 35.0961 -85.6872);
--color-amber-600: lab(60.3514% 40.5624 87.1228);
--color-panel: oklch(29.0% 0.005 84.6);
--tw-inset-ring-shadow: 0 0 #0000;
--color-emerald-700: lab(44.4871% -41.0396 11.0361);
--color-blue-300: lab(77.5052% -6.4629 -36.42);
--color-text-secondary: oklch(71.5% 0.008 84.6);
--color-cyan-700: lab(44.7267% -21.5987 -26.118);
--color-accent-purple: #cbb0f7;
--color-amber-300: lab(86.4156% 6.13147 78.3961);
--color-olive-100: lab(96.0988% -.493258 1.82395);
--btn-bg: oklch(97.0% 0.010 84.6);
--border-treatment: none;
--color-green-500: lab(70.5521% -66.5147 45.8073);
--color-emerald-600: lab(55.0481% -49.9246 15.93);
--card-bg: oklch(22.0% 0.004 84.6);
--color-violet-400: lab(62.8239% 34.9159 -60.0512);
--tw-ring-offset-color: #fff;
--color-white: #fff;
--color-red-400: lab(63.7053% 60.745 31.3109);
--color-blue-400: lab(65.0361% -1.42065 -56.9802);
--color-accent: oklch(71.5% 0.008 84.6);
--color-olive-400: lab(69.6658% -2.009 7.72947);
--color-red-500: lab(55.4814% 75.0732 48.8528);
--color-background: #121212;
--accent-heading-color: ;
--tw-ring-offset-width: 0px;
--color-violet-500: lab(49.9355% 55.1776 -81.8963);
--btn-text-color: #121212;
--color-tertiary: oklch(71.5% 0.216 303.9);
--color-violet-700: lab(35.2783% 67.9912 -88.793);
--tw-ring-offset-shadow: 0 0 #0000;
--color-olive-700: lab(29.8862% -2.11598 8.58277);
--color-text-body: lab(76.8314% .247538 3.04846);
--terminus-theme-purple-bg: lab(52.2932% 50.4727 -67.8536);
--color-teal-700: lab(44.4134% -33.1436 -4.22149);
--color-cyan-500: lab(67.805% -35.3952 -30.2018);
--color-sky-400: lab(70.687% -23.6078 -45.9483);
--color-amber-500: lab(72.7183% 31.8672 97.9407);
--color-yellow-700: lab(47.8202% 25.2426 66.5015);
--color-primary-green: lab(69.7863% -53.411 45.1934);
--terminus-theme-fuchsia-bg: lab(58.8% 80.536 -41.0299);
--color-olive-950: lab(3.26204% -.309289 1.13377);
--color-red-700: lab(40.4273% 67.2623 53.7441);
--color-emerald-500: lab(66.9756% -58.27 19.5419);
--color-blue-500: lab(54.1736% 13.3369 -74.6839);
--img-border: none;
--color-olive-600: lab(38.2553% -2.31101 9.30823);
--color-amber-700: lab(47.2709% 42.9082 69.2966);
--color-muted: oklch(48.0% 0.007 84.6);
--btn-border: none;
--color-emerald-50: lab(97.8462% -6.94966 1.85487);
--color-surface: oklch(22.0% 0.004 84.6);
--tw-border-style: solid;
--color-text: oklch(97.0% 0.010 84.6);
--terminus-theme-green-bg: lab(77.0851% -61.9109 52.9433);
--color-amber-950: lab(15.8111% 20.9107 23.3752);
--color-red-600: lab(48.4493% 77.4328 61.5452);
--terminus-theme-blue-bg: lab(57.7421% 5.71477 -72.009);
--color-red-50: lab(96.5005% 4.18508 1.52328);
--color-border: oklch(39.0% 0.006 84.6);
--color-blue-200: lab(86.15% -4.04379 -21.0797);
--terminus-theme-red-bg: lab(66.0623% 54.719 71.1127);
--color-primary: oklch(71.5% 0.008 84.6);
--color-olive-900: lab(10.5512% -1.19986 4.84231);
--color-black: #000;
--color-red-950: lab(13.003% 29.04 16.7519);
--color-emerald-400: lab(75.0771% -60.7313 19.4147);
--color-green-700: lab(47.0329% -47.0239 31.4788);
--color-fuchsia-400: lab(66.1178% 66.0652 -52.4733);
--color-purple-700: lab(36.1758% 69.8525 -80.0381);
--card-backdrop-blur: 0px;
--color-teal-500: lab(67.3859% -49.0983 -2.63511);
--color-yellow-500: lab(76.3898% 14.5258 98.4589);
--color-amber-50: lab(98.6252% -.635922 8.42309);
--color-primary-red: lab(53.6853% 69.6775 43.7724);
--color-lighten-50: lab(59.4% 0 0);
--border-width: 0px;
```

### Spacing

```css
--scroll-padding-top: 5.25rem;
--surface-texture-size: 200px 200px;
--space-xl: calc(2rem*1);
--space-section: calc(4rem*1);
--space-2xl: calc(3rem*1);
--tw-space-x-reverse: 0;
--body-size: 16px;
--spacing: .25rem;
--heading-letter-spacing: -0.025em;
--space-lg: calc(1.5rem*1);
--space-xs: calc(.25rem*1);
--btn-padding: 0.25rem 1rem;
--heading-size: 64px;
--space-md: calc(1rem*1);
--tw-space-y-reverse: 0;
--space-sm: calc(.5rem*1);
```

### Typography

```css
--text-2xl: 1.5rem;
--text-7xl: 4.5rem;
--text-lg: 1.125rem;
--font-body: "Inter","Inter Fallback", 'Inter', system-ui, sans-serif;
--text-5xl--line-height: 1;
--text-base--line-height: calc(1.5/1);
--tracking-wider: .05em;
--font-mono: "DM Mono","DM Mono Fallback",ui-monospace,monospace;
--text-lg--line-height: calc(1.75/1.125);
--font-sans: "Inter","Inter Fallback", 'Inter', system-ui, sans-serif;
--surface-texture: none;
--font-weight-bold: 700;
--font-instrument-serif: "Instrument Serif","Instrument Serif Fallback";
--text-6xl: 3.75rem;
--text-xs--line-height: calc(1/.75);
--default-font-family: "Inter","Inter Fallback", 'Inter', system-ui, sans-serif;
--font-weight-light: 300;
--font-inter: "Inter","Inter Fallback";
--font-abel: "Abel","Abel Fallback";
--text-7xl--line-height: 1;
--text-xl: 1.25rem;
--font-heading: 'Matter', system-ui, sans-serif;
--leading-relaxed: 1.625;
--leading-snug: 1.375;
--body-line-height: 1.6;
--text-2xl--line-height: calc(2/1.5);
--text-8xl: 6rem;
--tracking-wide: .025em;
--text-xl--line-height: calc(1.75/1.25);
--font-weight-semibold: 600;
--text-sm: .875rem;
--surface-texture-opacity: 0;
--leading-tight: 1.25;
--text-4xl: 2.25rem;
--text-sm--line-height: calc(1.25/.875);
--text-5xl: 3rem;
--text-3xl--line-height: calc(2.25/1.875);
--text-3xl: 1.875rem;
--text-xs: .75rem;
--tracking-widest: .1em;
--font-weight-medium: 500;
--font-weight-normal: 400;
--font-display: 'Matter', system-ui, sans-serif;
--heading-font-style: normal;
--text-6xl--line-height: 1;
--text-4xl--line-height: calc(2.5/2.25);
--font-dm-mono: "DM Mono","DM Mono Fallback";
--text-base: 1rem;
--default-mono-font-family: "DM Mono","DM Mono Fallback",ui-monospace,monospace;
--tracking-tight: -.025em;
```

### Shadows

```css
--tw-inset-shadow-alpha: 100%;
--tw-drop-shadow-alpha: 100%;
--tw-inset-shadow: 0 0 #0000;
--tw-shadow-alpha: 100%;
--shadow: none;
--img-shadow: 0 8px 30px rgb(0 0 0 / 0.4);
--tw-shadow: 0 0 #0000;
```

### Radii

```css
--btn-radius: calc(0.125rem*1.5);
--radius-sm: calc(0.125rem*.5);
--radius: 0.125rem;
--radius-2xl: 1rem;
--radius-md: 0.125rem;
--radius-lg: calc(0.125rem*1.5);
--img-radius: calc(0.125rem*1.5);
--radius-xs: .125rem;
--radius-xl: calc(0.125rem*2);
```

### Other

```css
--aspect-video: 16/9;
--terminus-theme-purple-fg: lab(4.41046% 13.3571 -20.3024);
--heading-weight: 400;
--btn-transform: none;
--tw-outline-style: solid;
--ease-in: cubic-bezier(.4,0,1,1);
--divider-display: none;
--blur-xl: 24px;
--terminus-sticky-top: 6rem;
--tw-divide-x-reverse: 0;
--tw-gradient-from: rgba(0, 0, 0, 0);
--tw-gradient-to: rgba(0, 0, 0, 0);
--tw-scale-z: 1;
--easing: cubic-bezier(0.4, 0, 0.2, 1);
--terminus-theme-red-fg: lab(6.72867% 19.3065 11.9957);
--density: 1;
--container-sm: 24rem;
--tw-gradient-via-position: 50%;
--duration-slow: calc(.4s*1);
--container-lg: 32rem;
--tw-gradient-to-position: 100%;
--terminus-theme-fuchsia-fg: lab(6.15372% 23.154 -11.873);
--default-transition-duration: .15s;
--btn-icon-display: none;
--duration-fast: calc(.1s*1);
--container-xs: 20rem;
--tw-gradient-from-position: 0%;
--ease-in-out: cubic-bezier(.4,0,.2,1);
--default-transition-timing-function: cubic-bezier(.4,0,.2,1);
--body-weight: 400;
--motion-speed: 1;
--container-5xl: 64rem;
--tw-translate-z: 0;
--tw-gradient-via: rgba(0, 0, 0, 0);
--tw-scale-y: 1;
--container-6xl: 72rem;
--container-3xl: 48rem;
--tw-translate-y: 0;
--blur-md: 12px;
--ease-out: cubic-bezier(0,0,.2,1);
--animate-spin: spin 1s linear infinite;
--container-4xl: 56rem;
--tw-content: "";
--tw-divide-y-reverse: 0;
--container-2xl: 42rem;
--tw-translate-x: 0;
--duration-normal: calc(.2s*1);
--terminus-theme-green-fg: lab(8.10487% -18.2775 12.441);
--tw-scale-x: 1;
--heading-transform: none;
--content-max-width: 80rem;
--divider-style: none;
--container-xl: 36rem;
--terminus-theme-blue-fg: lab(4.78603% 2.73034 -22.9539);
--container-7xl: 80rem;
--hover-transform: none;
--blur-sm: 8px;
```

### Semantic

```css
success: [object Object];
warning: [object Object];
error: [object Object];
info: [object Object];
```

## Transitions & Animations

**Easing functions:** `[object Object]`

**Durations:** `0.15s`, `0.2s`, `0.5s`, `8s`, `0.08s`

### Common Transitions

```css
transition: cubic-bezier(0.4, 0, 0.2, 1);
transition: color 0.15s cubic-bezier(0.4, 0, 0.2, 1), background-color 0.15s cubic-bezier(0.4, 0, 0.2, 1), border-color 0.15s cubic-bezier(0.4, 0, 0.2, 1), outline-color 0.15s cubic-bezier(0.4, 0, 0.2, 1), text-decoration-color 0.15s cubic-bezier(0.4, 0, 0.2, 1), fill 0.15s cubic-bezier(0.4, 0, 0.2, 1), stroke 0.15s cubic-bezier(0.4, 0, 0.2, 1), --tw-gradient-from 0.15s cubic-bezier(0.4, 0, 0.2, 1), --tw-gradient-via 0.15s cubic-bezier(0.4, 0, 0.2, 1), --tw-gradient-to 0.15s cubic-bezier(0.4, 0, 0.2, 1);
transition: transform 0.2s cubic-bezier(0.4, 0, 0.2, 1), translate 0.2s cubic-bezier(0.4, 0, 0.2, 1), scale 0.2s cubic-bezier(0.4, 0, 0.2, 1), rotate 0.2s cubic-bezier(0.4, 0, 0.2, 1);
transition: opacity 0.15s, scale 0.15s, display 0.15s allow-discrete, overlay 0.15s allow-discrete;
transition: color 0.2s cubic-bezier(0.4, 0, 0.2, 1), background-color 0.2s cubic-bezier(0.4, 0, 0.2, 1), border-color 0.2s cubic-bezier(0.4, 0, 0.2, 1), outline-color 0.2s cubic-bezier(0.4, 0, 0.2, 1), text-decoration-color 0.2s cubic-bezier(0.4, 0, 0.2, 1), fill 0.2s cubic-bezier(0.4, 0, 0.2, 1), stroke 0.2s cubic-bezier(0.4, 0, 0.2, 1), --tw-gradient-from 0.2s cubic-bezier(0.4, 0, 0.2, 1), --tw-gradient-via 0.2s cubic-bezier(0.4, 0, 0.2, 1), --tw-gradient-to 0.2s cubic-bezier(0.4, 0, 0.2, 1);
transition: opacity 0.15s cubic-bezier(0.4, 0, 0.2, 1);
transition: transform 0.15s cubic-bezier(0.4, 0, 0.2, 1), translate 0.15s cubic-bezier(0.4, 0, 0.2, 1), scale 0.15s cubic-bezier(0.4, 0, 0.2, 1), rotate 0.15s cubic-bezier(0.4, 0, 0.2, 1);
transition: opacity 0.5s cubic-bezier(0.4, 0, 0.2, 1), transform 0.5s cubic-bezier(0.4, 0, 0.2, 1);
transition: 0.2s cubic-bezier(0.4, 0, 0.2, 1);
transition: opacity 0.5s cubic-bezier(0.4, 0, 0.2, 1) 0.08s, transform 0.5s cubic-bezier(0.4, 0, 0.2, 1) 0.08s;
```

### Keyframe Animations

**reveal**
```css
@keyframes reveal {
  0% { opacity: 0; transform: scale(0.95); }
  100% { opacity: 1; transform: scale(1); }
}
```

**fill-progress**
```css
@keyframes fill-progress {
  0% { width: 0%; }
  100% { width: 100%; }
}
```

**scroll-left**
```css
@keyframes scroll-left {
  0% { transform: translate(0px); }
  100% { transform: translate(-50%); }
}
```

**scroll-right**
```css
@keyframes scroll-right {
  0% { transform: translate(-50%); }
  100% { transform: translate(0px); }
}
```

**loading-spinner-in**
```css
@keyframes loading-spinner-in {
  100% { opacity: 1; }
}
```

**spin-slow**
```css
@keyframes spin-slow {
  100% { transform: rotate(360deg); }
}
```

**spin**
```css
@keyframes spin {
  100% { transform: rotate(360deg); }
}
```

**hero-left-photo-carousel**
```css
@keyframes hero-left-photo-carousel {
  0%, 50% { opacity: 1; }
  55%, 95% { opacity: 0; }
  100% { opacity: 1; }
}
```

## Component Patterns

Detected UI component patterns and their most common styles:

### Buttons (20 instances)

```css
.button {
  background-color: oklch(0.97 0.01 84.6);
  color: rgb(18, 18, 18);
  font-size: 14px;
  font-weight: 400;
  padding-top: 0px;
  padding-right: 0px;
  border-radius: 3px;
}
```

### Cards (6 instances)

```css
.card {
  background-color: oklch(0.22 0.004 84.6);
  border-radius: 4px;
  box-shadow: rgba(0, 0, 0, 0) 0px 0px 0px 0px, rgba(0, 0, 0, 0) 0px 0px 0px 0px, rgba(0, 0, 0, 0) 0px 0px 0px 0px, rgba(0, 0, 0, 0) 0px 0px 0px 0px, rgba(0, 0, 0, 0.1) 0px 1px 3px 0px, rgba(0, 0, 0, 0.1) 0px 1px 2px -1px;
  padding-top: 0px;
  padding-right: 0px;
}
```

### Links (120 instances)

```css
.link {
  color: rgb(0, 0, 0);
  font-size: 16px;
  font-weight: 400;
}
```

### Navigation (7 instances)

```css
.navigatio {
  background-color: rgb(12, 12, 12);
  color: rgb(0, 0, 0);
  padding-top: 8px;
  padding-bottom: 8px;
  padding-left: 8px;
  padding-right: 8px;
  position: fixed;
  box-shadow: rgba(0, 0, 0, 0) 0px 0px 0px 0px, rgba(0, 0, 0, 0) 0px 0px 0px 0px, rgba(0, 0, 0, 0) 0px 0px 0px 0px, oklch(0.39 0.006 84.6) 0px 0px 0px 1px, rgba(0, 0, 0, 0.1) 0px 10px 15px -3px, rgba(0, 0, 0, 0.1) 0px 4px 6px -4px;
}
```

### Footer (1 instances)

```css
.foote {
  color: oklch(0.97 0.01 84.6);
  padding-top: 0px;
  padding-bottom: 0px;
  font-size: 16px;
}
```

### Modals (1 instances)

```css
.modal {
  background-color: rgb(255, 255, 255);
  border-radius: 0px;
  padding-top: 0px;
  padding-right: 0px;
}
```

### Tabs (3 instances)

```css
.tab {
  color: rgb(18, 18, 18);
  font-size: 16px;
  font-weight: 400;
  padding-top: 0px;
  padding-right: 4px;
  border-color: rgb(18, 18, 18);
  border-radius: 3.35544e+07px;
}
```

### Accordions (8 instances)

```css
.accordion {
  color: rgb(0, 0, 0);
  font-size: 16px;
  padding-top: 0px;
  padding-right: 0px;
  border-color: rgb(0, 0, 0);
}
```

## Component Clusters

Reusable component instances grouped by DOM structure and style similarity:

### Button — 5 instances, 1 variant

**Variant 1** (5 instances)

```css
  background: rgba(0, 0, 0, 0);
  color: lab(39.7069 0.226021 2.6737);
  padding: 0px 0px 0px 0px;
  border-radius: 4px;
  border: 0px solid lab(39.7069 0.226021 2.6737);
  font-size: 14px;
  font-weight: 400;
```

### Button — 3 instances, 1 variant

**Variant 1** (3 instances)

```css
  background: rgba(0, 0, 0, 0);
  color: oklch(0.715 0.008 84.6);
  padding: 0px 0px 0px 0px;
  border-radius: 3.35544e+07px;
  border: 0px solid oklch(0.715 0.008 84.6);
  font-size: 14px;
  font-weight: 400;
```

### Button — 1 instance, 1 variant

**Variant 1** (1 instance)

```css
  background: rgba(0, 0, 0, 0);
  color: oklch(0.97 0.01 84.6);
  padding: 0px 0px 0px 0px;
  border-radius: 3px;
  border: 0px solid oklch(0.97 0.01 84.6);
  font-size: 16px;
  font-weight: 400;
```

### Button — 3 instances, 1 variant

**Variant 1** (3 instances)

```css
  background: rgba(0, 0, 0, 0);
  color: rgb(18, 18, 18);
  padding: 0px 4px 0px 4px;
  border-radius: 3.35544e+07px;
  border: 0px solid rgb(18, 18, 18);
  font-size: 16px;
  font-weight: 400;
```

## Layout System

**7 grid containers** and **399 flex containers** detected.

### Container Widths

| Max Width | Padding |
|-----------|---------|
| 1280px | 40px |
| 100% | 0px |
| 768px | 0px |
| 672px | 0px |
| 1024px | 0px |

### Grid Column Patterns

| Columns | Usage Count |
|---------|-------------|
| 2-column | 3x |
| 3-column | 2x |
| 5-column | 1x |

### Grid Templates

```css
grid-template-columns: 320px 832px;
gap: 48px;
grid-template-columns: none;
grid-template-columns: 384px 384px 384px;
gap: 24px;
grid-template-columns: 454.391px 681.609px;
gap: 64px;
grid-template-columns: 220.797px 220.797px 220.797px 220.797px 220.812px;
gap: 24px;
```

### Flex Patterns

| Direction/Wrap | Count |
|----------------|-------|
| row/nowrap | 309x |
| column/nowrap | 88x |
| row/wrap | 2x |

**Gap values:** `12px`, `16px`, `20px`, `24px`, `2px`, `32px`, `32px 40px`, `40px`, `48px`, `4px`, `56px`, `64px`, `6px`, `80px`, `8px`

## Accessibility (WCAG 2.1)

**Overall Score: 100%** — 8 passing, 0 failing color pairs

### Passing Color Pairs

| Foreground | Background | Ratio | Level |
|------------|------------|-------|-------|
| `#121212` | `#f0e8d9` | 15.39:1 | AAA |

## Design System Score

**Overall: 93/100 (Grade: A)**

| Category | Score |
|----------|-------|
| Color Discipline | 100/100 |
| Typography Consistency | 80/100 |
| Spacing System | 100/100 |
| Shadow Consistency | 90/100 |
| Border Radius Consistency | 100/100 |
| Accessibility | 100/100 |
| CSS Tokenization | 100/100 |

**Strengths:** Tight, disciplined color palette, Well-defined spacing scale, Clean elevation system, Consistent border radii, Strong accessibility compliance, Good CSS variable tokenization

**Issues:**
- 30 !important rules — prefer specificity over overrides
- 1453 duplicate CSS declarations

## Gradients

**1 unique gradients** detected.

| Type | Direction | Stops | Classification |
|------|-----------|-------|----------------|
| linear | to top | 3 | bold |

```css
background: linear-gradient(to top, oklab(0 0 0 / 0.25) 0%, rgba(0, 0, 0, 0) 50%, rgba(0, 0, 0, 0) 100%);
```

## Z-Index Map

**2 unique z-index values** across 1 layers.

| Layer | Range | Elements |
|-------|-------|----------|
| sticky | 10,20 | header.s.t.i.c.k.y. .t.o.p.-.0. .z.-.1.0. .b.g.-.[.v.a.r.(.-.-.c.o.l.o.r.-.b.a.c.k.g.r.o.u.n.d.).]./.7.0. .b.a.c.k.d.r.o.p.-.b.l.u.r.-.m.d. .s.u.p.p.o.r.t.s.-.[.b.a.c.k.d.r.o.p.-.f.i.l.t.e.r.].:.b.g.-.[.v.a.r.(.-.-.c.o.l.o.r.-.b.a.c.k.g.r.o.u.n.d.).]./.6.0, a.a.b.s.o.l.u.t.e. .t.o.p.-.3. .l.e.f.t.-.3. .z.-.1.0. .r.o.u.n.d.e.d.-.f.u.l.l. .p.x.-.2...5. .p.y.-.1. .t.e.x.t.-.[.1.0.p.x.]./.[.1...1.5.]. .f.o.n.t.-.m.e.d.i.u.m. .t.r.a.c.k.i.n.g.-.w.i.d.e. .t.r.a.n.s.i.t.i.o.n.-.c.o.l.o.r.s. .b.g.-.w.h.i.t.e./.2.0. .t.e.x.t.-.w.h.i.t.e. .b.a.c.k.d.r.o.p.-.b.l.u.r.-.s.m. .h.o.v.e.r.:.b.g.-.w.h.i.t.e./.3.5, img.n.o.-.f.r.a.m.e. .r.e.l.a.t.i.v.e. .z.-.1.0. .m.a.x.-.h.-.8. .w.-.a.u.t.o. .m.a.x.-.w.-.[.1.6.0.p.x.]. .o.b.j.e.c.t.-.c.o.n.t.a.i.n |

## SVG Icons

**14 unique SVG icons** detected. Dominant style: **filled**.

| Size Class | Count |
|------------|-------|
| xs | 3 |
| sm | 7 |
| md | 1 |
| xl | 3 |

**Icon colors:** `currentColor`

## Font Files

| Family | Source | Weights | Styles |
|--------|--------|---------|--------|
| Inter | self-hosted | 100 900 | italic, normal |
| DM Mono | self-hosted | 400, 500 | normal |
| Instrument Serif | self-hosted | 400 | italic, normal |
| Abel | self-hosted | 400 | normal |
| Matter | self-hosted | 400, 500 | normal |

## Image Style Patterns

| Pattern | Count | Key Styles |
|---------|-------|------------|
| thumbnail | 24 | objectFit: fill, borderRadius: 0px, shape: square |
| hero | 8 | objectFit: cover, borderRadius: 3px, shape: rounded |
| general | 2 | objectFit: cover, borderRadius: 0px, shape: square |

**Aspect ratios:** 3:2 (9x), 3.65:1 (3x), 5.08:1 (3x), 4.67:1 (3x), 6.56:1 (3x), 21:9 (2x), 9.37:1 (1x), 3.69:1 (1x)

## Motion Language

**Feel:** mixed · **Scroll-linked:** yes

### Duration Tokens

| name | value | ms |
|---|---|---|
| `instant` | `80ms` | 80 |
| `xs` | `150ms` | 150 |
| `sm` | `200ms` | 200 |
| `lg` | `500ms` | 500 |

### Easing Families

- **custom** (1230 uses) — `cubic-bezier(0.4, 0, 0.2, 1)`

### Keyframes In Use

| name | kind | properties | uses |
|---|---|---|---|
| `scroll-left` | slide | transform | 2 |
| `hero-left-photo-carousel` | fade | opacity | 2 |

## Component Anatomy

### button — 12 instances

**Slots:** label, icon
**Variants:** secondary · outline
**Sizes:** medium

| variant | count | sample label |
|---|---|---|
| default | 8 | Products |
| outline | 3 |  |
| secondary | 1 |  |

## Brand Voice

**Tone:** friendly · **Pronoun:** third-person · **Headings:** Sentence case (tight)

### Top CTA Verbs

- **products** (1)
- **solutions** (1)
- **resources** (1)
- **enterprise** (1)

### Button Copy Patterns

- "products" (1×)
- "solutions" (1×)
- "resources" (1×)
- "enterprise" (1×)

### Sample Headings

> Ship better software with any agent
> Proud partner of industry leaders
> Proud partner of industry leaders
> Be more productive. Stay in control.
> Start in the terminal
> Ship better software with any agent
> Proud partner of industry leaders
> Proud partner of industry leaders
> Be more productive. Stay in control.
> Start in the terminal

## Page Intent

**Type:** `landing` (confidence 0.59)
**Description:** Ship faster with AI-powered terminal and coding agents.

Alternates: legal (0.4)

## Section Roles

Reading order (top→bottom): cta → cta → nav → feature-grid → hero → logo-wall → feature-grid → nav → hero → testimonial → cta → feature-grid → footer → nav

| # | Role | Heading | Confidence |
|---|------|---------|------------|
| 0 | cta | — | 0.75 |
| 1 | cta | — | 0.75 |
| 2 | nav | — | 0.9 |
| 3 | feature-grid | Ship better software with any agent | 0.8 |
| 4 | hero | Ship better software with any agent | 0.85 |
| 5 | logo-wall | Proud partner of industry leaders | 0.85 |
| 6 | feature-grid | Be more productive. Stay in control. | 0.8 |
| 7 | nav | — | 0.9 |
| 8 | hero | Warp Terminal is now open-source | 0.4 |
| 9 | testimonial | — | 0.8 |
| 10 | cta | Start shipping with agents. | 0.4 |
| 11 | feature-grid | Get Warp today | 0.8 |
| 12 | footer | PRODUCT | 0.95 |
| 13 | nav | PRODUCT | 0.9 |

## Material Language

**Label:** `flat` (confidence 0)

| Metric | Value |
|--------|-------|
| Avg saturation | 0.204 |
| Shadow profile | soft |
| Avg shadow blur | 0px |
| Max radius | 16px |
| backdrop-filter in use | no |
| Gradients | 1 |

## Imagery Style

**Label:** `flat-illustration` (confidence 0.132)
**Counts:** total 34, svg 13, icon 0, screenshot-like 0, photo-like 0
**Dominant aspect:** ultra-wide
**Radius profile on images:** square

## Component Library

**Detected:** `tailwindcss` (confidence 0.591)

Evidence:
- tailwind-like class density 59%

## Quick Start

To recreate this design in a new project:

1. **Install fonts:** Add `Inter` from Google Fonts or your font provider
2. **Import CSS variables:** Copy `variables.css` into your project
3. **Tailwind users:** Use the generated `tailwind.config.js` to extend your theme
4. **Design tokens:** Import `design-tokens.json` for tooling integration
