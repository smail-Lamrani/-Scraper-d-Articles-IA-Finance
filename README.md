# 📚 Scraper d'Articles IA & Finance

Script de scraping automatisé pour récupérer des articles académiques sur l'**Intelligence Artificielle appliquée à la Finance**.

## 🎯 Sources supportées

| Source | Type | Accès PDF |
|--------|------|-----------|
| [arXiv](https://arxiv.org) | Preprints académiques | ✅ Gratuit |
| [SSRN](https://www.ssrn.com) | Financial Economics Network | ⚠️ Auth requise |
| [Google Scholar](https://scholar.google.com) | Agrégateur | Variable |
| [JFDS](https://www.pm-research.com/content/iijjfds) | Journal spécialisé DS & Finance | Variable |
| [J Banking Finance](https://www.sciencedirect.com/journal/journal-of-banking-and-finance) | Journal académique | 🔓 Open Access prioritaire |
| [IEEE Xplore](https://ieeexplore.ieee.org) | Publications techniques | Variable |
| [JMLR](https://www.jmlr.org) | Machine Learning Research | ✅ Gratuit |
| [ResearchGate](https://www.researchgate.net) | Réseau de recherche | Variable |

---

## 📊 Dernier Scraping (29 Décembre 2025)


### Articles phares récupérés

#### 🏆 Prédiction de marché
- **S&P 500 Stock's Movement Prediction using CNN** - Prédiction avec réseaux convolutifs
- **Structured Event Representation and Stock Return Predictability** - LLMs pour extraction d'événements
- **Adaptive Weighted GA-SVR for Global Stock Indices Forecasting** - Prévision long-terme

#### 🔒 Risque & Fraude
- **Secure and Explainable Fraud Detection** - Framework privacy-preserving
- **Systemic Risk Radar** - Détection précoce de crises avec graphes multicouches
- **AIMM: AI-Driven Market Manipulation Detection** - Détection via Reddit + OHLCV

#### 📈 Portfolio & Trading
- **Covariance-Aware Simplex Projection** - Optimisation de portefeuille
- **Multi-Objective Bayesian Optimization for ESG Portfolio** - RL + critères ESG
- **Interpretable Hypothesis-Driven Trading** - Framework walk-forward

#### 🧠 Techniques avancées
- **HGAN-SDEs** - GANs pour équations différentielles stochastiques
- **LoFT-LLM** - LLMs pour forecasting time-series
- **Deep Learning for McKean-Vlasov FBSDEs** - Méthodes numériques avancées

---

## 🔧 Installation

```bash
# Cloner le repo
git clone https://github.com/smail-Lamrani/-Scraper-d-Articles-IA-Finance.git
cd scrapping_articles

# Installer les dépendances (avec uv)
uv sync

# Ou avec pip
pip install -r requirements.txt
```

## 🚀 Utilisation

### Scraper simple (arXiv uniquement)

```bash
python scrapper.py
```

### Scraper complet (8 plateformes)

```bash
python scrapper2.py
```

### Options disponibles

```python
from scrapper2 import FinanceAIScraper

# Créer le scraper
scraper = FinanceAIScraper(
    download_pdfs=True,      # Télécharger les PDFs
    strict_filter=True       # Filtrage finance strict
)

# Mots-clés personnalisés
keywords = [
    "machine learning and finance",
    "deep learning and trading",
    "reinforcement learning and portfolio"
]

# Lancer le scraping (toutes les plateformes)
scraper.scrape_all_platforms(keywords_list=keywords)

# Sauvegarder
scraper.save_results()
```

### Plateformes disponibles

| Code | Plateforme |
|------|------------|
| `arxiv` | arXiv |
| `ssrn` | SSRN Financial Economics |
| `scholar` | Google Scholar |
| `jfds` | Journal of Financial Data Science |
| `banking` | Journal of Banking & Finance |
| `ieee` | IEEE Xplore |
| `jmlr` | Journal of Machine Learning Research |
| `researchgate` | ResearchGate |

---

## 🔒 Système de filtrage

Le scraper utilise un **filtrage strict** pour garantir que seuls les articles liés à la finance sont conservés.

### Mots-clés de validation (34 termes)

```
finance, financial, trading, market, stock, portfolio, investment,
asset, pricing, risk, hedge, forex, currency, bond, derivative,
option, futures, commodities, banking, credit, volatility, returns,
profit, arbitrage, quantitative, algorithmic, hft, fund, etf,
cryptocurrency, bitcoin, blockchain, fintech, earnings
```

### Fonctionnement

1. **Requête arXiv améliorée** : Utilise `AND` + catégories `q-fin.*`, `econ.*`, `cs.AI`
2. **Post-filtrage** : Vérifie la présence d'au moins 1 mot-clé finance dans titre/abstract
3. **Rejet** : Articles ML purs sans application finance = exclus

---

## 📁 Structure des fichiers générés

```
scrapping_articles/
├── pdfs_articles/           # PDFs téléchargés (675+ fichiers)
│   └── arxiv/
├── pdfs_articles2/          # PDFs téléchargés (30 fichiers)
│   ├── arxiv/
│   ├── ssrn/
│   ├── google_scholar/
│   └── ...
├── articles_ia_finance_*.json    # Données JSON
├── articles_ia_finance_*.csv     # Données CSV
└── articles_ia_finance_index_*.html  # Index navigable
```

---

## 📋 Format des données

Chaque article contient :

```json
{
  "source": "arXiv",
  "article_id": "2512.21866v1",
  "title": "Secure and Explainable Fraud Detection...",
  "authors": ["Yiming Qian", "..."],
  "summary": "We propose an explainable, privacy-preserving...",
  "published": "2025-12-26",
  "url": "http://arxiv.org/abs/2512.21866v1",
  "pdf_url": "https://arxiv.org/pdf/2512.21866v1",
  "pdf_path": "pdfs_articles2/arxiv/2512.21866v1_..."
}
```

---

## 🛠️ Dépendances

```
requests>=2.32.5
beautifulsoup4>=4.14.3
pandas>=2.3.3
lxml>=6.0.2
```

---

## 📝 License

MIT License