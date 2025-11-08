"""
Utilities for Featured Articles System
Markdown rendering and HTML sanitization
"""

import markdown
import bleach
from markdown.extensions import fenced_code, tables, nl2br

# Allowed HTML tags for article content
ALLOWED_TAGS = [
    'p', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6',
    'figure', 'figcaption', 'img', 'hr', 'blockquote',
    'pre', 'code', 'table', 'thead', 'tbody', 'tr', 'th', 'td',
    'ul', 'ol', 'li', 'a', 'strong', 'em', 'br', 'span', 'div'
]

# Allowed HTML attributes
ALLOWED_ATTRIBUTES = {
    'a': ['href', 'title', 'target', 'rel'],
    'img': ['src', 'alt', 'title', 'role', 'loading', 'width', 'height'],
    'figure': ['class'],
    'figcaption': ['class'],
    'pre': ['class'],
    'code': ['class'],
    'table': ['class'],
    'th': ['scope'],
    'td': ['colspan', 'rowspan']
}

def render_markdown_to_html(markdown_text):
    """
    Convert markdown to sanitized HTML
    
    Args:
        markdown_text: Raw markdown content
        
    Returns:
        Sanitized HTML string
    """
    # Configure markdown extensions
    md = markdown.Markdown(extensions=[
        'fenced_code',
        'tables',
        'nl2br',
        'sane_lists'
    ])
    
    # Render markdown to HTML
    html = md.convert(markdown_text)
    
    # Sanitize HTML
    clean_html = bleach.clean(
        html,
        tags=ALLOWED_TAGS,
        attributes=ALLOWED_ATTRIBUTES,
        strip=True
    )
    
    return clean_html

def generate_excerpt_from_markdown(markdown_text, max_length=220):
    """
    Generate a plain text excerpt from markdown content
    
    Args:
        markdown_text: Raw markdown content
        max_length: Maximum excerpt length (default 220 chars)
        
    Returns:
        Plain text excerpt
    """
    # Strip markdown formatting
    import re
    
    # Remove code blocks
    text = re.sub(r'```.*?```', '', markdown_text, flags=re.DOTALL)
    # Remove inline code
    text = re.sub(r'`[^`]+`', '', text)
    # Remove links but keep text
    text = re.sub(r'\[([^\]]+)\]\([^\)]+\)', r'\1', text)
    # Remove images
    text = re.sub(r'!\[([^\]]*)\]\([^\)]+\)', '', text)
    # Remove headers
    text = re.sub(r'^#{1,6}\s+', '', text, flags=re.MULTILINE)
    # Remove emphasis
    text = re.sub(r'[*_]{1,2}([^*_]+)[*_]{1,2}', r'\1', text)
    # Remove blockquotes
    text = re.sub(r'^>\s+', '', text, flags=re.MULTILINE)
    # Collapse whitespace
    text = re.sub(r'\s+', ' ', text).strip()
    
    # Truncate to max_length
    if len(text) > max_length:
        text = text[:max_length].rsplit(' ', 1)[0] + '...'
    
    return text

def validate_html_accessibility(html_content):
    """
    Check HTML for basic accessibility issues
    
    Returns:
        List of accessibility warnings
    """
    from bs4 import BeautifulSoup
    
    warnings = []
    soup = BeautifulSoup(html_content, 'html.parser')
    
    # Check images for alt text
    images = soup.find_all('img')
    for img in images:
        if not img.get('alt'):
            src = img.get('src', 'unknown')
            warnings.append(f"Image missing alt text: {src[:50]}")
    
    # Check heading order
    headings = soup.find_all(['h1', 'h2', 'h3', 'h4', 'h5', 'h6'])
    if headings:
        levels = [int(h.name[1]) for h in headings]
        for i in range(1, len(levels)):
            if levels[i] > levels[i-1] + 1:
                warnings.append(f"Heading order skipped from h{levels[i-1]} to h{levels[i]}")
    
    return warnings
