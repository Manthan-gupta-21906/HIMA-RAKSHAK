# Design Language: Paddle - Subscriptions, Payments & Tax Compliance for SaaS & Mobile Apps

> Extracted from `https://paddle.com` on May 28, 2026
> 1022 elements analyzed

This document describes the complete design language of the website. It is structured for AI/LLM consumption — use it to faithfully recreate the visual design in any framework.

## Color Palette

### Primary Colors

| Role | Hex | RGB | HSL | Usage Count |
|------|-----|-----|-----|-------------|
| Primary | `#1c1a15` | rgb(28, 26, 21) | hsl(43, 14%, 10%) | 766 |
| Secondary | `#e4e1d1` | rgb(228, 225, 209) | hsl(51, 26%, 86%) | 4 |
| Accent | `#ffd400` | rgb(255, 212, 0) | hsl(50, 100%, 50%) | 16 |

### Neutral Colors

| Hex | HSL | Usage Count |
|-----|-----|-------------|
| `#fcfcfc` | hsl(0, 0%, 99%) | 967 |
| `#ebe7df` | hsl(40, 23%, 90%) | 81 |
| `#000000` | hsl(0, 0%, 0%) | 19 |
| `#d9d3c9` | hsl(37, 17%, 82%) | 15 |
| `#2b3033` | hsl(203, 9%, 18%) | 8 |
| `#545454` | hsl(0, 0%, 33%) | 2 |

### Background Colors

Used on large-area elements: `#0e1414`, `#f9f8f7`, `#d6cbb6`, `#ebe7df`, `#fcfcfc`, `#1c1a15`, `#ffd400`

### Text Colors

Text color palette: `#fcfcfc`, `#1c1a15`, `#0e1414`, `#2b3033`, `#ebe7df`, `#545454`, `#000000`, `#ffffff`

### Full Color Inventory

| Hex | Contexts | Count |
|-----|----------|-------|
| `#fcfcfc` | text, border, background | 967 |
| `#1c1a15` | text, border, background | 766 |
| `#0e1414` | background, text, border | 159 |
| `#ebe7df` | background, border, text | 81 |
| `#000000` | background, border, text | 19 |
| `#ffd400` | background | 16 |
| `#d9d3c9` | border | 15 |
| `#2b3033` | text, border | 8 |
| `#e4e1d1` | background | 4 |
| `#545454` | text, border | 2 |
| `#d6cbb6` | background | 1 |
| `#1cc691` | background | 1 |

## Typography

### Font Families

- **Inter** — used for body (892 elements)
- **Times** — used for body (54 elements)
- **serrifCondensed** — used for all (28 elements)

### Type Scale

| Size (px) | Size (rem) | Weight | Line Height | Letter Spacing | Used On |
|-----------|------------|--------|-------------|----------------|---------|
| 72px | 4.5rem | 400 | 72px | -0.72px | h1, span |
| 48px | 3rem | 400 | 57.6px | -0.48px | h2, p |
| 40px | 2.5rem | 400 | 48px | -0.4px | h3, h2 |
| 24px | 1.5rem | 400 | 36px | -0.4px | span, h4 |
| 20px | 1.25rem | 400 | 30px | -0.4px | body, div, a, header |
| 16px | 1rem | 400 | normal | normal | html, head, style, meta |
| 15px | 0.9375rem | 400 | 21px | -0.4px | div |
| 14px | 0.875rem | 500 | 21px | -0.4px | div, p, strong, a |
| 13px | 0.8125rem | 700 | 18.2px | normal | div |
| 11px | 0.6875rem | 500 | 16.5px | 1px | span |
| 10px | 0.625rem | 400 | 10px | 0.1px | span |

### Heading Scale

```css
h1 { font-size: 72px; font-weight: 400; line-height: 72px; }
h2 { font-size: 48px; font-weight: 400; line-height: 57.6px; }
h3 { font-size: 40px; font-weight: 400; line-height: 48px; }
h4 { font-size: 24px; font-weight: 400; line-height: 36px; }
h2 { font-size: 14px; font-weight: 500; line-height: 21px; }
```

### Body Text

```css
body { font-size: 16px; font-weight: 400; line-height: normal; }
```

### Font Weights in Use

`400` (558x), `500` (453x), `700` (5x), `300` (3x), `100` (2x), `600` (1x)

## Spacing

**Base unit:** 2px

| Token | Value | Rem |
|-------|-------|-----|
| spacing-1 | 1px | 0.0625rem |
| spacing-24 | 24px | 1.5rem |
| spacing-30 | 30px | 1.875rem |
| spacing-40 | 40px | 2.5rem |
| spacing-56 | 56px | 3.5rem |
| spacing-64 | 64px | 4rem |
| spacing-128 | 128px | 8rem |
| spacing-150 | 150px | 9.375rem |
| spacing-418 | 418px | 26.125rem |

## Border Radii

| Label | Value | Count |
|-------|-------|-------|
| sm | 3px | 6 |
| md | 6px | 4 |
| md | 10px | 16 |
| lg | 16px | 34 |
| xl | 24px | 5 |
| full | 32px | 5 |
| full | 64px | 3 |
| full | 100px | 1 |
| full | 120px | 2 |

## Box Shadows

**sm (inset)** — blur: 0px
```css
box-shadow: rgba(252, 252, 252, 0.24) 0px 0px 0px 1px inset;
```

**xl** — blur: 48px
```css
box-shadow: rgba(0, 0, 0, 0.15) 0px 8px 48px 0px;
```

**xl (inset)** — blur: 32px
```css
box-shadow: rgba(0, 0, 0, 0.32) 0px 32px 32px 0px, rgba(252, 252, 252, 0.1) 0px 0px 0px 2px inset;
```

