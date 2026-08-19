"""Web testing interface for easy browser exploration, searching and EPUB downloading."""

import html
from fastapi import APIRouter, Request, Response
from fastapi.responses import HTMLResponse
from app.sources.registry import registry
from app.config import settings

router = APIRouter(tags=["Web UI"])

WEB_HTML = """<!DOCTYPE html>
<html lang="vi">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no, viewport-fit=cover">
    <title>Z-Truyen X3 — Web Catalog & OPDS Hub</title>
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&display=swap" rel="stylesheet">
    <style>
        :root {
            --bg-main: #0b1120;
            --bg-card: #1e293b;
            --bg-card-hover: #334155;
            --border: #334155;
            --text-main: #f8fafc;
            --text-muted: #94a3b8;
            --primary: #38bdf8;
            --primary-hover: #0ea5e9;
            --accent: #f59e0b;
            --success: #10b981;
            --danger: #ef4444;
            --radius: 12px;
        }

        * {
            box-sizing: border-box;
            margin: 0;
            padding: 0;
            font-family: 'Plus Jakarta Sans', -apple-system, BlinkMacSystemFont, sans-serif;
            -webkit-tap-highlight-color: transparent;
        }

        html, body {
            background-color: var(--bg-main);
            color: var(--text-main);
            min-height: 100vh;
            width: 100%;
            overflow-x: hidden;
            display: flex;
            flex-direction: column;
        }

        header {
            background-color: rgba(30, 41, 59, 0.9);
            backdrop-filter: blur(12px);
            border-bottom: 1px solid var(--border);
            position: sticky;
            top: 0;
            z-index: 50;
            padding: 0.75rem 1rem;
        }

        .header-content {
            max-width: 1200px;
            margin: 0 auto;
            display: flex;
            justify-content: space-between;
            align-items: center;
            flex-wrap: wrap;
            gap: 0.5rem;
        }

        .logo {
            display: flex;
            align-items: center;
            gap: 0.5rem;
            text-decoration: none;
            color: var(--text-main);
            font-weight: 700;
            font-size: 1.1rem;
        }

        .logo-badge {
            background: linear-gradient(135deg, #38bdf8, #818cf8);
            color: #0f172a;
            padding: 0.2rem 0.5rem;
            border-radius: 6px;
            font-size: 0.75rem;
            font-weight: 800;
        }

        .opds-pill {
            background-color: rgba(56, 189, 248, 0.1);
            border: 1px solid rgba(56, 189, 248, 0.3);
            color: var(--primary);
            padding: 0.35rem 0.75rem;
            border-radius: 9999px;
            font-size: 0.75rem;
            display: flex;
            align-items: center;
            gap: 0.35rem;
            word-break: break-all;
        }

        .container {
            max-width: 1200px;
            width: 100%;
            margin: 0 auto;
            padding: 1.25rem 1rem;
            flex: 1;
        }

        .hero {
            text-align: center;
            margin-bottom: 1.5rem;
        }

        .hero h1 {
            font-size: clamp(1.4rem, 4vw, 2.2rem);
            font-weight: 800;
            margin-bottom: 0.5rem;
            background: linear-gradient(to right, #f8fafc, #94a3b8);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            line-height: 1.25;
        }

        .hero p {
            color: var(--text-muted);
            font-size: clamp(0.85rem, 2.5vw, 1rem);
            max-width: 650px;
            margin: 0 auto;
            padding: 0 0.5rem;
        }

        .search-box {
            max-width: 700px;
            margin: 1.25rem auto 0;
            display: flex;
            flex-direction: column;
            gap: 0.5rem;
            background-color: var(--bg-card);
            padding: 0.6rem;
            border-radius: var(--radius);
            border: 1px solid var(--border);
        }

        @media (min-width: 640px) {
            .search-box {
                flex-direction: row;
            }
        }

        .search-box input {
            flex: 1;
            background: transparent;
            border: none;
            padding: 0.65rem 0.75rem;
            color: var(--text-main);
            font-size: 0.95rem;
            outline: none;
            width: 100%;
        }

        .search-box select {
            background-color: var(--bg-main);
            color: var(--text-main);
            border: 1px solid var(--border);
            padding: 0.55rem 0.75rem;
            border-radius: 8px;
            font-size: 0.85rem;
            outline: none;
            cursor: pointer;
        }

        .search-box button {
            background-color: var(--primary);
            color: #0f172a;
            border: none;
            padding: 0.65rem 1.25rem;
            border-radius: 8px;
            font-weight: 700;
            font-size: 0.9rem;
            cursor: pointer;
            transition: all 0.2s;
            white-space: nowrap;
        }

        .search-box button:hover {
            background-color: var(--primary-hover);
        }

        .quick-nav {
            display: flex;
            justify-content: flex-start;
            gap: 0.5rem;
            margin-top: 1rem;
            overflow-x: auto;
            padding-bottom: 0.5rem;
            -webkit-overflow-scrolling: touch;
            scrollbar-width: none;
        }

        .quick-nav::-webkit-scrollbar {
            display: none;
        }

        @media (min-width: 640px) {
            .quick-nav {
                justify-content: center;
                flex-wrap: wrap;
            }
        }

        .quick-nav button {
            background-color: var(--bg-card);
            border: 1px solid var(--border);
            color: var(--text-muted);
            padding: 0.4rem 0.85rem;
            border-radius: 9999px;
            font-size: 0.8rem;
            cursor: pointer;
            transition: all 0.2s;
            white-space: nowrap;
            flex-shrink: 0;
        }

        .quick-nav button:hover, .quick-nav button.active {
            color: var(--text-main);
            border-color: var(--primary);
            background-color: rgba(56, 189, 248, 0.15);
        }

        .grid {
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(140px, 1fr));
            gap: 0.85rem;
            margin-top: 1.5rem;
        }

        @media (min-width: 640px) {
            .grid {
                grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
                gap: 1.25rem;
            }
        }

        .card {
            background-color: var(--bg-card);
            border: 1px solid var(--border);
            border-radius: var(--radius);
            overflow: hidden;
            display: flex;
            flex-direction: column;
            transition: transform 0.2s, box-shadow 0.2s;
            cursor: pointer;
        }

        .card:hover {
            transform: translateY(-3px);
            box-shadow: 0 8px 20px rgba(0,0,0,0.3);
            border-color: var(--primary);
        }

        .cover-wrap {
            aspect-ratio: 2/3;
            background-color: #0b1120;
            position: relative;
            overflow: hidden;
        }

        .cover-wrap img {
            width: 100%;
            height: 100%;
            object-fit: cover;
        }

        .badge-source {
            position: absolute;
            top: 0.4rem;
            left: 0.4rem;
            background-color: rgba(15, 23, 42, 0.85);
            backdrop-filter: blur(4px);
            color: var(--primary);
            padding: 0.15rem 0.4rem;
            border-radius: 4px;
            font-size: 0.65rem;
            font-weight: 700;
            text-transform: uppercase;
        }

        .card-body {
            padding: 0.75rem;
            display: flex;
            flex-direction: column;
            flex: 1;
        }

        .card-title {
            font-size: 0.85rem;
            font-weight: 700;
            line-height: 1.35;
            margin-bottom: 0.3rem;
            display: -webkit-box;
            -webkit-line-clamp: 2;
            -webkit-box-orient: vertical;
            overflow: hidden;
        }

        @media (min-width: 640px) {
            .card-title {
                font-size: 0.95rem;
            }
        }

        .card-author {
            color: var(--text-muted);
            font-size: 0.75rem;
            margin-bottom: 0.6rem;
            white-space: nowrap;
            overflow: hidden;
            text-overflow: ellipsis;
        }

        .card-btn {
            margin-top: auto;
            background-color: rgba(56, 189, 248, 0.1);
            color: var(--primary);
            border: 1px solid rgba(56, 189, 248, 0.3);
            padding: 0.4rem 0.5rem;
            border-radius: 6px;
            font-size: 0.75rem;
            font-weight: 700;
            text-align: center;
        }

        /* Modal */
        .modal-overlay {
            position: fixed;
            inset: 0;
            background-color: rgba(0,0,0,0.8);
            backdrop-filter: blur(6px);
            display: none;
            justify-content: center;
            align-items: flex-end;
            z-index: 100;
        }

        @media (min-width: 640px) {
            .modal-overlay {
                align-items: center;
                padding: 1.5rem;
            }
        }

        .modal {
            background-color: var(--bg-card);
            border: 1px solid var(--border);
            border-radius: 16px 16px 0 0;
            max-width: 650px;
            width: 100%;
            max-height: 88vh;
            display: flex;
            flex-direction: column;
            overflow: hidden;
            animation: modalSlideUp 0.25s ease-out;
        }

        @media (min-width: 640px) {
            .modal {
                border-radius: var(--radius);
                animation: modalFade 0.2s ease-out;
            }
        }

        @keyframes modalSlideUp {
            from { transform: translateY(100%); }
            to { transform: translateY(0); }
        }

        @keyframes modalFade {
            from { opacity: 0; transform: scale(0.96); }
            to { opacity: 1; transform: scale(1); }
        }

        .modal-header {
            padding: 1rem 1.25rem;
            border-bottom: 1px solid var(--border);
            display: flex;
            justify-content: space-between;
            align-items: center;
            background-color: rgba(30, 41, 59, 0.95);
        }

        .modal-header h3 {
            font-size: 1.05rem;
            font-weight: 700;
            overflow: hidden;
            text-overflow: ellipsis;
            white-space: nowrap;
            padding-right: 0.5rem;
        }

        .modal-close {
            background: transparent;
            border: none;
            color: var(--text-muted);
            font-size: 1.6rem;
            cursor: pointer;
            line-height: 1;
            padding: 0.2rem 0.5rem;
        }

        .modal-body {
            padding: 1rem;
            overflow-y: auto;
            display: flex;
            flex-direction: column;
            gap: 0.75rem;
        }

        .volume-item {
            background-color: var(--bg-main);
            border: 1px solid var(--border);
            border-radius: 10px;
            padding: 0.85rem 1rem;
            display: flex;
            flex-direction: column;
            gap: 0.65rem;
        }

        @media (min-width: 540px) {
            .volume-item {
                flex-direction: row;
                justify-content: space-between;
                align-items: center;
            }
        }

        .volume-info {
            flex: 1;
        }

        .volume-info h4 {
            font-size: 0.9rem;
            font-weight: 700;
            margin-bottom: 0.2rem;
            line-height: 1.35;
        }

        .volume-info p {
            color: var(--text-muted);
            font-size: 0.75rem;
        }

        .dl-btn {
            background-color: var(--primary);
            color: #0f172a;
            padding: 0.55rem 1rem;
            border-radius: 8px;
            border: none;
            text-decoration: none;
            font-size: 0.82rem;
            font-weight: 700;
            display: inline-flex;
            justify-content: center;
            align-items: center;
            gap: 0.4rem;
            transition: all 0.2s;
            cursor: pointer;
            white-space: nowrap;
            width: 100%;
        }

        @media (min-width: 540px) {
            .dl-btn {
                width: auto;
                min-width: 130px;
            }
        }

        .dl-btn:hover {
            background-color: var(--primary-hover);
        }

        .dl-btn.downloading {
            background-color: var(--accent) !important;
            color: #0f172a !important;
            cursor: wait;
            opacity: 0.9;
        }

        .dl-btn.success {
            background-color: var(--success) !important;
            color: #ffffff !important;
        }

        .loading {
            text-align: center;
            padding: 2.5rem 1rem;
            color: var(--text-muted);
            font-size: 0.95rem;
        }

        footer {
            border-top: 1px solid var(--border);
            padding: 1.25rem 1rem;
            text-align: center;
            color: var(--text-muted);
            font-size: 0.75rem;
            margin-top: auto;
        }
    </style>
</head>
<body>
    <header>
        <div class="header-content">
            <a href="/" class="logo">
                <span>📖 Z-Truyen X3</span>
                <span class="logo-badge">CrossVi OPDS</span>
            </a>
            <div class="opds-pill">
                <span>📡 OPDS:</span>
                <strong id="opds-url">http://localhost:8080/opds</strong>
            </div>
        </div>
    </header>

    <div class="container">
        <div class="hero">
            <h1>Thư Viện Truyện Tiếng Việt Cho Xteink X3</h1>
            <p>Duyệt, tìm kiếm và tải EPUB gom tập (50 chương/quyển) chuẩn hóa KOSync cho máy đọc sách E-ink.</p>
            
            <div class="search-box">
                <input type="text" id="search-input" placeholder="Nhập tên truyện, tác giả (ví dụ: Vũ Động Càn Khôn, Con Đường Bá Chủ)..." />
                <select id="source-select">
                    <option value="">Tất cả nguồn</option>
                    <option value="conduongbachu">Con Đường Bá Chủ</option>
                    <option value="storyaclick">Storya.click</option>
                    <option value="akaytruyen">AkayTruyen</option>
                </select>
                <button onclick="performSearch()">Tìm Kiếm</button>
            </div>

            <div class="quick-nav">
                <button class="active" onclick="loadCategory('hot', this)">🔥 Truyện Hot</button>
                <button onclick="loadCategory('latest', this)">⚡ Mới Cập Nhật</button>
                <button onclick="loadSearch('Con Đường Bá Chủ', 'conduongbachu', this)">⚔️ Con Đường Bá Chủ</button>
                <button onclick="loadSearch('Tiên Hiệp', '', this)">✨ Tiên Hiệp</button>
            </div>
        </div>

        <div id="results-container">
            <div class="loading">Đang tải danh sách truyện...</div>
        </div>
    </div>

    <!-- Detail Modal -->
    <div id="detail-modal" class="modal-overlay">
        <div class="modal">
            <div class="modal-header">
                <h3 id="modal-title">Chi tiết bộ truyện</h3>
                <button class="modal-close" onclick="closeModal()">&times;</button>
            </div>
            <div class="modal-body" id="modal-content">
                <div class="loading">Đang nạp danh sách tập EPUB...</div>
            </div>
        </div>
    </div>

    <footer>
        <p>Z-Truyen X3 — Powered by FastAPI &amp; Dynamic Volume Bundling. Tương thích 100% OPDS Browser CrossVi 1.1.2 &amp; KOReader.</p>
    </footer>

    <script>
        // Set dynamic OPDS URL based on current host
        document.getElementById('opds-url').innerText = window.location.origin + '/opds';

        document.getElementById('search-input').addEventListener('keypress', function(e) {
            if (e.key === 'Enter') performSearch();
        });

        async function fetchStories(endpoint) {
            const container = document.getElementById('results-container');
            container.innerHTML = '<div class="loading">Đang nạp dữ liệu từ máy chủ...</div>';
            try {
                const res = await fetch(endpoint);
                const text = await res.text();
                parseAtomFeed(text);
            } catch (err) {
                container.innerHTML = '<div class="loading" style="color: #ef4444;">Lỗi kết nối máy chủ: ' + err.message + '</div>';
            }
        }

        function parseAtomFeed(xmlText) {
            const parser = new DOMParser();
            const xml = parser.parseFromString(xmlText, 'text/xml');
            const entries = xml.querySelectorAll('entry');
            const container = document.getElementById('results-container');

            if (!entries || entries.length === 0) {
                container.innerHTML = '<div class="loading">Không tìm thấy truyện nào khớp với từ khóa.</div>';
                return;
            }

            let html = '<div class="grid">';
            entries.forEach(entry => {
                const title = entry.querySelector('title')?.textContent || 'Chưa có tiêu đề';
                const id = entry.querySelector('id')?.textContent || '';
                const author = entry.querySelector('author name')?.textContent || 'Đang cập nhật';
                
                // Get cover link
                let coverLink = 'https://images.unsplash.com/photo-1543002588-bfa74002ed7e?w=300';
                const linkElements = Array.from(entry.getElementsByTagName('link'));
                const imgLinkEl = linkElements.find(l => (l.getAttribute('rel') || '').includes('image'));
                if (imgLinkEl && imgLinkEl.getAttribute('href')) {
                    coverLink = imgLinkEl.getAttribute('href');
                }

                const subLinkEl = linkElements.find(l => l.getAttribute('rel') === 'subsection');
                const subLink = subLinkEl ? subLinkEl.getAttribute('href') : '';
                
                // Extract source and slug
                let source = 'Nguồn', slug = '';
                if (id.includes('urn:ztruyen:story:')) {
                    const parts = id.replace('urn:ztruyen:story:', '').split(':');
                    source = parts[0] || 'Nguồn';
                    slug = parts[1] || '';
                } else if (subLink) {
                    const match = subLink.match(/\\/book\\/([^\\/]+)\\/([^\\/]+)/);
                    if (match) {
                        source = match[1];
                        slug = match[2];
                    }
                }

                html += `
                    <div class="card" onclick="openStoryDetail('${source}', '${slug}', '${escapeHtml(title)}')">
                        <div class="cover-wrap">
                            <span class="badge-source">${source}</span>
                            <img src="${coverLink}" alt="${escapeHtml(title)}" onerror="this.src='https://images.unsplash.com/photo-1543002588-bfa74002ed7e?w=300'"/>
                        </div>
                        <div class="card-body">
                            <div class="card-title">${escapeHtml(title)}</div>
                            <div class="card-author">${escapeHtml(author)}</div>
                            <div class="card-btn">Xem &amp; Tải EPUB &rarr;</div>
                        </div>
                    </div>
                `;
            });
            html += '</div>';
            container.innerHTML = html;
        }

        function escapeHtml(str) {
            return String(str || '').replace(/'/g, "\\\\'").replace(/"/g, '&quot;');
        }

        function performSearch() {
            const q = document.getElementById('search-input').value.trim();
            const source = document.getElementById('source-select').value;
            let url = '/opds/search?q=' + encodeURIComponent(q);
            if (source) url += '&source=' + encodeURIComponent(source);
            fetchStories(url);
        }

        function loadCategory(cat, btn) {
            document.querySelectorAll('.quick-nav button').forEach(b => b.classList.remove('active'));
            if (btn) btn.classList.add('active');
            fetchStories('/opds/' + cat);
        }

        function loadSearch(q, src, btn) {
            document.querySelectorAll('.quick-nav button').forEach(b => b.classList.remove('active'));
            if (btn) btn.classList.add('active');
            document.getElementById('search-input').value = q;
            document.getElementById('source-select').value = src;
            performSearch();
        }

        async function openStoryDetail(source, slug, title) {
            const modal = document.getElementById('detail-modal');
            const modalTitle = document.getElementById('modal-title');
            const modalContent = document.getElementById('modal-content');
            
            modalTitle.innerText = title;
            modalContent.innerHTML = '<div class="loading">Đang nạp danh sách tập EPUB...</div>';
            modal.style.display = 'flex';

            try {
                const res = await fetch('/opds/book/' + source + '/' + slug);
                if (!res.ok) throw new Error('HTTP ' + res.status);
                const text = await res.text();
                const parser = new DOMParser();
                const xml = parser.parseFromString(text, 'text/xml');
                const entries = xml.querySelectorAll('entry');

                let bodyHtml = '<div style="display: flex; flex-direction: column; gap: 0.65rem;">';
                if (!entries || entries.length === 0) {
                    bodyHtml += '<p style="color: var(--text-muted); text-align: center; padding: 2rem 0;">Không tìm thấy tập nào.</p>';
                } else {
                    entries.forEach((entry, idx) => {
                        const entryTitle = entry.querySelector('title')?.textContent || ('Tập ' + (idx + 1));
                        const summary = entry.querySelector('summary')?.textContent || 'Gom 50 chương';
                        
                        // Extract acquisition download link
                        let dlLink = '';
                        const linkTags = Array.from(entry.getElementsByTagName('link'));
                        const acqTag = linkTags.find(l => (l.getAttribute('rel') || '').includes('acquisition'));
                        if (acqTag) {
                            dlLink = acqTag.getAttribute('href');
                        } else {
                            // Fallback direct URL format
                            const filename = `ztruyen_${source}_${slug}_v${String(idx+1).padStart(2, '0')}.epub`;
                            dlLink = `/opds/download/${source}/${slug}/${filename}`;
                        }

                        const filename = dlLink.split('/').pop() || `${slug}_v${idx+1}.epub`;

                        bodyHtml += `
                            <div class="volume-item">
                                <div class="volume-info">
                                    <h4>${escapeHtml(entryTitle)}</h4>
                                    <p>${escapeHtml(summary)}</p>
                                </div>
                                <button type="button" class="dl-btn" onclick="startDownload('${dlLink}', '${filename}', this)">
                                    <span>📥 Tải EPUB</span>
                                </button>
                            </div>
                        `;
                    });
                }
                bodyHtml += '</div>';
                modalContent.innerHTML = bodyHtml;
            } catch (err) {
                modalContent.innerHTML = '<p style="color: #ef4444; text-align: center; padding: 2rem 0;">Lỗi tải thông tin tập: ' + err.message + '</p>';
            }
        }

        async function startDownload(url, filename, btn) {
            if (!url || url === '#') {
                alert('Không tìm thấy link tải EPUB cho tập này.');
                return;
            }

            const originalContent = btn.innerHTML;
            btn.innerHTML = '<span>⏳ Đang cào &amp; nén...</span>';
            btn.classList.add('downloading');
            btn.disabled = true;

            try {
                const resp = await fetch(url);
                if (!resp.ok) {
                    let errMsg = 'Mã lỗi HTTP ' + resp.status;
                    try {
                        const errData = await resp.json();
                        if (errData.detail) errMsg = errData.detail;
                    } catch (_) {}
                    throw new Error(errMsg);
                }

                const blob = await resp.blob();
                const blobUrl = window.URL.createObjectURL(blob);
                const a = document.createElement('a');
                a.style.display = 'none';
                a.href = blobUrl;
                a.download = filename;
                document.body.appendChild(a);
                a.click();
                
                setTimeout(() => {
                    window.URL.revokeObjectURL(blobUrl);
                    a.remove();
                }, 1000);

                btn.classList.remove('downloading');
                btn.classList.add('success');
                btn.innerHTML = '<span>✅ Đã tải về!</span>';

                setTimeout(() => {
                    btn.classList.remove('success');
                    btn.innerHTML = originalContent;
                    btn.disabled = false;
                }, 3000);

            } catch (err) {
                alert('⚠️ Lỗi khi tải tập EPUB:\\n' + err.message);
                btn.classList.remove('downloading');
                btn.innerHTML = '<span>❌ Thử lại</span>';
                btn.disabled = false;
            }
        }

        function closeModal() {
            document.getElementById('detail-modal').style.display = 'none';
        }

        window.onclick = function(e) {
            const modal = document.getElementById('detail-modal');
            if (e.target === modal) closeModal();
        };

        // Initial Load
        loadCategory('hot', null);
    </script>
</body>
</html>
"""


@router.get("/", response_class=HTMLResponse)
@router.get("/web", response_class=HTMLResponse)
async def web_ui(request: Request) -> HTMLResponse:
    """Serve responsive web UI for story browsing and direct EPUB downloading."""
    return HTMLResponse(content=WEB_HTML)
