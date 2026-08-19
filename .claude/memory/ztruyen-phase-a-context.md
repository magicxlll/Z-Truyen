---
name: ztruyen-phase-a-context
description: Phase A project context and decisions for Z-Truyen X3 backend
metadata:
  type: project
---

# Z-Truyen Phase A — Context

## Project Role
- **Phase A:** Personal use (user is end user, single X3, local Mac mini M4)
- **Phase B:** Community platform (future, not now)

## Key Decisions Made

### Phase A Roadmap (5 phases, not 13)
1. Backend skeleton with OPDS (1-2 days)
2. storya.click adapter (1-2 days)
3. conduongbachu.com adapter (1 day)
4. CrossVi/CrossPoint simulator integration (1-2 days)
5. Physical X3 validation (remaining time)

### Tech Stack (Simplified from Spec)
- Python 3.12 + FastAPI (keep FastAPI — lightweight enough)
- httpx for HTTP
- ebooklib for EPUB generation
- JSON file storage (not SQLite — sufficient for 1 user)
- Filesystem cache (not Redis — sufficient for 1 user)
- No auth tokens (single user)
- No rate limiting (single user)
- No cloud deployment (local Mac mini only)

### Source Priority
1. **storya.click** — REST API JSON, clean endpoints, low complexity (2-day implementation)
2. **conduongbachu.com** — WordPress REST API, medium complexity (1-day implementation)
3. **akaytruyen.com** — HTML scraping + cookie auth + VIP chapters, HIGH complexity → **Deferred to Phase B**

### EPUB Strategy
- One chapter per EPUB (confirmed optimal for X3 ~380KB RAM)
- Filename: `ztruyen__<source>__<book_id>__<chapter_order>.epub`
- Clean XHTML with `<p>` paragraphs
- Cover normalized to 800x1200 JPEG quality 80

### OPDS (Simplified)
Only 4 endpoints needed:
- `GET /opds` — Root catalog
- `GET /opds/search?q=<query>` — Search (if supported)
- `GET /opds/book/<book_id>` — Book metadata + chapters
- `GET /opds/download/<chapter_id>` — EPUB download

### X3 Setup
- **Phase A:** CrossVi simulator on Mac mini first, then physical CrossVi 1.1.2 on X3
- **Hardware assumption:** UC8279 on newer units, use CrossPoint 1.5.0 as fallback
- **Connectivity:** Direct LAN (same Wi-Fi), X3 accesses `http://192.168.x.x:8080/opds`

### Legal/Usage
- Personal use only — no public distribution
- No KOSync in Phase A (Phase B feature)
- No cloud hosting in Phase A (local Mac mini only)

## Key Source Info

### storya.click API
- Base: `https://storya.click/api/v1`
- Search: `/stories/search?q=<query>`
- Catalog: `/stories?page=N&limit=20`
- Genres: `/genres`
- Book: `/stories/<slug>`
- Chapters: `/chapters/story/<slug>?page=N&limit=100&minimal=true`
- Content: `/chapters/<story>/<chapter>`
- Uses `rewrittenContent` field — clean text already available

### conduongbachu.com
- WordPress REST API: `/wp-json/wp/v2/posts?categories=<cat_id>&per_page=100&page=N`
- Hardcoded story list (STORIES table) — not general-purpose
- Only serves "Con Đường Bá Chủ" and spinoffs

### akaytruyen.com
- HTML scraping with cookie-based CSRF auth
- VIP chapter locking
- 900KB homepage, requires aggressive caching
- `max_concurrent = 1` enforced
- **DO NOT IMPLEMENT for Phase A**

## Open Questions (Need Resolution)
1. Does CrossVi OPDS client support `/opds/search?q=`? → Test with public server first
2. Max EPUB size CrossVi can download without failure? → Test 50KB, 200KB, 500KB, 1MB
3. Wi-Fi connectivity pattern? → Direct LAN for Phase A

## References
- Spec: `Z-Truyen_X3_Project_Spec.md`
- Critique: `Z-Truyen_X3_Critique.md`
- Original plugin: `https://github.com/magicxlll/Z-Truyenviet.koplugin` (cloned to `/tmp/truyenviet`)

**Why:** Phase A context is not derivable from git history or existing code — needs explicit memory.

**How to apply:** Use this for all Phase A backend implementation decisions. Ignore multi-user/cloud/Phase B features until explicitly requested.
