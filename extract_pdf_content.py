"""
Script d'extraction des abstracts et keywords depuis les PDFs articles
"""

import fitz  # PyMuPDF
import json
import re
import os
from pathlib import Path
from datetime import datetime

class PDFContentExtractor:
    """Extracteur de contenu pour les PDFs académiques"""
    
    def __init__(self, pdf_dir="pdfs_articles/arxiv", index_file="pdfs_articles_arxiv_index.json"):
        self.pdf_dir = Path(pdf_dir)
        self.index_file = Path(index_file)
        self.results = []
        
    def extract_text_from_pdf(self, pdf_path, max_pages=3):
        """Extraire le texte des premières pages du PDF"""
        try:
            doc = fitz.open(pdf_path)
            text = ""
            for page_num in range(min(max_pages, len(doc))):
                page = doc[page_num]
                text += page.get_text()
            doc.close()
            return text
        except Exception as e:
            print(f"   ❌ Erreur lecture PDF: {e}")
            return None
    
    def extract_abstract(self, text):
        """Extraire l'abstract du texte"""
        if not text:
            return None
        
        # Patterns pour trouver l'abstract
        patterns = [
            # Pattern standard: Abstract suivi de texte jusqu'à Introduction ou Keywords
            r'(?:^|\n)\s*Abstract[:\s]*\n?(.*?)(?=\n\s*(?:1\.?\s*Introduction|Keywords|Index Terms|I\.\s+Introduction|1\s+Introduction|\n\s*\d+\.\s+))',
            # Pattern alternatif avec Abstract en majuscules
            r'(?:^|\n)\s*ABSTRACT[:\s]*\n?(.*?)(?=\n\s*(?:1\.?\s*Introduction|Keywords|Index Terms|I\.\s+Introduction|INTRODUCTION|\n\s*\d+\.\s+))',
            # Pattern simple si rien d'autre ne marche
            r'(?:^|\n)\s*Abstract[:\s]*\n?(.{100,2000}?)(?=\n\n|\n\s*\n)',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text, re.DOTALL | re.IGNORECASE)
            if match:
                abstract = match.group(1).strip()
                # Nettoyer l'abstract
                abstract = re.sub(r'\s+', ' ', abstract)
                abstract = abstract.strip()
                if len(abstract) > 50:  # Minimum 50 caractères
                    return abstract[:3000]  # Maximum 3000 caractères
        
        return None
    
    def extract_keywords(self, text):
        """Extraire les keywords du texte"""
        if not text:
            return []
        
        # Patterns pour trouver les keywords
        patterns = [
            r'(?:Keywords|Key words|Key-words|Index Terms)[:\s—–-]*([^\n]+)',
            r'(?:Keywords|Key words)[:\s]*\n([^\n]+)',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                keywords_text = match.group(1)
                # Séparer par virgule, point-virgule ou tiret
                keywords = re.split(r'[,;•·]', keywords_text)
                keywords = [kw.strip().strip('.').strip() for kw in keywords]
                keywords = [kw for kw in keywords if len(kw) > 2 and len(kw) < 100]
                if keywords:
                    return keywords[:15]  # Maximum 15 keywords
        
        return []
    
    def process_all_pdfs(self):
        """Traiter tous les PDFs et extraire abstract/keywords"""
        print(f"\n{'='*60}")
        print(f"📚 EXTRACTION ABSTRACTS & KEYWORDS")
        print(f"{'='*60}")
        
        # Charger l'index existant
        if self.index_file.exists():
            with open(self.index_file, 'r', encoding='utf-8') as f:
                articles = json.load(f)
            print(f"📄 {len(articles)} articles dans l'index")
        else:
            print("❌ Fichier index non trouvé")
            return
        
        # Traiter chaque article
        processed = 0
        abstracts_found = 0
        keywords_found = 0
        
        for i, article in enumerate(articles):
            pdf_path = article.get('pdf_path')
            if not pdf_path:
                continue
            
            pdf_full_path = Path(pdf_path)
            if not pdf_full_path.exists():
                continue
            
            print(f"\n[{i+1}/{len(articles)}] {article.get('title', 'Unknown')[:60]}...")
            
            # Extraire le texte
            text = self.extract_text_from_pdf(pdf_full_path)
            
            if text:
                # Extraire abstract
                abstract = self.extract_abstract(text)
                if abstract:
                    article['abstract'] = abstract
                    abstracts_found += 1
                    print(f"   ✅ Abstract: {len(abstract)} caractères")
                else:
                    article['abstract'] = None
                    print(f"   ⚠️ Abstract non trouvé")
                
                # Extraire keywords
                keywords = self.extract_keywords(text)
                if keywords:
                    article['keywords'] = keywords
                    keywords_found += 1
                    print(f"   ✅ Keywords: {keywords[:3]}...")
                else:
                    article['keywords'] = []
                    print(f"   ⚠️ Keywords non trouvés")
            else:
                article['abstract'] = None
                article['keywords'] = []
            
            processed += 1
        
        # Sauvegarder l'index mis à jour
        output_file = self.index_file.parent / f"pdfs_articles_arxiv_index_with_abstracts.json"
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(articles, f, indent=2, ensure_ascii=False)
        
        # Aussi mettre à jour le fichier original
        with open(self.index_file, 'w', encoding='utf-8') as f:
            json.dump(articles, f, indent=2, ensure_ascii=False)
        
        print(f"\n{'='*60}")
        print(f"✅ EXTRACTION TERMINÉE!")
        print(f"{'='*60}")
        print(f"📊 PDFs traités: {processed}")
        print(f"📝 Abstracts trouvés: {abstracts_found} ({100*abstracts_found/max(1,processed):.1f}%)")
        print(f"🏷️  Keywords trouvés: {keywords_found} ({100*keywords_found/max(1,processed):.1f}%)")
        print(f"💾 Index sauvegardé: {output_file}")
        print(f"{'='*60}")


if __name__ == "__main__":
    extractor = PDFContentExtractor()
    extractor.process_all_pdfs()
