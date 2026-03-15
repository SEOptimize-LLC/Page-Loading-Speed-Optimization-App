# Page Speed Optimization Agent - Claude Code Guidelines

## Project Overview

AI-powered Streamlit web app for deep page speed analysis and optimization recommendations. Targets WordPress and Shopify sites with mobile-first focus. Combines Google PageSpeed Insights API v5 data, raw HTML analysis via BeautifulSoup, and curated expert knowledge to produce professional reports with AI-generated fix instructions.

## Tech Stack

- **Framework**: Streamlit (deploy to Streamlit Cloud)
- **AI**: OpenRouter API (Gemini Flash default, Claude Sonnet for deep analysis, GPT-4.1 Mini)
- **APIs**: Google PageSpeed Insights API v5
- **HTML Parsing**: BeautifulSoup4 + lxml
- **Reports**: Jinja2 templates + WeasyPrint PDF
- **Image Processing**: Pillow
- **Language**: Python 3.9+

## Project Structure

```
Page Loading Speed Optimization Agent/
|-- app.py                          # Main Streamlit entry point, orchestrates full pipeline
|-- requirements.txt                # Python dependencies
|-- packages.txt                    # System packages for Streamlit Cloud (WeasyPrint deps)
|-- .env.example                    # Environment variable template
|-- .streamlit/config.toml          # Streamlit theme and server config
|
|-- src/
|   |-- models/
|   |   |-- speed_issue.py          # Severity, CWVMetric, CWVStatus, SpeedIssue, CMSInfo
|   |   |-- analysis_result.py      # AnalysisResult, PageStats dataclasses
|   |-- collectors/
|   |   |-- pagespeed_client.py     # PSI API v5 client with full response parsing
|   |   |-- html_analyzer.py        # Raw HTML fetch + BeautifulSoup code-level analysis
|   |   |-- screenshot_processor.py # Screenshot cropping and severity-colored highlighting
|   |-- analyzers/
|   |   |-- cms_detector.py         # Multi-signal CMS detection (WP/Shopify/Wix/etc.)
|   |   |-- issue_classifier.py     # Severity classification, CWV mapping, priority scoring
|   |   |-- resource_analyzer.py    # Network request analysis, third-party impact, compression gaps
|   |-- ai/
|   |   |-- knowledge_base.py       # KB loader, section splitter, relevance-based selector
|   |   |-- prompt_builder.py       # System + user prompt construction for two-stage AI analysis
|   |   |-- openrouter_client.py    # OpenRouter API client with JSON parsing and streaming
|   |-- reports/
|       |-- report_generator.py     # Jinja2 HTML report generation with white-label support
|       |-- pdf_converter.py        # WeasyPrint HTML-to-PDF conversion
|       |-- templates/
|           |-- speed_report.html   # Full report HTML template with Jinja2 macros
|           |-- report_styles.css   # Professional CSS with custom properties for branding
|
|-- knowledge-base/                 # 6 curated expert markdown files
|   |-- pagespeed-insights-api.md
|   |-- performance-optimization-techniques.md
|   |-- wordpress-optimization.md
|   |-- wpspeedmatters-insights.md
|   |-- shopify-and-inp-cases.md
|   |-- shopify-liquid-patterns.md
|
|-- utils/
    |-- formatting.py               # format_bytes, format_ms, score_color, truncate_url
    |-- url_utils.py                # validate_url, normalize_url, extract_domain, is_same_origin
```

## Key Files

