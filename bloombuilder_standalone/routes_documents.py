"""Document Access Routes - iPad-friendly file viewing and downloading"""
import os
from flask import Blueprint, send_file, Response, render_template_string
from pathlib import Path

documents_bp = Blueprint('documents', __name__, url_prefix='/documents')

# Whitelist of allowed documents
ALLOWED_DOCUMENTS = [
    'COMPLETE_VISION_FOR_FAMOUS_AI.md',
    'FAMOUS_AI_HANDOFF.md',
    'READY_FOR_FAMOUS_AI.md'
]

DOCS_DIR = Path(__file__).parent

@documents_bp.route('/')
def index():
    """Document download hub - iPad friendly"""
    html = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Your BloomBuilder Documentation Files</title>
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <style>
            body {
                font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Arial, sans-serif;
                max-width: 800px;
                margin: 40px auto;
                padding: 20px;
                background: linear-gradient(135deg, #1a0e2e 0%, #2d1f3f 100%);
                color: #f5f3f8;
                line-height: 1.6;
            }
            h1 {
                color: #e91e63;
                margin-bottom: 10px;
            }
            .subtitle {
                color: #9c27b0;
                margin-bottom: 30px;
            }
            .file-card {
                background: rgba(255, 255, 255, 0.05);
                border: 2px solid #e91e63;
                border-radius: 12px;
                padding: 20px;
                margin-bottom: 20px;
            }
            .file-card h3 {
                margin-top: 0;
                color: #e91e63;
                font-size: 18px;
            }
            .file-card p {
                color: #ccc;
                margin: 10px 0;
            }
            .button-group {
                display: flex;
                gap: 10px;
                margin-top: 15px;
                flex-wrap: wrap;
            }
            .btn {
                display: inline-block;
                padding: 15px 25px;
                border-radius: 8px;
                text-decoration: none;
                font-weight: bold;
                font-size: 16px;
                transition: all 0.3s;
                text-align: center;
                min-width: 120px;
            }
            .btn-view {
                background: #9c27b0;
                color: white;
            }
            .btn-view:hover {
                background: #7b1fa2;
                transform: translateY(-2px);
            }
            .btn-download {
                background: #e91e63;
                color: white;
            }
            .btn-download:hover {
                background: #c2185b;
                transform: translateY(-2px);
            }
            .btn-all {
                background: #4caf50;
                color: white;
                font-size: 18px;
                padding: 20px 30px;
                width: 100%;
                margin-top: 20px;
            }
            .btn-all:hover {
                background: #388e3c;
            }
            .note {
                background: rgba(76, 175, 80, 0.1);
                border-left: 4px solid #4caf50;
                padding: 15px;
                margin-top: 30px;
                border-radius: 4px;
            }
            @media (max-width: 600px) {
                body {
                    margin: 20px auto;
                    padding: 15px;
                }
                .btn {
                    width: 100%;
                }
            }
        </style>
    </head>
    <body>
        <h1>🌸 Your BloomBuilder Files</h1>
        <p class="subtitle">All your documentation - ready to view or download</p>
        
        <div class="file-card">
            <h3>📄 COMPLETE_VISION_FOR_FAMOUS_AI.md</h3>
            <p><strong>⭐ Main Document</strong> - Send this one to Famous AI! Contains complete vision, philosophy, and design requirements.</p>
            <div class="button-group">
                <a href="/documents/view/COMPLETE_VISION_FOR_FAMOUS_AI.md" class="btn btn-view">👁 View & Copy</a>
                <a href="/documents/download/COMPLETE_VISION_FOR_FAMOUS_AI.md" class="btn btn-download">⬇️ Download</a>
            </div>
        </div>
        
        <div class="file-card">
            <h3>📄 FAMOUS_AI_HANDOFF.md</h3>
            <p>Technical details - API documentation, endpoints, database schema for Famous AI's reference.</p>
            <div class="button-group">
                <a href="/documents/view/FAMOUS_AI_HANDOFF.md" class="btn btn-view">👁 View & Copy</a>
                <a href="/documents/download/FAMOUS_AI_HANDOFF.md" class="btn btn-download">⬇️ Download</a>
            </div>
        </div>
        
        <div class="file-card">
            <h3>📄 READY_FOR_FAMOUS_AI.md</h3>
            <p>Quick reference - Status summary and what Famous AI needs to do.</p>
            <div class="button-group">
                <a href="/documents/view/READY_FOR_FAMOUS_AI.md" class="btn btn-view">👁 View & Copy</a>
                <a href="/documents/download/READY_FOR_FAMOUS_AI.md" class="btn btn-download">⬇️ Download</a>
            </div>
        </div>
        
        <div class="note">
            <strong>💡 How to use on iPad:</strong><br>
            • <strong>View & Copy:</strong> Opens the file in your browser where you can select and copy all text<br>
            • <strong>Download:</strong> Saves the file directly to your iPad's Files app
        </div>
    </body>
    </html>
    """
    return render_template_string(html)


@documents_bp.route('/view/<filename>')
def view_document(filename):
    """View document content (iPad can copy from here)"""
    if filename not in ALLOWED_DOCUMENTS:
        return "File not allowed", 403
    
    file_path = DOCS_DIR / filename
    if not file_path.exists():
        return f"File not found: {filename}", 404
    
    content = file_path.read_text(encoding='utf-8')
    
    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>{filename}</title>
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <style>
            body {{
                font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, monospace;
                max-width: 1000px;
                margin: 0 auto;
                padding: 20px;
                background: #1a1a1a;
                color: #f5f3f8;
            }}
            .header {{
                background: linear-gradient(135deg, #e91e63, #9c27b0);
                padding: 20px;
                border-radius: 8px;
                margin-bottom: 20px;
            }}
            .header h1 {{
                margin: 0;
                font-size: 20px;
            }}
            .actions {{
                margin: 20px 0;
                display: flex;
                gap: 10px;
                flex-wrap: wrap;
            }}
            .btn {{
                padding: 12px 20px;
                border-radius: 6px;
                text-decoration: none;
                font-weight: bold;
                display: inline-block;
            }}
            .btn-copy {{
                background: #4caf50;
                color: white;
            }}
            .btn-download {{
                background: #e91e63;
                color: white;
            }}
            .btn-back {{
                background: #9c27b0;
                color: white;
            }}
            .content {{
                background: #2d2d2d;
                padding: 30px;
                border-radius: 8px;
                border: 2px solid #e91e63;
                white-space: pre-wrap;
                word-wrap: break-word;
                font-family: 'Courier New', monospace;
                font-size: 14px;
                line-height: 1.6;
                overflow-x: auto;
            }}
            @media (max-width: 600px) {{
                body {{
                    padding: 10px;
                }}
                .content {{
                    padding: 15px;
                    font-size: 12px;
                }}
            }}
        </style>
    </head>
    <body>
        <div class="header">
            <h1>📄 {filename}</h1>
        </div>
        
        <div class="actions">
            <button onclick="copyContent()" class="btn btn-copy">📋 Copy All Text</button>
            <a href="/documents/download/{filename}" class="btn btn-download">⬇️ Download File</a>
            <a href="/documents" class="btn btn-back">← Back to Files</a>
        </div>
        
        <div class="content" id="content">{content}</div>
        
        <script>
            function copyContent() {{
                const content = document.getElementById('content').innerText;
                if (navigator.clipboard) {{
                    navigator.clipboard.writeText(content).then(() => {{
                        alert('✅ Copied to clipboard!');
                    }}).catch(() => {{
                        fallbackCopy();
                    }});
                }} else {{
                    fallbackCopy();
                }}
            }}
            
            function fallbackCopy() {{
                const content = document.getElementById('content');
                const range = document.createRange();
                range.selectNode(content);
                window.getSelection().removeAllRanges();
                window.getSelection().addRange(range);
                try {{
                    document.execCommand('copy');
                    alert('✅ Text selected - use iPad gesture to copy!');
                }} catch(err) {{
                    alert('Please manually select and copy the text below');
                }}
            }}
        </script>
    </body>
    </html>
    """
    return render_template_string(html)


@documents_bp.route('/download/<filename>')
def download_document(filename):
    """Download document file"""
    if filename not in ALLOWED_DOCUMENTS:
        return "File not allowed", 403
    
    file_path = DOCS_DIR / filename
    if not file_path.exists():
        return f"File not found: {filename}", 404
    
    return send_file(
        file_path,
        as_attachment=True,
        download_name=filename,
        mimetype='text/markdown'
    )
