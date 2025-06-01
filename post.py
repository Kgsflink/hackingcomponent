import re
import requests
from bs4 import BeautifulSoup
import os
from datetime import datetime
import shutil
import argparse
from urllib.parse import urlparse

class ArticleScraper:
    def __init__(self):
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        self.author_replacements = [
            ("Author: Théo ARCHIMBAUD – Pentester @Vaadata", "kgsflink"),
            ("Théo ARCHIMBAUD – Pentester @Vaadata", "kgsflink"),
            ("Author: Renaud CAYOL – Pentester @Vaadata", "kgsflink"),
            ("Renaud CAYOL – Pentester @Vaadata", "kgsflink"),
            ("<p><strong>Author: .*?@Vaadata</strong></p>", "<p><strong>Author: kgsflink</strong></p>")
        ]

    def sanitize_filename(self, filename):
        """Create safe filenames for storage"""
        filename = re.sub(r'[\\/*?:"<>|]', "", filename)
        return re.sub(r'\s+', '_', filename).lower()[:100]

    def create_directory_structure(self, base_dir, title):
        """Create organized folder structure for each article"""
        article_dir = os.path.join(base_dir, self.sanitize_filename(title))
        os.makedirs(article_dir, exist_ok=True)
        os.makedirs(os.path.join(article_dir, "images"), exist_ok=True)
        return article_dir

    def download_and_organize_images(self, soup, article_dir, url):
        """Download all images with proper naming and positioning"""
        base_url = '{uri.scheme}://{uri.netloc}'.format(uri=urlparse(url))
        images = []
        
        # Find all images and their context
        for idx, img in enumerate(soup.find_all('img')):
            src = img.get('src', '')
            if not src or src.startswith('data:'):
                continue
                
            # Handle relative URLs
            if not src.startswith(('http://', 'https://')):
                src = urljoin(base_url, src)
                
            try:
                # Get image with referer header for protected images
                response = requests.get(src, headers={**self.headers, 'Referer': url}, stream=True)
                response.raise_for_status()
                
                # Determine content type and extension
                content_type = response.headers.get('content-type', '').split('/')[-1]
                ext = content_type if content_type in ['jpeg', 'jpg', 'png', 'gif', 'webp'] else 'jpg'
                
                # Create descriptive filename based on context
                context = self.get_image_context(img)
                img_name = f"{idx+1}_{self.sanitize_filename(context)[:30]}.{ext}"
                img_path = os.path.join(article_dir, "images", img_name)
                
                # Save image
                with open(img_path, 'wb') as f:
                    response.raw.decode_content = True
                    shutil.copyfileobj(response.raw, f)
                
                # Update the img tag with new path
                img['src'] = f"images/{img_name}"
                images.append((src, f"images/{img_name}"))
                
            except Exception as e:
                print(f"Failed to download image {src}: {e}")
                images.append((src, src))  # Fallback to original URL
                
        return images

    def get_image_context(self, img):
        """Generate descriptive context for image filenames"""
        # Try to find caption
        if img.find_parent('figure') and img.find_parent('figure').find('figcaption'):
            return img.find_parent('figure').find('figcaption').get_text(strip=True)
        
        # Try to find adjacent heading
        for sibling in img.find_previous_siblings():
            if sibling.name in ['h2', 'h3', 'h4', 'h5', 'h6', 'p']:
                return sibling.get_text(strip=True)[:50]
                
        # Try to find parent section heading
        for ancestor in img.parents:
            if ancestor.find_previous_sibling(['h2', 'h3', 'h4', 'h5', 'h6']):
                return ancestor.find_previous_sibling(['h2', 'h3', 'h4', 'h5', 'h6']).get_text(strip=True)[:50]
                
        return "image"

    def replace_author_info(self, content):
        """Replace all variations of author information"""
        for pattern, replacement in self.author_replacements:
            content = re.sub(pattern, replacement, content, flags=re.IGNORECASE)
        return content

    def process_article_content(self, soup):
        """Clean and enhance article content"""
        # Remove unnecessary elements
        for element in soup.select('.post-meta, .tag-share, .related-posts, .post-foot'):
            element.decompose()
            
        # Improve formatting
        for table in soup.find_all('table'):
            table['class'] = table.get('class', []) + ['clean-table']
            
        return str(soup)

    def generate_professional_template(self, title, date, content):
        """Generate professional blog template with proper styling"""
        return f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title}</title>
    <link href="https://fonts.googleapis.com/css2?family=Merriweather:wght@400;700&family=Open+Sans:wght@400;600&display=swap" rel="stylesheet">
    <style>
        :root {{
            --primary-color: #2c3e50;
            --secondary-color: #3498db;
            --text-color: #333;
            --light-gray: #f8f9fa;
            --medium-gray: #e9ecef;
            --dark-gray: #6c757d;
        }}
        
        body {{
            font-family: 'Open Sans', sans-serif;
            line-height: 1.8;
            color: var(--text-color);
            max-width: 900px;
            margin: 0 auto;
            padding: 0 20px;
            background-color: #fff;
        }}
        
        header {{
            text-align: center;
            margin: 40px 0 60px;
            padding-bottom: 30px;
            border-bottom: 1px solid var(--medium-gray);
        }}
        
        h1 {{
            font-family: 'Merriweather', serif;
            color: var(--primary-color);
            font-size: 2.5rem;
            margin-bottom: 20px;
            line-height: 1.3;
        }}
        
        .meta {{
            color: var(--dark-gray);
            font-size: 0.95rem;
            margin-bottom: 30px;
        }}
        
        .featured-image {{
            max-width: 100%;
            height: auto;
            margin: 40px auto;
            border-radius: 4px;
            box-shadow: 0 5px 15px rgba(0,0,0,0.1);
            display: block;
        }}
        
        .content {{
            font-size: 1.1rem;
            margin-top: 40px;
        }}
        
        .content img {{
            max-width: 100%;
            height: auto;
            margin: 30px auto;
            display: block;
            border-radius: 4px;
            box-shadow: 0 3px 10px rgba(0,0,0,0.1);
        }}
        
        .content figcaption {{
            text-align: center;
            font-size: 0.9rem;
            color: var(--dark-gray);
            margin-top: 10px;
        }}
        
        h2, h3, h4 {{
            font-family: 'Merriweather', serif;
            color: var(--primary-color);
            margin-top: 50px;
            margin-bottom: 20px;
        }}
        
        h2 {{ font-size: 1.8rem; }}
        h3 {{ font-size: 1.5rem; }}
        h4 {{ font-size: 1.3rem; }}
        
        a {{
            color: var(--secondary-color);
            text-decoration: none;
            transition: color 0.3s;
        }}
        
        a:hover {{
            color: #1a6bac;
            text-decoration: underline;
        }}
        
        .clean-table {{
            width: 100%;
            border-collapse: collapse;
            margin: 30px 0;
            font-size: 0.95rem;
            box-shadow: 0 1px 3px rgba(0,0,0,0.1);
        }}
        
        .clean-table th, .clean-table td {{
            border: 1px solid var(--medium-gray);
            padding: 12px 15px;
            text-align: left;
        }}
        
        .clean-table th {{
            background-color: var(--light-gray);
            font-weight: 600;
        }}
        
        .clean-table tr:nth-child(even) {{
            background-color: var(--light-gray);
        }}
        
        pre {{
            background-color: var(--light-gray);
            padding: 20px;
            border-radius: 4px;
            overflow-x: auto;
            font-size: 0.9rem;
            line-height: 1.5;
            margin: 25px 0;
            border-left: 4px solid var(--secondary-color);
        }}
        
        code {{
            font-family: 'Courier New', Courier, monospace;
            background-color: var(--light-gray);
            padding: 2px 5px;
            border-radius: 3px;
            font-size: 0.9em;
        }}
        
        blockquote {{
            border-left: 4px solid var(--secondary-color);
            padding: 15px 20px;
            margin: 25px 0;
            background-color: var(--light-gray);
            font-style: italic;
        }}
        
        @media (max-width: 768px) {{
            body {{
                padding: 0 15px;
            }}
            
            h1 {{
                font-size: 2rem;
            }}
            
            .content {{
                font-size: 1rem;
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
    
    <div class="content">
        {content}
    </div>
</body>
</html>"""

    def scrape_article(self, url, output_dir="scraped_articles"):
        try:
            print(f"Processing: {url}")
            
            # Fetch the webpage
            response = requests.get(url, headers=self.headers)
            response.raise_for_status()
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Extract article content
            article = soup.find('article')
            if not article:
                print(f"No article found at {url}")
                return None
                
            # Extract metadata
            title = article.find('h1').get_text(strip=True) if article.find('h1') else "Untitled Article"
            date_element = article.find('time', class_='post-date')
            date = date_element.get_text(strip=True) if date_element else datetime.now().strftime("%B %d, %Y")
            
            # Create directory structure
            article_dir = self.create_directory_structure(output_dir, title)
            
            # Download and organize images
            self.download_and_organize_images(article, article_dir, url)
            
            # Process content
            content = self.process_article_content(article)
            content = self.replace_author_info(content)
            
            # Generate professional HTML
            html_content = self.generate_professional_template(title, date, content)
            
            # Save HTML file
            html_path = os.path.join(article_dir, "index.html")
            with open(html_path, 'w', encoding='utf-8') as f:
                f.write(html_content)
            
            print(f"Successfully saved to: {article_dir}")
            return article_dir
            
        except Exception as e:
            print(f"Error processing {url}: {str(e)}")
            return None

    def process_url_list(self, file_path, output_dir="scraped_articles"):
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                urls = [line.strip() for line in f if line.strip()]
                
            print(f"Found {len(urls)} URLs to process")
            
            for url in urls:
                self.scrape_article(url, output_dir)
                
        except Exception as e:
            print(f"Error processing URL list: {str(e)}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Professional Article Scraper')
    parser.add_argument('url', nargs='?', help='URL of the article to scrape')
    parser.add_argument('-l', '--list', help='Path to text file containing list of URLs')
    parser.add_argument('-o', '--output', default='scraped_articles', help='Output directory')
    
    args = parser.parse_args()
    
    scraper = ArticleScraper()
    
    if args.list:
        scraper.process_url_list(args.list, args.output)
    elif args.url:
        scraper.scrape_article(args.url, args.output)
    else:
        print("Please provide either a URL or a file with -l option")