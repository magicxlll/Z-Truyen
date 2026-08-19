# Z-Truyen X3 — Master Engineering Specification

**Version:** 1.0.0
**Date:** 2026-08-13
**Status:** Proposed baseline / execution specification
**Primary target:** Xteink X3 International
**Primary firmware base:** CrossVi 1.1.2 (preferred for native integration), with CrossPoint 1.5.0 retained as the upstream compatibility/reference baseline
**Project codename:** Z-Truyen
**Original source project:** `Z-Truyenviet.koplugin` (KOReader plugin)
**Primary purpose:** Build a reliable Vietnamese online-story discovery/download experience for Xteink X3 without compromising device stability, while allowing eventual public/community deployment and optional cloud hosting.

---

## 0. Executive Summary

Z-Truyen is a multi-stage system that converts the existing KOReader-only online story workflow into an X3-compatible service.

The project MUST NOT begin by modifying or flashing the X3 firmware.

The recommended architecture is:

```text
                         INTERNET
                             |
                             v
                  +----------------------+
                  | Z-Truyen Backend     |
                  |                      |
                  | - source adapters    |
                  | - search aggregator  |
                  | - scraper/parser     |
                  | - EPUB builder       |
                  | - cover processor    |
                  | - cache              |
                  | - OPDS/API           |
                  +----------+-----------+
                             |
                       HTTPS / OPDS
                             |
              +--------------+--------------+
              |                             |
              v                             v
       X3 CrossVi                    KOReader devices
       OPDS client                   Android/Kobo/Kindle/etc.
              |
              v
       EPUB downloaded to SD
              |
              v
       CrossVi/CrossPoint reader
```

The system MUST be developed in the following order:

1. Analyze and normalize the existing `Z-Truyenviet.koplugin` source.
2. Build an independent backend locally.
3. Implement OPDS 1.x compatibility.
4. Make the backend work with an unmodified CrossVi/CrossPoint X3.
5. Build a desktop/simulator integration test harness.
6. Add automated regression tests.
7. Only after the service is stable, consider a thin native X3 UI feature.
8. Only after simulator acceptance, perform physical X3 testing.
9. Only after physical X3 acceptance, publish a firmware-integrated release.
10. Only after local/server stability, deploy the backend to cloud hosting.

The project SHALL prefer a thin X3 client and a powerful server-side scraper.

The project SHALL NOT implement HTML scraping, JavaScript execution, anti-bot handling, or EPUB generation directly inside the X3 firmware unless a future engineering review explicitly approves it.

---

# 1. Objectives

## 1.1 Functional objectives

The final system SHOULD allow an X3 user to:

1. Connect X3 to Wi-Fi.
2. Open a Z-Truyen library through OPDS.
3. Browse categories/sources.
4. Search stories by title/author/keyword.
5. Open story metadata.
6. Browse chapters.
7. Select one or more chapters for download.
8. Download generated EPUB content from the server to X3 SD storage.
9. Open downloaded EPUB using the native X3 reader.
10. Continue reading offline after download.
11. Re-download/update chapters without creating duplicate books.
12. Preserve stable filenames/document identities suitable for KOReader-compatible progress synchronization.
13. Optionally use the same Z-Truyen backend from KOReader devices.

## 1.2 Non-functional objectives

The system MUST prioritize:

- X3 stability over feature count.
- No firmware modification during MVP.
- Offline reading after download.
- Low memory use on X3.
- Deterministic EPUB output.
- Stable document identity.
- Cache efficiency.
- Source adapter isolation.
- Ability to update a website scraper without updating X3 firmware.
- Reproducible builds.
- Automated tests before physical flashing.
- Easy self-hosting.
- Optional cloud deployment.

## 1.3 Explicit non-goals for MVP

The MVP MUST NOT attempt to:

- port the entire KOReader runtime to X3;
- execute `.koplugin` Lua code on X3;
- create a generic X3 plugin runtime;
- implement a web browser on X3;
- render arbitrary HTML directly on X3;
- stream pages live while reading;
- scrape websites directly from X3;
- require an always-on server for already-downloaded books;
- modify the X3 bootloader;
- replace CrossVi/CrossPoint's EPUB reader;
- implement server-side KOSync as part of the story backend.

---

# 2. Xteink X3 Hardware Baseline

## 2.1 Official published specifications

The official Xteink X3 product page currently lists:

- Display: 3.7-inch E-Ink class display.
- Pixel density: 259 PPI.
- Physical dimensions: 97.6 x 63.7 x 5.1 mm.
- Weight: 58 g.
- Storage: 16 GB microSD supplied; up to 256 GB expansion stated by Xteink.
- Officially listed document formats: EPUB and TXT on the dedicated X3 page; the comparison page also lists EPUB/TXT/MOBI/PDF/JPG/PNG across the current product family, so firmware-level support MUST be treated as authoritative for the actual device build.
- Battery: 650 mAh.
- Connectivity: 2.4 GHz Wi-Fi and Bluetooth.
- Inputs: physical buttons; gyroscope-based page turn is supported by current custom firmware.
- Charging/data: magnetic pogo-pin cable on current retail package.
- SoC: ESP32-C3 is confirmed by the CrossPoint/CrossVi ecosystem and community hardware analysis.
- The X3 board is known to contain a QMI8658 IMU, DS3231 RTC and BQ27220 battery fuel gauge in analyzed hardware revisions.

Official sources:

- https://www.xteink.com/products/xteink-x3
- https://www.xteink.com/pages/compare-our-products

Community/reverse-engineering reference:

- https://www.reddit.com/r/xteinkereader/comments/1r2x5gj/x3_firmware_analysis_gpio_and_epd/

## 2.2 Hardware constraints that directly affect Z-Truyen

The CrossPoint documentation states that the ESP32-C3 has roughly 380 KB usable RAM available to the firmware, and CrossPoint aggressively caches to SD to minimize RAM use.

Therefore:

- X3 MUST NOT parse large arbitrary HTML documents if server-side parsing can avoid it.
- X3 MUST NOT perform EPUB generation.
- X3 SHOULD receive final EPUB bytes rather than large raw HTML payloads.
- X3 networking SHOULD be short-lived and bounded.
- Large response bodies MUST be streamed/handled safely.
- The native reader MUST remain the source of truth for rendering.

Reference:
https://github.com/crosspoint-reader/crosspoint-reader

## 2.3 Hardware revision risk

CrossVi explicitly warns that newer X3 production revisions may use different display/power hardware and that new X3 units may use the UC8279 display controller. CrossVi 1.1.2 can detect it, but the project states that support on new hardware still requires validation.

Therefore:

- BEFORE ANY PHYSICAL FLASH, the exact hardware revision of the user's X3 MUST be identified where possible.
- A new X3 that has never run custom firmware MUST remain on stock until compatibility has been checked.
- The SD card MUST be backed up.
- The project MUST maintain a known-good recovery path.