## CSS Custom Properties

### Colors

```css
--rb-font-color: #1c1a15;
--rb-font-color-white: #ebe7df;
--rb-font-color-brown: #7e765d;
--rb-border-brown: #d9d3c9;
--th-color-body: rgba(var(--white-rgb),0.8);
--th-color-heading: var(--white);
--th-color-body-subtle: var(--neutral-60);
--th-color-background: var(--black);
--th-color-card: var(--neutral-80);
--th-color-link: var(--yellow);
--color-primary-yellow: #ffd400;
--color-primary-black: #0e1414;
--color-primary-white: #fcfcfc;
--color-extended-red-50: #fddad5;
--color-extended-red-100: #fcc7bf;
--color-extended-red-200: #faa396;
--color-extended-red-300: #f77f6c;
--color-extended-red-400: #f55a42;
--color-extended-red-500: #f4472c;
--color-extended-red-600: #db4028;
--color-extended-red-700: #b7321f;
--color-extended-red-800: #952316;
--color-extended-red-900: #73150d;
--color-extended-gold-50: #fdf1d6;
--color-extended-gold-100: #fceac1;
--color-extended-gold-200: #fbdc98;
--color-extended-gold-300: #f9cd6f;
--color-extended-gold-400: #f7bf46;
--color-extended-gold-500: #f6b831;
--color-extended-gold-600: #dfa52c;
--color-extended-gold-700: #c48022;
--color-extended-gold-800: #a85c18;
--color-extended-gold-900: #8c380f;
--color-extended-green-50: #cff6e4;
--color-extended-green-100: #b7f2d6;
--color-extended-green-200: #88eabb;
--color-extended-green-300: #59e1a0;
--color-extended-green-400: #29d885;
--color-extended-green-500: #11d477;
--color-extended-green-600: #0fbe6b;
--color-extended-green-700: #0c9453;
--color-extended-green-800: #086a3b;
--color-extended-green-900: #054024;
--color-extended-teal-50: #cdf9f9;
--color-extended-teal-100: #b4f6f6;
--color-extended-teal-200: #83f0f0;
--color-extended-teal-300: #15e3e3;
--color-extended-teal-400: #15e3e3;
--color-extended-teal-500: #06e0e0;
--color-extended-teal-600: #05c9c9;
--color-extended-teal-700: #049c9c;
--color-extended-teal-800: #037070;
--color-extended-teal-900: #024444;
--color-extended-blue-50: #d7e3ff;
--color-extended-blue-100: #c3d4ff;
--color-extended-blue-200: #9bb9ff;
--color-extended-blue-300: #739dff;
--color-extended-blue-400: #4b80ff;
--color-extended-blue-500: #3772ff;
--color-extended-blue-600: #3267e7;
--color-extended-blue-700: #2752b8;
--color-extended-blue-800: #1d3d89;
--color-extended-blue-900: #13295b;
--color-extended-purple-50: #e5d8ff;
--color-extended-purple-100: #d7c4ff;
--color-extended-purple-200: #bd9eff;
--color-extended-purple-300: #a378ff;
--color-extended-purple-400: #8851ff;
--color-extended-purple-500: #7b3dff;
--color-extended-purple-600: #6f37e7;
--color-extended-purple-700: #582cb8;
--color-extended-purple-800: #412189;
--color-extended-purple-900: #2a165b;
--color-extended-orchid-50: #f6dafd;
--color-extended-orchid-100: #f1c8fc;
--color-extended-orchid-200: #e9a4fa;
--color-extended-orchid-300: #e07ff7;
--color-extended-orchid-400: #d75bf5;
--color-extended-orchid-500: #d248f4;
--color-extended-orchid-600: #bd41dd;
--color-extended-orchid-700: #9634b0;
--color-extended-orchid-800: #6e2783;
--color-extended-orchid-900: #481a57;
--color-extended-pink-50: #fde0f5;
--color-extended-pink-100: #fcd1f0;
--color-extended-pink-200: #fab3e6;
--color-extended-pink-300: #f894dc;
--color-extended-pink-400: #f676d2;
--color-extended-pink-500: #f566cd;
--color-extended-pink-600: #dc5cb8;
--color-extended-pink-700: #be478f;
--color-extended-pink-800: #9e3366;
--color-extended-pink-900: #801f3e;
--color-neutral-light-50: #f7f8f9;
--color-neutral-light-100: #eceef1;
--color-neutral-light-200: #e2e5e7;
--color-neutral-light-300: #d8dbde;
--color-neutral-light-400: #cdd1d5;
--color-neutral-light-500: #c8cbd1;
--color-neutral-light-600: #c3c6cb;
--color-neutral-light-700: #b9bcbf;
--color-neutral-light-800: #afb1b4;
--color-neutral-light-900: #a5a7a9;
--color-neutral-dark-50: #696d6d;
--color-neutral-dark-100: #5f6364;
--color-neutral-dark-200: #54595b;
--color-neutral-dark-300: #4a4f52;
--color-neutral-dark-400: #404549;
--color-neutral-dark-500: #3a4044;
--color-neutral-dark-600: #353b3f;
--color-neutral-dark-700: #2b3033;
--color-neutral-dark-800: #212628;
--color-neutral-dark-900: #181c1d;
--color-neutral-dark-950: #0a0e0e;
--color-secondary-blue-300: var(--color-extended-blue-300);
--color-secondary-blue-400: var(--color-extended-blue-400);
--color-secondary-blue-600: var(--color-extended-blue-600);
--color-secondary-teal-200: var(--color-extended-teal-200);
--color-secondary-teal-300: var(--color-extended-teal-300);
--color-secondary-teal-600: var(--color-extended-teal-600);
--color-secondary-purple-100: var(--color-extended-purple-100);
--color-secondary-purple-300: var(--color-extended-purple-300);
--color-secondary-purple-600: var(--color-extended-purple-600);
--color-secondary-red-200: var(--color-extended-red-200);
--color-secondary-red-300: var(--color-extended-red-300);
--color-secondary-red-400: var(--color-extended-red-400);
```

