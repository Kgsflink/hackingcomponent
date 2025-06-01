import re
import requests
from bs4 import BeautifulSoup
import os
from datetime import datetime
import shutil
import argparse
from urllib.parse import urlparse, urljoin

class ProfessionalBlogScraper:
    def __init__(self):
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        self.author_replacements = [
            (r"Author: Théo ARCHIMBAUD – Pentester @Vaadata", "kgsflink"),
            (r"Théo ARCHIMBAUD – Pentester @Vaadata", "kgsflink"),
            (r"Author: Renaud CAYOL – Pentester @Vaadata", "kgsflink"),
            (r"Renaud CAYOL – Pentester @Vaadata", "kgsflink"),
            (r"<p><strong>Author: .*?@Vaadata</strong></p>", "<p><strong>Author: kgsflink</strong></p>")
        ]

    def sanitize_filename(self, filename):
        """Create safe filenames for storage"""
        filename = re.sub(r'[\\/*?:"<>|]', "", filename)
        return re.sub(r'\s+', '_', filename).lower()[:100]

    def create_article_directory(self, base_dir, title):
        """Create organized folder structure for each article"""
        article_dir = os.path.join(base_dir, self.sanitize_filename(title))
        os.makedirs(article_dir, exist_ok=True)
        os.makedirs(os.path.join(article_dir, "images"), exist_ok=True)
        return article_dir

    def process_images(self, soup, article_dir, base_url, keep_original_urls=False):
        """Handle images - either download or keep original URLs"""
        image_mapping = {}
        
        for img in soup.find_all('img'):
            # Get image source (prioritize lazy loading sources)
            src = img.get('data-lazy-src') or img.get('data-src') or img.get('src')
            if not src or src.startswith('data:'):
                continue
                
            # Handle relative URLs
            if not src.startswith(('http://', 'https://')):
                src = urljoin(base_url, src)
                
            if keep_original_urls:
                # Keep original URL and just clean attributes
                img['src'] = src
                for attr in ['data-src', 'data-lazy-src', 'srcset', 'data-srcset']:
                    if attr in img.attrs:
                        del img[attr]
                image_mapping[src] = src
            else:
                # Download image and update references
                try:
                    img_name = f"{len(image_mapping)+1}_{self.get_image_name(img, src)}"
                    img_path = os.path.join(article_dir, "images", img_name)
                    
                    response = requests.get(src, headers={**self.headers, 'Referer': base_url}, stream=True)
                    response.raise_for_status()
                    
                    with open(img_path, 'wb') as f:
                        response.raw.decode_content = True
                        shutil.copyfileobj(response.raw, f)
                    
                    img['src'] = f"images/{img_name}"
                    for attr in ['data-src', 'data-lazy-src', 'srcset', 'data-srcset']:
                        if attr in img.attrs:
                            del img[attr]
                    
                    image_mapping[src] = f"images/{img_name}"
                    
                except Exception as e:
                    print(f"Failed to download image {src}: {e}")
                    img['src'] = src  # Fallback to original URL
                    image_mapping[src] = src
                
        return image_mapping

    def get_image_name(self, img_tag, img_url):
        """Generate meaningful image filename"""
        # Try alt text first
        if img_tag.get('alt'):
            return f"{self.sanitize_filename(img_tag['alt'])}.{self.get_extension(img_url)}"
            
        # Try nearby heading
        for sibling in img_tag.find_previous_siblings():
            if sibling.name in ['h1', 'h2', 'h3', 'h4']:
                return f"{self.sanitize_filename(sibling.get_text())}.{self.get_extension(img_url)}"
                
        # Fallback to URL-based name
        return os.path.basename(img_url).split('?')[0]

    def get_extension(self, img_url):
        """Get appropriate file extension"""
        if img_url.lower().endswith(('.png', '.jpg', '.jpeg', '.gif', '.webp')):
            return img_url.split('.')[-1].lower()
        return 'jpg'

    def clean_content(self, soup):
        """Remove unwanted elements and clean up content"""
        # Remove unnecessary elements
        for element in soup.select('.post-meta, .tag-share, .related-posts, .post-foot, .comments-area'):
            element.decompose()
            
        # Clean up tables
        for table in soup.find_all('table'):
            table['class'] = table.get('class', []) + ['clean-table']
            
        return str(soup)

    def replace_author_info(self, content):
        """Replace all author variations with kgsflink"""
        for pattern, replacement in self.author_replacements:
            content = re.sub(pattern, replacement, content, flags=re.IGNORECASE)
        return content

    def generate_html_template(self, title, date, content):
        """Generate professional blog template"""
        return f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title}</title>
    <link href="https://fonts.googleapis.com/css2?family=Playfair+Display:wght@400;700&family=Source+Sans+Pro:wght@300;400;600&display=swap" rel="stylesheet">
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css">
    <style>
        :root {{
            --primary: #2a4365;
            --primary-light: #4299e1;
            --secondary: #c05621;
            --text: #2d3748;
            --text-light: #4a5568;
            --background: #f7fafc;
            --card-bg: #ffffff;
            --border: #e2e8f0;
            --shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06);
            --radius: 8px;
            --transition: all 0.3s ease;
        }}

        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}

        body {{
            font-family: 'Source Sans Pro', sans-serif;
            line-height: 1.8;
            color: var(--text);
            background-color: var(--background);
            padding: 0;
            margin: 0;
        }}

        .container {{
            max-width: 1200px;
            margin: 0 auto;
            padding: 0 20px;
        }}

        header {{
            background-color: var(--primary);
            color: white;
            padding: 80px 0 40px;
            margin-bottom: 60px;
            position: relative;
            overflow: hidden;
        }}

        header::before {{
            content: '';
            position: absolute;
            top: 0;
            left: 0;
            right: 0;
            height: 5px;
            background: linear-gradient(90deg, var(--primary-light), var(--secondary));
        }}

        .header-content {{
            max-width: 800px;
            margin: 0 auto;
            text-align: center;
            position: relative;
            z-index: 1;
        }}

        h1 {{
            font-family: 'Playfair Display', serif;
            font-size: 2.8rem;
            margin-bottom: 20px;
            line-height: 1.3;
            color: white;
        }}

        .meta {{
            display: flex;
            justify-content: center;
            align-items: center;
            gap: 20px;
            margin-bottom: 30px;
            color: rgba(255, 255, 255, 0.9);
            font-size: 0.95rem;
        }}

        .meta i {{
            margin-right: 5px;
            color: var(--primary-light);
        }}

        .article-container {{
            display: grid;
            grid-template-columns: 1fr min(800px, 100%) 1fr;
            margin-bottom: 80px;
        }}

        .article-container > * {{
            grid-column: 2;
        }}

        .content {{
            background-color: var(--card-bg);
            padding: 50px;
            border-radius: var(--radius);
            box-shadow: var(--shadow);
            font-size: 1.1rem;
            color: var(--text);
        }}

        .content p {{
            margin-bottom: 1.5em;
        }}

        .content img.blog-image {{
            max-width: 100%;
            height: auto;
            margin: 40px auto;
            display: block;
            border-radius: var(--radius);
            box-shadow: var(--shadow);
            transition: var(--transition);
        }}

        .content img.blog-image:hover {{
            transform: translateY(-5px);
            box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.1), 0 4px 6px -2px rgba(0, 0, 0, 0.05);
        }}

        .image-container {{
            margin: 40px 0;
            text-align: center;
        }}

        .image-container figcaption {{
            margin-top: 10px;
            font-size: 0.9rem;
            color: var(--text-light);
            font-style: italic;
        }}

        .section-heading {{
            font-family: 'Playfair Display', serif;
            color: var(--primary);
            margin: 60px 0 30px;
            padding-bottom: 10px;
            border-bottom: 2px solid var(--border);
            font-size: 1.8rem;
        }}

        .data-table {{
            width: 100%;
            border-collapse: collapse;
            margin: 30px 0;
            font-size: 0.95rem;
            box-shadow: var(--shadow);
            border-radius: var(--radius);
            overflow: hidden;
        }}

        .data-table th, .data-table td {{
            padding: 12px 15px;
            text-align: left;
            border: 1px solid var(--border);
        }}

        .data-table th {{
            background-color: var(--primary);
            color: white;
            font-weight: 600;
        }}

        .data-table tr:nth-child(even) {{
            background-color: var(--background);
        }}

        .table-container {{
            margin: 40px 0;
            overflow-x: auto;
        }}

        .code-block {{
            background-color: #2d3748;
            color: #e2e8f0;
            padding: 20px;
            border-radius: var(--radius);
            overflow-x: auto;
            margin: 30px 0;
            font-family: 'Courier New', monospace;
            font-size: 0.9rem;
            line-height: 1.6;
        }}

        blockquote {{
            border-left: 4px solid var(--primary-light);
            padding: 20px;
            margin: 30px 0;
            background-color: var(--background);
            font-style: italic;
            color: var(--text-light);
        }}

        blockquote::before {{
            content: '“';
            font-size: 3rem;
            color: var(--primary-light);
            line-height: 0;
            vertical-align: -0.4em;
            margin-right: 10px;
        }}

        a {{
            color: var(--primary-light);
            text-decoration: none;
            transition: var(--transition);
        }}

        a:hover {{
            color: var(--secondary);
            text-decoration: underline;
        }}

        footer {{
            text-align: center;
            padding: 30px 0;
            margin-top: 60px;
            border-top: 1px solid var(--border);
            color: var(--text-light);
            font-size: 0.9rem;
        }}

        @media (max-width: 768px) {{
            .container {{
                padding: 0 15px;
            }}
            
            h1 {{
                font-size: 2rem;
            }}
            
            .content {{
                padding: 30px;
            }}
            
            .article-container {{
                grid-template-columns: 1fr;
            }}
        }}
    </style>

