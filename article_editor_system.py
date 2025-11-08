from flask import render_template_string, request, jsonify, flash, redirect, url_for, session
from app import app, db
from werkzeug.utils import secure_filename
from datetime import datetime
import os
import json

# Simple article storage in database
@app.route('/admin/articles')
def admin_articles_list():
    """Admin interface - list all articles"""
    if not session.get('admin_authenticated'):
        flash('Please log in to access admin area', 'error')
        return redirect(url_for('admin_login'))
    
    # Get all articles from static/articles
    articles_dir = 'static/articles'
    articles = []
    
    if os.path.exists(articles_dir):
        for filename in os.listdir(articles_dir):
            if filename.endswith('.txt'):
                filepath = os.path.join(articles_dir, filename)
                stat = os.stat(filepath)
                articles.append({
                    'filename': filename,
                    'title': filename.replace('.txt', '').replace('_', ' ').title(),
                    'modified': datetime.fromtimestamp(stat.st_mtime).strftime('%Y-%m-%d %H:%M'),
                    'size': f"{stat.st_size / 1024:.1f} KB"
                })
    
    html = '''
    <!DOCTYPE html>
    <html>
    <head>
        <title>Article Editor - Admin</title>
        <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.2/dist/css/bootstrap.min.css" rel="stylesheet">
        <style>
            body { background: #f8f9fa; padding: 40px 20px; }
            .container { max-width: 1200px; }
            .article-row:hover { background: #f0f0f0; }
        </style>
    </head>
    <body>
        <div class="container">
            <div class="d-flex justify-content-between align-items-center mb-4">
                <h1>📚 Article Editor</h1>
                <div>
                    <a href="/admin/articles/new" class="btn btn-primary">+ New Article</a>
                    <a href="/admin" class="btn btn-secondary">Admin Home</a>
                </div>
            </div>
            
            {% if articles %}
            <table class="table table-hover bg-white">
                <thead>
                    <tr>
                        <th>Title</th>
                        <th>Filename</th>
                        <th>Last Modified</th>
                        <th>Size</th>
                        <th>Actions</th>
                    </tr>
                </thead>
                <tbody>
                    {% for article in articles %}
                    <tr class="article-row">
                        <td><strong>{{ article.title }}</strong></td>
                        <td><code>{{ article.filename }}</code></td>
                        <td>{{ article.modified }}</td>
                        <td>{{ article.size }}</td>
                        <td>
                            <a href="/admin/articles/edit/{{ article.filename }}" class="btn btn-sm btn-primary">Edit</a>
                            <a href="/article/{{ article.filename.replace('.txt', '') }}" class="btn btn-sm btn-success" target="_blank">View</a>
                        </td>
                    </tr>
                    {% endfor %}
                </tbody>
            </table>
            {% else %}
            <div class="alert alert-info">No articles found. Create your first article!</div>
            {% endif %}
        </div>
    </body>
    </html>
    '''
    return render_template_string(html, articles=articles)