### Spacing

```css
--rb-gap-spark: 2px;
--space-s: 1rem;
--space-m: 1.5rem;
--space-l: 2.5rem;
--space-xl: 4rem;
--gap-flush: 0;
--gap-2xs: 2rem;
--gap-xs: 4rem;
--gap-s: 5rem;
--gap-m: 8rem;
--gap-l: 12rem;
--gap-xl: 16rem;
--spacing-3xs: 0.25rem;
--spacing-xxs: 0.5rem;
--spacing-xs: 0.75rem;
--spacing-s: 1rem;
--spacing-m: 1.5rem;
--spacing-l: 2.5rem;
--spacing-xl: 3.5rem;
--spacing-2xl: 5rem;
```

### Typography

```css
--default-font: var(--font-inter),"Helvetica Neue",Helvetica,Arial,sans-serif;
--editorial-font: var(--font-tiempos-text),serif;
--font-serrif-condensed: "serrifCondensed","serrifCondensed Fallback";
--font-inter: "Inter","Inter Fallback";
--font-tiempos-text: "tiemposText","tiemposText Fallback";
```

### Other

```css
--rb-background: #f9f8f7;
--rb-background-black: #1c1a15;
--rb-background-brown: #ebe7df;
--rb-background-light-brown: #e8e6e2;
--rb-background-lighter-brown: #e4e1d1;
--rb-radii: 0.625rem;
--black: var(--color-primary-black);
--black-rgb: 14,20,20;
--white: var(--color-primary-white);
--white-rgb: 252,252,252;
--yellow: var(--color-primary-yellow);
--dark-teal: var(--color-extended-blue-900);
--pale-blue: var(--color-extended-blue-50);
--pale-pink: var(--color-neutral-light-100);
--orange: var(--color-extended-gold-500);
--red: var(--color-extended-red-400);
--blue: var(--color-extended-blue-300);
--billing-yellow: var(--color-extended-gold-100);
--billing-orange: var(--color-extended-gold-700);
--billing-blue: var(--color-extended-teal-200);
--metrics-blue: var(--color-extended-green-100);
--metrics-green: var(--color-extended-teal-800);
--metrics-orange: var(--color-extended-gold-400);
--pi-x: var(--color-primary-black);
--pi-y: var(--color-primary-black);
--pi-z: var(--color-primary-black);
--retain-blue: var(--color-extended-blue-100);
--retain-navy: var(--color-extended-blue-700);
--retain-pink: var(--color-extended-purple-100);
--neutral-20: var(--color-neutral-light-200);
--neutral-40: var(--color-neutral-light-900);
--neutral-60: var(--color-neutral-dark-50);
--neutral-70: var(--color-neutral-dark-700);
--neutral-80: var(--color-neutral-dark-900);
--neutral-dark-700: var(--color-neutral-dark-700);
--neutral-dark-900: var(--color-neutral-dark-900);
--black-alpha-95: rgba(var(--black-rgb),0.95);
--black-alpha-80: rgba(var(--black-rgb),0.8);
--black-alpha-60: rgba(var(--black-rgb),0.6);
--black-alpha-40: rgba(var(--black-rgb),0.4);
--black-alpha-20: rgba(var(--black-rgb),0.2);
--black-alpha-10: rgba(var(--black-rgb),0.1);
--black-alpha-5: rgba(var(--black-rgb),0.05);
--black-alpha-2: rgba(var(--black-rgb),0.02);
--white-alpha-95: rgba(var(--white-rgb),0.95);
--white-alpha-80: rgba(var(--white-rgb),0.8);
--white-alpha-60: rgba(var(--white-rgb),0.6);
--white-alpha-40: rgba(var(--white-rgb),0.4);
--white-alpha-20: rgba(var(--white-rgb),0.2);
--white-alpha-10: rgba(var(--white-rgb),0.1);
--white-alpha-5: rgba(var(--white-rgb),0.05);
--white-alpha-2: rgba(var(--white-rgb),0.02);
--gradient-cool: linear-gradient(268.02deg,var(--pale-blue) 0%,var(--pale-pink) 100%);
--highlight: var(--yellow);
--step--2: 0.72rem;
--step--1: 0.875rem;
--step-0: 0.9rem;
--step-1: 1rem;
--step-2: 1.1rem;
--step-3: 1.3rem;
--step-4: 2.3rem;
--step-5: 2.8rem;
--corner-s: 0.4rem;
--corner-m: 0.5rem;
--corner-l: 1rem;
--ease-1: cubic-bezier(0.246,0.75,0.187,1);
--ease-2: cubic-bezier(0.19,1,0.22,1);
--ease-3: cubic-bezier(1,0,0,1);
--breakpoint-s: 428px;
--breakpoint-m: 843px;
--breakpoint-l: 1024px;
--breakpoint-xl: 1440px;
--grid-page-gutter-s: 0px;
--grid-page-gutter-m: 40px;
--grid-page-gutter-l: 96px;
--grid-column-count-s: 4;
--grid-column-count-m: 6;
--grid-column-count-l: 12;
--grid-column-gutter-s: 24px;
--grid-column-gutter-m: 24px;
--grid-column-gutter-l: 40px;
--grid-content-max-width: 1248px;
--radii-s: 0.5rem;
--radii-m: 0.75rem;
--radii-l: 1rem;
--type-scale-3xs-s: 0.4688rem;
--type-scale-3xs-m: 0.4688rem;
--type-scale-3xs-l: 0.5rem;
--type-scale-3xs-xl: 0.5rem;
--type-scale-xxs-s: 0.5625rem;
--type-scale-xxs-m: 0.5625rem;
--type-scale-xxs-l: 0.6rem;
--type-scale-xxs-xl: 0.6rem;
--type-scale-xs-s: 0.6563rem;
--type-scale-xs-m: 0.6563rem;
--type-scale-xs-l: 0.76rem;
--type-scale-xs-xl: 0.76rem;
--type-scale-s-s: 0.8438rem;
--type-scale-s-m: 0.8438rem;
--type-scale-s-l: 0.9rem;
--type-scale-s-xl: 0.8438rem;
--type-scale-m-s: 0.9375rem;
--type-scale-m-m: 0.9375rem;
--type-scale-m-l: 1rem;
--type-scale-m-xl: 1rem;
--type-scale-l-s: 0.9844rem;
--type-scale-l-m: 0.9844rem;
--type-scale-l-l: 1.05rem;
--type-scale-l-xl: 1.05rem;
--type-scale-xl-s: 1.125rem;
--type-scale-xl-m: 1.125rem;
--type-scale-xl-l: 1.2rem;
--type-scale-xl-xl: 1.2rem;
--type-scale-2xl-s: 1.5rem;
--type-scale-2xl-m: 1.5rem;
--type-scale-2xl-l: 1.6rem;
--type-scale-2xl-xl: 1.6rem;
--type-scale-3xl-s: 1.75rem;
--type-scale-3xl-m: 1.75rem;
--type-scale-3xl-l: 2.5rem;
--type-scale-3xl-xl: 2.5rem;
--type-scale-4xl-s: 1.875rem;
--type-scale-4xl-m: 1.875rem;
--type-scale-4xl-l: 3.5rem;
--type-scale-4xl-xl: 3.5rem;
--type-scale-5xl-s: 2.8125rem;
--type-scale-5xl-m: 2.8125rem;
--type-scale-5xl-l: 4.25rem;
--type-scale-5xl-xl: 4.25rem;
```

