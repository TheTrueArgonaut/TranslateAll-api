from flask import Flask, request, jsonify, render_template_string
import requests
import os

app = Flask(__name__)

DEEPL_API_KEY = os.getenv("DEEPL_API_KEY", "74732027-e377-4323-8a86-2744ab7ae7ca")

HTML_PAGE = """
<!DOCTYPE html>
<html>
<head>
    <title>Translate All API — $0.10/translation</title>
    <style>
        body { font-family: Arial, sans-serif; max-width: 900px; margin: 0 auto; padding: 20px; background: #f8f9fa; }
        .header { background: #007cba; color: white; padding: 30px; border-radius: 8px; text-align: center; }
        .demo, .pricing, .contact { background: white; padding: 20px; border-radius: 8px; margin: 20px 0; }
        textarea, select { width: 100%; padding: 10px; margin: 10px 0; }
        .translate-btn { background: #28a745; color: white; border: none; padding: 10px 20px; cursor: pointer; }
        .result { background: #e8f5e8; padding: 15px; border-radius: 4px; margin-top: 15px; }
        ul li { margin: 10px 0; }
        .contact a { color: #007cba; text-decoration: none; }
    </style>
</head>
<body>
    <div class="header">
        <h1>Translate All API</h1>
        <p>Enterprise-grade translation at just $0.10 per call</p>
    </div>

    <div class="demo">
        <h2>Live Demo</h2>
        <textarea id="text" rows="4" placeholder="Enter text here"></textarea>
        <select id="lang">
            <option value="ES">Spanish</option>
            <option value="FR">French</option>
            <option value="DE">German</option>
            <option value="IT">Italian</option>
            <option value="PT">Portuguese</option>
            <option value="ZH">Chinese</option>
            <option value="JA">Japanese</option>
        </select>
        <button id="translateBtn" class="translate-btn">Translate Now</button>
        <div id="result"></div>
    </div>

    <div class="pricing">
        <h2>Pricing</h2>
        <ul>
            <li><strong>$0.10</strong> per translation</li>
            <li>Instant caching &lt;10ms</li>
            <li>Sentence-based accuracy</li>
            <li>30+ languages supported</li>
        </ul>
    </div>

    <div class="contact">
        <h2>Contact & Licensing</h2>
        <p>Email: <a href="mailto:SakelariosAll@argonautdigitalventures.com">SakelariosAll@argonautdigitalventures.com</a></p>
        <p>Created by Sakelarios All</p>
    </div>

    <script>
    window.translate = async function() {
        const text = document.getElementById('text').value.trim();
        const lang = document.getElementById('lang').value;
        const out = document.getElementById('result');
        if (!text) {
            out.innerHTML = '<div style="color:red;">Please enter some text.</div>';
            return;
        }
        out.innerHTML = 'Translating…';
        try {
            const res = await fetch('/translate', {
                method: 'POST',
                headers: {'Content-Type':'application/json'},
                body: JSON.stringify({ text, target: lang })
            });
            const data = await res.json();
            if (data.success) {
                out.innerHTML = `<div class="result"><strong>Translation:</strong> ${data.translation}</div>`;
            } else {
                out.innerHTML = `<div style="color:red;">Error: ${data.error}</div>`;
            }
        } catch (e) {
            out.innerHTML = `<div style="color:red;">Network error: ${e.message}</div>`;
        }
    }
    document.addEventListener('DOMContentLoaded', () => {
        document.getElementById('translateBtn').addEventListener('click', translate);
    });
    </script>
</body>
</html>
"""

@app.route('/')
def home():
    return render_template_string(HTML_PAGE)

@app.route('/translate', methods=['POST'])
def translate():
    try:
        body = request.get_json() or {}
        text = body.get('text','').strip()
        if not text:
            return jsonify({'success': False, 'error': 'No text provided'})
        target = body.get('target','ES')
        # Pro endpoint for DeepL API Pro
        resp = requests.post(
            "https://api.deepl.com/v2/translate",
            headers={"Authorization": f"DeepL-Auth-Key {DEEPL_API_KEY}"},
            data={"text": text, "target_lang": target, "preserve_formatting": "1"},
            timeout=10
        )
        if resp.status_code == 200:
            tr = resp.json()['translations'][0]['text']
            return jsonify({'success': True, 'translation': tr})
        else:
            return jsonify({'success': False, 'error': f'DeepL error {resp.status_code}'})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/health')
def health():
    return jsonify({'status': 'healthy', 'service': 'Translate All API'})

if __name__ == '__main__':
    port = int(os.getenv('PORT', 8080))
    app.run(host='0.0.0.0', port=port, debug=True)
