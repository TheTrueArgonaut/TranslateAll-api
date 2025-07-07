from flask import Flask, request, jsonify, render_template_string
from flask_cors import CORS
import requests
import os
import stripe
import sqlite3
import uuid
from datetime import datetime

app = Flask(__name__)
CORS(app)

DEEPL_API_KEY = os.getenv("DEEPL_API_KEY", "74732027-e377-4323-8a86-2744ab7ae7ca")
# Read the Stripe Secret Key from env for live mode
stripe.api_key = os.getenv("STRIPE_SECRET_KEY")
# Read the Stripe Publishable Key from env for live mode, defaulting to your live key if unset
stripe_publishable_key = os.getenv(
    "STRIPE_PUBLISHABLE_KEY",
    "pk_live_51Rhy6qCjwnT8QEVd4z0LnPKz2fgKfc4Yw7YXo1VwtHUK8ijFPjmoZpmaeCPUEr2pDAdwLsMMi8xaMdTKvxY6Wfdd00sxxNAKcD"
)

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
        console.log('translate() called', document.getElementById('text').value, document.getElementById('lang').value);
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
                body: JSON.stringify({text, target: lang})
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

    <!-- Stripe.js -->
    <script src="https://js.stripe.com/v3/"></script>

    <!-- Checkout button -->
    <button id="checkout-button" class="translate-btn">Subscribe for $9.99/mo</button>
    <script>
      const stripe = Stripe('{{ stripe_publishable_key }}');
      document.getElementById('checkout-button').addEventListener('click', async () => {
        try {
          const resp = await fetch('/create-checkout-session', { method: 'POST' });
          const data = await resp.json();
          if (data.error) {
            console.error('Checkout session error:', data.error);
            return;
          }
          if (!data.sessionId) {
            console.error('No sessionId returned from server');
            return;
          }
          await stripe.redirectToCheckout({ sessionId: data.sessionId });
        } catch (err) {
          console.error('Network or server error:', err);
        }
      });
    </script>
</body>
</html>
"""

# Initialize SQLite database for API keys
def init_db():
    conn = sqlite3.connect('api_keys.db')
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS api_keys (
            key TEXT PRIMARY KEY,
            created TIMESTAMP,
            uses INTEGER DEFAULT 0
        )
    ''')
    conn.commit()
    conn.close()

init_db()

@app.route('/')
def home():
    # Render the HTML template with the Stripe publishable key
    return render_template_string(HTML_PAGE, stripe_publishable_key=stripe_publishable_key)

@app.route('/health')
def health():
    return jsonify({'status': 'healthy', 'service': 'Translate All API'})

@app.route('/create-key', methods=['POST'])
def create_key():
    # generate and store a new API key
    new_key = uuid.uuid4().hex
    conn = sqlite3.connect('api_keys.db')
    c = conn.cursor()
    c.execute('INSERT INTO api_keys (key, created) VALUES (?, ?)', (new_key, datetime.utcnow()))
    conn.commit()
    conn.close()
    return jsonify({'apiKey': new_key})

@app.route('/create-checkout-session', methods=['POST'])
def create_checkout_session():
    try:
        session = stripe.checkout.Session.create(
            line_items=[{"price": "price_1RhzVOCjwnT8QEVdyoyyCLQ9", "quantity": 1}],
            mode="subscription",
            success_url=request.host_url + "?success=true",
            cancel_url=request.host_url + "?canceled=true",
        )
        return jsonify({"sessionId": session.id})
    except Exception as e:
        app.logger.error(f"Stripe session creation failed: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/translate', methods=['POST'])
def translate():
    # enforce API key, quota checking
    api_key = request.headers.get('X-API-KEY')
    if not api_key:
        return jsonify({'success': False, 'error': 'API key required'}), 401
    conn = sqlite3.connect('api_keys.db')
    c = conn.cursor()
    c.execute('SELECT uses FROM api_keys WHERE key = ?', (api_key,))
    row = c.fetchone()
    if not row:
        conn.close()
        return jsonify({'success': False, 'error': 'Invalid API key'}), 401
    uses = row[0] + 1
    if uses > 2000:
        conn.close()
        return jsonify({'success': False, 'error': 'Quota exceeded'}), 403
    c.execute('UPDATE api_keys SET uses = ? WHERE key = ?', (uses, api_key))
    conn.commit()
    conn.close()
    try:
        body = request.get_json() or {}
        text = body.get('text','').strip()
        if not text:
            return jsonify({'success': False, 'error': 'No text provided'})
        target = body.get('target','ES')
        resp = requests.post(
            "https://api.deepl.com/v2/translate",
            headers={"Authorization": f"DeepL-Auth-Key {DEEPL_API_KEY}"},
            data={"text": text, "target_lang": target, "preserve_formatting":"1"},
            timeout=10
        )
        if resp.status_code == 200:
            tr = resp.json()['translations'][0]['text']
            return jsonify({'success': True, 'translation': tr})
        else:
            return jsonify({'success': False, 'error': f'DeepL error {resp.status_code}'})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

if __name__ == '__main__':
    port = int(os.getenv('PORT', 8080))
    app.run(host='0.0.0.0', port=port, debug=True)