### Dependencies

```css
--black: --color-primary-black;
--white: --color-primary-white;
--yellow: --color-primary-yellow;
--dark-teal: --color-extended-blue-900;
--pale-blue: --color-extended-blue-50;
--pale-pink: --color-neutral-light-100;
--orange: --color-extended-gold-500;
--red: --color-extended-red-400;
--blue: --color-extended-blue-300;
--billing-yellow: --color-extended-gold-100;
--billing-orange: --color-extended-gold-700;
--billing-blue: --color-extended-teal-200;
--metrics-blue: --color-extended-green-100;
--metrics-green: --color-extended-teal-800;
--metrics-orange: --color-extended-gold-400;
--pi-x: --color-primary-black;
--pi-y: --color-primary-black;
--pi-z: --color-primary-black;
--retain-blue: --color-extended-blue-100;
--retain-navy: --color-extended-blue-700;
--retain-pink: --color-extended-purple-100;
--neutral-20: --color-neutral-light-200;
--neutral-40: --color-neutral-light-900;
--neutral-60: --color-neutral-dark-50;
--neutral-70: --color-neutral-dark-700;
--neutral-80: --color-neutral-dark-900;
--neutral-dark-700: --color-neutral-dark-700;
--neutral-dark-900: --color-neutral-dark-900;
--black-alpha-95: --black-rgb;
--black-alpha-80: --black-rgb;
--black-alpha-60: --black-rgb;
--black-alpha-40: --black-rgb;
--black-alpha-20: --black-rgb;
--black-alpha-10: --black-rgb;
--black-alpha-5: --black-rgb;
--black-alpha-2: --black-rgb;
--white-alpha-95: --white-rgb;
--white-alpha-80: --white-rgb;
--white-alpha-60: --white-rgb;
--white-alpha-40: --white-rgb;
--white-alpha-20: --white-rgb;
--white-alpha-10: --white-rgb;
--white-alpha-5: --white-rgb;
--white-alpha-2: --white-rgb;
--gradient-cool: --pale-blue,--pale-pink;
--highlight: --yellow;
--th-color-body: --white-rgb;
--th-color-heading: --white;
--th-color-body-subtle: --neutral-60;
--th-color-background: --black;
--th-color-card: --neutral-80;
--th-color-link: --yellow;
--default-font: --font-inter;
--editorial-font: --font-tiempos-text;
--color-secondary-blue-300: --color-extended-blue-300;
--color-secondary-blue-400: --color-extended-blue-400;
--color-secondary-blue-600: --color-extended-blue-600;
--color-secondary-teal-200: --color-extended-teal-200;
--color-secondary-teal-300: --color-extended-teal-300;
--color-secondary-teal-600: --color-extended-teal-600;
--color-secondary-purple-100: --color-extended-purple-100;
--color-secondary-purple-300: --color-extended-purple-300;
--color-secondary-purple-600: --color-extended-purple-600;
--color-secondary-red-200: --color-extended-red-200;
--color-secondary-red-300: --color-extended-red-300;
--color-secondary-red-400: --color-extended-red-400;
```

### Semantic

```css
success: [object Object];
warning: [object Object];
error: [object Object];
info: [object Object];
```

## Breakpoints

| Name | Value | Type |
|------|-------|------|
| sm | 428px | min-width |
| sm | 480px | max-width |
| sm | 639px | max-width |
| sm | 640px | min-width |
| sm | 641px | min-width |
| 843px | 843px | min-width |
| lg | 991px | max-width |
| lg | 992px | min-width |
| lg | 1023px | max-width |
| lg | 1024px | min-width |
| 1440px | 1440px | min-width |
| 1920px | 1920px | min-width |

