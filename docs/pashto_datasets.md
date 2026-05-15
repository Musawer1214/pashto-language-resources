---
layout: null
title: Pashto Datasets
description: Find Pashto datasets for speech recognition, text-to-speech, NLP, OCR, and machine translation.
keywords: Pashto datasets, Pashto corpus, Pashto ASR dataset, Pashto TTS dataset
---
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Pashto Datasets</title>
  <meta name="description" content="Find Pashto datasets for speech recognition, text-to-speech, NLP, OCR, and machine translation.">
  <style>
    :root {
      color-scheme: light;
      --ink: #14221f;
      --muted: #5c6f68;
      --line: #d8e3df;
      --paper: #ffffff;
      --paper-soft: #f7faf8;
      --surface: rgba(255, 255, 255, 0.9);
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

    body {
      margin: 0;
      min-height: 100vh;
      color: var(--ink);
      background:
        radial-gradient(circle at 16% 8%, rgba(47, 111, 159, 0.13), transparent 28rem),
        linear-gradient(180deg, #edf6f3 0%, #fbfcfa 44%, #f4f7f5 100%);
    }

    a { color: inherit; text-decoration: none; }

    .shell {
      width: min(1120px, calc(100% - 32px));
      margin: 0 auto;
      padding: 20px 0 48px;
    }

    .topbar {
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: 16px;
      padding: 12px 14px;
      border: 1px solid var(--line);
      border-radius: var(--radius);
      background: rgba(255, 255, 255, 0.82);
      box-shadow: 0 12px 28px rgba(33, 56, 50, 0.08);
      position: sticky;
      top: 12px;
      z-index: 10;
      backdrop-filter: blur(14px);
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
      margin-top: 2px;
      color: var(--muted);
      font-weight: 650;
    }

    .nav {
      display: flex;
      justify-content: flex-end;
      align-items: center;
      gap: 8px;
      flex-wrap: wrap;
    }

    .nav a,
    .button {
      min-height: 40px;
      display: inline-flex;
      align-items: center;
      justify-content: center;
      border: 1px solid var(--line);
      border-radius: 8px;
      background: white;
      color: var(--ink);
      font-weight: 750;
      padding: 0 14px;
      transition: transform 0.18s ease, border-color 0.18s ease;
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
      grid-template-columns: minmax(0, 1.1fr) minmax(280px, 0.9fr);
      gap: 18px;
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
      min-height: 390px;
      padding: clamp(24px, 5vw, 48px);
      display: flex;
      flex-direction: column;
      justify-content: space-between;
      background:
        linear-gradient(135deg, rgba(13, 61, 53, 0.96), rgba(47, 111, 159, 0.78)),
        url("https://images.unsplash.com/photo-1519389950473-47ba0277781c?auto=format&fit=crop&w=1400&q=78") center/cover;
      color: white;
      overflow: hidden;
      position: relative;
    }

    .hero-main::after {
      content: "";
      position: absolute;
      left: 0;
      right: 0;
      bottom: 0;
      height: 10px;
      background: linear-gradient(90deg, var(--blue), var(--accent), var(--brand-soft));
    }

    .eyebrow {
      display: inline-flex;
      width: max-content;
      border: 1px solid rgba(255, 255, 255, 0.24);
      border-radius: 999px;
      background: rgba(255, 255, 255, 0.12);
      padding: 7px 12px;
      font-size: 0.82rem;
      font-weight: 800;
      text-transform: uppercase;
    }

    h1 {
      margin: 22px 0 14px;
      max-width: 760px;
      font-size: clamp(2.1rem, 5.8vw, 4.6rem);
      line-height: 1;
      letter-spacing: 0;
    }

    .lede {
      max-width: 700px;
      margin: 0;
      color: rgba(255, 255, 255, 0.84);
      font-size: clamp(1rem, 2vw, 1.18rem);
      line-height: 1.65;
    }

    .actions {
      display: flex;
      gap: 10px;
      flex-wrap: wrap;
      margin-top: 24px;
    }

    .hero-main .button {
      border-color: rgba(255, 255, 255, 0.28);
      background: rgba(255, 255, 255, 0.13);
      color: white;
      backdrop-filter: blur(10px);
    }

    .hero-main .button.primary {
      background: white;
      border-color: white;
      color: var(--brand-dark);
    }

    .panel {
      padding: 22px;
      display: grid;
      gap: 14px;
      align-content: start;
    }

    .panel h2,
    .section h2,
    .card h3 {
      margin: 0;
    }

    .panel p,
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
      margin-bottom: 6px;
      color: var(--brand-dark);
      font-size: 2rem;
      line-height: 1;
    }

    .section {
      margin-top: 20px;
      padding: 26px;
      border: 1px solid var(--line);
      border-radius: var(--radius);
      background: rgba(255, 255, 255, 0.74);
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
      min-height: 176px;
      padding: 18px;
      display: flex;
      flex-direction: column;
      justify-content: space-between;
      background: var(--paper);
      box-shadow: 0 12px 30px rgba(30, 55, 49, 0.08);
    }

    .card h3 {
      margin-bottom: 8px;
      font-size: 1.05rem;
    }

    .card .button {
      width: max-content;
      margin-top: 18px;
    }

    .chip-row {
      display: flex;
      gap: 8px;
      flex-wrap: wrap;
      margin-top: 14px;
    }

    .chip {
      min-height: 30px;
      display: inline-flex;
      align-items: center;
      padding: 0 10px;
      border: 1px solid var(--line);
      border-radius: 999px;
      background: var(--paper-soft);
      color: var(--muted);
      font-size: 0.82rem;
      font-weight: 750;
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

      .hero,
      .grid {
        grid-template-columns: 1fr;
      }
    }

    @media (max-width: 560px) {
      .shell {
        width: min(100% - 20px, 1120px);
        padding-top: 10px;
      }

      .nav a,
      .button {
        width: 100%;
      }

      .hero-main,
      .panel,
      .section {
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
        <span>Pashto Resources<small>Dataset focus</small></span>
      </a>
      <div class="nav">
        <a href="search/">Search</a>
        <a href="papers/">Papers</a>
        <a href="pashto_asr.html">ASR</a>
        <a href="pashto_tts.html">TTS</a>
        <a href="https://github.com/musawer1214/pashto-language-resources">GitHub</a>
      </div>
    </nav>

    <section class="hero">
      <div class="hero-main">
        <div>
          <span class="eyebrow">Pashto dataset directory</span>
          <h1>Datasets for Pashto speech, text, OCR, and translation work.</h1>
          <p class="lede">Start from filtered catalog views, then open each original source to inspect licensing, download instructions, and dataset quality.</p>
          <div class="actions">
            <a class="button primary" href="search/?category=dataset">Browse all datasets</a>
            <a class="button" href="search/?category=dataset&mode=verified">Verified datasets</a>
          </div>
        </div>
      </div>

      <aside class="panel" aria-label="Dataset snapshot">
        <h2>Dataset Snapshot</h2>
        <p>The catalog keeps dataset entries grouped by task so you can avoid scanning unrelated papers and tools.</p>
        <div class="stat"><strong>49</strong><span>dataset entries in the catalog</span></div>
        <div class="stat"><strong>5</strong><span>common task filters: ASR, TTS, OCR, NLP, MT</span></div>
        <div class="stat"><strong>Daily</strong><span>automation checks for weak or dead resources</span></div>
      </aside>
    </section>

    <section class="section" aria-labelledby="dataset-paths">
      <div class="section-head">
        <div>
          <h2 id="dataset-paths">Dataset Paths</h2>
          <p>Use these entry points when you already know the kind of data you need.</p>
        </div>
      </div>

      <div class="grid">
        <article class="card">
          <div>
            <h3>Speech Recognition</h3>
            <p>Find speech corpora, audio-text pairs, and ASR evaluation resources.</p>
            <div class="chip-row">
              <span class="chip">ASR</span>
              <span class="chip">Speech</span>
            </div>
          </div>
          <a class="button primary" href="search/?category=dataset&task=asr">Open ASR datasets</a>
        </article>

        <article class="card">
          <div>
            <h3>Text to Speech</h3>
            <p>Find voice data and references useful for training or evaluating Pashto TTS systems.</p>
            <div class="chip-row">
              <span class="chip">TTS</span>
              <span class="chip">Voice</span>
            </div>
          </div>
          <a class="button primary" href="search/?category=dataset&task=tts">Open TTS datasets</a>
        </article>

        <article class="card">
          <div>
            <h3>Translation and Text</h3>
            <p>Find parallel corpora, text collections, dictionaries, and NLP datasets.</p>
            <div class="chip-row">
              <span class="chip">MT</span>
              <span class="chip">NLP</span>
            </div>
          </div>
          <a class="button primary" href="search/?category=dataset&task=mt">Open MT datasets</a>
        </article>

        <article class="card">
          <div>
            <h3>OCR and Documents</h3>
            <p>Find image, script, and document resources for Pashto OCR and text extraction.</p>
            <div class="chip-row">
              <span class="chip">OCR</span>
              <span class="chip">Documents</span>
            </div>
          </div>
          <a class="button" href="search/?category=dataset&task=ocr">Open OCR datasets</a>
        </article>

        <article class="card">
          <div>
            <h3>Raw Index</h3>
            <p>Open the repository dataset index when you need the Markdown source used by maintainers.</p>
            <div class="chip-row">
              <span class="chip">Repository</span>
              <span class="chip">Markdown</span>
            </div>
          </div>
          <a class="button" href="https://github.com/musawer1214/pashto-language-resources/blob/main/resources/datasets/README.md">Open dataset index</a>
        </article>

        <article class="card">
          <div>
            <h3>Add a Dataset</h3>
            <p>Use the contribution notes and catalog rules before adding a new resource.</p>
            <div class="chip-row">
              <span class="chip">Quality</span>
              <span class="chip">Metadata</span>
            </div>
          </div>
          <a class="button" href="https://github.com/musawer1214/pashto-language-resources/blob/main/README.md#contributing">Contribute</a>
        </article>
      </div>
    </section>

    <footer>
      Dataset links point to original sources whenever possible so licensing and access can be verified upstream.
    </footer>
  </main>
</body>
</html>