- `app.py` -- Main Streamlit entry point, orchestrates the full analysis pipeline
- `src/collectors/pagespeed_client.py` -- PSI API v5 client with 14 parse methods covering scores, field data, lab metrics, opportunities, diagnostics, LCP/CLS elements, stack packs, entities, screenshots, page stats, resource summary, third-party summary, and network requests
- `src/collectors/html_analyzer.py` -- Fetches raw HTML with mobile User-Agent, analyzes DOM size/depth, images (missing dimensions, srcset, fetchpriority, lazy above fold), scripts (render-blocking), styles (render-blocking CSS, @import), fonts (Google Fonts, font-display: block, missing preloads), meta tags, resource hints, and third-party domains
- `src/collectors/screenshot_processor.py` -- Crops elements from PSI full-page screenshot using Lighthouse node positions, adds severity-colored borders (red/orange/yellow)
- `src/analyzers/cms_detector.py` -- Detects CMS from 4 signal sources: PSI stack packs, network request URL patterns, entity classification, and HTML analysis. Identifies WP plugins and Shopify apps by name
- `src/analyzers/issue_classifier.py` -- Classifies opportunities, diagnostics, and HTML findings into CRITICAL/IMPORTANT/MINOR. Maps audits to CWV metrics via `AUDIT_CWV_MAP`. Calculates composite priority scores. Merges and deduplicates PSI + HTML issues
- `src/analyzers/resource_analyzer.py` -- Analyzes network requests for largest resources, resource type breakdown, third-party impact, uncompressed text resources, poorly-cached resources, and critical chain depth estimation
- `src/ai/knowledge_base.py` -- Loads all 6 KB markdown files, splits into sections by heading, scores sections by keyword matches against `AUDIT_TO_TOPIC` map, adds CMS-specific bonuses, concatenates top sections within token budget
- `src/ai/prompt_builder.py` -- Builds two-stage prompts: (1) per-issue analysis with detailed JSON schema for fix recommendations, (2) executive summary with roadmap schema for client-facing reports
- `src/ai/openrouter_client.py` -- OpenRouter API client with `analyze()`, `analyze_stream()`, and `analyze_json()` methods. JSON extraction handles markdown code blocks and bracket matching fallbacks
- `src/reports/report_generator.py` -- Jinja2 HTML report with score gauges, CWV cards, issue cards, executive summary, roadmap, page stats, filmstrip, screenshots. White-label via CSS custom property overrides
- `src/reports/pdf_converter.py` -- WeasyPrint HTML-to-PDF with graceful degradation when WeasyPrint is not installed
- `src/reports/templates/speed_report.html` -- Full Jinja2 template with macros for score gauges, CWV badges, severity badges, issue cards, code blocks, roadmap items
- `src/reports/templates/report_styles.css` -- Professional CSS with CSS custom properties for white-labeling (`--brand-color`, `--brand-color-light`, etc.)
- `src/models/speed_issue.py` -- Enums: `Severity` (with color/label/weight properties), `CWVMetric`, `CWVStatus`. Dataclasses: `CWVAssessment`, `SpeedIssue` (with priority_score property), `CMSInfo`
- `src/models/analysis_result.py` -- `AnalysisResult` dataclass with convenience properties: `critical_issues`, `important_issues`, `minor_issues`, `sorted_issues`, `cwv_pass`

## Knowledge Base

6 markdown files in `knowledge-base/`:

- `pagespeed-insights-api.md` -- Complete PSI API v5 reference: audit IDs, metric definitions, response structure
- `performance-optimization-techniques.md` -- web.dev official docs: HTML performance, images, fonts, JS, lazy loading, resource hints
- `wordpress-optimization.md` -- WPJohnny WordPress optimization: plugins, themes, PHP, caching, hosting
- `wpspeedmatters-insights.md` -- WPSpeedMatters advanced WP performance: hosting comparisons, autoptimize, database, CDN
- `shopify-and-inp-cases.md` -- Shopify optimization and INP case studies: app impact, theme optimization, CWV fixes
- `shopify-liquid-patterns.md` -- BS-DevShop Shopify Liquid code patterns: lazy loading, critical CSS, section rendering

The knowledge base selector in `knowledge_base.py` uses `AUDIT_TO_TOPIC` to map PSI audit IDs to keyword lists, then scores KB sections by keyword match count with heading bonuses and CMS-specific bonuses. CMS-specific files (`_CMS_FILES` dict) get automatic inclusion when the CMS matches.

## Data Flow

```
URL input
  |
  v
PSI API (mobile + desktop)  +  Raw HTML fetch (mobile UA)
  |                                |
  v                                v
PSIResult (scores, metrics,   HTMLAnalysis (DOM stats,
 opportunities, diagnostics,   image/script/style/font
 screenshots, entities,        findings, CMS signals,
 stack packs, network reqs)    third-party domains)
  |                                |
  +----------+--------------------+
             |
             v
       CMS Detection (4 signal sources)
             |
             v
       Issue Classification + Severity Scoring
       (AUDIT_CWV_MAP, priority score algorithm)
             |
             v
       Knowledge Base Section Selection
       (AUDIT_TO_TOPIC keyword matching)
             |
             v
       AI Analysis (OpenRouter)
       Stage 1: Per-issue recommendations (JSON array)
       Stage 2: Executive summary + roadmap (JSON object)
             |
             v
       AnalysisResult assembly
       (SpeedIssue list, CWVAssessments, CMSInfo, screenshots)
             |
             v
       Report Generation (Jinja2 HTML)
             |
             +---> HTML report download
             +---> PDF export (WeasyPrint)
```

## Conventions