## Transitions & Animations

**Easing functions:** `[object Object]`, `[object Object]`, `[object Object]`, `[object Object]`

**Durations:** `0.3s`, `0.24s`, `0.8s`, `0.2s`, `0.16s`, `0.15s`, `0.13s`, `0.32s`, `0.4s`

### Common Transitions

```css
transition: all;
transition: background-color 0.3s;
transition: transform 0.24s ease-out;
transition: 0.24s ease-out;
transition: background-color 0.8s cubic-bezier(0.246, 0.75, 0.187, 1), border-color 0.8s cubic-bezier(0.246, 0.75, 0.187, 1), color 0.8s cubic-bezier(0.246, 0.75, 0.187, 1);
transition: background-color 0.8s cubic-bezier(0.246, 0.75, 0.187, 1), border-color 0.8s cubic-bezier(0.246, 0.75, 0.187, 1), color 0.8s cubic-bezier(0.246, 0.75, 0.187, 1), box-shadow 0.8s cubic-bezier(0.246, 0.75, 0.187, 1), opacity 0.8s cubic-bezier(0.246, 0.75, 0.187, 1);
transition: background-position 0.2s ease-out, transform 0.2s ease-out;
transition: 0.16s ease-out;
transition: opacity 0.15s linear, filter 0.15s linear;
transition: transform 0.13s cubic-bezier(0.55, 0.055, 0.675, 0.19) 0.13s;
```

### Keyframe Animations

**error-404_headMove__6wbx0**
```css
@keyframes error-404_headMove__6wbx0 {
  0% { transform: rotate(-8deg); }
  50% { transform: rotate(8deg); }
  100% { transform: rotate(8deg); }
}
```

**error-404_tailWag__jlScO**
```css
@keyframes error-404_tailWag__jlScO {
  0% { transform: rotate(-8deg); }
  12% { transform: rotate(-4deg); }
  27% { transform: rotate(-6deg); }
  50% { transform: rotate(-5deg); }
  100% { transform: rotate(8deg); }
}
```

**footer-nav_play__kfdl6**
```css
@keyframes footer-nav_play__kfdl6 {
  0% { transform: rotateX(45deg) translateY(-50%); }
  100% { transform: rotateX(45deg) translateY(0px); }
}
```

**button_buttonGlow__pO_Vb**
```css
@keyframes button_buttonGlow__pO_Vb {
  0% { background-position: -200% center; }
  100% { background-position: 200% center; }
}
```

**toast_toastAnim__257iz**
```css
@keyframes toast_toastAnim__257iz {
  50% { opacity: 0.4; }
  100% { opacity: 1; }
}
```

**loader_lds-ripple__h4_r5**
```css
@keyframes loader_lds-ripple__h4_r5 {
  0% { top: 28px; left: 28px; width: 0px; height: 0px; opacity: 1; }
  100% { top: -1px; left: -1px; width: 58px; height: 58px; opacity: 0; }
}
```

**recognition-slider_marquee__V3gF2**
```css
@keyframes recognition-slider_marquee__V3gF2 {
  0% { transform: translate3d(-25%, 0px, 0px); }
  100% { transform: translate3d(-75%, 0px, 0px); }
}
```

**logo-garden_slide__phNeK**
```css
@keyframes logo-garden_slide__phNeK {
  0% { transform: translateX(0px); }
  100% { transform: translateX(-100%); }
}
```

## Component Patterns

Detected UI component patterns and their most common styles:

### Buttons (28 instances)

```css
.button {
  background-color: rgb(28, 26, 21);
  color: rgb(28, 26, 21);
  font-size: 16px;
  font-weight: 500;
  padding-top: 0px;
  padding-right: 0px;
  border-radius: 10px;
}
```

### Cards (45 instances)

```css
.card {
  background-color: rgb(252, 252, 252);
  border-radius: 0px;
  box-shadow: rgba(0, 0, 0, 0.32) 0px 32px 32px 0px, rgba(252, 252, 252, 0.1) 0px 0px 0px 2px inset;
  padding-top: 0px;
  padding-right: 0px;
}
```

### Inputs (5 instances)

```css
.input {
  background-color: rgba(0, 0, 0, 0.2);
  color: rgb(0, 0, 0);
  border-color: rgb(0, 0, 0);
  border-radius: 32px;
  font-size: 14px;
  padding-top: 0px;
  padding-right: 0px;
}
```

### Links (170 instances)

```css
.link {
  color: rgba(252, 252, 252, 0.6);
  font-size: 16px;
  font-weight: 500;
}
```

### Navigation (184 instances)

```css
.navigatio {
  background-color: rgb(249, 248, 247);
  color: rgb(28, 26, 21);
  padding-top: 0px;
  padding-bottom: 0px;
  padding-left: 0px;
  padding-right: 0px;
  position: static;
}
```

### Footer (73 instances)

```css
.foote {
  background-color: rgb(28, 26, 21);
  color: rgba(252, 252, 252, 0.6);
  padding-top: 0px;
  padding-bottom: 0px;
  font-size: 16px;
}
```

### Modals (6 instances)

```css
.modal {
  background-color: rgb(249, 248, 247);
  border-radius: 0px;
  padding-top: 32px;
  padding-right: 32px;
}
```

### Dropdowns (181 instances)

```css
.dropdown {
  background-color: rgb(14, 20, 20);
  border-radius: 0px;
  border-color: rgba(252, 252, 252, 0.6);
  padding-top: 0px;
}
```

### Badges (5 instances)

```css
.badge {
  background-color: rgb(255, 212, 0);
  color: rgb(28, 26, 21);
  font-size: 16px;
  font-weight: 400;
  padding-top: 0px;
  padding-right: 0px;
  border-radius: 0px;
}
```