Reference:
https://github.com/tvhdc/crossvi

---

# 3. Firmware Baselines

## 3.1 CrossPoint 1.5.0

Repository:
https://github.com/crosspoint-reader/crosspoint-reader

Release:
https://github.com/crosspoint-reader/crosspoint-reader/releases/tag/v1.5.0

Key relevant capabilities:

- ESP32-C3 X3/X4 firmware.
- EPUB 2/3 reader.
- TXT, BMP, XTC/XTCH support.
- Custom fonts.
- OPDS browser with saved servers, search, pagination and direct download.
- Wi-Fi file transfer/web UI.
- WebDAV and Calibre wireless workflows.
- OTA update support.
- KOReader progress sync.
- X3 gyroscope tilt page turning.
- Offline StarDict dictionary support.
- Background indexing of large books.
- Memory/CSS parser improvements for complex EPUBs.

CrossPoint 1.5.0 was released 2026-08-07.

Relevant release improvements include faster large-book opening, memory/CSS fixes and more accurate KOReader synchronization. The project documents an XPath-based progress mapping approach rather than only chapter/page offsets.

## 3.2 CrossVi 1.1.2

Repository:
https://github.com/tvhdc/crossvi

Release:
https://github.com/tvhdc/crossvi/releases/tag/v1.1.2

CrossVi is a fork of CrossPoint. It extends CrossPoint with:

- richer library UX;
- reading statistics;
- configurable Home layouts;
- bookmarks and highlights;
- custom typography and fonts;
- Vietnamese interface;
- Vietnamese-interface English vocabulary quiz;
- Wi-Fi;
- OPDS;
- Calibre/WebDAV;
- KOReader Sync;
- OTA;
- Quick Resume;
- clock and sleep screens;
- transactional storage safeguards.

CrossVi 1.1.2 was released 2026-08-11.

Critical warning:

The CrossVi repository explicitly says the firmware has not yet been validated on every newer X3/X4 hardware revision. New X3 production units may use UC8279. DO NOT ignore this warning.

## 3.3 Firmware selection policy for this project

The project SHALL treat:

- CrossVi 1.1.2 as the preferred native-integration development base because it has the UX direction and features best aligned with Z-Truyen.
- CrossPoint 1.5.0 as the upstream/reference compatibility baseline because it has a larger upstream community, extensive simulator support, and the most explicit published KOReader XPath mapping design.

MVP must work WITHOUT either firmware fork being modified.

Native integration must be isolated in a dedicated feature/module and must be easy to revert.

---

# 4. KOReader and KOSync Compatibility Model

## 4.1 Important architectural fact

X3 running CrossPoint or CrossVi does NOT run KOReader.

CrossPoint/CrossVi only implement compatibility with the KOReader synchronization protocol.

Therefore:

- `.koplugin` files cannot be copied to X3 and executed.
- KOReader Lua APIs are not available on X3.
- KOSync is a protocol/service compatibility feature, not KOReader itself.

## 4.2 KOSync concept

KOSync primarily synchronizes reading progress/location metadata. It does NOT automatically synchronize:

- EPUB files;
- highlights in every case;
- annotations database;
- font settings;
- UI themes;
- arbitrary application state;
- reading statistics databases unless a particular product implements its own extension.

A typical flow is:

```text
Device A
  -> identify document
  -> calculate progress/location
  -> upload progress
  -> sync server
  -> Device B requests remote progress
  -> map remote position to local document
  -> move reading cursor
```

## 4.3 Document identity

The system SHOULD prefer deterministic filename-based document identity for Z-Truyen-generated content when cross-device compatibility is desired.

Suggested canonical filename:

```text
ztruyen__{source}__{book_id}__{chapter_or_bundle_id}.epub
```

The book ID and chapter ID MUST be stable across refreshes.

Binary/content-based identity can be supported where byte-identical files are guaranteed, but filename identity is safer for content generated independently on multiple devices.

## 4.4 Position mapping

CrossPoint's documented current strategy maps internal X3 positions:

- `spineIndex`
- `pageNumber`
- `totalPages`

to KOReader sync payloads containing:

- `progress` (XPath-like location)
- `percentage`

CrossPoint's current design uses `ProgressMapper` and `ChapterXPathIndexer` to attempt element-level XPath mapping and falls back to a synthetic chapter path if exact mapping fails.

Reference:
https://github.com/crosspoint-reader/crosspoint-reader/discussions/61

This is important because page numbers do not mean the same thing on two readers with different fonts/screens/layouts.

Z-Truyen SHOULD therefore generate semantically clean EPUB XHTML with stable paragraph/chapter structure rather than highly dynamic HTML.

---

# 5. Source Project: Z-Truyenviet.koplugin

## 5.1 Original repository

https://github.com/magicxlll/Z-Truyenviet.koplugin

The repository is a pure-Lua KOReader plugin and currently identifies itself as “Truyện Việt cho KOReader”. It is forked from `hashi173/truyenviet.koplugin`.

## 5.2 Relevant capabilities of the existing plugin

The current plugin contains substantial reusable domain logic, including:

- multi-source story discovery;
- story search;
- chapter retrieval;
- chapter download;
- HTML/EPUB generation for text novels;
- CBZ generation for comic/manga sources;
- cover handling;
- source registry;
- reusable scraping rules;
- a “Super Scraper Engine” that can analyze OpenGraph/JSON-LD/HTML and generate reusable source rules.

The plugin explicitly says text stories are saved as HTML/EPUB and comics as CBZ, then opened by KOReader's existing reader.

Therefore the correct migration approach is NOT “port the Lua UI”.

The migration target is:

```text
Existing plugin
   |
   +-- source adapters ---------> backend source adapters
   +-- search service ----------> backend search service
   +-- chapter downloader ------> backend fetcher
   +-- document builder ---------> backend EPUB builder
   +-- cover cache --------------> backend cache
   +-- KOReader UI --------------> OPDS/native X3 UI
   +-- KOReader file open -------> X3 EPUB download/open
```

## 5.3 Legal/safety boundary

The project is a client/aggregation framework. Individual source websites may have their own terms, robots rules, authentication requirements, copyright restrictions, or anti-bot mechanisms.

Z-Truyen MUST:

- not bypass authentication or paywalls;
- not defeat CAPTCHAs or explicit technical access controls;
- respect source site terms where applicable;
- support user-configurable source enable/disable;
- make source adapters independently removable.

The project should be positioned as a technical aggregation client and self-hostable tool, not as a piracy service.

---

# 6. System Architecture

## 6.1 Canonical architecture

