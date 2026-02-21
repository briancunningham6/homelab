#!/usr/bin/env python3
"""
Update Handler Service
Receives webhooks from Diun, stores pending updates, provides approval UI
"""

import os
import json
import sqlite3
import subprocess
from datetime import datetime
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs

DB_PATH = os.getenv('DB_PATH', '/app/data/updates.db')
PORT = int(os.getenv('PORT', 8080))
HOMELAB_ROOT = os.getenv('HOMELAB_ROOT', '/homelab')


def init_db():
    """Initialize SQLite database for tracking updates"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS updates (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            app_name TEXT NOT NULL,
            container_name TEXT NOT NULL,
            current_image TEXT NOT NULL,
            new_image TEXT NOT NULL,
            new_tag TEXT NOT NULL,
            digest TEXT,
            detected_at TEXT NOT NULL,
            status TEXT NOT NULL DEFAULT 'pending',
            approved_at TEXT,
            completed_at TEXT,
            result TEXT,
            UNIQUE(app_name, new_tag)
        )
    ''')
    conn.commit()
    conn.close()


def parse_image_info(image_full):
    """Parse image string to extract app name and tag"""
    # Example: ghcr.io/immich-app/immich-server:v1.131.0
    parts = image_full.split(':')
    tag = parts[-1] if len(parts) > 1 else 'latest'
    image_path = parts[0]

    # Extract app name from image path
    if '/' in image_path:
        app_name = image_path.split('/')[-1]
    else:
        app_name = image_path

    return app_name, tag


def get_current_version(container_name):
    """Get current running version of a container"""
    try:
        result = subprocess.run(
            ['docker', 'inspect', container_name, '--format', '{{.Config.Image}}'],
            capture_output=True,
            text=True,
            timeout=5
        )
        if result.returncode == 0:
            return result.stdout.strip()
        return "unknown"
    except Exception:
        return "unknown"


def store_update(webhook_data):
    """Store detected update in database"""
    entry = webhook_data.get('entry', {})
    metadata = webhook_data.get('metadata', {})

    image_full = entry.get('image', '')
    app_name, new_tag = parse_image_info(image_full)
    container_name = metadata.get('name', app_name)

    # Get current version
    current_image = get_current_version(container_name)

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    try:
        cursor.execute('''
            INSERT OR IGNORE INTO updates
            (app_name, container_name, current_image, new_image, new_tag, digest, detected_at, status)
            VALUES (?, ?, ?, ?, ?, ?, ?, 'pending')
        ''', (
            app_name,
            container_name,
            current_image,
            image_full,
            new_tag,
            entry.get('digest', ''),
            datetime.now().isoformat()
        ))
        conn.commit()
    finally:
        conn.close()


def get_pending_updates():
    """Retrieve all pending updates"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute('''
        SELECT * FROM updates
        WHERE status = 'pending'
        ORDER BY detected_at DESC
    ''')
    updates = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return updates


def approve_update(update_id):
    """Mark update as approved and trigger update script"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Get update details
    cursor.execute('SELECT * FROM updates WHERE id = ?', (update_id,))
    row = cursor.fetchone()

    if not row:
        conn.close()
        return {"success": False, "error": "Update not found"}

    app_name = row[1]  # app_name column
    new_tag = row[5]   # new_tag column

    # Mark as approved
    cursor.execute('''
        UPDATE updates
        SET status = 'approved', approved_at = ?
        WHERE id = ?
    ''', (datetime.now().isoformat(), update_id))
    conn.commit()
    conn.close()

    # Trigger update script
    try:
        # Check if app-update script exists
        script_path = '/scripts/app-update'
        if not os.path.exists(script_path):
            return {
                "success": False,
                "error": f"Update script not found at {script_path}"
            }

        # Execute update script in background
        # Note: This runs synchronously for now; could be async with proper job queue
        env = os.environ.copy()
        env['AUTO_APPROVE'] = 'true'  # Skip interactive prompts
        env['HOMELAB_DIR'] = HOMELAB_ROOT

        result = subprocess.run(
            [script_path, app_name, new_tag],
            capture_output=True,
            text=True,
            timeout=300,  # 5 minute timeout
            env=env
        )

        # Update database with result
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute('''
            UPDATE updates
            SET status = ?, completed_at = ?, result = ?
            WHERE id = ?
        ''', (
            'completed' if result.returncode == 0 else 'failed',
            datetime.now().isoformat(),
            result.stdout + result.stderr,
            update_id
        ))
        conn.commit()
        conn.close()

        return {
            "success": result.returncode == 0,
            "output": result.stdout,
            "error": result.stderr if result.returncode != 0 else None
        }

    except subprocess.TimeoutExpired:
        return {"success": False, "error": "Update script timeout (>5 minutes)"}
    except Exception as e:
        return {"success": False, "error": str(e)}


def dismiss_update(update_id):
    """Mark update as dismissed"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''
        UPDATE updates
        SET status = 'dismissed', completed_at = ?
        WHERE id = ?
    ''', (datetime.now().isoformat(), update_id))
    conn.commit()
    conn.close()
    return {"success": True}