@app.route('/admin/articles/new')
def admin_new_article():
    """Create new article"""
    if not session.get('admin_authenticated'):
        flash('Please log in to access admin area', 'error')
        return redirect(url_for('admin_login'))
    
    html = '''
    <!DOCTYPE html>
    <html>
    <head>
        <title>New Article - Admin</title>
        <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.2/dist/css/bootstrap.min.css" rel="stylesheet">
        <style>
            body { background: #f8f9fa; padding: 40px 20px; }
            .container { max-width: 1200px; }
            .editor-container { background: white; padding: 30px; border-radius: 8px; }
            #editor { min-height: 500px; font-family: Georgia, serif; font-size: 16px; line-height: 1.8; }
            .image-gallery { display: grid; grid-template-columns: repeat(auto-fill, minmax(150px, 1fr)); gap: 10px; margin: 20px 0; }
            .image-thumb { width: 100%; height: 150px; object-fit: cover; border-radius: 4px; cursor: pointer; border: 2px solid transparent; }
            .image-thumb:hover { border-color: #0d6efd; }
            .toolbar { margin-bottom: 20px; padding: 15px; background: #f8f9fa; border-radius: 4px; }
        </style>
    </head>
    <body>
        <div class="container">
            <div class="d-flex justify-content-between align-items-center mb-4">
                <h1>📝 New Article</h1>
                <a href="/admin/articles" class="btn btn-secondary">← Back to Articles</a>
            </div>
            
            <div class="editor-container">
                <form id="articleForm" enctype="multipart/form-data">
                    <div class="mb-3">
                        <label class="form-label">Article Title</label>
                        <input type="text" name="title" class="form-control" required placeholder="Enter article title">
                    </div>
                    
                    <div class="mb-3">
                        <label class="form-label">Category</label>
                        <select name="category" class="form-control">
                            <option>Mythology & Culture</option>
                            <option>Botanical Science</option>
                            <option>Literature & Culture</option>
                            <option>History & Innovation</option>
                            <option>Practical Guides</option>
                            <option>Seasonal Stories</option>
                            <option>Science Fiction</option>
                        </select>
                    </div>
                    
                    <div class="mb-3">
                        <label class="form-label">Description (for article list)</label>
                        <input type="text" name="description" class="form-control" placeholder="Brief description">
                    </div>
                    
                    <div class="toolbar">
                        <button type="button" class="btn btn-sm btn-outline-secondary" onclick="insertImage()">📷 Insert Image</button>
                        <button type="button" class="btn btn-sm btn-outline-secondary" onclick="formatBold()">B</button>
                        <button type="button" class="btn btn-sm btn-outline-secondary" onclick="formatItalic()">I</button>
                        <button type="button" class="btn btn-sm btn-outline-secondary" onclick="insertHeading()">H</button>
                        <input type="file" id="imageUpload" accept="image/*" style="display:none" onchange="uploadImage()">
                    </div>
                    
                    <div class="mb-3">
                        <label class="form-label">Article Content</label>
                        <div id="editor" contenteditable="true" class="form-control">
                            Start writing your article here...
                        </div>
                    </div>
                    
                    <div id="uploadedImages" class="image-gallery"></div>
                    
                    <button type="submit" class="btn btn-primary btn-lg">Save Article</button>
                </form>
            </div>
        </div>
        
        <script>
        let uploadedImages = [];
        
        function insertImage() {
            document.getElementById('imageUpload').click();
        }
        
        async function uploadImage() {
            const file = document.getElementById('imageUpload').files[0];
            if (!file) return;
            
            const formData = new FormData();
            formData.append('image', file);
            
            const response = await fetch('/api/article-image-upload', {
                method: 'POST',
                body: formData
            });
            
            const data = await response.json();
            if (data.success) {
                uploadedImages.push(data.url);
                showUploadedImages();
                
                // Insert image into editor
                const img = `<img src="${data.url}" style="max-width: 100%; height: auto; margin: 20px 0; border-radius: 8px;">`;
                document.execCommand('insertHTML', false, img);
            }
        }
        
        function showUploadedImages() {
            const gallery = document.getElementById('uploadedImages');
            gallery.innerHTML = uploadedImages.map(url => 
                `<img src="${url}" class="image-thumb" onclick="insertImageIntoEditor('${url}')">`
            ).join('');
        }
        
        function insertImageIntoEditor(url) {
            const img = `<img src="${url}" style="max-width: 100%; height: auto; margin: 20px 0; border-radius: 8px;">`;
            document.execCommand('insertHTML', false, img);
        }
        
        function formatBold() {
            document.execCommand('bold');
        }
        
        function formatItalic() {
            document.execCommand('italic');
        }
        
        function insertHeading() {
            document.execCommand('formatBlock', false, 'h2');
        }
        
        document.getElementById('articleForm').onsubmit = async (e) => {
            e.preventDefault();
            
            const formData = new FormData(e.target);
            formData.append('content', document.getElementById('editor').innerHTML);
            
            const response = await fetch('/api/save-article', {
                method: 'POST',
                body: formData
            });
            
            const data = await response.json();
            if (data.success) {
                alert('Article saved successfully!');
                window.location.href = '/admin/articles';
            } else {
                alert('Error: ' + data.error);
            }
        };
        </script>
    </body>
    </html>
    '''
    return render_template_string(html)

