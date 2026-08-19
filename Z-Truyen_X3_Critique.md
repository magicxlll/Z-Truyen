# Z-Truyen X3 — Critical Review & Optimized Roadmap

**Version:** 1.1.0  
**Date:** 2026-08-13  
**Reviewer:** AI Coding Agent (Grill Session)  
**Context:** Phase A (personal use, single X3)  
**Host Options:** ~~Mac mini~~ → **Smartphone (Android + Termux)**  
**Sources under review:** `storya.click`, `akaytruyen.com`, `conduongbachu.com`

---

## Appendix: Smartphone Architecture (v1.1)

### Why Smartphone Over Mac mini?

| Criteria | Mac mini | Android + Termux |
|----------|----------|------------------|
| Availability | Fixed location | Always with you |
| Power | 24/7 capable | On-demand (battery conscious) |
| Setup | Requires desk/rack | Just open app |
| Cost | ~$600+ | Included with phone |
| Portability | None | Full |

### Target Architecture

```
┌─────────────────┐      Wi-Fi (LAN hoặc Hotspot)      ┌─────────────────┐
│     Android     │◄──── mDNS: ztruyen.local ─────────►│       X3        │
│                 │                                     │                 │
│  ┌───────────┐  │   http://ztruyen.local:8080/opds    │  CrossVi OPDS   │
│  │ Z-Truyen  │  │                                     │     Client      │
│  │  Backend  │──┼───────── OPDS Catalog ─────────────►│                 │
│  │  (Python) │  │                                     │                 │
│  └───────────┘  │───────── EPUB Download ─────────────►│   EPUB → SD    │
│                 │                                     │                 │
│  Termux        │                                     │                 │
│  + mDNS (avahi)│                                     │                 │
└─────────────────┘                                     └─────────────────┘
```

### Key Decisions

| Decision | Choice | Rationale |
|----------|--------|-----------|
| Platform | Termux + Python | Native Python, no VM overhead |
| Discovery | mDNS/Bonjour | Auto-discovery, no manual IP entry |
| Network | Wi-Fi LAN hoặc Hotspot | Both work with mDNS |
| Start/Stop | Auto-start on app open | Convenient UX |
| Port | Dynamic (8080 default) | Handle port conflicts |
| Storage | App internal storage | Scoped storage compliant |
| X3 Client | CrossVi OPDS | No custom firmware needed |

### Advantages Over Mac mini

1. **Portability** — Server travels with you
2. **No additional hardware** — Uses existing phone
3. **On-demand** — Only use battery when reading
4. **Simpler** — No router port forwarding needed
5. **Hotspot mode** — Works anywhere, no existing Wi-Fi required

---

## Executive Summary

The existing spec (`Z-Truyen_X3_Project_Spec.md`) is a **comprehensive production blueprint** suitable for Phase B (multi-user community platform). However, for Phase A (single-user personal reading), it suffers from **over-engineering, excessive phasing, and scope creep** that will slow initial validation significantly.

This critique identifies the gaps, contradictions, and unnecessary complexity, then proposes an **optimized Phase A architecture** that reduces effort by ~70% while achieving the same functional goals.

---

## 1. Issues with the Existing Spec

### 1.1 Over-Engineering for Phase A

The spec explicitly defines 13 phases with infrastructure designed for multi-user, cloud-hosted, community-distributed deployment. For a single user reading on one X3:

| Spec Feature | Phase A Relevance | Verdict |
|---|---|---|
| Device token auth (`Authorization: Bearer zt_<token>`) | Zero — single user | **Remove** |
| Per-user rate limits | Zero — one user | **Remove** |
| Source-level concurrency limits | Nice-to-have | **Defer** |
| SSRF protection | Nice-to-have | **Defer** |
| Cloudflare D1/R2/Render/Koyeb | Zero — local Mac mini only | **Remove** |
| Tailscale for remote access | Nice-to-have | **Defer** |
| Calibre/WebDAV integration | Nice-to-have | **Defer** |
| Circuit breaker on failing sources | Nice-to-have | **Defer** |
| Multiple source adapters architecture | Already have 3 sources | **Simplify** |
| KOSync XPath mapping | Not in Phase A scope | **Remove** |

**Impact:** ~60% of spec content is Phase B or irrelevant for Phase A.

### 1.2 Phasing is Too Granular

The spec defines 13 phases. For Phase A validation, this can be reduced to **5 phases**:

```
Phase A-1: Local backend skeleton (1-2 days)
Phase A-2: Single source adapter (storya.click) (1-2 days)
Phase A-3: OPDS catalog + EPUB download on Mac (1 day)
Phase A-4: X3 CrossPoint/CrossVi simulator integration (1-2 days)
Phase A-5: End-to-end validation + cleanup (1 day)
```

