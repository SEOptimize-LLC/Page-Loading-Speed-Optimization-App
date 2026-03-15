# PageSpeed Insights API v5 - Comprehensive Knowledge Base

## Table of Contents

1. [API Overview](#1-api-overview)
2. [Endpoint & Authentication](#2-endpoint--authentication)
3. [Request Parameters](#3-request-parameters)
4. [Rate Limits & Quotas](#4-rate-limits--quotas)
5. [Response Structure Overview](#5-response-structure-overview)
6. [Field Data (CrUX) - loadingExperience](#6-field-data-crux---loadingexperience)
7. [Lab Data - lighthouseResult](#7-lab-data---lighthouseresult)
8. [Performance Metrics & Weights](#8-performance-metrics--weights)
9. [Audit Object Structure](#9-audit-object-structure)
10. [Opportunity Audits (Resource-Level Issues)](#10-opportunity-audits-resource-level-issues)
11. [Diagnostic Audits](#11-diagnostic-audits)
12. [Element-Level Diagnostic Audits](#12-element-level-diagnostic-audits)
13. [Screenshot & Visual Data](#13-screenshot--visual-data)
14. [Network Requests & Resource Data](#14-network-requests--resource-data)
15. [Third-Party Analysis](#15-third-party-analysis)
16. [CMS & Technology Stack Detection](#16-cms--technology-stack-detection)
17. [Category Scores](#17-category-scores)
18. [Complete Audit Key Reference](#18-complete-audit-key-reference)
19. [Parsing Patterns for Agent Implementation](#19-parsing-patterns-for-agent-implementation)
20. [Field Data vs Lab Data](#20-field-data-vs-lab-data)
21. [Important Notes & Limitations](#21-important-notes--limitations)

---

## 1. API Overview

Google PageSpeed Insights (PSI) analyzes the content of a web page and generates suggestions to make that page faster. It provides both **field data** (real-world Chrome User Experience Report data from the trailing 28 days) and **lab data** (Lighthouse simulated analysis).

PSI uses Lighthouse under the hood, simulating page loads on:
- **Mobile**: Mid-tier device (Moto G Power) with mobile network throttling (simulated slow 4G)
- **Desktop**: Emulated desktop with wired connection

The API returns a comprehensive JSON response containing performance scores, detailed audit results, resource-level diagnostics, screenshots, and CMS-specific recommendations.

---

## 2. Endpoint & Authentication

### Base Endpoint

```
GET https://www.googleapis.com/pagespeedonline/v5/runPagespeed
```

### API Key

- **Optional** for basic usage but **recommended** for production/frequent use
- Create at: https://console.cloud.google.com/apis/credentials
- Enable "PageSpeed Insights API" in Google Cloud Console
- The API key is safe for embedding in URLs; it does not need encoding
- Append via query parameter: `key=YOUR_API_KEY`

### Example Requests

**Minimal request (no key):**
```bash
curl "https://www.googleapis.com/pagespeedonline/v5/runPagespeed?url=https://example.com"
```

**With API key and mobile strategy:**
```bash
curl "https://www.googleapis.com/pagespeedonline/v5/runPagespeed?url=https://example.com&strategy=mobile&key=YOUR_API_KEY"
```

**Multiple categories:**
```bash
curl "https://www.googleapis.com/pagespeedonline/v5/runPagespeed?url=https://example.com&strategy=mobile&category=performance&category=accessibility&category=seo&category=best-practices&key=YOUR_API_KEY"
```

---

## 3. Request Parameters

### Required Parameters

| Parameter | Type   | Description                        |
|-----------|--------|------------------------------------|
| `url`     | string | The URL to fetch and analyze       |

### Optional Parameters

| Parameter      | Type   | Description                                                    | Default     |
|----------------|--------|----------------------------------------------------------------|-------------|
| `strategy`     | string | Analysis strategy: `mobile` or `desktop`                       | `desktop`   |
| `category`     | string | Lighthouse category to run (can be repeated for multiple)      | `performance` |
| `locale`       | string | Locale for formatted results (e.g., `en-US`, `fr-FR`)         | `en`        |
| `utm_campaign` | string | Campaign name for analytics                                    | -           |
| `utm_source`   | string | Campaign source for analytics                                  | -           |
| `key`          | string | Google API key                                                 | -           |

### Category Values

- `performance` - Page speed and loading metrics
- `accessibility` - WCAG compliance checks
- `best-practices` - Modern web development standards
- `seo` - Search engine optimization checks

**Important**: To request multiple categories, repeat the `category` parameter:
```
?category=performance&category=seo&category=accessibility&category=best-practices
```

If no category is specified, only `performance` is returned.

---

## 4. Rate Limits & Quotas

| Condition         | Limit                           |
|-------------------|---------------------------------|
| Without API key   | Unspecified (subject to throttling) |
| With API key      | **25,000 queries per day**      |
| Per-minute limit  | **240 requests per minute** (400 per 100 seconds) |
| Cost              | **Free** (no charges)           |

**Best Practices:**
- Always use an API key for automated/production use
- Implement exponential backoff for rate limit errors (HTTP 429)
- Cache results; pages don't change minute-to-minute
- Stagger requests when testing multiple URLs

---

## 5. Response Structure Overview

The API returns a JSON object approximately 300-800KB in size (varies by page complexity and categories requested).

### Top-Level Response Structure

```json
{
  "captchaResult": "CAPTCHA_NOT_NEEDED",
  "kind": "pagespeedonline#result",
  "id": "https://example.com/",
  "loadingExperience": { },
  "originLoadingExperience": { },
  "lighthouseResult": { },
  "analysisUTCTimestamp": "2025-01-15T10:30:00.000Z",
  "version": {
    "major": 12,
    "minor": 0
  }
}
```

| Field                      | Description                                              |
|----------------------------|----------------------------------------------------------|
| `captchaResult`            | CAPTCHA verification status (typically `CAPTCHA_NOT_NEEDED`) |
| `kind`                     | Result type identifier: `pagespeedonline#result`         |
| `id`                       | The canonicalized/final URL after redirects               |
| `loadingExperience`        | **Field data** (CrUX) for the specific URL               |
| `originLoadingExperience`  | **Field data** (CrUX) aggregated for the entire origin   |
| `lighthouseResult`         | **Lab data** - comprehensive Lighthouse audit results     |
| `analysisUTCTimestamp`     | UTC timestamp when the analysis was performed             |
| `version`                  | PSI API version numbers                                   |

---

## 6. Field Data (CrUX) - loadingExperience

Field data comes from the Chrome User Experience Report (CrUX) and represents real-world user metrics collected over the trailing 28 days from Chrome users who have opted in.

> **Important**: Google has announced plans to discontinue including CrUX data in the PSI API response. Users should migrate to the dedicated CrUX API (https://developers.google.com/web/tools/chrome-user-experience-report/api/reference) or CrUX History API for field data.

### loadingExperience Structure

```json
{
  "loadingExperience": {
    "id": "https://example.com/",
    "metrics": {
      "CUMULATIVE_LAYOUT_SHIFT_SCORE": {
        "percentile": 1,
        "distributions": [
          { "min": 0, "max": 10, "proportion": 0.95 },
          { "min": 10, "max": 25, "proportion": 0.03 },
          { "min": 25, "proportion": 0.02 }
        ],
        "category": "FAST"
      },
      "EXPERIMENTAL_TIME_TO_FIRST_BYTE": {
        "percentile": 400,
        "distributions": [
          { "min": 0, "max": 800, "proportion": 0.85 },
          { "min": 800, "max": 1800, "proportion": 0.10 },
          { "min": 1800, "proportion": 0.05 }
        ],
        "category": "FAST"
      },
      "FIRST_CONTENTFUL_PAINT_MS": {
        "percentile": 1200,
        "distributions": [
          { "min": 0, "max": 1800, "proportion": 0.80 },
          { "min": 1800, "max": 3000, "proportion": 0.15 },
          { "min": 3000, "proportion": 0.05 }
        ],
        "category": "FAST"
      },
      "INTERACTION_TO_NEXT_PAINT": {
        "percentile": 150,
        "distributions": [
          { "min": 0, "max": 200, "proportion": 0.85 },
          { "min": 200, "max": 500, "proportion": 0.10 },
          { "min": 500, "proportion": 0.05 }
        ],
        "category": "FAST"
      },
      "LARGEST_CONTENTFUL_PAINT_MS": {
        "percentile": 2000,
        "distributions": [
          { "min": 0, "max": 2500, "proportion": 0.75 },
          { "min": 2500, "max": 4000, "proportion": 0.15 },
          { "min": 4000, "proportion": 0.10 }
        ],
        "category": "FAST"
      }
    },
    "overall_category": "FAST",
    "initial_url": "https://example.com/"
  }
}
```

### CrUX Metric Keys

| CrUX Key                          | Web Vital  | Unit          |
|-----------------------------------|------------|---------------|
| `CUMULATIVE_LAYOUT_SHIFT_SCORE`   | CLS        | Score (x100)  |
| `EXPERIMENTAL_TIME_TO_FIRST_BYTE` | TTFB       | Milliseconds  |
| `FIRST_CONTENTFUL_PAINT_MS`       | FCP        | Milliseconds  |
| `INTERACTION_TO_NEXT_PAINT`       | INP        | Milliseconds  |
| `LARGEST_CONTENTFUL_PAINT_MS`     | LCP        | Milliseconds  |

### Category Values

Each metric has a `category` field with one of:
- `FAST` - Good performance (green)
- `AVERAGE` - Needs improvement (orange)
- `SLOW` - Poor performance (red)
- `NONE` - Insufficient data

The `overall_category` reflects whether the page passes Core Web Vitals assessment (LCP, CLS, and INP all at 75th percentile must be "Good").

### Parsing Field Data

```python
# Python
field_data = response["loadingExperience"]["metrics"]

lcp_ms = field_data["LARGEST_CONTENTFUL_PAINT_MS"]["percentile"]
lcp_category = field_data["LARGEST_CONTENTFUL_PAINT_MS"]["category"]
cls_raw = field_data["CUMULATIVE_LAYOUT_SHIFT_SCORE"]["percentile"]
cls_value = cls_raw / 100  # CLS needs division by 100
inp_ms = field_data["INTERACTION_TO_NEXT_PAINT"]["percentile"]
fcp_ms = field_data["FIRST_CONTENTFUL_PAINT_MS"]["percentile"]

overall = response["loadingExperience"]["overall_category"]
passes_cwv = overall == "FAST"
```

```javascript
// JavaScript
const fieldData = response.loadingExperience.metrics;

const lcpMs = fieldData.LARGEST_CONTENTFUL_PAINT_MS.percentile;
const lcpCategory = fieldData.LARGEST_CONTENTFUL_PAINT_MS.category;
const clsRaw = fieldData.CUMULATIVE_LAYOUT_SHIFT_SCORE.percentile;
const clsValue = clsRaw / 100;
const inpMs = fieldData.INTERACTION_TO_NEXT_PAINT.percentile;
const fcpMs = fieldData.FIRST_CONTENTFUL_PAINT_MS.percentile;

const overall = response.loadingExperience.overall_category;
const passesCwv = overall === "FAST";
```

### originLoadingExperience

Same structure as `loadingExperience`, but aggregated across the entire origin domain (all pages), not just the specific URL. Useful when a specific URL doesn't have enough CrUX traffic data.

---

## 7. Lab Data - lighthouseResult

The `lighthouseResult` object is the largest section and contains all Lighthouse audit results (lab data).

### lighthouseResult Top-Level Structure

```json
{
  "lighthouseResult": {
    "requestedUrl": "https://example.com/",
    "finalUrl": "https://example.com/",
    "mainDocumentUrl": "https://example.com/",
    "finalDisplayedUrl": "https://example.com/",
    "lighthouseVersion": "12.2.1",
    "userAgent": "Mozilla/5.0 (Linux; Android 11; moto g power (2022)) ...",
    "fetchTime": "2025-01-15T10:30:00.000Z",
    "environment": {
      "networkUserAgent": "Mozilla/5.0 ...",
      "hostUserAgent": "Mozilla/5.0 ...",
      "benchmarkIndex": 1500,
      "credits": {}
    },
    "runWarnings": [],
    "configSettings": {
      "emulatedFormFactor": "mobile",
      "formFactor": "mobile",
      "locale": "en-US",
      "onlyCategories": ["performance"],
      "channel": "lr"
    },
    "audits": { },
    "categories": { },
    "categoryGroups": { },
    "stackPacks": [ ],
    "entities": [ ],
    "fullPageScreenshot": { },
    "timing": {
      "total": 12500
    },
    "i18n": { },
    "runtimeError": null
  }
}
```

### Key Properties

| Property           | Description                                                       |
|--------------------|-------------------------------------------------------------------|
| `requestedUrl`     | The URL originally requested                                      |
| `finalUrl`         | The URL after all redirects resolved                              |
| `lighthouseVersion`| Version of Lighthouse used (e.g., `12.2.1`)                      |
| `userAgent`        | Browser user agent used for the test                              |
| `fetchTime`        | ISO timestamp of when the test was run                            |
| `environment`      | Test environment details including benchmark index                |
| `configSettings`   | Settings used for the run (form factor, locale, categories)       |
| `audits`           | **Map of all audit results** (the main data)                      |
| `categories`       | Category-level scores (performance, accessibility, etc.)          |
| `categoryGroups`   | Metadata about audit groupings                                    |
| `stackPacks`       | CMS/framework-specific recommendations                           |
| `entities`         | Third-party entity classification                                 |
| `fullPageScreenshot`| Full page screenshot with element position data                   |
| `timing`           | Total analysis duration in milliseconds                           |
| `runtimeError`     | Error information if the analysis failed                          |

---

## 8. Performance Metrics & Weights

### Lighthouse 10+ Scoring Weights

| Metric                    | Audit Key                     | Weight | Unit         |
|---------------------------|-------------------------------|--------|--------------|
| First Contentful Paint    | `first-contentful-paint`      | 10%    | Seconds      |
| Speed Index               | `speed-index`                 | 10%    | Seconds      |
| Largest Contentful Paint  | `largest-contentful-paint`    | 25%    | Seconds      |
| Total Blocking Time       | `total-blocking-time`         | 30%    | Milliseconds |
| Cumulative Layout Shift   | `cumulative-layout-shift`     | 25%    | Unitless     |

### Core Web Vitals Thresholds

| Metric | Good         | Needs Improvement | Poor         |
|--------|--------------|-------------------|--------------|
| FCP    | 0 - 1.8s     | 1.8s - 3.0s       | > 3.0s       |
| LCP    | 0 - 2.5s     | 2.5s - 4.0s       | > 4.0s       |
| CLS    | 0 - 0.1      | 0.1 - 0.25        | > 0.25       |
| INP    | 0 - 200ms    | 200ms - 500ms     | > 500ms      |
| TTFB   | 0 - 800ms    | 800ms - 1800ms    | > 1800ms     |
| TBT    | 0 - 200ms    | 200ms - 600ms     | > 600ms      |
| SI     | 0 - 3.4s     | 3.4s - 5.8s       | > 5.8s       |

### Score Color Coding

- **0-49** (Red): Poor
- **50-89** (Orange): Needs Improvement
- **90-100** (Green): Good

### Accessing Metrics from the Consolidated Metrics Audit

```python
# All metrics in one place
metrics = response["lighthouseResult"]["audits"]["metrics"]["details"]["items"][0]

fcp_ms = metrics["firstContentfulPaint"]       # in milliseconds
lcp_ms = metrics["largestContentfulPaint"]      # in milliseconds
si_ms = metrics["speedIndex"]                   # in milliseconds
tbt_ms = metrics["totalBlockingTime"]           # in milliseconds
cls = metrics["cumulativeLayoutShift"]           # unitless decimal
tti_ms = metrics["interactive"]                  # in milliseconds (Time to Interactive)
```

---

## 9. Audit Object Structure

Every audit in `lighthouseResult.audits` follows a consistent structure:

```json
{
  "audit-key-name": {
    "id": "audit-key-name",
    "title": "Human-readable title",
    "description": "Detailed description with [link](url) to documentation",
    "score": 0.85,
    "scoreDisplayMode": "numeric",
    "displayValue": "2.5 s",
    "numericValue": 2500,
    "numericUnit": "millisecond",
    "details": {
      "type": "opportunity",
      "headings": [ ],
      "items": [ ],
      "overallSavingsMs": 1200,
      "overallSavingsBytes": 45000,
      "sortedBy": ["wastedBytes"],
      "debugData": { }
    },
    "warnings": []
  }
}
```

### Key Audit Properties

| Property           | Type              | Description                                              |
|--------------------|-------------------|----------------------------------------------------------|
| `id`               | string            | Unique audit identifier (same as the key)                |
| `title`            | string            | Human-readable audit name                                |
| `description`      | string            | Explanation with markdown links to documentation         |
| `score`            | number (0-1) or null | Normalized score; null for informational audits        |
| `scoreDisplayMode` | string            | `numeric`, `binary`, `manual`, `informative`, `notApplicable`, `error` |
| `displayValue`     | string            | Formatted value for display (e.g., "2.5 s", "350 KiB")  |
| `numericValue`     | number            | Raw numeric value                                        |
| `numericUnit`      | string            | Unit: `millisecond`, `byte`, `unitless`, `element`       |
| `details`          | object            | Detailed findings (structure varies by detail type)      |
| `warnings`         | array             | Any warnings encountered during the audit                |

### Audit Detail Types

The `details.type` field indicates the structure:

| Type               | Description                                               |
|--------------------|-----------------------------------------------------------|
| `opportunity`      | Resource optimization suggestions with savings estimates  |
| `table`            | Tabular data (diagnostics, informational)                 |
| `filmstrip`        | Series of screenshots during page load                    |
| `screenshot`       | Single screenshot                                         |
| `full-page-screenshot` | Full page screenshot with element node positions      |
| `debugdata`        | Debug information                                         |
| `treemap-data`     | JavaScript treemap coverage data                          |
| `criticalrequestchain` | Critical request chain waterfall                     |
| `list`             | List of items                                             |

---

## 10. Opportunity Audits (Resource-Level Issues)

Opportunity audits identify specific resources (files, images, scripts) that can be optimized, with estimated savings in bytes and/or milliseconds.

### Common Opportunity Audit Keys

| Audit Key                       | Issue                                      |
|---------------------------------|--------------------------------------------|
| `render-blocking-resources`     | JS/CSS blocking first paint                |
| `unused-javascript`             | JavaScript code that is loaded but not used |
| `unused-css-rules`              | CSS rules that are loaded but not applied  |
| `offscreen-images`              | Images not visible in initial viewport     |
| `modern-image-formats`          | Images not using WebP/AVIF                 |
| `uses-responsive-images`        | Images larger than their display size      |
| `efficiently-encode-images`     | Images that can be further compressed      |
| `uses-text-compression`         | Resources not using gzip/brotli            |
| `uses-long-cache-ttl`           | Resources with short cache TTL             |
| `unminified-javascript`         | JS files not minified                      |
| `unminified-css`                | CSS files not minified                     |
| `redirects`                     | Multiple page redirects in chain           |
| `server-response-time`          | Slow TTFB (> 600ms)                        |
| `efficient-animated-content`    | Large GIFs that should be video            |
| `duplicated-javascript`         | Same JS modules shipped multiple times     |
| `legacy-javascript`             | Polyfills/transforms not needed by modern browsers |
| `uses-rel-preload`              | Key requests that could be preloaded       |
| `uses-rel-preconnect`           | Origins that could be preconnected         |
| `preload-lcp-image`             | LCP image could be preloaded              |

### Opportunity Audit Detail Structure

```json
{
  "render-blocking-resources": {
    "id": "render-blocking-resources",
    "title": "Eliminate render-blocking resources",
    "score": 0,
    "displayValue": "Potential savings of 1,200 ms",
    "numericValue": 1200,
    "numericUnit": "millisecond",
    "details": {
      "type": "opportunity",
      "headings": [
        { "key": "url", "valueType": "url", "label": "URL" },
        { "key": "totalBytes", "valueType": "bytes", "label": "Transfer Size" },
        { "key": "wastedMs", "valueType": "timespanMs", "label": "Potential Savings" }
      ],
      "items": [
        {
          "url": "https://example.com/css/styles.css",
          "totalBytes": 85000,
          "wastedMs": 750
        },
        {
          "url": "https://example.com/js/main.js",
          "totalBytes": 120000,
          "wastedMs": 450
        }
      ],
      "overallSavingsMs": 1200,
      "overallSavingsBytes": 205000
    }
  }
}
```

### Parsing Opportunity Audits

```python
# Python - Extract all opportunity issues with resource URLs
audits = response["lighthouseResult"]["audits"]

opportunity_keys = [
    "render-blocking-resources",
    "unused-javascript",
    "unused-css-rules",
    "offscreen-images",
    "modern-image-formats",
    "uses-responsive-images",
    "efficiently-encode-images",
    "uses-text-compression",
    "uses-long-cache-ttl",
    "unminified-javascript",
    "unminified-css",
    "redirects",
    "server-response-time",
    "efficient-animated-content",
    "duplicated-javascript",
    "legacy-javascript",
    "preload-lcp-image",
]

for key in opportunity_keys:
    audit = audits.get(key)
    if audit and audit.get("score") is not None and audit["score"] < 1:
        details = audit.get("details", {})
        items = details.get("items", [])
        savings_ms = details.get("overallSavingsMs", 0)
        savings_bytes = details.get("overallSavingsBytes", 0)

        print(f"\n--- {audit['title']} ---")
        print(f"Score: {audit['score']}")
        print(f"Potential savings: {savings_ms}ms, {savings_bytes} bytes")

        for item in items:
            url = item.get("url", "N/A")
            wasted_bytes = item.get("wastedBytes", item.get("totalBytes", 0))
            wasted_ms = item.get("wastedMs", 0)
            print(f"  Resource: {url}")
            print(f"  Wasted: {wasted_bytes} bytes, {wasted_ms}ms")
```

### Resource Item Properties by Audit Type

**render-blocking-resources items:**
```json
{ "url": "...", "totalBytes": 85000, "wastedMs": 750 }
```

**unused-javascript items:**
```json
{ "url": "...", "totalBytes": 200000, "wastedBytes": 150000, "wastedPercent": 75 }
```

**unused-css-rules items:**
```json
{ "url": "...", "totalBytes": 45000, "wastedBytes": 30000, "wastedPercent": 66.7 }
```

**offscreen-images items:**
```json
{
  "url": "https://example.com/images/hero.jpg",
  "requestStartTime": 1234.5,
  "totalBytes": 250000,
  "wastedBytes": 250000,
  "wastedPercent": 100,
  "node": {
    "type": "node",
    "lhId": "1-2-IMG",
    "path": "1,HTML,1,BODY,2,DIV,0,IMG",
    "selector": "body > div.content > img.hero",
    "boundingRect": { "top": 2000, "bottom": 2400, "left": 0, "right": 400, "width": 400, "height": 400 },
    "snippet": "<img src=\"/images/hero.jpg\" class=\"hero\" width=\"400\" height=\"400\">",
    "nodeLabel": "hero image"
  }
}
```

**modern-image-formats items:**
```json
{
  "url": "https://example.com/images/photo.png",
  "totalBytes": 500000,
  "wastedBytes": 350000,
  "wastedWebpBytes": 200000,
  "fromProtocol": true,
  "isCrossOrigin": false,
  "node": { }
}
```

**uses-long-cache-ttl items:**
```json
{
  "url": "https://fonts.googleapis.com/css?family=Roboto",
  "cacheLifetimeMs": 0,
  "cacheHitProbability": 0,
  "totalBytes": 2157,
  "wastedBytes": 2157,
  "debugData": {
    "type": "debugdata",
    "max-age": 0,
    "public": true
  }
}
```

**uses-text-compression items:**
```json
{ "url": "...", "totalBytes": 100000, "wastedBytes": 70000 }
```

---

## 11. Diagnostic Audits

Diagnostic audits provide additional performance information. They have a weight of 0 and do NOT directly affect the performance score, but provide actionable guidance.

### Common Diagnostic Audit Keys

| Audit Key                     | What It Measures                                        |
|-------------------------------|---------------------------------------------------------|
| `total-byte-weight`           | Total page weight in bytes                              |
| `dom-size`                    | Number of DOM elements                                  |
| `bootup-time`                 | JavaScript execution time per script                    |
| `mainthread-work-breakdown`   | Main thread work categorized by type                    |
| `third-party-summary`         | Third-party script impact                               |
| `third-party-facades`         | Third-party resources that could be lazy loaded         |
| `font-display`                | Font loading strategy issues                            |
| `critical-request-chains`     | Critical request chain depth                            |
| `user-timings`                | Custom performance marks/measures                       |
| `long-tasks`                  | Tasks blocking main thread > 50ms                       |
| `non-composited-animations`   | Animations not composited                               |
| `unsized-images`              | Images without explicit width/height                    |
| `viewport`                    | Viewport meta tag configuration                         |
| `no-document-write`           | Use of document.write()                                 |
| `uses-passive-event-listeners`| Non-passive event listeners                             |
| `uses-http2`                  | Resources not served via HTTP/2                         |
| `prioritize-lcp-image`        | LCP image discovery optimization                        |
| `network-rtt`                 | Network round trip times                                |
| `network-server-latency`      | Server backend latencies                                |

### Diagnostic Audit Detail Structure

**dom-size:**
```json
{
  "dom-size": {
    "id": "dom-size",
    "title": "Avoid an excessive DOM size",
    "score": 0.5,
    "displayValue": "1,500 elements",
    "numericValue": 1500,
    "numericUnit": "element",
    "details": {
      "type": "table",
      "headings": [
        { "key": "statistic", "valueType": "text", "label": "Statistic" },
        { "key": "node", "valueType": "node", "label": "Element" },
        { "key": "value", "valueType": "numeric", "label": "Value" }
      ],
      "items": [
        { "statistic": "Total DOM Elements", "value": 1500 },
        {
          "statistic": "Maximum DOM Depth",
          "value": 18,
          "node": {
            "type": "node",
            "selector": "body > div > section > div > ...",
            "snippet": "<div class=\"deeply-nested\">",
            "nodeLabel": "deeply-nested"
          }
        },
        {
          "statistic": "Maximum Child Elements",
          "value": 65,
          "node": {
            "type": "node",
            "selector": "body > div.container",
            "snippet": "<div class=\"container\">",
            "nodeLabel": "container"
          }
        }
      ]
    }
  }
}
```

**bootup-time items:**
```json
{
  "url": "https://example.com/js/bundle.js",
  "total": 1250.5,
  "scripting": 800.2,
  "scriptParseCompile": 450.3
}
```

**mainthread-work-breakdown items:**
```json
[
  { "group": "scriptEvaluation", "groupLabel": "Script Evaluation", "duration": 2500 },
  { "group": "styleLayout", "groupLabel": "Style & Layout", "duration": 800 },
  { "group": "paintCompositeRender", "groupLabel": "Rendering", "duration": 400 },
  { "group": "scriptParseCompile", "groupLabel": "Script Parsing & Compilation", "duration": 350 },
  { "group": "parseHTML", "groupLabel": "Parse HTML & CSS", "duration": 200 },
  { "group": "garbageCollection", "groupLabel": "Garbage Collection", "duration": 100 },
  { "group": "other", "groupLabel": "Other", "duration": 150 }
]
```

### Consolidated Diagnostics Summary

The `diagnostics` audit provides an aggregate summary:

```python
diag = response["lighthouseResult"]["audits"]["diagnostics"]["details"]["items"][0]

num_requests = diag["numRequests"]          # Total network requests
total_bytes = diag["totalByteWeight"]       # Total page weight in bytes
num_scripts = diag["numScripts"]            # Number of script resources
num_stylesheets = diag["numStylesheets"]    # Number of stylesheets
num_fonts = diag["numFonts"]                # Number of font resources
num_tasks = diag["numTasks"]                # Total main thread tasks
num_tasks_over_50ms = diag["numTasksOver50ms"]  # Long tasks
total_task_time = diag["totalTaskTime"]     # Total main thread task time (ms)
max_rtt = diag["maxRtt"]                    # Max round trip time
max_server_latency = diag["maxServerLatency"]  # Max server latency
throughput = diag["throughput"]             # Network throughput (bytes/s)
```

---

## 12. Element-Level Diagnostic Audits

These audits identify specific DOM elements causing performance issues.

### largest-contentful-paint-element

Identifies the DOM element that is the LCP element.

```json
{
  "largest-contentful-paint-element": {
    "id": "largest-contentful-paint-element",
    "title": "Largest Contentful Paint element",
    "score": null,
    "scoreDisplayMode": "informative",
    "displayValue": "4,120 ms",
    "details": {
      "type": "table",
      "headings": [
        { "key": "node", "valueType": "node", "label": "Element" },
        { "key": "phase", "valueType": "text", "label": "Phase" },
        { "key": "timing", "valueType": "ms", "label": "Timing" }
      ],
      "items": [
        {
          "node": {
            "type": "node",
            "lhId": "page-0-IMG",
            "path": "1,HTML,1,BODY,0,DIV,3,SECTION,0,IMG",
            "selector": "body > div > section > img.hero-image",
            "boundingRect": {
              "top": 100,
              "bottom": 500,
              "left": 0,
              "right": 1200,
              "width": 1200,
              "height": 400
            },
            "snippet": "<img src=\"/images/hero.webp\" class=\"hero-image\" alt=\"Hero\">",
            "nodeLabel": "Hero"
          }
        }
      ]
    }
  }
}
```

### layout-shift-elements (CLS Culprits)

Identifies elements that shifted, contributing to CLS.

```json
{
  "layout-shift-elements": {
    "id": "layout-shift-elements",
    "title": "Avoid large layout shifts",
    "score": null,
    "scoreDisplayMode": "informative",
    "details": {
      "type": "table",
      "items": [
        {
          "node": {
            "type": "node",
            "lhId": "page-12-DIV",
            "path": "1,HTML,1,BODY,2,DIV,1,DIV",
            "selector": "body > div.content > div.ad-container",
            "snippet": "<div class=\"ad-container\" style=\"...\">",
            "nodeLabel": "ad-container",
            "boundingRect": { "top": 500, "left": 0, "width": 300, "height": 250 }
          },
          "score": 0.045
        }
      ]
    }
  }
}
```

> **Note**: In Lighthouse 13+, `layout-shift-elements` is being replaced by `cls-culprits-insight` for clearer identification of layout shift causes.

### Node Object Structure

When audits reference DOM elements, they use this node structure:

```json
{
  "type": "node",
  "lhId": "page-0-IMG",
  "path": "1,HTML,1,BODY,0,DIV,3,SECTION,0,IMG",
  "selector": "body > div > section > img.hero-image",
  "boundingRect": {
    "top": 100,
    "bottom": 500,
    "left": 0,
    "right": 1200,
    "width": 1200,
    "height": 400
  },
  "snippet": "<img src=\"/images/hero.webp\" class=\"hero-image\">",
  "nodeLabel": "Hero Image"
}
```

| Property       | Description                                                |
|----------------|------------------------------------------------------------|
| `type`         | Always `"node"`                                            |
| `lhId`         | Lighthouse internal element ID                             |
| `path`         | Numeric path through the DOM tree                          |
| `selector`     | CSS selector to identify the element                       |
| `boundingRect` | Position and dimensions on the page (top, bottom, left, right, width, height) |
| `snippet`      | HTML snippet showing the element's tag and attributes      |
| `nodeLabel`    | Human-friendly text label for the element                  |

---

## 13. Screenshot & Visual Data

### Final Screenshot

The final screenshot shows the page as it appears after loading.

**Path:** `lighthouseResult.audits["final-screenshot"]`

```json
{
  "final-screenshot": {
    "id": "final-screenshot",
    "title": "Final Screenshot",
    "score": null,
    "scoreDisplayMode": "informative",
    "details": {
      "type": "screenshot",
      "timing": 5000,
      "timestamp": 1705312200000,
      "data": "data:image/jpeg;base64,/9j/4AAQSkZJRgABAQAAAQABAAD..."
    }
  }
}
```

### Extracting the Final Screenshot

```python
# Python
import base64

screenshot_data = response["lighthouseResult"]["audits"]["final-screenshot"]["details"]["data"]

# Remove the data URI prefix
base64_str = screenshot_data.replace("data:image/jpeg;base64,", "")

# Decode and save
image_bytes = base64.b64decode(base64_str)
with open("screenshot.jpg", "wb") as f:
    f.write(image_bytes)
```

```javascript
// JavaScript - Display in HTML
const screenshotData = response.lighthouseResult.audits["final-screenshot"].details.data;
const img = document.createElement("img");
img.src = screenshotData; // data URI can be used directly as src
document.body.appendChild(img);
```

### Screenshot Thumbnails (Filmstrip)

Shows the page loading progression as a series of thumbnails.

**Path:** `lighthouseResult.audits["screenshot-thumbnails"]`

```json
{
  "screenshot-thumbnails": {
    "id": "screenshot-thumbnails",
    "title": "Screenshot Thumbnails",
    "score": null,
    "scoreDisplayMode": "informative",
    "details": {
      "type": "filmstrip",
      "scale": 1,
      "items": [
        {
          "timing": 300,
          "timestamp": 1705312195300,
          "data": "data:image/jpeg;base64,/9j/4AAQSkZ..."
        },
        {
          "timing": 600,
          "timestamp": 1705312195600,
          "data": "data:image/jpeg;base64,/9j/4AAQSkZ..."
        },
        {
          "timing": 900,
          "timestamp": 1705312195900,
          "data": "data:image/jpeg;base64,/9j/4AAQSkZ..."
        }
      ]
    }
  }
}
```

Each filmstrip item contains:
- `timing`: Milliseconds from navigation start
- `timestamp`: Absolute timestamp
- `data`: Base64-encoded JPEG image as data URI

### Full Page Screenshot

The full-page screenshot includes the entire scrollable page and element position mapping.

**Path:** `lighthouseResult.fullPageScreenshot`

```json
{
  "fullPageScreenshot": {
    "screenshot": {
      "data": "data:image/webp;base64,UklGR...",
      "width": 412,
      "height": 8500
    },
    "nodes": {
      "page-0-IMG": {
        "top": 100,
        "bottom": 500,
        "left": 0,
        "right": 412,
        "width": 412,
        "height": 400
      },
      "page-1-DIV": {
        "top": 500,
        "bottom": 750,
        "left": 10,
        "right": 402,
        "width": 392,
        "height": 250
      }
    }
  }
}
```

The `nodes` map connects element `lhId` values (from audit results) to their visual positions on the full-page screenshot, enabling visual overlay of problem elements.

### Extracting Element Screenshots from Full Page

```python
# Python - Crop a specific element from the full page screenshot
from PIL import Image
import base64
import io

fps = response["lighthouseResult"]["fullPageScreenshot"]
screenshot_data = fps["screenshot"]["data"].replace("data:image/webp;base64,", "")
screenshot_bytes = base64.b64decode(screenshot_data)
full_page = Image.open(io.BytesIO(screenshot_bytes))

# Get LCP element position
lcp_audit = response["lighthouseResult"]["audits"]["largest-contentful-paint-element"]
lcp_items = lcp_audit.get("details", {}).get("items", [])
if lcp_items:
    lh_id = lcp_items[0].get("node", {}).get("lhId")
    if lh_id and lh_id in fps["nodes"]:
        rect = fps["nodes"][lh_id]
        # Crop the element from the full page screenshot
        element_img = full_page.crop((rect["left"], rect["top"], rect["right"], rect["bottom"]))
        element_img.save("lcp_element.png")
```

---

## 14. Network Requests & Resource Data

### network-requests Audit

Lists every network request made during page load.

**Path:** `lighthouseResult.audits["network-requests"]`

```json
{
  "network-requests": {
    "id": "network-requests",
    "title": "Network Requests",
    "score": null,
    "details": {
      "type": "table",
      "headings": [
        { "key": "url", "valueType": "url", "label": "URL" },
        { "key": "protocol", "valueType": "text", "label": "Protocol" },
        { "key": "startTime", "valueType": "ms", "label": "Start Time" },
        { "key": "endTime", "valueType": "ms", "label": "End Time" },
        { "key": "transferSize", "valueType": "bytes", "label": "Transfer Size" },
        { "key": "resourceSize", "valueType": "bytes", "label": "Resource Size" },
        { "key": "statusCode", "valueType": "text", "label": "Status Code" },
        { "key": "mimeType", "valueType": "text", "label": "MIME Type" },
        { "key": "resourceType", "valueType": "text", "label": "Resource Type" }
      ],
      "items": [
        {
          "url": "https://example.com/",
          "protocol": "h2",
          "startTime": 0,
          "endTime": 450,
          "transferSize": 15000,
          "resourceSize": 45000,
          "statusCode": 200,
          "mimeType": "text/html",
          "resourceType": "Document",
          "priority": "VeryHigh",
          "experimentalFromMainFrame": true
        },
        {
          "url": "https://example.com/css/styles.css",
          "protocol": "h2",
          "startTime": 100,
          "endTime": 350,
          "transferSize": 8000,
          "resourceSize": 25000,
          "statusCode": 200,
          "mimeType": "text/css",
          "resourceType": "Stylesheet"
        },
        {
          "url": "https://example.com/js/app.js",
          "protocol": "h2",
          "startTime": 100,
          "endTime": 500,
          "transferSize": 95000,
          "resourceSize": 320000,
          "statusCode": 200,
          "mimeType": "application/javascript",
          "resourceType": "Script"
        }
      ]
    }
  }
}
```

### Resource Types

| resourceType  | Description                  |
|---------------|------------------------------|
| `Document`    | HTML document                |
| `Stylesheet`  | CSS files                    |
| `Script`      | JavaScript files             |
| `Image`       | Image files (JPG, PNG, etc.) |
| `Font`        | Font files (WOFF2, etc.)     |
| `XHR`         | XMLHttpRequest / Fetch API   |
| `Media`       | Audio/Video files            |
| `Other`       | Other resource types         |

### resource-summary Audit

Provides an aggregated summary by resource type.

```json
{
  "resource-summary": {
    "details": {
      "items": [
        { "resourceType": "total", "requestCount": 85, "transferSize": 2500000, "label": "Total" },
        { "resourceType": "script", "requestCount": 25, "transferSize": 1200000, "label": "Script" },
        { "resourceType": "image", "requestCount": 30, "transferSize": 800000, "label": "Image" },
        { "resourceType": "stylesheet", "requestCount": 5, "transferSize": 150000, "label": "Stylesheet" },
        { "resourceType": "font", "requestCount": 4, "transferSize": 200000, "label": "Font" },
        { "resourceType": "document", "requestCount": 1, "transferSize": 50000, "label": "Document" },
        { "resourceType": "other", "requestCount": 10, "transferSize": 100000, "label": "Other" },
        { "resourceType": "third-party", "requestCount": 40, "transferSize": 1800000, "label": "Third-party" }
      ]
    }
  }
}
```

---

## 15. Third-Party Analysis

### third-party-summary Audit

Breaks down third-party script impact by provider.

```json
{
  "third-party-summary": {
    "id": "third-party-summary",
    "title": "Reduce the impact of third-party code",
    "score": 0,
    "displayValue": "Third-party code blocked the main thread for 850 ms",
    "details": {
      "type": "table",
      "summary": {
        "wastedBytes": 219053,
        "wastedMs": 850
      },
      "headings": [
        { "key": "entity", "valueType": "link", "label": "Third-Party" },
        { "key": "transferSize", "valueType": "bytes", "label": "Transfer Size" },
        { "key": "blockingTime", "valueType": "ms", "label": "Main Thread Blocking Time" }
      ],
      "items": [
        {
          "entity": {
            "type": "link",
            "text": "Google Analytics",
            "url": "https://marketingplatform.google.com/about/analytics/"
          },
          "transferSize": 85000,
          "blockingTime": 200,
          "mainThreadTime": 350,
          "subItems": {
            "type": "subitems",
            "items": [
              {
                "url": "https://www.googletagmanager.com/gtag/js?id=G-XXXXX",
                "transferSize": 45000,
                "blockingTime": 120,
                "mainThreadTime": 200
              },
              {
                "url": "https://www.google-analytics.com/analytics.js",
                "transferSize": 40000,
                "blockingTime": 80,
                "mainThreadTime": 150
              }
            ]
          }
        },
        {
          "entity": {
            "type": "link",
            "text": "Facebook",
            "url": "https://www.facebook.com"
          },
          "transferSize": 134053,
          "blockingTime": 650,
          "mainThreadTime": 900
        }
      ]
    }
  }
}
```

### entities Array (lighthouseResult.entities)

Lighthouse also provides a top-level `entities` array classifying all third-party origins:

```json
{
  "entities": [
    {
      "name": "example.com",
      "isFirstParty": true,
      "isUnrecognized": false,
      "origins": ["https://example.com"],
      "homepage": "https://example.com"
    },
    {
      "name": "Google Analytics",
      "isFirstParty": false,
      "isUnrecognized": false,
      "origins": ["https://www.google-analytics.com", "https://www.googletagmanager.com"],
      "homepage": "https://marketingplatform.google.com/about/analytics/",
      "category": "analytics"
    },
    {
      "name": "Google Fonts",
      "isFirstParty": false,
      "isUnrecognized": false,
      "origins": ["https://fonts.googleapis.com", "https://fonts.gstatic.com"],
      "homepage": "https://fonts.google.com/",
      "category": "cdn"
    }
  ]
}
```

---

## 16. CMS & Technology Stack Detection

### stackPacks Array

Lighthouse detects the CMS/framework and includes platform-specific recommendations via the `stackPacks` array.

**Path:** `lighthouseResult.stackPacks`

```json
{
  "stackPacks": [
    {
      "id": "wordpress",
      "title": "WordPress",
      "iconDataURL": "data:image/svg+xml;base64,...",
      "descriptions": {
        "unused-css-rules": "Consider reducing, or switching, the number of [WordPress plugins](https://developer.wordpress.org/plugins/) loading unused CSS in your page...",
        "unused-javascript": "Consider reducing, or switching, the number of [WordPress plugins](https://developer.wordpress.org/plugins/) loading unused JavaScript in your page...",
        "modern-image-formats": "Consider using a [plugin](https://wordpress.org/plugins/search/avif/) that will convert your uploaded images to WebP/AVIF...",
        "render-blocking-resources": "There are a number of WordPress plugins that can help you [inline critical assets](https://developer.wordpress.org/plugins/) or [defer less important resources](https://developer.wordpress.org/plugins/)...",
        "offscreen-images": "Install a [lazy-load WordPress plugin](https://wordpress.org/plugins/search/lazy+load/) that provides the ability to defer any offscreen images...",
        "efficient-animated-content": "Consider uploading your GIF to a service which will make it available to embed as an HTML5 video.",
        "server-response-time": "Themes, plugins, and server specifications all contribute to server response time. Consider finding a more optimized theme, carefully selecting an optimization plugin, and/or upgrading your server.",
        "uses-long-cache-ttl": "Read about [Browser Caching in WordPress](https://developer.wordpress.org/advanced-administration/performance/optimization-caching/#browser-caching).",
        "uses-text-compression": "You can enable text compression in your web server configuration.",
        "uses-responsive-images": "Upload images directly through the [media library](https://wordpress.org/documentation/article/media-library-screen/) to ensure that the required image sizes are available..."
      }
    }
  ]
}
```

### Supported Stack Packs (as of 2025)

| ID          | Platform    |
|-------------|-------------|
| `wordpress` | WordPress   |
| `drupal`    | Drupal      |
| `magento`   | Magento     |
| `angular`   | Angular     |
| `react`     | React       |
| `amp`       | AMP         |
| `next.js`   | Next.js     |
| `nuxt`      | Nuxt.js     |
| `gatsby`    | Gatsby      |
| `wp-rocket` | WP Rocket   |

### CMS Detection Logic

```python
# Python - Detect CMS from stackPacks
stack_packs = response["lighthouseResult"].get("stackPacks", [])

detected_stacks = []
for pack in stack_packs:
    detected_stacks.append({
        "id": pack["id"],
        "title": pack["title"],
        "descriptions": pack.get("descriptions", {})
    })

# Check for specific CMS
is_wordpress = any(p["id"] == "wordpress" for p in stack_packs)
is_drupal = any(p["id"] == "drupal" for p in stack_packs)
is_magento = any(p["id"] == "magento" for p in stack_packs)
```

### Alternative CMS Detection Methods

When `stackPacks` is empty (e.g., Shopify, Wix, Squarespace are not currently in stack packs), use these fallback methods:

```python
# Method 1: Check network requests for CMS-specific patterns
network_items = response["lighthouseResult"]["audits"]["network-requests"]["details"]["items"]

cms_indicators = {
    "wordpress": ["/wp-content/", "/wp-includes/", "/wp-admin/"],
    "shopify": [".myshopify.com", "cdn.shopify.com", "/shopify/"],
    "wix": ["static.wixstatic.com", "parastorage.com", "wix.com"],
    "squarespace": ["static1.squarespace.com", "squarespace.com/assets"],
    "webflow": ["assets.website-files.com", "webflow.com"],
    "drupal": ["/sites/default/files/", "/modules/", "/core/misc/drupal.js"],
    "joomla": ["/media/system/", "/components/com_"],
    "magento": ["/static/version", "/media/catalog/", "mage/"],
}

detected_cms = set()
for item in network_items:
    url = item.get("url", "")
    for cms, patterns in cms_indicators.items():
        if any(pattern in url for pattern in patterns):
            detected_cms.add(cms)

# Method 2: Check the HTML document for meta generator tag
# (requires parsing the page HTML separately, not available in PSI response directly)

# Method 3: Check entities for known CDN/service patterns
entities = response["lighthouseResult"].get("entities", [])
for entity in entities:
    name_lower = entity.get("name", "").lower()
    if "shopify" in name_lower:
        detected_cms.add("shopify")
    elif "squarespace" in name_lower:
        detected_cms.add("squarespace")
    elif "wix" in name_lower:
        detected_cms.add("wix")
```

---

## 17. Category Scores

### Accessing Category Scores

```python
categories = response["lighthouseResult"]["categories"]

# Performance score (0-1, multiply by 100 for percentage)
perf_score = categories["performance"]["score"] * 100

# Other categories (only present if requested via category parameter)
accessibility_score = categories.get("accessibility", {}).get("score", None)
best_practices_score = categories.get("best-practices", {}).get("score", None)
seo_score = categories.get("seo", {}).get("score", None)

if accessibility_score is not None:
    accessibility_score *= 100
if best_practices_score is not None:
    best_practices_score *= 100
if seo_score is not None:
    seo_score *= 100
```

### Category Object Structure

```json
{
  "categories": {
    "performance": {
      "id": "performance",
      "title": "Performance",
      "score": 0.45,
      "auditRefs": [
        { "id": "first-contentful-paint", "weight": 10, "group": "metrics" },
        { "id": "largest-contentful-paint", "weight": 25, "group": "metrics" },
        { "id": "speed-index", "weight": 10, "group": "metrics" },
        { "id": "total-blocking-time", "weight": 30, "group": "metrics" },
        { "id": "cumulative-layout-shift", "weight": 25, "group": "metrics" },
        { "id": "render-blocking-resources", "weight": 0, "group": "load-opportunities" },
        { "id": "unused-javascript", "weight": 0, "group": "load-opportunities" },
        { "id": "dom-size", "weight": 0, "group": "diagnostics" },
        { "id": "bootup-time", "weight": 0, "group": "diagnostics" }
      ]
    }
  }
}
```

The `auditRefs` array tells you:
- Which audits belong to each category
- Their scoring weight (only metrics have weight > 0)
- Their display group: `metrics`, `load-opportunities`, or `diagnostics`

---

## 18. Complete Audit Key Reference

### Performance Metrics (Weighted - Affect Score)

| Audit Key                    | Description                      | Weight |
|------------------------------|----------------------------------|--------|
| `first-contentful-paint`     | First Contentful Paint           | 10%    |
| `speed-index`                | Speed Index                      | 10%    |
| `largest-contentful-paint`   | Largest Contentful Paint         | 25%    |
| `total-blocking-time`        | Total Blocking Time              | 30%    |
| `cumulative-layout-shift`    | Cumulative Layout Shift          | 25%    |
| `interactive`                | Time to Interactive (informational, no weight in LH10+) | 0% |

### Opportunity Audits (load-opportunities group)

| Audit Key                       | Description                                  |
|---------------------------------|----------------------------------------------|
| `render-blocking-resources`     | Eliminate render-blocking resources           |
| `unused-javascript`             | Remove unused JavaScript                     |
| `unused-css-rules`              | Remove unused CSS                            |
| `offscreen-images`              | Defer offscreen images                       |
| `modern-image-formats`          | Serve images in next-gen formats (WebP/AVIF) |
| `uses-responsive-images`        | Properly size images                         |
| `efficiently-encode-images`     | Efficiently encode images                    |
| `uses-text-compression`         | Enable text compression                      |
| `uses-long-cache-ttl`           | Serve static assets with efficient cache policy |
| `unminified-javascript`         | Minify JavaScript                            |
| `unminified-css`                | Minify CSS                                   |
| `redirects`                     | Avoid multiple page redirects                |
| `server-response-time`          | Reduce initial server response time          |
| `efficient-animated-content`    | Use video formats for animated content       |
| `duplicated-javascript`         | Remove duplicate modules in JS bundles       |
| `legacy-javascript`             | Avoid serving legacy JavaScript to modern browsers |
| `preload-lcp-image`             | Preload Largest Contentful Paint image       |
| `uses-rel-preload`              | Preload key requests                         |
| `uses-rel-preconnect`           | Preconnect to required origins               |
| `total-byte-weight`             | Avoid enormous network payloads              |

### Diagnostic Audits (diagnostics group)

| Audit Key                          | Description                                  |
|------------------------------------|----------------------------------------------|
| `dom-size`                         | Avoid an excessive DOM size                  |
| `bootup-time`                      | Reduce JavaScript execution time             |
| `mainthread-work-breakdown`        | Minimize main-thread work                    |
| `third-party-summary`             | Reduce the impact of third-party code        |
| `third-party-facades`             | Lazy load third-party resources with facades |
| `font-display`                     | Ensure text remains visible during webfont load |
| `critical-request-chains`          | Avoid chaining critical requests             |
| `user-timings`                     | User Timing marks and measures               |
| `long-tasks`                       | Avoid long main-thread tasks                 |
| `non-composited-animations`        | Avoid non-composited animations              |
| `unsized-images`                   | Image elements have explicit width and height |
| `viewport`                         | Has a meta viewport tag with width or initial-scale |
| `no-document-write`               | Avoids document.write()                      |
| `uses-passive-event-listeners`     | Uses passive listeners to improve scrolling performance |
| `uses-http2`                       | Use HTTP/2                                   |
| `prioritize-lcp-image`            | Prioritize the LCP image for faster loading  |
| `lcp-lazy-loaded`                  | LCP image was lazily loaded                  |

### Informational Audits (No Group)

| Audit Key                          | Description                                  |
|------------------------------------|----------------------------------------------|
| `final-screenshot`                 | Final screenshot of loaded page              |
| `screenshot-thumbnails`            | Screenshot thumbnails (filmstrip)            |
| `full-page-screenshot`             | Full page screenshot with element positions  |
| `network-requests`                 | Network requests table                       |
| `resource-summary`                 | Resource summary by type                     |
| `metrics`                          | Consolidated metrics summary                 |
| `diagnostics`                      | Diagnostics summary (request counts, etc.)   |
| `largest-contentful-paint-element` | LCP element identification                   |
| `layout-shift-elements`           | CLS culprit elements                         |
| `script-treemap-data`             | JavaScript treemap/coverage data             |
| `main-thread-tasks`               | Main thread task list                        |
| `network-rtt`                      | Network round trip times                     |
| `network-server-latency`          | Server backend latencies                     |
| `timing-budget`                    | Timing budget                                |
| `performance-budget`              | Performance budget                           |
| `max-potential-fid`               | Max Potential First Input Delay              |
| `first-meaningful-paint`          | First Meaningful Paint (deprecated metric)   |

### Lighthouse 13+ Insight Audits (Newer replacements)

| New Audit Key              | Replaces                      | Description                     |
|---------------------------|-------------------------------|---------------------------------|
| `cls-culprits-insight`    | `layout-shift-elements`       | CLS culprits insight            |
| `lcp-discovery-insight`   | -                             | LCP discovery optimization      |
| `lcp-phases-insight`      | -                             | LCP phase breakdown             |
| `dom-size-insight`        | `dom-size`                    | DOM size insight                |
| `render-blocking-insight` | `render-blocking-resources`   | Render blocking insight         |

> **Note**: Legacy audits remain available alongside new insight audits. Legacy removal is planned for October 2025.

---

## 19. Parsing Patterns for Agent Implementation

### Complete Agent Parsing Flow

```python
import requests
import json

def analyze_page(url: str, api_key: str, strategy: str = "mobile") -> dict:
    """
    Calls PSI API and extracts all performance issues.
    Returns structured analysis result.
    """

    # 1. Make API Request
    endpoint = "https://www.googleapis.com/pagespeedonline/v5/runPagespeed"
    params = {
        "url": url,
        "strategy": strategy,
        "category": ["performance", "accessibility", "seo", "best-practices"],
        "key": api_key,
    }

    response = requests.get(endpoint, params=params)
    data = response.json()

    result = {
        "url": data.get("id", url),
        "timestamp": data.get("analysisUTCTimestamp"),
        "strategy": strategy,
    }

    lhr = data.get("lighthouseResult", {})
    audits = lhr.get("audits", {})

    # 2. Extract Category Scores
    categories = lhr.get("categories", {})
    result["scores"] = {}
    for cat_id, cat_data in categories.items():
        result["scores"][cat_id] = round(cat_data.get("score", 0) * 100, 1)

    # 3. Extract Core Web Vitals (Field Data)
    field_data = data.get("loadingExperience", {})
    field_metrics = field_data.get("metrics", {})
    result["field_data"] = {
        "overall_category": field_data.get("overall_category", "NONE"),
        "lcp_ms": field_metrics.get("LARGEST_CONTENTFUL_PAINT_MS", {}).get("percentile"),
        "lcp_category": field_metrics.get("LARGEST_CONTENTFUL_PAINT_MS", {}).get("category"),
        "cls": field_metrics.get("CUMULATIVE_LAYOUT_SHIFT_SCORE", {}).get("percentile"),
        "cls_category": field_metrics.get("CUMULATIVE_LAYOUT_SHIFT_SCORE", {}).get("category"),
        "inp_ms": field_metrics.get("INTERACTION_TO_NEXT_PAINT", {}).get("percentile"),
        "inp_category": field_metrics.get("INTERACTION_TO_NEXT_PAINT", {}).get("category"),
        "fcp_ms": field_metrics.get("FIRST_CONTENTFUL_PAINT_MS", {}).get("percentile"),
        "fcp_category": field_metrics.get("FIRST_CONTENTFUL_PAINT_MS", {}).get("category"),
    }
    # CLS needs division by 100 to get the actual value
    if result["field_data"]["cls"] is not None:
        result["field_data"]["cls_value"] = result["field_data"]["cls"] / 100

    # 4. Extract Lab Metrics
    metrics_items = audits.get("metrics", {}).get("details", {}).get("items", [{}])
    metrics_data = metrics_items[0] if metrics_items else {}
    result["lab_metrics"] = {
        "fcp_ms": metrics_data.get("firstContentfulPaint"),
        "lcp_ms": metrics_data.get("largestContentfulPaint"),
        "speed_index_ms": metrics_data.get("speedIndex"),
        "tbt_ms": metrics_data.get("totalBlockingTime"),
        "cls": metrics_data.get("cumulativeLayoutShift"),
        "tti_ms": metrics_data.get("interactive"),
    }

    # Also extract display values for readable output
    result["lab_display"] = {}
    for key in ["first-contentful-paint", "largest-contentful-paint", "speed-index",
                 "total-blocking-time", "cumulative-layout-shift", "interactive"]:
        audit = audits.get(key, {})
        result["lab_display"][key] = {
            "display_value": audit.get("displayValue"),
            "score": audit.get("score"),
            "numeric_value": audit.get("numericValue"),
        }

    # 5. Extract Opportunity Issues (with resource URLs)
    opportunity_keys = [
        "render-blocking-resources", "unused-javascript", "unused-css-rules",
        "offscreen-images", "modern-image-formats", "uses-responsive-images",
        "efficiently-encode-images", "uses-text-compression", "uses-long-cache-ttl",
        "unminified-javascript", "unminified-css", "redirects", "server-response-time",
        "efficient-animated-content", "duplicated-javascript", "legacy-javascript",
        "preload-lcp-image", "uses-rel-preload", "uses-rel-preconnect",
    ]

    result["opportunities"] = []
    for key in opportunity_keys:
        audit = audits.get(key, {})
        score = audit.get("score")
        if score is not None and score < 1:
            details = audit.get("details", {})
            items = details.get("items", [])
            opportunity = {
                "audit_key": key,
                "title": audit.get("title"),
                "description": audit.get("description"),
                "score": score,
                "display_value": audit.get("displayValue"),
                "savings_ms": details.get("overallSavingsMs", 0),
                "savings_bytes": details.get("overallSavingsBytes", 0),
                "resources": [],
            }
            for item in items:
                resource = {
                    "url": item.get("url"),
                    "total_bytes": item.get("totalBytes"),
                    "wasted_bytes": item.get("wastedBytes"),
                    "wasted_ms": item.get("wastedMs"),
                    "wasted_percent": item.get("wastedPercent"),
                }
                # Include node info if present (for image audits)
                node = item.get("node")
                if node:
                    resource["element"] = {
                        "selector": node.get("selector"),
                        "snippet": node.get("snippet"),
                        "node_label": node.get("nodeLabel"),
                        "bounding_rect": node.get("boundingRect"),
                        "lh_id": node.get("lhId"),
                    }
                opportunity["resources"].append(resource)

            result["opportunities"].append(opportunity)

    # Sort by savings (ms first, then bytes)
    result["opportunities"].sort(
        key=lambda x: (x["savings_ms"], x["savings_bytes"]),
        reverse=True
    )

    # 6. Extract Diagnostic Issues
    diagnostic_keys = [
        "dom-size", "bootup-time", "mainthread-work-breakdown",
        "third-party-summary", "third-party-facades", "font-display",
        "critical-request-chains", "long-tasks", "non-composited-animations",
        "unsized-images", "uses-http2", "lcp-lazy-loaded",
    ]

    result["diagnostics"] = []
    for key in diagnostic_keys:
        audit = audits.get(key, {})
        score = audit.get("score")
        if score is not None and score < 1:
            details = audit.get("details", {})
            diagnostic = {
                "audit_key": key,
                "title": audit.get("title"),
                "score": score,
                "display_value": audit.get("displayValue"),
                "items": details.get("items", []),
            }
            result["diagnostics"].append(diagnostic)

    # 7. Extract LCP Element Info
    lcp_element_audit = audits.get("largest-contentful-paint-element", {})
    lcp_items = lcp_element_audit.get("details", {}).get("items", [])
    if lcp_items:
        first_item = lcp_items[0]
        # May have items within items for sub-elements
        sub_items = first_item.get("items", [first_item])
        for sub in sub_items:
            node = sub.get("node")
            if node:
                result["lcp_element"] = {
                    "selector": node.get("selector"),
                    "snippet": node.get("snippet"),
                    "node_label": node.get("nodeLabel"),
                    "bounding_rect": node.get("boundingRect"),
                    "lh_id": node.get("lhId"),
                }
                break

    # 8. Extract CLS Culprit Elements
    cls_audit = audits.get("layout-shift-elements", {})
    cls_items = cls_audit.get("details", {}).get("items", [])
    result["cls_elements"] = []
    for item in cls_items:
        node = item.get("node", {})
        result["cls_elements"].append({
            "selector": node.get("selector"),
            "snippet": node.get("snippet"),
            "node_label": node.get("nodeLabel"),
            "cls_contribution": item.get("score"),
        })

    # 9. Detect CMS / Technology Stack
    stack_packs = lhr.get("stackPacks", [])
    result["detected_stacks"] = [
        {"id": p["id"], "title": p["title"]}
        for p in stack_packs
    ]

    # Fallback CMS detection via network requests
    if not result["detected_stacks"]:
        network_items = audits.get("network-requests", {}).get("details", {}).get("items", [])
        cms_patterns = {
            "wordpress": ["/wp-content/", "/wp-includes/", "/wp-admin/", "wp-json"],
            "shopify": ["cdn.shopify.com", ".myshopify.com", "shopify.com/s/"],
            "wix": ["static.wixstatic.com", "parastorage.com"],
            "squarespace": ["static1.squarespace.com", "sqsp.net"],
            "webflow": ["assets.website-files.com", "webflow.io"],
            "magento": ["/static/version", "/media/catalog/", "/mage/"],
            "drupal": ["/sites/default/files/", "/core/misc/drupal.js"],
        }
        detected = set()
        for item in network_items:
            req_url = item.get("url", "")
            for cms, patterns in cms_patterns.items():
                if any(p in req_url for p in patterns):
                    detected.add(cms)
        result["detected_stacks_fallback"] = list(detected)

    # 10. Extract Screenshot Data
    final_ss = audits.get("final-screenshot", {}).get("details", {})
    result["screenshots"] = {
        "final": final_ss.get("data"),  # base64 data URI
        "final_timing": final_ss.get("timing"),
    }

    filmstrip = audits.get("screenshot-thumbnails", {}).get("details", {}).get("items", [])
    result["screenshots"]["filmstrip"] = [
        {"timing": f.get("timing"), "data": f.get("data")}
        for f in filmstrip
    ]

    fps = lhr.get("fullPageScreenshot", {})
    if fps:
        result["screenshots"]["full_page"] = {
            "data": fps.get("screenshot", {}).get("data"),
            "width": fps.get("screenshot", {}).get("width"),
            "height": fps.get("screenshot", {}).get("height"),
            "nodes": fps.get("nodes", {}),  # element positions
        }

    # 11. Extract Diagnostics Summary
    diag_summary = audits.get("diagnostics", {}).get("details", {}).get("items", [{}])
    if diag_summary:
        ds = diag_summary[0]
        result["page_stats"] = {
            "num_requests": ds.get("numRequests"),
            "total_byte_weight": ds.get("totalByteWeight"),
            "num_scripts": ds.get("numScripts"),
            "num_stylesheets": ds.get("numStylesheets"),
            "num_fonts": ds.get("numFonts"),
            "num_tasks": ds.get("numTasks"),
            "num_tasks_over_50ms": ds.get("numTasksOver50ms"),
            "total_task_time": ds.get("totalTaskTime"),
            "max_rtt": ds.get("maxRtt"),
            "max_server_latency": ds.get("maxServerLatency"),
            "throughput": ds.get("throughput"),
        }

    # 12. Extract Resource Summary
    res_summary = audits.get("resource-summary", {}).get("details", {}).get("items", [])
    result["resource_summary"] = [
        {
            "resource_type": item.get("resourceType"),
            "label": item.get("label"),
            "request_count": item.get("requestCount"),
            "transfer_size": item.get("transferSize"),
        }
        for item in res_summary
    ]

    return result
```

### JavaScript/Node.js Implementation

```javascript
async function analyzePageSpeed(url, apiKey, strategy = "mobile") {
  const endpoint = "https://www.googleapis.com/pagespeedonline/v5/runPagespeed";
  const params = new URLSearchParams({
    url: url,
    strategy: strategy,
    key: apiKey,
  });
  // Add multiple categories
  ["performance", "accessibility", "seo", "best-practices"].forEach((cat) => {
    params.append("category", cat);
  });

  const response = await fetch(`${endpoint}?${params.toString()}`);
  const data = await response.json();

  const lhr = data.lighthouseResult;
  const audits = lhr.audits;

  // Performance score
  const perfScore = Math.round(lhr.categories.performance.score * 100);

  // Lab metrics
  const metricsData = audits.metrics?.details?.items?.[0] || {};
  const labMetrics = {
    fcp: metricsData.firstContentfulPaint,
    lcp: metricsData.largestContentfulPaint,
    si: metricsData.speedIndex,
    tbt: metricsData.totalBlockingTime,
    cls: metricsData.cumulativeLayoutShift,
    tti: metricsData.interactive,
  };

  // Opportunities with resource URLs
  const opportunities = [];
  const opportunityKeys = [
    "render-blocking-resources",
    "unused-javascript",
    "unused-css-rules",
    "offscreen-images",
    "modern-image-formats",
    "uses-responsive-images",
    "efficiently-encode-images",
    "uses-text-compression",
    "unminified-javascript",
    "unminified-css",
    "uses-long-cache-ttl",
    "server-response-time",
    "preload-lcp-image",
    "legacy-javascript",
    "duplicated-javascript",
  ];

  for (const key of opportunityKeys) {
    const audit = audits[key];
    if (audit?.score !== null && audit?.score < 1) {
      const details = audit.details || {};
      opportunities.push({
        key,
        title: audit.title,
        score: audit.score,
        displayValue: audit.displayValue,
        savingsMs: details.overallSavingsMs || 0,
        savingsBytes: details.overallSavingsBytes || 0,
        resources: (details.items || []).map((item) => ({
          url: item.url,
          totalBytes: item.totalBytes,
          wastedBytes: item.wastedBytes,
          wastedMs: item.wastedMs,
        })),
      });
    }
  }

  // CMS Detection
  const stackPacks = lhr.stackPacks || [];
  const detectedCMS = stackPacks.map((p) => ({ id: p.id, title: p.title }));

  // Screenshots
  const finalScreenshot = audits["final-screenshot"]?.details?.data;
  const filmstrip = (audits["screenshot-thumbnails"]?.details?.items || []).map(
    (item) => ({ timing: item.timing, data: item.data })
  );

  return {
    url: data.id,
    perfScore,
    labMetrics,
    opportunities,
    detectedCMS,
    finalScreenshot,
    filmstrip,
  };
}
```

---

## 20. Field Data vs Lab Data

### Comparison

| Aspect            | Field Data (CrUX)                    | Lab Data (Lighthouse)                |
|-------------------|--------------------------------------|--------------------------------------|
| **Source**         | Real Chrome users over 28 days       | Simulated in controlled environment  |
| **Device**        | Actual user devices                  | Emulated (Moto G Power for mobile)   |
| **Network**       | Real network conditions              | Simulated throttling (slow 4G)       |
| **Metrics**       | FCP, LCP, CLS, INP, TTFB            | FCP, LCP, CLS, TBT, SI, TTI         |
| **Variability**   | Aggregated, stable                   | Can vary between runs                |
| **Use Case**      | Real user experience assessment      | Debugging and optimization           |
| **Availability**  | Only for pages with sufficient traffic | Always available                    |
| **Core Web Vitals**| Uses INP (real interactivity)       | Uses TBT (proxy for interactivity)   |

### When Each Is Unavailable

- **Field data may be missing** (`overall_category: "NONE"`) when the URL or origin doesn't have enough Chrome traffic
- **Lab data is always available** as it runs a fresh Lighthouse audit

### Key Difference: INP vs TBT

- **INP** (Interaction to Next Paint) is a field-only Core Web Vital measuring actual user interaction responsiveness
- **TBT** (Total Blocking Time) is the lab equivalent/proxy, measuring how long the main thread was blocked between FCP and TTI
- Both assess interactivity but through different lenses

---

## 21. Important Notes & Limitations

### API Behavior

1. **Response size**: Responses are typically 300-800KB of JSON depending on page complexity and requested categories
2. **Execution time**: API calls typically take 10-30 seconds to complete (Lighthouse must load and analyze the page)
3. **Variability**: Lab data scores can vary between runs due to simulated conditions and server variability; differences of 5-10 points are normal
4. **Throttling simulation**: Uses simulated throttling (not actual network throttling), which may not perfectly reflect real-world conditions
5. **No authentication support**: Cannot test pages behind login/authentication
6. **robots.txt**: The API respects robots.txt; pages blocked from crawling cannot be tested
7. **Redirects**: The `id` field returns the final URL after all redirects

### CrUX Data Deprecation

Google has announced plans to discontinue including CrUX real-world data in the PSI API response. For continued field data access, migrate to:
- **CrUX API**: https://developer.chrome.com/docs/crux/api/
- **CrUX History API**: For historical trends over time

### Lighthouse Version Updates

The Lighthouse version used by PSI is updated regularly. Check `lighthouseResult.lighthouseVersion` to know which version generated the results. Audit keys, scoring weights, and thresholds may change between major versions.

### Lighthouse 13 Changes (2025)

Lighthouse 13 introduces "insight-based audits" that consolidate multiple legacy audits into unified insights:
- Many existing audit IDs remain available during a transition period
- New insight audit IDs (like `cls-culprits-insight`, `lcp-discovery-insight`) are added alongside legacy ones
- Legacy audit removal planned for October 2025
- Performance scoring methodology remains unchanged

### Error Handling

```python
# Always check for runtime errors
runtime_error = data.get("lighthouseResult", {}).get("runtimeError")
if runtime_error:
    error_code = runtime_error.get("code")
    error_message = runtime_error.get("message")
    # Common errors:
    # - ERRORED_DOCUMENT_REQUEST: Page failed to load
    # - FAILED_DOCUMENT_REQUEST: Network error
    # - DNS_FAILURE: DNS resolution failed
    # - PROTOCOL_TIMEOUT: Page load timed out

# Check for run warnings
warnings = data.get("lighthouseResult", {}).get("runWarnings", [])
# Warnings don't prevent analysis but may affect accuracy

# Check HTTP errors from the API itself
if response.status_code == 429:
    # Rate limited - implement backoff
    pass
elif response.status_code == 400:
    # Invalid URL or parameters
    pass
elif response.status_code == 500:
    # Server error - retry
    pass
```

### Best Practices for Production Use

1. **Always use an API key** for reliable access and higher quotas
2. **Implement retry logic** with exponential backoff for 429 and 500 errors
3. **Cache results** for at least a few hours; page performance doesn't change minute-to-minute
4. **Request only needed categories** to reduce response size and processing time
5. **Use `strategy=mobile`** as the primary strategy since Google uses mobile-first indexing
6. **Handle missing field data** gracefully; many pages won't have CrUX data
7. **Store raw responses** for historical comparison and debugging
8. **Parse defensively** - always use `.get()` with defaults as audit structures can vary

---

## Appendix: Quick Reference Card

### Minimal API Call

```bash
curl "https://www.googleapis.com/pagespeedonline/v5/runPagespeed?url=https://example.com&strategy=mobile&key=YOUR_KEY"
```

### Key Data Access Paths

```
Performance Score:     lighthouseResult.categories.performance.score * 100
FCP (lab):            lighthouseResult.audits["first-contentful-paint"].numericValue
LCP (lab):            lighthouseResult.audits["largest-contentful-paint"].numericValue
TBT (lab):            lighthouseResult.audits["total-blocking-time"].numericValue
CLS (lab):            lighthouseResult.audits["cumulative-layout-shift"].numericValue
SI (lab):             lighthouseResult.audits["speed-index"].numericValue

LCP (field):          loadingExperience.metrics.LARGEST_CONTENTFUL_PAINT_MS.percentile
CLS (field):          loadingExperience.metrics.CUMULATIVE_LAYOUT_SHIFT_SCORE.percentile / 100
INP (field):          loadingExperience.metrics.INTERACTION_TO_NEXT_PAINT.percentile
FCP (field):          loadingExperience.metrics.FIRST_CONTENTFUL_PAINT_MS.percentile

All metrics:          lighthouseResult.audits.metrics.details.items[0]
Page stats:           lighthouseResult.audits.diagnostics.details.items[0]
LCP Element:          lighthouseResult.audits["largest-contentful-paint-element"].details.items
CLS Elements:         lighthouseResult.audits["layout-shift-elements"].details.items
CMS Detection:        lighthouseResult.stackPacks[].id
Network Requests:     lighthouseResult.audits["network-requests"].details.items
Final Screenshot:     lighthouseResult.audits["final-screenshot"].details.data
Filmstrip:            lighthouseResult.audits["screenshot-thumbnails"].details.items
Full Page Screenshot: lighthouseResult.fullPageScreenshot.screenshot.data
Element Positions:    lighthouseResult.fullPageScreenshot.nodes[lhId]
Third-Party Impact:   lighthouseResult.audits["third-party-summary"].details.items
Resource Summary:     lighthouseResult.audits["resource-summary"].details.items
```
