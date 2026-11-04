# -*- coding: utf-8 -*-
"""
iOS 文件接收服务器
- 接收 iOS（快捷指令 / App）通过 HTTP POST 上传的文件
- 支持 multipart/form-data 与原始 body（raw body）两种方式
- 提供简单的网页上传与文件列表页面
"""
import mimetypes
import os
import re
import socket
import datetime

from flask import Flask, request, jsonify, render_template, send_from_directory, abort

# 补充浏览器预览需要的 MIME 类型
mimetypes.add_type("image/heic", ".heic")
mimetypes.add_type("image/heif", ".heif")
mimetypes.add_type("image/avif", ".avif")
mimetypes.add_type("video/quicktime", ".mov")
mimetypes.add_type("video/mp4", ".m4v")

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
UPLOAD_DIR = os.path.join(BASE_DIR, "uploads")
os.makedirs(UPLOAD_DIR, exist_ok=True)

MAX_CONTENT_LENGTH = 2 * 1024 * 1024 * 1024  # 最大 2GB
PORT = 8900

app = Flask(__name__)
app.config["MAX_CONTENT_LENGTH"] = MAX_CONTENT_LENGTH
app.config["PORT"] = PORT


def safe_filename(name: str) -> str:
    """清理文件名，防止路径穿越和非法字符"""
    name = os.path.basename(name or "")
    name = re.sub(r'[<>:"/\\|?*\x00-\x1f]', "_", name).strip()
    return name or "unnamed"


def unique_path(filename: str) -> str:
    """同名文件自动加时间戳后缀，避免覆盖"""
    path = os.path.join(UPLOAD_DIR, filename)
    if not os.path.exists(path):
        return path
    stem, ext = os.path.splitext(filename)
    ts = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    return os.path.join(UPLOAD_DIR, f"{stem}_{ts}{ext}")


IMAGE_EXTS = {".jpg", ".jpeg", ".png", ".gif", ".webp", ".bmp", ".svg", ".heic", ".heif", ".avif"}
VIDEO_EXTS = {".mp4", ".m4v", ".mov", ".webm", ".avi", ".mkv", ".ogv"}


def media_kind(filename: str) -> str:
    """根据扩展名判断文件类型：image / video / other"""
    ext = os.path.splitext(filename)[1].lower()
    if ext in IMAGE_EXTS:
        return "image"
    if ext in VIDEO_EXTS:
        return "video"
    return "other"


def get_local_ips() -> list:
    """获取本机局域网 IP，方便在 iOS 上填写地址"""
    ips = set()
    try:
        hostname_ips = socket.gethostbyname_ex(socket.gethostname())[2]
        ips.update(hostname_ips)
    except OSError:
        pass
    # 通过 UDP 探测默认出口 IP
    for target in ("8.8.8.8", "1.1.1.1"):
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect((target, 80))
            ips.add(s.getsockname()[0])
            s.close()
        except OSError:
            pass
    return sorted(ip for ip in ips if not ip.startswith("127."))


@app.route("/", methods=["GET"])
def index():
    return render_template(
        "index.html",
        files=list_uploads(),
        ips=get_local_ips(),
        port=app.config["PORT"],
        max_mb=MAX_CONTENT_LENGTH // (1024 * 1024),
    )


def list_uploads() -> list:
    items = []
    for name in os.listdir(UPLOAD_DIR):
        p = os.path.join(UPLOAD_DIR, name)
        if os.path.isfile(p):
            st = os.stat(p)
            items.append({
                "name": name,
                "size": st.st_size,
                "kind": media_kind(name),
                "time": datetime.datetime.fromtimestamp(st.st_mtime).strftime("%Y-%m-%d %H:%M:%S"),
            })
    items.sort(key=lambda x: x["time"], reverse=True)
    return items


@app.route("/upload", methods=["POST", "PUT"])
def upload():
    saved = []

    # 方式一：multipart/form-data 表单字段（iOS 快捷指令 "获取文件" + POST 常用）
    # 注意：只有 multipart 才访问 request.files，否则会消耗输入流导致原始 body 读不到
    if request.mimetype == "multipart/form-data":
        for key, f in request.files.items():
            if f and f.filename:
                path = unique_path(safe_filename(f.filename))
                f.save(path)
                saved.append(path)

    # 方式二：原始 body（POST/PUT 直接传二进制，Header 里带 X-Filename 指定文件名）
    if not saved:
        body = request.get_data()
        if body:
            name = request.headers.get("X-Filename") or ""
            m = re.search(r'filename\*?="?([^";]+)"?', name)
            filename = safe_filename(m.group(1) if m else (name or "upload.bin"))
            path = unique_path(filename)
            with open(path, "wb") as fp:
                fp.write(body)
            saved.append(path)

    if not saved:
        return jsonify({"ok": False, "error": "没有收到文件"}), 400

    names = [os.path.basename(p) for p in saved]
    print(f"[{datetime.datetime.now():%H:%M:%S}] 收到文件: {names} 来自 {request.remote_addr}")
    return jsonify({"ok": True, "saved": names}), 201


@app.route("/files", methods=["GET"])
def files_api():
    return jsonify({"files": list_uploads()})


@app.route("/files/<path:filename>", methods=["GET"])
def download(filename):
    if not os.path.isfile(os.path.join(UPLOAD_DIR, filename)):
        abort(404)
    return send_from_directory(UPLOAD_DIR, filename, as_attachment=True)


@app.route("/preview/<path:filename>", methods=["GET"])
def preview(filename):
    """内联方式发送文件（浏览器中直接显示图片 / 播放视频）"""
    if not os.path.isfile(os.path.join(UPLOAD_DIR, filename)):
        abort(404)
    return send_from_directory(UPLOAD_DIR, filename)


@app.route("/files/<path:filename>", methods=["DELETE"])
def delete(filename):
    path = os.path.join(UPLOAD_DIR, filename)
    if not os.path.isfile(path):
        abort(404)
    os.remove(path)
    return jsonify({"ok": True})


if __name__ == "__main__":
    print("=" * 50)
    print("iOS 文件接收服务器已启动")
    for ip in get_local_ips():
        print(f"  iOS 上传地址: http://{ip}:{PORT}/upload")
    print(f"  文件保存目录: {UPLOAD_DIR}")
    print("=" * 50)
    app.run(host="0.0.0.0", port=PORT, threaded=True)