```text
                         +---------------------+
                         |   Source websites   |
                         |  A / B / C / ...    |
                         +----------+----------+
                                    |
                                HTTPS fetch
                                    |
                                    v
+-----------------------+   +-------------------------+
|  X3 / X4 / KOReader   |<->| Z-Truyen Backend        |
|                       |   |                         |
| OPDS client           |   | API / OPDS              |
| EPUB reader           |   | Source registry         |
| Local SD storage      |   | Search                  |
| KOSync client         |   | Fetch / parse           |
+-----------------------+   | EPUB builder            |
                            | Cover processing         |
                            | Cache                   |
                            | Auth / rate limits      |
                            +------------+------------+
                                         |
                                 +-------+-------+
                                 |               |
                                 v               v
                              Metadata         Object cache
                              DB               EPUB/covers
```

## 6.2 Separation of responsibilities

### X3 firmware

MUST be responsible for:

- Wi-Fi connectivity;
- UI/navigation;
- OPDS browsing;
- HTTP download;
- SD storage;
- EPUB reading;
- bookmarks/highlights if supported by firmware;
- KOSync;
- battery/power management.

MUST NOT be responsible for:

- web scraping;
- HTML/CSS/JS interpretation of arbitrary source sites;
- browser automation;
- EPUB generation from arbitrary HTML;
- anti-bot logic;
- source-specific DOM selectors.

### Backend

MUST be responsible for:

- source adapters;
- search aggregation;
- source-specific parsing;
- chapter extraction;
- content normalization;
- EPUB generation;
- cover normalization;
- caching;
- rate limiting;
- authentication;
- health/status APIs;
- optional content freshness checks.

---

# 7. OPDS Contract

## 7.1 Protocol target

Target OPDS 1.x compatibility first because it is directly aligned with the current CrossPoint/CrossVi workflow.

Minimum endpoints:

```text
GET /opds
GET /opds/search?q=<query>
GET /opds/category/<id>
GET /opds/book/<book_id>
GET /opds/book/<book_id>/chapters
GET /opds/download/<artifact_id>
```

The server MAY expose human-oriented web pages separately, but OPDS is the contract consumed by X3.

## 7.2 OPDS response design

Entries SHOULD contain:

- stable `id`;
- title;
- author when known;
- cover image;
- updated timestamp;
- content summary;
- acquisition/download link;
- navigation/subsection link where applicable.

## 7.3 Stable IDs

Never use scraped display text as the sole canonical ID.

Use:

```text
source_id + source_book_id
source_id + source_book_id + source_chapter_id
```

Normalize into an opaque but deterministic backend ID.

---

# 8. EPUB Generation Contract

## 8.1 EPUB strategy

The backend MUST generate standards-compliant EPUB 3 or EPUB 2-compatible packages accepted by current CrossVi/CrossPoint readers.

MVP SHOULD use one chapter per EPUB artifact because:

- X3 RAM is limited;
- large mega-EPUBs create indexing and memory pressure;
- chapter download/retry is easier;
- source updates are simpler.

A later “bundle 10/25/50 chapters per EPUB” feature MAY be implemented.

## 8.2 EPUB internal structure

Recommended:

```text
mimetype
META-INF/container.xml
OEBPS/
  content.opf
  nav.xhtml
  text/
    chapter.xhtml
  images/
    cover.jpg
    ...
```

## 8.3 Clean XHTML requirements

Generated chapter HTML MUST:

- use UTF-8;
- have explicit `<p>` elements for paragraphs;
- avoid unnecessary nested containers;
- use stable IDs only where necessary;
- avoid dynamic JS;
- avoid inline scripts;
- avoid external resources;
- use a small, deterministic CSS file;
- preserve paragraph boundaries;
- preserve chapter title.

Reason: clean structure improves rendering and increases the chance of precise CrossPoint <-> KOReader location mapping.

## 8.4 Filename identity

Canonical filename example:

```text
ztruyen__truyenfull__12345__chapter-0678.epub
```

Filename rules MUST:

- be ASCII-safe where practical;
- avoid illegal path characters;
- preserve a stable machine identifier;
- include a human-readable title only as optional metadata.

---

# 9. Backend API

## 9.1 Technology recommendation

MVP backend:

- Python 3.12+
- FastAPI
- httpx
- selectolax or BeautifulSoup/lxml
- ebooklib or a dedicated EPUB builder
- Pillow where needed for covers
- Pydantic
- pytest
- SQLite for local development

Potential later deployment:

- Docker
- Cloud Run
- Cloudflare R2
- Cloudflare D1 or PostgreSQL

## 9.2 Internal modules

```text
ztruyen-server/
├── app/
│   ├── main.py
│   ├── config.py
│   ├── api/
│   │   ├── opds.py
│   │   ├── books.py
│   │   ├── chapters.py
│   │   ├── search.py
│   │   └── health.py
│   ├── domain/
│   │   ├── models.py
│   │   ├── ids.py
│   │   └── content.py
│   ├── sources/
│   │   ├── base.py
│   │   ├── registry.py
│   │   ├── source_001.py
│   │   └── ...
│   ├── fetcher/
│   │   ├── http.py
│   │   ├── retries.py
│   │   └── normalization.py
│   ├── epub/
│   │   ├── builder.py
│   │   ├── css.py
│   │   └── validation.py
│   ├── cache/
│   │   ├── metadata.py
│   │   ├── objects.py
│   │   └── keys.py
│   ├── auth/
│   └── telemetry/
├── tests/
├── fixtures/
├── scripts/
├── Dockerfile
├── docker-compose.yml
└── README.md
```

## 9.3 Source adapter interface

Every source adapter MUST implement an interface equivalent to:

```python
class SourceAdapter(Protocol):
    id: str
    name: str

    async def search(self, query: str, page: int = 1) -> list[BookSummary]: ...
    async def get_book(self, book_id: str) -> Book: ...
    async def list_chapters(self, book_id: str, page: int = 1) -> list[Chapter]: ...
    async def get_chapter(self, book_id: str, chapter_id: str) -> ChapterContent: ...
```

Source-specific selectors/URLs MUST remain inside the source adapter.

No source-specific code may exist in OPDS rendering code.

## 9.4 Technical Scraping Specifications for Priority Sources

Extracted and ported from reference project `Z-Truyenviet.koplugin`:

### 9.4.1 Source `storya.click` (Adapter ID: `storyaclick`)
- **Type**: Next.js Single Page Application (SPA) with native JSON REST API endpoints.
- **Base URL**: `https://storya.click`
- **API Base**: `https://storya.click/api/v1`
- **Request Headers**:
  - `Accept: application/json`
  - `User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36`
