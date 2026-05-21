import json
import os
import re
from pathlib import Path
import pandas as pd
from pipeline.utils import get_logger, DATA_LAKE_ROOT

logger = get_logger("silver_transform")

def charger_depuis_bronze(data_lake_root: str = DATA_LAKE_ROOT) -> pd.DataFrame:
    """Charge et consolide toutes les offres depuis la zone Bronze."""
    logger.info("Chargement des fichiers JSON de la zone Bronze...")
    all_offres = []
    bronze_path = Path(data_lake_root) / 'bronze'

    if not bronze_path.exists():
        logger.error(f"Dossier Bronze inexistant : {bronze_path}")
        return pd.DataFrame()

    for json_file in bronze_path.rglob('offres_raw.json'):
        try:
            with open(json_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            all_offres.extend(data.get('offres', []))
        except Exception as e:
            logger.error(f"Erreur lors de la lecture de {json_file}: {e}")

    df = pd.DataFrame(all_offres)
    logger.info(f"[SILVER] {len(df)} offres chargées depuis Bronze")
    return df

def nettoyer_villes(df: pd.DataFrame) -> pd.DataFrame:
    """Normalise les noms de villes et ajoute la région administrative."""
    logger.info("Normalisation des villes...")
    
    mapping_villes = {
        r'\bcasa\b|\bcasablanca\b': 'Casablanca',
        r'\brabat\b': 'Rabat',
        r'\btanger\b|\btangier\b': 'Tanger',
        r'\bmarrakech\b|\bmarrakesh\b': 'Marrakech',
        r'\bfès\b|\bfes\b': 'Fès',
        r'\bkénitra\b|\bkenitra\b': 'Kénitra',
        r'\boujda\b': 'Oujda',
        r'\bagadir\b': 'Agadir'
    }

    mapping_regions = {
        'Casablanca': 'Casablanca-Settat',
        'Rabat': 'Rabat-Salé-Kénitra',
        'Tanger': 'Tanger-Tétouan-Al Hoceïma',
        'Marrakech': 'Marrakech-Safi',
        'Fès': 'Fès-Meknès',
        'Kénitra': 'Rabat-Salé-Kénitra',
        'Oujda': 'L\'Oriental',
        'Agadir': 'Souss-Massa'
    }

    def standardiser_ville(v):
        if pd.isna(v):
            return 'Non spécifié'
        v_clean = str(v).lower().strip()
        for pattern, city in mapping_villes.items():
            if re.search(pattern, v_clean):
                return city
        return str(v).strip().title()

    df['ville_std'] = df['ville'].apply(standardiser_ville)
    df['region_admin'] = df['ville_std'].map(mapping_regions).fillna('Autre Région')
    
    return df

def nettoyer_contrats(df: pd.DataFrame) -> pd.DataFrame:
    """Normalise les types de contrats."""
    logger.info("Normalisation des contrats...")
    
    mapping_contrats = {
        r'\bcdi\b|contrat à durée indéterminée|permanent': 'CDI',
        r'\bcdd\b|contrat à durée déterminée': 'CDD',
        r'\bfreelance\b|indépendant|consultant': 'Freelance',
        r'\bstage\b|stagiaire': 'Stage',
        r'\banapec\b': 'ANAPEC'
    }

    def standardiser_contrat(c):
        if pd.isna(c):
            return 'Non spécifié'
        c_clean = str(c).lower().strip()
        for pattern, contract in mapping_contrats.items():
            if re.search(pattern, c_clean):
                return contract
        return 'Autre'

    df['type_contrat_std'] = df['type_contrat'].apply(standardiser_contrat)
    return df

def nettoyer_titres_postes(df: pd.DataFrame) -> pd.DataFrame:
    """Standardise les intitulés de poste en familles de profils IT."""
    logger.info("Standardisation des titres de postes...")
    
    mapping_profils = {
        # Data Engineering
        r'data\s*eng(ineer|ineer\w*|\.)?|ingénieur\s+data|dev\s+data\s+eng': 'Data Engineer',
        r'etl\s*dev|pipeline\s*dev|ingénieur\s+etl':                          'Data Engineer',

        # Data Analysis
        r'data\s*anal(yst|yste|ytics)|analyste?\s+data|bi\s+anal':            'Data Analyst',
        r'business\s+intel(ligence)?|ingénieur\s+bi|développeur\s+bi':        'Data Analyst',
        r'reporting\s+(anal|spec|officer)':                                    'Data Analyst',

        # Data Science
        r'data\s*sci(entist|ence)|machine\s*learn|ml\s*eng|ia\s*eng':         'Data Scientist',
        r'deep\s*learn|nlp\s*eng|computer\s*vision':                           'Data Scientist',

        # Software Engineering
        r'full\s*stack|fullstack':                                             'Développeur Full Stack',
        r'back[\s-]*end|backend':                                              'Développeur Backend',
        r'front[\s-]*end|frontend':                                            'Développeur Frontend',
        r'dev(eloppeur|eloper)?\s+mobile|ios\s+dev|android\s+dev':            'Développeur Mobile',

        # Infrastructure
        r'devops|sre|site\s*reliab':                                           'DevOps / SRE',
        r'cloud\s*(arch|eng|admin)|aws\s+eng|gcp\s+eng|azure\s+eng':         'Cloud Engineer',
        r'sys(admin|tème)|réseau\s+inf|network\s+eng':                        'Admin Systèmes & Réseaux',

        # Cyber
        r'cyber|sécurité\s+info|pentester|soc\s+anal':                        'Cybersécurité',

        # Management
        r'chef\s+de\s+proj(et)?|project\s+man|scrum\s*master':               'Chef de Projet IT',
        r'architect(e)?\s+(log|tech|data|cloud|sol)':                         'Architecte IT',
    }

    df['profil_normalise'] = 'Autre IT'
    df['profil_source'] = df['titre_poste'].str.lower().str.strip()

    for pattern, profil in mapping_profils.items():
        masque = df['profil_source'].str.contains(pattern, regex=True, na=False)
        df.loc[masque, 'profil_normalise'] = profil

    non_classes = (df['profil_normalise'] == 'Autre IT').sum()
    logger.info(f"[SILVER] Titres : {len(df) - non_classes} offres classées, {non_classes} classées 'Autre IT'")
    return df

def normaliser_salaires(df: pd.DataFrame) -> pd.DataFrame:
    """Extrait et normalise les salaires en MAD mensuel brut."""
    logger.info("Normalisation des salaires...")
    TAUX_EUR_MAD = 10.8

    def parser_salaire(valeur):
        if pd.isna(valeur) or str(valeur).lower() in ['null', 'confidentiel', 'selon profil', '']:
            return None, None, False

        s = str(valeur).lower().replace(' ', '').replace('\u202f', '')

        # Conversion EUR → MAD
        est_eur = 'eur' in s or '€' in s
        s = s.replace('eur', '').replace('€', '').replace('mad', '').replace('dh', '')

        # Gestion "K" (milliers)
        s = re.sub(r'(\d+(?:\.\d+)?)k', lambda m: str(int(float(m.group(1)) * 1000)), s)

        # Extraction des montants
        nombres = re.findall(r'\d+(?:\.\d+)?', s)

        if not nombres:
            return None, None, False

        montants = [float(n) for n in nombres]

        if est_eur:
            montants = [m * TAUX_EUR_MAD for m in montants]

        if len(montants) >= 2:
            sal_min = min(montants[:2])
            sal_max = max(montants[:2])
        else:
            sal_min = sal_max = montants[0]

        # Cohérence : salaires IT Maroc raisonnables entre 3 000 et 100 000 MAD par mois
        if sal_min < 3000 or sal_max > 100000:
            return None, None, False

        return sal_min, sal_max, True

    resultats = df['salaire_brut'].apply(lambda x: pd.Series(parser_salaire(x),
                                          index=['salaire_min_mad', 'salaire_max_mad', 'salaire_connu']))
    df = pd.concat([df, resultats], axis=1)
    
    # Cast boolean explicitement
    df['salaire_connu'] = df['salaire_connu'].astype(bool)
    df['salaire_median_mad'] = (df['salaire_min_mad'] + df['salaire_max_mad']) / 2

    pct_connu = df['salaire_connu'].mean() * 100
    logger.info(f"[SILVER] Salaires : {pct_connu:.1f}% des offres ont un salaire exploitable")
    return df

def normaliser_experience(df: pd.DataFrame) -> pd.DataFrame:
    """Transforme l'expérience en valeur numérique (années min requises)."""
    logger.info("Normalisation des années d'expérience...")
    
    def parser_experience(valeur):
        if pd.isna(valeur):
            return None, None

        s = str(valeur).lower()

        if any(mot in s for mot in ['débutant', 'junior', 'stage', 'sans expérience']):
            return 0, 2
        if any(mot in s for mot in ['senior', 'confirmé', 'expert', 'lead']):
            return 5, None

        fourchette = re.search(r'(\d+)\s*[-àa]\s*(\d+)', s)
        if fourchette:
            return int(fourchette.group(1)), int(fourchette.group(2))

        min_seul = re.search(r'(\d+)\s*(?:ans?|years?)', s)
        if min_seul:
            return int(min_seul.group(1)), None

        return None, None

    resultats = df['experience_requise'].apply(
        lambda x: pd.Series(parser_experience(x), index=['experience_min_ans', 'experience_max_ans'])
    )
    df = pd.concat([df, resultats], axis=1)
    return df

def valider_dates_et_extraire_periodes(df: pd.DataFrame) -> pd.DataFrame:
    """Valide les dates et extrait l'année, le mois et un flag de cohérence."""
    logger.info("Validation des dates de publication et d'expiration...")
    
    df['date_pub_dt'] = pd.to_datetime(df['date_publication'], errors='coerce')
    df['date_exp_dt'] = pd.to_datetime(df['date_expiration'], errors='coerce')
    
    # Flag de cohérence temporelle : publication <= expiration
    df['date_coherence_ok'] = df['date_pub_dt'] <= df['date_exp_dt']
    
    # Remplir les valeurs manquantes avec True
    df['date_coherence_ok'] = df['date_coherence_ok'].fillna(True)
    
    # Extraire annee et mois
    df['annee'] = df['date_pub_dt'].dt.year.fillna(2024).astype(int).astype(str)
    df['mois'] = df['date_pub_dt'].dt.month.fillna(1).astype(int).apply(lambda x: f"{x:02d}")
    
    invalides = (~df['date_coherence_ok']).sum()
    logger.info(f"[SILVER] Dates : {invalides} offres possèdent des dates incohérentes (pub > exp)")
    
    return df

def normaliser_teletravail(df: pd.DataFrame) -> pd.DataFrame:
    """Standardise la politique de télétravail."""
    logger.info("Normalisation des politiques de télétravail...")
    
    def standardiser_telework(t):
        if pd.isna(t):
            return "Non spécifié"
        t_clean = str(t).lower().strip()
        if "hybride" in t_clean or "partiel" in t_clean:
            return "Hybride"
        elif "remote" in t_clean or "télétravail" in t_clean or "telework" in t_clean:
            return "Télétravail"
        elif "présentiel" in t_clean or "site" in t_clean:
            return "Présentiel"
        return "Non spécifié"
        
    df['teletravail_std'] = df['teletravail'].apply(standardiser_telework)
    return df

def executer_transform_silver(data_lake_root: str = DATA_LAKE_ROOT) -> pd.DataFrame:
    """Exécute l'ensemble du pipeline de transformation Silver."""
    df_raw = charger_depuis_bronze(data_lake_root)
    if df_raw.empty:
        raise ValueError("Aucune donnée chargée depuis la zone Bronze.")
        
    df_clean = df_raw.copy()
    
    # Application séquentielle des règles de nettoyage
    df_clean = nettoyer_villes(df_clean)
    df_clean = nettoyer_contrats(df_clean)
    df_clean = nettoyer_titres_postes(df_clean)
    df_clean = normaliser_salaires(df_clean)
    df_clean = normaliser_experience(df_clean)
    df_clean = valider_dates_et_extraire_periodes(df_clean)
    df_clean = normaliser_teletravail(df_clean)
    
    # Nettoyer les colonnes techniques temporaires
    cols_a_garder = [
        'id_offre', 'source', 'titre_poste', 'profil_normalise', 'description', 
        'competences_brut', 'entreprise', 'ville', 'ville_std', 'region_admin',
        'type_contrat', 'type_contrat_std', 'experience_requise', 'experience_min_ans', 'experience_max_ans',
        'salaire_brut', 'salaire_min_mad', 'salaire_max_mad', 'salaire_median_mad', 'salaire_connu',
        'niveau_etudes', 'secteur', 'date_publication', 'date_expiration', 'date_coherence_ok',
        'nb_postes', 'teletravail', 'teletravail_std', 'langue_requise', 'annee', 'mois'
    ]
    
    df_clean = df_clean[cols_a_garder]
    logger.info(f"[SILVER] Transformation terminée : {len(df_clean)} offres nettoyées.")
    return df_clean
