from flask import Flask, request, Response
from flask_cors import CORS
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin

app = Flask(__name__)
CORS(app)

def rewrite_html(html, base_url):
    soup = BeautifulSoup(html, 'html.parser')

    for tag in soup.find_all('a', href=True):
        tag['href'] = f"/proxy?url={urljoin(base_url, tag['href'])}"

    for form in soup.find_all('form', action=True):
        original_action = urljoin(base_url, form['action'])
        form['action'] = '/proxy'
        hidden = soup.new_tag('input', type='hidden', name='url', value=original_action)
        form.insert(0, hidden)

    for tag in soup.find_all(['img', 'script', 'link']):
        attr = 'src' if tag.name in ['img', 'script'] else 'href'
        if tag.has_attr(attr):
            tag[attr] = urljoin(base_url, tag[attr])

    return str(soup)

@app.route('/')
def home():
    return '''
    <form action="/proxy" method="get">
        URL: <input type="text" name="url" size="50">
        <input type="submit" value="Go">
    </form>
    '''

@app.route('/proxy', methods=['GET', 'POST'])
def proxy():
    target_url = request.args.get('url') if request.method == 'GET' else request.form.get('url')
    if not target_url:
        return 'No URL provided.'

    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5'
        }

        resp = requests.request(request.method, target_url, headers=headers, data=request.form if request.method == 'POST' else None, params=request.args)

        content_type = resp.headers.get('Content-Type', '')
        if 'text/html' in content_type:
            modified_html = rewrite_html(resp.text, target_url)
            return Response(modified_html, content_type='text/html')
        else:
            return Response(resp.content, content_type=content_type)

    except Exception as e:
        return f'Error: {e}'

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
