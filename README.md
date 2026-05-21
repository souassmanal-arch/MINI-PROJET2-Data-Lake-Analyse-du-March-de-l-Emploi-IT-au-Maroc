# Mexora RH Intelligence — Data Lake & Analyse du Marché de l'Emploi IT au Maroc

Ce dépôt implémente un **Data Lake** complet structuré en zones **Bronze (Raw)**, **Silver (Cleaned/Enriched)**, et **Gold (Curated/Analytics)** pour analyser le marché de l'emploi IT au Maroc. Ce projet a été réalisé pour accompagner la stratégie de recrutement du Directeur des Ressources Humaines (DRH) de **Mexora RH**.

## 🏗️ Architecture du Projet

Le projet respecte la structure suivante :

```text
mexora_rh_lake/
├── analysis/
│   ├── analyse_marche.py            # Script d'analyse SQL DuckDB & génération de graphiques
│   ├── create_ipynb.py              # Script utilitaire pour générer le notebook Jupyter
│   └── analyse_marche_it_maroc.ipynb # Notebook Jupyter interactif final
├── data_lake/                       # Dossier racine du Data Lake (généré automatiquement)
│   ├── bronze/                      # Zone Bronze : fichiers JSON bruts, partitionnés par source/mois
│   ├── silver/                      # Zone Silver : Parquet nettoyés et compétences extraites (NLP)
│   └── gold/                        # Zone Gold : Parquet des tables agrégées pour l'analyse
├── pipeline/
│   ├── bronze_ingestion.py          # Ingestion brute et partitionnement
│   ├── silver_transform.py          # Nettoyage avancé et typage
│   ├── silver_nlp.py                # Extraction regex et matching des compétences IT
│   ├── gold_aggregation.py          # Agrégations SQL (DuckDB) des tables analytiques
│   └── utils.py                     # Configuration commune (logs, chemins, etc.)
├── generate_data.py                 # Générateur de 5 000 offres d'emploi avec erreurs
├── referentiel_competences_it.json  # Référentiel de 300 compétences IT structurées
├── entreprises_it_maroc.csv         # Référentiel des entreprises IT au Maroc
├── offres_emploi_it_maroc.json      # Fichier d'offres brutes (généré par generate_data.py)
└── requirements.txt                 # Dépendances Python du projet
```

---

## 🚀 Guide de Démarrage Rapide

### 1. Installation des Dépendances
Assurez-vous de disposer de Python 3.11+ installé. Installez les bibliothèques requises :

```bash
pip install -r requirements.txt
```

### 2. Génération des Données Initiales
Générez le jeu de données fictif de 5 000 offres d'emploi IT contenant des anomalies volontaires (salaires incohérents, dates invalides, compétences mélangées, etc.) :

```bash
python generate_data.py
```

### 3. Exécution du Pipeline de Données (ETL)
Lancez l'orchestrateur du pipeline pour exécuter le flux complet (Bronze → Silver → Gold) :

```bash
python main.py
```
*Le script effectuera l'ingestion brute, appliquera les règles de nettoyage, réalisera l'extraction NLP des compétences et écrira les tables analytiques Gold. Il affichera un rapport comparatif statistique avant/après.*

### 4. Génération de l'Analyse du Marché
Exécutez le script d'analyse pour lancer les requêtes analytiques avec **DuckDB** et générer les graphiques professionnels dans le dossier `visualisations/` :

```bash
python analysis/analyse_marche.py
```

---

## 📊 Principaux Composants

- **Zone Bronze** : Stockée sous forme de fichiers JSON fidèles aux données d'origine, partitionnée sous le schéma `bronze/<source>/<annee_mois>/offres_raw.json`.
- **Zone Silver** : Consolidée et écrite au format Parquet. Elle applique un typage fort, calcule la médiane pour les fourchettes de salaires converties en MAD, filtre les anomalies temporelles et effectue un matching d'entités textuelles pour structurer les compétences.
- **Zone Gold** : Compilée par des requêtes SQL DuckDB sur les Parquet Silver. Elle contient les tables multidimensionnelles pré-agrégées (`top_competences`, `salaires_par_profil`, `offres_par_ville`, `entreprises_recruteurs`, `tendances_mensuelles`).
- **Analyse & Notebook** : Le dossier `analysis/` contient le notebook Jupyter `analyse_marche_it_maroc.ipynb` avec les graphiques interactifs et les interprétations des 5 questions clés de recrutement.