- **Endpoints & Schemas**:
  - **Search**: `GET /stories/search?q={query}` -> returns JSON `{ data: [{ title, slug, coverUrl, ... }] }`
  - **Hot/Latest**: `GET /stories/hot?page={page}&limit=20`, `GET /stories?page={page}&limit=20`
  - **Genres**: `GET /genres` and `GET /genres/slug/{slug}`
  - **Story Details**: `GET /stories/{story_slug}` -> returns `{ data: { title, description, rewrittenDescription, author: { name }, status, genres: [...] } }`
  - **Chapter List**: `GET /chapters/story/{story_slug}?page={page}&limit=100&minimal=true` -> returns `{ data: [{ title, order, slug, ... }], meta: { totalPages } }`
  - **Chapter Content**: `GET /chapters/{story_slug}/{chap_slug}` -> returns `{ data: { title, content, rewrittenContent, rawContent } }`
- **Content Normalization**:
  - Check if `rewrittenContent` / `content` contains `<p>` tags. If pure plain text with line breaks (`\n`), replace `\n\n` with `<br><br>` and wrap in `<div>`.

### 9.4.2 Source `akaytruyen.com` (Adapter ID: `akaytruyen`)
- **Type**: Laravel-based dynamic HTML website with JSON chapter endpoint.
- **Base URL**: `https://akaytruyen.com`
- **Authentication**:
  - Supports user login for VIP-locked chapters (`supports_login = true`).
  - Login Endpoint: `POST /login`
  - Body: `_token={csrf_token}&email={username}&password={password}&remember=1` (CSRF token extracted from `GET /login` HTML `name="_token"` or `name="csrf-token"`).
  - Session cookies (`set-cookie`) MUST be stored and sent in `Cookie` header for subsequent requests.
- **Scraping Rules**:
  - **Search**: `GET /tim-kiem?keyword={query}` -> Parse `<a class="title-text-story">` or `<a class="story-name">`, cover from `data-src` or `src`.
  - **Story Details**: Description from `<div class="desc" itemprop="description">`, author from `itemprop="author"`.
  - **Chapter List**: Dedicated JSON API `GET {story_url}/search-chapters?search=&page={page}` returning `{ "html": "..." }` containing `<a class="chapter-link-mobile">`. Fallback: `GET {story_url}?page={page}`. Total pages from `<input class="jump-input" max="N">`.
  - **Chapter Content**:
    - Check VIP Lock: If HTML contains `<div class="access-denied-container">` or "Chương này dành cho tài khoản VIP", trigger login/re-auth or raise VIP lock error.
    - Extract Title: `<h1 class="custom-text">` or `<h1/h2>`
    - Extract Content: Text inside `<div id="chapter-content">` up to `<div class="chapter-nav">`. Clean HTML via standard sanitizer.

### 9.4.3 Source `conduongbachu.com` (Adapter ID: `conduongbachu`)
- **Type**: WordPress CMS website with WP REST API (`wp-json`).
- **Base URL**: `https://conduongbachu.com`
- **Story Categories Mapping**:
  - Category 3 (`cat_id=3`): Main Story "Con Đường Bá Chủ (Chính Truyện)" (`slug="chapter-truyen"`)
  - Category 12 (`cat_id=12`): Side Story "Ngoại Truyện: Bất Hủ Thần Chiến" (`slug="ngoai-truyen"`)
  - Category 14 (`cat_id=14`): Side Story "Ngoại Truyện: Vạn Đạo Thần Chủ" (`slug="ngoai-truyen-van-dao-than-chu"`)
  - Category 15 (`cat_id=15`): Side Story "Ngoại Truyện: Chúa Tể Chi Lộ" (`slug="ngoai-truyen-chua-te-chi-lo"`)
- **Scraping Rules**:
  - **Chapter Indexing**:
    - WP REST API: `GET /wp-json/wp/v2/posts?categories={cat_id}&per_page=100&_fields=link,title&page={page}&order=asc&orderby=date`
    - Response Headers: Read `X-WP-Total` (total chapter posts) and `X-WP-TotalPages` (total API pages).
    - Parse JSON posts: link, rendered title (`title.rendered`).
    - Filter chapters by matching "Chương", "/chuong-", or leading chapter numbers (e.g., "3399: VÔ ĐỀ").
  - **Chapter Content**:
    - `GET {chapter_url}`
    - Title: `<h1 class="entry-title">`
    - Content Region: `<div class="entry-content">` up to `<nav id="nav-below">`.
    - Filter noise paragraphs: Remove elements with class `post-tts` or text containing "Nếu muốn tìm chương khác".

---

# 10. Authentication and Abuse Protection


## 10.1 MVP local mode

Local/self-hosted mode may support no authentication if bound to LAN only.

## 10.2 Public/cloud mode

Public deployments MUST support:

- device/user API token;
- per-user rate limits;
- source-level concurrency limits;
- request logging with privacy-aware retention;
- maximum chapter size;
- maximum generated EPUB size;
- cache-first behavior;
- circuit breaker on failing sources.

## 10.3 Device token

Recommended header:

```http
Authorization: Bearer zt_<token>
```

The X3 native client must be able to store the token securely enough for the device model available; do not assume hardware-secure storage.

---

# 11. Local Development Target: Mac mini M4

The user's Mac mini M4 is the preferred primary development host because it is already online 24/7.

It SHALL be able to run:

```text
Docker
  ├─ Z-Truyen backend
  ├─ local SQLite
  ├─ local object cache
  └─ optional mock sources
```

Local development URL examples:

```text
http://127.0.0.1:8080
http://192.168.x.x:8080/opds
```

The local server MUST be fully functional before cloud deployment begins.

---

# 12. Cloud Deployment Strategy

## 12.1 Preferred cloud architecture

Recommended public architecture:

```text
                 Custom domain
                       |
                       v
                 Cloudflare DNS
                       |
                       v
                 Cloud Run backend
                       |
            +----------+----------+
            |                     |
            v                     v
        Metadata DB           Cloudflare R2
        D1/Postgres           EPUB/covers/cache
```

## 12.2 Why not make Cloudflare Workers the full scraper runtime

Workers Free currently provides 100,000 requests/day but only 10 ms CPU/request and 50 subrequests/request.

This is excellent for:

- routing;
- authentication;
- lightweight OPDS formatting;
- cache lookups;
- rate limiting;

but it is not the preferred main runtime for a CPU-heavy parser/EPUB generation workload.

Reference:
https://developers.cloudflare.com/workers/platform/limits/

## 12.3 Cloudflare D1

Current documented Workers Free limits include:

- 10 databases/account;
- 500 MB/database;
- 5 GB total storage/account;
- 5 million rows read/day;
- 100,000 rows written/day.

Reference:
https://developers.cloudflare.com/d1/platform/limits/
https://developers.cloudflare.com/d1/platform/pricing/

D1 SHOULD store:

- source metadata;
- books;
- chapters;
- cache metadata;
- users/devices;
- timestamps;
- source adapter status.

D1 MUST NOT store the actual EPUB binary blobs if R2 is available.

## 12.4 Cloudflare R2

Current documented free monthly allowance for Standard storage includes:

- 10 GB-month storage;
- 1 million Class A operations/month;
- 10 million Class B operations/month;
- Internet egress free.

