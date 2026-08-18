# OpenSpec Proposal: SEO, GEO (AI Engine Optimization), Local Knowledge Graph & Verified Socials (Stage 11)

- **Change ID**: `seo-geo-local-knowledge-graph-2026`
- **Author**: Contexia Core Architecture & SEO Taskforce
- **Date**: 2026-08-18
- **Status**: Implemented / Ready for Stage 11 Production Verification

## 1. Problem Statement
The public-facing portal and landing files (`index.html`, `landing.html`, `crear-empresa.html`) suffered from:
1. Missing `robots.txt` and `sitemap.xml`, limiting crawl discovery for both traditional search engines and Generative AI engines (ChatGPT Search, PerplexityBot, ClaudeBot).
2. Entity ambiguity in Google Knowledge Graph due to missing `LocalBusiness` / `FinancialService` Schema.org with exact coordinates (Envigado / Valle de Aburrá) and `sameAs` array.
3. Outdated phone links referencing personal lines instead of the official Taty / Chatwoot WhatsApp Bridge (`+57 310 622 9289`).
4. Lack of structured `FAQPage` Schema to answer seasonal Persona Natural (Renta 2026 / 1.400 UVT) and B2B PyME queries.

## 2. Proposed Changes
- **Structured Knowledge Graph**: Multi-layer Schema.org (`LocalBusiness`, `FinancialService`, `SoftwareApplication`, `FAQPage`) with geocoordinates (`6.17591, -75.59174`) and `sameAs` links to Facebook (`/contexia.onlinee`), Instagram (`/contexia.online/`), LinkedIn, and Google Search.
- **AI Engine Optimization (GEO/LLMO)**: Direct factual FAQ answering topes 1.400 UVT and cédula lookup.
- **WPO & Performance**: Added `<link rel="preconnect">` for Google Fonts, `decoding="async"`, `fetchpriority="high"` for LCP logo, and `loading="lazy"` for secondary images.
- **Crawlability**: Added `robots.txt` and `sitemap.xml` with proper priorities and indexing directives.
- **Contact Alignment**: Standardized all WhatsApp click-to-chat links to `+57 310 622 9289`.
