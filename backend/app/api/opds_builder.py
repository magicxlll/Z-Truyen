"""OPDS 1.2 XML Atom Feed generator for e-reader catalog navigation and book acquisition."""

from __future__ import annotations

import html
import re
from datetime import datetime, timezone
from typing import Sequence
from app.domain.models import StorySummary, Story


def format_iso_time(dt: datetime | None = None) -> str:
    """Format datetime in UTC ISO 8601 string."""
    d = dt or datetime.now(timezone.utc)
    if d.tzinfo is None:
        d = d.replace(tzinfo=timezone.utc)
    return d.isoformat()


def clean_story_title(title: str) -> str:
    """Clean status badges and suffixes from story titles."""
    clean = re.sub(r"(?:Đang\s*viết|Hoàn\s*thành|Full|Hot|New|VIP)+$", "", title, flags=re.IGNORECASE).strip()
    clean = re.sub(r"\s+(Full|Hot|New|Đang viết)\s*$", "", clean, flags=re.IGNORECASE).strip()
    return clean or title


def format_chapter_title(order: int, raw_title: str, story_title: str = "") -> str:
    """Format chapter title cleanly as 'Chương {order}_{tên chương}' without trailing story/author names."""
    clean = raw_title.strip()
    if story_title and clean.startswith(story_title):
        clean = clean[len(story_title):].strip(" —-:_")

    # Match existing chapter prefixes (Chương X, Hồi X, Chapter X, Tiết X)
    m = re.match(r"^(?:chương|hồi|chap|chapter|tiết)\s*\d+[\s:._–—-]*(.*)$", clean, re.IGNORECASE)
    if m:
        sub_name = m.group(1).strip()
        if sub_name:
            return f"Chương {order}_{sub_name}"
        return f"Chương {order}"

    if clean and clean != f"Chương {order}":
        return f"Chương {order}_{clean}"
    return f"Chương {order}"


