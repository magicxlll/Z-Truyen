"""OPDS 1.2 XML Atom Feed generator for e-reader catalog navigation and book acquisition."""

import html
from datetime import datetime, timezone
from typing import Sequence
from app.domain.models import StorySummary, Story


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
        """Construct Root OPDS Catalog Feed with Source selection on top followed by categories."""
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

    <!-- 1. CHỌN KHO NGUỒN TRUYỆN (ĐƯỢC ĐẶT LÊN TRÊN CÙNG) -->
    <entry>
        <title>🌐 Chọn Nguồn Truyện (Tất Cả Nguồn)</title>
        <id>urn:ztruyen:category:sources</id>
        <updated>{now}</updated>
        <content type="text">Khám phá theo từng kho truyện: Storya.click, AkayTruyen, Con Đường Bá Chủ...</content>
        <link rel="subsection" href="{base_url}/opds/sources" type="application/atom+xml;profile=opds-catalog;kind=navigation"/>
    </entry>

    <entry>
        <title>📚 Kho Truyện: Storya (storya.click)</title>
        <id>urn:ztruyen:source:storyaclick:root</id>
        <updated>{now}</updated>
        <content type="text">Kho truyện dịch và convert phong phú từ Storya.click.</content>
        <link rel="subsection" href="{base_url}/opds/source/storyaclick" type="application/atom+xml;profile=opds-catalog;kind=navigation"/>
    </entry>

    <entry>
        <title>🌟 Kho Truyện: AkayTruyen (akaytruyen.com)</title>
        <id>urn:ztruyen:source:akaytruyen:root</id>
        <updated>{now}</updated>
        <content type="text">Tác phẩm tiên hiệp, huyền huyễn chọn lọc từ AkayTruyen.</content>
        <link rel="subsection" href="{base_url}/opds/source/akaytruyen" type="application/atom+xml;profile=opds-catalog;kind=navigation"/>
    </entry>

    <entry>
        <title>⚔️ Kho Truyện: Con Đường Bá Chủ</title>
        <id>urn:ztruyen:source:conduongbachu:root</id>
        <updated>{now}</updated>
        <content type="text">Chính truyện và ngoại truyện Con Đường Bá Chủ (Akay Hậu).</content>
        <link rel="subsection" href="{base_url}/opds/source/conduongbachu" type="application/atom+xml;profile=opds-catalog;kind=navigation"/>
    </entry>

    <!-- 2. CÁC DANH MỤC PHÂN LOẠI TOÀN HỆ THỐNG -->
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
        <title>✅ Truyện Hoàn Thành (Full Trọn Bộ)</title>
        <id>urn:ztruyen:category:completed</id>
        <updated>{now}</updated>
        <content type="text">Tuyển tập các bộ truyện đã hoàn tất trọn bộ.</content>
        <link rel="subsection" href="{base_url}/opds/completed" type="application/atom+xml;profile=opds-catalog;kind=acquisition"/>
    </entry>

    <entry>
        <title>📂 Thể Loại Truyện</title>
        <id>urn:ztruyen:category:genres</id>
        <updated>{now}</updated>
        <content type="text">Duyệt truyện theo thể loại: Tiên Hiệp, Kiếm Hiệp, Huyền Huyễn, Linh Dị...</content>
        <link rel="subsection" href="{base_url}/opds/genres" type="application/atom+xml;profile=opds-catalog;kind=navigation"/>
    </entry>
</feed>
"""
        return xml.strip()

    @staticmethod
    def build_source_root_feed(source_id: str, source_name: str, base_url: str = "") -> str:
        """Construct Dedicated Navigation Feed for a single Source."""
        now = format_iso_time()
        xml = f"""<?xml version="1.0" encoding="utf-8"?>
