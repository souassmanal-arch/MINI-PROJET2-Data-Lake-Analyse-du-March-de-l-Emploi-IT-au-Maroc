import os
from pathlib import Path
import duckdb
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

# Set style for professional charts
sns.set_theme(style="whitegrid")
plt.rcParams.update({
    'font.size': 11,
    'axes.labelsize': 12,
    'axes.titlesize': 14,
    'xtick.labelsize': 10,
    'ytick.labelsize': 10,
    'figure.titlesize': 16,
    'font.family': 'sans-serif'
})

# Paths
GOLD_PATH = Path("data_lake/gold")
SILVER_PATH = Path("data_lake/silver")
VIS_PATH = Path("visualisations")
VIS_PATH.mkdir(exist_ok=True)

# Connect to DuckDB
con = duckdb.connect()

def analyser_competences():
    print("\n" + "="*80)
    print(" QUESTION 1 : COMPÉTENCES LES PLUS DEMANDÉES")
    print("="*80)
    
    # 1. Top 20 compétences globales
    df_global = con.execute(f"""
        SELECT competence, famille, nb_offres_mentionnent, pct_offres_total
        FROM '{GOLD_PATH}/top_competences.parquet'
        WHERE profil = 'tous'
        ORDER BY nb_offres_mentionnent DESC
        LIMIT 20
    """).df()
    print("\n--- TOP 20 COMPÉTENCES GLOBALES ---")
    print(df_global.to_string(index=False))
    
    # 2. Top 5 compétences par profil data
    df_data = con.execute(f"""
        SELECT profil, competence, famille, nb_offres_mentionnent, rang_dans_profil
        FROM '{GOLD_PATH}/top_competences.parquet'
        WHERE profil IN ('Data Engineer', 'Data Analyst', 'Data Scientist')
          AND rang_dans_profil <= 5
        ORDER BY profil, rang_dans_profil
    """).df()
    print("\n--- TOP 5 COMPÉTENCES PAR PROFIL DATA ---")
    print(df_data.to_string(index=False))

    # Plot : Top 15 compétences globales
    plt.figure(figsize=(10, 6))
    top_15 = df_global.head(15)
    
    # Custom palette based on families
    unique_families = top_15['famille'].unique()
    colors = sns.color_palette("muted", len(unique_families))
    family_color_map = dict(zip(unique_families, colors))
    bar_colors = top_15['famille'].map(family_color_map)

    bars = plt.barh(top_15['competence'][::-1], top_15['pct_offres_total'][::-1], color=bar_colors[::-1].tolist(), edgecolor='none', height=0.6)
    
    # Add values at the end of bars
    for bar in bars:
        width = bar.get_width()
        plt.text(width + 0.5, bar.get_y() + bar.get_height()/2, f'{width:.1f}%', 
                 va='center', ha='left', fontsize=9, fontweight='bold', color='#2c3e50')

    # Legend for families
    from matplotlib.patches import Patch
    legend_elements = [Patch(facecolor=family_color_map[fam], label=fam.replace('_', ' ').title()) for fam in unique_families]
    plt.legend(handles=legend_elements, title="Famille de technologie", loc="lower right")

    plt.title("Top 15 des compétences IT les plus demandées au Maroc", pad=20, fontweight='bold')
    plt.xlabel("% des offres mentionnant la compétence")
    plt.ylabel("Compétences")
    plt.xlim(0, max(top_15['pct_offres_total']) + 8)
    plt.tight_layout()
    plt.savefig(VIS_PATH / "top_competences.png", dpi=300)
    plt.close()
    print(f"Graphique sauvegardé : {VIS_PATH / 'top_competences.png'}")