class OpdsBuilder:
    """Helper to construct standard OPDS 1.2 XML Atom Feed documents."""

    @staticmethod
    def build_root_feed(
        last_read: dict | None = None,
        current_source_id: str | None = None,
        base_url: str = "",
    ) -> str:
        """Construct Root OPDS Catalog Feed directly listing available story sources and key categories."""
        now = format_iso_time()
        entries: list[str] = []

        # 1. TẤT CẢ NGUỒN TRUYỆN
        entries.append(f"""    <entry>
        <title>🌐 Chọn Nguồn Truyện</title>
        <id>urn:ztruyen:category:sources</id>
        <updated>{now}</updated>
        <content type="text">Khám phá theo từng kho truyện: Storya.click, AkayTruyen, Con Đường Bá Chủ...</content>
        <link rel="subsection" href="{html.escape(base_url)}/opds/sources" type="application/atom+xml;profile=opds-catalog;kind=navigation"/>
    </entry>""")

        # Nguồn Hiện Tại
        current_name = "Tất Cả Nguồn (Storya, Akay, CĐBC)"
        if current_source_id == "storyaclick":
            current_name = "Storya.click"
        elif current_source_id == "akaytruyen":
            current_name = "AkayTruyen"
        elif current_source_id == "conduongbachu":
            current_name = "Con Đường Bá Chủ"

        entries.append(f"""    <entry>
        <title>📚 Nguồn Hiện Tại: {html.escape(current_name)}</title>
        <id>urn:ztruyen:source:current</id>
        <updated>{now}</updated>
        <content type="text">Đang xem kho truyện từ: {html.escape(current_name)}</content>
        <link rel="subsection" href="{html.escape(base_url)}/opds/sources" type="application/atom+xml;profile=opds-catalog;kind=navigation"/>
    </entry>""")

        # 2. KHO TRUYỆN: STORYA.CLICK
        entries.append(f"""    <entry>
        <title>📚 Kho Truyện: Storya.click</title>
        <id>urn:ztruyen:source:storyaclick</id>
        <updated>{now}</updated>
        <content type="text">Khám phá hàng ngàn truyện dịch &amp; convert từ Storya.click.</content>
        <link rel="subsection" href="{html.escape(base_url)}/opds/source/storyaclick" type="application/atom+xml;profile=opds-catalog;kind=navigation"/>
    </entry>""")

        # 3. KHO TRUYỆN: AKAYTRUYEN
        entries.append(f"""    <entry>
        <title>📚 Kho Truyện: AkayTruyen</title>
        <id>urn:ztruyen:source:akaytruyen</id>
        <updated>{now}</updated>
        <content type="text">Tuyển tập tác phẩm đặc sắc từ AkayTruyen.</content>
        <link rel="subsection" href="{html.escape(base_url)}/opds/source/akaytruyen" type="application/atom+xml;profile=opds-catalog;kind=navigation"/>
    </entry>""")

        # 4. KHO TRUYỆN: CON ĐƯỜNG BÁ CHỦ
        entries.append(f"""    <entry>
        <title>📚 Kho Truyện: Con Đường Bá Chủ</title>
        <id>urn:ztruyen:source:conduongbachu</id>
        <updated>{now}</updated>
        <content type="text">Trang chuyên biệt tiểu thuyết Con Đường Bá Chủ (Full &amp; Ngoại truyện).</content>
        <link rel="subsection" href="{html.escape(base_url)}/opds/source/conduongbachu" type="application/atom+xml;profile=opds-catalog;kind=navigation"/>
    </entry>""")

        # 5. TRUYỆN MỚI CẬP NHẬT (TẤT CẢ NGUỒN)
        entries.append(f"""    <entry>
        <title>⚡ Truyện Mới Cập Nhật (Tổng hợp)</title>
        <id>urn:ztruyen:category:latest</id>
        <updated>{now}</updated>
        <content type="text">Các tác phẩm và chương truyện mới cập nhật từ tất cả nguồn.</content>
        <link rel="subsection" href="{html.escape(base_url)}/opds/latest" type="application/atom+xml;profile=opds-catalog;kind=acquisition"/>
    </entry>""")

        # 6. TRUYỆN HOT & ĐỌC NHIỀU
        entries.append(f"""    <entry>
        <title>🔥 Truyện Hot &amp; Đọc Nhiều</title>
        <id>urn:ztruyen:category:hot</id>
        <updated>{now}</updated>
        <content type="text">Danh sách các bộ truyện được đọc nhiều nhất.</content>
        <link rel="subsection" href="{html.escape(base_url)}/opds/hot" type="application/atom+xml;profile=opds-catalog;kind=acquisition"/>
    </entry>""")

        # 7. TRUYỆN HOÀN THÀNH
        entries.append(f"""    <entry>
        <title>✅ Truyện Hoàn Thành (Full Trọn Bộ)</title>
        <id>urn:ztruyen:category:completed</id>
        <updated>{now}</updated>
        <content type="text">Tuyển tập các bộ truyện đã hoàn tất trọn bộ.</content>
        <link rel="subsection" href="{html.escape(base_url)}/opds/completed" type="application/atom+xml;profile=opds-catalog;kind=acquisition"/>
    </entry>""")

        # 8. THỂ LOẠI TRUYỆN
        entries.append(f"""    <entry>
        <title>📂 Thể Loại Truyện</title>
        <id>urn:ztruyen:category:genres</id>
        <updated>{now}</updated>
        <content type="text">Duyệt truyện theo thể loại: Tiên Hiệp, Kiếm Hiệp, Huyền Huyễn, Linh Dị...</content>
        <link rel="subsection" href="{html.escape(base_url)}/opds/genres" type="application/atom+xml;profile=opds-catalog;kind=navigation"/>
    </entry>""")

        # 9. TÌM KIẾM TRUYỆN
        entries.append(f"""    <entry>
        <title>🔍 Tìm Kiếm Truyện</title>
        <id>urn:ztruyen:category:search</id>
        <updated>{now}</updated>
        <content type="text">Nhập từ khóa tìm kiếm tác phẩm trên bàn phím ảo.</content>
        <link rel="search" href="{html.escape(base_url)}/opds/search?q={{searchTerms}}" type="application/atom+xml"/>
    </entry>""")

        # 10. ĐỌC TIẾP (Nếu có truyện vừa đọc)
        if last_read:
            story_title = clean_story_title(last_read.get("story_title", "Truyện vừa đọc"))
            source_id = last_read.get("source_id", "storyaclick")
            story_slug = last_read.get("story_slug", "")
            chap_order = last_read.get("chap_order", 1)
            continue_url = f"{base_url}/opds/book/{source_id}/{story_slug}/chapters?start={chap_order}&limit=50&sort=asc"
            entries.append(f"""    <entry>
        <title>📖 Đọc Tiếp: {html.escape(story_title)} (Chương {chap_order})</title>
        <id>urn:ztruyen:continue:{source_id}:{story_slug}</id>
        <updated>{now}</updated>
        <content type="text">Tiếp tục đọc {html.escape(story_title)} (lần đọc gần nhất: Chương {chap_order})</content>
        <link rel="subsection" href="{html.escape(continue_url)}" type="application/atom+xml;profile=opds-catalog;kind=acquisition"/>
    </entry>""")

        entries_str = "\n".join(entries)
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
    <link rel="self" href="{html.escape(base_url)}/opds" type="application/atom+xml;profile=opds-catalog;kind=navigation"/>
    <link rel="start" href="{html.escape(base_url)}/opds" type="application/atom+xml;profile=opds-catalog;kind=navigation"/>
    <link rel="search" href="{html.escape(base_url)}/opds/search?q={{searchTerms}}" type="application/atom+xml"/>

