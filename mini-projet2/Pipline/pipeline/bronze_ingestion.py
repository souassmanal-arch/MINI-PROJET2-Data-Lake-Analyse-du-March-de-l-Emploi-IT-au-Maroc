import json
import os
from datetime import datetime
from pathlib import Path
from pipeline.utils import get_logger, DATA_LAKE_ROOT

logger = get_logger("bronze_ingestion")

def ingerer_bronze(filepath_source: str, data_lake_root: str = DATA_LAKE_ROOT) -> dict:
    """
    Charge les données brutes dans la zone Bronze sans aucune modification.
    Partitionne par source et par mois de publication.

    Principe fondamental : la zone Bronze est IMMUABLE.
    On ne modifie JAMAIS les données une fois chargées en Bronze.
    C'est l'archive fidèle de ce qui a été reçu.
    """
    logger.info(f"Début de l'ingestion Bronze pour le fichier : {filepath_source}")
    
    if not os.path.exists(filepath_source):
        logger.error(f"Fichier source introuvable : {filepath_source}")
        raise FileNotFoundError(f"Source file {filepath_source} not found.")

    with open(filepath_source, 'r', encoding='utf-8') as f:
        data = json.load(f)

    offres = data.get('offres', [])
    stats = {'total': len(offres), 'par_source': {}, 'par_mois': {}}

    # Partitionnement par source et par mois
    partitions = {}
    for offre in offres:
        source = offre.get('source', 'inconnu').lower().replace(' ', '_')
        date_pub = offre.get('date_publication', '')

        try:
            mois_partition = datetime.strptime(date_pub[:7], '%Y-%m').strftime('%Y_%m')
        except (ValueError, TypeError):
            mois_partition = 'date_inconnue'

        cle = f"{source}/{mois_partition}"
        if cle not in partitions:
            partitions[cle] = []
        partitions[cle].append(offre)

    # Écriture dans Bronze
    nb_fichiers = 0
    for partition, offres_partition in partitions.items():
        chemin_dir = os.path.join(data_lake_root, 'bronze', partition)
        os.makedirs(chemin_dir, exist_ok=True)

        chemin_fichier = os.path.join(chemin_dir, 'offres_raw.json')
        with open(chemin_fichier, 'w', encoding='utf-8') as f:
            json.dump({
                'metadata': {
                    'source_fichier': filepath_source,
                    'date_ingestion': datetime.now().isoformat(),
                    'partition': partition,
                    'nb_offres': len(offres_partition)
                },
                'offres': offres_partition
            }, f, ensure_ascii=False, indent=2)

        nb_fichiers += 1
        source_nom = partition.split('/')[0]
        stats['par_source'][source_nom] = stats['par_source'].get(source_nom, 0) + len(offres_partition)
        
        mois_nom = partition.split('/')[1]
        stats['par_mois'][mois_nom] = stats['par_mois'].get(mois_nom, 0) + len(offres_partition)

    logger.info(f"[BRONZE] {stats['total']} offres ingérées dans {nb_fichiers} partitions.")
    return stats
