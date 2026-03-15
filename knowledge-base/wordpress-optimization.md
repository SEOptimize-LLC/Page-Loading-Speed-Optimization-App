# WordPress Performance Optimization Knowledge Base
## Source: WPJohnny.com - Practical WordPress Speed Expertise

> Compiled from 20+ articles by Johnny Nguyen (WPJohnny), a WordPress speed optimization expert with 13+ years of experience in WordPress design, development, hosting, and performance optimization. This represents real-world, battle-tested advice, not theoretical recommendations.

---

## Table of Contents

1. [Core Philosophy](#1-core-philosophy)
2. [Web Hosting & Server Optimization](#2-web-hosting--server-optimization)
3. [Web Server Selection](#3-web-server-selection)
4. [PHP Configuration](#4-php-configuration)
5. [Database Optimization](#5-database-optimization)
6. [Theme Optimization](#6-theme-optimization)
7. [Page Builder Impact & Migration](#7-page-builder-impact--migration)
8. [Plugin Optimization](#8-plugin-optimization)
9. [Recommended Plugin Stack](#9-recommended-plugin-stack)
10. [CSS & JavaScript Optimization](#10-css--javascript-optimization)
11. [Why Not to Combine CSS/JS](#11-why-not-to-combine-cssjs)
12. [Image Optimization](#12-image-optimization)
13. [Font Optimization](#13-font-optimization)
14. [Caching Strategy](#14-caching-strategy)
15. [Cache Plugin Configuration](#15-cache-plugin-configuration)
16. [CDN Configuration](#16-cdn-configuration)
17. [Core Web Vitals](#17-core-web-vitals)
18. [Why Speed Test Scores Do Not Matter](#18-why-speed-test-scores-do-not-matter)
19. [Lazy Loading - When to Avoid It](#19-lazy-loading---when-to-avoid-it)
20. [WooCommerce Performance](#20-woocommerce-performance)
21. [WordPress Backend Speed](#21-wordpress-backend-speed)
22. [WPML Speed Optimization](#22-wpml-speed-optimization)
23. [Security Without Performance Impact](#23-security-without-performance-impact)
24. [WP-Cron Management](#24-wp-cron-management)
25. [wp_options Table Cleanup](#25-wp_options-table-cleanup)
26. [HTTP Protocol & Compression](#26-http-protocol--compression)
27. [Quick Wins Checklist](#27-quick-wins-checklist)

---

## 1. Core Philosophy

WPJohnny's approach to WordPress speed optimization is fundamentally different from most guides. The core principles are:

### Rule #1: Optimize for HUMAN VISITORS, Not Speed Tests
- Speed test scores (PageSpeed, GTmetrix, Pingdom) are not the goal
- A site that renders instantly but takes 6 seconds total is better than one blank for 2.8 seconds then fully loads at 3 seconds
- "If you want A+/100 scores, I am not your guy!"

### Three Fundamental Principles
1. **Decrease code, do not add to it** - Code can only be lightened by removing it, not by adding optimization plugins on top
2. **Optimize for users, not test scores** - Real user experience trumps synthetic benchmarks
3. **Caching is LAST** - Set up caching only after everything is manually optimized; caching first is only a band-aid

### The Car Analogy
- The web server is the "engine" and the code is the "weight"
- Goal: improve the web server "engine" while decreasing code "weight"
- Installing more plugins to "lighten" existing code is like adding a turbocharger to a car that's towing a trailer of junk

### Impact Measurement
Measure every optimization in milliseconds:
- **LOW impact**: 100-200ms savings
- **MEDIUM impact**: ~500ms savings
- **HIGH impact**: 1+ second savings

Speed improvements compound across layers. Earlier optimization layers (hosting, theme) provide bigger wins than minor tweaks.

---

## 2. Web Hosting & Server Optimization

### Datacenter Location
- Keep DNS ping times under 100ms from server to visitors; 50ms is ideal
- US coast-to-coast averages 80ms; Western Europe 40-50ms; most Asian countries 80ms
- USA west coast recommended for balanced worldwide traffic
- Tier-4 datacenters offer 99.9999% uptime guarantees

### Hosting Tiers

| Tier | Cost/Month | Capacity | Recommendations |
|------|-----------|----------|-----------------|
| Shared | $5-30 | Under 100K hits/month | SiteGround, Kinsta, WP Engine |
| VPS/Cloud | $30-300 | Up to 30M hits/month | Cloudways, Gridpane |
| Dedicated | $200+ | High-traffic sites | LiquidWeb |

### Why Shared Hosting is Problematic
- "SHARED hosting = SHARED resources" across thousands of low-paying customers
- Outdated hardware and software (often 2+ generations behind)
- External databases on separate servers create additional latency
- Only ~$2 of a $5/month fee actually covers server infrastructure
- Frequent restarts due to resource conflicts
- Outdated PHP/MySQL versions remain unpatched
- DDoS and brute-force attacks can bring down entire shared servers

### Why Managed VPS Servers Are Often Slow
- Providers use vague terms like "vCPU" instead of transparent hardware specs
- A "$119/month managed VPS with 4 vCPUs" may underperform a "$20/month unmanaged VPS"
- Providers deploy "stock settings" without optimization
- Servers optimized to hold as many accounts as possible to maximize profits

**Red Flags in Hosting:**
- Storage listed as RAID-10 (mechanical drives, not SSD)
- "Unlimited" bandwidth claims
- No CPU specifications mentioned
- No burst capacity allowances

**Better Alternatives:**
- Unmanaged VPS from hardware-focused providers (Linode, DigitalOcean)
- Managed WordPress platforms (Cloudways, Gridpane, RunCloud)
- A properly configured $10/month unmanaged VPS typically outperforms an $80/month managed VPS

### External DNS
- Use services like Cloudflare or DNS Made Easy to reduce lookup latency
- Enables quick redirects during emergencies or migrations
- Provides faster problem mitigation

---

## 3. Web Server Selection

### Recommended Web Servers

| Server | Best For | Key Advantage |
|--------|----------|---------------|
| NGINX | Straightforward sites | Simple configuration, proven stability |
| LiteSpeed | Feature-rich WordPress sites | Built-in WordPress cache plugin, .htaccess support |
| OpenLiteSpeed | Budget-friendly LiteSpeed alternative | Free, LiteSpeed advantages, includes cache plugin |

### Avoid
- **Apache**: If required, use MPM events instead of worker or prefork
- Keep web server software updated for protocol improvements

### NGINX vs OpenLiteSpeed Comparison
- **Uncached**: NGINX handles fewer requests but with reasonable response times (~1s); OpenLiteSpeed processes more requests but with slower initial responses (~9s)
- **Cached**: Both run virtually at the same speed once cache kicks in (~66ms per request)
- **Critical insight**: Caching strategy matters far more than web server choice
- **LiteSpeed's real advantage**: The dedicated LiteSpeed Cache WordPress plugin, which is a "HUGE advantage" over NGINX

### When to Choose OpenLiteSpeed
- Migrating from Apache (needs .htaccess compatibility)
- Prioritizing ease of configuration
- Seeking built-in WordPress optimization tools

### When to Stick with NGINX
- Already satisfied with performance
- Comfortable with manual configuration
- Operating high-traffic sites requiring complex load balancing

---

## 4. PHP Configuration

### PHP Version Impact
- PHP 7.0 runs 3x faster than PHP 5.6
- Each subsequent version (e.g., 7.3 vs 7.2) yields ~10% improvement
- Always use the latest available version while testing theme/plugin compatibility

### Recommended PHP Settings

| Setting | Recommended Value | Notes |
|---------|------------------|-------|
| `max_execution_time` | 30-60 seconds | Higher for long processes like imports |
| `max_input_time` | 60 seconds | Increase only for lengthy operations |
| `max_input_vars` | 1000 | Unless plugins require more |
| `memory_limit` | 256M | Set lower to identify memory hogs via error logs |
| `zlib.output_compression` | Disabled | Leave off |

---

## 5. Database Optimization

### Database Engine Selection
- **Use MariaDB over MySQL** - MySQL 8 is substantially better than 5.7
- **Convert MyISAM tables to InnoDB** using phpMyAdmin or plugins (Servebolt Optimizer, LiteSpeed Cache)
- Run **MySQLTuner** for configuration recommendations

### Object Caching
- **Redis is superior to Memcache** for object caching
- Consider UNIX sockets for Redis/Memcache (25% faster than TCP sockets)
- Object caching is useful for high-traffic sites with dynamic content
- Avoid object caching on low-traffic static sites (overhead not worth it)

### wp_options Table Cleanup

**Performance Thresholds:**
- **Ideal**: Below 500KB of autoloaded data
- **Acceptable**: Up to 1MB
- **Critical**: Above 1MB requires immediate cleanup
- Sites with 40MB+ have experienced severe crashes

**Diagnostic SQL Queries:**
```sql
-- Check total autoload size
SELECT SUM(LENGTH(option_value)) as autoload_size
FROM wp_options WHERE autoload='yes';

-- List top offenders by size
SELECT option_name, length(option_value) AS option_value_length
FROM wp_options WHERE autoload='yes'
ORDER BY option_value_length DESC LIMIT 200;

-- Find specific plugin entries
SELECT * FROM wp_options
WHERE autoload = 'yes' AND option_name LIKE '%pluginname%';
```

**Common Bloat Culprits:**
- BackupBuddy, Jetpack, Revolution Slider
- Thrive Architect/Leads, WPMU DEV suite
- Redux framework (theme-based)
- Transient data accumulation
- BeRocket, SchemaPro, Security Ninja
- Spectra Gutenberg Blocks, TagDiv Newspaper theme

**Investigation Techniques:**
- Edit entries to review stored data
- Google the option name in quotes with "WordPress" or "plugin"
- Search partial prefixes (e.g., "wds_" for option "wds_service_results")
- Temporarily set autoload to "no" for testing; revert if issues arise
- Always backup database before deleting entries

### Database Cleanup Tools
- **Advanced Database Cleaner** - "incredible for tidying up your DB" - better than WP Optimize
- Available cleanup tasks: delete post revisions, remove auto-drafts, clean expired transients, optimize tables, convert to InnoDB

---

## 6. Theme Optimization

### Theme Selection (Speed Ranking)

**Recommended Fast Themes:**
1. **GeneratePress** - "Easily the fastest WordPress theme" - allows the most functionality with fewer plugins; best for DIY implementation
2. **Genesis Framework** - Well-coded, fast, excellent custom-coded base framework; biggest and strongest community
3. **Kadence** - Clean design vibe, not generic stock look
4. **Blocksy** - Great coding, super fancy starter designs, now a top player
5. **Neve** - Nice designs and UI, amazing customer support
6. **Artisan Themes** - Unique designs with incredible modules feature without pagebuilder bloat

**Themes to AVOID (Bloated/Slow):**
- **AVADA** - "Bloated, slow, poorly-coded, many issues"
- **Electro** - "Crazy bloated! 1000+ queries compared to under 100"
- **Jupiter X Theme** - "Slow and bloated"
- **ThemeForest themes** (The7, BeTheme, Enfold, X) - "junk themes piling on features to be everything to everyone"
- Any theme from ThemeForest, Envato, or Code Canyon

**Why these themes are slow:** "They load every CSS/JS library ever invented, so that people don't have to learn how to code."

### Theme Optimization Hierarchy
Custom-coded themes > well-coded frameworks (GeneratePress/Genesis) > bloated off-the-shelf themes

### Custom Theme Development Best Practices
- **Mobile-first design**: Cleaner code, offloads rendering to stronger desktop CPUs
- **Hard-code critical elements**: Menus, headers, footers, homepages
- **WP_Query**: Use wisely; avoid database abuse
- **Clean CSS**: Write from scratch; refactor over time
- **Minimize JavaScript**: Include only for mobile menus, search, essential functions
- Build simple functions directly into theme (avoid micro-plugins)

### Theme Cleanup Checklist
- [ ] Disable loading animations and spinners (improves perceived speed)
- [ ] Disable lazy loading (improves perceived load)
- [ ] Disable unused effects: animations, smooth scrolling, embedded maps
- [ ] Combine custom CSS from plugins into theme custom CSS area
- [ ] Enable theme CSS/JS minification options if available
- [ ] Convert JS effects to CSS when possible
- [ ] Remove JS dependency from mobile menus (build with CSS)
- [ ] Disable jQuery Migrate if unnecessary
- [ ] Consolidate JS hacks into single global file
- [ ] Place non-critical JS in footer only
- [ ] Limit essential JS to: mobile menu, search, ATF sliders

---

## 7. Page Builder Impact & Migration

### Why Page Builders Kill Performance
Page builders (Elementor, DIVI, WPBakery, Beaver Builder, AVADA) create:
- Excessive DOM elements slowing browser processing
- Massive CSS/JS libraries loaded on every page
- Cumulative layout shift through multiple browser repaints
- Increased server response times
- Large amounts of unused code

### Recommended Gutenberg Alternatives

**Block Libraries (Simple, fewer features):**
- **Otter Blocks** - Beautifully simplified set of blocks with conditional display
- **CoBlocks** - Clean interface, minimal approach
- **GenerateBlocks** - Minimal core blocks; suited for developers

**Native Gutenberg Pagebuilders (Comprehensive):**
- **Kadence Blocks** - Superior design templates with minimal interface feel
- **Stackable** - Most extensive block collection with mature community
- **Spectra** - Comprehensive blocks but caution: may cause high autoloads

**Proprietary Sitebuilders (Advanced):**
- **Bricks** - Most powerful developer features, strong community; gives "fancy, fun visual editing experience AND super fast speeds"
- **Cwicly** - Works with native Gutenberg editor; compatible with other plugins
- **Breakdance** - User-friendly interface similar to Elementor/DIVI

### Migration Strategy (Page Builder to Gutenberg)
1. Inventory pages using page builders (start with simpler pages first)
2. Disable page builders on staging sites to identify what breaks
3. Rebuild layouts using grid blocks, container blocks, native WordPress blocks
4. Keep page builders installed but deactivated initially; wait weeks before deleting
5. Simple animations and hover effects may need CSS knowledge to preserve

**Expected result**: "The speed difference will be massive."

---

## 8. Plugin Optimization

### Plugin Selection Philosophy
- **Consumer-grade plugins**: Many features, ease-of-use focus; slower
- **Developer-grade plugins**: Essential features, minimal styling, code quality; faster
- Multiple specialized plugins sometimes leaner than one bloated package
- Consult developer communities for plugin reputation (not just WordPress.org reviews)

### Plugins That Kill Performance (Avoid)

| Category | Avoid | Replace With |
|----------|-------|-------------|
| Page Builders | WPBakery, DIVI, AVADA, Elementor, Beaver Builder | Gutenberg + block plugins |
| Sliders | Slider Revolution | MetaSlider or Smart Slider 3 |
| Mega Menus | UberMenu | Max Mega Menu or custom code |
| Marketing | Thrive Architect, Thrive Leads, Thrive Comments | Lighter alternatives |
| Analytics | ExactMetrics | GAinWP or direct script |
| All-in-One | Jetpack | Only if required for WooCommerce |
| Icons | Font Awesome (30-200KB) | Custom icon fonts, SVGs, or CSS |
| Cache | W3 Total Cache | "Way too bloated and technical" |
| Cache | WPMU Hummingbird | "absolute garbage. Bloated and slow" |
| Cache | WP Super Cache | Outdated and slow |
| Image | WP Smush, EWWW | "horrible compression quality/file-size ratio" |

### Unnecessary Plugins (Do Natively Instead)
- **Custom CSS**: Use theme settings or Customizer > Additional CSS
- **Browser cache**: Use main cache plugin
- **Fonts**: Configure in theme
- **Header/footer code**: Add directly to theme files
- **HTTPS/SSL**: Set manually, no plugin needed
- **Galleries**: Use Gutenberg + WP Featherlight
- **Redirects**: Use .htaccess or server redirects
- **Simple performance tweaks**: Combine into single cache plugin

### Plugin Load Optimization
Many plugins load CSS/JS globally (every page) when only needed conditionally:

**Common Offenders:**
- Contact Form 7: Loads form CSS/JS on every page (use Fluent Forms instead)
- WooCommerce: Loads on non-shopping pages (disable via functions.php snippets)
- Slider plugins: Check for global load toggle
- WooCommerce AJAX cart fragments: Disable on non-cart pages

**How to Fix:**
1. Check plugin settings for "disable CSS/JS" options
2. For plugins without built-in toggles, use filter hooks in functions.php
3. Copy needed CSS/JS to theme custom areas after dequeuing
4. Use Asset CleanUp or Perfmatters to disable per-page

### Plugin Research Methodology
- Check development company background and other products
- Review developer community reputation (beyond WordPress.org)
- Assess update frequency and support quality
- Logical pricing: one-time fee (small), monthly (large), lifetime (new)
- Avoid marketplace plugins (ThemeForest, Code Canyon) - usually abandoned

### Redirect Handling
- PHP-level redirects are slower than server-level; they affect all traffic
- Use .htaccess (Apache/LiteSpeed) with proper rewrite rules
- NGINX redirects require server config access
- Export redirects from plugins to .htaccess format
- Use Safe Redirect Manager if plugin-based redirects are necessary
- Monitor 404s via Google Search Console
- LiteSpeed caches .htaccess, eliminating performance impact

---

## 9. Recommended Plugin Stack

### Performance-Focused Plugin Recommendations

**Caching:**
1. **WP Performance** (Free) - "awesome free cache plugin. Solid, reliable, many features, amazing UI"
2. **Swift Performance** (Free/Pro) - "Lite version is best free cache plugin, paid version is the fastest full-featured cache plugin"
3. **LiteSpeed Cache** (Free) - Best for high-traffic sites on LiteSpeed servers
4. **FlyingPress** (Pro) - "amazing premium cache plugin" with simple interface
5. **WP Rocket** (Pro) - Easy to use, reliable alternative; not recommended for NGINX

**SEO:**
1. **SEO Framework** - Top choice: "Clean and bloat-free"
2. **All-in-One SEO** - Second favorite: "High quality, and fast"
3. **Yoast SEO** - Improved but "annoying nag screens"

**Image Compression:**
1. **ShortPixel** - Best compression and glossy formats; does not slow WP admin
2. **WP Compress** - Great for sharp details, lower price than ShortPixel
3. **LiteSpeed Cache** (Free) - Handles massive sites

**Forms:**
1. **Fluent Forms** - "#1 favorite form plugin for both FREE and PAID"
2. **WS Form** - Developer favorite, comprehensive
3. **Gravity Forms** - Quality premium option
- **Avoid Contact Form 7** - "I hate how it loads on every page"

**Database:**
- **Advanced Database Cleaner** - "incredible for tidying up your DB"
- **WP Migrate Lite** - "easiest way to move databases"

**Backup:**
- **BackWPup** - "awesome free plugin" with S3 support
- **WPVivid** - Free with clone/staging features

**Security:**
- **Wordfence** - Full security plugin with malware scan and firewall
- **FluentAuth** - Login authorization with 2FA, social login, CAPTCHA

**Content:**
- **WP Show Posts** - Show posts anywhere without heavy queries
- **Lightweight Grid Columns** - Create layouts "without having to use a pagebuilder"

---

## 10. CSS & JavaScript Optimization

### JavaScript Reduction Strategy
1. Convert JS effects to CSS when possible (reduces conflicts)
2. Remove JS dependency from mobile menus; build with CSS
3. Disable jQuery Migrate if unnecessary
4. Consolidate JS hacks into single global file
5. Place non-critical JS in footer only
6. Limit essential JS to: mobile menu, search functionality, ATF sliders

### CSS Optimization
1. Write CSS from scratch when possible
2. Remove unused CSS from themes and plugins
3. Combine custom CSS from plugins into theme custom CSS area
4. Minify files separately rather than merging them
5. Use Critical CSS concept for above-the-fold styling
6. Refactor CSS over time to remove redundancy

### Dequeuing Plugin CSS/JS
```php
// Example: Dequeue Contact Form 7 styles/scripts on non-form pages
add_action('wp_enqueue_scripts', function() {
    if (!is_page('contact')) {
        wp_dequeue_style('contact-form-7');
        wp_dequeue_script('contact-form-7');
    }
});
```

---

## 11. Why Not to Combine CSS/JS

This is one of WPJohnny's most important and counterintuitive pieces of advice.

### The Problems with Combining

**1. Slows Initial Page Rendering**
Modern HTTP/2 allows parallel requests, eliminating the old rationale for combining files. Combined files delay rendering because the entire stylesheet must load before any content displays. Smaller separate files allow progressive rendering.

**2. Creates Compatibility Issues**
Merging mechanisms frequently break functionality. "Cache plugin broke my site" is a weekly complaint in WordPress communities. Potential failures in contact forms, scroll functions, or AJAX operations.

**3. Increases Page Load Unnecessarily**
A merged file loads unnecessary code on every page. WooCommerce CSS loads on non-commerce pages. Pagebuilder styles appear on plain pages. Creates wasteful bloat.

**4. Delays Cache Rebuilding**
Combining forces cache plugins to rebuild merged assets whenever content updates, rather than just rebuilding HTML cache.

### What to Do Instead
- **Defer JavaScript** to page footer (except critical above-the-fold scripts)
- **Load CSS progressively** for different sections
- **Use Critical CSS** concept for above-the-fold styling
- **Minify files separately** rather than merging them
- **Rely on browser caching** with long expiry times on individual files

### Exceptions (When Combining Might Help)
- Theme/plugin combining their own code (native optimization)
- Very small files (under 3KB total)
- Lightweight sites with minimal CSS/JS (under 10KB total)
- Inline CSS/JS on ultra-minimal pages

---

## 12. Image Optimization

### Format Selection Guide

| Format | Best For | Notes |
|--------|----------|-------|
| JPEG | Photos, multi-color images | Best quality-to-size ratio for photos |
| PNG | Few colors, sharp lines, transparency | Avoid when transparency not needed |
| WebP | Modern alternative | Better compression than JPEG; include fallbacks |
| SVG | Icons, simple graphics | Scales infinitely, CSS-controllable |
| GIF | Animations only | Rarely professional use |

### Dimension Strategy
- Resize to exact display area dimensions
- **Retina**: Use double-size images (800px for 400px display area)
- Less critical/smaller images: exact size is acceptable (no retina needed)
- Process camera photos: resize, crop, edit BEFORE uploading

**Device-Specific Sizing:**
- Desktop: ~1200px width
- Tablet: ~800px width
- Mobile: ~400px width
- Double dimensions for retina displays

### Media Size Configuration
- Set correct sizes in WordPress Settings > Media after design completion
- WooCommerce: Configure in Appearance > Customize > WooCommerce > Product Images
- Disable unused theme/plugin media sizes
- Many themes generate 20-30 thumbnail variants despite using only 3
- Fewer media sizes = less server storage and faster backups
- Regenerate thumbnails after cleanup

### Compression Workflow

**Manual Compression:**
- Photoshop: Export/Save-for-Web, target JPEG 50-60% quality
- Lightroom: Quality slider
- ShortPixel free web tool for quick one-offs

**Automated (Plugin-Based):**
- **ShortPixel** (recommended) - Best quality/file-size ratio; does not slow admin
- **LiteSpeed Cache** - Free, handles massive sites
- **WP Compress** - Great for sharp details, lower price

**Avoid:** WP Smush and EWWW - "horrible compression quality/file-size ratio"

### PNG-to-JPEG Conversion
- Convert transparent PNGs with solid backgrounds to JPEG
- Match background color; saves 50% file size
- No visual degradation on solid backgrounds

### Icon Implementation Strategy

| Scenario | Method | Why |
|----------|--------|-----|
| 2-3 simple icons (arrows, search, hamburger) | CSS | Zero weight |
| 2-3 complex icons | SVG | Lower weight than font |
| 10+ icons | Custom icon font (Fontastic, Fontello, IcoMoon) | Efficient bundling |
| Avoid | Font Awesome (30-200KB) | Loads thousands of unused icons |

**SVG Optimization:** Use Jake Archibald's SVGOMG tool for character removal and quality reduction.

### Decorative Graphics Optimization
- Redraw simple graphics/icons in CSS (lines, blocks, basic shapes)
- CSS icon collection: cssicon.space (512 pure-CSS icons)
- Combine images with CSS: gradients, shadows, filters

### Video Compression
- Always compress before deployment
- Output MP4 (balanced) or WebM (smaller)
- Remove unnecessary audio or color if background/silent video
- Quick method: Upload to YouTube/Vimeo, download compressed version
- Consider: Does video need sound, color, or that size?
- Images are often a better alternative to auto-playing video

### Browser Cache for Images
- Theme assets (PNG, SVG, favicon): 1 year expiry
- Older post images: 1 month
- Recent post images: 1-7 days (accounts for post-publication edits)
- Optimal range: 7-30 days

### CSS Sprites
- Combine multiple small images into one, call via CSS positioning
- Outdated for HTTP/2 environments and modern flat design
- Consider only with many small, multi-color images that are not SVG/font-compatible

---

## 13. Font Optimization

### Loading Methods (Speed Ranking)
1. **System fonts** - Fastest; limited design options
2. **Locally-loaded fonts** - Faster than webfonts; cached and CDN-friendly
3. **Webfonts (3rd-party like Google Fonts)** - Slowest baseline; cached after first load

### Font Quantity Guidelines
- **One font**: Fastest, cleanest
- **Two fonts**: Acceptable; disable unused styles
- **Three+ fonts**: Acceptable if thoughtfully used
- Create design variation with weight, size, spacing, case, color instead of more fonts

### Font Weight & Style Management
- Load only necessary weights: typically 400 (normal) and 700 (bold)
- Disable unused styles: italic variants rarely used for headings
- Disable unused character sets: extended Latin, Greek, Cyrillic unnecessary for English sites
- Body text needs: 400, italic 400, bold 700
- **Use variable fonts** to load multiple weights in single file

### Font Format
- **WOFF2** is recommended - most compressed/lightweight, suits all modern browsers

### Locally Loading Webfonts (Key Technique)
1. Download webfonts from source (e.g., Google Fonts)
2. Host on your server; change request URL from 3rd-party to local
3. **Tool**: google-webfonts-helper.herokuapp.com (Mario Ranftl)
4. **Plugin**: OMGF for Google Fonts local hosting
5. Eliminates 3rd-party requests; enables long browser cache

### Font Subsetting (Advanced - Huge Savings)
Load only the characters actually used in your content.

**Options:** Basic Latin, uppercase-only, numbers-only, currency symbols, specific characters

**Potential reduction:** Up to 1040x smaller files in extreme cases

**Tools:**
- Font Squirrel Webfont Generator (Expert mode, subset options)
- Everything Fonts Font Subsetter
- CLI: fonttools, glyphhanger, pyftsubset
- FontForge for character-by-character editing

When subsetting to this level, locally loading is the only approach that makes sense - no point making multiple calls to Google's font server for 1/3 of a font.

### Font Preloading
- Preload in header via `<link rel="preload">` tags
- Useful when content would load before font CSS

### Preventing Duplicate Font Loading
- Common rookie mistake: theme, pagebuilder, and plugin all load the same webfont
- Load fonts only once, preferably from theme
- Plugin settings: select "inherit" instead of picking fonts
- Watch pagebuilders, sliders, pop-ups, mega-menus for duplicate calls

### Font Display Strategy
- Load webfonts BEFORE content (accept FOIT; better UX than FOUT)
- **Disable font-display: swap** - Creates worse user experience than the FOIT it attempts to fix
- Load from theme, not plugins
- Plugin typography options should default to "inherit"

### Font Awesome Optimization
If you must use Font Awesome:
1. Download locally; change CSS request to local path
2. Remove unused icons (manual editing required)
3. Better: Replace with custom icons or SVGs
4. Reference: "Optimize Font Awesome to ridiculously low size of 10kb!" by WEBJEDA

---

## 14. Caching Strategy

### Caching Order of Operations
1. Optimize everything else FIRST (hosting, theme, plugins, code)
2. Implement caching LAST as the final performance layer
3. Caching on an unoptimized site is a band-aid, not a solution

### Types of Caching

**Full-Page Caching:**
- LiteSpeed Cache: Offers full-page caching with WordPress plugin
- FastCGI: NGINX caching method; pair with helper plugins
- Disk-based caching: Most common approach for WordPress

**Object Caching:**
- Redis: Superior to Memcache
- Useful for high-traffic sites with dynamic content
- Avoid on low-traffic static sites
- Cache expiry: 5-60 minutes recommended
- Use UNIX sockets (25% faster than TCP sockets)

**Browser Caching:**
- Set via cache plugin or .htaccess
- Long expiry times for static assets
- Short expiry for frequently updated content

### Caching Exceptions
- Disable caching on form pages
- Disable caching on shopping carts and checkouts
- Disable caching on WooCommerce account pages
- Private pages can be cached but require careful configuration

### Cache Plugin Rankings

**For Apache Servers:**
1. Swift Performance Lite (free)
2. Swift Performance Pro (paid)
3. WP Rocket (paid)
4. Simple Cache (free)

**For LiteSpeed Servers:**
1. LiteSpeed Cache (free) - Best option
2. Swift Performance
3. Simple Cache

**For NGINX Servers:**
1. Swift Performance
2. Breeze
3. Simple Cache

### Scenario-Based Selection

| Scenario | Recommended Plugin |
|----------|-------------------|
| Small sites, low traffic | WP Performance or Swift free |
| Large sites (400+ pages, 10K+ hits/month) | Swift Pro or LiteSpeed Cache |
| Non-LiteSpeed servers | WP Rocket or Swift |
| Content-heavy, low-traffic | Swift Pro (preloading excels) |
| WooCommerce stores | Swift Performance, Breeze, or WP Rocket |
| Optimized lean sites | Simple Cache with Redis |
| High-traffic sites | LiteSpeed Cache for server-level optimization |
| Shared hosting | Breeze or WP Rocket |

### Performance Expectations
- Realistic improvements: 40-70% speed increase on bloated sites
- Modest 10-20% gains on already-optimized sites

---

## 15. Cache Plugin Configuration

### Swift Performance Configuration

**General Settings:**
- Use Compute API (Premium): Enable - reduces CPU during cache pre-building
- Hide Footprints: Disable to verify caching via HTML comments
- Custom Htaccess: Place 301 HTTPS redirects here
- Heartbeat Control: Disable unless tracking sessions

**Media Optimization:**
- Lazy Load Images: **DISABLE** - "not loading everything initially means everything loads slower!"
- YouTube Smart Embed: Enable if videos are below the fold
- Image Optimization: Choose "picture elements" for WebP (avoids CDN conflicts)
- Gravatar Caching: Enable only for pages with 500+ comments

**Critical Settings:**
- Merge Scripts/Styles: **DISABLE BOTH** - "I wouldn't merge JS if I were you"
- Critical CSS Generation: **DISABLE** - Causes FOUT issues
- Minify HTML/CSS/JS: Disable if using Cloudflare (handles this already)
- Font Display Swap: **DISABLE** - Creates worse UX
- Enable Server Push: **DISABLE** - High CPU, little benefit
- Disable Emojis: Enable if emojis not used

**Caching Configuration:**
- Caching Mode: "Disk Cache with Rewrites" for maximum speed
- Cache Expiry Mode: "Action based" for most sites
- Enable Browser Cache and Gzip: Both ON
- Separate Mobile Cache: Disable (unless using AMP)

**Caching Exceptions:**
- Exclude post types without public-facing URLs
- Exclude pages with forms, WooCommerce account/cart/checkout
- Add "#revision#", "#autosave#", "#json#" to exclude URLs
- Exclude author pages, REST, and feed URLs

**Cache Warmup:**
- Prebuild Speed: "Unlimited" for VPS or sites under 1,000 pages
- Warmup Table Source: "Sitemap" for large sites (prioritizes important pages)
- Disable prebuild for Author, Terms, REST, Feed pages
- Enable only Archives (for category pages)

**WooCommerce Integration:**
- Cache Empty Minicart: Enable
- Disable Cart Fragments: **DO NOT disable** - removes needed cart functionality
- WooCommerce Session Cache (Beta): **DISABLE** - causes unpredictable behavior

**Troubleshooting:**
- Broken styling: First disable Merge Scripts/Styles
- High CPU: Limit threads to 1-3, disable merge and minify
- WSOD/Error 500: Delete plugin folder, cache directory, mu-plugins loader, htaccess rules

### LiteSpeed Cache Configuration

**Essential Quick Setup:**
1. Disable Guest Mode; enable cache
2. Turn OFF cache for logged-in users; disable "Serve Stale"
3. Drop query strings: fbclid, gclid, utm*, _ga
4. Enable browser cache
5. WooCommerce: Disable privately cached carts
6. Critical CSS: **Turn OFF**
7. Emoji: Enable removal

**CSS Optimization - All DISABLE:**
- Critical CSS: Unreliable
- CSS Minification: Delegate to Cloudflare
- CSS Combining: Risks breaking functionality
- Load CSS Asynchronously: Prevents layout shift
- Inline CSS Async Library: Causes rendering problems

**JavaScript Optimization - All DISABLE:**
- JS Minification: Use CDN services instead
- JS Combining: Unless extensively tested
- Exclude jQuery: Enable to prevent optimization conflicts

**HTML & Media - Mostly DISABLE:**
- HTML Minification: Cloudflare handles this better
- Lazy Loading Images: **DISABLE** (author strongly dislikes)
- Remove WordPress Emoji: Enable
- DNS Prefetch: Specify external domains (analytics, fonts, CDN)

**WooCommerce:**
- Privately Cache Cart: **DISABLE** (causes mixed cart sessions)
- Use Front Page TTL for Shop: Enable

**Object Caching:**
- Enable only if Redis/Memcache installed AND significant dynamic queries
- Redis over Memcache
- Cache WP-Admin: Keep disabled
- Store Transients: Leave enabled

**Key Philosophy:** "Don't enable features you don't understand." Default settings work well for most sites.

---

## 16. CDN Configuration

### CDN Rankings

| CDN | Tier | Key Feature | Cost |
|-----|------|-------------|------|
| Cloudflare | Top | Fastest DNS, free tier, global coverage | Free-$20+ |
| BunnyCDN | Top | Cheap, fast, transparent billing | Low |
| Amazon CloudFront | Top | Best for large files/video, S3 integration | Variable |
| KeyCDN | Good | Strong reviews, good for new implementations | Moderate |
| Fastly | Good | Performs well when operational | Higher |
| Akamai | Mid | Fast but expensive | High |
| MaxCDN/StackPath | Mid | Inconsistent performance | Higher |
| CDN77 | Avoid | "slow! Don't even bother" | - |
| CDN.net | Avoid | Billing problems | - |
| Beluga | Avoid | Poor performance, manual SSL, bad support | - |

### CDN Selection Criteria
1. **Budget**: Bandwidth requirements and pricing models
2. **Content type**: Static assets vs large files vs dynamic pages
3. **Geographic coverage**: POP locations matching visitor distribution
4. **Performance**: Speed, reliability, hit frequency

### Configuration Tips
- **Static Assets Only**: Cloudflare free plan suffices for images, CSS, JS
- **Maximum Speed**: Select providers with extensive page rule customization
- **Low-traffic WordPress sites**: Cloudflare free tier is effective
- **Premium features**: Require paid upgrades ($5+/month for private SSL)

### CDN for Image-Heavy Sites
1. Start with Cloudflare's free tier
2. Upgrade to BunnyCDN if additional speed required
3. Choose Amazon CloudFront for extensive options or S3-integrated workflows

---

## 17. Core Web Vitals

### WPJohnny's Position on CWV
- "If your site is built well, it'll rank fine for SEO without any missed opportunities"
- "Many super-fast high-ranking sites don't satisfy all those recommendations"
- Well-built sites already satisfy CWV naturally without focused optimization
- CWV cannot accurately measure for every type of web application
- WordPress loads differently than Joomla or Shopify

### Practical CWV Optimization Tips

**1. Eliminate Page Builders (Biggest Impact)**
- Remove Elementor, DIVI, WPBakery, etc.
- They load excessive JavaScript/CSS, cause CLS through repaints, and generate unused code
- Migrate to Gutenberg or modern builders like Bricks

**2. Remove Third-Party Scripts**
- Ads, chatbots, trackers extend total load time
- They load slower than local assets and often include unused functionality
- Eliminate non-essential scripts; defer only if absolutely necessary

**3. Asset Optimization**
- Defer non-critical CSS and JavaScript
- Generate critical CSS (if it works properly on your setup)
- Reduce unused code by removing plugins/services
- Minimize web fonts
- Self-host third-party assets (Google Analytics, web fonts)

**4. Image Optimization**
- Reduce image quantity where possible
- Select appropriate formats (JPEG vs PNG)
- Compress images appropriately
- Consider CDN implementation

**5. Implement Caching**
- Improves server response times
- Enables CSS/JavaScript optimization
- Requires proper configuration to avoid issues

### Key Caveat
Aggressive CWV optimization may harm actual user experience. Always prioritize what real users see and feel over what a test score reports.

---

## 18. Why Speed Test Scores Do Not Matter

### The Core Problem
Speed test scores encourage optimization for automated crawlers rather than actual users. "Optimizing for speed tests means delivering as FEW ASSETS AS POSSIBLE" rather than the intended user experience.

### What Actually Matters Instead
- **TTFB (Time to First Byte)**: Server response speed
- **First Paint/Content Paint Times**: When content becomes visually available
- **Critical waterfall items**: Essential resources at beginning of load sequence
- **The "Eye Test"**: Whether the site appears fast to real visitors

### Why Scores Are Flawed
1. **Lack of qualification**: Most users reading scores do not understand the metrics
2. **Outdated recommendations**: Tests still recommend GZIP over Brotli, penalize parallel HTTP/2 requests
3. **Context blindness**: An e-commerce site with images should not be scored the same as a text blog
4. **Wrong priorities**: Penalizing third-party scripts you cannot control (Google Analytics, Google Fonts) as heavily as your own code

### How to Properly Measure Performance
1. Use browser developer tools (Network tab) to see real-world loading
2. Examine the "Timings" tab in GTmetrix rather than overall scores
3. Prioritize visible rendering speed over total load completion
4. A site that renders instantly but takes 6 seconds total is BETTER than one blank for 2.8 seconds then fully loads in 3 seconds
5. Use FastOrSlow.com for unbiased raw data

---

## 19. Lazy Loading - When to Avoid It

### WPJohnny's Position
Fundamentally opposed to lazy loading for most websites. "It hurts UX (user experience) at the benefit of maybe tricking page speed tests." Lazy loading delays image display, making sites appear slower to actual users despite improving test scores.

### When to AVOID Lazy Loading
- Images positioned above the fold (delays header/banner rendering)
- E-commerce sites (users scrolling through products encounter loading delays)
- Sites with only a few images per page (static assets load quickly anyway)
- Fast-loading websites with strong servers (unnecessary optimization)
- When the primary motivation is deceiving page speed tests

### When Lazy Loading Makes Sense
1. **Content-heavy below-the-fold images** - Loading assets users may never view wastes resources
2. **Large image files without CDN** - Preserves bandwidth and server resources
3. **Weak servers** - Reduces processing burden
4. **Script optimization** - Effectively delays non-critical JavaScript

### Better Alternatives
- Implement a CDN to handle image delivery efficiently
- Use image preloading techniques (`rel="preload"` tags)
- Optimize images themselves rather than delaying their delivery

### Core Principle
"The point of your website is to serve users first and robots/search-engines second." True performance improvement means faster actual loading, not delayed delivery masquerading as optimization.

---

## 20. WooCommerce Performance

### WooCommerce-Specific Optimization

**Disable WooCommerce on Non-Shopping Pages:**
Use functions.php snippets to prevent WooCommerce CSS/JS from loading on pages that do not need it (blog posts, about page, etc.).

**Cart Fragments (wc-ajax=get_refreshed_fragments):**
- WooCommerce makes AJAX requests on EVERY page to update the cart total
- This happens even on pages without add-to-cart functionality (About Us, Blog Posts, Terms)
- Can account for up to 10-second delays on large sites
- Use the "Disable Cart Fragments" plugin or Perfmatters to selectively disable
- The plugin checks for cart hash cookie; if not present, disables the script while retaining functionality

**Cache Configuration for WooCommerce:**
- Exclude account, cart, and checkout pages from caching
- Cache empty minicart
- Do NOT disable cart fragments entirely in Swift Performance (removes needed functionality)
- Do NOT use WooCommerce Session Cache (Beta) in Swift Performance (causes unpredictable behavior)
- Disable privately cached carts in LiteSpeed Cache (causes mixed cart sessions)

**Product Image Optimization:**
- Configure product image sizes in Appearance > Customize > WooCommerce > Product Images
- Disable unused thumbnail sizes generated by WooCommerce themes
- Use ShortPixel or WP Compress for product image compression

---

## 21. WordPress Backend Speed

### Why the Backend is Slow
The backend is "completely dynamic" - must query the database for every request without caching. It also runs background processes like the Heartbeat API for auto-saving.

### Optimization Priority Order

**1. Audit Plugins & Themes (Most Critical)**
- Use Query Monitor plugin to identify slow queries and memory-heavy components
- Deactivate problematic plugins causing delays
- Replace bloated themes/plugins with higher-quality alternatives

**2. Check for Errors**
- Examine error.log in public_html directory
- Use browser dev tools to identify 404 requests
- Address plugins generating errors

**3. Memory Management**
- Monitor memory with WP Server Health Stats plugin
- Check autoloaded data in wp_options table
- In wp-config.php:
```php
define('WP_MEMORY_LIMIT', '256M');
define('WP_MAX_MEMORY_LIMIT', '256M');
```
- Remove unused plugins' leftover database entries

**4. Upgrade Hosting**
Quality hosting with modern PHP, MySQL, fast disk I/O, and adequate memory limits

**5. Heartbeat API Optimization**
- Use Heartbeat Control plugin or cache plugin settings
- Disable on frontend and non-editor backend pages
- Keep enabled in post editor for auto-saves
- Raise frequency to 120+ seconds

**6. Object Caching (Redis/Memcache)**
- Available primarily on VPS plans
- Cache expiry: 5-60 minutes recommended
- Beneficial for extensive time in backend
- Less useful for occasional admin access

**7. Security Plugin Impact**
Wordfence and Sucuri significantly slow backends through continuous scanning. Consider the security/speed trade-off.

### What Does NOT Help Backend Speed
- Better cache plugins (designed for frontend)
- Performance booster plugins (often increase memory usage)
- Cloudflare caching for admin areas
- Load balancing or clustering (addresses traffic, not slow code)
- Remote databases (increases latency)
- MySQL configuration tuning (rarely the actual issue)

---

## 22. WPML Speed Optimization

### Key Optimization Strategies

**1. Disable Auto-Registration of Strings**
WPML automatically registers thousands of strings from themes and plugins. Disable this feature and manually register only needed strings.

**2. Aggressively Delete Unnecessary Strings**
String translation is "the #1 reason for slow WPML sites."
- Scrutinize every string entry
- Remove all administrative interface text unless requiring multilingual admin
- Delete internal PHP strings visible only in code
- One example: a site with 25,000 strings needed only 100

**3. Maintain Clean Theme Code**
WPML reprocesses theme code, so inefficient theme structure multiplies the plugin's performance impact. Clean theme code can reduce WPML overhead by 500ms to 2 seconds.

**4. Apply Standard Speed Techniques**
- PHP 7+, object caching, page caching, GZIP compression, VPS hosting

**5. Dual-Site Architecture**
For multilingual projects, run the primary language on a non-WPML main domain. Place WPML on a subdomain handling additional languages with their own TLDs.

### Performance Benchmarks
Achievable: 1-second load times on a six-language site with high content volume. WPML overhead: 200-300ms compared to non-WPML equivalents.

---

## 23. Security Without Performance Impact

### Core Principle
Security is best done at server level, not software (PHP) level.

### Skip These (Performance-Draining):
- IP blockers, blacklists/whitelists, brute-force plugins
- External security checks on every visitor
- Security scans and file/directory monitoring on every page load
- Spam blocks and CAPTCHAs (add JavaScript overhead)
- Most traditional security plugins

### Recommended Security Methods

**1. Choose Quality Plugins**
Verify plugins are properly coded by respected developers.

**2. Protect wp-admin Access**
- HTTP authentication to lock down admin pages (zero server overhead)
- Security plugins like Wordfence only if necessary

**3. Disable XML-RPC Protocol**
```apache
<Files xmlrpc.php>
Order Allow,Deny
Deny from all
</Files>
```

**4. Additional Hardening (Zero Performance Impact):**
- Replace default "admin" username
- Rename login from wp-login.php
- Change table prefix from "wp_"
- Install login attempt limiters
- Prevent PHP execution in upload directories
- Use unique database passwords

**5. Use a CDN (Improves Both Security AND Speed)**
Cloudflare (free tier) blocks malicious traffic before reaching your server.

**6. Regular Backups**
Maintain restoration capability for quick recovery.

---

## 24. WP-Cron Management

### The Problem
Default WP-Cron checks on every single page visit, adding overhead to every request.

### The Fix
1. Disable default WP-Cron in wp-config.php:
```php
define('DISABLE_WP_CRON', true);
```
2. Set up a real server cron job with 5-minute intervals
3. Alternative: Use EasyCron third-party service for managed hosting without cron access

### Additional Tips
- Ban resource-heavy cron tasks: cache pre-builders, broken-link checkers
- Reference: "The nightmare that is wp-cron.php" by The cPanel Guy

---

## 25. wp_options Table Cleanup

### Why It Matters
The wp_options table with autoloaded data is queried on EVERY single page load. Bloated autoloads directly slow every request.

### Performance Thresholds
- **Ideal**: Below 500KB autoloaded data
- **Acceptable**: Up to 1MB
- **Critical**: Above 1MB - immediate cleanup needed
- **Catastrophic**: 40MB+ has caused severe site crashes

### Diagnostic Queries
```sql
-- Check total autoload size
SELECT SUM(LENGTH(option_value)) as autoload_size
FROM wp_options WHERE autoload='yes';

-- List top offenders
SELECT option_name, length(option_value) AS option_value_length
FROM wp_options WHERE autoload='yes'
ORDER BY option_value_length DESC LIMIT 200;

-- Search specific plugin data
SELECT * FROM wp_options
WHERE autoload = 'yes' AND option_name LIKE '%pluginname%';
```

### Common Bloat Sources
BackupBuddy, Jetpack, Revolution Slider, Thrive Architect/Leads, WPMU DEV suite, Redux framework, transient data accumulation, BeRocket, SchemaPro, Security Ninja, Spectra Gutenberg Blocks, TagDiv Newspaper theme.

### Cleanup Process
1. Always backup database first
2. Identify top offenders using SQL queries
3. Google option names to identify source plugins
4. Temporarily set autoload to "no" for testing
5. Delete entries from fully removed plugins
6. Use Advanced Database Cleaner plugin for ongoing maintenance

---

## 26. HTTP Protocol & Compression

### HTTP Protocol
- Implement HTTP/2 or HTTP/3 (requires HTTPS/SSL)
- HTTP/2 enables parallelization, feeling ~3x faster than HTTP/1
- Verify with: keycdn.com/http2-test and http3check.net

### Content Encoding
- **BROTLI compression**: Superior to GZIP
  - Static compression: Level 4
  - Enable on CDNs and Cloudflare as well
- **GZIP (legacy fallback)**:
  - Dynamic compression: Level 1
  - Static compression: Level 6

### Server Module Cleanup
Disable unused services to reduce resource usage:
- DNS (if using external like Cloudflare)
- Email (if using G-Suite, MXroute)
- FTP/SFTP (if using SSH)
- Memcache/Redis (if not used for object caching)
- Scan system for listening ports and unneeded services

---

## 27. Quick Wins Checklist

### Immediate Actions (Do These First)
- [ ] Upgrade to latest PHP version
- [ ] Switch to NGINX or LiteSpeed/OpenLiteSpeed
- [ ] Enable HTTP/2 or HTTP/3
- [ ] Enable Brotli compression
- [ ] Disable WP-Cron, set up real server cron
- [ ] Use external DNS (Cloudflare free tier)
- [ ] Check and clean wp_options autoloads (target under 500KB)

### Theme & Design
- [ ] Switch to GeneratePress, Genesis, Kadence, or Blocksy
- [ ] Remove page builders; migrate to Gutenberg
- [ ] Disable loading animations and spinners
- [ ] Disable smooth scrolling and unnecessary effects
- [ ] Build mobile menus with CSS, not JavaScript
- [ ] Hard-code headers, footers, menus where possible

### Plugins
- [ ] Audit all plugins; remove unused ones
- [ ] Replace bloated plugins with lightweight alternatives
- [ ] Disable plugin CSS/JS on pages where not needed
- [ ] Use Fluent Forms instead of Contact Form 7
- [ ] Use SEO Framework instead of Yoast
- [ ] Use ShortPixel for image compression
- [ ] Install Advanced Database Cleaner

### Fonts
- [ ] Locally host Google Fonts (use OMGF plugin or manual method)
- [ ] Use WOFF2 format only
- [ ] Load only needed font weights (400, 700)
- [ ] Disable unused character sets
- [ ] Remove duplicate font loading from plugins
- [ ] Consider font subsetting for maximum optimization
- [ ] Remove Font Awesome; use custom icon fonts or SVGs

### Images
- [ ] Set correct WordPress media sizes
- [ ] Disable unused thumbnail sizes
- [ ] Use JPEG for photos (not PNG)
- [ ] Compress all images (ShortPixel recommended)
- [ ] Size images to actual display dimensions
- [ ] Use SVG for icons and simple graphics
- [ ] Replace decorative images with CSS where possible

### Caching (Do This LAST)
- [ ] Install appropriate cache plugin for your server type
- [ ] Do NOT combine CSS/JS
- [ ] Do NOT enable Critical CSS (unreliable)
- [ ] Do NOT enable font-display: swap
- [ ] Do NOT enable lazy loading (in most cases)
- [ ] Disable minification if using Cloudflare
- [ ] Exclude forms, cart, checkout from caching
- [ ] Enable browser caching

### WooCommerce Specific
- [ ] Disable WooCommerce CSS/JS on non-shopping pages
- [ ] Disable cart fragments on pages without cart functionality
- [ ] Configure product image sizes correctly
- [ ] Exclude account/cart/checkout from cache
- [ ] Disable privately cached carts in cache plugin

### Database
- [ ] Convert MyISAM tables to InnoDB
- [ ] Clean expired transients
- [ ] Delete post revisions and auto-drafts
- [ ] Remove leftover data from deleted plugins
- [ ] Run Advanced Database Cleaner regularly
- [ ] Consider Redis object caching for high-traffic sites

---

## Source Articles

All advice compiled from WPJohnny.com articles:

- [The Ultimate WordPress Speed Optimization Guide](https://wpjohnny.com/ultimate-wordpress-speed-optimization-guide/) - 130+ performance tips
- [Core Web Vitals Score Optimization Tips](https://wpjohnny.com/core-web-vitals-score-optimization-tips/)
- [Thoughts on Google Web Vitals](https://wpjohnny.com/thoughts-google-web-vitals/)
- [Why PageSpeed, Pingdom, GTmetrix Scores Don't Matter](https://wpjohnny.com/google-pagespeed-pingdom-and-gtmetrix-scores-dont-matter/)
- [Which is the Fastest WordPress Theme?](https://wpjohnny.com/fastest-wordpress-theme/)
- [Fastest Lightweight WordPress Themes Review](https://wpjohnny.com/fastest-lightweight-wordpress-themes-review/)
- [Best WordPress Themes](https://wpjohnny.com/best-wordpress-themes/)
- [Best WordPress Plugins](https://wpjohnny.com/best-wordpress-plugins/)
- [Best WordPress Cache Plugins Review](https://wpjohnny.com/best-wordpress-cache-plugins-review/)
- [Best WordPress Cache Plugins 2021](https://wpjohnny.com/best-wordpress-cache-plugins-2021/)
- [WP Performance Cache Plugin Review](https://wpjohnny.com/wp-performance-cache-plugin-review/)
- [Swift Performance Cache Plugin Unofficial Guide](https://wpjohnny.com/swift-performance-wordpress-cache-plugin-unofficial-guide/)
- [LiteSpeed Cache Plugin Unofficial Guide](https://wpjohnny.com/litespeed-cache-wordpress-plugin-unofficial-guide/)
- [Why You Shouldn't Combine CSS/JS](https://wpjohnny.com/why-you-shouldnt-combine-css-js-performance-reasons/)
- [Why You Should Never Use Lazy Load](https://wpjohnny.com/never-use-lazy-load/)
- [Best CDN Providers for WordPress](https://wpjohnny.com/best-cdn-providers-for-wordpress-speed-review/)
- [Clean Up wp_options Table Autoloaded Data](https://wpjohnny.com/clean-up-wp_options-table-autoloaded-data/)
- [Speeding Up WordPress Backend](https://wpjohnny.com/speed-up-wordpress-backend/)
- [Why Shared Hosting Sucks](https://wpjohnny.com/why-shared-hosting-sucks/)
- [Why Are Managed VPS Servers So Slow?](https://wpjohnny.com/why-are-managed-vps-servers-so-slow/)
- [NGINX vs OpenLiteSpeed Speed Comparison](https://wpjohnny.com/nginx-vs-openlitespeed-speed-comparison/)
- [Replace Bloated Pagebuilders with Gutenberg Blocks](https://wpjohnny.com/replace-bloated-pagebuilders-with-gutenberg-blocks/)
- [Best Gutenberg Pagebuilders for WordPress](https://wpjohnny.com/best-gutenberg-pagebuilders-wordpress/)
- [Monster Guide to WordPress Image Optimization](https://wpjohnny.com/monster-guide-wordpress-image-optimization/)
- [ShortPixel is the Best Image Compression Plugin](https://wpjohnny.com/shortpixel-is-the-best-image-compression-plugin-for-wordpress/)
- [How to Optimize/Compress Your Website Images](https://wpjohnny.com/how-to-optimize-compress-your-website-images/)
- [WPML Speed Optimization Tips](https://wpjohnny.com/wpml-speed-optimization-tips/)
- [WordPress Security Tips Without Slowing Performance](https://wpjohnny.com/easy-wordpress-security-tips-without-slowing-performance/)
- [WordPress Hosting Review](https://wpjohnny.com/best-wordpress-hosting-reviews/)