{entries_str}
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
    <title>📚 Kho Truyện: {html.escape(source_name)}</title>
    <updated>{now}</updated>
    <link rel="self" href="{html.escape(base_url)}/opds/source/{source_id}" type="application/atom+xml;profile=opds-catalog;kind=navigation"/>
    <link rel="start" href="{html.escape(base_url)}/opds" type="application/atom+xml;profile=opds-catalog;kind=navigation"/>
    <link rel="search" href="{html.escape(base_url)}/opds/search?source={source_id}&amp;q={{searchTerms}}" type="application/atom+xml"/>

    <entry>
        <title>📚 Đang Xem Kho: {html.escape(source_name)}</title>
        <id>urn:ztruyen:source:{source_id}:indicator</id>
        <updated>{now}</updated>
        <content type="text">Bạn đang duyệt kho truyện {html.escape(source_name)}.</content>
        <link rel="self" href="{html.escape(base_url)}/opds/source/{source_id}" type="application/atom+xml;profile=opds-catalog;kind=navigation"/>
    </entry>

    <entry>
        <title>⚡ Truyện Mới Cập Nhật</title>
        <id>urn:ztruyen:source:{source_id}:latest</id>
        <updated>{now}</updated>
        <content type="text">Các tác phẩm mới cập nhật từ kho truyện {html.escape(source_name)}.</content>
        <link rel="subsection" href="{html.escape(base_url)}/opds/latest?source={source_id}" type="application/atom+xml;profile=opds-catalog;kind=acquisition"/>
    </entry>

    <entry>
        <title>🔥 Truyện Hot &amp; Đọc Nhiều</title>
        <id>urn:ztruyen:source:{source_id}:hot</id>
        <updated>{now}</updated>
        <content type="text">Các truyện được đọc nhiều nhất từ kho truyện {html.escape(source_name)}.</content>
        <link rel="subsection" href="{html.escape(base_url)}/opds/hot?source={source_id}" type="application/atom+xml;profile=opds-catalog;kind=acquisition"/>
    </entry>

    <entry>
        <title>✅ Truyện Hoàn Thành (Full Trọn Bộ)</title>
        <id>urn:ztruyen:source:{source_id}:completed</id>
        <updated>{now}</updated>
        <content type="text">Các truyện đã hoàn thành trọn bộ từ kho truyện {html.escape(source_name)}.</content>
        <link rel="subsection" href="{html.escape(base_url)}/opds/completed?source={source_id}" type="application/atom+xml;profile=opds-catalog;kind=acquisition"/>
    </entry>

    <entry>
        <title>📂 Thể Loại Truyện</title>
        <id>urn:ztruyen:source:{source_id}:genres</id>
        <updated>{now}</updated>
        <content type="text">Duyệt theo thể loại của {html.escape(source_name)}.</content>
        <link rel="subsection" href="{html.escape(base_url)}/opds/genres?source={source_id}" type="application/atom+xml;profile=opds-catalog;kind=navigation"/>
    </entry>

    <entry>
        <title>🌐 Chọn Kho Truyện Khác</title>
        <id>urn:ztruyen:source:{source_id}:all_sources</id>
        <updated>{now}</updated>
        <content type="text">Chuyển sang nguồn truyện khác.</content>
        <link rel="subsection" href="{html.escape(base_url)}/opds/sources" type="application/atom+xml;profile=opds-catalog;kind=navigation"/>
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
        """Construct Acquisition Feed listing multiple stories with original cover image support."""
        now = format_iso_time()
        xml_entries: list[str] = []

        for s in stories:
            clean_title = clean_story_title(s.title)
            escaped_title = html.escape(clean_title)
            escaped_author = html.escape(s.author)
            story_book_url = f"{base_url}/opds/book/{s.source_id}/{s.slug}"
            entry_id = f"urn:ztruyen:story:{s.source_id}:{s.slug}"

            # Original cover URL
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
        <content type="text">Tác giả: {escaped_author}</content>
        <link rel="subsection" href="{html.escape(story_book_url)}" type="application/atom+xml;profile=opds-catalog;kind=acquisition"/>
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
    <link rel="start" href="{html.escape(base_url)}/opds" type="application/atom+xml;profile=opds-catalog;kind=navigation"/>
    <link rel="search" href="{html.escape(base_url)}/opds/search?q={{searchTerms}}" type="application/atom+xml"/>
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
        clean_title = clean_story_title(story.title)
        escaped_title = html.escape(clean_title)
        escaped_desc = html.escape(story.description or f"Tác phẩm {clean_title}")
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
        total_ch = story.total_chapters or (volume_slices[-1]["end_order"] if volume_slices else 1)

        # 1. ĐỌC TỪNG CHƯƠNG (TỪ ĐẦU 1 -> N)
        chapters_asc_url = f"{base_url}/opds/book/{story.source_id}/{story.slug}/chapters?sort=asc"
        entries.append(f"""    <entry>
        <title>Đọc Từng Chương (Từ Đầu: 1 -> {total_ch})</title>
        <id>urn:ztruyen:action:{story.source_id}:{story.slug}:chapters_asc</id>
        <updated>{now}</updated>
        <summary type="text">Duyệt danh sách từ Chương 1 đến Chương {total_ch}.</summary>
        <link rel="subsection" href="{html.escape(chapters_asc_url)}" type="application/atom+xml;profile=opds-catalog;kind=acquisition"/>
        {cover_tags}
    </entry>""")

        # 2. ĐỌC TỪNG CHƯƠNG (MỚI NHẤT N -> 1)
        chapters_desc_url = f"{base_url}/opds/book/{story.source_id}/{story.slug}/chapters?sort=desc"
        entries.append(f"""    <entry>
        <title>Đọc Từng Chương (Mới Nhất: {total_ch} -> 1)</title>
        <id>urn:ztruyen:action:{story.source_id}:{story.slug}:chapters_desc</id>
        <updated>{now}</updated>
        <summary type="text">Duyệt danh sách từ các chương mới nhất trở về trước.</summary>
        <link rel="subsection" href="{html.escape(chapters_desc_url)}" type="application/atom+xml;profile=opds-catalog;kind=acquisition"/>
        {cover_tags}
    </entry>""")

        # 3. ĐỌC NGAY CHƯƠNG 1
        c1_url = f"{base_url}/opds/download/{story.source_id}/{story.slug}/ztruyen_{story.source_id}_{story.slug}_c0001.epub"
        entries.append(f"""    <entry>
        <title>Chương 1</title>
        <id>urn:ztruyen:chapter:{story.source_id}:{story.slug}:c0001</id>
        <updated>{now}</updated>
        <summary type="text">Tải nhanh chương 1 để đọc tức thì.</summary>
        <link rel="http://opds-spec.org/acquisition" href="{html.escape(c1_url)}" type="application/epub+zip" title="Tải &amp; Đọc Chương 1"/>
        {cover_tags}
    </entry>""")

        # 4. TẢI TRỌN BỘ (ALL CHƯƠNG)
        all_url = f"{base_url}/opds/download/{story.source_id}/{story.slug}/ztruyen_{story.source_id}_{story.slug}_all.epub"
        entries.append(f"""    <entry>
        <title>Trọn Bộ ({total_ch} Chương)</title>
        <id>urn:ztruyen:volume:{story.source_id}:{story.slug}:all</id>
        <updated>{now}</updated>
        <summary type="text">Tải toàn bộ {total_ch} chương thành 1 file EPUB hoàn chỉnh để lưu offline.</summary>
        <link rel="http://opds-spec.org/acquisition" href="{html.escape(all_url)}" type="application/epub+zip" title="Tải Trọn Bộ ({total_ch} Chương)"/>
        {cover_tags}
    </entry>""")

        # 5. CÁC TẬP GOM SẴN (50 CHƯƠNG / TẬP)
        for s in volume_slices:
            vol_idx = s["vol_index"]
            start_ch = s["start_order"]
            end_ch = s["end_order"]
            vol_title = f"Tập {vol_idx:02d} (Chương {start_ch}-{end_ch})"
            vol_filename = f"ztruyen_{story.source_id}_{story.slug}_v{vol_idx:02d}.epub"
            download_url = f"{base_url}/opds/download/{story.source_id}/{story.slug}/{vol_filename}"
            vol_id = f"urn:ztruyen:volume:{story.source_id}:{story.slug}:v{vol_idx:02d}"

            entry = f"""    <entry>
        <title>{html.escape(vol_title)}</title>
        <id>{vol_id}</id>
        <updated>{now}</updated>
        <summary type="text">Bao gồm {s['count']} chương ({start_ch} đến {end_ch}). Chuẩn hóa KOSync cho Xteink X3.</summary>
        <link rel="http://opds-spec.org/acquisition"
              href="{html.escape(download_url)}"
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
    <author><name>{html.escape(story.author or 'Đang cập nhật')}</name></author>
    <content type="text">{escaped_desc}</content>
    <link rel="self" href="{html.escape(self_url)}" type="application/atom+xml;profile=opds-catalog;kind=acquisition"/>
    <link rel="start" href="{html.escape(base_url)}/opds" type="application/atom+xml;profile=opds-catalog;kind=navigation"/>
    {cover_tags}

{entries_str}
</feed>
"""
        return xml.strip()

    @staticmethod
    def build_chapter_ranges_feed(
        story: Story,
        total_chapters: int,
        chapters_per_range: int = 50,
        last_read_order: int | None = None,
        base_url: str = "",
        sort_order: str = "asc",
    ) -> str:
        """Construct Navigation Feed listing chapter range blocks (50 chapters/range) for long stories."""
        now = format_iso_time(story.updated_at)
        clean_title = clean_story_title(story.title)
        escaped_title = html.escape(clean_title)
        escaped_desc = html.escape(story.description or f"Tác phẩm {clean_title}")
        feed_id = f"urn:ztruyen:book:{story.source_id}:{story.slug}:ranges:{sort_order}"
        self_url = f"{base_url}/opds/book/{story.source_id}/{story.slug}/chapters?sort={sort_order}"

        cover_tags = ""
        if story.cover_url:
            escaped_cover = html.escape(story.cover_url)
            cover_tags = (
                f'<link rel="http://opds-spec.org/image" href="{escaped_cover}" type="image/jpeg"/>\n'
                f'    <link rel="http://opds-spec.org/image/thumbnail" href="{escaped_cover}" type="image/jpeg"/>'
            )

        entries: list[str] = []

        # 1. ĐỌC TIẾP (Nếu có chương đọc dở)
        if last_read_order and last_read_order > 0:
            lr_range_start = ((last_read_order - 1) // chapters_per_range) * chapters_per_range + 1
            lr_range_end = min(lr_range_start + chapters_per_range - 1, total_chapters)
            lr_url = f"{base_url}/opds/book/{story.source_id}/{story.slug}/chapters?start={lr_range_start}&limit={chapters_per_range}&sort={sort_order}"
            entries.append(f"""    <entry>
        <title>Đọc Tiếp: Chương {last_read_order} (Khối {lr_range_start}-{lr_range_end})</title>
        <id>urn:ztruyen:range:{story.source_id}:{story.slug}:continue:{last_read_order}</id>
        <updated>{now}</updated>
        <summary type="text">Tiếp tục từ Chương {last_read_order}</summary>
        <link rel="subsection" href="{html.escape(lr_url)}" type="application/atom+xml;profile=opds-catalog;kind=acquisition"/>
        {cover_tags}
    </entry>""")

        # 2. CÁC KHỐI CHƯƠNG (50 CHƯƠNG / KHỐI)
        ranges: list[tuple[int, int]] = []
        start = 1
        while start <= total_chapters:
            end = min(start + chapters_per_range - 1, total_chapters)
            ranges.append((start, end))
            start = end + 1

        if sort_order == "desc":
            ranges.reverse()

        for s_order, e_order in ranges:
            count = e_order - s_order + 1
            start_param = e_order if sort_order == "desc" else s_order
            range_url = f"{base_url}/opds/book/{story.source_id}/{story.slug}/chapters?start={start_param}&limit={count}&sort={sort_order}"
            range_id = f"urn:ztruyen:range:{story.source_id}:{story.slug}:r{s_order:04d}_{e_order:04d}_{sort_order}"
            extra_label = " (Mới nhất)" if sort_order == "desc" and e_order == total_chapters else ""
            entry = f"""    <entry>
        <title>Chương {s_order} - {e_order} ({count} Chương){extra_label}</title>
        <id>{range_id}</id>
        <updated>{now}</updated>
        <summary type="text">Danh sách các chương từ Chương {s_order} đến Chương {e_order}</summary>
        <link rel="subsection" href="{html.escape(range_url)}" type="application/atom+xml;profile=opds-catalog;kind=acquisition"/>
        {cover_tags}
    </entry>"""
            entries.append(entry)

        entries_str = "\n".join(entries)
        sort_name = "Mới Nhất N -> 1" if sort_order == "desc" else "Từ Đầu 1 -> N"
        xml = f"""<?xml version="1.0" encoding="utf-8"?>
<feed xmlns="http://www.w3.org/2005/Atom"
      xmlns:dc="http://purl.org/dc/terms/"
      xmlns:opds="http://opds-spec.org/2010/catalog">
    <id>{feed_id}</id>
    <title>{escaped_title} — Chọn Khối Chương ({sort_name})</title>
    <updated>{now}</updated>
    <author><name>{html.escape(story.author or 'Đang cập nhật')}</name></author>
    <content type="text">{escaped_desc}</content>
    <link rel="self" href="{html.escape(self_url)}" type="application/atom+xml;profile=opds-catalog;kind=navigation"/>
    <link rel="start" href="{html.escape(base_url)}/opds" type="application/atom+xml;profile=opds-catalog;kind=navigation"/>
    <link rel="up" href="{html.escape(base_url)}/opds/book/{story.source_id}/{story.slug}" type="application/atom+xml;profile=opds-catalog;kind=acquisition"/>
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
        range_label: str = "",
        self_url: str = "",
        prev_url: str | None = None,
        next_url: str | None = None,
    ) -> str:
        """Construct Story Detail Feed listing individual chapters.
        Layout:
          Title: Chương {order}_{tên chương}
          Author: Omitted to prevent CrossVi from appending ' - author' suffix to every line.
        """
        now = format_iso_time(story.updated_at)
        clean_title = clean_story_title(story.title)
        escaped_title = html.escape(clean_title)
        escaped_desc = html.escape(story.description or f"Tác phẩm {clean_title}")
        
        feed_id_suffix = f":{range_label}" if range_label else f":{sort_order}"
        feed_id = f"urn:ztruyen:book:{story.source_id}:{story.slug}:chapters{feed_id_suffix}"
        if not self_url:
            self_url = f"{base_url}/opds/book/{story.source_id}/{story.slug}/chapters?sort={sort_order}"

        cover_tags = ""
        if story.cover_url:
            escaped_cover = html.escape(story.cover_url)
            cover_tags = (
                f'<link rel="http://opds-spec.org/image" href="{escaped_cover}" type="image/jpeg"/>\n'
                f'    <link rel="http://opds-spec.org/image/thumbnail" href="{escaped_cover}" type="image/jpeg"/>'
            )

        entries: list[str] = []
        for c in chapters:
            order = getattr(c, "order", 1)
            raw_title = getattr(c, "title", f"Chương {order}")
            formatted_title = format_chapter_title(order, raw_title, story.title)

            chap_filename = f"ztruyen_{story.source_id}_{story.slug}_c{order:04d}.epub"
            download_url = f"{base_url}/opds/download/{story.source_id}/{story.slug}/{chap_filename}"
            chap_id = f"urn:ztruyen:chapter:{story.source_id}:{story.slug}:c{order:04d}"

            entry = f"""    <entry>
        <title>{html.escape(formatted_title)}</title>
        <id>{chap_id}</id>
        <updated>{now}</updated>
        <summary type="text">{html.escape(formatted_title)}</summary>
        <link rel="http://opds-spec.org/acquisition"
              href="{html.escape(download_url)}"
              type="application/epub+zip"
              title="Đọc Chương {order}"/>
        {cover_tags}
    </entry>"""
            entries.append(entry)

        entries_str = "\n".join(entries)

        pagination_links = ""
        if prev_url:
            pagination_links += f'    <link rel="previous" href="{html.escape(prev_url)}" type="application/atom+xml;profile=opds-catalog;kind=acquisition"/>\n'
        if next_url:
            pagination_links += f'    <link rel="next" href="{html.escape(next_url)}" type="application/atom+xml;profile=opds-catalog;kind=acquisition"/>\n'

        feed_title_extra = f" ({range_label})" if range_label else ""
        xml = f"""<?xml version="1.0" encoding="utf-8"?>
<feed xmlns="http://www.w3.org/2005/Atom"
      xmlns:dc="http://purl.org/dc/terms/"
      xmlns:opds="http://opds-spec.org/2010/catalog">
    <id>{feed_id}</id>
    <title>{escaped_title}{feed_title_extra}</title>
    <updated>{now}</updated>
    <author><name>{html.escape(story.author or 'Đang cập nhật')}</name></author>
    <content type="text">{escaped_desc}</content>
    <link rel="self" href="{html.escape(self_url)}" type="application/atom+xml;profile=opds-catalog;kind=acquisition"/>
    <link rel="start" href="{html.escape(base_url)}/opds" type="application/atom+xml;profile=opds-catalog;kind=navigation"/>
    <link rel="up" href="{html.escape(base_url)}/opds/book/{story.source_id}/{story.slug}" type="application/atom+xml;profile=opds-catalog;kind=acquisition"/>
    {cover_tags}
{pagination_links}
{entries_str}
</feed>
"""
        return xml.strip()