Reference:
https://developers.cloudflare.com/r2/pricing/

R2 SHOULD store:

- generated EPUB files;
- normalized cover images;
- optional text cache;
- optional source snapshots for debugging, only if legally/operationally appropriate.

## 12.5 Cloud Run

Cloud Run is the preferred execution environment for the backend because the application is naturally containerized and can run Python parsing/EPUB libraries.

Current Cloud Run pricing documentation lists an always-free tier; depending on billing model it includes substantial monthly CPU/RAM allowances and request-based free usage.

Reference:
https://cloud.google.com/run/pricing

The project MUST configure budget alerts before public deployment.

## 12.6 Render/Koyeb

Render Free is acceptable for prototypes but NOT preferred for the production baseline because:

- Free services spin down after 15 minutes idle;
- wake-up takes about one minute;
- local files are ephemeral.

Reference:
https://render.com/docs/free

Koyeb may be used for experiments, but the project SHOULD NOT depend on a low-resource free instance for the main production scraper.

---

# 13. Domain Strategy

Development:

- use local IP or platform-generated hostname.

Pilot:

- use a dedicated subdomain, e.g. `opds.example.com`.

Production:

- use a custom domain behind Cloudflare.

The project MUST keep service URLs configurable. Firmware MUST NOT hard-code a single global domain.

---

# 14. Self-Hosting and Community Distribution

The project SHOULD support two distribution modes.

## 14.1 Hosted demo/community service

Example:

```text
https://opds.example.com
```

Advantages:

- zero installation for users;
- simple X3 setup.

Risks:

- one public scraper IP can be rate-limited/blocked;
- operating costs scale;
- source site terms must be reviewed;
- abuse can affect every user.

## 14.2 Self-hosted mode (preferred long-term OSS model)

Distribute:

- Docker image;
- docker-compose file;
- macOS app/launcher if practical;
- Windows package if practical;
- Linux instructions.

Example:

```text
docker compose up -d
```

Then show:

```text
OPDS URL: http://192.168.1.20:8080/opds
```

This is the community distribution model most analogous to a KOReader plugin in terms of independence: each user runs their own backend.

---

# 15. Remote Home Hosting

For a user running Z-Truyen on a home Mac mini/NAS 24/7:

Preferred architecture:

```text
X3 (anywhere)
    |
    | HTTPS / secure tunnel
    v
Cloudflare / Tailscale
    |
    v
Mac mini
    |
    v
Z-Truyen backend
```

Tailscale's current Personal plan allows 6 free users in one tailnet; it also has a community-on-GitHub free program for eligible open-source projects.

Reference:
https://tailscale.com/docs/reference/free-plans-discounts

Do not require users to expose random router ports directly unless explicitly needed.

---

# 16. Native X3 Integration Strategy

## 16.1 MVP: no firmware modification

The first usable version MUST use the existing CrossVi/CrossPoint OPDS feature.

User workflow:

```text
X3
 -> Wi-Fi
 -> Settings / OPDS
 -> Add Z-Truyen server
 -> Browse/search
 -> Select book
 -> Select chapter
 -> Download EPUB
 -> Open EPUB
```

No custom firmware is required for this stage.

## 16.2 Native phase

Only after the backend is proven should the project create a thin native X3 feature.

Suggested UI:

```text
Home
  └─ Z-Truyen
       ├─ Search
       ├─ Sources
       ├─ Recent
       ├─ Favorites
       └─ Downloads
```

The native client SHOULD call backend APIs, not scrape sites.

## 16.3 No plugin runtime requirement

The project MUST NOT create a generic dynamic native plugin framework as part of the first native integration.

A generic plugin runtime increases:

- ABI complexity;
- memory pressure;
- security exposure;
- SD/runtime management complexity;
- regression surface;
- firmware recovery risk.

If a plugin framework is ever desired, it must be a separate project with its own specification.

---

# 17. Simulator Strategy

## 17.1 CrossPoint Simulator

Repository:
https://github.com/crosspoint-reader/crosspoint-simulator

The simulator compiles CrossPoint-based firmware natively and renders the E-Ink display in an SDL2 desktop window. It supports CrossPoint forks, although newly added firmware methods may require stubs.

Current documented host support:

- macOS, including Apple Silicon/M4;
- Linux;
- Ubuntu under WSL on Windows.

Native Windows is not the primary supported target; WSL is recommended.

Reference:
https://github.com/crosspoint-reader/crosspoint-simulator

## 17.2 CrossVi simulator

CrossVi includes its own simulator launcher:

```bash
python3 scripts/run_simulator.py x3
python3 scripts/run_simulator.py x4
```

The CrossVi repository states that the simulator can verify build, boot, UI and basic application flows.

It explicitly does NOT replace physical testing of:

- E-Ink refresh;
- ghosting;
- SD timing;
- power use;
- physical buttons;
- sleep/wake.

Reference:
https://github.com/tvhdc/crossvi

## 17.3 Required development host

Preferred:

```text
macOS Apple Silicon
+ VS Code
+ Git
+ Python 3.12+
+ pioarduino/PlatformIO
+ SDL2
+ curl
+ CMake/toolchain as required
+ Docker Desktop
```

The user's Mac mini M4 is confirmed by the simulator documentation as a tested Apple Silicon host class.

---

# 18. Test Environment Architecture

```text
Mac mini M4 / Developer PC
|
+-- Git repository
|
+-- CrossVi simulator
|      |
|      +-- virtual X3 UI
|
+-- Z-Truyen backend (local)
|      |
|      +-- SQLite
|      +-- object cache
|      +-- mock source fixtures
|
+-- Browser/API test tools
|
+-- Docker
|      |
|      +-- production-like backend image
|
+-- CI
       |
       +-- unit tests
       +-- integration tests
       +-- lint
       +-- firmware build
       +-- simulator smoke test
```

---

# 19. Multi-Stage Development Plan

# Phase 0 — Repository Reconnaissance

### Objective
Understand exact current upstream interfaces before writing code.

### Tasks

1. Clone CrossVi.
2. Clone CrossPoint.
3. Clone CrossPoint Simulator.
4. Clone `Z-Truyenviet.koplugin`.
5. Map:
   - reader APIs;
   - OPDS implementation;
   - networking layer;
   - file download layer;
   - library model;
   - KOSync layer;
   - simulator HAL;
   - existing source adapters.
6. Produce a code-map document.

### Deliverable
`docs/01-code-map.md`

### Acceptance gate
No implementation starts until the agent can name the exact files/modules responsible for:

- OPDS;
- HTTP;
- EPUB open;
- SD file creation;
- simulator input;
- CrossVi home/library screen;
- KOSync;
- source registry in Z-Truyenviet.

---

# Phase 1 — Backend Skeleton

### Objective
Build a source-independent FastAPI service.