### Switches (5 instances)

```css
.switche {
  background-color: rgba(0, 0, 0, 0.02);
  border-radius: 0px;
  border-color: rgb(14, 20, 20) rgb(14, 20, 20) rgba(0, 0, 0, 0.08) rgba(0, 0, 0, 0.08);
}
```

## Component Clusters

Reusable component instances grouped by DOM structure and style similarity:

### Button — 8 instances, 2 variants

**Variant 1** (5 instances)

```css
  background: rgba(0, 0, 0, 0);
  color: rgb(28, 26, 21);
  padding: 0px 12px 0px 12px;
  border-radius: 0px;
  border: 0px none rgb(28, 26, 21);
  font-size: 16px;
  font-weight: 500;
```

**Variant 2** (3 instances)

```css
  background: rgb(14, 20, 20);
  color: rgb(255, 255, 255);
  padding: 8px 32px 8px 32px;
  border-radius: 64px;
  border: 0px none rgb(255, 255, 255);
  font-size: 14px;
  font-weight: 700;
```

### Button — 1 instance, 1 variant

**Variant 1** (1 instance)

```css
  background: rgba(0, 0, 0, 0);
  color: rgb(28, 26, 21);
  padding: 0px 0px 0px 0px;
  border-radius: 0px;
  border: 0px none rgb(28, 26, 21);
  font-size: 16px;
  font-weight: 400;
```

### Button — 7 instances, 2 variants

**Variant 1** (2 instances)

```css
  background: rgb(228, 225, 209);
  color: rgb(28, 26, 21);
  padding: 0px 0px 0px 0px;
  border-radius: 10px;
  border: 1px solid rgba(252, 252, 252, 0.02);
  font-size: 16px;
  font-weight: 500;
```

**Variant 2** (5 instances)

```css
  background: rgb(14, 20, 20);
  color: rgb(252, 252, 252);
  padding: 0px 0px 0px 0px;
  border-radius: 10px;
  border: 1px solid rgb(14, 20, 20);
  font-size: 16px;
  font-weight: 500;
```

### Button — 3 instances, 1 variant

**Variant 1** (3 instances)

```css
  background: rgb(28, 26, 21);
  color: rgb(252, 252, 252);
  padding: 16px 20px 16px 20px;
  border-radius: 10px;
  border: 0px none rgb(252, 252, 252);
  font-size: 16px;
  font-weight: 500;
```

### Button — 3 instances, 1 variant

**Variant 1** (3 instances)

```css
  background: rgb(255, 212, 0);
  color: rgb(252, 252, 252);
  padding: 3.52px 3.52px 3.52px 3.52px;
  border-radius: 3px;
  border: 0px none rgb(252, 252, 252);
  font-size: 16px;
  font-weight: 500;
```

### Link — 3 instances, 1 variant

**Variant 1** (3 instances)

```css
  background: rgb(252, 252, 252);
  color: rgb(28, 26, 21);
  padding: 40px 40px 40px 40px;
  border-radius: 24px;
  border: 1px solid rgba(0, 0, 0, 0);
  font-size: 20px;
  font-weight: 400;
```

### Card — 3 instances, 1 variant

**Variant 1** (3 instances)

```css
  background: rgba(0, 0, 0, 0);
  color: rgb(28, 26, 21);
  padding: 0px 0px 0px 0px;
  border-radius: 0px;
  border: 0px none rgb(28, 26, 21);
  font-size: 20px;
  font-weight: 400;
```

### Card — 4 instances, 1 variant

**Variant 1** (4 instances)

```css
  background: rgba(0, 0, 0, 0);
  color: rgb(28, 26, 21);
  padding: 0px 0px 0px 0px;
  border-radius: 0px;
  border: 0px none rgb(28, 26, 21);
  font-size: 20px;
  font-weight: 400;
```

### Card — 9 instances, 1 variant

**Variant 1** (9 instances)

```css
  background: rgba(0, 0, 0, 0);
  color: rgb(28, 26, 21);
  padding: 0px 0px 0px 0px;
  border-radius: 0px;
  border: 0px none rgb(28, 26, 21);
  font-size: 20px;
  font-weight: 400;
```

### Card — 1 instance, 1 variant

**Variant 1** (1 instance)

```css
  background: rgba(0, 0, 0, 0);
  color: rgb(252, 252, 252);
  padding: 0px 0px 0px 0px;
  border-radius: 0px;
  border: 0px none rgb(252, 252, 252);
  font-size: 20px;
  font-weight: 400;
```

### Card — 4 instances, 1 variant

**Variant 1** (4 instances)

```css
  background: rgba(0, 0, 0, 0);
  color: rgb(28, 26, 21);
  padding: 0px 0px 0px 0px;
  border-radius: 0px;
  border: 0px none rgb(28, 26, 21);
  font-size: 20px;
  font-weight: 400;
```

### Card — 1 instance, 1 variant

**Variant 1** (1 instance)

```css
  background: rgba(0, 0, 0, 0);
  color: rgb(28, 26, 21);
  padding: 0px 0px 0px 0px;
  border-radius: 0px;
  border: 0px none rgb(28, 26, 21);
  font-size: 20px;
  font-weight: 400;
```

### Card — 8 instances, 1 variant

**Variant 1** (8 instances)

```css
  background: rgba(0, 0, 0, 0);
  color: rgb(28, 26, 21);
  padding: 0px 0px 0px 0px;
  border-radius: 0px;
  border: 0px none rgb(28, 26, 21);
  font-size: 48px;
  font-weight: 400;
```

### Card — 3 instances, 1 variant

**Variant 1** (3 instances)

