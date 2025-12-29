"""
Script de scraping pour articles IA & Finance de Marché avec téléchargement PDF
Supporte: arXiv, SSRN, Google Scholar, ResearchGate, et autres
"""

import requests
from bs4 import BeautifulSoup
import pandas as pd
import time
import json
from datetime import datetime
import re
from urllib.parse import urljoin, quote
import xml.etree.ElementTree as ET
import os
from pathlib import Path

class FinanceAIScraper:
    # Mots-clés obligatoires pour valider qu'un article est lié à la finance
    FINANCE_KEYWORDS = [
        'finance', 'financial', 'trading', 'trader', 'trade',
        'market', 'stock', 'equity', 'portfolio', 'investment',
        'asset', 'pricing', 'risk', 'hedge', 'hedging',
        'forex', 'currency', 'bond', 'derivative', 'option',
        'futures', 'commodities', 'banking', 'credit', 'loan',
        'volatility', 'returns', 'profit', 'loss', 'arbitrage',
        'quantitative', 'algorithmic', 'high-frequency', 'hft',
        'wealth', 'fund', 'etf', 'index', 'dow', 'nasdaq', 's&p',
        'cryptocurrency', 'bitcoin', 'blockchain', 'defi',
        'fintech', 'robo-advisor', 'sentiment', 'earnings'
    ]
    
    def __init__(self, download_pdfs=True, strict_filter=True):
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        self.results = []
        self.download_pdfs = download_pdfs
        self.strict_filter = strict_filter  # Activer le filtrage strict
        self.rejected_count = 0  # Compteur d'articles rejetés
        
        # Créer dossiers pour PDFs
        if self.download_pdfs:
            self.pdf_dir = Path('pdfs_articles2')
            self.pdf_dir.mkdir(exist_ok=True)
            
            # Sous-dossiers par source
            for source in ['arxiv', 'ssrn', 'scholar', 'researchgate', 'other']:
                (self.pdf_dir / source).mkdir(exist_ok=True)
    
    def is_finance_relevant(self, title, summary=""):
        """Vérifier si l'article est pertinent pour la finance"""
        text = f"{title} {summary}".lower()
        
        # Chercher au moins un mot-clé finance
        for keyword in self.FINANCE_KEYWORDS:
            if keyword in text:
                return True
        
        return False
    
    def download_pdf(self, url, title, source, article_id=None):
        """Télécharger un PDF depuis une URL"""
        if not url:
            return None
        
        try:
            # Créer un nom de fichier sûr
            safe_title = re.sub(r'[^\w\s-]', '', title)[:100]
            safe_title = re.sub(r'\s+', '_', safe_title)
            
            if article_id:
                filename = f"{article_id}_{safe_title}.pdf"
            else:
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                filename = f"{timestamp}_{safe_title}.pdf"
            
            # Déterminer le sous-dossier
            source_lower = source.lower().replace(' ', '')
            folder = self.pdf_dir / source_lower
            filepath = folder / filename
            
            # Télécharger le PDF
            print(f"   📥 Téléchargement: {filename[:50]}...")
            response = requests.get(url, headers=self.headers, timeout=60, stream=True)
            response.raise_for_status()
            
            # Vérifier que c'est bien un PDF
            content_type = response.headers.get('content-type', '').lower()
            if 'pdf' not in content_type and 'application' not in content_type:
                print(f"   ⚠️  Pas un PDF: {content_type}")
                return None
            
            # Sauvegarder le fichier
            with open(filepath, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
            
            file_size = os.path.getsize(filepath) / (1024 * 1024)  # MB
            print(f"   ✅ PDF sauvegardé: {filepath} ({file_size:.2f} MB)")
            
            return str(filepath)
            
        except Exception as e:
            print(f"   ❌ Erreur téléchargement PDF: {e}")
            return None
    
    def scrape_arxiv(self, keywords="machine learning finance", max_results=50):
        """Scrape arXiv pour articles IA & Finance avec téléchargement PDF"""
        print(f"🔍 Scraping arXiv avec: {keywords}")
        
        base_url = "http://export.arxiv.org/api/query"
        
        # Construire une requête plus stricte avec AND
        # Séparer les mots-clés et les joindre avec AND
        terms = keywords.split()
        if len(terms) > 1:
            # Recherche dans titre OU abstract avec tous les termes
            query_parts = [f'all:{term}' for term in terms]
            search_query = ' AND '.join(query_parts)
        else:
            search_query = f'all:{keywords}'
        
        # Ajouter filtre catégorie q-fin (Quantitative Finance) OU cs (Computer Science)
        # pour cibler les articles pertinents
        category_filter = '(cat:q-fin.* OR cat:stat.ML OR cat:cs.LG OR cat:cs.AI)'
        search_query = f'({search_query}) AND {category_filter}'
        
        print(f"   📝 Requête: {search_query}")
        
        params = {
            'search_query': search_query,
            'start': 0,
            'max_results': max_results * 2,  # Récupérer plus pour compenser le filtrage
            'sortBy': 'submittedDate',
            'sortOrder': 'descending'
        }
        
        try:
            response = requests.get(base_url, params=params, timeout=30)
            response.raise_for_status()
            
            # Parser XML
            root = ET.fromstring(response.content)
            ns = {'atom': 'http://www.w3.org/2005/Atom'}
            
            for entry in root.findall('atom:entry', ns):
                title = entry.find('atom:title', ns).text.strip()
                article_id = entry.find('atom:id', ns).text.split('/')[-1]
                
                article = {
                    'source': 'arXiv',
                    'article_id': article_id,
                    'title': title,
                    'authors': [author.find('atom:name', ns).text 
                               for author in entry.findall('atom:author', ns)],
                    'summary': entry.find('atom:summary', ns).text.strip()[:500],
                    'published': entry.find('atom:published', ns).text[:10],
                    'url': entry.find('atom:id', ns).text,
                    'pdf_url': None,
                    'pdf_path': None
                }
                
                # Récupérer lien PDF
                for link in entry.findall('atom:link', ns):
                    if link.get('title') == 'pdf':
                        article['pdf_url'] = link.get('href')
                        break
                
                # Appliquer le filtrage strict si activé
                if self.strict_filter:
                    if not self.is_finance_relevant(title, article['summary']):
                        self.rejected_count += 1
                        print(f"   ⏭️  Rejeté (hors sujet): {title[:50]}...")
                        continue
                
                # Télécharger le PDF si disponible (seulement si l'article est pertinent)
                if self.download_pdfs and article['pdf_url']:
                    pdf_path = self.download_pdf(
                        article['pdf_url'], 
                        title, 
                        'arxiv',
                        article_id
                    )
                    article['pdf_path'] = pdf_path
                    time.sleep(2)  # Rate limiting pour téléchargement
                
                self.results.append(article)
                
                # Limiter au nombre demandé
                if len([r for r in self.results if r['source'] == 'arXiv']) >= max_results:
                    break
            
            arxiv_count = len([r for r in self.results if r['source'] == 'arXiv'])
            print(f"✅ {arxiv_count} articles arXiv pertinents récupérés ({self.rejected_count} rejetés)")
            
        except Exception as e:
            print(f"❌ Erreur arXiv: {e}")
    
    def scrape_ssrn(self, keywords="machine learning finance", max_pages=3):
        """Scrape SSRN (Financial Economics Network)"""
        print(f"🔍 Scraping SSRN avec: {keywords}")
        
        base_url = "https://papers.ssrn.com/sol3/results.cfm"
        
        try:
            for page in range(1, max_pages + 1):
                params = {
                    'npage': page,
                    'query': keywords
                }
                
                response = requests.get(base_url, params=params, 
                                      headers=self.headers, timeout=30)
                soup = BeautifulSoup(response.content, 'html.parser')
                
                # Chercher les articles
                articles = soup.find_all('div', class_='box-abstract')
                
                if not articles:
                    articles = soup.find_all('a', href=re.compile(r'abstract_id='))
                
                for article_elem in articles[:10]:
                    try:
                        title_elem = article_elem.find('h3') or article_elem
                        title = title_elem.get_text(strip=True)
                        
                        link = article_elem.find('a', href=True)
                        url = urljoin(base_url, link['href']) if link else ""
                        
                        # Extraire l'ID de l'article
                        article_id = None
                        if url:
                            match = re.search(r'abstract_id=(\d+)', url)
                            if match:
                                article_id = match.group(1)
                        
                        article = {
                            'source': 'SSRN',
                            'article_id': article_id,
                            'title': title,
                            'authors': [],
                            'summary': '',
                            'published': '',
                            'url': url,
                            'pdf_url': None,
                            'pdf_path': None
                        }
                        
                        # SSRN nécessite souvent authentification pour PDFs
                        # On garde juste l'URL pour référence
                        if article_id:
                            article['pdf_url'] = f"https://papers.ssrn.com/sol3/Delivery.cfm/SSRN_ID{article_id}_code.pdf"
                        
                        self.results.append(article)
                    except:
                        continue
                
                time.sleep(2)  # Rate limiting
            
            print(f"✅ Articles SSRN récupérés (PDFs nécessitent authentification)")
            
        except Exception as e:
            print(f"❌ Erreur SSRN: {e}")
    
    def scrape_google_scholar(self, keywords="AI market finance", max_results=20):
        """Scrape Google Scholar (version simplifiée)"""
        print(f"🔍 Scraping Google Scholar avec: {keywords}")
        print("⚠️  Note: Google Scholar limite le scraping, résultats limités")
        
        base_url = "https://scholar.google.com/scholar"
        params = {
            'q': keywords,
            'hl': 'en',
            'as_sdt': '0,5'
        }
        
        try:
            response = requests.get(base_url, params=params, 
                                  headers=self.headers, timeout=30)
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Chercher les résultats
            for result in soup.find_all('div', class_='gs_ri')[:max_results]:
                try:
                    title_elem = result.find('h3', class_='gs_rt')
                    title = title_elem.get_text(strip=True) if title_elem else ""
                    
                    link_elem = title_elem.find('a') if title_elem else None
                    url = link_elem['href'] if link_elem and link_elem.has_attr('href') else ""
                    
                    summary_elem = result.find('div', class_='gs_rs')
                    summary = summary_elem.get_text(strip=True)[:300] if summary_elem else ""
                    
                    authors_elem = result.find('div', class_='gs_a')
                    authors = authors_elem.get_text(strip=True) if authors_elem else ""
                    
                    # Chercher lien PDF
                    pdf_link = result.find('a', href=re.compile(r'\.pdf$'))
                    pdf_url = pdf_link['href'] if pdf_link else None
                    
                    article = {
                        'source': 'Google Scholar',
                        'article_id': None,
                        'title': title,
                        'authors': [authors],
                        'summary': summary,
                        'published': '',
                        'url': url,
                        'pdf_url': pdf_url,
                        'pdf_path': None
                    }
                    
                    # Télécharger PDF si disponible
                    if self.download_pdfs and pdf_url and pdf_url.startswith('http'):
                        pdf_path = self.download_pdf(pdf_url, title, 'scholar')
                        article['pdf_path'] = pdf_path
                        time.sleep(3)
                    
                    self.results.append(article)
                except:
                    continue
            
            print(f"✅ Articles Google Scholar récupérés")
            
        except Exception as e:
            print(f"❌ Erreur Google Scholar: {e}")
    
    def scrape_researchgate(self, keywords="AI finance", max_results=20):
        """Scrape ResearchGate (version simplifiée)"""
        print(f"🔍 Scraping ResearchGate avec: {keywords}")
        
        base_url = "https://www.researchgate.net/search/publication"
        params = {'q': keywords}
        
        try:
            response = requests.get(base_url, params=params, 
                                  headers=self.headers, timeout=30)
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Chercher les publications
            articles = soup.find_all('div', class_='nova-legacy-e-text')[:max_results]
            
            for article in articles:
                try:
                    title = article.get_text(strip=True)
                    
                    self.results.append({
                        'source': 'ResearchGate',
                        'article_id': None,
                        'title': title,
                        'authors': [],
                        'summary': '',
                        'published': '',
                        'url': '',
                        'pdf_url': None,
                        'pdf_path': None
                    })
                except:
                    continue
            
            print(f"✅ Articles ResearchGate récupérés")
            
        except Exception as e:
            print(f"❌ Erreur ResearchGate: {e}")
    
    def scrape_all(self, keywords_list=None):
        """Scrape toutes les sources"""
        if keywords_list is None:
            keywords_list = [
                "machine learning finance",
                "deep learning trading",
                "AI market prediction",
                "algorithmic trading",
                "financial forecasting neural networks"
            ]
        
        print("=" * 60)
        print("🚀 DÉBUT DU SCRAPING MULTI-SOURCES")
        print("=" * 60)
        
        for keywords in keywords_list:
            print(f"\n📊 Mots-clés: {keywords}")
            print("-" * 60)
            
            self.scrape_arxiv(keywords, max_results=30)
            time.sleep(3)
            
            # Les autres sources peuvent être plus restrictives
            # self.scrape_ssrn(keywords, max_pages=2)
            # time.sleep(3)
            
            # self.scrape_google_scholar(keywords, max_results=10)
            # time.sleep(5)
        
        print("\n" + "=" * 60)
        print(f"✅ SCRAPING TERMINÉ: {len(self.results)} articles récupérés")
        
        # Compter PDFs téléchargés
        pdfs_downloaded = sum(1 for r in self.results if r.get('pdf_path'))
        print(f"📥 PDFs téléchargés: {pdfs_downloaded}/{len(self.results)}")
        print("=" * 60)
    
    def save_results(self, filename='articles_ia_finance'):
        """Sauvegarder les résultats"""
        if not self.results:
            print("⚠️  Aucun résultat à sauvegarder")
            return
        
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        # Sauvegarder en CSV
        df = pd.DataFrame(self.results)
        csv_file = f'{filename}_{timestamp}.csv'
        df.to_csv(csv_file, index=False, encoding='utf-8-sig')
        print(f"💾 CSV sauvegardé: {csv_file}")
        
        # Sauvegarder en JSON
        json_file = f'{filename}_{timestamp}.json'
        with open(json_file, 'w', encoding='utf-8') as f:
            json.dump(self.results, f, indent=2, ensure_ascii=False)
        print(f"💾 JSON sauvegardé: {json_file}")
        
        # Créer un index HTML des PDFs
        if self.download_pdfs:
            self.create_pdf_index(filename, timestamp)
        
        # Statistiques
        print(f"\n📊 STATISTIQUES:")
        print(f"   Total articles: {len(self.results)}")
        for source in df['source'].unique():
            count = len(df[df['source'] == source])
            pdfs = len(df[(df['source'] == source) & (df['pdf_path'].notna())])
            print(f"   - {source}: {count} articles ({pdfs} PDFs)")
    
    def create_pdf_index(self, filename, timestamp):
        """Créer un index HTML pour naviguer dans les PDFs"""
        html_file = f'{filename}_index_{timestamp}.html'
        
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <title>Index Articles IA Finance - {timestamp}</title>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 20px; }}
                h1 {{ color: #2c3e50; }}
                .article {{ 
                    border: 1px solid #ddd; 
                    padding: 15px; 
                    margin: 10px 0; 
                    border-radius: 5px;
                }}
                .title {{ font-weight: bold; font-size: 1.1em; color: #2980b9; }}
                .source {{ color: #27ae60; font-weight: bold; }}
                .authors {{ color: #7f8c8d; font-size: 0.9em; }}
                .pdf-link {{ 
                    background: #3498db; 
                    color: white; 
                    padding: 5px 10px; 
                    text-decoration: none;
                    border-radius: 3px;
                    display: inline-block;
                    margin-top: 5px;
                }}
                .pdf-link:hover {{ background: #2980b9; }}
                .no-pdf {{ color: #e74c3c; }}
            </style>
        </head>
        <body>
            <h1>📚 Index Articles IA & Finance</h1>
            <p>Généré le: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
            <p>Total: {len(self.results)} articles</p>
            <hr>
        """
        
        for i, article in enumerate(self.results, 1):
            authors = ', '.join(article['authors'][:3]) if article['authors'] else 'N/A'
            if len(article['authors']) > 3:
                authors += ' et al.'
            
            html_content += f"""
            <div class="article">
                <div class="title">{i}. {article['title']}</div>
                <div class="source">Source: {article['source']}</div>
                <div class="authors">Auteurs: {authors}</div>
                <div>Date: {article['published'] or 'N/A'}</div>
            """
            
            if article['pdf_path']:
                html_content += f'<a href="{article["pdf_path"]}" class="pdf-link" target="_blank">📄 Voir PDF</a>'
            else:
                html_content += '<span class="no-pdf">❌ PDF non disponible</span>'
            
            if article['url']:
                html_content += f' <a href="{article["url"]}" target="_blank">🔗 Lien source</a>'
            
            html_content += "</div>"
        
        html_content += """
        </body>
        </html>
        """
        
        with open(html_file, 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        print(f"📄 Index HTML créé: {html_file}")
    
    def filter_by_keywords(self, keywords):
        """Filtrer les résultats par mots-clés"""
        filtered = []
        keywords_lower = [k.lower() for k in keywords]
        
        for article in self.results:
            text = f"{article['title']} {article['summary']}".lower()
            if any(kw in text for kw in keywords_lower):
                filtered.append(article)
        
        return filtered


# ==================== UTILISATION ====================

if __name__ == "__main__":
    # Créer le scraper avec téléchargement PDF activé
    scraper = FinanceAIScraper(download_pdfs=True)
    
    # Mots-clés personnalisés
    custom_keywords = [
        "machine learning finance",
        "deep learning trading",
        "reinforcement learning portfolio",
        "neural networks market prediction",
        "AI algorithmic trading"
    ]
    
    # Lancer le scraping
    scraper.scrape_all(keywords_list=custom_keywords)
    
    # Sauvegarder les résultats
    scraper.save_results()
    
    # Afficher quelques exemples
    print("\n📄 EXEMPLES D'ARTICLES RÉCUPÉRÉS:")
    print("=" * 60)
    for i, article in enumerate(scraper.results[:5], 1):
        print(f"\n{i}. {article['title'][:80]}...")
        print(f"   Source: {article['source']}")
        print(f"   PDF: {'✅ Téléchargé' if article['pdf_path'] else '❌ Non disponible'}")
        if article['pdf_path']:
            print(f"   Chemin: {article['pdf_path']}")