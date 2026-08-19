Test debug X3

Tài liệu này cung cấp các nội dung log. nội dung debug hiện tại sẽ là mới nhất. Ai agent đọc nó và xử lý lỗi.  
nội dung log:  
~ $ cd ~/ztruyen

~/ztruyen $ ztruyen

/data/data/com.termux/files/home/ztruyen/android/[start-server.sh](http://start-server.sh): line 32: ip: command not found

  


======================================================================

    🚀 Z-TRUYEN X3 POCKET HOST SERVER ĐANG HOẠT ĐỘNG (PORT 8080)

======================================================================

  


 🌐 1. Tự động nhận diện (mDNS Zeroconf):

    [http://ztruyen.local:8080/opds](http://ztruyen.local:8080/opds)

  


 📶 2. Khi bạn phát Điểm phát sóng di động (Hotspot):

    [http://192.168.43.1:8080/opds](http://192.168.43.1:8080/opds)

  


 📚 HƯỚNG DẪN DÀNH CHO MÁY ĐỌC SÁCH XTEINK X3:

    - Mở OPDS Browser trên X3

    - Nhập URL: [http://ztruyen.local:8080/opds](http://ztruyen.local:8080/opds) (hoặc IP ở trên)

    - Duyệt truyện &amp; bấm Tải về máy!

  


 💡 Nhấn tổ hợp phím [Ctrl + C] trên bàn phím để tắt server.

======================================================================

  


2026-08-19 10:35:22 [INFO] [ztruyen:21] Registered source adapter: Storya (storyaclick)

2026-08-19 10:35:22 [INFO] [ztruyen:21] Registered source adapter: AkayTruyen (akaytruyen)

2026-08-19 10:35:22 [INFO] [ztruyen:21] Registered source adapter: Con Đường Bá Chủ (conduongbachu)

Traceback (most recent call last):

  File "&lt;frozen runpy&gt;", line 203, in *run*module_as_main

  File "&lt;frozen runpy&gt;", line 88, in *run*code

  File "/data/data/com.termux/files/home/.ztruyen-venv/lib/python3.14/site-packages/uvicorn/__main__.py", line 4, in &lt;module&gt;

    uvicorn.main()

    ~~~~~~~~~~~~^^

  File "/data/data/com.termux/files/home/.ztruyen-venv/lib/python3.14/site-packages/click/[core.py](http://core.py)", line 1569, in **call**

    return self.main(*args, **kwargs)

           ~~~~~~~~~^^^^^^^^^^^^^^^^^

  File "/data/data/com.termux/files/home/.ztruyen-venv/lib/python3.14/site-packages/click/[core.py](http://core.py)", line 1490, in main

    rv = self.invoke(ctx)

  File "/data/data/com.termux/files/home/.ztruyen-venv/lib/python3.14/site-packages/click/[core.py](http://core.py)", line 1353, in invoke

    return ctx.invoke(self.callback, **ctx.params)

           ~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

  File "/data/data/com.termux/files/home/.ztruyen-venv/lib/python3.14/site-packages/click/[core.py](http://core.py)", line 907, in invoke

    return callback(*args, **kwargs)

  File "/data/data/com.termux/files/home/.ztruyen-venv/lib/python3.14/site-packages/uvicorn/[main.py](http://main.py)", line 440, in main

    run(

    ~~~^

        app,

        ^^^^

    ...&lt;48 lines&gt;...

        reset_contextvars=reset_contextvars,

        ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

    )

    ^

  File "/data/data/com.termux/files/home/.ztruyen-venv/lib/python3.14/site-packages/uvicorn/[main.py](http://main.py)", line 609, in run

    config.load_app()

    ~~~~~~~~~~~~~~~^^

  File "/data/data/com.termux/files/home/.ztruyen-venv/lib/python3.14/site-packages/uvicorn/[config.py](http://config.py)", line 428, in load_app

    return import_from_string([self.app](http://self.app))

  File "/data/data/com.termux/files/home/.ztruyen-venv/lib/python3.14/site-packages/uvicorn/[importer.py](http://importer.py)", line 19, in import_from_string

    module = importlib.import_module(module_str)

  File "/data/data/com.termux/files/usr/lib/python3.14/importlib/__init__.py", line 88, in import_module

    return *bootstrap.*gcd_import(name[level:], package, level)

           ~~~~~~~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

  File "&lt;frozen importlib._bootstrap&gt;", line 1406, in *gcd*import

  File "&lt;frozen importlib._bootstrap&gt;", line 1371, in *find*and_load

  File "&lt;frozen importlib._bootstrap&gt;", line 1342, in *find*and_load_unlocked

  File "&lt;frozen importlib._bootstrap&gt;", line 938, in *load*unlocked

  File "&lt;frozen importlib._bootstrap_external&gt;", line 759, in exec_module

  File "&lt;frozen importlib._bootstrap&gt;", line 491, in *call*with_frames_removed

  File "/data/data/com.termux/files/home/ztruyen/backend/app/[main.py](http://main.py)", line 13, in &lt;module&gt;

    from app.api.books import router as books_router

  File "/data/data/com.termux/files/home/ztruyen/backend/app/api/[books.py](http://books.py)", line 7, in &lt;module&gt;

    from app.epub.bundler import volume_bundler

  File "/data/data/com.termux/files/home/ztruyen/backend/app/epub/[bundler.py](http://bundler.py)", line 16, in &lt;module&gt;

    from app.cache.object_storage import storage, ObjectStorage

  File "/data/data/com.termux/files/home/ztruyen/backend/app/cache/object_[storage.py](http://storage.py)", line 91, in &lt;module&gt;

    storage = ObjectStorage()

  File "/data/data/com.termux/files/home/ztruyen/backend/app/cache/object_[storage.py](http://storage.py)", line 15, in **init**

    self.ensure_directories()

    ~~~~~~~~~~~~~~~~~~~~~~~^^

  File "/data/data/com.termux/files/home/ztruyen/backend/app/cache/object_[storage.py](http://storage.py)", line 19, in ensure_directories

    self.epub_dir.mkdir(parents=True, exist_ok=True)

    ~~~~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

  File "/data/data/com.termux/files/usr/lib/python3.14/pathlib/__init__.py", line 1011, in mkdir

    os.mkdir(self, mode)

    ~~~~~~~~^^^^^^^^^^^^

PermissionError: [Errno 13] Permission denied: '/data/data/com.termux/files/home/ztruyen/backend/data/cache/epubs'

~/ztruyen $

  
