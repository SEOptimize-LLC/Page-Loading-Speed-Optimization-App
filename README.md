# Page Speed Optimization Agent

AI-powered page speed analysis and optimization tool for WordPress and Shopify sites. Combines Google PageSpeed Insights API v5 data with raw HTML analysis and curated expert knowledge to generate detailed, CMS-aware optimization reports with professional HTML/PDF output.

## Key Features

- **Google PageSpeed Insights API v5** integration with full mobile + desktop analysis
- **Raw HTML analysis** with BeautifulSoup for deep code-level issue detection
- **AI-powered recommendations** via OpenRouter (Gemini Flash, Claude Sonnet, GPT-4.1 Mini)
- **CMS-aware optimization** with WordPress and Shopify-specific advice
- **Professional HTML/PDF reports** with screenshots and visual diagnostics
- **White-label ready** with custom branding, logo, and colors
- **Curated knowledge base** with 6 expert-sourced markdown files (web.dev, WPJohnny, WPSpeedMatters, BS-DevShop)
- **Mobile-first analysis** with 90% focus on mobile performance
- **Core Web Vitals assessment** covering LCP, CLS, and INP
- **Issue severity classification** into Critical, Important, and Minor categories
- **Screenshot cropping** with severity-colored element highlighting
- **Implementation roadmap** with effort estimates and prioritized quick-wins

---

## How It Works

The analysis pipeline processes a URL through five stages:

1. **Data Collection** -- The URL is sent to the PageSpeed Insights API v5 for both mobile and desktop strategies. Simultaneously, the raw HTML is fetched and parsed with BeautifulSoup/lxml for code-level analysis that PSI may not catch (missing `fetchpriority`, lazy-loaded above-fold images, render-blocking scripts without `async`/`defer`, excessive inline CSS/JS, font loading issues, etc.).

2. **CMS Detection** -- WordPress and Shopify are detected through multiple signals: PSI stack packs, meta generator tags, CDN domain patterns (`cdn.shopify.com`, `/wp-content/`), JavaScript globals (`Shopify.theme`), and network request URL patterns. Known plugins (Elementor, WP Rocket, Yoast) and Shopify apps (Judge.me, Klaviyo, PageFly) are identified from network requests.

3. **Issue Classification & Severity Scoring** -- Every PSI opportunity, diagnostic, and HTML finding is classified as Critical, Important, or Minor based on potential savings, affected CWV metrics, and whether those metrics are currently in the "poor" range. Issues are mapped to specific Core Web Vitals (LCP, CLS, INP, FCP, TBT) and scored with a composite priority algorithm.

4. **AI-Powered Recommendations** -- The knowledge base selector matches detected audit IDs to relevant expert sections. A prompt is built with the full PSI data, HTML findings, CMS type, and selected knowledge base context. The AI model generates per-issue fix instructions with code examples, CMS-specific guidance, and effort estimates. A second AI call produces an executive summary and implementation roadmap.

5. **Report Generation** -- A Jinja2 HTML template renders the complete report with score gauges, CWV assessment cards, issue cards with screenshots, the executive summary, implementation roadmap, and page statistics. The report can be exported as PDF via WeasyPrint. White-label branding is applied through CSS custom properties.

---

## Setup

### Prerequisites

- Python 3.9+
- Google PageSpeed Insights API key (free from Google Cloud Console)
- OpenRouter API key (for AI-powered recommendations)

### Local Development

```bash
# Clone or download the project
cd "Page Loading Speed Optimization Agent"

# Create and activate a virtual environment (recommended)
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Copy the example env file and add your API keys
cp .env.example .env
# Edit .env with your PAGESPEED_API_KEY and OPENROUTER_API_KEY

# Run the app
streamlit run app.py
```

### Streamlit Cloud Deployment