@app.route('/admin/articles/edit/<filename>')
def admin_edit_article(filename):
    """Edit existing article"""
    if not session.get('admin_authenticated'):
        flash('Please log in to access admin area', 'error')
        return redirect(url_for('admin_login'))
    
    filepath = os.path.join('static/articles', filename)
    if not os.path.exists(filepath):
        flash('Article not found', 'error')
        return redirect(url_for('admin_articles_list'))
    
    with open(filepath, 'r') as f:
        content = f.read()
    
    # Extract metadata if exists
    title = filename.replace('.txt', '').replace('_', ' ').title()
    
    html = '''
    <!DOCTYPE html>
    <html>
    <head>
        <title>Edit Article - Admin</title>
        <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.2/dist/css/bootstrap.min.css" rel="stylesheet">
        <style>
            body { background: #f8f9fa; padding: 40px 20px; }
            .container { max-width: 1200px; }
            .editor-container { background: white; padding: 30px; border-radius: 8px; }
            #editor { min-height: 500px; font-family: Georgia, serif; font-size: 16px; line-height: 1.8; border: 1px solid #ddd; padding: 20px; border-radius: 4px; }
            .toolbar { margin-bottom: 20px; padding: 15px; background: #f8f9fa; border-radius: 4px; }
            .image-gallery { display: grid; grid-template-columns: repeat(auto-fill, minmax(150px, 1fr)); gap: 10px; margin: 20px 0; }
            .image-thumb { width: 100%; height: 150px; object-fit: cover; border-radius: 4px; cursor: pointer; border: 2px solid transparent; }
            .image-thumb:hover { border-color: #0d6efd; }
        </style>
    </head>
    <body>
        <div class="container">
            <div class="d-flex justify-content-between align-items-center mb-4">
                <h1>✏️ Edit Article</h1>
                <a href="/admin/articles" class="btn btn-secondary">← Back to Articles</a>
            </div>
            
            <div class="editor-container">
                <form id="articleForm" enctype="multipart/form-data">
                    <input type="hidden" name="filename" value="{{ filename }}">
                    
                    <div class="mb-3">
                        <label class="form-label">Article Title</label>
                        <input type="text" name="title" class="form-control" value="{{ title }}" required>
                    </div>
                    
                    <div class="toolbar">
                        <button type="button" class="btn btn-sm btn-outline-secondary" onclick="insertImage()">📷 Insert Image</button>
                        <button type="button" class="btn btn-sm btn-outline-secondary" onclick="formatBold()"><strong>B</strong></button>
                        <button type="button" class="btn btn-sm btn-outline-secondary" onclick="formatItalic()"><em>I</em></button>
                        <button type="button" class="btn btn-sm btn-outline-secondary" onclick="insertHeading()">H2</button>
                        <button type="button" class="btn btn-sm btn-outline-secondary" onclick="insertParagraph()">¶</button>
                        <input type="file" id="imageUpload" accept="image/*" style="display:none" onchange="uploadImage()">
                    </div>
                    
                    <div class="mb-3">
                        <label class="form-label">Article Content</label>
                        <div id="editor" contenteditable="true">{{ content }}</div>
                    </div>
                    
                    <div id="uploadedImages" class="image-gallery"></div>
                    
                    <div class="d-flex gap-2">
                        <button type="submit" class="btn btn-primary btn-lg">Save Changes</button>
                        <a href="/article/{{ filename.replace('.txt', '') }}" class="btn btn-success btn-lg" target="_blank">Preview</a>
                    </div>
                </form>
            </div>
        </div>
        
        <script>
        let uploadedImages = [];
        
        function insertImage() {
            document.getElementById('imageUpload').click();
        }
        
        async function uploadImage() {
            const file = document.getElementById('imageUpload').files[0];
            if (!file) return;
            
            const formData = new FormData();
            formData.append('image', file);
            
            const response = await fetch('/api/article-image-upload', {
                method: 'POST',
                body: formData
            });
            
            const data = await response.json();
            if (data.success) {
                uploadedImages.push(data.url);
                showUploadedImages();
                
                // Insert image into editor with nice formatting
                const img = `<figure style="margin: 30px 0; text-align: center;">
                    <img src="${data.url}" style="max-width: 100%; height: auto; border-radius: 8px; box-shadow: 0 4px 12px rgba(0,0,0,0.1);">
                    <figcaption style="margin-top: 10px; color: #666; font-style: italic;">Click to add caption</figcaption>
                </figure>`;
                document.execCommand('insertHTML', false, img);
            }
        }
        
        function showUploadedImages() {
            const gallery = document.getElementById('uploadedImages');
            if (uploadedImages.length > 0) {
                gallery.innerHTML = '<h5>Recent Uploads (click to insert):</h5>' + 
                    uploadedImages.map(url => 
                        `<img src="${url}" class="image-thumb" onclick="insertImageIntoEditor('${url}')">`
                    ).join('');
            }
        }
        
        function insertImageIntoEditor(url) {
            const img = `<figure style="margin: 30px 0; text-align: center;">
                <img src="${url}" style="max-width: 100%; height: auto; border-radius: 8px; box-shadow: 0 4px 12px rgba(0,0,0,0.1);">
                <figcaption style="margin-top: 10px; color: #666; font-style: italic;">Click to add caption</figcaption>
            </figure>`;
            document.execCommand('insertHTML', false, img);
        }
        
        function formatBold() {
            document.execCommand('bold');
        }
        
        function formatItalic() {
            document.execCommand('italic');
        }
        
        function insertHeading() {
            document.execCommand('formatBlock', false, 'h2');
        }
        
        function insertParagraph() {
            document.execCommand('insertParagraph');
        }
        
        document.getElementById('articleForm').onsubmit = async (e) => {
            e.preventDefault();
            
            const formData = new FormData(e.target);
            formData.append('content', document.getElementById('editor').innerHTML);
            
            const response = await fetch('/api/update-article', {
                method: 'POST',
                body: formData
            });
            
            const data = await response.json();
            if (data.success) {
                alert('Article updated successfully!');
            } else {
                alert('Error: ' + data.error);
            }
        };
        </script>
    </body>
    </html>
    '''
    return render_template_string(html, filename=filename, title=title, content=content)

