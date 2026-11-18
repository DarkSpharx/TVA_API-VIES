"""Script de collecte automatisée de l'API VIES.
Meridian Distribution | Phase 3
"""

import time
import logging
from datetime import datetime
from pathlib import Path
import pandas as pd
import requests

# 1. Configuration des logs
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler("doc/journal_collecte.log", encoding="utf-8"),
        logging.StreamHandler()
    ]
)

def interroger_vies(numero_normalise):
    """Interroge l'API VIES pour un numéro normalisé (ex: FR27552032534)."""
    pays = numero_normalise[:2]
    numero = numero_normalise[2:]
    url = f"https://ec.europa.eu/taxation_customs/vies/rest-api/ms/{pays}/vat/{numero}"
    
    debut = time.perf_counter()
    try:
        reponse = requests.get(url, timeout=30)
        temps = time.perf_counter() - debut
        reponse.raise_for_status()
        donnees = reponse.json()
        return {
            "isValid": donnees.get("isValid"),
            "userError": donnees.get("userError"),
            "name": donnees.get("name"),
            "address": donnees.get("address"),
            "temps_reponse_s": temps,
            "statut_http": reponse.status_code,
            "erreur": None
        }
    except Exception as e:
        temps = time.perf_counter() - debut
        logging.error(f"Erreur pour {numero_normalise} : {e}")
        return {
            "isValid": None,
            "userError": None,
            "name": None,
            "address": None,
            "temps_reponse_s": temps,
            "statut_http": getattr(e.response, "status_code", None),
            "erreur": str(e)
        }

def lancer_collecte(limite_echantillon=None, pause_s=2):
    """Lance la campagne d'appels avec mode échantillon, reprise et temporisation."""
    data_dir = Path("data")
    resultats_path = data_dir / "resultats_vies.csv"
    source_path = data_dir / "numeros_tva_nettoyes.csv" 
    
    if not source_path.exists():
        logging.error("Fichier source nettoyé introuvable. Exécutez le notebook de nettoyage d'abord.")
        return

    df = pd.read_csv(source_path, dtype=str, keep_default_na=False)
    
    if limite_echantillon:
        df = df.head(limite_echantillon)
        logging.info(f"Mode échantillon activé : {limite_echantillon} lignes.")

    deja_faits = set()
    if resultats_path.exists():
        df_res = pd.read_csv(resultats_path, dtype=str)
        if "numero_tva" in df_res.columns:
            deja_faits = set(df_res["numero_tva"].dropna())
            logging.info(f"Reprise : {len(deja_faits)} numéros déjà traités ignorés.")

    resultats = []
    
    for idx, row in df.iterrows():
        # Le fichier nettoyé contient directement les numéros au format attendu (colonne 'numero_tva' ou 'tva_normalisee')
        num = row.get("numero_tva", "").strip()
        if not num:
            num = row.get("tva_normalisee", "").strip()
        
        if not num or num in deja_faits:
            continue
            
        logging.info(f"Interrogation de {num}...")
        res = interroger_vies(num)
        
        resultats.append({
            "date_appel": datetime.now().isoformat(),
            "numero_tva": num,
            "isValid": res["isValid"],
            "userError": res["userError"],
            "temps_reponse_s": res["temps_reponse_s"],
            "statut_http": res["statut_http"],
            "erreur": res["erreur"]
        })
        
        time.sleep(pause_s)

    if resultats:
        df_nouveaux = pd.DataFrame(resultats)
        if resultats_path.exists():
            df_nouveaux.to_csv(resultats_path, mode="a", header=False, index=False)
        else:
            df_nouveaux.to_csv(resultats_path, index=False)
        logging.info(f"Sauvegarde de {len(resultats)} nouveaux résultats dans {resultats_path}")

if __name__ == "__main__":
    lancer_collecte(limite_echantillon=200, pause_s=2)