1. Push the project to a GitHub repository
2. Go to [share.streamlit.io](https://share.streamlit.io)
3. Connect your repository and select the branch
4. Set `app.py` as the main file path
5. Add secrets in Streamlit Cloud settings (Settings > Secrets):
   ```toml
   PAGESPEED_API_KEY = "your-google-psi-api-key"
   OPENROUTER_API_KEY = "your-openrouter-api-key"
   DEFAULT_MODEL = "google/gemini-2.0-flash-001"  # optional
   ```
6. Deploy -- `packages.txt` is already included for WeasyPrint system dependencies (libcairo2, libpango, etc.)

---

## API Keys Setup

### Google PageSpeed Insights API Key

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select an existing one
3. Navigate to **APIs & Services > Library**
4. Search for and enable **PageSpeed Insights API**
5. Go to **APIs & Services > Credentials**
6. Click **Create Credentials > API Key**
7. Copy the key and add it to your `.env` file as `PAGESPEED_API_KEY`

The PageSpeed Insights API is free with a generous quota (25,000 requests per day).

### OpenRouter API Key

1. Go to [openrouter.ai](https://openrouter.ai/)
2. Create an account and sign in
3. Navigate to the **API Keys** section
4. Click **Create Key**
5. Copy the key and add it to your `.env` file as `OPENROUTER_API_KEY`

OpenRouter provides access to multiple AI models through a single API. The default model (Gemini 2.0 Flash) is fast and cost-effective for bulk analysis.

---

## Project Structure

```
Page Loading Speed Optimization Agent/
|
|-- app.py                          # Main Streamlit entry point; orchestrates the full pipeline
|-- requirements.txt                # Python dependencies
|-- packages.txt                    # System packages for Streamlit Cloud (WeasyPrint deps)
|-- .env.example                    # Environment variable template
|-- .streamlit/
|   |-- config.toml                 # Streamlit theme and server configuration
|
|-- src/
|   |-- models/
|   |   |-- speed_issue.py          # Severity, CWVMetric, CWVStatus, SpeedIssue, CMSInfo dataclasses
|   |   |-- analysis_result.py      # AnalysisResult and PageStats dataclasses
|   |
|   |-- collectors/
|   |   |-- pagespeed_client.py     # PSI API v5 client with full response parsing (14 parse methods)
|   |   |-- html_analyzer.py        # Raw HTML fetching + BeautifulSoup analysis for code-level issues
|   |   |-- screenshot_processor.py # Full-page screenshot cropping and severity-colored highlighting
|   |
|   |-- analyzers/
|   |   |-- cms_detector.py         # Multi-signal CMS detection (WordPress/Shopify/Wix/Squarespace/etc.)
|   |   |-- issue_classifier.py     # Severity classification, CWV mapping, and priority scoring
|   |   |-- resource_analyzer.py    # Network request analysis, third-party impact, compression/cache gaps
|   |
|   |-- ai/
|   |   |-- knowledge_base.py       # Loads KB markdown files, selects relevant sections by audit ID
|   |   |-- prompt_builder.py       # Constructs system + user prompts for issue analysis and exec summary
|   |   |-- openrouter_client.py    # OpenRouter API client with JSON parsing and streaming support
|   |
|   |-- reports/
|       |-- report_generator.py     # Jinja2 HTML report generation with white-label support
|       |-- pdf_converter.py        # WeasyPrint HTML-to-PDF conversion
|       |-- templates/
|           |-- speed_report.html   # Full report HTML template with macros and responsive layout
|           |-- report_styles.css   # Professional CSS with CSS custom properties for branding
|
|-- knowledge-base/                 # 6 curated expert knowledge base files
|   |-- pagespeed-insights-api.md
|   |-- performance-optimization-techniques.md
|   |-- wordpress-optimization.md
|   |-- wpspeedmatters-insights.md
|   |-- shopify-and-inp-cases.md
|   |-- shopify-liquid-patterns.md
|
|-- utils/
    |-- formatting.py               # Helpers for bytes, milliseconds, scores, and URL truncation
    |-- url_utils.py                # URL validation, normalization, domain extraction
```

---

## Knowledge Base

The `knowledge-base/` directory contains 6 curated markdown files that the AI uses as expert reference material when generating recommendations. The knowledge base selector (`knowledge_base.py`) matches detected audit IDs to relevant sections, ensuring the AI receives targeted context rather than the full corpus.

| File | Source | Coverage |
|------|--------|----------|
| `pagespeed-insights-api.md` | Google PSI API docs | Complete PSI API v5 reference -- audit IDs, metric definitions, response structure |
| `performance-optimization-techniques.md` | web.dev | HTML performance, image optimization, font loading, JavaScript/CSS strategies, lazy loading, resource hints |
| `wordpress-optimization.md` | WPJohnny.com | WordPress-specific speed optimization -- plugin recommendations, theme performance, PHP tuning, caching strategies |
| `wpspeedmatters-insights.md` | WPSpeedMatters.com | Advanced WordPress performance -- hosting comparisons, autoptimize settings, database optimization, CDN configuration |
| `shopify-and-inp-cases.md` | Various | Shopify performance optimization and INP case studies -- app impact analysis, theme optimization, Shopify-specific CWV fixes |
| `shopify-liquid-patterns.md` | BS-DevShop.com | Copy-paste-ready Shopify Liquid code patterns for performance -- lazy loading, critical CSS, section rendering optimization |

---

## Configuration

### AI Model Selection

The sidebar in the Streamlit UI allows selecting from three AI models via OpenRouter:

| Model | ID | Best For |
|-------|----|----------|
| **Gemini 2.0 Flash** (default) | `google/gemini-2.0-flash-001` | Fast analysis, cost-effective, bulk operations |
| **Claude Sonnet** | `anthropic/claude-sonnet-4-5-20250514` | Deep reasoning, complex performance analysis |
| **GPT-4.1 Mini** | `openai/gpt-4.1-mini` | Balanced performance and cost |

### White-Label Settings

Reports support full white-label customization through the sidebar:

- **Company Name** -- Appears in the report header and footer
- **Company Logo** -- URL or data URI displayed in the report header
- **Brand Color** -- Hex color applied to all accent elements via CSS custom properties
- **Contact Email** -- Displayed in the report footer

### Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `PAGESPEED_API_KEY` | Yes | Google PageSpeed Insights API key |
| `OPENROUTER_API_KEY` | Yes | OpenRouter API key for AI model access |
| `DEFAULT_MODEL` | No | Default AI model ID (defaults to `google/gemini-2.0-flash-001`) |

---

## Tech Stack

| Component | Technology |
|-----------|-----------|
| Web Framework | [Streamlit](https://streamlit.io/) |
| Page Speed Data | [Google PageSpeed Insights API v5](https://developers.google.com/speed/docs/insights/v5/get-started) |
| AI Model Routing | [OpenRouter API](https://openrouter.ai/) |
| HTML Parsing | [BeautifulSoup4](https://www.crummy.com/software/BeautifulSoup/) + [lxml](https://lxml.de/) |
| Image Processing | [Pillow](https://python-pillow.org/) |
| Report Templates | [Jinja2](https://jinja.palletsprojects.com/) |
| PDF Generation | [WeasyPrint](https://weasyprint.org/) |
| HTTP Client | [Requests](https://docs.python-requests.org/) |
| Runtime | Python 3.9+ |

---

## License

Private / Internal use.
