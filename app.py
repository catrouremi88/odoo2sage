from flask import Flask, request, send_file, render_template_string
import os, tempfile, io
from datetime import datetime
from converter import convert

app = Flask(__name__)

HTML = """<!DOCTYPE html>
<html lang="fr">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Odoo → Sage Export · MAJORE</title>
<link href="https://fonts.googleapis.com/css2?family=DM+Mono:ital,wght@0,400;0,500&family=DM+Sans:wght@300;400;600&display=swap" rel="stylesheet">
<style>
  *, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }
  :root {
    --bg: #0d0d10;
    --surface: #16161a;
    --border: #252530;
    --accent: #6c63ff;
    --accent2: #00e5a0;
    --text: #e8e8f0;
    --muted: #64647a;
    --danger: #ff4d6a;
    --r: 14px;
  }
  body {
    background: var(--bg);
    color: var(--text);
    font-family: 'DM Sans', sans-serif;
    min-height: 100vh;
    display: flex;
    align-items: center;
    justify-content: center;
    padding: 2rem;
    background-image:
      radial-gradient(ellipse 55% 35% at 75% 5%, rgba(108,99,255,0.13) 0%, transparent 65%),
      radial-gradient(ellipse 35% 25% at 5% 90%, rgba(0,229,160,0.08) 0%, transparent 60%);
  }
  .card {
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: 22px;
    padding: 2.8rem;
    width: 100%;
    max-width: 500px;
    box-shadow: 0 0 0 1px rgba(108,99,255,0.07), 0 40px 80px rgba(0,0,0,0.5);
  }
  .header {
    display: flex;
    align-items: center;
    gap: 12px;
    margin-bottom: 2.2rem;
  }
  .logo-box {
    width: 38px; height: 38px;
    background: linear-gradient(135deg, var(--accent) 0%, var(--accent2) 100%);
    border-radius: 10px;
    display: flex; align-items: center; justify-content: center;
    font-size: 17px; flex-shrink: 0;
  }
  .brand {
    font-family: 'DM Mono', monospace;
    font-size: 0.78rem;
    color: var(--muted);
    letter-spacing: 0.06em;
    line-height: 1.4;
  }
  .brand strong { color: var(--text); display: block; }
  h1 {
    font-size: 1.55rem;
    font-weight: 600;
    letter-spacing: -0.025em;
    margin-bottom: 0.4rem;
  }
  .sub {
    color: var(--muted);
    font-size: 0.875rem;
    line-height: 1.55;
    margin-bottom: 2rem;
  }
  .drop-zone {
    position: relative;
    border: 2px dashed var(--border);
    border-radius: var(--r);
    padding: 2.2rem 1.5rem;
    text-align: center;
    cursor: pointer;
    transition: border-color 0.2s, background 0.2s;
    background: rgba(255,255,255,0.015);
  }
  .drop-zone:hover, .drop-zone.over {
    border-color: var(--accent);
    background: rgba(108,99,255,0.07);
  }
  .drop-zone input[type="file"] {
    position: absolute; inset: 0;
    opacity: 0; cursor: pointer;
    width: 100%; height: 100%;
  }
  .drop-icon { font-size: 2rem; margin-bottom: 0.6rem; display: block; }
  .drop-text { font-size: 0.875rem; color: var(--muted); line-height: 1.5; }
  .drop-text strong { color: var(--accent); }
  .file-badge {
    display: none;
    margin-top: 0.9rem;
    padding: 0.6rem 0.9rem;
    background: rgba(0,229,160,0.08);
    border: 1px solid rgba(0,229,160,0.2);
    border-radius: 8px;
    font-family: 'DM Mono', monospace;
    font-size: 0.78rem;
    color: var(--accent2);
    gap: 6px;
    align-items: center;
  }
  .file-badge.show { display: flex; }
  .btn {
    display: block; width: 100%;
    margin-top: 1.3rem;
    padding: 0.875rem;
    background: linear-gradient(135deg, var(--accent) 0%, #8b5cf6 100%);
    color: #fff;
    border: none; border-radius: var(--r);
    font-family: 'DM Sans', sans-serif;
    font-size: 0.95rem; font-weight: 600;
    cursor: pointer;
    transition: transform 0.15s, box-shadow 0.15s;
    letter-spacing: 0.01em;
  }
  .btn:hover:not(:disabled) {
    transform: translateY(-2px);
    box-shadow: 0 10px 28px rgba(108,99,255,0.38);
  }
  .btn:disabled { opacity: 0.45; cursor: not-allowed; }
  .btn .spin {
    display: none; width: 16px; height: 16px;
    border: 2px solid rgba(255,255,255,0.3);
    border-top-color: #fff;
    border-radius: 50%;
    animation: spin 0.65s linear infinite;
    margin: 0 auto;
  }
  .btn.loading .lbl { display: none; }
  .btn.loading .spin { display: block; }
  @keyframes spin { to { transform: rotate(360deg); } }
  .alert {
    margin-top: 1rem;
    padding: 0.75rem 1rem;
    border-radius: 9px;
    font-size: 0.84rem;
    line-height: 1.45;
  }
  .alert-err { background: rgba(255,77,106,0.1); border: 1px solid rgba(255,77,106,0.22); color: var(--danger); }
  .sep { border: none; border-top: 1px solid var(--border); margin: 1.8rem 0 1.4rem; }
  .rules {
    display: grid; grid-template-columns: 1fr 1fr;
    gap: 0.65rem;
  }
  .rule {
    background: rgba(255,255,255,0.025);
    border: 1px solid var(--border);
    border-radius: 9px;
    padding: 0.6rem 0.75rem;
    font-size: 0.73rem;
  }
  .rule .rl { color: var(--muted); margin-bottom: 2px; }
  .rule .rv { font-family: 'DM Mono', monospace; font-size: 0.75rem; color: var(--text); }
</style>
</head>
<body>
<div class="card">
  <div class="header">
    <div class="logo-box">⟶</div>
    <div class="brand"><strong>Built by Rémi Catrou</strong>Odoo → Sage 100</div>
  </div>

  <h1>Export Sage 100</h1>
  <p class="sub">Importe l'extraction Odoo (.xlsx) pour générer le fichier d'import Sage avec les codes analytiques.</p>

  {% if error %}
  <div class="alert alert-err">⚠ {{ error }}</div>
  {% endif %}

  <form method="POST" enctype="multipart/form-data" id="frm">
    <div class="drop-zone" id="dz">
      <input type="file" name="odoo_file" accept=".xlsx" id="fi" required>
      <span class="drop-icon">📂</span>
      <div class="drop-text">
        <strong>Clique ou glisse</strong> ton fichier ici<br>
        Export Odoo (.xlsx)
      </div>
      <div class="file-badge" id="badge">📄 <span id="fname"></span></div>
    </div>
    <button class="btn" id="btn" type="submit" disabled>
      <span class="lbl">Générer le fichier Sage</span>
      <div class="spin"></div>
    </button>
  </form>

  {% if error %}{% else %}
  <hr class="sep">
  <div class="rules">
    <div class="rule"><div class="rl">Journal</div><div class="rv">VT (fixe)</div></div>
    <div class="rule"><div class="rl">Dates</div><div class="rv">JJMMAA</div></div>
    <div class="rule"><div class="rl">Compte 411</div><div class="rv">41100000</div></div>
    <div class="rule"><div class="rl">Altios</div><div class="rv">Codes rétro</div></div>
    <div class="rule"><div class="rl">Clients</div><div class="rv">Codes affaires</div></div>
    <div class="rule"><div class="rl">Taxe EX/EU/20%</div><div class="rv">Export/CEE/FR</div></div>
  </div>
  {% endif %}
</div>

<script>
  const fi = document.getElementById('fi');
  const btn = document.getElementById('btn');
  const dz = document.getElementById('dz');
  const badge = document.getElementById('badge');
  const fname = document.getElementById('fname');

  fi.addEventListener('change', () => {
    if (fi.files.length) {
      fname.textContent = fi.files[0].name;
      badge.classList.add('show');
      btn.disabled = false;
    }
  });

  dz.addEventListener('dragover', e => { e.preventDefault(); dz.classList.add('over'); });
  dz.addEventListener('dragleave', () => dz.classList.remove('over'));
  dz.addEventListener('drop', e => { e.preventDefault(); dz.classList.remove('over'); });

  function resetBtn() {
    btn.classList.remove('loading');
    btn.disabled = false;
  }

  document.getElementById('frm').addEventListener('submit', (e) => {
    e.preventDefault();
    if (!fi.files.length) return;

    btn.classList.add('loading');
    btn.disabled = true;

    const formData = new FormData(document.getElementById('frm'));
    const today = new Date();
    const dd = String(today.getDate()).padStart(2,'0');
    const mm = String(today.getMonth()+1).padStart(2,'0');
    const yyyy = today.getFullYear();
    const filename = `IMPORTSAGE_${dd}${mm}${yyyy}.txt`;

    fetch('/', { method: 'POST', body: formData })
      .then(res => {
        if (!res.ok) return res.text().then(t => { throw new Error(t); });
        return res.blob();
      })
      .then(blob => {
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url; a.download = filename;
        document.body.appendChild(a); a.click();
        document.body.removeChild(a);
        URL.revokeObjectURL(url);

        resetBtn();

        // Message succès
        let banner = document.getElementById('success-banner');
        if (!banner) {
          banner = document.createElement('div');
          banner.id = 'success-banner';
          banner.style.cssText = 'margin-top:1rem;padding:0.75rem 1rem;border-radius:9px;font-size:0.84rem;line-height:1.45;background:rgba(0,229,160,0.08);border:1px solid rgba(0,229,160,0.22);color:#00e5a0;';
          document.getElementById('frm').after(banner);
        }
        banner.innerHTML = `✓ Fichier <strong>${filename}</strong> généré — disponible dans vos téléchargements.`;
      })
      .catch(err => {
        resetBtn();
        alert('Erreur lors de la conversion. Vérifiez votre fichier.');
      });
  });
</script>
</body>
</html>"""

@app.route('/', methods=['GET'])
def index():
    return render_template_string(HTML, error=None)

@app.route('/', methods=['POST'])
def upload():
    f = request.files.get('odoo_file')
    if not f or not f.filename.endswith('.xlsx'):
        return render_template_string(HTML, error="Fichier invalide — seuls les fichiers .xlsx sont acceptés.")

    try:
        with tempfile.NamedTemporaryFile(suffix='.xlsx', delete=False) as tmp:
            f.save(tmp.name)
            result = convert(tmp.name)
        os.unlink(tmp.name)

        filename = f"IMPORTSAGE_{datetime.today().strftime('%d%m%Y')}.txt"
        output = io.BytesIO(result.encode('utf-8'))
        output.seek(0)
        return send_file(
            output,
            mimetype='text/plain',
            as_attachment=True,
            download_name=filename
        )
    except Exception as e:
        return render_template_string(HTML, error=f"Erreur lors de la conversion : {str(e)}")

if __name__ == '__main__':
    app.run(debug=False)