</head>
<body>
    <header>
        <h1>{title}</h1>
        <div class="meta">
            <span class="date">{date}</span> • <span class="author">kgsflink</span>
        </div>
    </header>
    
    <article class="content">
        {content}
    </article>
</body>
</html>"""

    def scrape_article(self, url, output_dir="professional_blogs", keep_original_urls=False):
        try:
            print(f"Processing: {url}")
            
            # Fetch page
            response = requests.get(url, headers=self.headers)
            response.raise_for_status()
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Extract article
            article = soup.find('article')
            if not article:
                print("No article content found")
                return None
                
            # Get metadata
            title = article.find('h1').get_text(strip=True) if article.find('h1') else "Professional Blog Post"
            date_element = article.find('time', class_='post-date')
            date = date_element.get_text(strip=True) if date_element else datetime.now().strftime("%B %d, %Y")
            
            # Create directory (even if keeping original URLs for consistency)
            article_dir = self.create_article_directory(output_dir, title)
            
            # Process images (either download or keep original URLs)
            base_url = '{uri.scheme}://{uri.netloc}'.format(uri=urlparse(url))
            self.process_images(article, article_dir, base_url, keep_original_urls)
            
            # Clean content
            content = self.clean_content(article)
            content = self.replace_author_info(content)
            
            # Generate HTML
            html = self.generate_html_template(title, date, content)
            
            # Save file
            with open(os.path.join(article_dir, "index.html"), 'w', encoding='utf-8') as f:
                f.write(html)
                
            print(f"Successfully saved to: {article_dir}")
            return article_dir
            
        except Exception as e:
            print(f"Error processing {url}: {str(e)}")
            return None

    def process_url_list(self, file_path, output_dir="professional_blogs", keep_original_urls=False):
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                urls = [line.strip() for line in f if line.strip()]
                
            print(f"Found {len(urls)} URLs to process")
            
            for url in urls:
                self.scrape_article(url, output_dir, keep_original_urls)
                
        except Exception as e:
            print(f"Error processing URL list: {str(e)}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Professional Blog Scraper')
    parser.add_argument('url', nargs='?', help='Single URL to scrape')
    parser.add_argument('-l', '--list', help='File containing list of URLs')
    parser.add_argument('-o', '--output', default='professional_blogs', help='Output directory')
    parser.add_argument('--keep-urls', action='store_true', help='Keep original image URLs instead of downloading')
    
    args = parser.parse_args()
    
    scraper = ProfessionalBlogScraper()
    
    if args.list:
        scraper.process_url_list(args.list, args.output, args.keep_urls)
    elif args.url:
        scraper.scrape_article(args.url, args.output, args.keep_urls)
    else:
        print("Please provide a URL or file with -l option")