def analyser_geographie():
    print("\n" + "="*80)
    print(" QUESTION 2 : OPPORTUNITÉS PAR VILLE (TANGER VS CASA VS RABAT)")
    print("="*80)
    
    # 1. Volume d'offres par ville
    df_villes = con.execute(f"""
        SELECT 
            ville,
            SUM(nb_offres) AS total_offres,
            SUM(nb_offres_remote) AS total_remote,
            ROUND(SUM(nb_offres_remote) * 100.0 / SUM(nb_offres), 1) AS pct_remote
        FROM '{GOLD_PATH}/offres_par_ville.parquet'
        GROUP BY ville
        ORDER BY total_offres DESC
    """).df()
    print("\n--- RÉPARTITION DU VOLUME D'OFFRES PAR VILLE ---")
    print(df_villes.to_string(index=False))
    
    # 2. Focus Tanger : profil et remote
    df_tanger = con.execute(f"""
        SELECT 
            profil,
            SUM(nb_offres) AS nb_offres_tanger,
            ROUND(SUM(nb_offres_remote) * 100.0 / NULLIF(SUM(nb_offres), 0), 1) AS pct_remote_tanger
        FROM '{GOLD_PATH}/offres_par_ville.parquet'
        WHERE ville = 'Tanger'
        GROUP BY profil
        ORDER BY nb_offres_tanger DESC
    """).df()
    print("\n--- OPPORTUNITÉS PAR PROFIL À TANGER ---")
    print(df_tanger.to_string(index=False))

    # Plot : Répartition par ville (Horizontal bar)
    plt.figure(figsize=(8, 5))
    df_villes_clean = df_villes[df_villes['ville'] != 'Non Spécifié'].head(6)
    
    # Creating double bars for Total vs Remote
    y_pos = range(len(df_villes_clean))
    plt.barh([y - 0.2 for y in y_pos], df_villes_clean['total_offres'], height=0.4, label='Total Offres', color='#2c3e50')
    plt.barh([y + 0.2 for y in y_pos], df_villes_clean['total_remote'], height=0.4, label='Dont Télétravail / Hybride', color='#1abc9c')
    
    plt.yticks(y_pos, df_villes_clean['ville'])
    plt.xlabel("Nombre d'offres d'emploi")
    plt.ylabel("Villes")
    plt.title("Volume d'offres IT et part du télétravail par ville au Maroc", pad=20, fontweight='bold')
    plt.legend(loc="lower right")
    plt.gca().invert_yaxis()
    plt.tight_layout()
    plt.savefig(VIS_PATH / "geo_distribution.png", dpi=300)
    plt.close()
    print(f"Graphique sauvegardé : {VIS_PATH / 'geo_distribution.png'}")


