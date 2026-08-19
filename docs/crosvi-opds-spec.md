# CrossVi OPDS Specification Notes

This document records findings about OPDS support in CrossVi firmware and CrossPoint Reader based on Z-Truyen backend implementation.

## OPDS Version Support

### CrossVi 1.1.2 / CrossPoint 1.5.0

| Feature | Support Status |
|---------|---------------|
| OPDS 1.0 | Full Support |
| OPDS 1.2 | Full Support |
| OPDS 2.0 | Limited / Not Tested |

### Implementation Details

The Z-Truyen backend implements **OPDS 1.2** (based on Atom Publishing Protocol) with the following characteristics:

```xml
<!-- Root Catalog Feed -->
<feed xmlns="http://www.w3.org/2005/Atom"
      xmlns:opds="http://opds-spec.org/2010/catalog"
      xmlns:dc="http://purl.org/dc/elements/1.1/">
```

## Supported OPDS Link Relations

### Acquisition Links

| Relation | MIME Type | Purpose |
|----------|-----------|---------|
| `http://opds-spec.org/acquisition/open-access` | `application/epub+zip` | Download EPUB |
| `http://opds-spec.org/cover` | `image/jpeg` | Book cover image |
| `alternate` | `application/atom+xml;profile=opds-catalog` | Navigation to book detail |

### Navigation Links

| Relation | Purpose |
|----------|---------|
| `self` | Current feed reference |
| `start` | Root catalog link |
| `search` | Search endpoint |
| `subsection` | Navigation to sub-catalogs |

## Search Implementation

### CrossVi Search Behavior

CrossVi OPDS Browser supports keyword search via the `/opds/search` endpoint:

```
GET /opds/search?q=<keyword>
```

**Notes:**
- CrossVi sends search queries as URL-encoded parameters
- Supports partial title matching
- Response time depends on backend scraper implementation

### Z-Truyen Backend Search Endpoint

```
GET /opds/search?q=<query>&source=<optional_source>
```

**Parameters:**
- `q` (required): Search query string
- `source` (optional): Filter by source (storyaclick, akaytruyen, conduongbachu)

## Download Behavior

### EPUB Download Flow

1. User navigates to book detail page
2. Backend generates deterministic EPUB with:
   - 50 chapters per volume (configurable)
   - Clean XHTML content
   - SHA-1 hash for KOSync
3. CrossVi downloads via acquisition link
4. File saved to virtual SD card (`/sdcard/`)

### File Naming Convention

```
ztruyen_{source_id}_{book_slug}_v{volume_index:02d}.epub
```

**Examples:**
- `ztruyen_storyaclick_main_v01.epub`
- `ztruyen_conduongbachu_side_v02.epub`
- `ztruyen_akaytruyen_main_v03.epub`

## Known Limitations

### CrossVi Specific

1. **No OPDS 2.0**: CrossVi only supports OPDS 1.0/1.2 Atom feeds
2. **Limited HTTP Headers**: Some advanced headers may not be respected
3. **SD Card Storage**: Virtual storage limited by simulator configuration
4. **No Streaming**: Full EPUB must be downloaded before reading

### CrossPoint Reader Specific

1. **Memory Constraints**: ESP32-C3 has limited RAM (~380KB)
   - Large EPUBs (>1MB) may cause issues
   - Backend limits chapters per volume to 50
2. **Font Rendering**: Vietnamese diacritics require proper UTF-8 XHTML
3. **KOSync**: Requires deterministic SHA-1 hashing for sync accuracy

## Z-Truyen Backend OPDS Responses

### Root Catalog (`/opds/`)

Returns navigation and featured content:
- Hot stories feed
- New updates feed
- Genre categories
- Source list

### Book Detail (`/opds/book/{source}/{slug}`)

Returns:
- Book metadata (title, author, summary)
- Volume list (each 50 chapters)
- Cover image link

### Chapter Download (`/opds/download/{source}/{slug}/{volume}`)

Returns:
- EPUB binary (`application/epub+zip`)
- `Content-Disposition: attachment` header
- `X-KOSync-SHA1` header for sync verification

## Validation Checklist

For CrossVi compatibility, OPDS feeds must:

- [ ] Use valid Atom XML with OPDS namespace
- [ ] Include `rel` attribute on all `<link>` elements
- [ ] Use correct MIME types for acquisitions
- [ ] Support UTF-8 encoding for Vietnamese text
- [ ] Return appropriate HTTP status codes
- [ ] Handle search queries with proper URL encoding
- [ ] Generate EPUB files under 1MB per volume

## Testing Commands

```bash
# Test root catalog
curl -s http://localhost:8080/opds/ | head -50

# Test search
curl -s "http://localhost:8080/opds/search?q=bá" | head -30

# Test book detail
curl -s http://localhost:8080/opds/book/conduongbachu/main | head -50

# Download EPUB
curl -s -O -J http://localhost:8080/opds/download/conduongbachu/main/ztruyen_conduongbachu_main_v01.epub
```

## References

- [OPDS Specification 1.2](https://opds-spec.org/specs/opds-catalog-1-2/)
- [Atom Publishing Protocol](https://tools.ietf.org/html/rfc5023)
- [CrossVi Firmware](https://github.com/tvhdc/crossvi)
- [CrossPoint Reader](https://github.com/crosspoint-reader/crosspoint-reader)