```css
  background: rgba(0, 0, 0, 0);
  color: rgb(28, 26, 21);
  padding: 0px 0px 0px 0px;
  border-radius: 0px;
  border: 0px none rgb(28, 26, 21);
  font-size: 20px;
  font-weight: 400;
```

### Card — 3 instances, 1 variant

**Variant 1** (3 instances)

```css
  background: rgba(0, 0, 0, 0);
  color: rgb(28, 26, 21);
  padding: 0px 0px 0px 0px;
  border-radius: 0px;
  border: 0px none rgb(28, 26, 21);
  font-size: 24px;
  font-weight: 400;
```

### Card — 2 instances, 1 variant

**Variant 1** (2 instances)

```css
  background: rgba(0, 0, 0, 0);
  color: rgb(252, 252, 252);
  padding: 0px 0px 0px 0px;
  border-radius: 0px;
  border: 0px none rgb(252, 252, 252);
  font-size: 20px;
  font-weight: 400;
```

### Button — 1 instance, 1 variant

**Variant 1** (1 instance)

```css
  background: rgba(0, 0, 0, 0);
  color: rgb(252, 252, 252);
  padding: 6px 6px 6px 6px;
  border-radius: 4px;
  border: 1px solid rgba(0, 0, 0, 0);
  font-size: 20px;
  font-weight: 100;
```

## Layout System

**96 grid containers** and **249 flex containers** detected.

### Container Widths

| Max Width | Padding |
|-----------|---------|
| 100% | 0px |
| 480px | 16px |

### Grid Column Patterns

| Columns | Usage Count |
|---------|-------------|
| 2-column | 57x |
| 16-column | 26x |
| 3-column | 11x |
| 1-column | 1x |
| 6-column | 1x |

### Grid Templates

```css
grid-template-columns: 0px [main-start] 63.3281px 63.3281px 63.3281px 63.3281px 63.3281px 63.3281px 63.3281px 63.3281px 63.3281px 63.3281px 63.3281px 63.3281px [main-end] 0px;
gap: normal 40px;
grid-template-columns: 0px [main-start] 63.3281px 63.3281px 63.3281px 63.3281px 63.3281px 63.3281px 63.3281px 63.3281px 63.3281px 63.3281px 63.3281px 63.3281px [main-end] 0px;
gap: normal 40px;
grid-template-columns: 0px [main-start] 63.3281px 63.3281px 63.3281px 63.3281px 63.3281px 63.3281px 63.3281px 63.3281px 63.3281px 63.3281px 63.3281px 63.3281px [main-end] 0px;
gap: normal 40px;
grid-template-columns: 0px [main-start] 63.3281px 63.3281px 63.3281px 63.3281px 63.3281px 63.3281px 63.3281px 63.3281px 63.3281px 63.3281px 63.3281px 63.3281px [main-end] 0px;
gap: normal 40px;
grid-template-columns: subgrid [] [] [] [] [] [] [] [] [] [] [] [] [] [] [];
```

### Flex Patterns

| Direction/Wrap | Count |
|----------------|-------|
| row/nowrap | 195x |
| column/nowrap | 46x |
| row-reverse/nowrap | 1x |
| row/wrap | 3x |
| column-reverse/nowrap | 4x |

**Gap values:** `0px 12px`, `10px`, `12px`, `16px`, `16px 24px`, `16px 32px`, `18px`, `24px`, `24px 12px`, `2px`, `32px`, `40px`, `40px 32px`, `64px`, `8px`, `normal 16px`, `normal 40px`

## Accessibility (WCAG 2.1)

**Overall Score: 100%** — 14 passing, 0 failing color pairs

### Passing Color Pairs

| Foreground | Background | Ratio | Level |
|------------|------------|-------|-------|
| `#0e1414` | `#fcfcfc` | 18.13:1 | AAA |
| `#ffffff` | `#0e1414` | 18.6:1 | AAA |
| `#0e1414` | `#ffd400` | 13:1 | AAA |
| `#1c1a15` | `#ffd400` | 12.14:1 | AAA |

## Design System Score

**Overall: 89/100 (Grade: B)**

| Category | Score |
|----------|-------|
| Color Discipline | 100/100 |
| Typography Consistency | 80/100 |
| Spacing System | 100/100 |
| Shadow Consistency | 100/100 |
| Border Radius Consistency | 80/100 |
| Accessibility | 100/100 |
| CSS Tokenization | 100/100 |

**Strengths:** Tight, disciplined color palette, Well-defined spacing scale, Clean elevation system, Strong accessibility compliance, Good CSS variable tokenization

**Issues:**
- 67 !important rules — prefer specificity over overrides
- 74% of CSS is unused — consider purging
- 4552 duplicate CSS declarations

## Z-Index Map

**10 unique z-index values** across 4 layers.

