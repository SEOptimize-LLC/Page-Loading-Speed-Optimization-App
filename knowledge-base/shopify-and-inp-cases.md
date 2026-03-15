# Shopify Performance Optimization & INP Case Studies

> **Last Updated:** March 2026
> **Purpose:** Comprehensive reference for Shopify-specific page speed optimization and real-world INP (Interaction to Next Paint) case studies with actionable techniques.

---

## Table of Contents

- [Part 1: Shopify Performance Optimization](#part-1-shopify-performance-optimization)
  - [1. Shopify Performance Landscape](#1-shopify-performance-landscape)
  - [2. Core Web Vitals on Shopify](#2-core-web-vitals-on-shopify)
  - [3. LCP Optimization (Largest Contentful Paint)](#3-lcp-optimization-largest-contentful-paint)
  - [4. CLS Optimization (Cumulative Layout Shift)](#4-cls-optimization-cumulative-layout-shift)
  - [5. INP Optimization (Interaction to Next Paint)](#5-inp-optimization-interaction-to-next-paint)
  - [6. Shopify Liquid Template Optimization](#6-shopify-liquid-template-optimization)
  - [7. Image Optimization & Shopify CDN](#7-image-optimization--shopify-cdn)
  - [8. Font Loading Optimization](#8-font-loading-optimization)
  - [9. JavaScript & Render-Blocking Resources](#9-javascript--render-blocking-resources)
  - [10. Third-Party App & Script Management](#10-third-party-app--script-management)
  - [11. Theme Selection & Optimization](#11-theme-selection--optimization)
  - [12. Mobile-Specific Optimization](#12-mobile-specific-optimization)
  - [13. Lazy Loading Implementation](#13-lazy-loading-implementation)
  - [14. Checkout Performance](#14-checkout-performance)
  - [15. Performance Measurement Tools](#15-performance-measurement-tools)
- [Part 2: INP Case Studies](#part-2-inp-case-studies)
  - [Case Study 1: QuintoAndar](#case-study-1-quintoandar)
  - [Case Study 2: Disney+ Hotstar](#case-study-2-disney-hotstar)
  - [Case Study 3: PubConsent (PubTech)](#case-study-3-pubconsent-pubtech)
  - [Cross-Cutting INP Lessons](#cross-cutting-inp-lessons)

---

## Part 1: Shopify Performance Optimization

### 1. Shopify Performance Landscape

#### Platform Baseline Performance

Shopify provides significant built-in performance advantages that many platforms do not offer:

- **Global CDN**: Shopify includes a world-class Content Delivery Network at no additional cost, ensuring fast delivery of assets worldwide.
- **Automatic Image Conversion**: When you upload PNG or JPEG images, Shopify automatically generates WebP versions and serves them to supported browsers, typically reducing file size by 25-35% without quality loss.
- **Base Load Time**: Shopify loads fast out-of-the-box with an average load time of approximately 1.2 seconds on a clean install.
- **HTTP/2 Support**: Shopify's servers support HTTP/2, enabling multiplexed connections for faster parallel resource loading.

#### How Performance Degrades

Despite the strong baseline, performance degrades through a predictable pattern:

1. **App accumulation** -- every installed app can inject JavaScript globally across all pages
2. **Theme customization bloat** -- adding sections, features, and custom code without performance audits
3. **Unoptimized media** -- large hero images, uncompressed product photos, auto-playing videos
4. **Third-party scripts** -- analytics, chat widgets, review platforms, tracking pixels, heatmaps
5. **Liquid template complexity** -- nested loops, redundant queries, excessive filter chains

#### Business Impact

- Over 47% of users expect a website to load in 2 seconds or less
- Every one-second improvement in page load time boosts conversions by approximately 2%
- A one-second delay reduces conversions by approximately 7%
- 18% of shoppers abandon carts because checkout is slow or confusing
- If checkout takes more than 30 seconds, 50% of US shoppers are less likely to complete the purchase

---

### 2. Core Web Vitals on Shopify

#### Current Shopify Median Performance

Based on real-world Chrome User Experience Report (CrUX) data:

| Metric | Shopify Median | Good Threshold | Shopify Status |
|--------|---------------|----------------|----------------|
| **LCP** | Varies widely | < 2.5 seconds | Most common failure point |
| **CLS** | 0.01 | < 0.1 | Excellent (rarely a problem) |
| **INP** | 153ms | < 200ms | Generally good, but at risk |

**Key insight**: LCP is where Shopify stores most commonly fail Core Web Vitals. CLS is typically excellent out of the box. INP is within the "good" range for most stores but can degrade quickly with app bloat.

#### Primary Causes of CWV Failure on Shopify

1. **Installed apps** injecting JavaScript globally across every page
2. **Unoptimized hero images** (the LCP element on most homepages)
3. **Third-party scripts** (reviews, chat widgets, tracking pixels)
4. **Heavy themes** with excessive built-in features that load whether used or not
5. **Render-blocking CSS and JavaScript** delaying first paint

---

### 3. LCP Optimization (Largest Contentful Paint)

LCP measures how quickly the main content of a page becomes visible. On Shopify stores, the LCP element is typically the hero image on the homepage, the main product image on product pages, or a large heading/banner.

#### Identifying the LCP Element

Use Chrome DevTools Performance panel or PageSpeed Insights to identify which element is the LCP element on each page template. Common LCP elements on Shopify:

- **Homepage**: Hero/slideshow image or banner
- **Collection page**: Collection header image or first product image
- **Product page**: Main product image
- **Blog page**: Featured image or article title

#### Critical LCP Fixes for Shopify

##### 1. Preload the LCP Image

Add a preload hint in the `<head>` section of `theme.liquid` or the relevant section file:

```liquid
<link rel="preload"
      as="image"
      href="{{ section.settings.image | image_url: width: 1200 }}"
      fetchpriority="high">
```

##### 2. Never Lazy-Load the LCP Image

The LCP image must load immediately. Ensure it uses `loading="eager"` (or simply omit the `loading` attribute) and add `fetchpriority="high"`:

```liquid
<img src="{{ section.settings.image | image_url: width: 1200 }}"
     width="1200"
     height="700"
     fetchpriority="high"
     decoding="async"
     alt="{{ section.settings.image.alt }}">
```

##### 3. Remove JavaScript That Hides the Hero

Common offenders include:
- Fade-in animations (`opacity: 0` until JavaScript runs)
- Slideshow initialization delays
- CSS transforms controlled by JavaScript (`visibility: hidden`, `transform: translateY()`)

These patterns can add multiple seconds to LCP. A simple `opacity: 0` transition controlled by JS can prevent the LCP element from being registered until the script executes.

##### 4. Optimize Image Size and Format

- Hero images should be 150-250 KB maximum (WebP/AVIF)
- Request the nearest displayed width from Shopify's CDN (1200-1600px for desktop hero, 600-800px for mobile)
- Enable WebP/AVIF delivery (automatic through Shopify CDN)
- Use `srcset` to serve different sizes for different viewports

##### 5. Minimize Render-Blocking Resources

- Defer non-critical CSS and JavaScript
- Inline critical CSS needed for above-the-fold rendering
- Move scripts to just before `</body>` when possible

#### Real-World LCP Result

A store that removed the hero fade-in animation, preloaded the exact hero image, and deferred chat and heatmap scripts saw mobile LCP improve from **3.6s to 2.2s**, with add-to-cart rate increasing **+9.4%** week-over-week.

---

### 4. CLS Optimization (Cumulative Layout Shift)

CLS measures how much a webpage shifts unexpectedly during loading. While Shopify's median CLS of 0.01 is excellent, specific patterns can cause poor scores.

#### Five Primary CLS Issues on Shopify

##### 1. Images Without Dimension Reservations

**Problem**: When the browser renders a page without knowing image dimensions, it initially treats the image height as zero. When the image loads, the content below shifts down.

**Solutions**:
- Always add `height` and `width` HTML attributes to images
- Use Shopify's `image_tag` Liquid filter, which automatically embeds dimensions
- Apply CSS `aspect-ratio` property for dimension maintenance
- Use `object-fit: cover` when cropping images within containers

```liquid
<!-- Automatic dimensions with image_tag -->
{{ product.featured_image | image_url: width: 600 | image_tag }}

<!-- Manual with aspect ratio -->
<div style="aspect-ratio: 16/9;">
  {{ section.settings.image | image_url: width: 1200 | image_tag }}
</div>
```

##### 2. App-Injected Content Without Reserved Space

**Problem**: Shopify apps and third-party scripts inject content (banners, popups, review widgets) after the page has started rendering, causing content below to shift.

**Solutions**:
- Set `min-height` on app block containers:
  ```css
  .shopify-app-block {
    min-height: 23px;
  }
  ```
- Reposition injected elements beside static content of equal or greater height
- Use CSS next-sibling combinators and `:not()` pseudo-classes for non-app-block injections
- Position widgets below the fold when possible
- If CLS is caused by an app, contact the app developer or replace the app

##### 3. CSS Loading Strategy Issues

**Problem**: Lazy-loading stylesheets using async patterns causes render delays and layout shifts when styles are applied late.

**Solutions**:
- Avoid async CSS patterns for above-fold content
- Keep CSS render-blocking for above-fold sections (this is intentional and correct)
- Only apply async loading to below-fold sections using Liquid `section.index`
- Test performance impact with WebPageTest before implementing async CSS

##### 4. Animation-Triggered Shifts

**Problem**: Incorrect animation approaches using `top`, `bottom`, `left`, `right` properties generate CLS scores.

**Solutions**:
- Replace position-based animations with `transform: translateY()` or `transform: translateX()`
- Use hardware-accelerated transforms for smoother performance
- Respect `prefers-reduced-motion` media queries for accessibility

##### 5. Web Font Swap Shifts

**Problem**: When `font-display: swap` is used, the fallback font renders first. If it has different metrics than the custom font, content shifts when the custom font loads.

**Solutions**:
- Implement CSS font descriptors to match fallback font metrics:
  ```css
  @font-face {
    font-family: 'Custom Font Fallback';
    src: local('Arial');
    size-adjust: 105%;
    ascent-override: 95%;
    descent-override: 22%;
    line-gap-override: 0%;
  }
  ```
- Use tools like Fallback Font Generator to calculate the correct metric overrides
- Limit to 2-3 font weights to reduce swap opportunities

#### CLS Detection Tools

- **Chrome DevTools**: Disable cache, throttle network, observe visual shifts during page load
- **WebPageTest**: View Web Vitals section showing every frame with layout shifts (pink highlights indicate shifted content)
- **Web Vitals Chrome Extension**: Outputs shift details to browser console with element identification
- **PageSpeed Insights**: Filter results for CLS diagnostics with visual problem identification

---

### 5. INP Optimization (Interaction to Next Paint)

INP measures the time between a user interaction (click, tap, keypress) and the next visual update on screen. Unlike First Input Delay (FID), which only measured the first interaction, INP measures all interactions throughout the session and reports the worst one.

#### Three Components of INP

Every interaction has three measurable phases:

1. **Input Delay** -- time between user action and when event handlers begin executing (caused by other tasks blocking the main thread)
2. **Processing Time** -- time spent running JavaScript event handlers in response to the interaction
3. **Presentation Delay** -- time for the browser to recalculate layout, apply styles, and paint the visual update

The total of these three phases determines the INP score.

#### Good/Needs Improvement/Poor Thresholds

| Rating | INP Value |
|--------|-----------|
| Good | <= 200ms |
| Needs Improvement | 200-500ms |
| Poor | > 500ms |

#### Common Causes of Poor INP on Shopify

1. **Too much JavaScript loaded on every page** -- especially from multipurpose apps and tag managers
2. **Long tasks on the main thread** -- JavaScript execution blocks that exceed 50ms prevent the browser from responding to interactions
3. **Third-party script interference** -- analytics, marketing tags, and chat widgets that fire heavy JavaScript on user interaction
4. **Layout thrashing** -- JavaScript that reads and writes DOM layout properties in rapid succession, forcing the browser to recalculate layout repeatedly
5. **Inefficient theme JavaScript** -- unoptimized event handlers, missing debouncing, excessive DOM manipulation
6. **JavaScript framework overhead** -- themes using Vue, React, or other frameworks without proper optimization

#### Shopify-Specific INP Fixes

##### 1. Template-Level Script Loading

Move from "load on every page" to template-level loading:
- Use App Embeds or theme app extensions to load scripts only where needed
- Load review widget scripts only on product pages
- Load search scripts only on search and collection pages
- Schedule analytics and marketing tags after first paint or on interaction

##### 2. App Audit and Cleanup

- Remove apps that are no longer actively used
- Replace multi-tool apps with lighter single-purpose alternatives
- Evaluate the trade-off between each app's features and its performance cost
- Check if apps inject scripts globally or only on relevant pages

##### 3. Defer Non-Essential JavaScript

```html
<!-- Use defer for scripts that depend on DOM order -->
<script src="analytics.js" defer></script>

<!-- Use async for independent scripts -->
<script src="tracking.js" async></script>
```

Use `requestIdleCallback` to delay background functionality until the browser is idle:

```javascript
if ('requestIdleCallback' in window) {
  requestIdleCallback(() => {
    // Initialize non-critical features
    initChatWidget();
    loadHeatmapScript();
  });
}
```

##### 4. Break Long Tasks with Yielding

When event handlers must perform significant work, yield to the main thread periodically:

```javascript
function yieldToMain() {
  return new Promise(resolve => {
    setTimeout(resolve, 0);
  });
}

// Usage in event handlers
async function handleFilterClick() {
  showLoadingSpinner();
  await yieldToMain(); // Let browser paint the spinner
  await applyFilters();
  await yieldToMain(); // Let browser paint results
  hideLoadingSpinner();
}
```

##### 5. Debounce and Throttle Interactions

Prevent excessive processing on rapid interactions:

```javascript
// Debounce search input
const debouncedSearch = debounce((query) => {
  performSearch(query);
}, 300);

searchInput.addEventListener('input', (e) => {
  debouncedSearch(e.target.value);
});
```

---

### 6. Shopify Liquid Template Optimization

Poorly optimized Liquid code is found in approximately 83% of analyzed themes, adding 2-4 seconds to load time. Liquid is server-side rendered, so optimization reduces Time to First Byte (TTFB) and accelerates overall page delivery.

#### Performance Targets

| Metric | Target | Maximum |
|--------|--------|---------|
| Total Liquid render time | 200ms | 500ms |
| Time to First Byte (TTFB) | < 600ms | < 800ms |

#### Loop Optimization

Loops are the most common source of Liquid performance problems.

**Bad -- Unrestricted loop with nested logic:**
```liquid
{% for product in collection.products %}
  {% for variant in product.variants %}
    {% if variant.available %}
      <!-- Processing every variant of every product -->
    {% endif %}
  {% endfor %}
{% endfor %}
```

**Good -- Limited loop with pre-filtered data:**
```liquid
{% for product in collection.products limit: 6 %}
  {% assign first_available = product.selected_or_first_available_variant %}
  <!-- Use the pre-selected variant -->
{% endfor %}
```

**Rules:**
- Always use `limit` on `for` loops when displaying a specific count
- Use `sort_by` at the collection level rather than sorting inside the loop
- Avoid nested loops; they multiply processing time exponentially
- Never query data inside loops; fetch once and store in a variable

#### Variable Caching

Store calculated values to avoid redundant processing:

```liquid
<!-- Bad: Recalculates on every use -->
{% if product.compare_at_price | minus: product.price > 0 %}
  Save {{ product.compare_at_price | minus: product.price | money }}
{% endif %}

<!-- Good: Calculate once, use the variable -->
{% assign savings = product.compare_at_price | minus: product.price %}
{% assign savings_percent = savings | times: 100 | divided_by: product.compare_at_price %}
{% if savings > 0 %}
  Save {{ savings | money }} ({{ savings_percent }}% off)
{% endif %}
```

#### Use `render` Instead of `include`

The `render` tag provides better performance isolation than `include`:

```liquid
<!-- Bad: include shares parent scope (slower) -->
{% include 'product-card' %}

<!-- Good: render has isolated scope (faster) -->
{% render 'product-card', product: product, show_price: true %}
```

Pass individual values rather than entire objects when possible to minimize data transfer between scopes.

#### Conditional Logic Optimization

- Place the most likely-to-fail condition first in AND operations (short-circuit evaluation)
- Replace deep `if-elsif-else` chains with `case-when` statements
- Pre-calculate boolean conditions and store in variables:

```liquid
{% assign is_sale = false %}
{% if product.compare_at_price > product.price %}
  {% assign is_sale = true %}
{% endif %}

<!-- Use the cached boolean multiple times -->
{% if is_sale %}<span class="sale-badge">Sale</span>{% endif %}
```

#### Filter Efficiency

Expensive filters include: `where`, `map`, complex image transformations, and JSON parsing.

- Minimize filter chaining
- Cache expensive filter results in variables
- Never use expensive filters inside loops

#### Whitespace Stripping

Use the `-` character in Liquid tags to strip whitespace, reducing HTML size by 5-10%:

```liquid
{%- assign title = product.title -%}
{%- if title != blank -%}
  <h2>{{ title }}</h2>
{%- endif -%}
```

#### Use `capture` for Repeated Complex HTML

```liquid
{% capture price_display %}
  <span class="price">{{ product.price | money }}</span>
  {% if product.compare_at_price > product.price %}
    <span class="compare-price">{{ product.compare_at_price | money }}</span>
  {% endif %}
{% endcapture %}

<!-- Use price_display variable multiple times without re-rendering -->
{{ price_display }}
```

#### Offload Complex Logic

Move complex calculations out of Liquid templates:
- Use metafields to store pre-calculated values
- Use the Storefront API for data-intensive operations
- Move computational logic to backend scripts or edge functions

---

### 7. Image Optimization & Shopify CDN

#### Shopify's Image Infrastructure

Shopify's CDN provides automatic image optimization:

- **Automatic format conversion**: Serves WebP to supported browsers, AVIF where supported, with JPEG/PNG fallback
- **Dynamic resizing**: Generates resized variants on-the-fly via URL parameters
- **Global edge caching**: Images are served from the closest CDN node to the visitor
- **No additional cost**: Included with every Shopify plan

#### Using the `image_url` Filter

The `image_url` filter accesses Shopify's image API for optimized delivery:

```liquid
<!-- Basic usage with width -->
{{ product.featured_image | image_url: width: 600 }}

<!-- Combined with image_tag for complete HTML -->
{{ product.featured_image | image_url: width: 600 | image_tag }}
```

The `image_tag` filter automatically:
- Adds `width` and `height` attributes (preventing CLS)
- Applies `loading="lazy"` for images in sections lower on the page
- Generates proper `alt` attributes

#### Implementing Responsive Images with srcset

Serve appropriately sized images for each device:

```liquid
{{ section.settings.image | image_url: width: 600 | image_tag:
    widths: '300, 600, 900, 1200',
    sizes: '(min-width: 1200px) 600px, (min-width: 800px) 50vw, 100vw',
    style: 'width: 100%; height: auto;' }}
```

#### Recommended Image Sizes by Context

| Context | Width Range | Notes |
|---------|-------------|-------|
| Hero/Banner (desktop) | 1200-1600px | Preload, fetchpriority="high" |
| Hero/Banner (mobile) | 600-800px | Use `<picture>` for art direction |
| Product grid | 400-600px | Lazy load, use srcset |
| Product page main | 800-1200px | Consider zoom requirements |
| Thumbnails | 100-200px | Lazy load |
| Blog featured image | 600-1000px | Lazy load below fold |

#### DPR Capping for Mobile

Prevent unnecessary 3x+ resolution downloads on mobile:

```liquid
<picture>
  <source media="(max-width: 800px)"
    srcset="{{ section.settings.image | image_url: width: 400 }} 1x,
            {{ section.settings.image | image_url: width: 800 }} 2x">
  {{ section.settings.image | image_url: width: 1600 | image_tag:
      widths: '800, 1200, 1600',
      sizes: '(min-width: 1000px) 760px, 100vw' }}
</picture>
```

Most users cannot distinguish between 2x and 3x+ resolution at typical viewing distances, so capping at 2x saves significant bandwidth.

#### Art Direction with `<picture>`

Serve different crops/images at different breakpoints:

```liquid
<picture>
  <source media="(max-width: 768px)"
    srcset="{{ section.settings.mobile_image | image_url: width: 400 }} 400w,
            {{ section.settings.mobile_image | image_url: width: 800 }} 800w"
    sizes="100vw">
  <source media="(min-width: 769px)"
    srcset="{{ section.settings.desktop_image | image_url: width: 1200 }} 1200w,
            {{ section.settings.desktop_image | image_url: width: 1600 }} 1600w"
    sizes="80vw">
  {{ section.settings.desktop_image | image_url: width: 1200 | image_tag }}
</picture>
```

#### Image Best Practices

- **Do not over-provision srcset sizes**: Too many variants reduce CDN cache hit rates. The difference between 600px and 700px images rarely justifies both.
- **Upload high-resolution source images**: Shopify's CDN cannot enlarge images beyond the original. Requesting 1000px from a 500px original delivers a degraded result.
- **Use SVG for logos and icons**: Vector formats scale infinitely without quality loss.
- **Target file sizes**: Hero images <= 250KB, product images <= 150KB, thumbnails <= 30KB (all in WebP).
- **Avoid background images in CSS**: Use `<img>` or `<picture>` elements for content images so the browser can apply responsive loading and format negotiation.

---

### 8. Font Loading Optimization

#### The Font Loading Problem

Custom web fonts are one of the most impactful performance factors on Shopify. They can delay text rendering, cause layout shifts (CLS), and increase overall page weight.

#### `font-display: swap`

The most fundamental fix. Instructs browsers to show a fallback system font immediately while the custom font loads, ensuring text is always visible:

```css
@font-face {
  font-family: 'CustomFont';
  src: url('custom-font.woff2') format('woff2');
  font-display: swap;
}
```

#### Preloading Critical Fonts

Shopify improved Shopify.com loading by 50% (saving 1.2 seconds) with just 17 lines of preloading code:

```liquid
<!-- In theme.liquid <head> -->
<link rel="preload"
      href="{{ 'custom-font.woff2' | asset_url }}"
      as="font"
      type="font/woff2"
      crossorigin>
```

**Rules for font preloading:**
- Only preload the 1-2 most critical font files (the ones used for above-fold text)
- Do not preload every font file -- over-fetching wastes bandwidth
- Always include `crossorigin` attribute for font preloads (required by the spec)

#### Font Format: Use WOFF2

WOFF2 is the most efficient web font format:
- Smaller than WOFF, OTF, or TTF
- Better compression
- Supported by all modern browsers
- Should be the only format you serve (with WOFF as a fallback for very old browsers)

#### Reducing Font File Count

- Limit to 2-3 font files per font family
- Use only the weights you actually need (typically Regular 400 and Bold 700)
- Avoid loading italic variants unless specifically required
- Consider using system fonts for body text and custom fonts only for headings

#### Fallback Font Metric Matching

To prevent CLS when fonts swap, match fallback font metrics to your custom font:

```css
@font-face {
  font-family: 'CustomFont Fallback';
  src: local('Arial');
  size-adjust: 105%;
  ascent-override: 95%;
  descent-override: 22%;
  line-gap-override: 0%;
}

body {
  font-family: 'CustomFont', 'CustomFont Fallback', Arial, sans-serif;
}
```

Use tools like the Fallback Font Generator to calculate the correct metric overrides for your specific custom font.

---

### 9. JavaScript & Render-Blocking Resources

#### Understanding Render-Blocking

Parser-blocking scripts block the construction and rendering of the DOM until the script is loaded, parsed, and executed. This creates network congestion and significantly delays page rendering, directly impacting First Contentful Paint (FCP) and Largest Contentful Paint (LCP).

#### `defer` vs `async`

| Attribute | Download | Execution | Order Preserved |
|-----------|----------|-----------|-----------------|
| None (default) | Blocks parsing | Immediate | Yes |
| `async` | Parallel | As soon as downloaded | No |
| `defer` | Parallel | After HTML parsing complete | Yes |

**When to use each:**
- `defer`: When execution order matters (most cases). Script runs after HTML is fully parsed.
- `async`: When the script is independent and order doesn't matter (analytics, tracking).
- Neither: Only for critical inline scripts that must execute immediately.

**General rule**: Use `defer` if execution order matters, `async` otherwise.

#### Shopify-Specific JavaScript Patterns

##### Move Scripts Before `</body>`

Most JavaScript should be placed just before the closing `</body>` tag unless there is a strong reason it must be in the `<head>`:

```liquid
<!-- theme.liquid -->
<head>
  <!-- Only critical CSS and preload hints here -->
</head>
<body>
  {{ content_for_layout }}

  <!-- Non-critical scripts at the end -->
  <script src="{{ 'theme.js' | asset_url }}" defer></script>
</body>
```

##### Conditional Script Loading

Load scripts only on pages where they are needed:

```liquid
{% if template.name == 'product' %}
  <script src="{{ 'product-reviews.js' | asset_url }}" defer></script>
{% endif %}

{% if template.name == 'search' or template.name == 'collection' %}
  <script src="{{ 'search-filters.js' | asset_url }}" defer></script>
{% endif %}
```

##### Inline Critical JavaScript

For small amounts of critical JavaScript (under 1KB), inline it to avoid an additional network request:

```liquid
<script>
  // Critical: prevent FOUC for dark mode
  document.documentElement.classList.toggle('dark-mode',
    localStorage.getItem('theme') === 'dark');
</script>
```

##### Use `requestIdleCallback` for Non-Essential Work

```javascript
// Delay non-critical initialization
if ('requestIdleCallback' in window) {
  requestIdleCallback(() => {
    initWishlist();
    initRecentlyViewed();
    initNewsletterPopup();
  });
} else {
  // Fallback for Safari
  setTimeout(() => {
    initWishlist();
    initRecentlyViewed();
    initNewsletterPopup();
  }, 2000);
}
```

#### CSS Optimization

- **Inline critical CSS**: Extract the CSS needed for above-fold rendering and inline it in `<head>`
- **Load remaining CSS asynchronously**: But only for below-fold sections -- above-fold CSS should remain render-blocking (this is intentional and correct for preventing CLS)
- **Minify all CSS files**: Remove whitespace, comments, and unused rules
- **Remove unused CSS**: Audit stylesheets for selectors that no longer match any elements

---

### 10. Third-Party App & Script Management

#### The App Bloat Problem

Shopify stores accumulate apps over time, each injecting scripts that increase HTTP requests and slow page loading. The introduction of apps injects JavaScript elements that can potentially slow down every page, not just the ones where the app functionality is used.

#### Quarterly Audit Process

Perform a quarterly audit of all installed apps and third-party scripts:

1. **List all installed apps** and their purpose
2. **Measure each app's impact** using Chrome DevTools Network tab and Performance panel
3. **Categorize apps** by necessity:
   - **Essential**: Payment, shipping, inventory (cannot remove)
   - **Revenue-generating**: Reviews, upsells, email capture (evaluate ROI vs. performance cost)
   - **Nice-to-have**: Social proof, chat widgets, animations (consider removing or deferring)
   - **Unused**: Apps installed for testing or no longer needed (remove immediately)
4. **Check for leftover code**: Uninstalling an app does not always remove its injected code from the theme. Manually check `theme.liquid`, `snippets/`, and `assets/` for orphaned scripts.
5. **Replace multi-tool apps** with lighter single-purpose alternatives when the performance cost exceeds the convenience benefit.

#### Script Loading Strategies

##### Use Google Tag Manager (GTM)

GTM can consolidate multiple tracking scripts and provide controlled loading:
- Combine tracking codes into a single container
- Control when scripts fire (page load, DOM ready, scroll, click)
- Reduce initial page load by deferring non-essential tags

##### Conditional Loading by Page Type

```liquid
<!-- Only load review scripts on product pages -->
{% if template.name == 'product' %}
  {{ 'review-widget.js' | asset_url | script_tag }}
{% endif %}

<!-- Only load cart scripts when cart has items -->
{% if cart.item_count > 0 %}
  {{ 'upsell-widget.js' | asset_url | script_tag }}
{% endif %}
```

##### Interaction-Based Loading

Load scripts only when the user interacts with the relevant feature:

```javascript
// Load chat widget only when user clicks the chat button
document.querySelector('.chat-trigger').addEventListener('click', () => {
  const script = document.createElement('script');
  script.src = 'https://chat-provider.com/widget.js';
  document.body.appendChild(script);
}, { once: true });
```

##### App Deferral Pattern

Use the App Deferral strategy to delay non-critical app scripts:

```javascript
// Defer app initialization until after page load
window.addEventListener('load', () => {
  setTimeout(() => {
    // Initialize non-critical apps
    initReviewsWidget();
    initSocialProofNotifications();
  }, 3000); // 3-second delay after load
});
```

#### Monitoring for Regressions

- Schedule regular Lighthouse or Core Web Vitals checks (weekly minimum)
- Use Shopify's Web Performance Dashboard for real user data
- Set up performance budgets and alerts
- Test any new app installation against performance baseline before committing

---

### 11. Theme Selection & Optimization

#### Dawn Theme: The Performance Benchmark

Shopify's Dawn theme is the performance standard for Shopify themes:
- **Performance score**: 99 in Lighthouse
- **Load time**: Approximately 0.6 seconds
- **Architecture**: Built with performance as the primary design constraint
- **OS2.0**: Full Online Store 2.0 sections architecture
- **Minimal JavaScript**: Uses vanilla JS with no framework overhead
- **Responsive images**: Built-in srcset and lazy loading

Dawn is the reference implementation. Developers can explore the Dawn repository to see how Shopify applies performance principles.

#### Top-Performing Shopify Themes (2025-2026 Data)

Based on Core Web Vitals pass rates from UXIFY study (March 2025):

| Theme | CWV Pass Rate | Type |
|-------|--------------|------|
| Bullet | 97.1% | Premium |
| Exhibit | 96.7% | Premium |
| Taiga | 95.4% | Premium |
| Dawn | ~95% | Free |
| Horizon | ~93% | Free (Dawn successor) |

#### Theme Optimization Checklist

1. **Remove unused theme features**: Disable sections and blocks you are not using
2. **Limit homepage sections**: Each section adds Liquid processing and potentially JS/CSS
3. **Audit theme JavaScript**: Check if the theme loads framework libraries (jQuery, Vue, React) and whether they are necessary
4. **Check for inline scripts**: Theme sections that inject `<script>` tags add up quickly
5. **Review theme settings**: Some themes have performance-impacting settings (animation effects, parallax scrolling, infinite scroll)
6. **Test with and without apps**: Measure baseline theme performance before adding apps

#### Custom Theme Performance Considerations

Custom themes can achieve better performance than off-the-shelf themes by:
- Removing all non-essential code
- Building only the features actually needed
- Optimizing specifically for the store's content structure
- However, this requires expert developers and higher initial investment
- Over 3 years, total cost may be similar to premium themes, but with a system tailored exactly to the business

---

### 12. Mobile-Specific Optimization

#### Mobile Commerce Reality

- **81%+ of traffic** to Shopify stores comes from mobile devices
- **Over 50% of ecommerce purchases** are made on mobile
- Google uses **mobile-first indexing**, prioritizing mobile page versions for search rankings
- Mobile performance directly impacts organic search visibility and conversion rates

#### Mobile Performance Strategies

##### 1. Responsive Image Sizing

Serve appropriately sized images for mobile screens:

```liquid
<picture>
  <!-- Mobile: max 2x DPR, smaller images -->
  <source media="(max-width: 768px)"
    srcset="{{ image | image_url: width: 400 }} 1x,
            {{ image | image_url: width: 800 }} 2x">
  <!-- Desktop: larger images -->
  <source media="(min-width: 769px)"
    srcset="{{ image | image_url: width: 800 }} 1x,
            {{ image | image_url: width: 1600 }} 2x">
  {{ image | image_url: width: 800 | image_tag }}
</picture>
```

##### 2. Touch-Optimized Interactions

- Minimum tap target size: 48x48px (Google's recommendation)
- Adequate spacing between interactive elements to prevent mis-taps
- Use `touch-action: manipulation` to eliminate 300ms tap delay
- Avoid hover-dependent interactions that don't work on touch devices

##### 3. Mobile Navigation

- Use collapsible "hamburger" menus or accordion-style navigation
- Keep navigation hierarchy shallow (max 2-3 levels)
- Implement sticky header with minimal height to maximize content area
- Consider bottom navigation for key actions (cart, search)

##### 4. Reduce Mobile Payload

- Serve smaller images via srcset (cap at 2x DPR)
- Defer more scripts on mobile (slower processors, slower networks)
- Consider removing decorative elements on mobile (animations, parallax, large background images)
- Use the `<picture>` element with media queries to serve completely different (lighter) images on mobile

##### 5. Test on Real Devices

- Do not rely solely on Chrome DevTools device emulation
- Test on actual mid-range Android devices (not just flagship phones)
- Test on 3G/4G throttled connections
- Test with various screen sizes (especially narrow screens under 375px)

---

### 13. Lazy Loading Implementation

#### What to Lazy Load

- **Images below the fold**: All images that are not visible in the initial viewport
- **Videos**: Load thumbnail/placeholder first, load video player on interaction
- **Sections below the fold**: Use Shopify's section rendering API
- **App widgets below the fold**: Defer initialization until scrolled into view

#### What NOT to Lazy Load

- **The LCP image**: Hero images, main product images, above-fold banners -- these must load immediately
- **Above-fold content**: Anything visible without scrolling
- **Critical CSS and JavaScript**: Resources needed for initial render

#### Implementation Methods

##### 1. Native HTML Lazy Loading

The simplest approach. Add `loading="lazy"` to below-fold images:

```html
<img src="product.webp" loading="lazy" width="400" height="400" alt="Product">
```

##### 2. Shopify's Built-In Behavior

Shopify's `image_tag` filter automatically sets `loading="lazy"` for images in sections further down the page. To take advantage of this default, **do not manually set the loading attribute** unless you need to override it:

```liquid
<!-- Automatic lazy loading for below-fold sections -->
{{ product.featured_image | image_url: width: 600 | image_tag }}

<!-- Override for above-fold LCP image -->
{{ section.settings.hero | image_url: width: 1200 | image_tag: loading: 'eager' }}
```

##### 3. Section Lazy Loading with Intersection Observer

Load entire sections dynamically when scrolled into view:

```javascript
const observer = new IntersectionObserver((entries) => {
  entries.forEach(entry => {
    if (entry.isIntersecting) {
      const section = entry.target;
      const url = section.dataset.sectionUrl;
      fetch(url)
        .then(response => response.text())
        .then(html => {
          section.innerHTML = html;
        });
      observer.unobserve(section);
    }
  });
}, { rootMargin: '200px' }); // Start loading 200px before entering viewport

document.querySelectorAll('[data-lazy-section]').forEach(el => {
  observer.observe(el);
});
```

##### 4. Video Lazy Loading

Load only a thumbnail initially, then load the video player on click:

```liquid
<div class="video-placeholder" data-video-url="{{ section.settings.video_url }}">
  {{ section.settings.video_thumbnail | image_url: width: 800 | image_tag: loading: 'lazy' }}
  <button class="play-button" aria-label="Play video">Play</button>
</div>

<script>
document.querySelectorAll('.video-placeholder').forEach(placeholder => {
  placeholder.querySelector('.play-button').addEventListener('click', () => {
    const iframe = document.createElement('iframe');
    iframe.src = placeholder.dataset.videoUrl;
    iframe.allow = 'autoplay; encrypted-media';
    placeholder.replaceWith(iframe);
  }, { once: true });
});
</script>
```

##### 5. JavaScript Library: lazysizes

For more advanced lazy loading (background images, iframes), the lazysizes library is lightweight and reliable:

```html
<img data-src="product.webp" class="lazyload" width="400" height="400" alt="Product">
<script src="lazysizes.min.js" async></script>
```

#### Critical Warning

Never lazy-load the LCP element. If your hero image or main product image uses `loading="lazy"`, it will significantly delay LCP because the browser will not start downloading it until it determines the element is near the viewport (which requires layout computation).

---

### 14. Checkout Performance

#### Shopify Checkout Constraints

Shopify manages the checkout experience, which limits direct optimization opportunities. However, several strategies can improve checkout speed:

#### Optimization Strategies

##### 1. Minimize Checkout Customizations
- Keep checkout extensions lightweight
- Avoid loading unnecessary scripts in checkout
- Each additional element adds processing time

##### 2. Reduce Form Complexity
- Request only essential fields (6-8 fields maximum)
- Collapse optional fields ("Address 2", "Company") by default
- Enable Google Autocomplete for address fields (20% faster than manual typing)
- Pre-fill forms using customer data when available

##### 3. Optimize Checkout Media
- Compress any images displayed in checkout (trust badges, logos)
- Remove decorative elements that add no value to the conversion process
- Keep checkout branding minimal and lightweight

##### 4. Remove Heavy Scripts from Checkout
- Audit which apps inject scripts into the checkout flow
- Remove tracking scripts that don't need to fire during checkout
- Defer analytics pixels to after the purchase confirmation

##### 5. Shop Pay and Accelerated Checkout
- Shop Pay provides a pre-optimized, one-tap checkout experience
- Enable accelerated checkout options (Apple Pay, Google Pay) to bypass the form entirely
- These are pre-optimized by Shopify and load independently of your theme

---

### 15. Performance Measurement Tools

#### Shopify-Specific Tools

| Tool | Purpose | Access |
|------|---------|--------|
| **Shopify Web Performance Dashboard** | Real user data from actual customers | Shopify Admin > Online Store > Web Performance |
| **Shopify Theme Inspector** | Liquid render profiling with flame graphs | Chrome Extension (requires store access) |
| **Shopify Theme Check** | Automated theme code linting for performance | CLI tool or VS Code extension |

#### Shopify Theme Inspector Details

The Shopify Theme Inspector for Chrome is a browser plugin that visualizes Liquid render profiling data in a flame graph format:

- **Flame graph view**: Shows the call hierarchy and time spent in each Liquid file, section, and snippet
- **Sandwich view**: Aggregates "Self" times (execution time excluding children) and "Total" times (including children)
- **Target benchmarks**: Aim for 200ms total Liquid render time, maximum 500ms
- **Requirements**: Needs Themes staff permission or collaborator account with Themes permission

#### General Performance Tools

| Tool | Best For |
|------|----------|
| **Google PageSpeed Insights** | Lab + field data with specific recommendations |
| **Chrome DevTools Performance Panel** | Detailed interaction profiling and long task identification |
| **WebPageTest** | Detailed waterfall analysis, filmstrip view, CLS frame analysis |
| **Chrome User Experience Report (CrUX)** | Real-world field data at origin and URL level |
| **TREO Sitespeed** | Free domain-wide CrUX analysis |
| **Lighthouse** | Comprehensive lab audit with actionable suggestions |
| **Web Vitals Chrome Extension** | Real-time CWV monitoring with element attribution |
| **GTmetrix** | Combined PageSpeed and waterfall analysis |

#### Measurement Best Practices

- **Measure real user data**, not just lab data. Lab tests run on fast hardware and do not reflect the experience of users on mid-range mobile devices.
- **Test on throttled connections**. Simulate 3G and 4G to understand the experience for users on slower networks.
- **Test the most important pages**: Homepage, top collection pages, top product pages, and checkout.
- **Establish baselines** before making changes so you can measure the impact of each optimization.
- **Monitor continuously**: Performance degrades over time as apps and content are added. Set up regular checks (weekly minimum).

---

## Part 2: INP Case Studies

### Case Study 1: QuintoAndar

**Company**: QuintoAndar (Brazilian real estate platform)
**Source**: [web.dev/case-studies/quintoandar-inp](https://web.dev/case-studies/quintoandar-inp)

#### Problem

QuintoAndar's property search interactions reached **4-second interaction time at the 75th percentile**. The platform suffered from excessive main thread work during initial page load, causing high input delay -- the time lag before event handlers execute when users interact with the page.

#### Root Causes

1. **Long tasks blocking the main thread**: Heavy JavaScript execution prevented timely response to user interactions
2. **High input delay**: When users clicked filters or navigated search results, the browser could not begin processing the interaction because other tasks were occupying the main thread
3. **Inefficient React rendering**: Expensive state updates blocked the UI
4. **CSS-in-JS overhead**: Runtime style generation added processing time
5. **Third-party tracking pixels**: Client-side pixel loading consumed main thread resources

#### Optimization Techniques

##### 1. Yielding to the Main Thread

Implemented `async`/`await` patterns to create yield points, allowing the browser to process higher-priority tasks (like responding to user interactions):

```javascript
function yieldToMain() {
  return new Promise(resolve => {
    setTimeout(resolve, 0);
  });
}

// Usage pattern
async function handleFilterChange() {
  showLoadingSpinner();
  await yieldToMain();  // Let browser paint the spinner
  await loadFilterData();
  await yieldToMain();  // Let browser paint results
  hideLoadingSpinner();
}
```

The key insight: providing visual feedback (loading spinner) immediately before yielding gives users confidence that their interaction was registered, even though the actual processing has not yet completed.

##### 2. React Transitions (`useTransition`)

Used React's `useTransition` hook to separate high-priority input handling from time-consuming rendering updates:

```javascript
const [isPending, startTransition] = useTransition();

function handleFilterClick(filter) {
  // High priority: update the UI immediately
  setActiveFilter(filter);

  // Low priority: expensive data processing
  startTransition(() => {
    applyFilterToResults(filter);
  });
}
```

This pattern prevents UI blocking during computationally expensive updates.

##### 3. Memoization and Debouncing

- Memoized expensive calculations to prevent unnecessary re-computation
- Debounced rapid user interactions (e.g., map zoom, search typing)

##### 4. AbortController for Request Cancellation

Implemented `AbortController` to cancel in-flight API requests when users changed filters rapidly, preventing wasted processing:

```javascript
let controller = new AbortController();

function fetchResults(filter) {
  controller.abort(); // Cancel previous request
  controller = new AbortController();

  fetch(`/api/search?filter=${filter}`, {
    signal: controller.signal
  });
}
```

##### 5. Infrastructure Changes

- **Removed CSS-in-JS**: Eliminated runtime style generation overhead
- **Removed third-party pixels from client**: Moved tracking to server-side
- **React Suspense**: Implemented code-splitting for lazy-loaded components
- **Canary release system**: Staged rollouts (1% -> 10% -> 65% -> 100%) with automatic rollback on performance degradation

#### Results

| Metric | Before | After | Change |
|--------|--------|-------|--------|
| Mobile INP (p75) | 1,006ms | 216ms | **-78% (80% reduction)** |
| Pages meeting "good" INP | 42% | 78% | **+85%** |
| Pages with "poor" INP | 32% | 6.9% | **-78%** |
| Conversion volume (YoY) | Baseline | +36% | **+36% increase** |

#### Organizational Approach

QuintoAndar declared a **"Code Yellow"** -- an organizational alert that prioritized performance across all engineering teams. They implemented:
- Fixed and variable threshold alarms reviewed bi-weekly
- Detailed runbooks for incident procedures
- Cross-team collaboration rather than siloed fixes

#### Key Lessons for WordPress/Shopify

1. **Yield to the main thread** in long event handlers. Even a simple `setTimeout(resolve, 0)` can dramatically improve responsiveness.
2. **Show visual feedback immediately** before starting expensive work. Users perceive the interaction as faster.
3. **Cancel stale work** when users change their input before previous processing completes.
4. **Remove CSS-in-JS** if possible -- runtime style generation is expensive.
5. **Move tracking pixels server-side** to reduce client-side main thread work.
6. **Performance requires organizational commitment**, not just technical fixes.

---

### Case Study 2: Disney+ Hotstar

**Company**: Disney+ Hotstar (streaming platform, smart TV and set-top box users)
**Source**: [web.dev/case-studies/hotstar-inp](https://web.dev/case-studies/hotstar-inp)

#### Problem

Disney+ Hotstar's smart TV and set-top box users experienced **675 milliseconds of INP**, classified as poor performance. The constrained hardware of smart TVs and set-top boxes amplified every performance inefficiency.

#### Root Causes

##### 1. Spatial Navigation Library Causing Layout Thrashing

A third-party spatial navigation library (for TV remote control navigation) read the position of all focusable elements and built a new tree on every interaction. For a homepage with 10 trays of 7 cards each, this meant 70+ focusable elements requiring constant recalculation.

**The problem**: Every time the user navigated with the remote, the library:
1. Read layout properties of all 70+ elements (triggering forced layout)
2. Built a new navigation tree
3. Applied focus styles
4. This cycle repeated on every single button press

##### 2. Third-Party Carousel Library Causing Per-Card Recalculation

An external carousel library read the dimensions of each card during horizontal navigation, adding unnecessary layout recalculations for every single card movement instead of reading once per tray.

##### 3. Excessive Script Processing at Startup

The application processed more scripts than necessary during startup, occupying the main thread and preventing responsive interaction handling during the critical early seconds of the user experience.

#### Optimization Techniques

##### 1. Custom Carousel Library (Replacing Third-Party)

Built an in-house carousel that eliminates layout thrashing:
- **Read dimensions once per tray** rather than per-card
- Used **composited animations** (CSS transforms) instead of layout-triggering properties
- Saved approximately **35 KB (compressed)** by removing the third-party library

```javascript
// Before: Library reads layout on every card navigation
// carousel.moveTo(nextCard) -> reads card.offsetWidth, card.offsetLeft for EVERY card

// After: Read once, calculate with math
class OptimizedCarousel {
  constructor(tray) {
    // Read dimensions ONCE during initialization
    this.cardWidth = tray.firstChild.offsetWidth;
    this.gap = parseInt(getComputedStyle(tray).gap);
    this.position = 0;
  }

  moveNext() {
    this.position++;
    // Calculate position with math, no DOM reads needed
    const offset = this.position * (this.cardWidth + this.gap);
    // Use composited animation (transform) - no layout triggered
    this.tray.style.transform = `translateX(-${offset}px)`;
  }
}
```

##### 2. Lazy Loading of Trays with Yielding

Instead of rendering all content trays at once:
- Loaded **only the 2 visible trays** plus 1 above and 1 below the viewport
- Applied the **`setTimeout()` yielding strategy** to split rendering across multiple tasks
- This allowed the main thread to handle remote control interactions between rendering chunks

```javascript
async function renderTrays(trays) {
  const visibleStart = getFirstVisibleTrayIndex();

  // Render visible trays immediately
  renderTray(trays[visibleStart]);
  renderTray(trays[visibleStart + 1]);

  // Render adjacent trays with yielding
  for (let i = 0; i < trays.length; i++) {
    if (i === visibleStart || i === visibleStart + 1) continue;
    await yieldToMain(); // Allow remote control interactions
    renderTray(trays[i]);
  }
}
```

##### 3. Predictive Asset Preloading

Built an in-house asset preloader that determines which page the user is likely to navigate to next and preloads its assets. This reduced startup script processing while maintaining fast subsequent page loads.

##### 4. Task Cancellation Utility

Created a task generator utility that allows cancellation of in-progress tasks. For example, when a user navigates away from a title card, the trailer preview loading is immediately cancelled:

```javascript
function createCancellableTask(taskFn) {
  let cancelled = false;

  return {
    run: async (...args) => {
      cancelled = false;
      const result = await taskFn(...args);
      if (cancelled) return null;
      return result;
    },
    cancel: () => { cancelled = true; }
  };
}

const trailerLoader = createCancellableTask(loadTrailer);

// When user focuses a card
trailerLoader.run(cardId);

// When user moves to next card
trailerLoader.cancel(); // Stop loading previous trailer
trailerLoader.run(nextCardId);
```

#### Results

| Metric | Before | After | Change |
|--------|--------|-------|--------|
| INP | 675ms | 272ms | **-60% (61% improvement)** |
| Tray interaction latency | ~400ms | ~100ms | **-75%** |
| Page render time (Tizen) | 6.47s | 4.46s | **-31%** |
| Page render time (WebOS) | Baseline | - | **-25.2%** |
| Weekly card views per user | 111 | 226 | **+104% (doubled)** |

The doubling of weekly card views demonstrates that responsiveness improvements directly correlate with user engagement -- users browse more content when interactions feel instant.

#### Key Lessons for WordPress/Shopify

1. **Layout thrashing is the enemy of INP**. If JavaScript reads layout properties (offsetWidth, offsetHeight, getBoundingClientRect) and then writes to the DOM repeatedly, performance will be terrible.
2. **Build custom solutions for performance-critical paths**. Third-party libraries optimize for features and compatibility, not for your specific performance constraints.
3. **Read DOM dimensions once and calculate with math**. Avoid repeated forced layout by caching measured values.
4. **Use CSS transforms for animations** instead of layout-triggering properties (top, left, width, height).
5. **Render only what is visible** plus a small buffer. Lazy-load everything else.
6. **Cancel unnecessary work** when user behavior changes (navigates away, changes selection).
7. **Yield between rendering chunks** to keep the main thread responsive to user input.

---

### Case Study 3: PubConsent (PubTech)

**Company**: PubTech (publisher technology company, maker of PubConsent consent management platform)
**Source**: [web.dev/case-studies/pubconsent-inp](https://web.dev/case-studies/pubconsent-inp)

#### Problem

PubConsent's consent management platform (CMP) caused long tasks that blocked UI updates when users interacted with consent dialogs. When users clicked buttons like "Accept All," the interaction triggered extensive JavaScript processing that prevented the browser from rendering UI changes, making the dialog appear frozen.

#### Root Causes

1. **Third-party script interference**: The biggest contributors to long tasks were other third-party scripts (analytics, advertising providers) that fired during CMP interactions
2. **IAB TCF library processing**: The TCF (Transparency and Consent Framework) library performed expensive encoding/decoding operations during every consent action
3. **Synchronous DOM operations**: Immediately removing DOM nodes when closing the consent dialog triggered expensive rendering work during the interaction
4. **Redundant loop processing**: The TCF library's publisher restrictions encoding contained unnecessary loops

#### Optimization Techniques

##### 1. High-Priority Yielding with Scheduler API

Implemented `yieldToMainUiBlocking()` using progressive enhancement of the Scheduler API:

```javascript
function yieldToMainUiBlocking() {
  return new Promise((resolve) => {
    if ('scheduler' in window) {
      // Best: Scheduler.yield() (Chromium 129+)
      if ('yield' in window.scheduler) {
        return window.scheduler.yield().then(() => resolve(true));
      }
      // Good: postTask with user-blocking priority
      if ('postTask' in window.scheduler) {
        return window.scheduler.postTask(
          () => resolve(true),
          { priority: 'user-blocking' }
        );
      }
    }
    // Fallback: resolve immediately for non-Chromium browsers
    resolve(false);
  });
}
```

This approach prioritizes internal CMP operations while yielding to allow the browser to paint visual updates.

##### 2. Background-Priority Yielding

For lower-priority work, a separate yielding function:

```javascript
function yieldToMainBackground() {
  return new Promise((resolve) => {
    if ('scheduler' in window) {
      if ('yield' in window.scheduler) {
        return window.scheduler.yield().then(() => resolve(true));
      }
      if ('postTask' in window.scheduler) {
        return window.scheduler.postTask(
          () => resolve(true),
          { priority: 'background' }
        );
      }
    }
    // Fallback: setTimeout for non-Chromium browsers
    setTimeout(() => resolve(false), 0);
  });
}
```

##### 3. Lazy De-rendering

Instead of immediately removing DOM nodes when closing the consent dialog (which triggers expensive layout recalculation during the interaction), PubTech:

1. Applied `display: none` via CSS immediately (instant visual removal)
2. Deferred actual DOM node removal to idle time using `requestIdleCallback`

```javascript
function closeConsentDialog(dialogElement) {
  // Step 1: Visually hide immediately (cheap CSS change)
  dialogElement.style.display = 'none';

  // Step 2: Actually remove from DOM during idle time
  if ('requestIdleCallback' in window) {
    requestIdleCallback(() => {
      dialogElement.remove();
    });
  } else {
    setTimeout(() => {
      dialogElement.remove();
    }, 1000);
  }
}
```

This dramatically reduced the rendering work during the user's interaction.

##### 4. IAB TCF Library Optimization

Two specific improvements to the most computationally expensive parts of the TCF library:

1. **Cached decoding results**: Reused calculated results for decoding processes that were being re-executed during third-party callbacks
2. **Reduced unnecessary loops**: Optimized publisher restrictions encoding, achieving up to **60% reduction in loops** per user consent action

#### Results

| Metric | Before | After | Change |
|--------|--------|-------|--------|
| Overall CMP INP | Baseline | - | **Up to 65% improvement** |
| IAB TCF library INP (mobile) | Baseline | - | **Up to 77% improvement** |
| TCF-induced long tasks | Baseline | - | **Up to 85% reduction** |
| Origins passing good INP (mobile) | 13% | 55.46% | **+326% (over 400% improvement)** |
| Origins passing good INP (desktop) | 84% | 99.12% | **+18%** |
| Real-world page INP example | 470ms | 230ms | **-51%** |
| Ad viewability | Baseline | - | **Up to 1.5% improvement** |

#### Key Lessons for WordPress/Shopify

1. **Third-party vendors can and should optimize their INP impact**. If a consent plugin, review widget, or chat tool is causing poor INP, the vendor should be accountable.
2. **Use the Scheduler API with progressive enhancement**. Chromium browsers get the best experience immediately; other browsers maintain baseline functionality through fallbacks.
3. **Lazy de-rendering is powerful**: Hide elements with CSS immediately, remove from DOM later. This separates the visual response (fast) from the cleanup work (deferred).
4. **Cache computed results** that will be needed by multiple callbacks or re-executions.
5. **Audit library internals** for redundant processing. Even well-known libraries (like IAB TCF) can have optimization opportunities.
6. **Consent management platforms significantly impact INP** across the web. If your site uses a CMP, ensure it uses modern yielding strategies.

---

### Cross-Cutting INP Lessons

#### Universal Patterns Across All Three Case Studies

##### 1. Yielding to the Main Thread

All three case studies used yielding as a core technique. The pattern is consistent:

```javascript
// Basic yielding (works everywhere)
function yieldToMain() {
  return new Promise(resolve => setTimeout(resolve, 0));
}

// Advanced yielding (Chromium with fallback)
async function yieldWithPriority(priority = 'user-visible') {
  if ('scheduler' in window && 'yield' in window.scheduler) {
    await window.scheduler.yield();
  } else if ('scheduler' in window && 'postTask' in window.scheduler) {
    await new Promise(resolve =>
      window.scheduler.postTask(resolve, { priority })
    );
  } else {
    await new Promise(resolve => setTimeout(resolve, 0));
  }
}

// Usage in event handlers
async function handleUserInteraction() {
  showVisualFeedback();          // Immediate UI response
  await yieldToMain();           // Let browser paint
  await performExpensiveWork();  // Do the heavy lifting
  await yieldToMain();           // Let browser paint results
  updateUI();                    // Show final state
}
```

##### 2. Visual Feedback Before Heavy Work

Every case study emphasized showing immediate visual feedback before starting expensive processing:
- QuintoAndar: Loading spinners before filter processing
- Hotstar: Immediate focus highlight before tray navigation
- PubConsent: Immediate dialog hide before DOM cleanup

##### 3. Eliminating Layout Thrashing

Reading and writing DOM layout properties in alternation forces the browser to recalculate layout repeatedly. All case studies addressed this:
- Read layout properties in batches
- Write layout changes in batches
- Cache DOM measurements
- Use CSS transforms instead of layout-triggering properties

##### 4. Cancelling Unnecessary Work

When user behavior changes faster than processing completes:
- QuintoAndar: AbortController for API requests
- Hotstar: Task cancellation utility for trailer loading
- PubConsent: Not processing redundant consent calculations

##### 5. Lazy Rendering and Deferred Cleanup

Render only what is immediately needed:
- Hotstar: Only visible trays + 1 buffer above and below
- PubConsent: CSS hide immediately, DOM removal deferred to idle
- QuintoAndar: React Suspense for code-splitting

#### Business Impact Summary

| Company | INP Improvement | Business Outcome |
|---------|----------------|------------------|
| QuintoAndar | 1,006ms -> 216ms (-78%) | +36% conversion volume (YoY) |
| Disney+ Hotstar | 675ms -> 272ms (-60%) | +104% weekly card views per user |
| PubConsent | Up to 65% improvement | +1.5% ad viewability |

The consistent finding: **improving INP directly improves business metrics**. Users interact more, convert more, and engage more deeply when interactions feel responsive.

#### Applicability to WordPress and Shopify

| INP Technique | WordPress Applicability | Shopify Applicability |
|---------------|------------------------|----------------------|
| Yielding to main thread | High -- apply in custom JS, plugin event handlers | High -- apply in theme JS, app interaction handlers |
| Visual feedback first | High -- loading states for AJAX operations, filter changes | High -- product variant selection, cart updates, filter changes |
| Cancel stale work | Medium -- search autocomplete, filter changes | Medium -- predictive search, collection filtering |
| Lazy de-rendering | High -- modals, popups, consent dialogs | High -- quick-view modals, cart drawers, consent popups |
| Layout thrash prevention | High -- carousels, infinite scroll, masonry grids | High -- product grids, slideshows, mega menus |
| Scheduler API | Medium -- progressive enhancement in custom code | Medium -- progressive enhancement in theme JS |
| Remove CSS-in-JS | Low (rarely used in WP) | Low (rarely used in Shopify Liquid) |
| Server-side tracking | High -- move analytics to server | Medium -- limited by Shopify's architecture |

#### INP Debugging Checklist

1. **Identify the slow interaction**: Use Chrome DevTools Performance panel to record the interaction
2. **Find the long task**: Look for tasks > 50ms that overlap with the interaction
3. **Attribute the cause**: Is it your code, a third-party script, or the browser's rendering work?
4. **Measure the three components**: Input delay (main thread busy?), processing time (handler too slow?), or presentation delay (too much rendering work?)
5. **Apply the appropriate fix**:
   - High input delay -> defer/remove blocking scripts
   - Long processing time -> yield, debounce, or optimize the handler
   - High presentation delay -> reduce DOM changes, use CSS transforms, lazy de-render
6. **Verify with field data**: Lab improvements must be confirmed with real user data (CrUX)