Compared to spec's 13 phases (0-12), this is **5x faster to first usable result**.

### 1.3 Conflicting Design Decisions

The spec contains some internal contradictions:

1. **"No firmware modification during MVP"** but also includes **"Native X3 Integration Strategy"** in Phase 16 — this creates false expectation that native UI is planned.

2. **Section 9.1 recommends Python 3.12+ FastAPI** but Section 21.3 says **"Prefer additive changes"** — FastAPI's strict Pydantic models and async patterns are invasive for a minimal backend.

3. **Section 7.1 specifies OPDS endpoints** but does not specify **OPDS compatibility level** (OPDS 1.0 vs 1.2 vs 2.0) or validate which standard the CrossPoint/CrossVi OPDS client actually implements.

### 1.4 Missing Critical Information

The spec omits:

1. **OPDS compatibility matrix** — what exactly does CrossPoint/CrossVi OPDS client support? Does it support search? Acquisition links? How does it handle paginated feeds?

2. **EPUB validation criteria** — what EPUB features does CrossPoint/CrossVi EPUB reader actually support? EPUB 2 only? EPUB 3? What CSS features? Embedded fonts?

3. **X3 download constraints** — maximum file size? Maximum response time before timeout? Does the OPDS client follow redirects?

4. **Source API health** — are the three source APIs stable? Any rate limits? Any authentication requirements we should know about?

### 1.5 Simulator Strategy is Under-specified

The spec says "use CrossVi simulator" but:

- Does the simulator support OPDS client UI testing?
- Does it simulate network requests?
- Does it have a mock SD card filesystem?
- What's the build/setup process on macOS Apple Silicon?

Without this, Phase 6 (Simulator Integration) is a black box.

---

## 2. Source Adapter Analysis

Based on inspection of `Z-Truyenviet.koplugin`, the three sources have very different complexity profiles:

### 2.1 storya.click (Recommended First)

**Type:** REST API JSON  
**Complexity:** Low  
**Endpoints confirmed:**
- `GET /api/v1/stories/search?q=<query>`
- `GET /api/v1/stories?page=N&limit=20`
- `GET /api/v1/genres`
- `GET /api/v1/genres/slug/<slug>`
- `GET /api/v1/stories/<slug>`
- `GET /api/v1/chapters/story/<slug>?page=N&limit=100&minimal=true`
- `GET /api/v1/chapters/<story>/<chapter>`

**Content strategy:** Uses `rewrittenContent` field preferentially over raw HTML — clean, sanitized text available directly from API.

**Recommendation:** Port directly to Python. This is a **2-day implementation maximum**.

### 2.2 conduongbachu.com (Recommended Second)

**Type:** WordPress REST API  
**Complexity:** Low-Medium  
**Endpoints:**
- WordPress standard REST API: `/wp-json/wp/v2/posts?categories=<cat_id>&per_page=100&page=N`
- Story pages are HTML (for description/author metadata)
- Chapter pages are HTML (for content)

**Special case:** This source has **hardcoded story list** (STORIES table) — not a general-purpose story site. It only serves "Con Đường Bá Chủ" and its spinoffs.

**Recommendation:** Implement as a **simple Python adapter**. No complex HTML parsing needed for catalog. Chapter content parsing is straightforward WordPress HTML.

### 2.3 akaytruyen.com (Recommended Third / Deferred)

**Type:** HTML scraping + Cookie-based auth  
**Complexity:** High  
**Key challenges:**
- Requires CSRF token + cookie management for auth
- VIP chapter locking with login requirement
- Complex HTML parsing with multiple fallback selectors
- `max_concurrent = 1` enforced by KOReader plugin (rate limiting built-in)
- Home page is ~900KB — aggressive caching required

**Recommendation:** **Defer to Phase B**. The complexity is 5-10x higher than the other two sources. No API means all parsing is fragile and site-structure-dependent.

---

## 3. Optimized Architecture for Phase A

### 3.1 Minimal Viable Architecture

```
                    LOCAL MAC MINI
                    (macOS, 24/7)
                         |
                         v
    +------------------------------------------+
    |          Z-Truyen Backend                 |
    |                                          |
    |  Python FastAPI (simplified)             |
    |  ├─ OPDS catalog endpoint (/opds)       |
    |  ├─ Source adapters (storya, cdb)       |
    |  ├─ EPUB builder (ebooklib)             |
    |  └─ Static file serving (EPUB downloads) |
    +------------------------------------------+
                         |
                     HTTP (local network)
                         |
                         v
                    X3 with CrossVi
                    OPDS client
                    |
                    v
               EPUB saved to SD
               Read offline
```

