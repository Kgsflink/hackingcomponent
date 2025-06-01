import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin
import os
from datetime import datetime

def fetch_and_redesign_article(url):
    try:
        # Fetch the webpage
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        response = requests.get(url, headers=headers)
        response.raise_for_status()

        # Parse HTML content
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Extract the main article content
        article = soup.find('article')
        if not article:
            raise ValueError("No article found on the page")
            
        # Extract title
        title = article.find('h1').get_text(strip=True) if article.find('h1') else "Article"
        
        # Extract date
        date_element = article.find('time', class_='post-date')
        date = date_element.get_text(strip=True) if date_element else datetime.now().strftime("%B %d, %Y")
        
        # Extract featured image
        featured_image = article.find('figure', class_='wp-block-image')
        featured_image_src = ""
        if featured_image and featured_image.find('img'):
            featured_image_src = featured_image.find('img')['src']
        
        # Extract all images
        images = []
        for img in article.find_all('img'):
            src = img.get('src', '')
            if src and not src.startswith('data:'):
                images.append(src)
        
        # Create a directory for images
        os.makedirs('article_images', exist_ok=True)
        
        # Download images
        local_images = {}
        for idx, img_url in enumerate(images[:5]):  # Limit to 5 images to avoid too many downloads
            try:
                img_data = requests.get(img_url, headers=headers).content
                img_name = f"image_{idx+1}.{img_url.split('.')[-1].lower()}"
                img_path = os.path.join('article_images', img_name)
                
                with open(img_path, 'wb') as handler:
                    handler.write(img_data)
                
                local_images[img_url] = img_path
            except Exception as e:
                print(f"Failed to download image {img_url}: {e}")
                local_images[img_url] = img_url  # Fallback to original URL
        
        # Create the redesigned HTML
        html_template = f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title}</title>
    <style>
        body {{
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            line-height: 1.6;
            color: #333;
            max-width: 900px;
            margin: 0 auto;
            padding: 20px;
        }}
        header {{
            text-align: center;
            margin-bottom: 40px;
            border-bottom: 1px solid #eee;
            padding-bottom: 20px;
        }}
        h1 {{
            color: #2c3e50;
            margin-bottom: 10px;
        }}
        .date {{
            color: #7f8c8d;
            font-size: 0.9em;
        }}
        .featured-image {{
            max-width: 100%;
            height: auto;
            margin: 20px 0;
            border-radius: 5px;
        }}
        .content {{
            margin-top: 30px;
        }}
        img {{
            max-width: 100%;
            height: auto;
            margin: 15px 0;
            border-radius: 3px;
            box-shadow: 0 2px 5px rgba(0,0,0,0.1);
        }}
        h2, h3, h4 {{
            color: #2c3e50;
            margin-top: 30px;
        }}
        a {{
            color: #3498db;
            text-decoration: none;
        }}
        a:hover {{
            text-decoration: underline;
        }}
        .wp-block-table table {{
            width: 100%;
            border-collapse: collapse;
            margin: 20px 0;
        }}
        .wp-block-table th, .wp-block-table td {{
            border: 1px solid #ddd;
            padding: 8px;
            text-align: left;
        }}
        .wp-block-table th {{
            background-color: #f2f2f2;
        }}
        pre {{
            background-color: #f5f5f5;
            padding: 15px;
            border-radius: 4px;
            overflow-x: auto;
        }}
        code {{
            font-family: 'Courier New', Courier, monospace;
            background-color: #f5f5f5;
            padding: 2px 4px;
            border-radius: 3px;
            font-size: 0.9em;
        }}
    </style>
</head>
<body>
    <header>
        <h1>{title}</h1>
        <div class="date">{date}</div>
        {f'<img src="{local_images.get(featured_image_src, featured_image_src)}" alt="Featured Image" class="featured-image">' if featured_image_src else ''}
    </header>
    
    <div class="content">
        {article.find('div', class_='post-content').prettify() if article.find('div', class_='post-content') else article.prettify()}
    </div>
</body>
</html>
        """
        
        # Replace image URLs in the content with local paths
        for original_url, local_path in local_images.items():
            html_template = html_template.replace(original_url, local_path)
        
        # Save the HTML file
        filename = f"{title.lower().replace(' ', '_')}.html"
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(html_template)
        
        print(f"Article saved as {filename}")
        return filename
        
    except Exception as e:
        print(f"An error occurred: {e}")
        return None

if __name__ == "__main__":
    url = input("Enter the article URL: ")
    fetch_and_redesign_article(url)