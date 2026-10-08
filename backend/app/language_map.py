from dataclasses import dataclass


@dataclass(frozen=True)
class Language:
    code: str
    nllb_code: str
    name: str


LANGUAGES = [
    Language("en", "eng_Latn", "English"),
    Language("fr", "fra_Latn", "French"),
    Language("es", "spa_Latn", "Spanish"),
    Language("de", "deu_Latn", "German"),
    Language("hi", "hin_Deva", "Hindi"),
    Language("ar", "arb_Arab", "Arabic"),
    Language("zh", "zho_Hans", "Chinese (Simplified)"),
    Language("ja", "jpn_Jpan", "Japanese"),
]