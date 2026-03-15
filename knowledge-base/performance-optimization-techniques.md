# Web Performance Optimization Techniques - Comprehensive Knowledge Base

> Compiled from web.dev official documentation. Covers HTML performance, resource loading,
> image optimization, font optimization, JavaScript code splitting, lazy loading,
> prefetching/prerendering/precaching, content-visibility CSS, AVIF compression,
> and module preloading.

---

## Table of Contents

1. [General HTML Performance](#1-general-html-performance)
2. [Resource Loading Optimization](#2-resource-loading-optimization)
3. [Image Performance](#3-image-performance)
4. [Web Font Optimization](#4-web-font-optimization)
5. [JavaScript Code Splitting](#5-javascript-code-splitting)
6. [Lazy Loading Images and Iframes](#6-lazy-loading-images-and-iframes)
7. [Prefetching, Prerendering, and Precaching](#7-prefetching-prerendering-and-precaching)
8. [CSS content-visibility Property](#8-css-content-visibility-property)
9. [AVIF Image Compression](#9-avif-image-compression)
10. [Module Preloading](#10-module-preloading)
11. [Cross-Cutting Optimization Priority Matrix](#11-cross-cutting-optimization-priority-matrix)

---

## 1. General HTML Performance

**Source**: https://web.dev/learn/performance/general-html-performance

### Core Metrics Impact

- Time to First Byte (TTFB) is the foundational metric. A high TTFB makes it challenging to reach "good" thresholds for Largest Contentful Paint (LCP) and First Contentful Paint (FCP).
- Every optimization in this section targets reducing TTFB.

### 1.1 Redirect Management

#### Same-Origin Redirects (Within Your Control)

- **Problem**: Each redirect adds an additional HTTP request-response cycle, directly increasing latency.
- **Common anti-pattern**: Redirecting from trailing slash (`example.com/page/`) to non-trailing slash (`example.com/page`) or vice versa.
- **Fix**: Link directly to the correct canonical URL. Audit internal links to eliminate redirect chains.

#### Cross-Origin Redirects (Outside Your Control)

- Created by ads, URL shorteners, and third-party services.
- Audit for redirect chains: HTTP-to-HTTPS upgrades or cross-origin-to-same-origin cascades.
- Minimize reliance on URL shorteners for critical navigation paths.

### 1.2 HTML Caching Strategies

#### Static HTML Pages

- **Recommended cache lifetime**: 5 minutes minimum for static HTML resources.
- **ETag-based validation**:
  - Server sends: `ETag: "33a64df551425fcc55e4d42a148795d9f25f89d4"`
  - Browser sends on subsequent request: `If-None-Match: "33a64df551425fcc55e4d42a148795d9f25f89d4"`
  - Server responds with `304 Not Modified` if content unchanged (no body transferred).
- **Alternative**: Use `Last-Modified` response header with date/time stamps for simpler implementations.

#### Personalized / Authenticated HTML

- **Recommendation**: Avoid caching HTML altogether for personalized or authenticated content.
- **Reason**: Browser cache cannot be invalidated by the server; stale personalized content creates security and freshness concerns.

### 1.3 Server Response Optimization

#### Dynamic vs. Static Content

- Dynamically generated responses (database queries, template rendering) produce higher TTFB than static pages.
- **Anti-pattern**: Displaying a loading spinner client-side and then fetching all data via AJAX/fetch. This moves unpredictable server work to the user's device and network.
- **Principle**: Minimize client-side effort. Server-rendered content with fast TTFB produces better user-centric metrics than client-side rendering.

#### Server-Timing Header

Provides server-side performance diagnostics visible in DevTools:

```http
Server-Timing: auth;dur=55.5, db;dur=220
```

- Multiple metrics supported, each with duration in milliseconds.
- Data is collectable via the Navigation Timing API for field (real-user) analysis.
- Use this to identify slow backend components (auth, database, template rendering).

#### Hosting Infrastructure

- Evaluate hosting providers using [ismyhostfastyet.com](https://ismyhostfastyet.com) (based on Chrome User Experience Report data).
- Shared hosting providers are often susceptible to high TTFB.
- Dedicated/cloud hosting with proper scaling produces more consistent TTFB.

### 1.4 Compression

#### Algorithm Selection

| Algorithm | Compression Improvement | Browser Support | Use Case |
|-----------|------------------------|-----------------|----------|
| **Brotli** | ~15-20% better than gzip | All major browsers | Primary algorithm |
| **Gzip** | Baseline | Universal | Fallback for legacy browsers |

#### File Size Considerations

- Files smaller than ~1 KiB compress poorly or not at all.
- Larger files compress more effectively but take significantly more time to parse and evaluate after decompression.
- Any content change alters the file hash, affecting cache efficiency.

#### Compression Timing

| Type | When Applied | Best For |
|------|-------------|----------|
| **Static compression** | Ahead of time, at build/deploy | CSS, JavaScript, SVG images, other static assets |
| **Dynamic compression** | Per-request at server | HTML (especially personalized/authenticated content) |

- Static compression removes compression latency from the server response time entirely.
- **Practical recommendation**: Delegate compression to your CDN for optimal configuration.

### 1.5 Content Delivery Networks (CDNs)

- Cache resources from origin server at geographically distributed edge locations.
- Reduce round-trip time (RTT) via physical proximity to users.
- Enable HTTP/2 or HTTP/3, advanced caching, and compression optimizations.
- Can significantly improve TTFB, especially for globally distributed audiences.

### 1.6 Priority Order

1. **Minimize redirects** (immediate TTFB impact)
2. **Implement caching strategy** (5-minute minimum for static HTML; avoid for personalized content)
3. **Optimize server response times** (hosting review, backend optimization)
4. **Enable compression** (Brotli primary, gzip fallback)
5. **Deploy CDN** for edge delivery

---

## 2. Resource Loading Optimization

**Source**: https://web.dev/learn/performance/optimize-resource-loading

### Core Concepts

#### Render-Blocking Resources

- **CSS is render-blocking by design**: The browser halts rendering until the CSSOM (CSS Object Model) is constructed to prevent Flash of Unstyled Content (FOUC).
- This is intentional behavior but must be minimized through CSS optimization.

#### Parser-Blocking Resources

- A `<script>` element without `async` or `defer` attributes blocks the HTML parser.
- Scripts may modify the DOM during construction, which is why this behavior exists.
- The parser cannot continue until the script downloads, parses, and executes.

#### The Preload Scanner

- The browser's secondary HTML parser scans raw HTML to speculatively discover and fetch resources before the primary parser reaches them.
- This is a critical performance optimization built into all modern browsers.

**Resources NOT discoverable by the preload scanner:**

| Resource Type | Why Hidden |
|--------------|-----------|
| CSS `background-image` properties | Requires CSSOM construction |
| Dynamically injected `<script>` elements | Added via JavaScript |
| Dynamic `import()` calls | JavaScript runtime decision |
| Client-rendered HTML | Generated after JavaScript execution |
| CSS `@import` declarations | Sequential loading after parent CSS |

- For unavoidable late-discovered resources, use `rel="preload"` resource hints.

### 2.1 CSS Optimization Techniques

#### Minification

Remove whitespace, comments, and unnecessary characters:

```css
/* Before */
h1 {
  font-size: 2em;
  color: #000000;
}

/* After minification */
h1{font-size:2em;color:#000}
```

#### Remove Unused CSS

- Use Chrome DevTools **Coverage** tool (Ctrl+Shift+P > "Show Coverage") to identify unused styles.
- Focus on substantial unused portions that can be split into separate files or deleted.
- Critical for reducing render-blocking CSS payload.

#### Avoid CSS @import Declarations

```css
/* ANTI-PATTERN: Creates request chains, downloads consecutively */
@import url('reset.css');
@import url('typography.css');
```

```html
<!-- CORRECT: Concurrent downloading -->
<link rel="stylesheet" href="reset.css">
<link rel="stylesheet" href="typography.css">
```

- `@import` creates sequential request chains that delay initial render.
- Multiple `<link>` elements allow concurrent/parallel downloading.

#### Inline Critical CSS

```html
<head>
  <style>
    /* Critical CSS for above-the-fold content */
    .hero { display: flex; align-items: center; }
    .nav { position: fixed; top: 0; }
  </style>
  <!-- Load remaining CSS asynchronously -->
  <link rel="stylesheet" href="non-critical.css" media="print" onload="this.media='all'">
</head>
```

- Critical CSS = styles required to render content visible within the initial viewport.
- Place essential styles in `<head>` via `<style>` tags.
- Load remaining CSS asynchronously at body end or with media-swap pattern.
- **Trade-off**: Inlined CSS adds HTML bytes and does NOT cache independently across pages.

### 2.2 JavaScript Optimization Techniques

#### async vs. defer Attributes

```html
<!-- Downloads in parallel, executes IMMEDIATELY when ready (may be out of order) -->
<script src="analytics.js" async></script>

<!-- Downloads in parallel, executes AFTER document parsing (maintains order) -->
<script src="app.js" defer></script>

<!-- type="module" is deferred by default -->
<script type="module" src="module.js"></script>
```

| Attribute | Download | Execution Timing | Order Preserved |
|-----------|----------|------------------|-----------------|
| None | Blocks parser | Immediately, blocks parser | Yes |
| `async` | Parallel | Immediately when downloaded | No |
| `defer` | Parallel | After HTML parsing complete | Yes |
| `type="module"` | Parallel | After HTML parsing (deferred by default) | Yes |

**Guidelines**:
- Use `defer` for scripts that need DOM access and must execute in order.
- Use `async` for independent scripts (analytics, tracking) that don't depend on DOM or other scripts.
- `type="module"` automatically defers; no additional attribute needed.

#### Avoid Client-Side Rendering of Critical Content

- Markup rendered by JavaScript sidesteps the preload scanner.
- Creates critical request chains and long tasks.
- **Never render LCP elements with JavaScript** if they can be server-rendered.
- Client-side rendering generates long tasks that harm INP (Interaction to Next Paint).

#### JavaScript Minification and Uglification

- **Minification**: Removes whitespace and comments.
- **Uglification**: Shortens variable and function names (`scriptElement` becomes `t`).
- Both reduce file size and improve download speed.

### 2.3 Implementation Priority

1. **Remove unused CSS** (measurable impact on FCP/LCP)
2. **Minify CSS and JavaScript** (quick wins via bundlers)
3. **Replace `@import` with `<link>`** (immediate optimization)
4. **Inline critical CSS** (test trade-offs first)
5. **Apply `defer` to non-critical scripts** (safe parser unblocking)
6. **Avoid client-side rendering of critical content** (architectural decision)

---

## 3. Image Performance

**Source**: https://web.dev/learn/performance/image-performance

### Key Fact

Images are the heaviest and most prevalent resource on the web. Optimizing dimensions, formats, and compression directly reduces Largest Contentful Paint (LCP).

### 3.1 Image Sizing and Device Pixel Ratio (DPR)

- A 500x500px CSS container needs a 500x500px image at 1x DPR, 1000x1000px at 2x DPR, 1500x1500px at 3x DPR.
- Modern devices (iPhones, flagship Android) commonly have 2x or 3x DPR.
- Serving oversized images wastes bandwidth; serving undersized images appears blurry.

#### srcset with Pixel Density Descriptors

```html
<img
  alt="Product photo"
  width="500"
  height="500"
  src="/image-500.jpg"
  srcset="/image-500.jpg 1x, /image-1000.jpg 2x, /image-1500.jpg 3x"
>
```

- Browser selects the appropriate source based on device DPR.
- `1x` for standard displays, `2x` for Retina/HiDPI, `3x` for ultra-high density.

#### srcset with Width Descriptors + sizes Attribute

For responsive layouts where image display size changes across viewports:

```html
<img
  alt="Product photo"
  width="500"
  height="500"
  src="/image-500.jpg"
  srcset="/image-500.jpg 500w, /image-1000.jpg 1000w, /image-1500.jpg 1500w"
  sizes="(min-width: 768px) 500px, 100vw"
>
```

**How the browser calculates the correct image**:
1. Read the `sizes` attribute to determine CSS display width for the current viewport.
2. Multiply by device DPR: `CSS width x DPR = required device pixels`.
3. Select the closest `srcset` candidate that meets or exceeds that pixel count.

**Example**: 320px viewport, 3x DPR, displayed at `100vw`:
- Required: 320 x 3 = 960 device pixels
- Selected: `1000w` image (closest >= 960)

**Critical requirement**: Width descriptors (`w`) MUST be paired with a `sizes` attribute. Without `sizes`, width descriptors do not work.

### 3.2 Image File Formats

| Format | Type | Transparency | Animation | Browser Support | Best For |
|--------|------|-------------|-----------|----------------|----------|
| **AVIF** | Lossy + Lossless | Yes | Yes | Chrome 85+, Firefox, Safari 16.4+ | Photos, complex images (best compression) |
| **WebP** | Lossy + Lossless | Yes | Yes | All modern browsers | Photos, graphics (good compression) |
| **JPEG** | Lossy only | No | No | Universal | Photos (legacy fallback) |
| **PNG** | Lossless only | Yes | No | Universal | Graphics with transparency (legacy) |
| **GIF** | Lossless | Yes (1-bit) | Yes | Universal | Simple animations (limited 256 colors) |
| **SVG** | Vector | Yes | Yes | Universal | Icons, logos, line art, diagrams |

- **AVIF** offers >50% savings compared to JPEG in some cases. Supports Wide Color Gamut (WCG) and High Dynamic Range (HDR).
- **WebP** offers better compression than JPEG, PNG, or GIF with both lossy and lossless modes. Widely supported.
- Use AVIF as primary, WebP as first fallback, JPEG/PNG as final fallback.

### 3.3 Compression Techniques

#### Lossy Compression

- Works through quantization and chroma subsampling (discarding color information).
- Most effective on high-density images with lots of noise and colors (photographs).
- **Avoid on**: Line art, sharp edges, high-contrast text on flat backgrounds (prone to visible artifacts).

#### Lossless Compression

- Reduces file size by encoding pixels based on differences from neighboring pixels.
- No data loss; pixel-perfect reproduction.
- Applicable to: GIF, PNG, WebP, AVIF.
- Use for: Screenshots, diagrams, graphics with text.

#### Tools

- **Squoosh** (web app): Interactive compression comparison.
- **ImageOptim** (macOS): Batch lossless optimization.
- **svgo** (Node.js): SVG minification and optimization.
- Automatic image CDNs (Cloudinary, imgix, Cloudflare Images).

### 3.4 The `<picture>` Element

#### Format Fallback Pattern

```html
<picture>
  <source type="image/avif" srcset="image.avif">
  <source type="image/webp" srcset="image.webp">
  <img
    alt="Product photo"
    width="500"
    height="500"
    src="/image.jpg"
  >
</picture>
```

- Browser selects the first `<source>` whose `type` it supports.
- Order matters: most modern format first, legacy fallback last.
- The `<img>` element is required and serves as the ultimate fallback.

#### Responsive + Format Fallback

```html
<picture>
  <source
    type="image/avif"
    srcset="/image-500.avif 500w, /image-1000.avif 1000w, /image-1500.avif 1500w"
    sizes="(min-width: 768px) 500px, 100vw"
  >
  <source
    type="image/webp"
    srcset="/image-500.webp 500w, /image-1000.webp 1000w, /image-1500.webp 1500w"
    sizes="(min-width: 768px) 500px, 100vw"
  >
  <img
    alt="Product photo"
    width="500"
    height="500"
    src="/image-500.jpg"
    srcset="/image-500.jpg 500w, /image-1000.jpg 1000w, /image-1500.jpg 1500w"
    sizes="(min-width: 768px) 500px, 100vw"
  >
</picture>
```

#### Art Direction with Media Queries

```html
<picture>
  <source
    media="(min-width: 561px)"
    srcset="/image-desktop.jpg, /image-desktop-2x.jpg 2x"
  >
  <source
    media="(max-width: 560px)"
    srcset="/image-mobile.jpg, /image-mobile-2x.jpg 2x"
  >
  <img src="/image-desktop.jpg" alt="Product photo" width="500" height="500">
</picture>
```

- `media` attributes on `<source>` are **commands** (not hints) -- the browser must obey them.
- Use for serving different image crops or compositions for different viewport sizes.

### 3.5 Mobile-Specific Considerations

Limit image variants served to mobile to reduce bandwidth:

```html
<picture>
  <source
    media="(min-width: 561px)"
    srcset="/image-500.jpg, /image-1000.jpg 2x, /image-1500.jpg 3x"
  >
  <source
    media="(max-width: 560px)"
    srcset="/image-500.jpg 1x, /image-1000.jpg 2x"
  >
  <img src="/image-500.jpg" alt="..." width="500" height="500">
</picture>
```

- Prevents serving 3x images on small viewports even with high DPR.
- Reduces bandwidth while maintaining acceptable quality perception on small screens.

### 3.6 Server-Side Format Negotiation (Accept Header)

```javascript
if (request.headers.accept) {
  if (request.headers.accept.includes('image/avif')) {
    return reply.from('image.avif');
  } else if (request.headers.accept.includes('image/webp')) {
    return reply.from('image.webp');
  }
}
return reply.from('image.jpg');
```

**Critical**: Include `Vary: Accept` in response headers so CDNs cache different formats separately for the same URL.

### 3.7 Lazy Loading Images

```html
<img loading="lazy" src="image.jpg" alt="..." width="500" height="500">
```

- Defers image download until the image is in or near the viewport.
- Saves bandwidth by prioritizing above-the-fold content.
- **Never lazy-load the LCP image** (hero image, above-fold images).
- Always specify `width` and `height` to prevent layout shifts.

### 3.8 Decoding Attribute

```html
<img decoding="async" src="large-image.jpg" alt="...">
```

| Value | Behavior |
|-------|----------|
| `async` | Decode asynchronously; improves render time for other content |
| `sync` | Decode synchronously; present with other content simultaneously |
| `auto` | Browser decides (default) |

- Effects only noticeable on large, high-resolution images with long decode times.

### 3.9 SVG Optimization

- SVG is text-based vector format ideal for line art, diagrams, charts, logos, and icons.
- Optimize with **svgo** (Node.js tool): minification, compression, lossy optimization of path data.
- SVG compresses well with Brotli/gzip since it is XML text.

### 3.10 Anti-Patterns

1. Serving oversized images (wasted bandwidth, slower load).
2. Serving only one image size for all viewports and DPRs.
3. Using only JPEG/PNG when WebP/AVIF are widely supported.
4. Missing `width` and `height` attributes (causes layout shifts / CLS).
5. Lazy-loading above-the-fold or LCP candidate images.
6. Using lossy compression on line art, text, or sharp-edge graphics.

---

## 4. Web Font Optimization

**Source**: https://web.dev/learn/performance/optimize-web-fonts

### 4.1 Font Discovery and Loading

#### How Browsers Discover Fonts

1. Browser parses HTML, encounters `<link>` to external CSS (or inline `<style>`).
2. Browser downloads and parses CSS, finds `@font-face` declarations.
3. Browser determines which fonts are actually needed by matching selectors to DOM elements.
4. Browser downloads only the needed font files.

**Key insight**: Fonts are NOT downloaded until the browser determines they are needed for the current page layout. The `@font-face` declaration alone does not trigger a download.

#### Preload Fonts for Early Discovery

```html
<link rel="preload" as="font" href="/fonts/OpenSans-Regular-webfont.woff2" crossorigin>
```

- Bypasses the stylesheet download-parse-match delay.
- The `crossorigin` attribute is **mandatory for all fonts**, including self-hosted ones, because fonts are CORS resources.
- **Caution**: Overusing preload risks diverting bandwidth from more critical resources. Only preload fonts used above the fold.

#### Inline @font-face Declarations

```html
<head>
  <style>
    @font-face {
      font-family: 'Open Sans';
      src: url('/fonts/OpenSans-Regular.woff2') format('woff2');
      font-display: swap;
    }
  </style>
</head>
```

- Enables earlier font discovery than external stylesheets.
- **Limitation**: The browser only begins downloading font files after ALL render-blocking resources have been loaded. External CSS still blocks font downloads even with inlined `@font-face`.

### 4.2 Font File Optimization

#### WOFF2 Format

- **WOFF2 provides up to 30% better compression than WOFF**.
- Wide browser support across all modern browsers.
- WOFF2 should be the only format you serve unless targeting very old browsers.

```css
@font-face {
  font-family: 'MyFont';
  src: url('myfont.woff2') format('woff2');
  /* No need for WOFF, EOT, or TTF fallbacks for modern browsers */
}
```

#### Self-Hosting vs. Third-Party CDN

| Approach | Pros | Cons |
|----------|------|------|
| **Self-hosting** | No cross-origin connection overhead; full control over caching; faster in most scenarios | Requires CDN setup, HTTP/2+, proper caching headers |
| **Third-party (e.g., Google Fonts)** | Easy setup; automatic subsetting | Requires cross-origin connections; slower due to additional DNS+TCP+TLS roundtrips |

- **Recommendation**: Self-host fonts with CDN, HTTP/2 or HTTP/3, and proper caching headers.
- If using third-party, add preconnect hints.

#### Preconnect for Third-Party Fonts

```html
<!-- Google Fonts requires TWO preconnect hints (CSS and font files are on different origins) -->
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
```

### 4.3 Font Subsetting

Removes unused glyphs to significantly reduce file size.

#### Google Fonts Subsetting

```html
<!-- Latin subset only -->
<link href="https://fonts.googleapis.com/css?family=Roboto&subset=latin" rel="stylesheet">

<!-- Extreme subsetting: only specific characters -->
<link href="https://fonts.googleapis.com/css?family=Monoton&text=Welcome" rel="stylesheet">
```

#### Self-Hosted Subsetting Tools

- **glyphanger**: Analyzes pages to determine required glyphs, generates subsets.
- **subfont**: Automated subsetting for self-hosted fonts.
- **pyftsubset** (fonttools): Python-based font subsetting.

#### unicode-range in @font-face

```css
@font-face {
  font-family: 'MyFont';
  src: url('myfont-latin.woff2') format('woff2');
  unicode-range: U+0000-00FF, U+0131, U+0152-0153;
}

@font-face {
  font-family: 'MyFont';
  src: url('myfont-cyrillic.woff2') format('woff2');
  unicode-range: U+0400-045F, U+0490-0491, U+04B0-04B1;
}
```

- Browser only downloads the font file whose `unicode-range` matches characters on the page.
- Useful for multi-language sites serving different character sets.

### 4.4 font-display Property

Controls how text renders while web fonts load:

| Value | Block Period | Swap Period | Behavior | CLS Risk | Best For |
|-------|------------|------------|----------|----------|----------|
| `block` | Up to 3s (Chrome/Firefox); infinite (Safari) | Infinite | Invisible text until font loads | None | Icon fonts (where fallback is meaningless) |
| `swap` | ~0ms | Infinite | Show fallback immediately, swap when ready | **High** | Body text (content visibility priority) |
| `fallback` | ~100ms | ~3s | Brief block, then fallback, then swap if ready | Medium | Balanced approach |
| `optional` | ~100ms | 0ms | Use font only if loaded within 100ms; otherwise use fallback for entire page visit | **None** | Performance-first; font cached for next visit |

```css
@font-face {
  font-family: 'MyFont';
  src: url('myfont.woff2') format('woff2');
  font-display: swap; /* Most widely used value */
}
```

**Recommendations**:
- `swap` for body text where content visibility is priority.
- `optional` for the best performance (eliminates layout shift entirely).
- `fallback` as a balanced middle ground.
- `block` only for icon fonts or decorative fonts where fallback text would be meaningless.

### 4.5 Anti-Patterns

1. **Inlining font files as base64**: Increases HTML payload size, defeats caching, and delays other resource discovery through preload scanner interference.
2. **Loading too many font weights/styles**: Each weight/style is a separate file download.
3. **Not specifying `crossorigin` on font preload links**: Font will be fetched twice (once without CORS, once with).
4. **Using multiple font formats when WOFF2 suffices**: Unnecessary bytes in CSS.
5. **Not using `font-display`**: Defaults to `block`, causing invisible text (FOIT).

### 4.6 Variable Fonts

- A single variable font file can replace multiple static font files (regular, bold, italic, etc.).
- Reduces total download size when using multiple weights/styles of the same family.
- Supported in all modern browsers.

```css
@font-face {
  font-family: 'MyVariableFont';
  src: url('myfont-variable.woff2') format('woff2-variations');
  font-weight: 100 900; /* Range of weights in single file */
  font-display: swap;
}
```

---

## 5. JavaScript Code Splitting

**Source**: https://web.dev/learn/performance/code-split-javascript

### 5.1 Why Code Split

- Reduces initial JavaScript payload sent to the browser.
- Improves page load responsiveness and Interaction to Next Paint (INP).
- Lighthouse warns when JavaScript execution exceeds 2 seconds and fails above 3.5 seconds.
- Total Blocking Time (TBT) has high correlation with INP, indicating users frequently interact during initial load.

### 5.2 Dynamic import() Syntax

The primary code-splitting mechanism in modern JavaScript:

```javascript
// STATIC IMPORT (loaded immediately, bundled together)
import { validateForm } from './validate-form.mjs';

// DYNAMIC IMPORT (loaded on demand, separate chunk)
document.querySelector('#myForm').addEventListener('blur', async () => {
  const { validateForm } = await import('./validate-form.mjs');
  validateForm();
}, { once: true });
```

- `import()` is an asynchronous, function-like expression.
- Returns a Promise that resolves to the module.
- Bundlers automatically create separate chunks for dynamic imports.

### 5.3 Bundler Configuration

#### Webpack SplitChunksPlugin

```javascript
// webpack.config.js
module.exports = {
  optimization: {
    splitChunks: {
      chunks: 'all', // Split both async and initial imports
      maxSize: 50000, // Subdivide chunks larger than 50KB
    },
  },
};
```

| `chunks` Value | Behavior |
|----------------|----------|
| `async` (default) | Only handles dynamic `import()` calls |
| `initial` | Processes static imports only |
| `all` | Splits both, enables sharing chunks between async and initial |

- `maxSize` subdivides large scripts to prevent long tasks that block the main thread.

#### Other Bundlers

- **Rollup**: Automatic code splitting on dynamic `import()`.
- **esbuild**: Requires explicit opt-in for code splitting (`splitting: true`).
- **Parcel**: Automatic code splitting on dynamic `import()`.
- **Vite**: Uses Rollup under the hood; automatic code splitting.

### 5.4 Framework Integration

#### React

```jsx
import React, { lazy, Suspense } from 'react';

// React.lazy wraps dynamic import
const LazyComponent = lazy(() => import('./HeavyComponent'));

function App() {
  return (
    <Suspense fallback={<div>Loading...</div>}>
      <LazyComponent />
    </Suspense>
  );
}
```

#### Next.js

```javascript
import dynamic from 'next/dynamic';

const DynamicComponent = dynamic(() => import('../components/HeavyComponent'), {
  loading: () => <p>Loading...</p>,
});
```

### 5.5 Streaming Compilation Preservation

V8 JavaScript engine offers streaming compilation optimizations. To preserve them:

1. Transform source code to avoid JavaScript modules (transpile to IIFE/CommonJS for production).
2. Use `.mjs` extension for module-based JavaScript in production builds.

### 5.6 Bundle Size Trade-offs

| Approach | Pros | Cons |
|----------|------|------|
| **Larger bundles** | Better compression ratios | Increased script evaluation time; longer initial load |
| **Smaller bundles** | Improved caching efficiency; faster individual chunk parsing | Reduced compression effectiveness; more HTTP requests |

### 5.7 Identifying Code-Splitting Candidates

- **Chrome DevTools Coverage tool**: Identifies unused JavaScript during page load.
- **Lighthouse**: Reports per-file execution times; highlights scripts exceeding thresholds.
- **webpack-bundle-analyzer**: Visualizes chunk sizes and composition.

### 5.8 Common Splitting Strategies

| Strategy | Description | Best For |
|----------|-------------|----------|
| **Route-based** | Split by page/route | Multi-page apps, SPAs |
| **Component-based** | Split by UI component | Heavy components (modals, charts, editors) |
| **Vendor splitting** | Separate third-party libraries | Libraries that change less frequently than app code |
| **Interaction-based** | Load on user interaction | Form validation, search, tooltips |

---

## 6. Lazy Loading Images and Iframes

**Source**: https://web.dev/learn/performance/lazy-load-images-and-iframe-elements

### 6.1 The `loading` Attribute

```html
<!-- Lazy load: defers until near viewport -->
<img loading="lazy" src="offscreen-image.jpg" alt="..." width="600" height="400">

<!-- Eager load: immediate download (default behavior) -->
<img loading="eager" src="hero-image.jpg" alt="..." width="1200" height="600">
```

| Value | Behavior |
|-------|----------|
| `eager` | Default. Load immediately regardless of viewport position. |
| `lazy` | Defer loading until the element approaches the visible viewport. Distance thresholds vary by browser. |

**Browser support**: Supported in all major browsers for both `<img>` and `<iframe>` elements. No polyfill necessary.

### 6.2 Critical Rules

#### Never Lazy-Load LCP Candidates

- Hero images and above-the-fold content MUST use `loading="eager"` (or omit the attribute entirely).
- Different viewport sizes, aspect ratios, and devices display varying amounts of vertical content.
- What is "above the fold" on desktop may be below the fold on mobile (and vice versa).
- **Lazy-loaded images must wait for complete layout calculations** before the browser determines viewport proximity, delaying requests beyond the preload scanner phase.

#### Always Specify Dimensions

```html
<!-- CORRECT: Dimensions specified -->
<img loading="lazy" src="image.jpg" alt="..." width="600" height="400">

<!-- ANTI-PATTERN: No dimensions = layout shifts -->
<img loading="lazy" src="image.jpg" alt="...">
```

- Without `width` and `height`, the browser cannot reserve space, causing Cumulative Layout Shift (CLS).

#### Picture Element Usage

```html
<!-- Apply loading="lazy" to the <img> element, NOT the <picture> -->
<picture>
  <source type="image/avif" srcset="image.avif">
  <source type="image/webp" srcset="image.webp">
  <img loading="lazy" src="image.jpg" alt="..." width="600" height="400">
</picture>
```

### 6.3 Iframe Lazy Loading

```html
<iframe
  loading="lazy"
  src="https://www.youtube.com/embed/VIDEO_ID"
  width="560"
  height="315"
  title="Video title"
></iframe>
```

- Defers loading the entire HTML document and all its subresources.
- Significant savings: YouTube embeds save >500 KiB; Facebook Like button saves >200 KiB.
- Chrome reserves space with placeholders for lazy-loaded iframes.
- Always specify `width` and `height` attributes.

### 6.4 The Facade Pattern

Replace resource-heavy third-party embeds with static placeholders; load the real embed only on user interaction.

```html
<!-- Static facade: lightweight poster image -->
<div class="video-facade" onclick="loadYouTube(this)">
  <img src="video-thumbnail.jpg" alt="Video title">
  <button aria-label="Play video">Play</button>
</div>

<script>
function loadYouTube(facade) {
  const iframe = document.createElement('iframe');
  iframe.src = 'https://www.youtube.com/embed/VIDEO_ID?autoplay=1';
  iframe.width = 560;
  iframe.height = 315;
  facade.replaceWith(iframe);
}
</script>
```

**Available facade libraries**:
- `lite-youtube-embed`: Lightweight YouTube embed facade.
- `lite-vimeo-embed`: Lightweight Vimeo embed facade.
- React Live Chat Loader: Chat widget facades.

### 6.5 JavaScript-Based Lazy Loading (for Unsupported Elements)

For elements where `loading="lazy"` is not available (`<video>`, CSS `background-image`, `poster` attributes):

```html
<video class="lazy" autoplay loop muted playsinline width="320" height="480">
  <source data-src="video.webm" type="video/webm">
  <source data-src="video.mp4" type="video/mp4">
</video>
```

Libraries like **lazysizes** and **yall.js** use the Intersection Observer API to:
1. Observe elements with a `lazy` class.
2. Swap `data-src` to `src` when the element enters the viewport.
3. Trigger download and playback.

### 6.6 Fetch Priority + Loading Attribute Interaction

```html
<!-- High priority but still lazy: waits for CSS before loading -->
<img loading="lazy" fetchpriority="high" src="image.jpg" alt="...">
```

- `fetchpriority` adjusts network priority independently of `loading`.
- An image with `fetchpriority="high"` and `loading="lazy"` still waits until CSS is downloaded and parsed and the image is determined to be near the viewport.
- These are separate concerns; use them independently based on need.

### 6.7 Anti-Patterns

1. Lazy-loading above-the-fold or LCP-candidate images.
2. Using JavaScript lazy-loading libraries when native `loading="lazy"` is sufficient (harms INP).
3. Omitting dimensions on lazy-loaded elements (causes CLS).
4. Assuming uniform viewport behavior across devices and orientations.
5. Lazy-loading small, critical UI images (logos, navigation icons).

---

## 7. Prefetching, Prerendering, and Precaching

**Source**: https://web.dev/learn/performance/prefetching-prerendering-precaching

### 7.1 Prefetching Resources

```html
<head>
  <!-- Prefetch a script needed on the next page -->
  <link rel="prefetch" as="script" href="/date-picker.js">

  <!-- Prefetch CSS needed on the next page -->
  <link rel="prefetch" as="style" href="/date-picker.css">

  <!-- Prefetch a full page document -->
  <link rel="prefetch" href="/next-page" as="document">
</head>
```

| Characteristic | Detail |
|---------------|--------|
| **Priority** | Lowest priority; avoids contending with current page resources |
| **Storage** | HTTP cache |
| **Browser behavior** | Discretionary -- browser MAY ignore based on network quality, system preferences, or Data Saver mode |
| **Browser support** | All modern browsers except Safari (behind flag) |

**When to use**:
- Resources likely needed within seconds (modals, date pickers, next page content).
- Only on fast connections; check for Data Saver.
- Avoid cross-origin document prefetching (creates duplicate requests).

### 7.2 Speculation Rules API

Modern alternative to `<link rel="prefetch">` for page prefetching and prerendering (Chromium-based browsers):

#### Prefetch via Speculation Rules

```html
<script type="speculationrules">
{
  "prefetch": [{
    "source": "list",
    "urls": ["/page-a", "/page-b"]
  }]
}
</script>
```

**Key difference from `<link rel="prefetch">`**: Speculation Rules prefetches are stored in **memory cache** (faster retrieval) rather than HTTP cache.

#### Prerender via Speculation Rules

```html
<script type="speculationrules">
{
  "prerender": [{
    "source": "list",
    "urls": ["/page-a", "/page-b"]
  }]
}
</script>
```

- **Prerendering** goes further than prefetching: it fetches, processes, and **fully renders** the entire page in a hidden background tab.
- JavaScript on the prerendered page is executed.
- When the user navigates, the prerendered page is activated instantly (near-zero navigation time).
- **Use sparingly**: Only when fairly certain the user intends to navigate to the prerendered page. Prerendering is computationally expensive and uses significant bandwidth.

#### Eagerness Levels

```html
<script type="speculationrules">
{
  "prerender": [{
    "source": "document",
    "where": { "href_matches": "/*" },
    "eagerness": "moderate"
  }]
}
</script>
```

| Eagerness | Trigger |
|-----------|---------|
| `immediate` | As soon as rules are observed |
| `eager` | Similar to immediate (behavior may change) |
| `moderate` | On hover for 200ms |
| `conservative` | On pointer/touch down |

#### Dynamic Speculation Rules via JavaScript

```javascript
const defined = document.createElement('script');
defined.type = 'speculationrules';
defined.textContent = JSON.stringify({
  prefetch: [{
    source: 'list',
    urls: ['/next-page'],
  }],
});
document.head.append(defined);
```

### 7.3 Quicklink Library

Dynamically prefetches visible links within the viewport:

```html
<script src="https://unpkg.com/quicklink@2/dist/quicklink.umd.js"></script>
<script>quicklink.listen();</script>
```

- Observes links in the viewport using Intersection Observer.
- Prefetches their targets at idle time.
- Respects Data Saver and slow connections.

### 7.4 Service Worker Precaching

Cache resources during service worker installation for instant retrieval:

#### Using Workbox

```javascript
import { precacheAndRoute } from 'workbox-precaching';

// Precache manifest (generated at build time)
precacheAndRoute([
  { url: '/styles/product-page.ac29.css', revision: null }, // Hash in filename
  { url: '/index.html', revision: '518747aa' }, // No hash; revision tracked
]);
```

| Characteristic | Detail |
|---------------|--------|
| **Strategy** | Cache-only (resources served from Cache API, not network) |
| **When** | During service worker installation |
| **Storage** | Cache API (NOT HTTP cache; controlled by JavaScript) |
| **Versioning** | Workbox tracks revisions; automatically removes expired entries |
| **Browser support** | Widely supported across modern browsers |

**Use case**: Precache CSS, JavaScript, and font files for commonly navigated pages (e.g., precache product detail page assets while on product listing page).

### 7.5 Comparison Matrix

| Technique | When Loaded | Storage | Renders Page | Browser Support | Bandwidth Cost |
|-----------|-------------|---------|-------------|----------------|---------------|
| `<link rel="prefetch">` | Low priority, at browser discretion | HTTP cache | No | All except Safari | Low |
| Speculation Rules (prefetch) | Per eagerness setting | Memory cache | No | Chromium | Low |
| Speculation Rules (prerender) | Per eagerness setting | Memory cache | Yes (full render + JS execution) | Chromium | High |
| Service Worker precaching | At SW installation | Cache API | No | Wide | Varies |

### 7.6 Anti-Patterns

1. **Prefetching too aggressively on slow connections**: Check `navigator.connection.saveData` and `navigator.connection.effectiveType`.
2. **Prerendering uncertain navigations**: Wastes significant CPU and bandwidth.
3. **Precaching too many resources**: Better to precache too little than too much. Use runtime caching for less-certain resources.
4. **Cross-origin document prefetching**: Creates duplicate requests.
5. **Ignoring the Data Saver signal**: Always respect user preferences for reduced data usage.

### 7.7 Implementation Priority

1. **Service Worker precaching** (most reliable, broad support, offline capability)
2. **`<link rel="prefetch">`** for near-term resources (widely supported, low risk)
3. **Speculation Rules** for navigation optimization (Chromium only, highest impact)

---

## 8. CSS content-visibility Property

**Source**: https://web.dev/articles/content-visibility

### 8.1 Property Values

```css
.element {
  content-visibility: auto;    /* Automatic containment; skip rendering when off-screen */
  content-visibility: hidden;  /* Always skip rendering; preserve cached state */
  content-visibility: visible; /* Default behavior; no containment */
}
```

| Value | Behavior | Containment Applied | Rendering State |
|-------|----------|-------------------|-----------------|
| `visible` | Normal rendering | None | Always rendered |
| `auto` | Skip rendering when off-screen | layout, style, paint (+ size when off-screen) | Cached when off-screen |
| `hidden` | Never render regardless of position | layout, style, paint, size | Cached but not displayed |

### 8.2 CSS Containment Types Used

| Type | Effect |
|------|--------|
| `size` | Element can be laid out without examining descendants |
| `layout` | Descendants cannot affect external page layout |
| `style` | Property effects cannot escape the element |
| `paint` | Descendants do not display outside the element bounds |

### 8.3 contain-intrinsic-size

When `content-visibility: auto` applies size containment to off-screen elements, the element has zero height by default (its contents are not rendered). This causes scrollbar jumping and incorrect page height.

```css
.content-section {
  content-visibility: auto;
  contain-intrinsic-size: auto 1000px;
}
```

- Provides a placeholder height (1000px) when content is not rendered.
- The `auto` keyword tells the browser to remember the last-rendered size and use that instead of the placeholder on subsequent visits (essential for infinite scrollers and back-navigation).

#### Shorthand Variants

```css
/* Single value: applied to both width and height */
contain-intrinsic-size: 1000px;

/* Two values: width then height */
contain-intrinsic-size: auto 0px auto 1000px;

/* Individual properties */
contain-intrinsic-width: auto 0px;
contain-intrinsic-height: auto 1000px;
```

### 8.4 Performance Impact

**Measured results**:
- Travel blog example: rendering time reduced from **232ms to 30ms** (7.7x improvement).
- Expected reduction: **50% or more** from rendering costs on content-heavy pages.
- Facebook experiment: Up to **250ms navigation improvement** with cached views.
- Direct INP (Interaction to Next Paint) metric improvements through reduced main-thread work.

### 8.5 Implementation Pattern

```css
/* Apply to repeating content sections */
.article-section,
.comment-block,
.product-card,
.feed-item {
  content-visibility: auto;
  contain-intrinsic-size: auto 500px; /* Estimated height */
}
```

Best applied to:
- Long-form articles with many sections.
- Comment threads.
- Product listing pages.
- Social media feeds.
- Any page with significant off-screen content.

### 8.6 content-visibility: hidden vs. Alternatives

| Property | Rendering State | Takes Space | Updates While Hidden | Re-render Cost |
|----------|----------------|-------------|---------------------|---------------|
| `display: none` | Destroyed | No | No | Full re-render (expensive) |
| `visibility: hidden` | Maintained | Yes | Yes (continues updating) | None (already rendered) |
| `content-visibility: hidden` | Cached/preserved | No | No | Cheap (uses cached state) |

- Use `content-visibility: hidden` for SPA inactive views, tab panels, off-screen slide content.
- Significantly cheaper to show/hide than `display: none` because rendering state is preserved.

### 8.7 Browser Support

| Browser | Version |
|---------|---------|
| Chrome/Edge | 85+ |
| Firefox | 125+ |
| Safari | 18+ |

Baseline: Newly available as of September 15, 2025.

### 8.8 Accessibility Considerations

- `content-visibility: auto` **preserves content in the accessibility tree** (unlike `visibility: hidden`).
- Screen readers can still access off-screen content; in-page search (Ctrl+F) still works.
- **Caution**: Landmark elements (`<nav>`, `<header>`, `<footer>`, `<main>`, `<aside>`) may clutter the accessibility tree when off-screen.

```html
<!-- Apply aria-hidden to landmarks that are off-screen to prevent accessibility tree clutter -->
<section class="offscreen-section" content-visibility="auto" aria-hidden="true">
  <nav>...</nav>
</section>
```

### 8.9 Anti-Patterns

1. **Not specifying `contain-intrinsic-size`**: Causes scrollbar jumping and incorrect page length.
2. **Using on above-the-fold content**: Adds overhead without benefit (content is always visible).
3. **Calling DOM APIs on skipped subtrees**: May force rendering; Chromium logs console warnings.
4. **Applying to very small elements**: Overhead of containment may exceed rendering savings.

---

## 9. AVIF Image Compression

**Source**: https://web.dev/articles/compress-images-avif

### 9.1 Compression Performance

- AVIF offers **greater than 50% file size reduction** compared to JPEG in some cases.
- Based on the AV1 video codec by the Alliance for Open Media.
- Supports both lossy and lossless encoding modes.

### 9.2 AVIF Advanced Features

| Feature | Description |
|---------|-------------|
| **HDR** | High Dynamic Range support |
| **WCG** | Wide Color Gamut support |
| **Film grain synthesis** | Artificial film grain added during decode (encode smaller, decode with grain) |
| **Progressive decoding** | Spatial scalability (low-res preview first) and quality scalability (gradual improvement) |
| **Lossless mode** | Pixel-perfect compression for line art/screenshots |
| **Alpha channel** | Separate quality control for transparency |

### 9.3 Encoding Libraries

| Library | Description | Used By |
|---------|-------------|---------|
| **libaom** | Reference AV1 encoder/decoder (Alliance for Open Media) | Direct CLI usage |
| **libavif** | AVIF muxing/parsing reference implementation | Chrome decoder |
| **libheif** | Alternative implementation | ImageMagick, libvips, sharp (Node.js) |

### 9.4 Command-Line Encoding with avifenc

#### Basic Usage

```bash
./avifenc [options] input.jpg output.avif
```

#### Recommended Quality Settings

```bash
# Standard lossy encoding (recommended)
./avifenc --min 0 --max 63 -a end-usage=q -a cq-level=18 -a tune=ssim input.jpg output.avif

# With alpha channel (separate alpha quality)
./avifenc --min 0 --max 63 --minalpha 0 --maxalpha 63 \
  -a end-usage=q -a cq-level=18 -a tune=ssim input.png output.avif

# Separate color and alpha quality levels
./avifenc --min 0 --max 63 --minalpha 0 --maxalpha 63 \
  -a end-usage=q -a color:cq-level=18 -a alpha:cq-level=10 \
  -a tune=ssim input.png output.avif
```

#### Multi-Threaded Encoding

```bash
# Use 8 threads for ~5x faster encoding
./avifenc --min 0 --max 63 -a end-usage=q -a cq-level=18 \
  -a tune=ssim --jobs 8 input.jpg output.avif
```

### 9.5 Key Parameters Reference

| Parameter | Range | Description | Recommendation |
|-----------|-------|-------------|----------------|
| `cq-level` | 0-63 | Constrained quality level (lower = higher quality) | 18-25 for web photos |
| `--min` / `--max` | 0-63 | Min/max quantizer for color | 0 and 63 respectively (let cq-level control) |
| `--minalpha` / `--maxalpha` | 0-63 | Min/max quantizer for alpha channel | 0 and 63 respectively |
| `--speed` | 0-10 | Encoder speed (lower = better compression, slower) | 6 (default, good balance) |
| `--tune` | ssim / psnr | Quality optimization metric | ssim (perceptual quality) |
| `--jobs` | Integer | Worker threads for parallel encoding | Number of CPU cores |
| `end-usage` | q / vbr / cbr / cq | Rate control mode | q (constant quality) |

### 9.6 Performance Improvements (libaom 2.0 to 3.1)

- **5x reduction** in memory usage.
- **6.5x reduction** in CPU usage (speed=6, cq-level=18 for 8.1 MP images).
- Multi-threading and tiled encoding optimizations.
- All-intra encoding mode support.

### 9.7 Node.js Integration

```javascript
// Using sharp (Node.js)
const sharp = require('sharp');

await sharp('input.jpg')
  .avif({ quality: 50 }) // 0-100, maps to cq-level internally
  .toFile('output.avif');
```

```javascript
// Using imagemin-avif
const imagemin = require('imagemin');
const imageminAvif = require('imagemin-avif');

await imagemin(['images/*.jpg'], {
  destination: 'build/images',
  plugins: [
    imageminAvif({ quality: 50 })
  ]
});
```

### 9.8 HTML Implementation

```html
<!-- Progressive enhancement with fallbacks -->
<picture>
  <source type="image/avif" srcset="photo.avif">
  <source type="image/webp" srcset="photo.webp">
  <img src="photo.jpg" alt="Description" width="800" height="600">
</picture>

<!-- With responsive sizes -->
<picture>
  <source
    type="image/avif"
    srcset="photo-400.avif 400w, photo-800.avif 800w, photo-1200.avif 1200w"
    sizes="(min-width: 768px) 800px, 100vw"
  >
  <source
    type="image/webp"
    srcset="photo-400.webp 400w, photo-800.webp 800w, photo-1200.webp 1200w"
    sizes="(min-width: 768px) 800px, 100vw"
  >
  <img
    src="photo-800.jpg"
    srcset="photo-400.jpg 400w, photo-800.jpg 800w, photo-1200.jpg 1200w"
    sizes="(min-width: 768px) 800px, 100vw"
    alt="Description"
    width="800"
    height="600"
  >
</picture>
```

### 9.9 When to Use AVIF

| Scenario | Use AVIF? | Reason |
|----------|-----------|--------|
| Photographs (lossy) | Yes | Best compression ratios |
| Graphics with transparency | Yes | Superior alpha channel compression |
| HDR/WCG content | Yes | Only modern format with full support |
| Line art / screenshots (lossless) | Yes | Good lossless compression |
| Animated images | Consider | Supports animation but limited tooling |
| Legacy browser requirement | No (as sole format) | Must provide fallbacks |
| Real-time encoding needed | Caution | Encoding is slower than JPEG/WebP |

### 9.10 Browser Support

| Browser | AVIF Support |
|---------|-------------|
| Chrome | 85+ |
| Firefox | 93+ |
| Safari | 16.4+ |
| Edge | 121+ |

Always provide WebP and JPEG fallbacks via `<picture>` element.

---

## 10. Module Preloading

**Source**: https://web.dev/articles/modulepreload

### 10.1 The Problem with Regular Preload for Modules

Standard `<link rel="preload">` fails for ES modules due to three issues:

| Problem | Detail |
|---------|--------|
| **Credentials mode mismatch** | `type="module"` scripts use `omit` credentials mode by default; `<link rel="preload">` cannot replicate this without complex attribute synchronization |
| **No module-aware compilation** | Regular preload caches the file but does not compile it as a module; compilation is deferred until execution, losing the performance benefit |
| **No dependency discovery** | Modules have import chains; regular preload does not traverse or prefetch dependencies |

### 10.2 modulepreload Syntax

```html
<head>
  <!-- Preload a module and its dependencies -->
  <link rel="modulepreload" href="critical-module.mjs">

  <!-- The module script that will use it -->
  <script type="module" src="critical-module.mjs"></script>
</head>
```

**Advantages over regular preload**:
- Credentials mode defaults work correctly without manual configuration.
- Browser can parse and compile the module during the preload phase.
- Some browsers will recursively discover and preload dependencies.

### 10.3 Dependency Chain Handling

The specification permits but does not require recursive dependency preloading. For cross-browser reliability, explicitly list all modules in the dependency tree:

```html
<!-- Flat list of entire dependency tree -->
<link rel="modulepreload" href="app.mjs">
<link rel="modulepreload" href="router.mjs">
<link rel="modulepreload" href="store.mjs">
<link rel="modulepreload" href="utils.mjs">
<link rel="modulepreload" href="api-client.mjs">
```

- Browsers that support recursive loading will handle deduplication automatically.
- Browsers that do not will still benefit from the explicit list.

### 10.4 Browser Support

| Browser | Version |
|---------|---------|
| Chrome | 66+ |
| Edge | 79+ |
| Firefox | 115+ |
| Safari | 17+ |

Baseline: Newly available as of September 18, 2023.

### 10.5 Performance Implications

- Maximizes bandwidth utilization during network roundtrips by exposing dependency information upfront.
- Primary benefit emerges with deep dependency trees where serial roundtrips would otherwise cascade.
- **Current best practice**: Still bundle applications into chunks rather than relying entirely on module granularity. Modulepreload complements bundling, not replaces it.

### 10.6 Implementation Pattern

```html
<head>
  <!-- Preload the main entry point and critical dependencies -->
  <link rel="modulepreload" href="/js/app.mjs">
  <link rel="modulepreload" href="/js/router.mjs">
  <link rel="modulepreload" href="/js/critical-component.mjs">

  <!-- Non-critical modules loaded normally -->
  <script type="module" src="/js/app.mjs"></script>
</head>
```

### 10.7 Anti-Patterns

1. **Using `<link rel="preload" as="script">` for modules**: Does not compile as module; wastes the preload benefit.
2. **Assuming recursive loading works in all browsers**: Explicitly list dependency tree.
3. **Replacing bundling with modulepreload alone**: Module parsing overhead remains measurable; bundling provides more predictable performance.
4. **Preloading too many modules**: Only preload critical-path modules needed for initial render.

---

## 11. Cross-Cutting Optimization Priority Matrix

### Tier 1: Critical (Implement First)

These optimizations have the highest impact on Core Web Vitals and are relatively straightforward to implement.

| Optimization | Primary Metric Impact | Effort |
|-------------|----------------------|--------|
| Enable Brotli compression (gzip fallback) | TTFB, FCP, LCP | Low (server/CDN config) |
| Serve images in AVIF/WebP with JPEG fallback | LCP | Medium (build pipeline) |
| Add `width` and `height` to all images | CLS | Low (HTML attributes) |
| Use `loading="lazy"` on below-fold images | LCP (indirect, bandwidth) | Low (HTML attribute) |
| Minify CSS and JavaScript | FCP, LCP | Low (build tool config) |
| Use `defer` on non-critical scripts | FCP, LCP, TBT | Low (HTML attribute) |
| Remove unused CSS | FCP, LCP | Medium (analysis required) |
| Deploy CDN | TTFB | Medium (infrastructure) |

### Tier 2: High Impact (Implement Second)

| Optimization | Primary Metric Impact | Effort |
|-------------|----------------------|--------|
| Implement responsive images (srcset + sizes) | LCP, bandwidth | Medium (multiple image sizes) |
| Code-split JavaScript (dynamic imports) | TBT, INP | Medium (bundler config) |
| Optimize web fonts (WOFF2, font-display, subsetting) | FCP, CLS | Medium |
| Inline critical CSS | FCP | Medium (tool integration) |
| Self-host fonts with preload | FCP | Medium |
| Eliminate render-blocking resources | FCP, LCP | Medium |
| Replace CSS @import with <link> | FCP | Low |

### Tier 3: Advanced (Implement Third)

| Optimization | Primary Metric Impact | Effort |
|-------------|----------------------|--------|
| Implement `content-visibility: auto` | INP, rendering time | Low (CSS property) |
| Prefetch/prerender likely navigation targets | Next-page LCP | Medium |
| Service worker precaching (Workbox) | Repeat visit LCP, offline | High |
| Implement facade pattern for third-party embeds | LCP, TBT | Medium |
| Use `<link rel="modulepreload">` for critical modules | FCP, TBT | Low |
| Use fetchpriority="high" on LCP image | LCP | Low |
| Server-side content negotiation (Accept header for images) | LCP | Medium |
| Use Speculation Rules API | Next-page metrics | Low-Medium |

### Tier 4: Fine-Tuning

| Optimization | Primary Metric Impact | Effort |
|-------------|----------------------|--------|
| Variable fonts (replace multiple static fonts) | FCP | Medium |
| Image decoding="async" on large images | Rendering smoothness | Low |
| unicode-range subsetting for multi-language | FCP | Medium |
| SVG optimization with svgo | Rendering | Low |
| Static pre-compression at build time | TTFB | Low |
| Server-Timing headers for diagnostics | Debugging | Low |

---

## Quick Reference: HTML Attributes and CSS Properties

### HTML Attributes for Performance

```html
<!-- Images -->
<img loading="lazy" decoding="async" fetchpriority="high"
     width="800" height="600"
     src="image.jpg" srcset="..." sizes="...">

<!-- Scripts -->
<script defer src="app.js"></script>
<script async src="analytics.js"></script>
<script type="module" src="module.mjs"></script>

<!-- Resource Hints -->
<link rel="preload" as="font" href="font.woff2" crossorigin>
<link rel="preload" as="image" href="hero.avif">
<link rel="preconnect" href="https://cdn.example.com">
<link rel="prefetch" as="document" href="/next-page">
<link rel="modulepreload" href="module.mjs">

<!-- Stylesheets -->
<link rel="stylesheet" href="critical.css">
<link rel="stylesheet" href="non-critical.css" media="print" onload="this.media='all'">
```

### CSS Properties for Performance

```css
/* Content visibility for off-screen rendering optimization */
.section {
  content-visibility: auto;
  contain-intrinsic-size: auto 500px;
}

/* Font display control */
@font-face {
  font-family: 'MyFont';
  src: url('font.woff2') format('woff2');
  font-display: swap;        /* or: optional, fallback, block */
  unicode-range: U+0000-00FF; /* Latin subset */
}

/* CSS containment (manual) */
.widget {
  contain: layout style paint;
}
```

### JavaScript Patterns for Performance

```javascript
// Dynamic import for code splitting
const module = await import('./heavy-module.mjs');

// Intersection Observer for custom lazy loading
const observer = new IntersectionObserver((entries) => {
  entries.forEach(entry => {
    if (entry.isIntersecting) {
      const img = entry.target;
      img.src = img.dataset.src;
      observer.unobserve(img);
    }
  });
});

// Speculation Rules (dynamic)
const rules = document.createElement('script');
rules.type = 'speculationrules';
rules.textContent = JSON.stringify({
  prerender: [{ source: 'list', urls: ['/likely-next-page'] }]
});
document.head.append(rules);

// Service Worker precaching with Workbox
import { precacheAndRoute } from 'workbox-precaching';
precacheAndRoute(self.__WB_MANIFEST);
```

---

## Mobile-Specific Considerations Summary

1. **Images**: Limit maximum image resolution served to mobile (skip 3x on small viewports). Use art direction via `<picture>` to serve different crops for mobile.

2. **Fonts**: Use `font-display: optional` on slow mobile connections to prevent layout shift. Subset fonts aggressively for mobile-first pages.

3. **JavaScript**: Code splitting is even more critical on mobile due to slower CPU and limited memory. Keep initial JS bundle under 50KB compressed.

4. **Lazy loading**: Mobile viewports show less content initially, so more content qualifies for lazy loading. But be careful: what's below-fold on desktop may be visible on mobile.

5. **Prefetching/Prerendering**: Respect `navigator.connection.saveData` and `navigator.connection.effectiveType`. Avoid prefetching on slow or metered connections.

6. **content-visibility**: Particularly beneficial on mobile where rendering budget is tighter and content-heavy pages cause more jank.

7. **Compression**: Brotli is supported on all modern mobile browsers. The bandwidth savings are proportionally more impactful on mobile networks.

8. **CDN**: Critical for mobile users who may have higher latency connections. Edge locations reduce round-trip time significantly.

---

## Core Web Vitals Mapping

| Metric | What It Measures | Key Optimizations |
|--------|-----------------|-------------------|
| **LCP** (Largest Contentful Paint) | Time to render the largest visible element | Image optimization, preload LCP resource, fetchpriority="high", CDN, compression, eliminate render-blocking resources |
| **INP** (Interaction to Next Paint) | Responsiveness to user interactions | Code splitting, defer/async scripts, content-visibility, reduce main thread work, avoid long tasks |
| **CLS** (Cumulative Layout Shift) | Visual stability during loading | width/height on images, font-display: optional/fallback, contain-intrinsic-size, avoid injecting content above existing content |
| **FCP** (First Contentful Paint) | Time to first visible content | Inline critical CSS, remove unused CSS, font optimization, compression, minimize redirects |
| **TTFB** (Time to First Byte) | Server response time | CDN, caching, compression, minimize redirects, optimize server infrastructure |

---

*Last updated: 2026-03-15*
*Sources: web.dev/learn/performance, web.dev/articles*
