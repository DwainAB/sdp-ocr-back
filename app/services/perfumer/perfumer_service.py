import json
import unicodedata
from typing import Dict, List, Optional

from openai import OpenAI

from app.core.config import settings
from app.core.logger import get_logger

logger = get_logger(__name__)

# Répartition indicative tête/cœur/fond selon la famille olfactive classique,
# utilisée comme garde-fou dans le prompt et comme filet de sécurité si l'IA
# est indisponible ou renvoie une réponse invalide.
_BASE_SPLIT = {"top": 0.25, "heart": 0.35, "base": 0.40}

# Pourcentage du volume total effectivement composé de notes parfumantes,
# le reste étant l'alcool/support. Ajusté selon l'intensité souhaitée.
_CONCENTRATION_BY_INTENSITY = {
    "light": 0.12,
    "moderate": 0.18,
    "strong": 0.25,
}

_INTENSITY_ALIASES = {
    # léger
    "leger": "light", "light": "light", "ligero": "light", "leve": "light",
    # modéré
    "modere": "moderate", "moderate": "moderate", "moderado": "moderate",
    # fort
    "fort": "strong", "strong": "strong", "fuerte": "strong", "forte": "strong",
}


def _strip_accents(value: str) -> str:
    normalized = unicodedata.normalize("NFKD", value)
    return "".join(c for c in normalized if not unicodedata.combining(c))


def normalize_intensity(raw: Optional[str]) -> str:
    """Normalise un libellé d'intensité (FR/EN/ES/PT, libellé ou code) vers light/moderate/strong."""
    if not raw:
        return "moderate"
    key = _strip_accents(raw.strip().lower())
    return _INTENSITY_ALIASES.get(key, "moderate")


