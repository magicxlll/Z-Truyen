"""OPDS 1.2 XML Atom Feed generator for e-reader catalog navigation and book acquisition."""

import html
from datetime import datetime, timezone
from typing import Sequence
from app.domain.models import StorySummary, Story, VolumeBundle


def format_iso_time(dt: datetime | None = None) -> str:
    """Format datetime in UTC ISO 8601 string."""
    d = dt or datetime.now(timezone.utc)
    if d.tzinfo is None:
        d = d.replace(tzinfo=timezone.utc)
    return d.isoformat()


class OpdsBuilder:
    """Helper to construct standard OPDS 1.2 XML Atom Feed documents."""

    @staticmethod
    def build_root_feed(base_url: str = "") -> str:
        """Construct Root OPDS Catalog Feed with navigation entries."""
        now = format_iso_time()
        xml = f"""<?xml version="1.0" encoding="utf-8"?>
<feed xmlns="http://www.w3.org/2005/Atom"
      xmlns:dc="http://purl.org/dc/terms/"
      xmlns:opds="http://opds-spec.org/2010/catalog">
    <id>urn:ztruyen:catalog:root</id>
    <title>Z-Truyen X3 — Thư Viện Truyện Tiếng Việt</title>
    <updated>{now}</updated>
    <author>
        <name>Z-Truyen X3</name>
        <uri>https://github.com/ztruyen</uri>
    </author>
    <link rel="self" href="{base_url}/opds" type="application/atom+xml;profile=opds-catalog;kind=navigation"/>
    <link rel="start" href="{base_url}/opds" type="application/atom+xml;profile=opds-catalog;kind=navigation"/>
    <link rel="search" href="{base_url}/opds/search?q={{searchTerms}}" type="application/atom+xml"/>

    <entry>
        <title>🔥 Truyện Hot &amp; Đọc Nhiều</title>
        <id>urn:ztruyen:category:hot</id>
        <updated>{now}</updated>
        <content type="text">Danh sách các bộ truyện được đọc nhiều nhất trên mọi nguồn.</content>
        <link rel="subsection" href="{base_url}/opds/hot" type="application/atom+xml;profile=opds-catalog;kind=acquisition"/>
    </entry>

    <entry>
        <title>⚡ Mới Cập Nhật</title>
        <id>urn:ztruyen:category:latest</id>
        <updated>{now}</updated>
        <content type="text">Các tác phẩm và chương truyện mới cập nhật gần đây.</content>
        <link rel="subsection" href="{base_url}/opds/latest" type="application/atom+xml;profile=opds-catalog;kind=acquisition"/>
    </entry>

    <entry>
        <title>📚 Thể Loại Truyện</title>
        <id>urn:ztruyen:category:genres</id>
        <updated>{now}</updated>
        <content type="text">Duyệt truyện theo thể loại: Tiên Hiệp, Kiếm Hiệp, Huyền Huyễn, Linh Dị...</content>
        <link rel="subsection" href="{base_url}/opds/genres" type="application/atom+xml;profile=opds-catalog;kind=navigation"/>
    </entry>

    <entry>
        <title>🌐 Nguồn Cào Truyện</title>
        <id>urn:ztruyen:category:sources</id>
        <updated>{now}</updated>
        <content type="text">Duyệt theo từng nguồn: Storya.click, AkayTruyen, Con Đường Bá Chủ...</content>
        <link rel="subsection" href="{base_url}/opds/sources" type="application/atom+xml;profile=opds-catalog;kind=navigation"/>
    </entry>
</feed>
"""
        return xml.strip()

    @staticmethod
    def build_story_list_feed(
        feed_id: str,
        title: str,
        stories: Sequence[StorySummary],
        self_url: str,
        base_url: str = "",
    ) -> str:
        """Construct Acquisition Feed listing multiple stories."""
        now = format_iso_time()
        xml_entries: list[str] = []

        for s in stories:
            escaped_title = html.escape(s.title)
            escaped_author = html.escape(s.author)
            story_book_url = f"{base_url}/opds/book/{s.source_id}/{s.slug}"
            entry_id = f"urn:ztruyen:story:{s.source_id}:{s.slug}"

            cover_tag = ""
            if s.cover_url:
                escaped_cover = html.escape(s.cover_url)
                cover_tag = (
                    f'<link rel="http://opds-spec.org/image" href="{escaped_cover}" type="image/jpeg"/>\n'
                    f'        <link rel="http://opds-spec.org/image/thumbnail" href="{escaped_cover}" type="image/jpeg"/>'
                )

            entry_xml = f"""    <entry>
        <title>{escaped_title}</title>
        <id>{entry_id}</id>
        <updated>{now}</updated>
        <author><name>{escaped_author}</name></author>
        <content type="text">Nguồn: {s.source_id} | Tác giả: {escaped_author}</content>
        <link rel="subsection" href="{story_book_url}" type="application/atom+xml;profile=opds-catalog;kind=acquisition"/>
        {cover_tag}
    </entry>"""
            xml_entries.append(entry_xml)

        entries_str = "\n".join(xml_entries)
        xml = f"""<?xml version="1.0" encoding="utf-8"?>
<feed xmlns="http://www.w3.org/2005/Atom"
      xmlns:dc="http://purl.org/dc/terms/"
      xmlns:opds="http://opds-spec.org/2010/catalog">
    <id>{html.escape(feed_id)}</id>
    <title>{html.escape(title)}</title>
    <updated>{now}</updated>
    <link rel="self" href="{html.escape(self_url)}" type="application/atom+xml;profile=opds-catalog;kind=acquisition"/>
    <link rel="start" href="{base_url}/opds" type="application/atom+xml;profile=opds-catalog;kind=navigation"/>
    <link rel="search" href="{base_url}/opds/search?q={{searchTerms}}" type="application/atom+xml"/>

{entries_str}
</feed>
"""
        return xml.strip()

    @staticmethod
    def build_book_volumes_feed(
        story: Story,
        volume_slices: Sequence[dict[str, int]],
        base_url: str = "",
    ) -> str:
        """Construct Story Detail Feed with downloadable Volume EPUBs."""
        now = format_iso_time(story.updated_at)
        escaped_title = html.escape(story.title)
        escaped_author = html.escape(story.author)
        escaped_desc = html.escape(story.description or f"Tác phẩm {story.title}")
        feed_id = f"urn:ztruyen:book:{story.source_id}:{story.slug}"
        self_url = f"{base_url}/opds/book/{story.source_id}/{story.slug}"

        cover_tags = ""
        if story.cover_url:
            escaped_cover = html.escape(story.cover_url)
            cover_tags = (
                f'<link rel="http://opds-spec.org/image" href="{escaped_cover}" type="image/jpeg"/>\n'
                f'    <link rel="http://opds-spec.org/image/thumbnail" href="{escaped_cover}" type="image/jpeg"/>'
            )

        entries: list[str] = []
        for s in volume_slices:
            vol_idx = s["vol_index"]
            start_ch = s["start_order"]
            end_ch = s["end_order"]
            vol_title = f"{story.title} — Tập {vol_idx:02d} (Chương {start_ch} - {end_ch})"
            vol_filename = f"ztruyen_{story.source_id}_{story.slug}_v{vol_idx:02d}.epub"
            download_url = f"{base_url}/opds/download/{story.source_id}/{story.slug}/{vol_filename}"
            vol_id = f"urn:ztruyen:volume:{story.source_id}:{story.slug}:v{vol_idx:02d}"

            entry = f"""    <entry>
        <title>{html.escape(vol_title)}</title>
        <id>{vol_id}</id>
        <updated>{now}</updated>
        <author><name>{escaped_author}</name></author>
        <summary type="text">Bao gồm {s['count']} chương ({start_ch} đến {end_ch}). Tối ưu cho Xteink X3 &amp; KOReader.</summary>
        <link rel="http://opds-spec.org/acquisition"
              href="{download_url}"
              type="application/epub+zip"
              title="Tải EPUB Tập {vol_idx:02d}"/>
        {cover_tags}
    </entry>"""
            entries.append(entry)

        entries_str = "\n".join(entries)

        xml = f"""<?xml version="1.0" encoding="utf-8"?>
<feed xmlns="http://www.w3.org/2005/Atom"
      xmlns:dc="http://purl.org/dc/terms/"
      xmlns:opds="http://opds-spec.org/2010/catalog">
    <id>{feed_id}</id>
    <title>{escaped_title}</title>
    <updated>{now}</updated>
    <author><name>{escaped_author}</name></author>
    <content type="text">{escaped_desc}</content>
    <link rel="self" href="{self_url}" type="application/atom+xml;profile=opds-catalog;kind=acquisition"/>
    <link rel="start" href="{base_url}/opds" type="application/atom+xml;profile=opds-catalog;kind=navigation"/>
    {cover_tags}

{entries_str}
</feed>
"""
        return xml.strip()