def analyser_salaires():
    print("\n" + "="*80)
    print(" QUESTION 3 : SALAIRES MÉDIANS IT")
    print("="*80)
    
    # 1. Salaires médians nationaux par profil
    df_sal_nat = con.execute(f"""
        SELECT 
            profil,
            SUM(nb_offres) AS nb_offres,
            ROUND(AVG(salaire_median_mad), 0) AS salaire_moyen,
            ROUND(MEDIAN(salaire_median_mad), 0) AS salaire_median,
            ROUND(MIN(salaire_min_observe), 0) AS salaire_min,
            ROUND(MAX(salaire_max_observe), 0) AS salaire_max
        FROM '{GOLD_PATH}/salaires_par_profil.parquet'
        GROUP BY profil
        ORDER BY salaire_median DESC NULLS LAST
    """).df()
    print("\n--- SALAIRES MÉDIANS NATIONAUX PAR PROFIL IT ---")
    print(df_sal_nat.to_string(index=False))
    
    # 2. Salaires à Tanger spécifiquement
    df_sal_tanger = con.execute(f"""
        SELECT 
            profil,
            SUM(nb_offres) AS nb_offres_tanger,
            ROUND(MEDIAN(salaire_median_mad), 0) AS salaire_median_tanger,
            (
                SELECT ROUND(MEDIAN(salaire_median_mad), 0)
                FROM '{GOLD_PATH}/salaires_par_profil.parquet' AS sub
                WHERE sub.profil = main.profil
            ) AS salaire_median_national
        FROM '{GOLD_PATH}/salaires_par_profil.parquet' AS main
        WHERE ville = 'Tanger'
        GROUP BY profil
        ORDER BY salaire_median_tanger DESC NULLS LAST
    """).df()
    df_sal_tanger['ecart_mad'] = df_sal_tanger['salaire_median_tanger'] - df_sal_tanger['salaire_median_national']
    print("\n--- SALAIRES MÉDIANS À TANGER VS RÉFÉRENTIEL NATIONAL ---")
    print(df_sal_tanger.to_string(index=False))

    # Plot : Distribution des salaires par profil (Boxplot)
    # On charge les données Silver offres_clean pour faire un boxplot propre
    df_offres = con.execute(f"""
        SELECT profil_normalise AS profil, salaire_median_mad
        FROM '{SILVER_PATH}/offres_clean/offres_clean.parquet'
        WHERE salaire_connu = TRUE
          AND profil_normalise != 'Autre IT'
    """).df()
    
    plt.figure(figsize=(12, 6))
    # Order by median
    order = df_offres.groupby('profil')['salaire_median_mad'].median().sort_values(ascending=False).index
    
    sns.boxplot(
        x='salaire_median_mad', 
        y='profil', 
        data=df_offres, 
        order=order,
        palette="viridis",
        width=0.6,
        showfliers=False # hide outliers for readability
    )
    
    plt.title("Distribution des salaires proposés par profil IT au Maroc (MAD/mois)", pad=20, fontweight='bold')
    plt.xlabel("Salaire médian proposé (MAD)")
    plt.ylabel("Profil IT")
    plt.tight_layout()
    plt.savefig(VIS_PATH / "boxplot_salaires.png", dpi=300)
    plt.close()
    print(f"Graphique sauvegardé : {VIS_PATH / 'boxplot_salaires.png'}")


def analyser_experience():
    print("\n" + "="*80)
    print(" QUESTION 4 : CORRÉLATION EXPÉRIENCE / SALAIRE")
    print("="*80)
    
    df_corr = con.execute(f"""
        SELECT 
            profil_normalise AS profil,
            ROUND(CORR(experience_min_ans, salaire_median_mad), 3) AS correlation_pearson,
            COUNT(*) AS nb_offres_analysees
        FROM '{SILVER_PATH}/offres_clean/offres_clean.parquet'
        WHERE salaire_connu = TRUE 
          AND experience_min_ans IS NOT NULL
        GROUP BY profil_normalise
        ORDER BY correlation_pearson DESC
    """).df()
    print("\n--- CORRÉLATION DE PEARSON EXPÉRIENCE VS SALAIRE PAR PROFIL ---")
    print(df_corr.to_string(index=False))
    
    # 2. Progression par tranches d'expérience globales
    df_tranches = con.execute(f"""
        SELECT 
            CASE 
                WHEN experience_min_ans = 0 THEN '0 - Débutant (0-1 an)'
                WHEN experience_min_ans BETWEEN 1 AND 2 THEN '1-2 ans Junior'
                WHEN experience_min_ans BETWEEN 3 AND 4 THEN '3-4 ans Confirmé'
                WHEN experience_min_ans BETWEEN 5 AND 7 THEN '5-7 ans Senior'
                WHEN experience_min_ans >= 8 THEN '8+ ans Lead/Expert'
            END AS tranche_experience,
            COUNT(*) AS nb_offres,
            ROUND(MEDIAN(salaire_median_mad), 0) AS salaire_median_mad
        FROM '{SILVER_PATH}/offres_clean/offres_clean.parquet'
        WHERE salaire_connu = TRUE 
          AND experience_min_ans IS NOT NULL
        GROUP BY tranche_experience
        ORDER BY MIN(experience_min_ans)
    """).df()
    print("\n--- SALAIRE MÉDIAN PAR TRANCHE D'EXPÉRIENCE (TOUS PROFILS) ---")
    print(df_tranches.to_string(index=False))


