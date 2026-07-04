#!/usr/bin/env python3
import json
import os
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parent
DATA_ROOT = Path(os.environ.get("DATA_ROOT", str(ROOT / "server"))).resolve()
DATA_FILE = DATA_ROOT / "data.json"
UPLOAD_ROOT = Path(os.environ.get("UPLOAD_ROOT", str(ROOT / "assets" / "uploads"))).resolve()
THUMB_ROOT = UPLOAD_ROOT / "thumbs"
PORT = int(os.environ.get("PORT", "8000"))


def ensure_storage_dirs():
    DATA_ROOT.mkdir(parents=True, exist_ok=True)
    UPLOAD_ROOT.mkdir(parents=True, exist_ok=True)
    THUMB_ROOT.mkdir(parents=True, exist_ok=True)


def load_students():
    ensure_storage_dirs()
    if DATA_FILE.exists():
        try:
            return json.loads(DATA_FILE.read_text())
        except Exception:
            return []
    return []


def save_students(students):
    ensure_storage_dirs()
    DATA_FILE.write_text(json.dumps(students, indent=2))


class CollegeHandler(BaseHTTPRequestHandler):
    def _send_json(self, payload, status=200):
        body = json.dumps(payload).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        # CORS: reflect Origin if present so credentials can be used from browsers
        origin = self.headers.get('Origin')
        if origin:
            self.send_header("Access-Control-Allow-Origin", origin)
            self.send_header("Access-Control-Allow-Credentials", "true")
        else:
            self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, PUT, DELETE, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type, X-Admin-Portal")
        self.end_headers()
        self.wfile.write(body)

    def do_OPTIONS(self):
        self.send_response(204)
        origin = self.headers.get('Origin')
        if origin:
            self.send_header("Access-Control-Allow-Origin", origin)
            self.send_header("Access-Control-Allow-Credentials", "true")
        else:
            self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, PUT, DELETE, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type, X-Admin-Portal")
        self.end_headers()

    def do_GET(self):
        parsed = urlparse(self.path)
        if parsed.path == "/health":
            self._send_json({"ok": True})
            return

        if parsed.path == "/api/students":
            self._send_json(load_students())
            return

        if parsed.path == "/api/gallery":
            ensure_storage_dirs()
            files = []
            allowed_exts = {'.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp'}
            for f in sorted(UPLOAD_ROOT.iterdir()):
                # skip non-files, hidden files, and thumbnail/webp entries
                if not f.is_file():
                    continue
                if f.name.startswith('.'):
                    continue
                if f.parent.name == 'thumbs':
                    continue
                if f.suffix.lower() not in allowed_exts:
                    continue
                thumb = (THUMB_ROOT / f.name)
                webp = UPLOAD_ROOT / (f.stem + '.webp')
                files.append({
                    'name': f.name,
                    'url': '/' + str(Path('assets') / 'uploads' / f.name),
                    'thumb': ('/' + str(Path('assets') / 'uploads' / 'thumbs' / f.name)) if thumb.exists() else ('/' + str(Path('assets') / 'uploads' / f.name)),
                    'webp': ('/' + str(Path('assets') / 'uploads' / webp.name)) if webp.exists() else None
                })
            self._send_json(files)
            return

        path = parsed.path.lstrip("/") or "index.html"
        if path.startswith("assets/uploads/"):
            rel_path = path[len("assets/uploads/"):]
            target = (UPLOAD_ROOT / rel_path).resolve()
            if str(target).startswith(str(UPLOAD_ROOT)) and target.exists() and target.is_file():
                content = target.read_bytes()
                mime = "image/jpeg" if target.suffix.lower() in {".jpg", ".jpeg"} else "image/png" if target.suffix.lower() == ".png" else "image/webp" if target.suffix.lower() == ".webp" else "application/octet-stream"
                self.send_response(200)
                self.send_header("Content-Type", mime)
                self.send_header("Content-Length", str(len(content)))
                self.end_headers()
                self.wfile.write(content)
                return
        elif path.startswith("uploads/"):
            rel_path = path[len("uploads/"):]
            target = (UPLOAD_ROOT / rel_path).resolve()
            if str(target).startswith(str(UPLOAD_ROOT)) and target.exists() and target.is_file():
                content = target.read_bytes()
                mime = "image/jpeg" if target.suffix.lower() in {".jpg", ".jpeg"} else "image/png" if target.suffix.lower() == ".png" else "image/webp" if target.suffix.lower() == ".webp" else "application/octet-stream"
                self.send_response(200)
                self.send_header("Content-Type", mime)
                self.send_header("Content-Length", str(len(content)))
                self.end_headers()
                self.wfile.write(content)
                return

        target = (ROOT / path).resolve()
        if str(target).startswith(str(ROOT)) and target.exists() and target.is_file():
            content = target.read_bytes()
            mime = "text/html" if target.suffix.lower() in {".html", ".htm"} else "application/octet-stream"
            self.send_response(200)
            self.send_header("Content-Type", mime)
            self.send_header("Content-Length", str(len(content)))
            self.end_headers()
            self.wfile.write(content)
            return

        self._send_json({"error": "Not found"}, 404)

    def do_POST(self):
        parsed = urlparse(self.path)
        # Allow client to request the server to set the admin upload cookie
        if parsed.path == "/api/set_admin_cookie":
            body = json.dumps({"ok": True}).encode("utf-8")
            self.send_response(200)
            origin = self.headers.get('Origin')
            if origin:
                self.send_header("Access-Control-Allow-Origin", origin)
                self.send_header("Access-Control-Allow-Credentials", "true")
            else:
                self.send_header("Access-Control-Allow-Origin", "*")
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(body)))
            # Set cookie for admin uploads (not HttpOnly so client can still read if needed)
            self.send_header("Set-Cookie", "upload_admin=1; Path=/")
            self.end_headers()
            self.wfile.write(body)
            return
        if parsed.path == "/api/upload":
            # Handle multipart upload and save files to assets/uploads
            content_type = self.headers.get('Content-Type', '')
            if 'multipart/form-data' not in content_type:
                self._send_json({'error': 'Expected multipart/form-data'}, 400)
                return
            # Parse multipart form-data without cgi (removed in Python 3.14)
            # Simple image type detection (imghdr removed in Python 3.14)
            def detect_image_kind(data: bytes):
                if not data or len(data) < 12:
                    return None
                if data.startswith(b'\xff\xd8'):
                    return 'jpeg'
                if data.startswith(b'\x89PNG\r\n\x1a\n'):
                    return 'png'
                if data[:6] in (b'GIF87a', b'GIF89a'):
                    return 'gif'
                if data.startswith(b'BM'):
                    return 'bmp'
                if data[:4] == b'RIFF' and data[8:12] == b'WEBP':
                    return 'webp'
                return None
            from email.parser import BytesParser
            from email.policy import default
            length = int(self.headers.get('Content-Length', '0'))
            body = self.rfile.read(length) if length else b''
            fs = []
            try:
                # Build a pseudo-email bytes stream so the parser can extract parts
                content_type = self.headers.get('Content-Type', '')
                parser = BytesParser(policy=default)
                msg = parser.parsebytes(b'Content-Type: ' + content_type.encode('utf-8') + b"\r\n\r\n" + body)
                # iterate attachments
                for part in msg.iter_attachments():
                    filename = part.get_filename()
                    payload = part.get_payload(decode=True)
                    fs.append({'filename': filename, 'data': payload})
            except Exception:
                # fallback: treat body as single file when parsing fails
                fs.append({'filename': None, 'data': body})
            uploads = []
            ensure_storage_dirs()
            upload_dir = UPLOAD_ROOT
            thumb_dir = THUMB_ROOT

            # Try to import Pillow for resizing; if unavailable, we'll save original files only
            has_pillow = False
            try:
                from PIL import Image
                has_pillow = True
            except Exception:
                has_pillow = False

            MAX_BYTES = 10 * 1024 * 1024  # 10MB per file
            # Allow uploads if client indicates admin portal origin.
            # Accept when one of:
            # - upload_admin cookie present
            # - custom header X-Admin-Portal is set by the admin UI
            # - Referer ends with /admin.html
            cookie = self.headers.get('Cookie', '')
            xadmin = self.headers.get('X-Admin-Portal')
            referer = self.headers.get('Referer', '')
            ok_admin = False
            if 'upload_admin=1' in cookie:
                ok_admin = True
            if xadmin and str(xadmin) == '1':
                ok_admin = True
            if referer and referer.endswith('/admin.html'):
                ok_admin = True

            if not ok_admin:
                self._send_json({'error': 'Forbidden - admin upload only'}, 403)
                return

            for entry in fs:
                filename = entry.get('filename') or 'upload'
                data = entry.get('data') or b''
                if not data:
                    continue
                if len(data) > MAX_BYTES:
                    continue
                filename = os.path.basename(filename)
                safe_name = filename.replace(' ', '_')
                # basic image type check
                kind = detect_image_kind(data)
                if kind not in ('jpeg', 'png', 'gif', 'bmp', 'webp'):
                    continue

                # make unique name to avoid collisions
                base, ext = os.path.splitext(safe_name)
                timestamp = str(int(time.time() * 1000))
                target_name = f"{base}_{timestamp}{ext or '.'+kind}"
                target = upload_dir / target_name
                with open(target, 'wb') as out:
                    out.write(data)
                # generate thumbnail, optionally resize full image, and create WebP
                thumb_path = thumb_dir / target_name
                if has_pillow:
                    try:
                        img = Image.open(target)
                        # ensure RGB for JPEG
                        if img.mode in ('RGBA', 'LA'):
                            bg = Image.new('RGB', img.size, (255,255,255))
                            bg.paste(img, mask=img.split()[3])
                            img = bg
                        elif img.mode != 'RGB':
                            img = img.convert('RGB')

                        # resize full image if very large
                        MAX_FULL = (2000, 2000)
                        if img.width > MAX_FULL[0] or img.height > MAX_FULL[1]:
                            img.thumbnail(MAX_FULL, Image.LANCZOS)
                            img.save(target, quality=85)

                        # thumbnail
                        THUMB_SZ = (400, 300)
                        thumb = img.copy()
                        thumb.thumbnail(THUMB_SZ, Image.LANCZOS)
                        thumb.save(thumb_path, quality=80)
                        # also save WebP optimized version
                        webp_path = upload_dir / (os.path.splitext(target_name)[0] + '.webp')
                        try:
                            img.save(webp_path, 'WEBP', quality=80, method=6)
                        except Exception:
                            pass
                    except Exception:
                        # If Pillow processing fails, ensure thumb is a copy of original
                        try:
                            with open(thumb_path, 'wb') as t:
                                t.write(data)
                        except Exception:
                            pass
                else:
                    # pillow not available, copy original as thumbnail fallback
                    try:
                        with open(thumb_path, 'wb') as t:
                            t.write(data)
                    except Exception:
                        pass

                uploads.append({'name': target_name, 'url': '/' + str(Path('assets') / 'uploads' / target_name), 'thumb': '/' + str(Path('assets') / 'uploads' / 'thumbs' / target_name)})
            self._send_json({'uploaded': uploads}, 201)
            return
            return

        if parsed.path != "/api/students":
            self._send_json({"error": "Not found"}, 404)
            return

        length = int(self.headers.get("Content-Length", "0"))
        body = self.rfile.read(length).decode("utf-8") if length else "{}"
        try:
            data = json.loads(body) if body else {}
        except json.JSONDecodeError:
            self._send_json({"error": "Invalid JSON"}, 400)
            return

        if not data:
            self._send_json({"error": "No student data"}, 400)
            return

        student = dict(data)
        student.setdefault("id", str(int(time.time() * 1000)))
        students = load_students()
        students.append(student)
        save_students(students)
        self._send_json(student, 201)

    def do_PUT(self):
        parsed = urlparse(self.path)
        if not parsed.path.startswith("/api/students/"):
            self._send_json({"error": "Not found"}, 404)
            return

        student_id = parsed.path.split("/")[-1]
        length = int(self.headers.get("Content-Length", "0"))
        body = self.rfile.read(length).decode("utf-8") if length else "{}"
        try:
            data = json.loads(body) if body else {}
        except json.JSONDecodeError:
            self._send_json({"error": "Invalid JSON"}, 400)
            return

        students = load_students()
        found = False
        for index, student in enumerate(students):
            if str(student.get("id")) == str(student_id):
                students[index] = {**student, **data}
                found = True
                break

        if not found:
            self._send_json({"error": "Student not found"}, 404)
            return

        save_students(students)
        updated_student = next((item for item in students if str(item.get("id")) == str(student_id)), None)
        self._send_json(updated_student or {}, 200)

    def do_DELETE(self):
        parsed = urlparse(self.path)
        # Expect /api/upload?name=filename
        if parsed.path != '/api/upload':
            self._send_json({'error': 'Not found'}, 404)
            return

        # Admin check
        cookie = self.headers.get('Cookie', '') or ''
        xadmin = (self.headers.get('X-Admin-Portal') or '').strip()
        referer = self.headers.get('Referer', '') or ''
        ok_admin = False
        if 'upload_admin=1' in cookie:
            ok_admin = True
        if xadmin == '1':
            ok_admin = True
        if referer.endswith('/admin.html'):
            ok_admin = True

        if not ok_admin:
            self._send_json({
                'error': 'Forbidden - admin only',
                'cookie': cookie,
                'xadmin': xadmin,
                'referer': referer
            }, 403)
            return

        from urllib.parse import parse_qs
        qs = parse_qs(parsed.query)
        name = qs.get('name', [None])[0]
        if not name:
            self._send_json({'error': 'Missing name parameter'}, 400)
            return

        ensure_storage_dirs()
        target = UPLOAD_ROOT / name
        deleted = []
        try:
            if target.exists() and target.is_file():
                target.unlink()
                deleted.append(str(target))
            thumb = THUMB_ROOT / name
            if thumb.exists() and thumb.is_file():
                thumb.unlink()
                deleted.append(str(thumb))
            webp = UPLOAD_ROOT / (Path(name).stem + '.webp')
            if webp.exists() and webp.is_file():
                webp.unlink()
                deleted.append(str(webp))
            self._send_json({'deleted': deleted}, 200)
        except Exception as e:
            self._send_json({'error': str(e)}, 500)
        return


if __name__ == "__main__":
    server = ThreadingHTTPServer(("0.0.0.0", PORT), CollegeHandler)
    print(f"Server running on http://localhost:{PORT}")
    server.serve_forever()