@app.route('/api/article-image-upload', methods=['POST'])
def upload_article_image():
    """Upload image for article"""
    if not session.get('admin_authenticated'):
        return jsonify({'success': False, 'error': 'Unauthorized'}), 403
    
    if 'image' not in request.files:
        return jsonify({'success': False, 'error': 'No file provided'}), 400
    
    file = request.files['image']
    if not file.filename or file.filename == '':
        return jsonify({'success': False, 'error': 'No file selected'}), 400
    
    # Secure filename
    filename = secure_filename(file.filename)
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    filename = f"article_{timestamp}_{filename}"
    
    # Save to static/uploads/articles
    upload_dir = os.path.join('static', 'uploads', 'articles')
    os.makedirs(upload_dir, exist_ok=True)
    filepath = os.path.join(upload_dir, filename)
    file.save(filepath)
    
    # Return URL
    url = f'/{filepath}'
    return jsonify({'success': True, 'url': url, 'filename': filename})

@app.route('/api/save-article', methods=['POST'])
def save_new_article():
    """Save new article"""
    if not session.get('admin_authenticated'):
        return jsonify({'success': False, 'error': 'Unauthorized'}), 403
    
    title = request.form.get('title')
    content = request.form.get('content')
    category = request.form.get('category', 'General')
    description = request.form.get('description', '')
    
    if not title or not content:
        return jsonify({'success': False, 'error': 'Title and content are required'}), 400
    
    # Create filename from title
    filename = title.lower().replace(' ', '_').replace('-', '_')
    filename = ''.join(c for c in filename if c.isalnum() or c == '_')
    filename = f"{filename}.txt"
    
    # Save to static/articles
    filepath = os.path.join('static/articles', filename)
    os.makedirs('static/articles', exist_ok=True)
    
    with open(filepath, 'w') as f:
        f.write(content)
    
    # Update articles metadata (if we need it)
    # For now, just save the content
    
    return jsonify({'success': True, 'filename': filename})

@app.route('/api/update-article', methods=['POST'])
def update_existing_article():
    """Update existing article"""
    if not session.get('admin_authenticated'):
        return jsonify({'success': False, 'error': 'Unauthorized'}), 403
    
    filename = request.form.get('filename')
    content = request.form.get('content')
    
    if not filename or not content:
        return jsonify({'success': False, 'error': 'Filename and content are required'}), 400
    
    filepath = os.path.join('static/articles', filename)
    
    with open(filepath, 'w') as f:
        f.write(content)
    
    return jsonify({'success': True, 'filename': filename})