| Layer | Range | Elements |
|-------|-------|----------|
| modal | 99999998,99999998 | div.i.u.b.e.n.d.a.-.c.s.-.d.e.f.a.u.l.t.-.f.l.o.a.t.i.n.g. .i.u.b.e.n.d.a.-.c.s.-.b.o.t.t.o.m. .i.u.b.e.n.d.a.-.c.s.-.r.i.g.h.t. .i.u.b.e.n.d.a.-.c.s.-.s.l.i.d.e.i.n. .i.u.b.e.n.d.a.-.c.s.-.b.r.a.n.d.e.d. .i.u.b.e.n.d.a.-.c.s.-.p.a.d.d.e.d. .i.u.b.e.n.d.a.-.c.s.-.v.i.s.i.b.l.e |
| dropdown | 100,240 | header.s.i.t.e.-.h.e.a.d.e.r._.h.e.a.d.e.r._._.R.G.l.7.x, nav.h.e.a.d.e.r.-.n.a.v._.h.e.a.d.e.r._._.n.a.v._._.L._.o.x.P, header.s.i.t.e.-.h.e.a.d.e.r._.h.e.a.d.e.r._._.R.G.l.7.x. .s.i.t.e.-.h.e.a.d.e.r._.h.e.a.d.e.r.-.-.m.o.b.i.l.e._._.m.l.f.J.v |
| sticky | 12,12 | div, div, div |
| base | -1,3 | img.s.t.a.t.i.c.-.h.e.r.o.-.b.a.n.n.e.r._.b.a.n.n.e.r._._.c.o.v.e.r._._.p.h.M.y.S, a.b.u.t.t.o.n._.b.u.t.t.o.n._._.Z.9.Q.a.o. .b.u.t.t.o.n._.b.u.t.t.o.n.-.-.s.e.c.o.n.d.a.r.y._._.b.O.g.s.q, a.b.u.t.t.o.n._.b.u.t.t.o.n._._.Z.9.Q.a.o. .b.u.t.t.o.n._.b.u.t.t.o.n.-.-.p.r.i.m.a.r.y._._.m.I.Y.V.V |

**Issues:**
- [object Object]

## SVG Icons

**37 unique SVG icons** detected. Dominant style: **filled**.

| Size Class | Count |
|------------|-------|
| sm | 26 |
| md | 11 |

**Icon colors:** `currentColor`

## Font Files

| Family | Source | Weights | Styles |
|--------|--------|---------|--------|
| Inter | self-hosted | 100 900 | normal |
| serrifCondensed | self-hosted | 400, 500 | normal |
| tiemposText | self-hosted | 400, 500, 600, 700 | normal, italic |

## Image Style Patterns

| Pattern | Count | Key Styles |
|---------|-------|------------|
| thumbnail | 38 | objectFit: contain, borderRadius: 0px, shape: square |
| general | 3 | objectFit: cover, borderRadius: 12px, shape: rounded |
| hero | 3 | objectFit: cover, borderRadius: 0px, shape: square |

**Aspect ratios:** 2.73:1 (22x), 1:1 (6x), 5.83:1 (4x), 3.43:1 (3x), 16:9 (3x), 2:3 (3x), 4.34:1 (1x), 5.82:1 (1x)

## Motion Language

**Feel:** smooth · **Scroll-linked:** yes

### Duration Tokens

| name | value | ms |
|---|---|---|
| `xs` | `130ms` | 130 |
| `sm` | `160ms` | 160 |
| `md` | `300ms` | 300 |
| `xl` | `800ms` | 800 |

### Easing Families

- **ease-in-out** (24 uses) — `ease`
- **ease-out** (17 uses) — `cubic-bezier(0.246, 0.75, 0.187, 1)`
- **linear** (1 uses) — `linear`
- **ease-in** (1 uses) — `cubic-bezier(0.55, 0.055, 0.675, 0.19)`

### Keyframes In Use

| name | kind | properties | uses |
|---|---|---|---|
| `logo-garden_slide__phNeK` | slide-x | transform | 2 |

## Component Anatomy

### card — 38 instances

**Slots:** media

### button — 23 instances

**Slots:** label
**Variants:** secondary · primary

| variant | count | sample label |
|---|---|---|
| default | 17 | Product |
| secondary | 4 | Discover Billing |
| primary | 2 | Reject all |

### link — 3 instances


## Brand Voice

**Tone:** friendly · **Pronoun:** you-only · **Headings:** Title Case (tight)

### Top CTA Verbs

- **get** (3)
- **discover** (3)
- **book** (2)
- **product** (1)
- **solutions** (1)
- **developers** (1)
- **resources** (1)
- **support** (1)

### Button Copy Patterns

- "get started" (3×)
- "book a demo" (2×)
- "product" (1×)
- "solutions" (1×)
- "developers" (1×)
- "resources" (1×)
- "support" (1×)
- "login" (1×)
- "discover billing" (1×)
- "discover profitwell metrics" (1×)

### Sample Headings

> Sell globally.
Grow without the complexity.
> Merchant of Record platform
> Billing
> ProfitWell Metrics
> Retain

## Page Intent

**Type:** `landing` (confidence 0.29)
**Description:** Increase revenue, reduce risk and reduce cost with Paddle, the payment solution powering global revenue for n8n, Letterboxd & AdGuard. One platform that handles billing, tax and compliance.

Alternates: legal (0.4)

## Section Roles

Reading order (top→bottom): feature-grid → nav → cta → nav → pricing-table → footer → nav

| # | Role | Heading | Confidence |
|---|------|---------|------------|
| 0 | cta | — | 0.75 |
| 1 | nav | — | 0.9 |
| 2 | feature-grid | — | 0.8 |
| 3 | nav | — | 0.9 |
| 4 | pricing-table | Sell globally.
Grow without the complexity. | 0.9 |
| 5 | footer | — | 0.95 |
| 6 | nav | — | 0.9 |

## Material Language

**Label:** `flat` (confidence 0)

| Metric | Value |
|--------|-------|
| Avg saturation | 0.244 |
| Shadow profile | soft |
| Avg shadow blur | 0px |
| Max radius | 120px |
| backdrop-filter in use | no |
| Gradients | 0 |

## Imagery Style

**Label:** `photography` (confidence 0.25)
**Counts:** total 44, svg 15, icon 9, screenshot-like 0, photo-like 22
**Dominant aspect:** ultra-wide
**Radius profile on images:** square

## Quick Start

To recreate this design in a new project:

1. **Install fonts:** Add `Inter` from Google Fonts or your font provider
2. **Import CSS variables:** Copy `variables.css` into your project
3. **Tailwind users:** Use the generated `tailwind.config.js` to extend your theme
4. **Design tokens:** Import `design-tokens.json` for tooling integration