<feed xmlns="http://www.w3.org/2005/Atom"
      xmlns:dc="http://purl.org/dc/terms/"
      xmlns:opds="http://opds-spec.org/2010/catalog">
    <id>urn:ztruyen:source:{source_id}</id>
    <title>📚 {html.escape(source_name)}</title>
    <updated>{now}</updated>
    <link rel="self" href="{base_url}/opds/source/{source_id}" type="application/atom+xml;profile=opds-catalog;kind=navigation"/>
    <link rel="start" href="{base_url}/opds" type="application/atom+xml;profile=opds-catalog;kind=navigation"/>
    <link rel="search" href="{base_url}/opds/search?source={source_id}&amp;q={{searchTerms}}" type="application/atom+xml"/>

    <entry>
        <title>🔥 Truyện Hot ({html.escape(source_name)})</title>
        <id>urn:ztruyen:source:{source_id}:hot</id>
        <updated>{now}</updated>
        <content type="text">Các truyện được đọc nhiều nhất từ nguồn {html.escape(source_name)}.</content>
        <link rel="subsection" href="{base_url}/opds/hot?source={source_id}" type="application/atom+xml;profile=opds-catalog;kind=acquisition"/>
    </entry>

    <entry>
        <title>⚡ Mới Cập Nhật ({html.escape(source_name)})</title>
        <id>urn:ztruyen:source:{source_id}:latest</id>
        <updated>{now}</updated>
        <content type="text">Các tác phẩm mới cập nhật từ nguồn {html.escape(source_name)}.</content>
        <link rel="subsection" href="{base_url}/opds/latest?source={source_id}" type="application/atom+xml;profile=opds-catalog;kind=acquisition"/>
    </entry>

    <entry>
        <title>✅ Truyện Hoàn Thành ({html.escape(source_name)})</title>
        <id>urn:ztruyen:source:{source_id}:completed</id>
        <updated>{now}</updated>
        <content type="text">Các truyện đã hoàn thành từ nguồn {html.escape(source_name)}.</content>
        <link rel="subsection" href="{base_url}/opds/completed?source={source_id}" type="application/atom+xml;profile=opds-catalog;kind=acquisition"/>
    </entry>

    <entry>
        <title>🔍 Tìm Kiếm Trong {html.escape(source_name)}</title>
        <id>urn:ztruyen:source:{source_id}:search</id>
        <updated>{now}</updated>
        <content type="text">Tìm kiếm tác phẩm thuộc nguồn {html.escape(source_name)}.</content>
        <link rel="subsection" href="{base_url}/opds/search?source={source_id}&amp;q=" type="application/atom+xml;profile=opds-catalog;kind=acquisition"/>
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
        prev_url: str | None = None,
        next_url: str | None = None,
    ) -> str:
        """Construct Acquisition Feed listing multiple stories with high-quality E-ink cover proxy."""
        now = format_iso_time()
        xml_entries: list[str] = []

        for s in stories:
            escaped_title = html.escape(s.title)
            escaped_author = html.escape(s.author)
            story_book_url = f"{base_url}/opds/book/{s.source_id}/{s.slug}"
            entry_id = f"urn:ztruyen:story:{s.source_id}:{s.slug}"

            # High quality JPEG cover endpoint for E-ink display
            cover_proxy_url = f"{base_url}/opds/cover/{s.source_id}/{s.slug}"
            cover_tag = (
                f'<link rel="http://opds-spec.org/image" href="{cover_proxy_url}" type="image/jpeg"/>\n'
                f'        <link rel="http://opds-spec.org/image/thumbnail" href="{cover_proxy_url}" type="image/jpeg"/>'
            )

            entry_xml = f"""    <entry>
        <title>{escaped_title}</title>
        <id>{entry_id}</id>
        <updated>{now}</updated>
        <author><name>{escaped_author}</name></author>
        <content type="text">Nguồn: {s.source_id.upper()} | Tác giả: {escaped_author}</content>
        <link rel="subsection" href="{story_book_url}" type="application/atom+xml;profile=opds-catalog;kind=acquisition"/>
        {cover_tag}
    </entry>"""
            xml_entries.append(entry_xml)

        entries_str = "\n".join(xml_entries)

        pagination_links = ""
        if prev_url:
            pagination_links += f'    <link rel="previous" href="{html.escape(prev_url)}" type="application/atom+xml;profile=opds-catalog;kind=acquisition"/>\n'
        if next_url:
            pagination_links += f'    <link rel="next" href="{html.escape(next_url)}" type="application/atom+xml;profile=opds-catalog;kind=acquisition"/>\n'

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
{pagination_links}
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
        """Construct Story Detail Feed with all Acquisition Options: Single-chapter, Volumes, Full story."""
        now = format_iso_time(story.updated_at)
        escaped_title = html.escape(story.title)
        clean_author = story.title if (not story.author or story.author == "Đang cập nhật") else story.author
        escaped_author = html.escape(clean_author)
        escaped_desc = html.escape(story.description or f"Tác phẩm {story.title}")
        feed_id = f"urn:ztruyen:book:{story.source_id}:{story.slug}"
        self_url = f"{base_url}/opds/book/{story.source_id}/{story.slug}"

        cover_proxy_url = f"{base_url}/opds/cover/{story.source_id}/{story.slug}"
        cover_tags = (
            f'<link rel="http://opds-spec.org/image" href="{cover_proxy_url}" type="image/jpeg"/>\n'
            f'    <link rel="http://opds-spec.org/image/thumbnail" href="{cover_proxy_url}" type="image/jpeg"/>'
        )

        entries: list[str] = []

        # 1. ĐỌC TỪNG CHƯƠNG (STREAMING 0.3S) - SẮP XẾP TỪ ĐẦU (1 -> N)
        chapters_asc_url = f"{base_url}/opds/book/{story.source_id}/{story.slug}/chapters?sort=asc"
        entries.append(f"""    <entry>
        <title>⚡ Đọc Từng Chương (Từ Đầu 1 ➔ N)</title>
        <id>urn:ztruyen:action:{story.source_id}:{story.slug}:chapters_asc</id>
        <updated>{now}</updated>
        <author><name>{escaped_author}</name></author>
        <summary type="text">Tải tức thì 0.3s/chương &amp; tự động tải ngầm 3 chương kế tiếp khi đọc.</summary>
        <link rel="subsection" href="{chapters_asc_url}" type="application/atom+xml;profile=opds-catalog;kind=acquisition"/>
        {cover_tags}
    </entry>""")

        # 2. ĐỌC TỪNG CHƯƠNG - SẮP XẾP MỚI NHẤT (N -> 1)
        chapters_desc_url = f"{base_url}/opds/book/{story.source_id}/{story.slug}/chapters?sort=desc"
        entries.append(f"""    <entry>
        <title>⚡ Đọc Chương Mới Nhất (N ➔ 1)</title>
        <id>urn:ztruyen:action:{story.source_id}:{story.slug}:chapters_desc</id>
        <updated>{now}</updated>
        <author><name>{escaped_author}</name></author>
        <summary type="text">Xem các chương mới nhất vừa cập nhật để đọc tiếp.</summary>
        <link rel="subsection" href="{chapters_desc_url}" type="application/atom+xml;profile=opds-catalog;kind=acquisition"/>
        {cover_tags}
    </entry>""")

        # 3. ĐỌC NGAY CHƯƠNG 1 (TRỰC TIẾP 1-CLICK)
        c1_url = f"{base_url}/opds/download/{story.source_id}/{story.slug}/ztruyen_{story.source_id}_{story.slug}_c0001.epub"
        entries.append(f"""    <entry>
        <title>{escaped_title} — Chương 1</title>
        <id>urn:ztruyen:chapter:{story.source_id}:{story.slug}:c0001</id>
        <updated>{now}</updated>
        <author><name>{escaped_author}</name></author>
        <summary type="text">Tải nhanh chương 1 (15KB) để đọc tức thì.</summary>
        <link rel="http://opds-spec.org/acquisition" href="{c1_url}" type="application/epub+zip" title="Tải &amp; Đọc Chương 1"/>
        {cover_tags}
    </entry>""")

        # 4. TẢI TRỌN BỘ (ALL CHƯƠNG)
        total_ch = story.total_chapters or (volume_slices[-1]["end_order"] if volume_slices else 1)
        all_url = f"{base_url}/opds/download/{story.source_id}/{story.slug}/ztruyen_{story.source_id}_{story.slug}_all.epub"
        entries.append(f"""    <entry>
        <title>{escaped_title} — Trọn Bộ ({total_ch} Chương)</title>
        <id>urn:ztruyen:volume:{story.source_id}:{story.slug}:all</id>
        <updated>{now}</updated>
        <author><name>{escaped_author}</name></author>
        <summary type="text">Tải toàn bộ {total_ch} chương thành 1 file EPUB hoàn chỉnh để lưu offline.</summary>
        <link rel="http://opds-spec.org/acquisition" href="{all_url}" type="application/epub+zip" title="Tải Trọn Bộ ({total_ch} Chương)"/>
        {cover_tags}
    </entry>""")

        # 5. CÁC TẬP GOM SẴN (50 CHƯƠNG / TẬP)
        for s in volume_slices:
            vol_idx = s["vol_index"]
            start_ch = s["start_order"]
            end_ch = s["end_order"]
            vol_title = f"{story.title} — Tập {vol_idx:02d} (Chương {start_ch}-{end_ch})"
            vol_filename = f"ztruyen_{story.source_id}_{story.slug}_v{vol_idx:02d}.epub"
            download_url = f"{base_url}/opds/download/{story.source_id}/{story.slug}/{vol_filename}"
            vol_id = f"urn:ztruyen:volume:{story.source_id}:{story.slug}:v{vol_idx:02d}"

            entry = f"""    <entry>
        <title>{html.escape(vol_title)}</title>
        <id>{vol_id}</id>
        <updated>{now}</updated>
        <author><name>{escaped_author}</name></author>
        <summary type="text">Bao gồm {s['count']} chương ({start_ch} đến {end_ch}). Chuẩn hóa KOSync cho Xteink X3.</summary>
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

    @staticmethod
    def build_book_chapters_feed(
        story: Story,
        chapters: list,
        base_url: str = "",
        sort_order: str = "asc",
    ) -> str:
        """Construct Story Detail Feed listing individual chapters for near-online instant reading."""
        now = format_iso_time(story.updated_at)
        escaped_title = html.escape(story.title)
        clean_author = story.title if (not story.author or story.author == "Đang cập nhật") else story.author
        escaped_author = html.escape(clean_author)
        escaped_desc = html.escape(story.description or f"Tác phẩm {story.title}")
        feed_id = f"urn:ztruyen:book:{story.source_id}:{story.slug}:chapters:{sort_order}"
        self_url = f"{base_url}/opds/book/{story.source_id}/{story.slug}/chapters?sort={sort_order}"

        cover_proxy_url = f"{base_url}/opds/cover/{story.source_id}/{story.slug}"
        cover_tags = (
            f'<link rel="http://opds-spec.org/image" href="{cover_proxy_url}" type="image/jpeg"/>\n'
            f'    <link rel="http://opds-spec.org/image/thumbnail" href="{cover_proxy_url}" type="image/jpeg"/>'
        )

        entries: list[str] = []
        for c in chapters:
            order = getattr(c, "order", 1)
            raw_title = getattr(c, "title", f"Chương {order}")
            chap_display_title = f"{story.title} — {raw_title}"
            chap_filename = f"ztruyen_{story.source_id}_{story.slug}_c{order:04d}.epub"
            download_url = f"{base_url}/opds/download/{story.source_id}/{story.slug}/{chap_filename}"
            chap_id = f"urn:ztruyen:chapter:{story.source_id}:{story.slug}:c{order:04d}"

            entry = f"""    <entry>
        <title>{html.escape(chap_display_title)}</title>
        <id>{chap_id}</id>
        <updated>{now}</updated>
        <author><name>{escaped_author}</name></author>
        <summary type="text">{escaped_title} — Chương {order}. Tải tức thì 0.3s &amp; tự động tải ngầm 3 chương kế tiếp.</summary>
        <link rel="http://opds-spec.org/acquisition"
              href="{download_url}"
              type="application/epub+zip"
              title="Đọc Chương {order}"/>
        {cover_tags}
    </entry>"""
            entries.append(entry)

        entries_str = "\n".join(entries)

        sort_label = "Mới nhất (N ➔ 1)" if sort_order == "desc" else "Từ đầu (1 ➔ N)"
        xml = f"""<?xml version="1.0" encoding="utf-8"?>
<feed xmlns="http://www.w3.org/2005/Atom"
      xmlns:dc="http://purl.org/dc/terms/"
      xmlns:opds="http://opds-spec.org/2010/catalog">
    <id>{feed_id}</id>
    <title>{escaped_title} — Danh Sách Chương ({sort_label})</title>
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