def analyser_entreprises():
    print("\n" + "="*80)
    print(" QUESTION 5 : TOP RECRUTEURS & CONCURRENCE POUR MEXORA")
    print("="*80)
    
    # 1. Top 20 recruteurs nationaux
    df_recruteurs = con.execute(f"""
        SELECT 
            entreprise,
            ville,
            nb_offres_publiees,
            salaire_moyen_propose
        FROM '{GOLD_PATH}/entreprises_recruteurs.parquet'
        ORDER BY nb_offres_publiees DESC
        LIMIT 20
    """).df()
    print("\n--- TOP 20 ENTREPRISES QUI RECRUTENT LE PLUS AU MAROC ---")
    print(df_recruteurs.to_string(index=False))
    
    # 2. Focus Tanger : concurrents directs de Mexora (recrutent profil Data à Tanger)
    df_comp_tanger = con.execute(f"""
        SELECT 
            entreprise,
            nb_offres_publiees,
            profils_recrutes,
            salaire_moyen_propose,
            CASE 
                WHEN salaire_moyen_propose > 20000 THEN 'Compétiteur fort (>20k MAD)'
                WHEN salaire_moyen_propose > 12000 THEN 'Compétiteur moyen (12-20k MAD)'
                ELSE 'Compétiteur faible (<12k MAD)'
            END AS niveau_competition
        FROM '{GOLD_PATH}/entreprises_recruteurs.parquet'
        WHERE ville = 'Tanger'
          AND (
            list_contains(profils_recrutes, 'Data Engineer')
            OR list_contains(profils_recrutes, 'Data Analyst')
            OR list_contains(profils_recrutes, 'Data Scientist')
          )
        ORDER BY salaire_moyen_propose DESC NULLS LAST
    """).df()
    print("\n--- CONCURRENTS DIRECTS DE MEXORA (PROFILS DATA À TANGER) ---")
    print(df_comp_tanger.to_string(index=False))


def generer_courbe_tendances():
    # Plot 4: Évolution mensuelle pour les profils Data (Data Engineer, Data Analyst, Data Scientist)
    df_trends = con.execute(f"""
        SELECT 
            annee,
            mois,
            profil,
            nb_offres
        FROM '{GOLD_PATH}/tendances_mensuelles.parquet'
        WHERE profil IN ('Data Engineer', 'Data Analyst', 'Data Scientist')
        ORDER BY profil, annee, mois
    """).df()
    
    df_trends['periode'] = df_trends['annee'] + "-" + df_trends['mois']
    
    plt.figure(figsize=(10, 5))
    sns.lineplot(
        x='periode', 
        y='nb_offres', 
        hue='profil', 
        data=df_trends, 
        marker='o',
        linewidth=2,
        palette=['#3498db', '#e67e22', '#2ecc71']
    )
    
    plt.title("Évolution mensuelle des offres d'emploi Data au Maroc (2023-2024)", pad=20, fontweight='bold')
    plt.xlabel("Période (Mois)")
    plt.ylabel("Nombre d'offres publiées")
    plt.xticks(rotation=45)
    plt.legend(title="Profil Data")
    plt.tight_layout()
    plt.savefig(VIS_PATH / "trends_data_roles.png", dpi=300)
    plt.close()
    print(f"Graphique sauvegardé : {VIS_PATH / 'trends_data_roles.png'}")


def main():
    print("DÉBUT DE L'ANALYSE DU MARCHÉ DE L'EMPLOI IT")
    analyser_competences()
    analyser_geographie()
    analyser_salaires()
    analyser_experience()
    analyser_entreprises()
    generer_courbe_tendances()
    con.close()
    print("\nFIN DE L'ANALYSE. Toutes les visualisations sont dans le dossier 'visualisations/'.")

if __name__ == "__main__":
    main()
