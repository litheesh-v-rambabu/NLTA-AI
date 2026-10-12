# NLTA: Multilingual Browser Extension for Real-Time Translation

A Chrome extension that translates the text you are looking at on any web page, using a **self-hosted** translation model instead of a paid API. The extension collects the visible text, sends it to a small Python backend, and writes the translation back into the page. The original text is kept so you can restore it with one click.

> **Status: work in progress.** The backend and the core extension flow work locally. Auto-translate on scroll, a better language detector, an accessibility "Listen" feature, deployment and Chrome Web Store packaging are still to do. See [Roadmap](#roadmap) and [Known limitations](#known-limitations).

## Features

- **Translate the visible part of a page.** Text on screen, plus one screen above and below, is translated in rounds of 50 pieces.
- **Restore original** puts the page back without a refresh.
- **Self-hosted translation** with Meta's NLLB-200 (distilled, 600M parameters). No per-character fees, and page text is not sent to a third-party translation service.
- **Language detection** per batch, so you only choose the target language.
- **Batch endpoint with a cache.** Repeated strings are answered from an in-memory TTL + LRU cache, and duplicates inside one batch are translated once.
- **Safe by default.** The extension skips scripts, styles, code blocks, text inputs, text areas and editable content, so it never rewrites what you are typing.
- **Tested backend.** 17 automated tests cover the API and the cache.

Languages currently supported: English, French, Spanish, German, Hindi, Arabic, Chinese (Simplified) and Japanese. The live list is available from `GET /languages`.

## How it works

```
 Web page ──(visible text nodes)──► content.js ──► popup.js ──HTTP──► FastAPI backend
                                                                       ├─ language detection
                                                                       ├─ TTL + LRU cache
                                                                       └─ NLLB-200 (600M)
 Web page ◄──(translations; originals kept for Restore)───────────────┘
```

1. `content.js` walks the page's text nodes and keeps the ones that are visible and near the viewport.
2. `popup.js` sends up to 50 texts per request to `POST /translate/batch`.
3. The backend detects the source language once per batch, checks the cache, translates only the texts it has not seen, and returns the results in the same order.
4. The extension writes each translation into its original text node and remembers the original text.

## Tech stack

| Part | Technology |
|---|---|
| Extension | Chrome Extension, Manifest V3, plain JavaScript |
| Backend | Python, FastAPI, Uvicorn, Pydantic |
| Translation | [`facebook/nllb-200-distilled-600M`](https://huggingface.co/facebook/nllb-200-distilled-600M) via Hugging Face Transformers and PyTorch |
| Detection | `langdetect` (an XLM-RoBERTa detector is planned behind the same function) |
| Tests | pytest with FastAPI's `TestClient` |

## Project structure

```
NLTA-AI/
├── README.md
├── backend/
│   ├── app/
│   │   ├── main.py          # FastAPI app and endpoints
│   │   ├── detector.py      # language detection
│   │   ├── translator.py    # NLLB model wrapper (lazy loading, batching)
│   │   ├── cache.py         # TTL + LRU cache
│   │   └── language_map.py  # supported languages and NLLB codes
│   └── tests/
│       ├── test_basic.py
│       └── test_cache.py
└── extension/
    ├── manifest.json
    ├── content.js           # finds and remembers the page's text nodes
    └── popup/
        ├── popup.html
        └── popup.js         # UI, calls the backend, writes translations back
```

## Getting started

You need Python 3.12 or newer and Google Chrome.

### 1. Run the backend

```bash
git clone https://github.com/<your-username>/NLTA-AI.git
cd NLTA-AI
python3 -m venv .venv
source .venv/bin/activate
pip install fastapi "uvicorn[standard]" pydantic langdetect transformers torch sentencepiece pytest httpx

cd backend
uvicorn app.main:app --reload
```

The server listens on `http://localhost:8000`. Interactive API docs are at `http://localhost:8000/docs`.

The **first translation downloads the NLLB model** (roughly 2.5 GB) and loads it into memory, so it is slow. Later requests are much faster, and repeated texts come from the cache.

### 2. Run the tests

From the `backend` folder:

```bash
python -m pytest -v
```

### 3. Load the extension

1. Open `chrome://extensions`.
2. Turn on **Developer mode**.
3. Click **Load unpacked** and choose the `extension` folder (the one that contains `manifest.json`).
4. After any change to the extension's files, click the reload arrow on its card and refresh the page you are testing.

### 4. Use it

1. Keep the backend running.
2. Open a normal web page, for example a French Wikipedia article.
3. Click the extension icon, choose a target language and click **Translate this page**. Keep the popup open until it finishes.
4. Click **Restore original** to undo.

Chrome does not allow extensions on pages such as `chrome://` or the Chrome Web Store, so use an ordinary website.

## API

| Method | Path | Purpose |
|---|---|---|
| `GET` | `/health` | Server status |
| `GET` | `/languages` | Supported languages |
| `POST` | `/detect` | Detect the language of a text |
| `POST` | `/translate` | Translate one text |
| `POST` | `/translate/batch` | Translate 1 to 50 texts, cache-aware |

Example:

```bash
curl -X POST http://localhost:8000/translate/batch \
  -H "Content-Type: application/json" \
  -d '{"texts": ["Bonjour tout le monde", "Comment allez-vous ?"], "target_lang": "en"}'
```

```json
{
  "translations": ["Hello everyone", "How are you?"],
  "source_lang": "fr",
  "target_lang": "en"
}
```

Invalid requests (empty text, more than 50 texts, an unsupported language) are rejected with a 4xx error.

## Known limitations

- **Licence of the model.** NLLB-200 weights are released under **CC-BY-NC 4.0**, which is non-commercial. Check this before publishing a commercial product or a paid extension, and consider an alternative model with a permissive licence.
- **Short strings translate poorly.** Single words and short UI labels have little context. For example "Article" or "Petite" can come back as something unrelated. Full sentences are much better. Handling short strings separately is planned.
- **Slow first request.** The model loads on the first call, and CPU inference is slow for large pages.
- **The popup must stay open.** Translation currently runs from the popup, which closes when you click away. A background service worker will replace this.
- **Local only.** The extension talks to `http://localhost:8000`. There is no authentication, CORS is open, and there is no hosted backend yet.
- **No right-to-left layout handling yet.** Translating into Arabic works, but the page direction is not adjusted.
- **Changing the target language** requires pressing **Restore original** first, because translated text is not re-translated from the original.

## Privacy

Text from the page is sent only to **your own backend**. It is not sent to any third-party translation service. The model files are downloaded once from Hugging Face. Text inputs, text areas and editable content are never read or changed.

## Roadmap

- [x] FastAPI backend: health, languages, detect, translate, batch
- [x] NLLB-200 translation with lazy loading and batching
- [x] TTL + LRU cache with deduplication inside a batch
- [x] Automated tests (17)
- [x] Chrome extension (Manifest V3) that finds visible text and talks to the backend
- [x] Translate visible text in rounds and restore the original
- [ ] Background service worker, translate as you scroll, and handle dynamic pages (`MutationObserver`)
- [ ] XLM-RoBERTa language detector behind the existing `detect_language` function
- [ ] Right-to-left support (`dir` and `lang` on translated text)
- [ ] **Listen** feature for blind and low-vision users: read translated text aloud with the Web Speech API, correct `lang` attributes, screen-reader-friendly live regions, keyboard shortcuts, and speed and voice controls
- [ ] Skip sensitive pages and fields by default
- [ ] Measure detection accuracy, translation quality and latency
- [ ] Lock down CORS, add authentication, and deploy the backend
- [ ] Chrome Web Store packaging and privacy policy

## Acknowledgements

- [NLLB Team, Meta AI](https://github.com/facebookresearch/fairseq/tree/nllb): *No Language Left Behind* (2022)
- [Hugging Face Transformers](https://github.com/huggingface/transformers)
- [FastAPI](https://fastapi.tiangolo.com/)
- [`langdetect`](https://github.com/Mimino666/langdetect)

## License

No licence has been chosen for this repository yet. Add a `LICENSE` file before sharing it publicly. The NLLB model weights are covered by their own licence (CC-BY-NC 4.0), as described above.
