from app.language_map import LANGUAGES

_NLLB_CODES = {lang.code: lang.nllb_code for lang in LANGUAGES}


class Translator:
    MODEL_NAME = "facebook/nllb-200-distilled-600M"

    def __init__(self):
        self._tokenizer = None
        self._model = None

    def _load(self):
        # Imported and loaded on first use, so importing this file never downloads anything.
        if self._model is None:
            from transformers import AutoModelForSeq2SeqLM, AutoTokenizer

            self._tokenizer = AutoTokenizer.from_pretrained(self.MODEL_NAME)
            self._model = AutoModelForSeq2SeqLM.from_pretrained(self.MODEL_NAME)

    def translate_batch(self, texts: list[str], source: str, target: str) -> list[str]:
        self._load()
        self._tokenizer.src_lang = _NLLB_CODES[source]
        inputs = self._tokenizer(
            texts, return_tensors="pt", padding=True, truncation=True, max_length=256
        )
        output = self._model.generate(
            **inputs,
            forced_bos_token_id=self._tokenizer.convert_tokens_to_ids(_NLLB_CODES[target]),
            max_length=256,
        )
        return self._tokenizer.batch_decode(output, skip_special_tokens=True)

    def translate(self, text: str, source: str, target: str) -> str:
        return self.translate_batch([text], source, target)[0]