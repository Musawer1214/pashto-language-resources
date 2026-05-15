---
layout: null
title: Pashto Language Resources
description: A curated hub for Pashto datasets, papers, tools, ASR, TTS, OCR, NLP, and machine translation resources.
---
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Pashto Language Resources</title>
  <meta name="description" content="A curated hub for Pashto datasets, papers, tools, ASR, TTS, OCR, NLP, and machine translation resources.">
  <style>
    :root {
      color-scheme: light;
      --ink: #14221f;
      --muted: #5c6f68;
      --line: #d8e3df;
      --line-strong: #bfd0ca;
      --paper: #ffffff;
      --paper-soft: #f7faf8;
      --surface: rgba(255, 255, 255, 0.88);
      --brand: #176b5b;
      --brand-dark: #0d3d35;
      --brand-soft: #dff2ed;
      --accent: #c2782f;
      --accent-soft: #fff1de;
      --blue: #2f6f9f;
      --shadow: 0 20px 48px rgba(24, 50, 43, 0.13);
      --radius: 8px;
      font-family: Inter, ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
    }

    * { box-sizing: border-box; }

    html { scroll-behavior: smooth; }

    body {
      margin: 0;
      min-height: 100vh;
      color: var(--ink);
      background:
        radial-gradient(circle at 12% 8%, rgba(23, 107, 91, 0.13), transparent 30rem),
        linear-gradient(180deg, #edf6f3 0%, #fbfcfa 38%, #f4f7f5 100%);
    }

    a { color: inherit; text-decoration: none; }

    .shell {
      width: min(1180px, calc(100% - 32px));
      margin: 0 auto;
      padding: 20px 0 48px;
    }

    .topbar {
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: 16px;
      padding: 12px 14px;
      background: rgba(255, 255, 255, 0.78);
      border: 1px solid var(--line);
      border-radius: var(--radius);
      box-shadow: 0 12px 28px rgba(33, 56, 50, 0.08);
      backdrop-filter: blur(14px);
      position: sticky;
      top: 12px;
      z-index: 10;
    }

    .brand {
      display: inline-flex;
      align-items: center;
      gap: 10px;
      min-width: 210px;
      font-weight: 800;
    }

    .brand-mark {
      width: 36px;
      height: 36px;
      display: grid;
      place-items: center;
      border-radius: 8px;
      background: var(--brand-dark);
      color: white;
      font-weight: 900;
    }

    .brand small {
      display: block;
      color: var(--muted);
      font-weight: 650;
      margin-top: 2px;
    }

    .nav {
      display: flex;
      align-items: center;
      gap: 8px;
      flex-wrap: wrap;
      justify-content: flex-end;
    }

    .nav a,
    .button {
      min-height: 40px;
      display: inline-flex;
      align-items: center;
      justify-content: center;
      gap: 8px;
      border-radius: 8px;
      border: 1px solid var(--line);
      background: white;
      color: var(--ink);
      font-weight: 750;
      padding: 0 14px;
      transition: transform 0.18s ease, border-color 0.18s ease, background 0.18s ease;
    }

    .nav a:hover,
    .button:hover {
      transform: translateY(-1px);
      border-color: var(--brand);
    }

    .button.primary {
      background: var(--brand);
      border-color: var(--brand);
      color: white;
    }

    .hero {
      margin-top: 22px;
      display: grid;
      grid-template-columns: minmax(0, 1.25fr) minmax(280px, 0.75fr);
      gap: 18px;
      align-items: stretch;
    }

    .hero-main,
    .panel,
    .card {
      border: 1px solid var(--line);
      border-radius: var(--radius);
      background: var(--surface);
      box-shadow: var(--shadow);
    }

    .hero-main {
      overflow: hidden;
      position: relative;
      min-height: 470px;
      padding: clamp(26px, 5vw, 54px);
      display: flex;
      flex-direction: column;
      justify-content: space-between;
      background:
        linear-gradient(135deg, rgba(13, 61, 53, 0.95), rgba(23, 107, 91, 0.88)),
        url("https://images.unsplash.com/photo-1481627834876-b7833e8f5570?auto=format&fit=crop&w=1600&q=78") center/cover;
      color: white;
    }

    .hero-main::after {
      content: "";
      position: absolute;
      inset: auto 0 0;
      height: 12px;
      background: linear-gradient(90deg, var(--accent), #e0b965, var(--blue));
    }

    .eyebrow {
      display: inline-flex;
      width: max-content;
      align-items: center;
      gap: 8px;
      border-radius: 999px;
      border: 1px solid rgba(255, 255, 255, 0.24);
      background: rgba(255, 255, 255, 0.12);
      padding: 7px 12px;
      font-size: 0.83rem;
      font-weight: 800;
      text-transform: uppercase;
    }

    h1 {
      margin: 22px 0 14px;
      max-width: 820px;
      font-size: clamp(2.2rem, 6vw, 5rem);
      line-height: 1;
      letter-spacing: 0;
    }

    .lede {
      max-width: 720px;
      color: rgba(255, 255, 255, 0.84);
      font-size: clamp(1rem, 2vw, 1.22rem);
      line-height: 1.65;
      margin: 0;
    }

    .hero-actions {
      display: flex;
      align-items: center;
      gap: 10px;
      flex-wrap: wrap;
      margin-top: 26px;
    }

    .hero-actions .button {
      border-color: rgba(255, 255, 255, 0.26);
      background: rgba(255, 255, 255, 0.12);
      color: white;
      backdrop-filter: blur(10px);
    }

    .hero-actions .primary {
      background: white;
      color: var(--brand-dark);
      border-color: white;
    }

    .snapshot {
      padding: 22px;
      display: grid;
      gap: 14px;
      align-content: start;
      background: rgba(255, 255, 255, 0.9);
    }

    .snapshot h2,
    .section h2 {
      margin: 0;
      font-size: 1.15rem;
    }

    .snapshot p,
    .section p,
    .card p {
      margin: 0;
      color: var(--muted);
      line-height: 1.58;
    }

    .stat {
      padding: 16px;
      border: 1px solid var(--line);
      border-radius: var(--radius);
      background: var(--paper);
    }

    .stat strong {
      display: block;
      font-size: 2rem;
      color: var(--brand-dark);
      line-height: 1;
      margin-bottom: 6px;
    }

    .section {
      margin-top: 20px;
      padding: 26px;
      border: 1px solid var(--line);
      border-radius: var(--radius);
      background: rgba(255, 255, 255, 0.72);
    }

    .section-head {
      display: flex;
      justify-content: space-between;
      gap: 16px;
      align-items: end;
      margin-bottom: 18px;
    }

    .grid {
      display: grid;
      grid-template-columns: repeat(3, minmax(0, 1fr));
      gap: 14px;
    }

    .card {
      min-height: 190px;
      padding: 18px;
      display: flex;
      flex-direction: column;
      justify-content: space-between;
      background: var(--paper);
      box-shadow: 0 12px 30px rgba(30, 55, 49, 0.08);
    }

    .card h3 {
      margin: 0 0 8px;
      font-size: 1.06rem;
    }

    .chip-row {
      display: flex;
      gap: 8px;
      flex-wrap: wrap;
      margin-top: 14px;
    }

    .chip {
      display: inline-flex;
      align-items: center;
      min-height: 30px;
      padding: 0 10px;
      border-radius: 999px;
      border: 1px solid var(--line);
      background: var(--paper-soft);
      color: var(--muted);
      font-size: 0.82rem;
      font-weight: 750;
    }

    .card .button {
      width: max-content;
      margin-top: 18px;
    }

    .wide {
      grid-column: span 2;
      background: linear-gradient(135deg, var(--accent-soft), white);
    }

    footer {
      padding: 26px 4px 0;
      color: var(--muted);
      font-size: 0.9rem;
    }

    @media (max-width: 900px) {
      .topbar,
      .section-head {
        align-items: stretch;
        flex-direction: column;
      }

      .nav {
        justify-content: flex-start;
      }

      .hero {
        grid-template-columns: 1fr;
      }

      .hero-main {
        min-height: 430px;
      }

      .grid {
        grid-template-columns: 1fr;
      }

      .wide {
        grid-column: auto;
      }
    }

    @media (max-width: 560px) {
      .shell {
        width: min(100% - 20px, 1180px);
        padding-top: 10px;
      }

      .nav a,
      .button {
        width: 100%;
      }

      .hero-main,
      .section,
      .snapshot {
        padding: 18px;
      }
    }
  </style>
</head>
<body>
  <main class="shell">
    <nav class="topbar" aria-label="Site navigation">
      <a class="brand" href="./">
        <span class="brand-mark">PL</span>
        <span>Pashto Resources<small>Datasets, papers, tools</small></span>
      </a>
      <div class="nav">
        <a href="search/">Search</a>
        <a href="papers/">Papers</a>
        <a href="pashto_datasets.html">Datasets</a>
        <a href="pashto_asr.html">ASR</a>
        <a href="pashto_tts.html">TTS</a>
        <a href="https://github.com/musawer1214/pashto-language-resources">GitHub</a>
      </div>
    </nav>

    <section class="hero">
      <div class="hero-main">
        <div>
          <span class="eyebrow">Open Pashto language technology catalog</span>
          <h1>Find useful Pashto resources without digging through noise.</h1>
          <p class="lede">Browse curated datasets, papers, models, benchmarks, and tools for speech, text, OCR, NLP, and machine translation work.</p>
          <div class="hero-actions">
            <a class="button primary" href="search/">Open resource search</a>
            <a class="button" href="papers/">Browse papers</a>
          </div>
        </div>
      </div>

      <aside class="snapshot" aria-label="Catalog snapshot">
        <h2>Catalog Snapshot</h2>
        <p>The site separates technical resources from research papers and highlights stronger, reviewed entries first.</p>
        <div class="stat"><strong>302</strong><span>total catalog records</span></div>
        <div class="stat"><strong>127</strong><span>technical resources</span></div>
        <div class="stat"><strong>175</strong><span>research papers</span></div>
      </aside>
    </section>

    <section class="section" aria-labelledby="paths-title">
      <div class="section-head">
        <div>
          <h2 id="paths-title">Choose a Starting Point</h2>
          <p>Focused pages help you jump directly into the kind of Pashto work you are doing.</p>
        </div>
      </div>

      <div class="grid">
        <article class="card">
          <div>
            <h3>Technical Search</h3>
            <p>Filter datasets, models, tools, benchmarks, code, and projects by task, source, review status, and keyword.</p>
            <div class="chip-row">
              <span class="chip">Datasets</span>
              <span class="chip">Models</span>
              <span class="chip">Tools</span>
            </div>
          </div>
          <a class="button primary" href="search/">Search resources</a>
        </article>

        <article class="card">
          <div>
            <h3>Paper Search</h3>
            <p>Explore Pashto research papers with task filters for ASR, OCR, machine translation, NLP, and speech work.</p>
            <div class="chip-row">
              <span class="chip">ASR</span>
              <span class="chip">MT</span>
              <span class="chip">OCR</span>
            </div>
          </div>
          <a class="button primary" href="papers/">Open papers</a>
        </article>

        <article class="card">
          <div>
            <h3>Datasets</h3>
            <p>Start with public Pashto datasets, corpus links, speech data, text data, and evaluation resources.</p>
            <div class="chip-row">
              <span class="chip">Speech</span>
              <span class="chip">Text</span>
              <span class="chip">MT</span>
            </div>
          </div>
          <a class="button primary" href="pashto_datasets.html">View datasets</a>
        </article>

        <article class="card">
          <div>
            <h3>ASR</h3>
            <p>Find automatic speech recognition datasets, models, benchmarks, and papers for Pashto speech.</p>
            <div class="chip-row">
              <span class="chip">Speech</span>
              <span class="chip">Benchmarks</span>
            </div>
          </div>
          <a class="button" href="pashto_asr.html">ASR page</a>
        </article>

        <article class="card">
          <div>
            <h3>TTS</h3>
            <p>Find text-to-speech papers, datasets, models, and training references for Pashto voice systems.</p>
            <div class="chip-row">
              <span class="chip">Voice</span>
              <span class="chip">Speech synthesis</span>
            </div>
          </div>
          <a class="button" href="pashto_tts.html">TTS page</a>
        </article>

        <article class="card wide">
          <div>
            <h3>Contribute or Audit</h3>
            <p>Use the catalog guide and contribution notes to add useful resources, improve metadata, or remove dead and low-value links.</p>
            <div class="chip-row">
              <span class="chip">Quality checks</span>
              <span class="chip">Metadata</span>
              <span class="chip">Automation</span>
            </div>
          </div>
          <a class="button" href="https://github.com/musawer1214/pashto-language-resources/blob/main/docs/resource_catalog.md">Read catalog guide</a>
        </article>
      </div>
    </section>

    <section class="section" aria-labelledby="how-title">
      <div class="section-head">
        <div>
          <h2 id="how-title">How to Use This Hub</h2>
          <p>Use search first when you need a resource quickly. Use the topic pages when you are planning a focused ASR, TTS, dataset, OCR, NLP, or MT workflow.</p>
        </div>
        <a class="button" href="https://github.com/musawer1214/pashto-language-resources/blob/main/README.md#contributing">Contribute</a>
      </div>
      <div class="grid">
        <article class="card">
          <div>
            <h3>Scan by Task</h3>
            <p>Task filters surface resource groups such as ASR, TTS, OCR, NLP, and machine translation.</p>
          </div>
        </article>
        <article class="card">
          <div>
            <h3>Open the Source</h3>
            <p>Every result keeps the original URL visible so you can verify the project, paper, dataset, or model card yourself.</p>
          </div>
        </article>
        <article class="card">
          <div>
            <h3>Prefer Reviewed Items</h3>
            <p>Curated and checked entries are highlighted, while the automation filters out empty, deleted, and placeholder resources.</p>
          </div>
        </article>
      </div>
    </section>

    <footer>
      Maintained as an open catalog for Pashto language technology research and development.
    </footer>
  </main>
</body>
</html>
