"""
Script de scraping COMPLET pour TOUTES les plateformes IA & Finance
Sources: arXiv, SSRN, Google Scholar, JFDS, J Banking Finance, IEEE, JMLR, ResearchGate
"""

import requests
from bs4 import BeautifulSoup
import pandas as pd
import time
import json
from datetime import datetime
import re
from urllib.parse import urljoin, quote, urlparse
import xml.etree.ElementTree as ET
import os
from pathlib import Path

class FinanceAIScraper:
    """Scraper spécialisé IA & Finance avec filtrage strict"""
    
    # Mots-clés obligatoires pour valider la pertinence finance
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
        'fintech', 'robo-advisor', 'sentiment', 'earnings',
        'macroeconomic', 'monetary', 'fiscal', 'recession'
    ]
    
    def __init__(self, download_pdfs=True, strict_filter=True):
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        }
        self.results = []
        self.download_pdfs = download_pdfs
        self.strict_filter = strict_filter
        self.rejected_count = 0
        self.seen_titles = set()  # Pour la déduplication
        self.duplicate_count = 0
        
        # Créer dossiers pour PDFs
        if self.download_pdfs:
            self.pdf_dir = Path('pdfs_articles')
            self.pdf_dir.mkdir(exist_ok=True)
            
            # Sous-dossiers par source
            sources = ['arxiv', 'ssrn', 'google_scholar', 'jfds', 'banking_finance', 
                      'ieee', 'jmlr', 'researchgate']
            for source in sources:
                (self.pdf_dir / source).mkdir(exist_ok=True)
    
    def normalize_title(self, title):
        """Normaliser un titre pour la comparaison"""
        # Enlever ponctuation, espaces multiples, mettre en minuscule
        normalized = re.sub(r'[^\w\s]', '', title.lower())
        normalized = re.sub(r'\s+', ' ', normalized).strip()
        return normalized
    
    def is_duplicate(self, title):
        """Vérifier si un article est un doublon"""
        normalized = self.normalize_title(title)
        if normalized in self.seen_titles:
            self.duplicate_count += 1
            return True
        self.seen_titles.add(normalized)
        return False
    
    def remove_duplicates(self):
        """Supprimer les doublons des résultats"""
        seen = set()
        unique_results = []
        for article in self.results:
            normalized = self.normalize_title(article['title'])
            if normalized not in seen:
                seen.add(normalized)
                unique_results.append(article)
        
        removed = len(self.results) - len(unique_results)
        self.results = unique_results
        return removed
    
    def is_finance_relevant(self, title, summary=""):
        """Vérifier si l'article est pertinent pour la finance"""
        text = f"{title} {summary}".lower()
        for keyword in self.FINANCE_KEYWORDS:
            if keyword in text:
                return True
        return False
    
    def download_pdf(self, url, title, source, article_id=None):
        """Télécharger un PDF depuis une URL"""
        if not url:
            return None
        
        try:
            safe_title = re.sub(r'[^\w\s-]', '', title)[:100]
            safe_title = re.sub(r'\s+', '_', safe_title)
            
            if article_id:
                filename = f"{article_id}_{safe_title}.pdf"
            else:
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                filename = f"{timestamp}_{safe_title}.pdf"
            
            source_lower = source.lower().replace(' ', '_')
            folder = self.pdf_dir / source_lower
            filepath = folder / filename
            
            print(f"   📥 Téléchargement: {filename[:50]}...")
            response = requests.get(url, headers=self.headers, timeout=60, stream=True)
            response.raise_for_status()
            
            content_type = response.headers.get('content-type', '').lower()
            if 'pdf' not in content_type and 'application' not in content_type:
                print(f"   ⚠️  Pas un PDF: {content_type}")
                return None
            
            with open(filepath, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
            
            file_size = os.path.getsize(filepath) / (1024 * 1024)
            print(f"   ✅ PDF sauvegardé: {file_size:.2f} MB")
            
            return str(filepath)
            
        except Exception as e:
            print(f"   ❌ Erreur téléchargement PDF: {e}")
            return None
    
    def scrape_arxiv(self, keywords="machine learning and finance", max_results=100):
        """1. arXiv - API officielle avec filtrage strict
        URL ref: https://arxiv.org/search/?query=machine+learning+and+finance&searchtype=all
        """
        print(f"\n{'='*60}")
        print(f"📚 1. SCRAPING arXiv")
        print(f"{'='*60}")
        print(f"Mots-clés: {keywords}")
        
        base_url = "http://export.arxiv.org/api/query"
        
        # Construire une requête stricte avec AND
        terms = keywords.replace(' and ', ' ').split()
        if len(terms) > 1:
            query_parts = [f'all:{term}' for term in terms]
            search_query = ' AND '.join(query_parts)
        else:
            search_query = f'all:{keywords}'
        
        # Filtrer par catégories pertinentes (q-fin = Quantitative Finance)
        category_filter = '(cat:q-fin.* OR cat:stat.ML OR cat:cs.LG OR cat:cs.AI OR cat:econ.*)'
        search_query = f'({search_query}) AND {category_filter}'
        
        print(f"   📝 Requête: {search_query}")
        
        params = {
            'search_query': search_query,
            'start': 0,
            'max_results': max_results * 2,  # Plus pour compenser le filtrage
            'sortBy': 'submittedDate',
            'sortOrder': 'descending'
        }
        
        try:
            response = requests.get(base_url, params=params, timeout=30)
            response.raise_for_status()
            
            root = ET.fromstring(response.content)
            ns = {'atom': 'http://www.w3.org/2005/Atom'}
            
            count = 0
            for entry in root.findall('atom:entry', ns):
                title = entry.find('atom:title', ns).text.strip()
                summary = entry.find('atom:summary', ns).text.strip()[:500]
                article_id = entry.find('atom:id', ns).text.split('/')[-1]
                
                # Filtrage strict
                if self.strict_filter and not self.is_finance_relevant(title, summary):
                    self.rejected_count += 1
                    print(f"   ⏭️  Rejeté (hors sujet): {title[:50]}...")
                    continue
                
                article = {
                    'source': 'arXiv',
                    'article_id': article_id,
                    'title': title,
                    'authors': [author.find('atom:name', ns).text 
                               for author in entry.findall('atom:author', ns)],
                    'summary': summary,
                    'published': entry.find('atom:published', ns).text[:10],
                    'url': entry.find('atom:id', ns).text,
                    'pdf_url': None,
                    'pdf_path': None
                }
                
                for link in entry.findall('atom:link', ns):
                    if link.get('title') == 'pdf':
                        article['pdf_url'] = link.get('href')
                        break
                
                if self.download_pdfs and article['pdf_url']:
                    pdf_path = self.download_pdf(
                        article['pdf_url'], title, 'arxiv', article_id
                    )
                    article['pdf_path'] = pdf_path
                    time.sleep(2)
                
                self.results.append(article)
                count += 1
                
                if count >= max_results:
                    break
            
            print(f"✅ arXiv: {count} articles pertinents ({self.rejected_count} rejetés)")
            
        except Exception as e:
            print(f"❌ Erreur arXiv: {e}")
    
    def scrape_ssrn(self, keywords="machine learning finance", max_pages=5):
        """2. SSRN (Financial Economics Network)
        URL ref: https://www.ssrn.com/index.cfm/en/decisionscirn/
        """
        print(f"\n{'='*60}")
        print(f"📊 2. SCRAPING SSRN (Financial Economics Network)")
        print(f"{'='*60}")
        print(f"Mots-clés: {keywords}")
        
        base_url = "https://papers.ssrn.com/sol3/results.cfm"
        count = 0
        
        try:
            for page in range(1, max_pages + 1):
                print(f"   Page {page}/{max_pages}...")
                params = {'npage': page, 'query': keywords}
                
                response = requests.get(base_url, params=params, 
                                      headers=self.headers, timeout=30)
                soup = BeautifulSoup(response.content, 'html.parser')
                
                for link in soup.find_all('a', href=re.compile(r'abstract_id=')):
                    try:
                        title = link.get_text(strip=True)
                        if not title or len(title) < 10:
                            continue
                        
                        # Filtrage strict
                        if self.strict_filter and not self.is_finance_relevant(title):
                            self.rejected_count += 1
                            continue
                        
                        url = urljoin(base_url, link['href'])
                        match = re.search(r'abstract_id=(\d+)', url)
                        article_id = match.group(1) if match else None
                        
                        article = {
                            'source': 'SSRN',
                            'article_id': article_id,
                            'title': title,
                            'authors': [],
                            'summary': '',
                            'published': '',
                            'url': url,
                            'pdf_url': f"https://papers.ssrn.com/sol3/Delivery.cfm/SSRN_ID{article_id}_code.pdf" if article_id else None,
                            'pdf_path': None
                        }
                        
                        self.results.append(article)
                        count += 1
                    except:
                        continue
                
                time.sleep(3)
            
            print(f"✅ SSRN: {count} articles récupérés")
            
        except Exception as e:
            print(f"❌ Erreur SSRN: {e}")
    
    def scrape_google_scholar(self, keywords="Agentic AI finance", max_results=50):
        """3. Google Scholar avec filtrage
        URL ref: https://scholar.google.com/scholar?hl=en&as_sdt=0%2C5&q=Agentic+AI
        Alerts: https://scholar.google.com/scholar_alerts?view_op=list_alerts&hl=en
        """
        print(f"\n{'='*60}")
        print(f"🎓 3. SCRAPING Google Scholar")
        print(f"{'='*60}")
        print(f"Mots-clés: {keywords}")
        print("⚠️  Note: Google Scholar limite le scraping")
        
        base_url = "https://scholar.google.com/scholar"
        count = 0
        
        try:
            for start in range(0, max_results, 10):
                params = {
                    'q': keywords,
                    'hl': 'en',
                    'start': start,
                    'as_sdt': '0,5'
                }
                
                response = requests.get(base_url, params=params, 
                                      headers=self.headers, timeout=30)
                soup = BeautifulSoup(response.content, 'html.parser')
                
                for result in soup.find_all('div', class_='gs_ri'):
                    try:
                        title_elem = result.find('h3', class_='gs_rt')
                        if not title_elem:
                            continue
                        
                        title = title_elem.get_text(strip=True)
                        
                        summary_elem = result.find('div', class_='gs_rs')
                        summary = summary_elem.get_text(strip=True)[:300] if summary_elem else ""
                        
                        # Filtrage strict
                        if self.strict_filter and not self.is_finance_relevant(title, summary):
                            self.rejected_count += 1
                            continue
                        
                        link_elem = title_elem.find('a')
                        url = link_elem['href'] if link_elem and link_elem.has_attr('href') else ""
                        
                        authors_elem = result.find('div', class_='gs_a')
                        authors = authors_elem.get_text(strip=True) if authors_elem else ""
                        
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
                        
                        if self.download_pdfs and pdf_url and pdf_url.startswith('http'):
                            pdf_path = self.download_pdf(pdf_url, title, 'google_scholar')
                            article['pdf_path'] = pdf_path
                            time.sleep(3)
                        
                        self.results.append(article)
                        count += 1
                    except:
                        continue
                
                time.sleep(5)
            
            print(f"✅ Google Scholar: {count} articles récupérés")
            
        except Exception as e:
            print(f"❌ Erreur Google Scholar: {e}")
    
    def scrape_jfds(self, keywords="data science finance"):
        """4. Journal of Financial Data Science - Best articles DS & Finance
        URL ref: https://www.pm-research.com/content/iijjfds
        """
        print(f"\n{'='*60}")
        print(f"📈 4. SCRAPING Journal of Financial Data Science")
        print(f"{'='*60}")
        
        base_url = "https://www.pm-research.com/content/iijjfds"
        count = 0
        
        try:
            response = requests.get(base_url, headers=self.headers, timeout=30)
            soup = BeautifulSoup(response.content, 'html.parser')
            
            for article_elem in soup.find_all('div', class_=['article', 'toc-item', 'highwire-cite']):
                try:
                    title_elem = article_elem.find(['h3', 'h4', 'a', 'span'], class_=re.compile(r'title|cite'))
                    if not title_elem:
                        continue
                    
                    title = title_elem.get_text(strip=True)
                    if len(title) < 10:
                        continue
                    
                    # JFDS est spécifiquement sur la finance, pas besoin de filtrer
                    link = article_elem.find('a', href=True)
                    url = urljoin(base_url, link['href']) if link else ""
                    
                    article = {
                        'source': 'JFDS',
                        'article_id': None,
                        'title': title,
                        'authors': [],
                        'summary': '',
                        'published': '',
                        'url': url,
                        'pdf_url': None,
                        'pdf_path': None
                    }
                    
                    self.results.append(article)
                    count += 1
                except:
                    continue
            
            print(f"✅ JFDS: {count} articles récupérés (tous finance-related)")
            
        except Exception as e:
            print(f"❌ Erreur JFDS: {e}")
    
    def scrape_banking_finance(self, keywords="machine learning", open_access_only=True):
        """5. Journal of Banking and Finance - Focus Open Access
        URL ref: https://www.sciencedirect.com/journal/journal-of-banking-and-finance
        Note: Articles have open access "Free" and some only abstract
        """
        print(f"\n{'='*60}")
        print(f"🏦 5. SCRAPING Journal of Banking and Finance")
        print(f"{'='*60}")
        print(f"   🔓 Mode: {'Open Access uniquement' if open_access_only else 'Tous les articles'}")
        
        # URL de recherche ScienceDirect pour ce journal
        search_url = f"https://www.sciencedirect.com/search?qs={quote(keywords)}&show=100&sortBy=date&pub=Journal%20of%20Banking%20and%20Finance&accessTypes=openaccess" if open_access_only else f"https://www.sciencedirect.com/search?qs={quote(keywords)}&show=100&sortBy=date&pub=Journal%20of%20Banking%20and%20Finance"
        count = 0
        open_access_count = 0
        
        try:
            response = requests.get(search_url, headers=self.headers, timeout=30)
            soup = BeautifulSoup(response.content, 'html.parser')
            
            for result in soup.find_all(['div', 'li'], class_=re.compile(r'result|search-result|ResultItem')):
                try:
                    title_elem = result.find(['h2', 'h3', 'a'], class_=re.compile(r'result-title|title'))
                    if not title_elem:
                        title_elem = result.find('a')
                    if not title_elem:
                        continue
                    
                    title = title_elem.get_text(strip=True)
                    if len(title) < 15:
                        continue
                    
                    # Filtrage strict
                    if self.strict_filter and not self.is_finance_relevant(title):
                        self.rejected_count += 1
                        continue
                    
                    link = result.find('a', href=True)
                    url = urljoin('https://www.sciencedirect.com', link['href']) if link else ""
                    
                    # Vérifier si open access
                    is_open = bool(result.find(text=re.compile(r'open access|Open Access', re.I)) or
                                   result.find(class_=re.compile(r'open-access|openAccess')))
                    
                    if open_access_only and is_open:
                        open_access_count += 1
                    
                    article = {
                        'source': 'J Banking Finance',
                        'article_id': None,
                        'title': title,
                        'authors': [],
                        'summary': '',
                        'published': '',
                        'url': url,
                        'pdf_url': None,
                        'pdf_path': None,
                        'open_access': is_open
                    }
                    
                    self.results.append(article)
                    count += 1
                except:
                    continue
            
            print(f"✅ J Banking Finance: {count} articles ({open_access_count} Open Access)")
            
        except Exception as e:
            print(f"❌ Erreur J Banking Finance: {e}")
    
    def scrape_ieee(self, keywords="machine learning finance", max_results=50):
        """6. IEEE Xplore - Mixed private/public articles
        URL ref: https://ieeexplore.ieee.org/popular/all
        """
        print(f"\n{'='*60}")
        print(f"⚡ 6. SCRAPING IEEE Xplore")
        print(f"{'='*60}")
        print(f"Mots-clés: {keywords}")
        
        # URL de recherche IEEE
        search_url = f"https://ieeexplore.ieee.org/search/searchresult.jsp?queryText={quote(keywords)}&highlight=true&returnType=SEARCH&matchPubs=true&rowsPerPage=50"
        count = 0
        
        try:
            response = requests.get(search_url, headers=self.headers, timeout=30)
            soup = BeautifulSoup(response.content, 'html.parser')
            
            for result in soup.find_all(['div', 'xpl-results-item'], class_=re.compile(r'result|List-results')):
                try:
                    title_elem = result.find(['h2', 'h3', 'a'], class_=re.compile(r'title|result'))
                    if not title_elem:
                        title_elem = result.find('a')
                    if not title_elem:
                        continue
                    
                    title = title_elem.get_text(strip=True)
                    if len(title) < 10:
                        continue
                    
                    # Filtrage strict
                    if self.strict_filter and not self.is_finance_relevant(title):
                        self.rejected_count += 1
                        continue
                    
                    link = result.find('a', href=True)
                    url = urljoin('https://ieeexplore.ieee.org', link['href']) if link else ""
                    
                    # Détecter Open Access
                    is_open = bool(result.find(text=re.compile(r'open access', re.I)))
                    
                    article = {
                        'source': 'IEEE',
                        'article_id': None,
                        'title': title,
                        'authors': [],
                        'summary': '',
                        'published': '',
                        'url': url,
                        'pdf_url': None,
                        'pdf_path': None,
                        'open_access': is_open
                    }
                    
                    self.results.append(article)
                    count += 1
                    
                    if count >= max_results:
                        break
                except:
                    continue
            
            print(f"✅ IEEE: {count} articles récupérés")
            
        except Exception as e:
            print(f"❌ Erreur IEEE: {e}")
    
    def scrape_jmlr(self, filter_finance=True):
        """7. Journal of Machine Learning Research - Core AI with finance applicability
        URL ref: https://www.jmlr.org/
        """
        print(f"\n{'='*60}")
        print(f"🤖 7. SCRAPING JMLR")
        print(f"{'='*60}")
        print(f"   🔍 Mode: {'Filtrage finance activé' if filter_finance else 'Tous les articles ML'}")
        
        base_url = "https://www.jmlr.org/papers/"
        count = 0
        
        try:
            response = requests.get(base_url, headers=self.headers, timeout=30)
            soup = BeautifulSoup(response.content, 'html.parser')
            
            for item in soup.find_all('dt'):
                try:
                    title_elem = item.find('a')
                    if not title_elem:
                        continue
                    
                    title = title_elem.get_text(strip=True)
                    
                    # Pour JMLR, on peut filter ou pas selon l'option
                    if filter_finance and self.strict_filter and not self.is_finance_relevant(title):
                        self.rejected_count += 1
                        continue
                    
                    url = urljoin(base_url, title_elem['href'])
                    
                    dd = item.find_next('dd')
                    pdf_link = dd.find('a', string=re.compile(r'pdf', re.I)) if dd else None
                    if not pdf_link:
                        pdf_link = dd.find('a', href=re.compile(r'\.pdf')) if dd else None
                    pdf_url = urljoin(base_url, pdf_link['href']) if pdf_link else None
                    
                    article = {
                        'source': 'JMLR',
                        'article_id': None,
                        'title': title,
                        'authors': [],
                        'summary': '',
                        'published': '',
                        'url': url,
                        'pdf_url': pdf_url,
                        'pdf_path': None
                    }
                    
                    if self.download_pdfs and pdf_url:
                        pdf_path = self.download_pdf(pdf_url, title, 'jmlr')
                        article['pdf_path'] = pdf_path
                        time.sleep(2)
                    
                    self.results.append(article)
                    count += 1
                    
                    if count >= 50:
                        break
                except:
                    continue
            
            print(f"✅ JMLR: {count} articles récupérés")
            
        except Exception as e:
            print(f"❌ Erreur JMLR: {e}")
    
    def scrape_researchgate(self, keywords="AI finance", max_results=50):
        """8. ResearchGate - Recherches AI et Finance
        URL ref: https://www.researchgate.net/
        """
        print(f"\n{'='*60}")
        print(f"🔬 8. SCRAPING ResearchGate")
        print(f"{'='*60}")
        print(f"Mots-clés: {keywords}")
        
        base_url = "https://www.researchgate.net/search/publication"
        params = {'q': keywords}
        count = 0
        
        try:
            response = requests.get(base_url, params=params, 
                                  headers=self.headers, timeout=30)
            soup = BeautifulSoup(response.content, 'html.parser')
            
            for item in soup.find_all(['div', 'article', 'li'], class_=re.compile(r'publication|research-item|nova')):
                try:
                    title_elem = item.find(['h3', 'h4', 'a'], class_=re.compile(r'title|publication'))
                    if not title_elem:
                        title_elem = item.find('a')
                    if not title_elem:
                        continue
                    
                    title = title_elem.get_text(strip=True)
                    if len(title) < 10:
                        continue
                    
                    # Filtrage strict
                    if self.strict_filter and not self.is_finance_relevant(title):
                        self.rejected_count += 1
                        continue
                    
                    link = item.find('a', href=True)
                    url = urljoin('https://www.researchgate.net', link['href']) if link else ""
                    
                    article = {
                        'source': 'ResearchGate',
                        'article_id': None,
                        'title': title,
                        'authors': [],
                        'summary': '',
                        'published': '',
                        'url': url,
                        'pdf_url': None,
                        'pdf_path': None
                    }
                    
                    self.results.append(article)
                    count += 1
                    
                    if count >= max_results:
                        break
                except:
                    continue
            
            print(f"✅ ResearchGate: {count} articles récupérés")
            
        except Exception as e:
            print(f"❌ Erreur ResearchGate: {e}")
    
    def scrape_all_platforms(self, keywords_list=None, target_articles=1000):
        """SCRAPE TOUTES LES 8 PLATEFORMES - VERSION 1000+ ARTICLES
        
        Args:
            keywords_list: Liste de mots-clés (None = liste étendue par défaut)
            target_articles: Objectif minimum d'articles (défaut: 1000)
        """
        if keywords_list is None:
            # Liste étendue de 20 mots-clés pour maximiser les résultats
            keywords_list = [
                # Machine Learning & Finance
                "machine learning finance",
                "deep learning trading",
                "neural network stock prediction",
                "reinforcement learning portfolio",
                "LSTM stock market",
                # AI & Trading
                "artificial intelligence trading",
                "algorithmic trading machine learning",
                "high frequency trading AI",
                "automated trading neural network",
                "quant trading deep learning",
                # Risk & Fraud
                "credit risk machine learning",
                "fraud detection deep learning",
                "financial risk prediction",
                "market risk neural network",
                # NLP & Finance
                "NLP financial news",
                "sentiment analysis stock",
                "financial text mining",
                "LLM finance",
                # Crypto & Blockchain
                "cryptocurrency prediction machine learning",
                "bitcoin price forecasting neural network"
            ]
        
        print("\n" + "="*80)
        print(f"🚀 SCRAPING MASSIF - OBJECTIF: {target_articles}+ ARTICLES")
        print("="*80)
        print(f"📊 Nombre de mots-clés: {len(keywords_list)}")
        print(f"📚 Plateformes: 8 (arXiv, SSRN, Scholar, JFDS, Banking, IEEE, JMLR, RG)")
        print(f"🔒 Filtrage strict: {'ACTIVÉ' if self.strict_filter else 'DÉSACTIVÉ'}")
        print(f"🔄 Déduplication: ACTIVÉE")
        print("="*80)
        
        for i, keywords in enumerate(keywords_list, 1):
            print(f"\n🔍 CYCLE {i}/{len(keywords_list)}: {keywords}")
            print(f"   Articles actuels: {len(self.results)} | Objectif: {target_articles}")
            print("="*80)
            
            # 1. arXiv - 100 articles par mot-clé
            self.scrape_arxiv(keywords, max_results=100)
            time.sleep(2)
            
            # 2. SSRN - 5 pages
            self.scrape_ssrn(keywords, max_pages=5)
            time.sleep(2)
            
            # 3. Google Scholar - 30 articles
            self.scrape_google_scholar(keywords, max_results=30)
            time.sleep(3)
            
            # 4. JFDS
            self.scrape_jfds(keywords)
            time.sleep(2)
            
            # 5. Banking Finance
            self.scrape_banking_finance(keywords)
            time.sleep(2)
            
            # 6. IEEE - 50 articles
            self.scrape_ieee(keywords, max_results=50)
            time.sleep(2)
            
            # 7. JMLR (une fois seulement)
            if i == 1:
                self.scrape_jmlr()
                time.sleep(2)
            
            # 8. ResearchGate - 50 articles
            self.scrape_researchgate(keywords, max_results=50)
            time.sleep(2)
            
            # Vérifier si objectif atteint
            if len(self.results) >= target_articles:
                print(f"\n✅ Objectif de {target_articles} articles atteint!")
                break
        
        # Supprimer les doublons finaux
        duplicates_removed = self.remove_duplicates()
        
        print("\n" + "="*80)
        print("✅ SCRAPING TERMINÉ!")
        print("="*80)
        print(f"📊 Total articles uniques: {len(self.results)}")
        print(f"🔄 Doublons supprimés: {duplicates_removed}")
        print(f"🚫 Articles rejetés (hors sujet): {self.rejected_count}")
        
        # Compter PDFs
        pdfs_downloaded = sum(1 for r in self.results if r.get('pdf_path'))
        print(f"📥 PDFs téléchargés: {pdfs_downloaded}")
        print("="*80)
    
    def save_results(self, filename='articles_ia_finance_complet'):
        """Sauvegarder tous les résultats"""
        if not self.results:
            print("⚠️  Aucun résultat à sauvegarder")
            return
        
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        # CSV
        df = pd.DataFrame(self.results)
        csv_file = f'{filename}_{timestamp}.csv'
        df.to_csv(csv_file, index=False, encoding='utf-8-sig')
        print(f"\n💾 CSV sauvegardé: {csv_file}")
        
        # JSON
        json_file = f'{filename}_{timestamp}.json'
        with open(json_file, 'w', encoding='utf-8') as f:
            json.dump(self.results, f, indent=2, ensure_ascii=False)
        print(f"💾 JSON sauvegardé: {json_file}")
        
        # Index HTML
        if self.download_pdfs:
            self.create_pdf_index(filename, timestamp)
        
        # Statistiques détaillées
        print(f"\n{'='*60}")
        print("📊 STATISTIQUES PAR PLATEFORME:")
        print(f"{'='*60}")
        for source in sorted(df['source'].unique()):
            total = len(df[df['source'] == source])
            pdfs = len(df[(df['source'] == source) & (df['pdf_path'].notna())])
            print(f"   {source:20s}: {total:4d} articles ({pdfs:3d} PDFs)")
        print(f"{'='*60}")
        print(f"   {'TOTAL':20s}: {len(df):4d} articles")
        print(f"{'='*60}")
    
    def create_pdf_index(self, filename, timestamp):
        """Créer index HTML interactif"""
        html_file = f'{filename}_index_{timestamp}.html'
        
        html = f"""<!DOCTYPE html>
<html><head><meta charset="utf-8">
<title>Index Articles IA Finance - {timestamp}</title>
<style>
body {{font-family: Arial; margin: 20px; background: #f5f5f5;}}
h1 {{color: #2c3e50; text-align: center;}}
.stats {{background: #3498db; color: white; padding: 15px; border-radius: 5px; margin: 20px 0;}}
.article {{background: white; border-left: 4px solid #3498db; padding: 15px; margin: 10px 0; border-radius: 5px; box-shadow: 0 2px 4px rgba(0,0,0,0.1);}}
.title {{font-weight: bold; font-size: 1.1em; color: #2980b9; margin-bottom: 10px;}}
.source {{display: inline-block; background: #27ae60; color: white; padding: 3px 8px; border-radius: 3px; font-size: 0.85em; margin: 5px 5px 5px 0;}}
.authors {{color: #7f8c8d; font-size: 0.9em; margin: 5px 0;}}
.pdf-link {{background: #e74c3c; color: white; padding: 8px 15px; text-decoration: none; border-radius: 3px; display: inline-block; margin: 10px 5px 0 0;}}
.pdf-link:hover {{background: #c0392b;}}
.url-link {{background: #95a5a6; color: white; padding: 8px 15px; text-decoration: none; border-radius: 3px; display: inline-block; margin: 10px 5px 0 0;}}
.no-pdf {{color: #e74c3c; font-weight: bold;}}
.filter {{margin: 20px 0; padding: 15px; background: white; border-radius: 5px;}}
.filter input {{padding: 10px; width: 300px; font-size: 1em; border: 2px solid #3498db; border-radius: 3px;}}
</style>
<script>
function filterArticles() {{
    const input = document.getElementById('searchInput').value.toLowerCase();
    const articles = document.getElementsByClassName('article');
    for (let article of articles) {{
        const text = article.textContent.toLowerCase();
        article.style.display = text.includes(input) ? '' : 'none';
    }}
}}
</script>
</head><body>
<h1>📚 Index Complet - Articles IA & Finance</h1>
<div class="stats">
<p><strong>Généré le:</strong> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
<p><strong>Total articles:</strong> {len(self.results)}</p>
<p><strong>PDFs téléchargés:</strong> {sum(1 for r in self.results if r.get('pdf_path'))}</p>
</div>
<div class="filter">
<input type="text" id="searchInput" onkeyup="filterArticles()" placeholder="🔍 Filtrer par mot-clé...">
</div>
<hr>
"""
        
        for i, article in enumerate(self.results, 1):
            authors = ', '.join(article['authors'][:3]) if article['authors'] else 'N/A'
            if len(article['authors']) > 3:
                authors += ' et al.'
            
            html += f"""
<div class="article">
<div class="title">{i}. {article['title']}</div>
<span class="source">{article['source']}</span>
<div class="authors">Auteurs: {authors}</div>
<div>Date: {article['published'] or 'N/A'}</div>
"""
            
            if article['pdf_path']:
                html += f'<a href="{article["pdf_path"]}" class="pdf-link" target="_blank">📄 Ouvrir PDF</a>'
            else:
                html += '<span class="no-pdf">❌ PDF non disponible</span>'
            
            if article['url']:
                html += f' <a href="{article["url"]}" class="url-link" target="_blank">🔗 Source</a>'
            
            html += "</div>"
        
        html += "</body></html>"
        
        with open(html_file, 'w', encoding='utf-8') as f:
            f.write(html)
        
        print(f"📄 Index HTML créé: {html_file}")


# ==================== UTILISATION ====================

if __name__ == "__main__":
    print("🎯 SCRAPER MASSIF - OBJECTIF 1000+ ARTICLES IA & FINANCE")
    print("="*80)
    print("🔒 Mode: FILTRAGE STRICT + DÉDUPLICATION AUTOMATIQUE")
    print("="*80)
    
    # Créer le scraper avec téléchargement PDF ET filtrage strict
    scraper = FinanceAIScraper(download_pdfs=True, strict_filter=True)
    
    # Lancer le scraping avec objectif de 1000 articles
    # Les 20 mots-clés par défaut seront utilisés automatiquement
    scraper.scrape_all_platforms(target_articles=1000)
    
    # Sauvegarder tous les résultats
    scraper.save_results('articles_1000_ia_finance')
    
    # Afficher aperçu des résultats
    print("\n" + "="*80)
    print("📄 APERÇU DES RÉSULTATS (15 premiers articles):")
    print("="*80)
    
    for i, article in enumerate(scraper.results[:15], 1):
        title_display = article['title'][:65] + "..." if len(article['title']) > 65 else article['title']
        print(f"\n{i}. {title_display}")
        print(f"   📚 Source: {article['source']}")
        if article['pdf_path']:
            print(f"   ✅ PDF téléchargé")
        else:
            print(f"   ❌ PDF non disponible")
    
    print("\n" + "="*80)
    print("🎉 SCRAPING TERMINÉ!")
    print("="*80)
    print(f"📊 Total articles uniques: {len(scraper.results)}")
    print(f"📥 PDFs téléchargés: {sum(1 for r in scraper.results if r.get('pdf_path'))}")
    print(f"🔄 Doublons supprimés: {scraper.duplicate_count}")
    print(f"🚫 Articles rejetés (hors sujet): {scraper.rejected_count}")
    print("\n💡 Consulte le fichier HTML pour naviguer facilement dans tous les articles!")
    print("="*80)
