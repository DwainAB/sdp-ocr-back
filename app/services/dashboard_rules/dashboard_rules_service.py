import time
from typing import Dict, List, Optional

import requests

from app.core.config import settings
from app.core.logger import get_logger

logger = get_logger(__name__)

# Durée de vie du cache en mémoire (secondes) pour /api/ingredients et
# /api/ingredient-rules : évite un aller-retour réseau vers le dashboard à
# chaque suggestion de quantités côté tablette.
_CACHE_TTL_SECONDS = 300


class DashboardRulesService:
    """
    Récupère depuis le dashboard SDP (API Railway) les règles de dosage max
    par ingrédient, filtrées selon le coffret / la taille de flacon / l'intensité
    choisis par le client, pour les faire respecter par le dosage IA.
    """

    def __init__(self):
        self._ingredients_cache: Optional[Dict[int, str]] = None
        self._ingredients_cache_at: float = 0.0
        self._rules_cache: Optional[List[dict]] = None
        self._rules_cache_at: float = 0.0

    # ── Ingrédients (id -> nom) ──

    def _fetch_ingredients(self) -> Dict[int, str]:
        now = time.time()
        if self._ingredients_cache is not None and (now - self._ingredients_cache_at) < _CACHE_TTL_SECONDS:
            return self._ingredients_cache

        try:
            response = requests.get(
                f"{settings.DASHBOARD_API_URL}/api/ingredients",
                params={"active_only": "true"},
                timeout=5,
            )
            response.raise_for_status()
            ingredients = response.json()

            name_by_id: Dict[int, str] = {}
            for ingredient in ingredients:
                translations = ingredient.get("translations") or {}
                name = translations.get("fr") or translations.get("en") or ingredient.get("name")
                if name:
                    name_by_id[ingredient["id"]] = name

            self._ingredients_cache = name_by_id
            self._ingredients_cache_at = now
            return name_by_id
        except Exception as e:
            logger.warning(f"[DashboardRulesService] Échec récupération /api/ingredients : {e}")
            # On garde le cache précédent (même expiré) plutôt que de tout perdre.
            return self._ingredients_cache or {}

    # ── Règles de dosage max ──

    def _fetch_max_dosage_rules(self) -> List[dict]:
        now = time.time()
        if self._rules_cache is not None and (now - self._rules_cache_at) < _CACHE_TTL_SECONDS:
            return self._rules_cache

        try:
            response = requests.get(
                f"{settings.DASHBOARD_API_URL}/api/ingredient-rules",
                params={"rule_type": "max_dosage", "active_only": "true"},
                timeout=5,
            )
            response.raise_for_status()
            rules = response.json()

            self._rules_cache = rules
            self._rules_cache_at = now
            return rules
        except Exception as e:
            logger.warning(f"[DashboardRulesService] Échec récupération /api/ingredient-rules : {e}")
            return self._rules_cache or []

    def get_max_dosage_by_note_name(
        self,
        box_set: Optional[str],
        bottle_size: Optional[str],
        intensity: Optional[str] = None,
    ) -> Dict[str, float]:
        """
        Retourne {note_name: max_ml} pour les règles de type max_dosage applicables
        au coffret / à la taille de flacon (et intensité si précisée) donnés.

        Une règle sans box_set/bottle_size/intensity renseigné (None) s'applique à
        tous ; une règle avec intensity = "toutes" s'applique à toutes les intensités.
        Si plusieurs règles concernent la même note, la plus restrictive (max_ml le
        plus petit) est retenue.
        """
        name_by_id = self._fetch_ingredients()
        rules = self._fetch_max_dosage_rules()

        max_by_note: Dict[str, float] = {}
        for rule in rules:
            if not rule.get("is_active", True):
                continue
            if rule.get("max_ml") is None:
                continue

            rule_box_set = rule.get("box_set")
            if rule_box_set and box_set and rule_box_set != box_set:
                continue

            rule_bottle_sizes = rule.get("bottle_sizes") or []
            if rule_bottle_sizes and bottle_size and bottle_size not in rule_bottle_sizes:
                continue

            rule_intensity = rule.get("intensity")
            if (
                rule_intensity
                and rule_intensity != "toutes"
                and intensity
                and rule_intensity != intensity
            ):
                continue

            max_ml = float(rule["max_ml"])
            for ingredient_id in rule.get("target_ingredient_ids") or []:
                note_name = name_by_id.get(ingredient_id)
                if not note_name:
                    continue
                if note_name not in max_by_note or max_ml < max_by_note[note_name]:
                    max_by_note[note_name] = max_ml

        return max_by_note


dashboard_rules_service = DashboardRulesService()
