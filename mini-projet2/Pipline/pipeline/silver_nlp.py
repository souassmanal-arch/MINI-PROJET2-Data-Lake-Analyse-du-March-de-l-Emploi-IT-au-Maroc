import json
import re
from pathlib import Path
import pandas as pd
from pipeline.utils import get_logger, DATA_LAKE_ROOT, REFERENTIAL_PATH

logger = get_logger("silver_nlp")

def extraire_competences(df: pd.DataFrame, referentiel_path: str = REFERENTIAL_PATH) -> pd.DataFrame:
    """
    Extrait les compétences IT depuis deux sources :
      1. Le champ 'competences_brut' (liste semi-structurée)
      2. Le champ 'description' (texte libre — plus riche mais plus bruité)

    Stratégie : matching sur le référentiel de compétences normalisé.
    Chaque offre produit une ligne par compétence détectée.
    """
    logger.info("Démarrage de l'extraction des compétences (NLP/Regex)...")
    
    if not Path(referentiel_path).exists():
        logger.error(f"Référentiel de compétences introuvable : {referentiel_path}")
        raise FileNotFoundError(f"Skills referential not found at {referentiel_path}")

    with open(referentiel_path, 'r', encoding='utf-8') as f:
        referentiel = json.load(f)

    # Construire un dictionnaire plat : alias → nom_normalise, famille
    dict_competences = {}
    for famille, competences in referentiel['familles'].items():
        for nom_normalise, aliases in competences.items():
            for alias in aliases:
                dict_competences[alias.lower()] = {
                    'competence': nom_normalise,
                    'famille': famille
                }

    # Trier par longueur décroissante pour éviter les faux positifs
    # (ex: "node" ne doit pas matcher avant "node.js")
    aliases_tries = sorted(dict_competences.keys(), key=len, reverse=True)

    resultats = []

    for idx, offre in df.iterrows():
        # Concaténer les deux sources de texte
        texte_complet = ' '.join(filter(None, [
            str(offre.get('competences_brut', '') or ''),
            str(offre.get('description', '') or '')
        ])).lower()

        # Remplacer les caractères de séparation par des espaces pour faciliter le matching de mots entiers
        texte_complet = re.sub(r'[\/\n•,\-]', ' ', texte_complet)

        competences_trouvees = set()

        for alias in aliases_tries:
            # Recherche en tant que mot entier (word boundary)
            # Pour gérer les alias spéciaux comme c# ou .net, on adapte la regex
            if '+' in alias or '#' in alias or '.' in alias:
                # Regex sans word boundary standard pour les symboles
                pattern = r'(?:^|\s)' + re.escape(alias) + r'(?:\s|$|,|\.)'
            else:
                pattern = r'\b' + re.escape(alias) + r'\b'
                
            if re.search(pattern, texte_complet):
                info = dict_competences[alias]
                cle = info['competence']
                if cle not in competences_trouvees:
                    competences_trouvees.add(cle)
                    resultats.append({
                        'id_offre':      offre['id_offre'],
                        'profil':        offre.get('profil_normalise'),
                        'ville':         offre.get('ville_std'),
                        'competence':    info['competence'],
                        'famille':       info['famille'],
                        'date_pub':      offre.get('date_publication'),
                        'annee':         str(offre.get('annee')),
                        'mois':          str(offre.get('mois')),
                    })

        # Offre sans compétence détectée : tracer
        if not competences_trouvees:
            resultats.append({
                'id_offre':      offre['id_offre'],
                'profil':        offre.get('profil_normalise'),
                'ville':         offre.get('ville_std'),
                'competence':    'non_détecté',
                'famille':       'inconnu',
                'date_pub':      offre.get('date_publication'),
                'annee':         str(offre.get('annee')),
                'mois':          str(offre.get('mois')),
            })

    df_competences = pd.DataFrame(resultats)

    nb_offres_avec = df_competences[df_competences['competence'] != 'non_détecté']['id_offre'].nunique()
    logger.info(f"[SILVER NLP] {len(df_competences)} lignes de compétences extraites.")
    logger.info(f"[SILVER NLP] {nb_offres_avec}/{len(df)} offres ont au moins 1 compétence détectée.")

    return df_competences

def sauvegarder_silver(df_offres: pd.DataFrame, df_competences: pd.DataFrame,
                        data_lake_root: str = DATA_LAKE_ROOT):
    """Sauvegarde les données Silver au format Parquet."""
    silver_path = Path(data_lake_root) / 'silver'

    # Offres nettoyées
    chemin_offres = silver_path / 'offres_clean' / 'offres_clean.parquet'
    chemin_offres.parent.mkdir(parents=True, exist_ok=True)
    df_offres.to_parquet(chemin_offres, index=False, compression='snappy')
    logger.info(f"[SILVER] offres_clean.parquet sauvegardé ({chemin_offres.stat().st_size // 1024} Ko)")

    # Compétences extraites
    chemin_comp = silver_path / 'competences_extraites' / 'competences.parquet'
    chemin_comp.parent.mkdir(parents=True, exist_ok=True)
    df_competences.to_parquet(chemin_comp, index=False, compression='snappy')
    logger.info(f"[SILVER] competences.parquet sauvegardé ({chemin_comp.stat().st_size // 1024} Ko)")
