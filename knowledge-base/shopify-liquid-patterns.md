# Shopify Liquid Performance Patterns — Practical Implementation Guide

> Compiled from BS-DevShop.com articles. Contains copy-paste-ready Shopify Liquid code
> for image optimization, LCP preloading, video lazy loading, Speculation Rules,
> render-blocking script fixes, and speed-killing app identification.

---

## Table of Contents

1. [Image Optimization with Native image_tag](#1-image-optimization-with-native-image_tag)
2. [LCP Preloading with preload_tag](#2-lcp-preloading-with-preload_tag)
3. [Video Lazy Loading Facade](#3-video-lazy-loading-facade)
4. [Speculation Rules API](#4-speculation-rules-api)
5. [Render-Blocking Script Fixes](#5-render-blocking-script-fixes)
6. [Speed-Killing Apps](#6-speed-killing-apps)
7. [Width Sizing Reference](#7-width-sizing-reference)

---

## 1. Image Optimization with Native image_tag

Shopify's built-in `image_tag` filter handles responsive images, WebP conversion, and lazy loading natively. No custom snippets needed.

### Hero/LCP Images (Above the Fold)

```liquid
{{ section.settings.hero_image | image_url: width: 1600 | image_tag:
  loading: 'eager',
  fetchpriority: 'high',
  widths: '800, 1200, 1600, 2000',
  sizes: '(min-width: 1200px) 1200px, 100vw',
  alt: 'Hero banner description' }}
```

**Critical attributes:**
- `loading: 'eager'` — prevents lazy-loading of LCP candidates
- `fetchpriority: 'high'` — signals browser resource prioritization
- `widths` — responsive breakpoints for srcset generation
- `sizes` — tells browser which width to download at each viewport

### Below-the-Fold Product Images

```liquid
{{ product.featured_image | image_url: width: 800 | image_tag:
  loading: 'lazy',
  widths: '400, 600, 800, 1000',
  sizes: '(min-width: 768px) 50vw, 100vw',
  alt: product.title }}
```

### Carousel/Slideshow Images

```liquid
{% for image in product.images %}
  {{ image | image_url: width: 800 | image_tag:
    loading: forloop.first ? 'eager' : 'lazy',
    widths: '400, 600, 800',
    alt: product.title | append: ' - view ' | append: forloop.index }}
{% endfor %}
```

Only the first carousel image loads eagerly; rest are lazy.

### Thumbnail Grids

```liquid
{{ product.featured_image | image_url: width: 400 | image_tag:
  loading: 'lazy',
  widths: '200, 300, 400',
  sizes: '(min-width: 768px) 25vw, 50vw',
  class: 'product-grid-image',
  alt: product.title }}
```

### Anti-Patterns to Detect

1. `loading: 'lazy'` on LCP images — delays largest paint
2. Oversized width specifications for thumbnails — wastes bandwidth
3. Missing alt text — accessibility and SEO issue
4. Lazy-loading first carousel image — delays visible content
5. Missing width/height attributes — causes CLS

### Performance Results

- LCP improvement: ~30-40% faster when migrating from custom snippets
- Bandwidth reduction: 40-60% with WebP + responsive images
- Automatic WebP conversion: ~30% smaller than JPEG

---

## 2. LCP Preloading with preload_tag

Shopify's `preload_tag` filter initiates image downloads before the browser discovers `<img>` elements during parsing.

### Real-World Results

"We used this exact snippet on a client store and decreased LCP load time 72%. This resulted in a +11% CVR lift, and an extra $71k in monthly revenue."

### Mobile Image Preloading

```liquid
{{ block.settings.mobile_image
   | image_url: width: 1000
   | preload_tag: as: 'image', loading: loading,
     fetchpriority: priority, media: '(max-width: 769px)'
}}
```

### Homepage Hero Preload in `<head>`

```liquid
{% if template == 'index' %}
  <link rel="preload"
    as="image"
    href="{{ section.settings.hero_image | image_url: width: 1600 }}"
    imagesrcset="
      {{ section.settings.hero_image | image_url: width: 800 }} 800w,
      {{ section.settings.hero_image | image_url: width: 1200 }} 1200w,
      {{ section.settings.hero_image | image_url: width: 1600 }} 1600w"
    imagesizes="(min-width: 1200px) 1200px, 100vw">
{% endif %}
```

### Priority Assignment Logic for Carousels

```liquid
{% if forloop.first %}
  {% assign preload = true %}
  {% assign loading = 'eager' %}
  {% assign priority = 'high' %}
{% endif %}
```

### Constraints

- Limit to 1-2 preloads maximum — excess preloading degrades performance
- Only preload the actual LCP element, not secondary images
- Use `media` queries to target mobile vs desktop preloads separately

---

## 3. Video Lazy Loading Facade

Videos (5-15MB each) should never load on page load. Use the facade pattern: show a poster image, load video only on interaction or when visible.

### Simple Intersection Observer Approach

**HTML (use data-src instead of src):**
```html
<video controls poster="https://cdn.shopify.com/images/first-frame.jpg">
  <source data-src="https://cdn.shopify.com/video.mp4" type="video/mp4">
</video>
```

**JavaScript (add before `</body>` in theme.liquid):**
```javascript
document.addEventListener('DOMContentLoaded', function() {
  const videoSources = document.querySelectorAll('source[data-src]');

  if ('IntersectionObserver' in window) {
    const videoObserver = new IntersectionObserver((entries, observer) => {
      entries.forEach(entry => {
        if (entry.isIntersecting) {
          const source = entry.target;
          source.setAttribute('src', source.getAttribute('data-src'));
          source.removeAttribute('data-src');
          source.closest('video').load();
          observer.unobserve(source);
        }
      });
    }, { rootMargin: '50px' });

    videoSources.forEach(source => videoObserver.observe(source));
  } else {
    videoSources.forEach(source => {
      source.setAttribute('src', source.getAttribute('data-src'));
      source.removeAttribute('data-src');
    });
  }
});
```

### Advanced Video Facade Snippet

Save as `snippets/video-facade.liquid`. Supports autoplay and click-to-play modes with:
- Debounced click handlers (100ms) to prevent multiple load requests
- `requestAnimationFrame` for smooth performance
- Event listeners for `shopify:section:load` and `shopify:block:select`
- Google Analytics event tracking for video plays
- Error handling and poster image fallback

**Usage - Product Page (click-to-play):**
```liquid
{% render 'video-facade',
  video_url: product.metafields.custom.demo_video,
  poster_url: product.metafields.custom.video_poster,
  autoplay: false,
  alt_text: product.title | append: ' demonstration'
%}
```

**Usage - Hero Section (autoplay):**
```liquid
{% render 'video-facade',
  video_url: section.settings.hero_video_url,
  poster_url: section.settings.hero_poster,
  autoplay: true,
  alt_text: 'Brand introduction video'
%}
```

### Performance Impact

- Average landing page scroll rate: 43% — most users never see below-fold videos
- Expected 15-40% reduction in initial load time on video-heavy pages
- Poster images: typically <100KB vs video files: 5-15MB each

---

## 4. Speculation Rules API

Prefetch or prerender pages before users click links. Makes subsequent page navigation feel instant.

### Performance Gains

- **Prefetch**: 300-800ms faster navigation
- **Prerender**: 500-1,500ms faster navigation (page fully rendered in background)

### Basic Prefetch (Recommended Starting Point)

```html
<script type="speculationrules">
{
  "prefetch": [
    {
      "urls": ["/collections/all", "/collections/bestsellers", "/cart"]
    }
  ]
}
</script>
```

### Smart Prefetch with Pattern Matching

```html
<script type="speculationrules">
{
  "prefetch": [
    {
      "where": {
        "and": [
          { "href_matches": "/products/*" },
          { "not": { "href_matches": "*variant_id=*" } }
        ]
      }
    }
  ]
}
</script>
```

### Eagerness Controls

```html
<script type="speculationrules">
{
  "prefetch": [
    {
      "urls": ["/collections/all"],
      "eagerness": "immediate"
    }
  ],
  "prerender": [
    {
      "urls": ["/products/bestseller"],
      "eagerness": "conservative"
    }
  ]
}
</script>
```

| Eagerness | Behavior |
|-----------|----------|
| `immediate` | Start right away |
| `eager` | Start when browser idle (default) |
| `conservative` | Only on hover (server-friendly) |

### NEVER Prefetch These (Side-Effect Pages)

- `/cart/add` or `/cart/update` — accidental cart modifications
- `/account/logout` — unintended logouts
- `/checkout/step-1` — order creation
- `/account/orders` — privacy exposure

### Safe to Prefetch

- Collection pages, product pages, homepage
- About, contact, FAQ pages
- Cart view page (read-only)

### Warnings

- **Analytics inflation**: Prefetched pages count as visits in Google Analytics even if users don't view them
- **Server load**: Each prefetch request consumes server resources
- **Browser support**: Chrome/Edge (full), Safari (prefetch only), Firefox (partial), older browsers ignore gracefully

### Shopify Integration

Place in `templates/theme.liquid` header or footer section.

---

## 5. Render-Blocking Script Fixes

### What Makes a Script Render-Blocking

A `<script>` without `async` or `defer` blocks HTML parsing. The browser stops rendering until the script downloads, parses, and executes.

### Fix Options (in order of preference)

**1. Defer (maintains execution order):**
```html
<script src="script.js" defer></script>
```

**2. Async (independent scripts only):**
```html
<script src="analytics.js" async></script>
```

**3. Dynamic loading (non-critical scripts):**
```javascript
window.addEventListener('load', () => {
  const script = document.createElement('script');
  script.src = 'non-critical-script.js';
  document.head.appendChild(script);
});
```

**4. Remove entirely** — audit scripts for actual business value.

### Shopify-Specific Constraints

- **Cannot modify app-injected scripts** — Apps use Shopify's ScriptTag API. Only option: remove the app or contact developer.
- **Cannot modify Shopify core scripts** — These are platform-controlled.
- **CAN modify theme scripts** — Add defer/async in Liquid templates.
- **Uninstalling apps doesn't always remove scripts** — Audit ScriptTag entries manually.

### What to Focus On

Scripts taking >100ms or appearing repeatedly in Performance tab are problematic. Prioritize by main thread blocking time, not file size.

---

## 6. Speed-Killing Apps

### Common Speed Killers on Shopify

- **Live chat widgets** — especially "fancy" ones with animations
- **Review apps** — loading extensive review libraries and widgets
- **Currency converter tools** — often add heavy JS bundles
- **Pop-up and email capture utilities** — DOM manipulation on every page
- **Social media feed integrations** — external API calls + rendering

### Generally Acceptable Apps

- Basic analytics solutions
- Simple SEO tools
- Inventory management systems
- Lightweight product recommendation widgets

### Detection Threshold

Scripts taking **>100ms main thread time** or **appearing repeatedly** in Chrome DevTools Performance tab need investigation.

### Audit Process

1. Open Chrome DevTools → Performance tab
2. Record a page load
3. Sort third-party scripts by "Main Thread Time"
4. Network tab: sort by load time
5. Remove unused apps entirely (don't just disable)
6. Test each page type separately (homepage, product, collection)
7. Always test on mobile

---

## 7. Width Sizing Reference

**Formula**: Image max-width = displayed size x 1.5 (for retina)

| Use Case | Display Width | Max Width | Widths Array |
|----------|--------------|-----------|-------------|
| Thumbnail | 200px | 400px | 200, 300, 400 |
| Collection grid | 300px | 500px | 200, 300, 400, 500 |
| Blog images | 600px | 900px | 400, 600, 800 |
| Product main | 600px | 1000px | 400, 600, 800, 1000 |
| Hero banner | 1200px | 2000px | 800, 1200, 1600, 2000 |

### DPR Capping for Mobile

Cap at 2x DPR for mobile devices. A 400px display width needs max 800px image, not 1200px (3x). The visual difference between 2x and 3x is imperceptible but the bandwidth cost is significant.

---

## Sources

- https://www.bs-devshop.com/blog/site-speed-cut-render-blocking-scripts
- https://www.bs-devshop.com/blog/lcp-score-fix-with-ai
- https://www.bs-devshop.com/blog/img-compressor-snippet
- https://www.bs-devshop.com/blog/faster-pages-with-preloading-lcp
- https://www.bs-devshop.com/blog/lazy-loading-videos-for-ecom
- https://www.bs-devshop.com/blog/instantly-load-shopify-pages-with-speculation-rules-api
- https://www.bs-devshop.com/blog/speed-killer-apps
- https://www.bs-devshop.com/blog/improve-site-speed-lazy-loading-videos