### Implement

- `/healthz`
- `/version`
- `/opds`
- basic book model
- basic chapter model
- mock source
- deterministic EPUB builder

### No real website scraping yet.

### Acceptance

- `GET /healthz` < 500 ms local.
- OPDS XML validates.
- One mock book appears.
- One mock chapter downloads as EPUB.
- EPUB opens successfully in a desktop EPUB reader.

---

# Phase 2 — Source Adapter Porting

### Objective
Port selected Z-Truyenviet sources into backend source adapters.

### Rule
Start with ONE text source only.

### For each adapter

- search;
- metadata;
- chapter list;
- chapter extraction;
- cover;
- encoding normalization;
- tests with saved fixtures.

### Acceptance

A recorded fixture reproduces the same normalized chapter text on every run.

No source adapter may access another source adapter's internals.

---

# Phase 3 — OPDS Integration with Unmodified X3 Firmware

### Objective
Prove the entire system without modifying firmware.

### Environment

```text
X3
 + CrossVi 1.1.2 OR CrossPoint 1.5.0
 + local Mac mini server
```

### Steps

1. Add server URL.
2. Browse root catalog.
3. Search.
4. Open book.
5. Browse chapter list.
6. Download EPUB.
7. Confirm file exists on SD.
8. Open book.
9. Read.
10. Reboot X3.
11. Reopen downloaded EPUB.
12. Confirm offline reading.

### Acceptance

No firmware change.

---

# Phase 4 — KOSync Compatibility Validation

### Objective
Ensure generated EPUB identity/location works with KOReader.

### Test matrix

| Source | Device A | Device B | Direction | Expected |
|---|---|---|---|---|
| Z-Truyen | X3 | Android KOReader | X3 -> Android | same chapter/near paragraph |
| Z-Truyen | Android KOReader | X3 | Android -> X3 | same chapter/near paragraph |
| Z-Truyen | X3 | X4 CrossPoint | bidirectional | stable |
| Z-Truyen | X3 | second X3 | bidirectional | stable |

### Acceptance

For clean generated EPUBs:

- document IDs must match according to selected sync mode;
- chapter must match;
- location SHOULD map to paragraph-level where the firmware supports exact XPath mapping;
- percentage fallback must remain functional.

---

# Phase 5 — Automated Backend Test Suite

### Unit tests

- source parsing;
- ID generation;
- slug/filename generation;
- chapter ordering;
- Unicode handling;
- Vietnamese diacritics;
- EPUB metadata;
- EPUB XML validity;
- cache key generation.

### Property tests

- arbitrary titles cannot create invalid paths;
- duplicate chapter IDs remain deterministic;
- malformed source input does not crash the server.

### Integration tests

```text
mock source
 -> scraper
 -> normalized chapter
 -> EPUB builder
 -> OPDS
 -> download
```

### Load tests

At minimum:

- 1 user;
- 5 concurrent users;
- 20 concurrent requests;
- 100 cache-hit downloads.

No requirement for production-scale performance at this phase.

---

# Phase 6 — CrossVi Simulator Integration

### Objective
Implement native UI only after backend is stable.

### Simulator

```bash
python3 scripts/run_simulator.py x3
```

### Features

First screen:

```text
Z-Truyen
```

Then:

```text
Search
Sources
Recent
Favorites
Downloads
```

### Important design rule

Every network operation MUST have:

- timeout;
- loading state;
- success state;
- retry state;
- offline/error state.

### No arbitrary HTML.

The native client receives structured JSON/OPDS and EPUB URLs only.

---

# Phase 7 — Simulator Regression Suite

The simulator MUST automatically test:

1. Boot.
2. Home screen.
3. Enter Z-Truyen.
4. Search.
5. Search result rendering.
6. Book details.
7. Chapter list.
8. Download progress.
9. Download failure.
10. Retry.
11. Download success.
12. Local file existence.
13. Open EPUB.
14. Return to library.
15. Offline mode.
16. Empty search result.
17. Malformed API response.
18. Slow server.
19. HTTP timeout.
20. Auth failure.
21. Token expiration.
22. Cache hit.
23. Cache miss.

### Acceptance gate

All mandatory simulator tests PASS.

Any crash, boot loop, memory corruption, unhandled exception or persistent UI dead end blocks the phase.

---

# Phase 8 — Memory and Resource Stress Testing

Because X3 uses ESP32-C3 with tight RAM, the native client must be stress tested.

Tests:

- 1000-item search response;
- 1000-chapter book response;
- 20 MB EPUB;
- 50 MB EPUB;
- malformed JSON;
- truncated HTTP body;
- slow network;
- repeated search/open/back loops;
- repeated download/delete/download cycles;
- Wi-Fi reconnect loops.

The client MUST limit list sizes and page results.

The client MUST NOT keep the entire OPDS catalog in RAM.

---

# Phase 9 — Security Testing

### Local backend

- path traversal;
- SSRF protections;
- arbitrary URL fetch validation;
- oversized request rejection;
- invalid source ID rejection.

### Cloud backend

- token auth;
- rate limiting;
- source-level concurrency limits;
- maximum response size;
- maximum EPUB size;
- safe MIME/type handling;
- log redaction.

### SSRF requirement

The source discovery/import endpoint MUST NOT allow arbitrary unauthenticated server-side fetching of internal/private addresses.

Block ranges such as:

- `127.0.0.0/8`
- RFC1918 private IPv4 ranges
- link-local ranges
- loopback
- cloud metadata service addresses
- local Unix sockets where applicable

unless an explicit admin-only workflow is implemented.

---

# Phase 10 — Physical X3 Test Gate

ONLY after Phases 0–9 pass.

### Pre-flash checklist

- Backup entire SD card.
- Record current stock firmware version.
- Record X3 device/hardware information.
- Confirm firmware checksum.
- Confirm recovery method.
- Confirm device is eligible for custom firmware flashing.
- Keep known-good stock firmware.
- Do not flash an unverified binary.

### Physical tests

1. Boot.
2. Home.
3. Wi-Fi connect.
4. OPDS browse.
5. Native Z-Truyen UI if implemented.
6. Search.
7. Download small EPUB.
8. Open EPUB.
9. Read 30+ pages.
10. Sleep.
11. Wake.
12. Power-cycle.
13. Wi-Fi reconnect.
14. Download again.
15. Delete book.
16. Re-download.
17. Check battery behavior.
18. Check ghosting.
19. Check page turn latency.
20. Check SD stability.
21. Check KOSync.

### Physical acceptance gate

A native firmware release cannot be published unless all critical tests pass on the user's exact X3 hardware revision.

---

# Phase 11 — Long-Run Reliability Test

Minimum target:

- 7 days normal use.
- 100+ page turns/session.
- 20+ network downloads.
- 10+ sleep/wake cycles.
- 5+ full power cycles.
- 5+ KOSync operations.
- no corruption.
- no bootloop.
- no unrecoverable hang.