**No cloud. No auth. No multi-user. No rate limiting.**

### 3.2 Technology Stack Simplification

| Spec Recommendation | Phase A Reality | Rationale |
|---|---|---|
| Python 3.12+ + FastAPI | **Python 3.12 + FastAPI** | Keep — FastAPI is lightweight enough |
| Pydantic for all models | **Pydantic for OPDS only** | OPDS XML generation benefits from it |
| httpx for async HTTP | **httpx** | Keep — good async support |
| selectolax/BeautifulSoup | **httpx + raw string parsing** | JSON APIs, minimal HTML needed |
| ebooklib | **ebooklib** | Keep — EPUB generation standard |
| SQLite for metadata | **JSON file storage** | Sufficient for 1 user, zero DB setup |
| Redis/object cache | **Filesystem cache** | Sufficient for 1 user |

### 3.3 Backend Module Structure (Simplified)

```text
ztruyen-backend/
├── main.py              # FastAPI app, OPDS endpoint
├── sources/
│   ├── base.py          # Protocol definition
│   ├── storya.py        # JSON API adapter
│   └── conduongbachu.py # WordPress API adapter
├── epub_builder.py      # EPUB generation
├── opds_renderer.py     # OPDS XML generation
└── static/              # Cached EPUBs served here
```

**vs. spec's 20+ module structure** — this is 5x simpler.

### 3.4 OPDS Contract (Simplified for Phase A)

The spec's OPDS endpoints are correct but over-engineered. Phase A needs only:

```text
GET /opds                          # Root catalog
GET /opds/search?q=<query>         # Search (if CrossVi supports it)
GET /opds/book/<book_id>           # Book metadata + chapters
GET /opds/download/<chapter_id>     # EPUB download
```

**No auth headers. No pagination extensions. No acquisition links beyond what's needed.**

---

## 4. EPUB Strategy

### 4.1 One Chapter per EPUB (Confirmed Optimal)

As discussed in the grill session:
- X3 has ~380KB usable RAM
- Large EPUBs cause indexing/memory pressure
- Per-chapter allows granular download/retry
- 500 chapters = 500 files — acceptable on X3's library UI

### 4.2 EPUB Internal Structure

```text
mimetype
META-INF/container.xml
OEBPS/
  content.opf
  nav.xhtml
  text/
    chapter.xhtml     # Clean XHTML, UTF-8, <p> paragraphs
  images/
    cover.jpg         # Normalized to max 800x1200, JPEG quality 80
```

### 4.3 Filename Convention (Per Spec)

```
ztruyen__<source>__<book_id>__<chapter_order>.epub
```

Example: `ztruyen__storya__abc123__001.epub`

### 4.4 Document Identity for KOSync (Future)

When KOSync becomes relevant (Phase B), the filename-based identity model in the spec is correct. The `<dc:identifier>` in content.opf should match the filename.

---

## 5. Optimized Phase A Roadmap

### Phase A-1: Backend Skeleton (Day 1-2)

**Goal:** Running local server with OPDS catalog.

**Tasks:**
1. Python project setup (`uv` or `pip`)
2. FastAPI app with `GET /opds` returning valid OPDS XML
3. Static file serving for EPUB downloads
4. Health endpoint `GET /healthz`

**Deliverable:** `curl http://localhost:8080/opds` returns valid OPDS XML with one mock book.

**No scraping. No EPUB generation. No source adapters.**

### Phase A-2: storya.click Adapter (Day 2-4)

**Goal:** Working search and chapter download from first source.

**Tasks:**
1. Implement `storya.py` source adapter
2. Wire into OPDS catalog
3. EPUB builder with ebooklib
4. One successful chapter download as EPUB

**Deliverable:** OPDS catalog shows books from storya.click. Download chapter as EPUB. EPUB opens in desktop reader (Calibre/Adequate).

### Phase A-3: conduongbachu.com Adapter (Day 4-5)

**Goal:** Second source working.

**Tasks:**
1. Implement `conduongbachu.py` source adapter
2. Wire into OPDS catalog alongside storya
3. Validate chapter download

**Deliverable:** OPDS catalog shows books from both sources.

### Phase A-4: CrossVi/CrossPoint Simulator (Day 5-7)

**Goal:** Prove end-to-end without physical X3.

**Tasks:**
1. Set up CrossVi simulator on Mac mini
2. Add Z-Truyen OPDS server to simulator
3. Browse catalog
4. Download EPUB
5. Open EPUB in simulator reader

