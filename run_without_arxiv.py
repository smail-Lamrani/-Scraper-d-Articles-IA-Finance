"""
Script pour scraper toutes les plateformes SAUF arXiv
"""
from scrapper2 import FinanceAIScraper

if __name__ == "__main__":
    print("🎯 SCRAPING SANS arXiv (7 plateformes)")
    print("="*80)
    
    # Créer le scraper
    scraper = FinanceAIScraper(download_pdfs=True, strict_filter=True)
    
    # Mots-clés
    keywords = [
        "machine learning and finance",
        "deep learning and trading",
        "AI and algorithmic trading"
    ]
    
    # Lancer le scraping SANS arXiv
    scraper.scrape_all_platforms(keywords_list=keywords, skip_arxiv=True)
    
    # Sauvegarder
    scraper.save_results('articles_sans_arxiv')
    
    print("\n✅ Terminé!")