If any severe issue occurs, classify:

- P0 = brick/data loss/security failure.
- P1 = critical feature unusable.
- P2 = major functional issue/workaround exists.
- P3 = minor UI/UX defect.

Only P2/P3 may be considered for beta release, with documented known issues.

---

# Phase 12 — Cloud Deployment

## 12.1 Containerization

Build:

```text
ztruyen-server:<git-sha>
```

The container MUST be immutable.

No persistent content may depend on the container filesystem.

## 12.2 Storage

Cloud deployment SHOULD use:

- Cloud Run for compute;
- D1/Postgres for metadata;
- R2 for EPUB/covers.

## 12.3 Cache policy

Default cache key:

```text
source/book_id/chapter_id/content_version
```

When a source reports no explicit version, compute a normalized content hash.

Cache headers and server-side freshness policy MUST be configurable.

## 12.4 Cloud rate control

Per source:

- max concurrency;
- min delay where appropriate;
- timeout;
- retry budget;
- circuit breaker.

The server MUST avoid repeatedly hitting the source when a cached artifact is available.

---

# Phase 13 — Public Community Release

## 13.1 Release artifacts

GitHub release MUST include:

- backend source;
- Docker image reference;
- docker-compose file;
- configuration reference;
- local deployment guide;
- cloud deployment guide;
- source-adapter development guide;
- X3 setup guide;
- known limitations;
- security disclosure process.

## 13.2 User experience

### Self-hosted

```text
1. Install server.
2. Start server.
3. Open admin/setup page.
4. Create device token.
5. Add OPDS URL to X3.
6. Use.
```

### Hosted

```text
1. Enter provided server URL.
2. Enter device token.
3. Browse/search/download.
```

---

# 20. Suggested Repository Layout for the Complete Project

```text
Z-Truyen/
|
+-- README.md
+-- LICENSE
+-- SECURITY.md
+-- CONTRIBUTING.md
+-- CHANGELOG.md
|
+-- backend/
|   +-- app/
|   +-- tests/
|   +-- fixtures/
|   +-- Dockerfile
|   +-- pyproject.toml
|   +-- docker-compose.yml
|
+-- firmware/
|   +-- crossvi/
|   +-- patches/
|   +-- docs/
|   +-- tests/
|
+-- simulator/
|   +-- integration/
|   +-- test-data/
|
+-- sources/
|   +-- source-specs/
|   +-- fixtures/
|
+-- docs/
|   +-- architecture.md
|   +-- api.md
|   +-- opds.md
|   +-- epub.md
|   +-- kosync.md
|   +-- simulator.md
|   +-- hardware-test.md
|   +-- deployment.md
|   +-- source-adapter-guide.md
|
+-- scripts/
|   +-- run-dev.sh
|   +-- run-tests.sh
|   +-- validate-epub.sh
|   +-- run-simulator.sh
|
+-- .github/
    +-- workflows/
        +-- backend.yml
        +-- firmware.yml
        +-- simulator.yml
```

---

# 21. AI Agent Operating Rules

The repository will be executed primarily by an AI coding agent. The agent MUST follow these rules.

## 21.1 No destructive action without explicit phase gate

The agent MUST NOT:

- flash a physical X3 automatically;
- change the X3 bootloader;
- overwrite the user's firmware;
- delete the SD backup;
- publish a release binary before required tests pass.

## 21.2 Work incrementally

Every task MUST result in:

1. code change;
2. tests;
3. test output;
4. short change log;
5. known limitations.

## 21.3 Prefer additive changes

New code SHOULD be isolated in:

```text
ztruyen/
online_stories/
```

rather than invasive modification of core reader code.

## 21.4 Preserve upstream mergeability

When modifying CrossVi:

- avoid broad formatting-only changes;
- isolate Z-Truyen changes in dedicated commits;
- preserve upstream files where possible;
- keep a documented upstream base commit/tag;
- maintain a patch stack or clean branch.

## 21.5 No speculative rewrites

The agent MUST NOT rewrite the reader engine, Wi-Fi stack, SD abstraction, KOSync implementation or rendering engine unless a test proves a required change.

---

# 22. AI Agent Execution Workflow

For each task:

```text
1. Inspect repository.
2. State assumptions.
3. Identify impacted modules.
4. Make smallest change.
5. Add/update tests.
6. Run unit tests.
7. Run integration tests.
8. Run simulator.
9. Produce evidence.
10. Stop if a required gate fails.
```

Do not silently skip failed gates.

When a failure is found:

```text
FAIL
 -> capture logs
 -> classify P0/P1/P2/P3
 -> reproduce
 -> patch
 -> re-run regression
```

---

# 23. Acceptance Test Matrix

| ID | Area | Test | Required |
|---|---|---|---|
| T001 | Backend | health endpoint | PASS |
| T002 | OPDS | catalog validates | PASS |
| T003 | OPDS | search works | PASS |
| T004 | OPDS | book navigation works | PASS |
| T005 | OPDS | chapter navigation works | PASS |
| T006 | Download | EPUB downloads | PASS |
| T007 | EPUB | package validates | PASS |
| T008 | EPUB | Vietnamese UTF-8 correct | PASS |
| T009 | EPUB | cover works | PASS if source has cover |
| T010 | Cache | repeat request hits cache | PASS |
| T011 | Cache | invalidates correctly | PASS |
| T012 | Source | parser fixture stable | PASS |
| T013 | Simulator | boot | PASS |
| T014 | Simulator | UI navigation | PASS |
| T015 | Simulator | search flow | PASS |
| T016 | Simulator | download flow | PASS |
| T017 | Simulator | error flow | PASS |
| T018 | Simulator | offline flow | PASS |
| T019 | Stress | large response handling | PASS |
| T020 | Stress | repeated downloads | PASS |
| T021 | KOSync | X3 -> KOReader | PASS |
| T022 | KOSync | KOReader -> X3 | PASS |
| T023 | Security | SSRF rejection | PASS |
| T024 | Security | auth enforcement | PASS in cloud |
| T025 | Physical | boot | PASS |
| T026 | Physical | Wi-Fi | PASS |
| T027 | Physical | OPDS/download | PASS |
| T028 | Physical | EPUB reading | PASS |
| T029 | Physical | sleep/wake | PASS |
| T030 | Physical | SD stability | PASS |
| T031 | Physical | KOSync | PASS |
| T032 | Long-run | 7-day soak | PASS |

---

# 24. Failure and Rollback Strategy

## Backend

Every deploy MUST be versioned by Git SHA.

Rollback:

```text
current -> previous known-good container
```

## Cloud cache

Never delete all cached EPUBs during deploy.

## Firmware

Every custom firmware build MUST have:

- Git SHA;
- release tag;
- firmware checksum;
- source base tag;
- build environment;
- test report.

