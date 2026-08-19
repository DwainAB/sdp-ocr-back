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
        max_dosage_by_note: Optional[Dict[str, float]] = None,
    ) -> Dict[str, Dict[str, float]]:
        """
        Retourne {"top": {note: ml, ...}, "heart": {...}, "base": {...}}
        dont la somme vaut exactement total_volume_ml (arrondi à 0.1 ml).

        max_dosage_by_note : plafonds en ml par note (règles du dashboard, selon
        le coffret / la taille de flacon / l'intensité), à ne jamais dépasser.
        """
        normalized_intensity = normalize_intensity(intensity)
        max_dosage_by_note = max_dosage_by_note or {}

        try:
            result = self._ask_llm(
                top_notes, heart_notes, base_notes, normalized_intensity, total_volume_ml,
                max_dosage_by_note,
            )
            return self._validate_and_fix(
                result, top_notes, heart_notes, base_notes, total_volume_ml, max_dosage_by_note,
            )
        except Exception as e:
            logger.warning(f"[PerfumerService] Échec de l'appel IA, fallback déterministe : {e}")
            return self._fallback_split(
                top_notes, heart_notes, base_notes, normalized_intensity, total_volume_ml,
                max_dosage_by_note,
            )

    # ── Appel LLM ──

    def _ask_llm(
        self,
        top_notes: List[str],
        heart_notes: List[str],
        base_notes: List[str],
        intensity: str,
        total_volume_ml: float,
        max_dosage_by_note: Dict[str, float],
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

        prompt = self._build_prompt(
            top_notes, heart_notes, base_notes, intensity, total_volume_ml, max_dosage_by_note,
        )

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
        max_dosage_by_note: Dict[str, float],
    ) -> str:
        concentration = _CONCENTRATION_BY_INTENSITY[intensity]

        max_dosage_section = ""
        applicable_caps = {
            note: cap
            for note, cap in max_dosage_by_note.items()
            if note in top_notes or note in heart_notes or note in base_notes
        }
        if applicable_caps:
            caps_lines = "\n".join(
                f"- {note} : maximum {cap} ml (règle de sécurité/dosage imposée, à respecter strictement)"
                for note, cap in applicable_caps.items()
            )
            max_dosage_section = f"""

Contraintes de dosage maximum à respecter IMPÉRATIVEMENT (ne jamais dépasser, même
si cela réduit le volume total de notes en-dessous de la cible d'intensité) :
{caps_lines}"""

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
  name = nom exact de la note, quantity_ml = quantité en ml).{max_dosage_section}

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
        max_dosage_by_note: Dict[str, float],
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

        # Garde-fou dur : l'IA doit déjà respecter les plafonds via le prompt,
        # mais on les fait respecter ici aussi au cas où elle les ignorerait.
        for family_notes in fixed.values():
            for note, cap in max_dosage_by_note.items():
                if note in family_notes and family_notes[note] > cap:
                    family_notes[note] = round(cap, 1)

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
        max_dosage_by_note: Dict[str, float],
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
            result[family] = self._split_with_caps(notes, per_note, max_dosage_by_note)

        return result

    @staticmethod
    def _split_with_caps(
        notes: List[str], even_share: float, max_dosage_by_note: Dict[str, float]
    ) -> Dict[str, float]:
        """
        Répartit équitablement even_share ml entre `notes`, plafonne celles ayant
        une règle de dosage max, et redistribue le surplus ainsi libéré entre les
        notes restantes (sans jamais dépasser leur propre plafond).
        """
        remaining_notes = list(notes)
        allocated: Dict[str, float] = {}
        pending_volume = even_share * len(notes)

        # Boucle car plafonner une note peut faire baisser le partage équitable
        # des autres en-dessous de leur propre plafond, ou l'inverse.
        while remaining_notes:
            share = pending_volume / len(remaining_notes)
            capped = [n for n in remaining_notes if n in max_dosage_by_note and max_dosage_by_note[n] < share]
            if not capped:
                for note in remaining_notes:
                    allocated[note] = share
                break
            for note in capped:
                allocated[note] = max_dosage_by_note[note]
                pending_volume -= max_dosage_by_note[note]
            remaining_notes = [n for n in remaining_notes if n not in capped]
            if not remaining_notes:
                break

        return {note: round(allocated[note], 1) for note in notes}


perfumer_service = PerfumerService()