- **Data models** defined in `src/models/` as Python dataclasses with enum types
- **All API keys** accessed via `st.secrets` (Streamlit Cloud) or `.env` (local development via python-dotenv)
- **Issues classified** as `CRITICAL` / `IMPORTANT` / `MINOR` using the `Severity` enum
- **Mobile-first**: all analysis prioritizes mobile strategy; 90% of AI recommendations focus on mobile
- **Reports are white-label ready** via CSS custom properties (`--brand-color`, `--brand-color-light`, etc.)
- **PSI audit IDs** are the canonical identifiers used throughout the pipeline (e.g., `render-blocking-resources`, `unused-javascript`)
- **Knowledge base sections** are scored and selected per-analysis, not loaded in full
- **AI output** is always JSON -- `analyze_json()` handles markdown code blocks, bracket matching, and multiple extraction attempts
- **Exponential backoff** on PSI API requests (rate limits, server errors, timeouts)
- **File naming**: kebab-case for all files (e.g., `pagespeed-client.py`, `issue-classifier.py`)
- **Function naming**: snake_case for all Python functions and variables

## Common Tasks

### Add a new PSI audit detection
1. Add the audit ID to `OPPORTUNITY_AUDIT_IDS` or `DIAGNOSTIC_AUDIT_IDS` in `src/collectors/pagespeed_client.py`
2. Add the CWV mapping to `AUDIT_CWV_MAP` in `src/analyzers/issue_classifier.py`
3. Add severity classification by placing the audit ID in `CRITICAL_AUDITS` or `IMPORTANT_AUDITS` sets
4. Add topic keywords to `AUDIT_TO_TOPIC` in `src/ai/knowledge_base.py` so the KB selector can find relevant sections

### Add CMS support (e.g., Webflow, Magento)
1. Add detection patterns to `CMS_URL_INDICATORS` in `src/analyzers/cms_detector.py`
2. Add HTML-based detection logic in `src/collectors/html_analyzer.py` `_detect_cms()` method
3. Create knowledge base markdown files in `knowledge-base/`
4. Register the new CMS files in `_CMS_FILES` dict in `src/ai/knowledge_base.py`

### Modify report design
1. Edit `src/reports/templates/report_styles.css` for styling changes
2. Edit `src/reports/templates/speed_report.html` for layout and content changes
3. The template uses Jinja2 macros for reusable components (score gauges, badges, issue cards)
4. CSS custom properties in `:root` control the brand theming

### Update AI prompts
1. Edit `src/ai/prompt_builder.py`
2. `build_issue_analysis_prompt()` -- controls per-issue fix recommendations (JSON array output)
3. `build_executive_summary_prompt()` -- controls exec summary and roadmap (JSON object output)
4. The system prompt defines the output JSON schema; changes must be reflected in `app.py` where the response is parsed

### Add knowledge base content
1. Create or edit a markdown file in `knowledge-base/`
2. Use heading markers (`#`, `##`, `###`, `####`) to define sections -- the KB loader splits on these
3. Sections shorter than 50 characters are discarded
4. Add keyword mappings to `AUDIT_TO_TOPIC` in `src/ai/knowledge_base.py` so new content gets selected for relevant audits
5. For CMS-specific files, add the filename stem to `_CMS_FILES`

### Adjust severity classification logic
1. Edit `src/analyzers/issue_classifier.py`
2. `_determine_severity()` uses a 6-rule decision hierarchy based on audit sets, savings thresholds, and CWV metric health
3. `_calculate_priority_score()` blends severity weight, ms/bytes savings, CWV health bonus, and breadth bonus
4. `HTML_FINDING_MAP` controls default severities and CWV mappings for HTML-based findings
5. `HTML_TO_PSI_OVERLAP` prevents duplicate reporting when both PSI and HTML detect the same issue

## Environment Variables

```env
# Required
PAGESPEED_API_KEY=         # Google PageSpeed Insights API key
OPENROUTER_API_KEY=        # OpenRouter API key

# Optional
DEFAULT_MODEL=google/gemini-2.0-flash-001  # Default AI model
```

For Streamlit Cloud, set these in Settings > Secrets as TOML format. For local development, use a `.env` file (loaded via python-dotenv).

## Available AI Models

| Key | Model ID | Use Case |
|-----|----------|----------|
| `gemini-flash` | `google/gemini-2.0-flash-001` | Fast, cost-effective (default) |
| `claude-sonnet` | `anthropic/claude-sonnet-4-5-20250514` | Deep reasoning, complex analysis |
| `gpt-4.1-mini` | `openai/gpt-4.1-mini` | Balanced performance and cost |

Models are defined in `OpenRouterClient.MODELS` in `src/ai/openrouter_client.py`.
