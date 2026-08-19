"""E-ink optimized XHTML templates and ultra-lightweight CSS stylesheet for EPUBs."""

EPUB_CSS = """
@charset "utf-8";

body {
    margin: 5% 4%;
    padding: 0;
    font-family: serif;
    font-size: 1.05em;
    line-height: 1.6;
    text-align: justify;
    text-justify: inter-word;
    color: #000000;
    background-color: #ffffff;
}

h1, h2, h3 {
    text-align: center;
    font-weight: bold;
    margin-top: 1.5em;
    margin-bottom: 1em;
    page-break-before: always;
    page-break-after: avoid;
    line-height: 1.3;
}

h1.story-title {
    font-size: 1.6em;
    margin-top: 2em;
    margin-bottom: 0.5em;
}

p.author {
    text-align: center;
    font-style: italic;
    margin-bottom: 2em;
}

p {
    margin: 0.4em 0;
    text-indent: 1.5em;
    orphans: 2;
    widows: 2;
}

p.no-indent {
    text-indent: 0;
}

.center {
    text-align: center;
    text-indent: 0;
}

.cover-image {
    text-align: center;
    margin: 0;
    padding: 0;
}

.cover-image img {
    max-width: 100%;
    max-height: 95vh;
    object-fit: contain;
}

hr {
    border: none;
    border-top: 1px solid #666666;
    margin: 2em auto;
    width: 60%;
}
""".strip()

XHTML_CHAPTER_TEMPLATE = """<?xml version="1.0" encoding="utf-8"?>
<!DOCTYPE html>
<html xmlns="http://www.w3.org/1999/xhtml" xml:lang="vi" lang="vi">
<head>
    <meta charset="utf-8" />
    <title>{title}</title>
    <link rel="stylesheet" type="text/css" href="style.css" />
</head>
<body>
    <h2 id="chap-title">{title}</h2>
    <div class="chapter-body">
{content}
    </div>
</body>
</html>
"""

XHTML_TITLE_PAGE_TEMPLATE = """<?xml version="1.0" encoding="utf-8"?>
<!DOCTYPE html>
<html xmlns="http://www.w3.org/1999/xhtml" xml:lang="vi" lang="vi">
<head>
    <meta charset="utf-8" />
    <title>{title}</title>
    <link rel="stylesheet" type="text/css" href="style.css" />
</head>
<body>
    <div class="center" style="margin-top: 25%;">
        <h1 class="story-title">{title}</h1>
        <p class="author">Tác giả: {author}</p>
        <p class="no-indent" style="font-weight: bold; margin-top: 1em;">{volume_title}</p>
        <hr/>
        <p class="no-indent" style="font-size: 0.9em; color: #444;">Nguồn: {source_name}</p>
        <p class="no-indent" style="font-size: 0.85em; color: #666;">Đóng gói bởi Z-Truyen X3</p>
    </div>
</body>
</html>
"""
