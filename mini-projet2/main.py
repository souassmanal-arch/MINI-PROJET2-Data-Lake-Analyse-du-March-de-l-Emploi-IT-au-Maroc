import os
import sys
import pandas as pd
from pipeline.utils import get_logger, DATA_LAKE_ROOT
from pipeline.bronze_ingestion import ingerer_bronze
from pipeline.silver_transform import executer_transform_silver
from pipeline.silver_nlp import extraire_competences, sauvegarder_silver
from pipeline.gold_aggregation import construire_gold

logger = get_logger("main")

def print_stats_report(df_raw: pd.DataFrame, df_clean: pd.DataFrame, df_comp: pd.DataFrame):
    """Calcule et affiche un rapport comparatif des statistiques avant/après nettoyage."""
    print("\n" + "="*50)
    print("      STATISTIQUES AVANT / APRÈS NETTOYAGE")
    print("="*50)
    
    total_raw = len(df_raw)
    total_clean = len(df_clean)
    
    # Villes
    villes_raw_unique = df_raw['ville'].nunique() if 'ville' in df_raw.columns else 0
    villes_clean_unique = df_clean['ville_std'].nunique()
    
    # Contrats
    contrats_raw_unique = df_raw['type_contrat'].nunique() if 'type_contrat' in df_raw.columns else 0
    contrats_clean_unique = df_clean['type_contrat_std'].nunique()
    
    # Profils
    profils_raw_unique = df_raw['titre_poste'].nunique() if 'titre_poste' in df_raw.columns else 0
    profils_clean_unique = df_clean['profil_normalise'].nunique()
    
    # Salaires
    def est_salaire_renseigne_raw(val):
        if pd.isna(val) or str(val).lower() in ['null', 'confidentiel', 'selon profil', '']:
            return False
        return True
        
    salaires_renseignes_raw = df_raw['salaire_brut'].apply(est_salaire_renseigne_raw).sum() if 'salaire_brut' in df_raw.columns else 0
    salaires_valides_clean = df_clean['salaire_connu'].sum()
    
    pct_sal_raw = (salaires_renseignes_raw / total_raw) * 100
    pct_sal_clean = (salaires_valides_clean / total_clean) * 100
    
    # Dates incohérentes
    dates_incoherentes = (~df_clean['date_coherence_ok']).sum()
    
    # Compétences
    competences_detectees = df_comp[df_comp['competence'] != 'non_détecté']['id_offre'].nunique()
    pct_comp_detectees = (competences_detectees / total_clean) * 100

    lbl_total = "Volume total d'offres"
    lbl_villes = "Nombre de valeurs de villes distinctes"
    lbl_contrats = "Nombre de types de contrats"
    lbl_postes = "Nombre d'intitulés de poste distincts"
    lbl_salaires = "Offres avec salaires exploitables (%)"
    lbl_comp = "Offres avec compétences détectées (%)"
    lbl_dates = "Nombre de dates invalides (pub > exp)"

    print(f"{'Métrique':<35} | {'Avant':<12} | {'Après':<12}")
    print("-"*67)
    print(f"{lbl_total:<35} | {total_raw:<12} | {total_clean:<12}")
    print(f"{lbl_villes:<35} | {villes_raw_unique:<12} | {villes_clean_unique:<12}")
    print(f"{lbl_contrats:<35} | {contrats_raw_unique:<12} | {contrats_clean_unique:<12}")
    print(f"{lbl_postes:<35} | {profils_raw_unique:<12} | {profils_clean_unique:<12}")
    print(f"{lbl_salaires:<35} | {pct_sal_raw:.1f}%        | {pct_sal_clean:.1f}%")
    print(f"{lbl_comp:<35} | {'N/A':<12} | {pct_comp_detectees:.1f}%")
    print(f"{lbl_dates:<35} | {'N/A':<12} | {dates_incoherentes:<12}")
    print("="*50 + "\n")

def main():
    logger.info("Démarrage global du pipeline Mexora RH Intelligence.")
    
    raw_data_file = "offres_emploi_it_maroc.json"
    
    # Étape 1 : Ingestion Bronze
    try:
        logger.info("--- ÉTAPE 1 : INGESTION BRONZE ---")
        stats_bronze = ingerer_bronze(raw_data_file, DATA_LAKE_ROOT)
    except Exception as e:
        logger.error(f"Erreur lors de l'ingestion Bronze : {e}")
        sys.exit(1)
        
    # Étape 2 : Nettoyage & Standardisation Silver
    try:
        logger.info("--- ÉTAPE 2 : NETTOYAGE & STANDARDISATION SILVER ---")
        df_clean = executer_transform_silver(DATA_LAKE_ROOT)
        
        # NLP Extraction compétences
        df_comp = extraire_competences(df_clean)
        
        # Sauvegarde Parquet dans la zone Silver
        sauvegarder_silver(df_clean, df_comp, DATA_LAKE_ROOT)
    except Exception as e:
        logger.error(f"Erreur lors de la transformation Silver : {e}")
        sys.exit(1)
        
    # Étape 3 : Calcul des Agrégats Gold
    try:
        logger.info("--- ÉTAPE 3 : AGRÉGATION GOLD ---")
        construire_gold(DATA_LAKE_ROOT)
    except Exception as e:
        logger.error(f"Erreur lors de l'agrégation Gold : {e}")
        sys.exit(1)
        
    # Affichage des statistiques avant/après
    try:
        df_raw = pd.DataFrame(pd.read_json(raw_data_file)['offres'].tolist())
        print_stats_report(df_raw, df_clean, df_comp)
    except Exception as e:
        logger.warning(f"Impossible d'afficher le rapport de statistiques complet : {e}")
        
    logger.info("Pipeline exécuté avec succès.")

if __name__ == "__main__":
    main()