No physical firmware flash without an explicit human confirmation at the physical stage.

---

# 25. Observability

The backend MUST provide:

```text
GET /healthz
GET /version
GET /metrics   (optional initially)
```

Logs MUST identify:

- request ID;
- source ID;
- book ID;
- chapter ID;
- cache hit/miss;
- duration;
- status.

Do not log passwords or bearer tokens.

---

# 26. Performance Targets

## Backend local

- OPDS catalog: < 500 ms from cache.
- Search from cache: < 1 s.
- Cache-hit EPUB: network-bound only.
- New chapter scrape: target < 10 s where source responds normally.

## X3 client

No hard real-time guarantee.

UI MUST show progress for operations likely to exceed 1–2 seconds.

Never block indefinitely on network requests.

---

# 27. Offline Behavior

The X3 MUST remain a normal offline reader.

If server unavailable:

- existing downloaded EPUBs remain readable;
- library remains accessible;
- Z-Truyen shows a clear network error;
- no repeated aggressive retries.

The user MUST NOT lose downloaded books because the server is unavailable.

---

# 28. Optional Future Features

After MVP:

1. Batch chapter download.
2. Automatic “download next N chapters”.
3. “Continue reading” list.
4. New-chapter detection.
5. Multi-source book matching.
6. Reader sync metadata.
7. Server-side account library.
8. Native notifications.
9. Cloud-hosted public OPDS.
10. Source health dashboard.
11. Automatic source-rule regeneration with human approval.
12. Optional comic/manga support via CBZ.
13. Bundle multiple chapters into larger EPUBs.
14. Calibre integration.
15. RSS/feed ingestion.

---

# 29. Final Recommended Roadmap

```text
                 Z-TRUYEN DEVELOPMENT ROADMAP

PHASE 0  Research/code-map
   |
   v
PHASE 1  Local backend skeleton
   |
   v
PHASE 2  Port ONE source adapter
   |
   v
PHASE 3  OPDS + unmodified X3
   |
   v
PHASE 4  KOSync interoperability
   |
   v
PHASE 5  Automated tests
   |
   v
PHASE 6  CrossVi simulator native UI
   |
   v
PHASE 7  Simulator regression
   |
   v
PHASE 8  Memory/stress/security tests
   |
   v
PHASE 9  Human review gate
   |
   v
PHASE 10 Physical X3 test
   |
   v
PHASE 11 7-day reliability soak
   |
   v
PHASE 12 Local production packaging
   |
   v
PHASE 13 Cloud Run + R2/D1 + Cloudflare
   |
   v
PHASE 14 Community self-host release
```

---

# 30. Final Architecture Decision Record

## Decision A

**Server-side scraping instead of X3-side scraping.**

Reason:

- protects X3 RAM/CPU;
- avoids firmware coupling to changing websites;
- makes source updates independent of X3 releases.

## Decision B

**OPDS for MVP.**

Reason:

- already supported by CrossPoint/CrossVi;
- no firmware change required;
- immediate real-device validation.

## Decision C

**EPUB as the canonical text artifact.**

Reason:

- X3 reader already handles EPUB;
- offline support;
- cross-device compatibility;
- KOSync can operate on a stable document identity.

## Decision D

**CrossVi 1.1.2 as future native UI base; CrossPoint 1.5.0 as upstream reference.**

Reason:

- CrossVi aligns better with Vietnamese UX and project-specific features;
- CrossPoint has larger upstream ecosystem and strong documented KOSync/simulator architecture.

## Decision E

**Simulator-first development.**

Reason:

- reduces flash cycles;
- avoids premature brick risk;
- allows AI agent to iterate independently;
- user only needs to validate simulator builds until the physical test gate.

## Decision F

**Cloud second, local-first.**

Reason:

- local Mac mini M4 is already available;
- simpler debugging;
- no cloud lock-in;
- same Docker image can later be deployed to cloud.

---

# 31. Definition of Done

The project is considered MVP-complete when all of the following are true:

- [ ] One real source works end-to-end.
- [ ] Search works.
- [ ] Book/chapter navigation works.
- [ ] EPUB generation passes validation.
- [ ] OPDS works from unmodified CrossVi/CrossPoint.
- [ ] X3 can download and open the EPUB.
- [ ] Downloaded books remain readable offline.
- [ ] KOSync interoperability is tested.
- [ ] Simulator regression suite passes.
- [ ] Backend unit/integration tests pass.
- [ ] Security checks pass.
- [ ] No firmware modification is required for MVP.
- [ ] Native UI build, if implemented, passes simulator gates.
- [ ] Physical flash occurs only after explicit human approval.
- [ ] Physical X3 test passes.
- [ ] Recovery path has been verified.
- [ ] 7-day reliability soak passes.
- [ ] Docker deployment is reproducible.
- [ ] Cloud deployment is optional and documented.

---

# 32. Primary References

## Xteink

- https://www.xteink.com/products/xteink-x3
- https://www.xteink.com/pages/compare-our-products

## CrossPoint

- https://github.com/crosspoint-reader/crosspoint-reader
- https://github.com/crosspoint-reader/crosspoint-reader/releases/tag/v1.5.0
- https://github.com/crosspoint-reader/crosspoint-reader/discussions/61
- https://github.com/crosspoint-reader/crosspoint-reader/blob/develop/USER_GUIDE.md
- https://github.com/crosspoint-reader/crosspoint-simulator

## CrossVi

- https://github.com/tvhdc/crossvi
- https://github.com/tvhdc/crossvi/releases/tag/v1.1.2

## Original KOReader plugin

- https://github.com/magicxlll/Z-Truyenviet.koplugin

## Cloud

- https://developers.cloudflare.com/workers/platform/limits/
- https://developers.cloudflare.com/d1/platform/limits/
- https://developers.cloudflare.com/d1/platform/pricing/
- https://developers.cloudflare.com/r2/pricing/
- https://cloud.google.com/run/pricing
- https://render.com/docs/free
- https://tailscale.com/docs/reference/free-plans-discounts

---

# 33. AI Agent Initial Task

When this specification is first loaded, the AI agent MUST NOT modify firmware or attempt to flash an X3.

The first autonomous task is:

```text
1. Clone/inspect CrossVi 1.1.2.
2. Inspect CrossPoint 1.5.0.
3. Inspect CrossPoint simulator.
4. Inspect Z-Truyenviet.koplugin.
5. Produce a code map.
6. Build CrossVi simulator.
7. Build a minimal local Z-Truyen backend.
8. Implement a mock OPDS catalog.
9. Demonstrate the simulator consuming the mock service.
10. Run all tests.
11. Do not touch physical X3.
```

The AI agent MUST stop at this point and produce a machine-readable test report and human-readable summary before proceeding to source scraping or native firmware changes.

---

## End of Specification
