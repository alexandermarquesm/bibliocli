import sys
import os
import requests
from typing import List

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../..')))

from bibliocli.domain.entities import BookSearchResult
from bibliocli.application.interfaces import BookSearchProvider, BookDownloadProvider

class WikisourceProvider(BookSearchProvider, BookDownloadProvider):
    def _get_wikidata_info(self, qids: List[str], domain: str) -> dict:
        """
        Busca Autores (P50/P170) e Imagens (P18) no Wikidata em lote.
        """
        if not qids: return {}
        
        results = {}
        headers = {'User-Agent': 'MeuLeitorApp/1.0 (dev@exemplo.com)'}
        try:
            api_url = "https://www.wikidata.org/w/api.php"
            params = {
                "action": "wbgetentities",
                "ids": "|".join(qids),
                "props": "claims|labels",
                "languages": domain, 
                "format": "json"
            }
            r = requests.get(api_url, params=params, headers=headers).json()
            entities = r.get("entities", {})
            
            author_qids_to_fetch = []
            entity_map = {} 
            
            for qid, data in entities.items():
                results[qid] = {"author": None, "cover_url": None}
                claims = data.get("claims", {})
                
                # --- CAPA (P18) ---
                if "P18" in claims:
                    img_name = claims["P18"][0].get("mainsnak", {}).get("datavalue", {}).get("value")
                    if img_name:
                         import hashlib
                         safe_name = img_name.replace(" ", "_")
                         md5 = hashlib.md5(safe_name.encode('utf-8')).hexdigest()
                         results[qid]["cover_url"] = f"https://upload.wikimedia.org/wikipedia/commons/thumb/{md5[0]}/{md5[:2]}/{safe_name}/400px-{safe_name}"

                # --- AUTOR (P50 ou P170) ---
                author_claim = claims.get("P50") or claims.get("P170")
                if author_claim:
                    auth_qid = author_claim[0].get("mainsnak", {}).get("datavalue", {}).get("value", {}).get("id")
                    if auth_qid:
                        entity_map[qid] = auth_qid
                        author_qids_to_fetch.append(auth_qid)

            if author_qids_to_fetch:
                params_auth = {
                    "action": "wbgetentities",
                    "ids": "|".join(list(set(author_qids_to_fetch))),
                    "props": "labels",
                    "languages": f"{domain}|en",
                    "format": "json"
                }
                r_auth = requests.get(api_url, params=params_auth, headers=headers).json()
                auth_entities = r_auth.get("entities", {})
                for book_qid, auth_qid in entity_map.items():
                    auth_data = auth_entities.get(auth_qid, {})
                    label_data = auth_data.get("labels", {}).get(domain) or auth_data.get("labels", {}).get("en")
                    if label_data:
                        results[book_qid]["author"] = label_data["value"]
        except Exception: pass
        return results

    def search(self, query: str) -> List[BookSearchResult]:
        results = []
        headers = {'User-Agent': 'MeuLeitorApp/1.0 (dev@exemplo.com)'}
        wikisource_logo = "https://upload.wikimedia.org/wikipedia/commons/thumb/4/4c/Wikisource-logo.svg/400px-Wikisource-logo.svg.png"
        
        # --- BUSCAR EM PORTUGUÊS (PT) ---
        try:
            r_pt = requests.get(
                "https://pt.wikisource.org/w/api.php",
                params={
                    "action": "query", 
                    "list": "search", 
                    "srsearch": query, 
                    "format": "json"
                },
                headers=headers
            ).json()
            search_items_raw = r_pt.get("query", {}).get("search", [])[:10]
            pageids = [str(item["pageid"]) for item in search_items_raw]
            
            qids = {}
            valid_pageids = set()
            if pageids:
                r_props = requests.get(
                    "https://pt.wikisource.org/w/api.php",
                    params={
                        "action": "query",
                        "pageids": "|".join(pageids),
                        "prop": "pageprops|categories",
                        "cllimit": "max",
                        "format": "json"
                    },
                    headers=headers
                ).json()
                pages = r_props.get("query", {}).get("pages", {})
                for pid, pdata in pages.items():
                    cats = [c.get("title", "").lower() for c in pdata.get("categories", [])]
                    skip = any("desambiguação" in c or "listas de versões" in c or "sem fichas de dados" in c for c in cats)
                    
                    if not skip:
                        valid_pageids.add(str(pid))
                        qid = pdata.get("pageprops", {}).get("wikibase_item")
                        if qid: qids[int(pid)] = qid

            search_items = [item for item in search_items_raw if str(item["pageid"]) in valid_pageids][:4]

            wikidata_payload = self._get_wikidata_info(list(qids.values()), "pt")

            for item in search_items:
                pid = item["pageid"]
                qid = qids.get(pid)
                w_data = wikidata_payload.get(qid, {}) if qid else {}
                author = w_data.get("author") or "Autor Desconhecido"
                
                title = item["title"]
                import re
                year_match = re.search(r'\((\d{4})\)', title)
                year = year_match.group(1) if year_match else None
                
                results.append(BookSearchResult(
                    source="Wikisource (PT)",
                    title=title,
                    author=author,
                    language="pt-br",
                    link=f"https://pt.wikisource.org/wiki/{title.replace(' ', '_')}",
                    year=year,
                    cover_url=wikisource_logo
                ))
        except Exception: pass
        
        # --- BUSCAR EM INGLÊS (EN) ---
        try:
            r_en = requests.get(
                "https://en.wikisource.org/w/api.php",
                params={
                    "action": "query", 
                    "list": "search", 
                    "srsearch": query, 
                    "format": "json"
                },
                headers=headers
            ).json()
            search_items_en_raw = r_en.get("query", {}).get("search", [])[:10]
            pageids_en = [str(item["pageid"]) for item in search_items_en_raw]
            
            qids_en = {}
            valid_pageids_en = set()
            if pageids_en:
                r_props_en = requests.get(
                    "https://en.wikisource.org/w/api.php",
                    params={
                        "action": "query",
                        "pageids": "|".join(pageids_en),
                        "prop": "pageprops|categories",
                        "cllimit": "max",
                        "format": "json"
                    },
                    headers=headers
                ).json()
                pages_en = r_props_en.get("query", {}).get("pages", {})
                for pid, pdata in pages_en.items():
                    cats = [c.get("title", "").lower() for c in pdata.get("categories", [])]
                    skip = any("disambiguation" in c or "versions pages" in c for c in cats)
                    
                    if not skip:
                        valid_pageids_en.add(str(pid))
                        qid = pdata.get("pageprops", {}).get("wikibase_item")
                        if qid: qids_en[int(pid)] = qid

            search_items_en = [item for item in search_items_en_raw if str(item["pageid"]) in valid_pageids_en][:4]

            wikidata_payload_en = self._get_wikidata_info(list(qids_en.values()), "en")

            for item in search_items_en:
                pid = item["pageid"]
                qid = qids_en.get(pid)
                w_data = wikidata_payload_en.get(qid, {}) if qid else {}
                author = w_data.get("author") or "Autor Desconhecido"
                
                title = item["title"]
                import re
                year_match = re.search(r'\((\d{4})\)', title)
                year = year_match.group(1) if year_match else None
                
                results.append(BookSearchResult(
                    source="Wikisource (EN)",
                    title=title,
                    author=author,
                    language="en",
                    link=f"https://en.wikisource.org/wiki/{title.replace(' ', '_')}",
                    year=year,
                    cover_url=wikisource_logo
                ))
        except Exception: pass
            
        return results

    def search_by_author(self, author: str) -> List[BookSearchResult]:
        """No Wikisource a busca textual já funciona para cruzar nomes de autores com obras."""
        return self.search(author)

    def get_popular_books(self) -> List[BookSearchResult]:
        """Wikisource não possui API nativa simples para 'mais populares'."""
        return []

    def can_download(self, url: str) -> bool:
        return "wikisource.org/wiki/" in url

    def _clean_html(self, html: str) -> str:
        """Remove tags HTML simples para extrair o texto."""
        import re
        # Remove tags script e style
        text = re.sub(r'<(script|style).*?>.*?</\1>', '', html, flags=re.DOTALL | re.IGNORECASE)
        # Remove todas as outras tags
        text = re.sub(r'<.*?>', ' ', text)
        # Normaliza espaços
        text = re.sub(r'\s+', ' ', text).strip()
        return text

    def download(self, url: str, destiny_path: str) -> bool:
        """
        Baixa o texto do Wikisource. Usa a API de exportação WSExport para
        garantir um arquivo .txt perfeitamente formatado.
        """
        import urllib.parse
        try:
            # Extrair título já formatado para a URL (com underlines)
            title_quoted = url.split("/wiki/")[-1]
            domain = "pt" if "pt.wikisource.org" in url else "en"
            
            headers = {'User-Agent': 'MeuLeitorApp/1.0 (dev@exemplo.com)'}
            export_url = f"https://ws-export.wmcloud.org/?format=txt&lang={domain}&page={title_quoted}"
            
            r = requests.get(export_url, headers=headers)
            
            if r.status_code == 200:
                text_content = r.text
                
                # O WSExport pode retornar HTML caso falhe em renderizar uma página não suportada.
                if "<html" in text_content[:500].lower():
                    print(f"Aviso: O WSExport retornou uma página de erro HTML para '{title_quoted}'.")
                    return False
                    
                with open(destiny_path, "w", encoding="utf-8") as f:
                    f.write(text_content)
                return True
            else:
                print(f"Aviso: O WSExport falhou com status {r.status_code} para '{title_quoted}'.")
                return False

        except Exception as e:
            print(f"Erro ao processar download do Wikisource: {e}")
            
        return False

    def get_info(self, url: str) -> BookSearchResult:
        import urllib.parse
        title_quoted = url.split("/wiki/")[-1]
        title = urllib.parse.unquote(title_quoted)
        domain = "pt" if "pt.wikisource.org" in url else "en"
        wikisource_logo = "https://upload.wikimedia.org/wikipedia/commons/thumb/4/4c/Wikisource-logo.svg/400px-Wikisource-logo.svg.png"
        
        headers = {'User-Agent': 'MeuLeitorApp/1.0 (dev@exemplo.com)'}
        api_url = f"https://{domain}.wikisource.org/w/api.php"
        
        qid = None
        try:
            # Buscar apenas QID para o Autor
            r = requests.get(
                api_url, 
                params={
                    "action": "query",
                    "titles": title,
                    "prop": "pageprops",
                    "format": "json"
                },
                headers=headers
            ).json()
            pages = r.get("query", {}).get("pages", {})
            for pid, pdata in pages.items():
                qid = pdata.get("pageprops", {}).get("wikibase_item")
        except Exception: pass

        # Hidratação do Autor via Wikidata
        author = "Autor Desconhecido"
        if qid:
            w_data = self._get_wikidata_info([qid], domain).get(qid, {})
            if w_data.get("author"): author = w_data["author"]

        import re
        year_match = re.search(r'\((\d{4})\)', title)
        year = year_match.group(1) if year_match else None
        
        return BookSearchResult(
            source=f"Wikisource ({domain.upper()})",
            title=title,
            author=author,
            language=domain,
            link=url,
            year=year,
            cover_url=wikisource_logo
        )
