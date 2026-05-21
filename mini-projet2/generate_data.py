import json
import csv
import random
from datetime import datetime, timedelta

# Set seed for reproducibility
random.seed(42)

# Load referential and companies to align generation
try:
    with open('referentiel_competences_it.json', 'r', encoding='utf-8') as f:
        ref_data = json.load(f)
except Exception as e:
    ref_data = {}

try:
    companies = []
    with open('entreprises_it_maroc.csv', 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            companies.append(row['nom_entreprise'])
except Exception as e:
    companies = ["TechMaroc SARL", "Capgemini", "Inwi", "Maroc Telecom", "Orange", "HPS", "SQLI", "Attijariwafa Bank"]

# Define profiles and their technical keywords for realistic generation
profiles_tech = {
    "Data Engineer": {
        "titles": ["Data Engineer", "Ingénieur Big Data", "Dev Data", "Data Eng.", "ETL Developer", "Ingénieur ETL", "Data Pipeline Dev"],
        "skills": ["python", "spark", "sql", "airflow", "dbt", "hadoop", "kafka", "aws", "gcp", "azure", "snowflake", "databricks"],
        "desc_template": "Nous recherchons un {title} pour concevoir et optimiser nos pipelines de données. Vous maîtriserez les technologies comme {skills_str}. Vous travaillerez sur des architectures distribuées dans un environnement agile."
    },
    "Data Analyst": {
        "titles": ["Data Analyst", "Analyste Data", "BI Analyst", "Business Intelligence Dev", "Développeur BI", "Reporting Officer", "Ingénieur BI"],
        "skills": ["sql", "power_bi", "tableau", "excel", "looker", "metabase", "python", "qlik"],
        "desc_template": "Dans le cadre de notre croissance, nous recrutons un {title}. Rattaché à la direction, vous concevez des dashboards sous {skills_str} et analysez les KPIs métiers à l'aide de requêtes SQL complexes."
    },
    "Data Scientist": {
        "titles": ["Data Scientist", "Scientifique de données", "Machine Learning Eng", "ML Engineer", "IA Engineer", "NLP Specialist", "Deep Learning Eng"],
        "skills": ["python", "r", "sql", "tensorflow", "pytorch", "scikit-learn", "django", "flask", "gcp", "aws"],
        "desc_template": "Nous cherchons un {title} passionné par la modélisation et l'apprentissage statistique. Vous développerez des modèles prédictifs avec {skills_str} et les déploierez en production."
    },
    "Développeur Full Stack": {
        "titles": ["Développeur Full Stack", "Full Stack Developer", "Dev Fullstack React/Node", "Ingénieur Full Stack Java", "Fullstack Web Dev"],
        "skills": ["javascript", "react", "node.js", "angular", "spring", "sql", "docker", "git", "nextjs", "vue"],
        "desc_template": "Intégré dans une équipe produit, vous serez {title} en charge du développement front-end et back-end. Stack cible : {skills_str}. Expérience en développement d'API REST souhaitée."
    },
    "Développeur Backend": {
        "titles": ["Développeur Backend", "Backend Developer", "Dev Back-end Java/Spring", "Ingénieur Backend Python", "Backend PHP Developer"],
        "skills": ["java", "spring", "python", "django", "php", "laravel", "sql", "postgresql", "docker", "git", "go"],
        "desc_template": "Nous recrutons un {title} pour renforcer notre équipe technique. Vous participerez à la conception et au développement des services backend en utilisant {skills_str} et gérerez les bases de données SQL/NoSQL."
    },
    "Développeur Frontend": {
        "titles": ["Développeur Frontend", "Frontend Developer", "Dev Front-end React", "Frontend Engineer Angular", "Vue.js Developer"],
        "skills": ["javascript", "react", "angular", "vue", "typescript", "git", "html", "css", "nextjs"],
        "desc_template": "Nous recherchons un {title} talentueux pour concevoir des interfaces web réactives et fluides. Vous travaillerez avec {skills_str} et collaborerez avec notre équipe UI/UX."
    },
    "DevOps / SRE": {
        "titles": ["DevOps Engineer", "Ingénieur DevOps", "SRE", "DevOps / Cloud Engineer", "Infrastructure DevOps", "Cloud DevOps Developer"],
        "skills": ["docker", "kubernetes", "ansible", "terraform", "jenkins", "git", "aws", "azure", "gcp", "linux"],
        "desc_template": "Rattaché à l'équipe Infra, vous serez {title}. Votre mission consiste à automatiser les déploiements et gérer la CI/CD via {skills_str}. Vous assurerez la haute disponibilité et la scalabilité."
    },
    "Chef de Projet IT": {
        "titles": ["Chef de projet IT", "Project Manager IT", "Scrum Master", "Chef de Projet Agile", "Product Owner", "IT Project Leader"],
        "skills": ["jira", "confluence", "scrum", "agile", "trello", "git", "kanban", "pmp"],
        "desc_template": "En tant que {title}, vous piloterez les projets de développement logiciel de bout en bout. Vous animerez les rituels Scrum, coordonnerez les équipes techniques et assurerez le reporting."
    }
}

# Messy representations for cities
cities_messy = [
    # Casablanca (highest weight)
    ("Casablanca", 0.45), ("casa", 0.08), ("CASABLANCA", 0.05), ("Casablanca ", 0.02),
    # Rabat
    ("Rabat", 0.15), ("rabat", 0.03), ("RABAT", 0.02),
    # Tanger
    ("Tanger", 0.08), ("tanger", 0.02), ("TANGER", 0.01), ("Tangier", 0.01),
    # Marrakech
    ("Marrakech", 0.04), ("marrakech", 0.01), ("Marrakesh", 0.01),
    # Fès
    ("Fès", 0.03), ("Fes", 0.01), ("fes", 0.01),
    # Others
    ("Agadir", 0.01), ("Oujda", 0.01), ("Kénitra", 0.01)
]

def get_weighted_city():
    r = random.random()
    cumulative = 0.0
    for city, weight in cities_messy:
        cumulative += weight
        if r <= cumulative:
            return city
    return "Casablanca"

# Messy contract types
contracts_messy = [
    "CDI", "cdi", "Contrat à durée indéterminée", "Permanent",
    "Freelance", "freelance", "CDD", "cdd", "Stage", "stage", "ANAPEC"
]

# Messy experience ranges
experiences_messy = [
    "3-5 ans", "3 à 5 ans", "min 3 ans", "Débutant accepté", "Senior (7+ ans)",
    "1-2 ans", "5-7 ans", "8+ ans", "2 à 4 ans", "Débutant", "10 ans d'expérience", None
]

# Messy salary formats
salaries_messy_templates = [
    "{min}-{max} MAD", "{min}K-{max}K", "Selon profil", "Confidentiel",
    "{min_eur}-{max_eur} EUR", "{val_eur}€", "{min} MAD", "{min}dh",
    "{min}K-{max}K MAD", "{min}-{max} dh"
]

def generate_salary(profile):
    # Salaries depend on the profile to reflect real trends
    base_salaries = {
        "Data Engineer": (12000, 25000),
        "Data Analyst": (8000, 16000),
        "Data Scientist": (14000, 30000),
        "Développeur Full Stack": (10000, 22000),
        "Développeur Backend": (9000, 20000),
        "Développeur Frontend": (8000, 18000),
        "DevOps / SRE": (13000, 26000),
        "Chef de Projet IT": (12000, 22000)
    }
    
    min_b, max_b = base_salaries.get(profile, (8000, 15000))
    # Add random variance
    sal_min = int(round(random.randint(min_b, max_b) / 1000.0) * 1000)
    sal_max = sal_min + random.randint(2, 8) * 1000
    
    choice = random.choices(
        [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10], 
        weights=[0.3, 0.15, 0.2, 0.1, 0.05, 0.03, 0.07, 0.05, 0.03, 0.01, 0.01]
    )[0]
    
    if choice == 0:
        return f"{sal_min}-{sal_max} MAD"
    elif choice == 1:
        return f"{sal_min//1000}K-{sal_max//1000}K"
    elif choice == 2:
        return "Selon profil"
    elif choice == 3:
        return "Confidentiel"
    elif choice == 4:
        # Convert to EUR
        return f"{int(sal_min/10.8)}-{int(sal_max/10.8)} EUR"
    elif choice == 5:
        return f"{int(sal_min/10.8)}€"
    elif choice == 6:
        return f"{sal_min} MAD"
    elif choice == 7:
        return f"{sal_min}dh"
    elif choice == 8:
        return f"{sal_min//1000}K-{sal_max//1000}K MAD"
    elif choice == 9:
        return f"{sal_min}-{sal_max} dh"
    else:
        return None

# Generate dates with deliberate errors
def generate_dates():
    start_date = datetime(2023, 1, 1)
    end_date = datetime(2024, 11, 30)
    delta_days = (end_date - start_date).days
    
    random_days = random.randint(0, delta_days)
    pub_date = start_date + timedelta(days=random_days)
    
    # 5% probability of invalid dates (pub_date > exp_date)
    if random.random() < 0.05:
        # Publication date is after expiration
        exp_date = pub_date - timedelta(days=random.randint(10, 30))
    else:
        exp_date = pub_date + timedelta(days=random.randint(15, 60))
        
    return pub_date.strftime("%Y-%m-%d"), exp_date.strftime("%Y-%m-%d")

# Sources and details
sources = ["rekrute", "marocannonce", "linkedin"]
levels = ["Bac+5", "Bac+3", "Bac+4", "Ingénieur", "Master"]
sectors = ["Informatique / Télécom", "Secteur bancaire", "Conseil & Intégration", "E-commerce", "Assurances"]
telework_types = ["Hybride", "Télétravail", "Présentiel", "Remote", "Télétravail partiel", None]
languages_list = [["Français", "Anglais"], ["Français"], ["Français", "Anglais", "Arabe"], ["Anglais"]]

# Generating 5000 offers
offres = []
for i in range(1, 5001):
    profile = random.choice(list(profiles_tech.keys()))
    details = profiles_tech[profile]
    
    title = random.choice(details["titles"])
    # Randomly select 3-6 skills for this offer
    skills_selected = random.sample(details["skills"], random.randint(3, min(6, len(details["skills"]))))
    
    # Format skills into messy list
    separators = [", ", " / ", " • ", "\n", " - ", " / "]
    sep = random.choice(separators)
    competences_brut = sep.join(skills_selected)
    
    # Generate description
    description = details["desc_template"].format(
        title=title,
        skills_str=", ".join(skills_selected)
    )
    
    # Add random extra text or skills to description
    if random.random() < 0.3:
        description += " Connaissances en git, docker et de la méthodologie agile."
        
    entreprise = random.choice(companies)
    ville = get_weighted_city()
    type_contrat = random.choice(contracts_messy)
    experience_requise = random.choice(experiences_messy)
    salaire_brut = generate_salary(profile)
    pub_date, exp_date = generate_dates()
    
    offre = {
        "id_offre": f"OFFRE-{i:05d}",
        "source": random.choice(sources),
        "titre_poste": title,
        "description": description,
        "competences_brut": competences_brut,
        "entreprise": entreprise,
        "ville": ville,
        "type_contrat": type_contrat,
        "experience_requise": experience_requise,
        "salaire_brut": salaire_brut,
        "niveau_etudes": random.choice(levels),
        "secteur": random.choice(sectors),
        "date_publication": pub_date,
        "date_expiration": exp_date,
        "nb_postes": random.choices([1, 2, 3, 5], weights=[0.8, 0.12, 0.05, 0.03])[0],
        "teletravail": random.choice(telework_types),
        "langue_requise": random.choice(languages_list)
    }
    offres.append(offre)

dataset = {"offres": offres}

with open("offres_emploi_it_maroc.json", "w", encoding="utf-8") as f:
    json.dump(dataset, f, ensure_ascii=False, indent=2)

print(f"Generated 5000 offers and saved in offres_emploi_it_maroc.json")