class UpdateHandler(BaseHTTPRequestHandler):
    """HTTP request handler for update management"""

    def log_message(self, format, *args):
        """Custom logging"""
        print(f"[{datetime.now().isoformat()}] {format % args}")

    def do_GET(self):
        """Handle GET requests"""
        parsed = urlparse(self.path)
        path = parsed.path

        if path == '/health':
            self.send_response(200)
            self.send_header('Content-Type', 'text/plain')
            self.end_headers()
            self.wfile.write(b'OK')

        elif path == '/' or path == '/dashboard':
            self.serve_dashboard()

        elif path.startswith('/approve/'):
            update_id = int(path.split('/')[-1])
            result = approve_update(update_id)
            self.send_json_response(result)

        elif path.startswith('/dismiss/'):
            update_id = int(path.split('/')[-1])
            result = dismiss_update(update_id)
            self.send_json_response(result)

        else:
            self.send_error(404, 'Not Found')

    def do_POST(self):
        """Handle POST requests"""
        if self.path == '/webhook':
            content_length = int(self.headers.get('Content-Length', 0))
            body = self.rfile.read(content_length)

            try:
                webhook_data = json.loads(body)
                store_update(webhook_data)

                self.send_response(200)
                self.send_header('Content-Type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps({"status": "received"}).encode())

            except Exception as e:
                self.send_error(500, f'Error processing webhook: {str(e)}')
        else:
            self.send_error(404, 'Not Found')

    def serve_dashboard(self):
        """Serve dashboard HTML"""
        updates = get_pending_updates()

        html = self.render_dashboard(updates)

        self.send_response(200)
        self.send_header('Content-Type', 'text/html; charset=utf-8')
        self.end_headers()
        self.wfile.write(html.encode())

    def render_dashboard(self, updates):
        """Render dashboard HTML"""
        rows = []
        for update in updates:
            detected = datetime.fromisoformat(update['detected_at'])
            time_ago = self.time_ago(detected)

            rows.append(f'''
            <tr>
                <td><strong>{update['app_name']}</strong></td>
                <td><code>{update['container_name']}</code></td>
                <td><code>{self.extract_tag(update['current_image'])}</code></td>
                <td><code>{update['new_tag']}</code></td>
                <td>{time_ago}</td>
                <td>
                    <button onclick="approveUpdate({update['id']})" class="btn btn-success">
                        Approve & Update
                    </button>
                    <button onclick="dismissUpdate({update['id']})" class="btn btn-warning">
                        Dismiss
                    </button>
                </td>
            </tr>
            ''')

        rows_html = '\n'.join(rows) if rows else '<tr><td colspan="6" style="text-align: center; color: #666;">No pending updates</td></tr>'

        return f'''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Update Manager - Homelab</title>
    <style>
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            margin: 0;
            padding: 20px;
            background: #f5f5f5;
        }}
        .container {{
            max-width: 1200px;
            margin: 0 auto;
            background: white;
            padding: 30px;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }}
        h1 {{
            margin-top: 0;
            color: #333;
        }}
        table {{
            width: 100%;
            border-collapse: collapse;
            margin-top: 20px;
        }}
        th, td {{
            padding: 12px;
            text-align: left;
            border-bottom: 1px solid #ddd;
        }}
        th {{
            background: #f8f9fa;
            font-weight: 600;
            color: #555;
        }}
        code {{
            background: #f4f4f4;
            padding: 2px 6px;
            border-radius: 3px;
            font-family: 'Monaco', 'Courier New', monospace;
            font-size: 0.9em;
        }}
        .btn {{
            padding: 8px 16px;
            border: none;
            border-radius: 4px;
            cursor: pointer;
            font-size: 14px;
            margin-right: 8px;
        }}
        .btn-success {{
            background: #28a745;
            color: white;
        }}
        .btn-success:hover {{
            background: #218838;
        }}
        .btn-warning {{
            background: #ffc107;
            color: #212529;
        }}
        .btn-warning:hover {{
            background: #e0a800;
        }}
        .message {{
            padding: 12px;
            margin-bottom: 20px;
            border-radius: 4px;
            display: none;
        }}
        .message.success {{
            background: #d4edda;
            color: #155724;
            border: 1px solid #c3e6cb;
        }}
        .message.error {{
            background: #f8d7da;
            color: #721c24;
            border: 1px solid #f5c6cb;
        }}
    </style>
</head>
<body>
    <div class="container">
        <h1>🔄 Update Manager</h1>
        <p>Pending container updates detected by Diun</p>

        <div id="message" class="message"></div>

        <table>
            <thead>
                <tr>
                    <th>Application</th>
                    <th>Container</th>
                    <th>Current Version</th>
                    <th>New Version</th>
                    <th>Detected</th>
                    <th>Actions</th>
                </tr>
            </thead>
            <tbody>
                {rows_html}
            </tbody>
        </table>
    </div>

    <script>
        function showMessage(text, type) {{
            const msg = document.getElementById('message');
            msg.textContent = text;
            msg.className = 'message ' + type;
            msg.style.display = 'block';
            setTimeout(() => msg.style.display = 'none', 5000);
        }}

        async function approveUpdate(id) {{
            if (!confirm('Start update? This will back up, pull new image, and restart the container.')) {{
                return;
            }}

            try {{
                const response = await fetch('/approve/' + id);
                const result = await response.json();

                if (result.success) {{
                    showMessage('Update started successfully', 'success');
                    setTimeout(() => location.reload(), 2000);
                }} else {{
                    showMessage('Update failed: ' + (result.error || 'Unknown error'), 'error');
                }}
            }} catch (e) {{
                showMessage('Request failed: ' + e.message, 'error');
            }}
        }}

        async function dismissUpdate(id) {{
            if (!confirm('Dismiss this update notification?')) {{
                return;
            }}

            try {{
                const response = await fetch('/dismiss/' + id);
                const result = await response.json();

                if (result.success) {{
                    showMessage('Update dismissed', 'success');
                    setTimeout(() => location.reload(), 1000);
                }}
            }} catch (e) {{
                showMessage('Request failed: ' + e.message, 'error');
            }}
        }}
    </script>
</body>
</html>
        '''

    @staticmethod
    def extract_tag(image_full):
        """Extract tag from full image string"""
        if ':' in image_full:
            return image_full.split(':')[-1]
        return 'latest'

    @staticmethod
    def time_ago(dt):
        """Convert datetime to human-readable time ago"""
        now = datetime.now()
        diff = now - dt

        seconds = diff.total_seconds()
        if seconds < 60:
            return 'just now'
        elif seconds < 3600:
            mins = int(seconds / 60)
            return f'{mins} minute{"s" if mins != 1 else ""} ago'
        elif seconds < 86400:
            hours = int(seconds / 3600)
            return f'{hours} hour{"s" if hours != 1 else ""} ago'
        else:
            days = int(seconds / 86400)
            return f'{days} day{"s" if days != 1 else ""} ago'

    def send_json_response(self, data):
        """Send JSON response"""
        self.send_response(200 if data.get('success') else 500)
        self.send_header('Content-Type', 'application/json')
        self.end_headers()
        self.wfile.write(json.dumps(data).encode())


def main():
    """Main entry point"""
    print(f"Initializing database at {DB_PATH}...")
    init_db()

    server = HTTPServer(('0.0.0.0', PORT), UpdateHandler)
    print(f"Update Handler listening on port {PORT}")
    print(f"Dashboard: http://localhost:{PORT}/")
    print(f"Webhook endpoint: http://localhost:{PORT}/webhook")

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nShutting down...")
        server.shutdown()


if __name__ == '__main__':
    main()