class PerfumerService:
    """
    Calcule la répartition en ml de chaque note olfactive choisie par le client,
    à partir de l'intensité souhaitée et du volume total du flacon, via un LLM.
    """

    def __init__(self):
        self._client: Optional[OpenAI] = None

    @property
    def client(self) -> OpenAI:
        if not settings.OPENAI_API_KEY:
            raise ValueError("OPENAI_API_KEY environment variable is required")
        if self._client is None:
            self._client = OpenAI(api_key=settings.OPENAI_API_KEY)
        return self._client

    def suggest_quantities(
        self,
        top_notes: List[str],
        heart_notes: List[str],
        base_notes: List[str],
        intensity: str,
        total_volume_ml: float,
    ) -> Dict[str, Dict[str, float]]:
        """
        Retourne {"top": {note: ml, ...}, "heart": {...}, "base": {...}}
        dont la somme vaut exactement total_volume_ml (arrondi à 0.1 ml).
        """
        normalized_intensity = normalize_intensity(intensity)

        try:
            result = self._ask_llm(
                top_notes, heart_notes, base_notes, normalized_intensity, total_volume_ml
            )
            return self._validate_and_fix(
                result, top_notes, heart_notes, base_notes, total_volume_ml
            )
        except Exception as e:
            logger.warning(f"[PerfumerService] Échec de l'appel IA, fallback déterministe : {e}")
            return self._fallback_split(
                top_notes, heart_notes, base_notes, normalized_intensity, total_volume_ml
            )

    # ── Appel LLM ──

    def _ask_llm(
        self,
        top_notes: List[str],
        heart_notes: List[str],
        base_notes: List[str],
        intensity: str,
        total_volume_ml: float,
    ) -> dict:
        # Le mode "strict" d'OpenAI n'autorise pas les objets à clés dynamiques
        # (additionalProperties) : chaque "properties" doit lister exhaustivement
        # ses clés dans "required". On utilise donc une liste plate d'objets
        # {family, name, quantity_ml} plutôt qu'un dict par note.
        schema = {
            "type": "object",
            "properties": {
                "notes": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "family": {"type": "string", "enum": ["top", "heart", "base"]},
                            "name": {"type": "string"},
                            "quantity_ml": {"type": "number"},
                        },
                        "required": ["family", "name", "quantity_ml"],
                        "additionalProperties": False,
                    },
                },
            },
            "required": ["notes"],
            "additionalProperties": False,
        }

        prompt = self._build_prompt(top_notes, heart_notes, base_notes, intensity, total_volume_ml)

        response = self.client.chat.completions.create(
            model=settings.OPENAI_MODEL,
            messages=[
                {
                    "role": "system",
                    "content": (
                        "Tu es un parfumeur expert (nez professionnel) qui dose des formules de parfum. "
                        "Tu réponds uniquement avec un JSON respectant strictement le schéma fourni, "
                        "sans texte additionnel."
                    ),
                },
                {"role": "user", "content": prompt},
            ],
            response_format={
                "type": "json_schema",
                "json_schema": {"name": "note_quantities", "schema": schema, "strict": True},
            },
            temperature=0.3,
        )

        content = response.choices[0].message.content
        return json.loads(content)

    def _build_prompt(
        self,
        top_notes: List[str],
        heart_notes: List[str],
        base_notes: List[str],
        intensity: str,
        total_volume_ml: float,
    ) -> str:
        concentration = _CONCENTRATION_BY_INTENSITY[intensity]
        return f"""
Compose le dosage d'un parfum sur-mesure pour un flacon de {total_volume_ml} ml.

Notes de tête choisies : {", ".join(top_notes) or "aucune"}
Notes de cœur choisies : {", ".join(heart_notes) or "aucune"}
Notes de fond choisies : {", ".join(base_notes) or "aucune"}

Intensité souhaitée par le client : {intensity} (light = parfum léger peu concentré,
moderate = équilibré, strong = parfum riche et concentré).

Règles de dosage à respecter :
- Le volume total des notes parfumantes (tête + cœur + fond) doit représenter environ
  {round(concentration * 100)}% du volume du flacon ({total_volume_ml} ml), le reste étant l'alcool/support
  (tu n'as pas besoin de renvoyer l'alcool, seulement les notes).
- Répartis ce volume de notes entre les 3 familles en respectant approximativement :
  tête ~25%, cœur ~35%, fond ~40% du volume de notes (ajustable légèrement selon le nombre
  de notes dans chaque famille et leur nature).
- À l'intérieur de chaque famille, répartis équitablement entre les notes choisies, en tenant
  compte de leur puissance olfactive typique (une note très puissante comme le musc, le patchouli,
  l'oud ou la vanille doit recevoir une part plus faible qu'une note légère comme les agrumes ou le thé vert).
- Chaque quantité doit être un nombre positif en ml, arrondi à 0.1 ml.
- N'inclus dans le JSON qu'une entrée par note listée ci-dessus (family = "top"/"heart"/"base",
  name = nom exact de la note, quantity_ml = quantité en ml).

Réponds uniquement avec le JSON du schéma demandé.
""".strip()

    # ── Validation / garde-fou ──

    def _validate_and_fix(
        self,
        result: dict,
        top_notes: List[str],
        heart_notes: List[str],
        base_notes: List[str],
        total_volume_ml: float,
    ) -> Dict[str, Dict[str, float]]:
        expected = {"top": top_notes, "heart": heart_notes, "base": base_notes}
        fixed: Dict[str, Dict[str, float]] = {"top": {}, "heart": {}, "base": {}}

        # La réponse LLM est une liste plate [{family, name, quantity_ml}, ...]
        by_family: Dict[str, Dict[str, float]] = {"top": {}, "heart": {}, "base": {}}
        for entry in result.get("notes") or []:
            family = entry.get("family")
            name = entry.get("name")
            if family in by_family and isinstance(name, str):
                by_family[family][name] = entry.get("quantity_ml")

        for family, notes in expected.items():
            family_values = by_family[family]
            for note in notes:
                value = family_values.get(note)
                if not isinstance(value, (int, float)) or value <= 0:
                    raise ValueError(f"Quantité manquante ou invalide pour '{note}' ({family})")
                fixed[family][note] = round(float(value), 1)

        total = sum(v for family in fixed.values() for v in family.values())
        if total <= 0:
            raise ValueError("Somme des quantités nulle")
        if total > total_volume_ml:
            raise ValueError(
                f"Somme des quantités ({total} ml) dépasse le volume du flacon ({total_volume_ml} ml)"
            )

        return fixed

    # ── Fallback déterministe (pas d'IA disponible / réponse invalide) ──

    def _fallback_split(
        self,
        top_notes: List[str],
        heart_notes: List[str],
        base_notes: List[str],
        intensity: str,
        total_volume_ml: float,
    ) -> Dict[str, Dict[str, float]]:
        concentration = _CONCENTRATION_BY_INTENSITY[intensity]
        notes_volume = total_volume_ml * concentration

        families = {"top": top_notes, "heart": heart_notes, "base": base_notes}
        active_weights = {k: w for k, w in _BASE_SPLIT.items() if families[k]}
        weight_sum = sum(active_weights.values()) or 1.0

        result: Dict[str, Dict[str, float]] = {"top": {}, "heart": {}, "base": {}}
        for family, notes in families.items():
            if not notes:
                continue
            family_volume = notes_volume * (active_weights.get(family, 0) / weight_sum)
            per_note = family_volume / len(notes)
            result[family] = {note: round(per_note, 1) for note in notes}

        return result


perfumer_service = PerfumerService()
