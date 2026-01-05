from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from app.schemas.export_schemas import ExportRequest
import csv
import io
from typing import Dict, List

router = APIRouter()

@router.post("/generate-csv")
async def generate_csv(request: ExportRequest):
    """
    Génère un fichier CSV à partir des données utilisateur reçues
    """
    try:
        # Créer le contenu CSV en mémoire
        output = io.StringIO()

        # Définir les en-têtes avec les noms en français
        fieldnames = [
            "référence",
            "nom",
            "prénom",
            "email",
            "téléphone",
            "profession",
            "ville",
            "pays"
        ]

        writer = csv.DictWriter(
            output,
            fieldnames=fieldnames,
            delimiter=";",
            lineterminator="\n"
        )

        # Écrire l'en-tête
        writer.writeheader()

        # Écrire les données
        for user in request.data:
            row = {
                "référence": user.reference,
                "nom": user.last_name,
                "prénom": user.first_name,
                "email": user.email,
                "téléphone": user.phone,
                "profession": user.job,
                "ville": user.city,
                "pays": user.country
            }
            writer.writerow(row)

        # Récupérer le contenu CSV
        csv_content = output.getvalue()
        output.close()

        # Créer le stream de réponse
        csv_stream = io.StringIO(csv_content)

        return StreamingResponse(
            io.BytesIO(csv_content.encode('utf-8')),
            media_type="text/csv",
            headers={
                "Content-Disposition": "attachment; filename=export_users.csv"
            }
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur lors de la génération du CSV: {str(e)}")