**Deliverable:** Simulator successfully browses, downloads, and reads an EPUB from Z-Truyen.

### Phase A-5: CrossVi Physical X3 (Day 7+)

**Goal:** Real device validation.

**Pre-check:**
1. Identify X3 hardware revision (check for UC8279)
2. Backup SD card
3. Flash CrossVi 1.1.2
4. Test basic OPDS with public server first (e.g., feedbooks.com)

**Then:**
1. Point X3 OPDS to local Mac mini server (via LAN IP)
2. End-to-end flow validation

**Deliverable:** EPUB on real X3, read offline.

---

## 6. Open Questions Requiring User Decision

These are not blockers for Phase A-1 but need resolution before A-4:

### Q1: CrossVi or CrossPoint for Simulator?

Both have simulators. Recommendation: **CrossVi 1.1.2** because it has Vietnamese UI and aligns with the project's UX direction (per spec Decision D).

**Action needed:** User to clone and build CrossVi simulator on Mac mini.

### Q2: OPDS Search Support?

Does CrossVi OPDS client support `/opds/search?q=`? If not, we need a workaround (category browsing instead).

**Action needed:** Test with a known-working public OPDS server after flashing simulator/X3.

### Q3: Max EPUB Download Size?

What's the largest EPUB CrossVi can download without failure? We should test with progressively larger EPUBs.

**Action needed:** Create test EPUBs of 50KB, 200KB, 500KB, 1MB and test on simulator.

### Q4: Wi-Fi Connectivity Pattern?

How will X3 reach Mac mini? Options:
- **Direct LAN:** Both on same Wi-Fi network (simplest)
- **Tailscale:** For remote access scenarios (Phase B)
- **ngrok/cloudflare tunnel:** Temporary for testing

**Recommendation for Phase A:** Direct LAN. Mac mini and X3 on same Wi-Fi. X3 accesses `http://192.168.x.x:8080/opds`.

---

## 7. Risks and Mitigations

| Risk | Severity | Mitigation |
|---|---|---|
| storya.click API goes down or changes | Medium | Add graceful fallback; cache aggressively |
| CrossVi OPDS client incompatible with our OPDS | High | Test early with simulator; use OPDS 1.0 for maximum compatibility |
| UC8279 X3 incompatible with CrossVi | High | Use CrossPoint 1.5.0 as fallback; validate hardware first |
| akaytruyen.com VIP chapters blocked | Low | Accept limitation for Phase A; document for Phase B |
| Mac mini goes to sleep | Low | Configure Energy Saver to never sleep; or use `caffeinate` |

---

## 8. Summary of Deviations from Original Spec

| Spec Section | Original Spec | This Critique | Reason |
|---|---|---|---|
| Phases 0-13 | 14 phases | 5 phases | Speed to MVP |
| Multi-user auth | Full token system | None | Single user |
| Cloud deployment | Cloud Run + R2 + D1 | Local Mac mini only | Phase A scope |
| Source adapters | Full registry pattern | Direct adapter classes | Simplicity |
| KOSync | XPath mapping | Not in scope | Phase B only |
| Database | SQLite | JSON files | Proportional complexity |
| Cache | Redis/object cache | Filesystem cache | Sufficient |
| Rate limiting | Per-user, per-source | None | Single user |
| Security | SSRF, abuse protection | Basic URL validation | Single user |
| Calibre/WebDAV | Full integration | Not in scope | Phase B only |

---

## 9. Recommended Next Steps

1. **Create minimal backend** — `uv init ztruyen-backend`, add FastAPI, serve mock OPDS
2. **Validate OPDS** with CrossPoint's existing public test server or simulator first
3. **Implement storya.click adapter** as the first real source
4. **Test EPUB** with Calibre/Adequate on Mac before touching X3
5. **Build CrossVi simulator** on Mac mini
6. **Flash CrossVi on X3** only after simulator validation passes

---

## 10. Conclusion

The original spec is a **well-structured production blueprint** but needs significant trimming for Phase A. The key insight is:

> **For single-user personal reading on one X3 with a local Mac mini server, the entire infrastructure for multi-user cloud deployment is unnecessary overhead.**

The optimized approach reduces:
- **Phases:** 13 → 5
- **Backend modules:** 20+ → 5
- **Tech stack:** Full production → Minimal viable
- **Time to first result:** ~2 weeks spec → ~3-5 days optimized

**The spec's architecture decisions (server-side scraping, OPDS for MVP, EPUB as artifact, CrossVi as base) are sound and should be preserved.** The trimming applies to multi-user infrastructure, cloud deployment, and Phase B features.

---

*End of Critique*
