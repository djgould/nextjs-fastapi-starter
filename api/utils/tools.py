"""Helper functions for handling tool operations in the FastAPI router."""
from datetime import datetime
import json
import pytz
import requests
from requests.adapters import HTTPAdapter, Retry
from firecrawl import FirecrawlApp
import logging
import xml.etree.ElementTree as ElementTree
from fastapi import HTTPException
import os

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Request timeout settings
REQUEST_TIMEOUT = 60  # seconds

# Configure requests session with retries and longer timeouts
session = requests.Session()
retries = Retry(
    total=3,
    backoff_factor=0.5,
    status_forcelist=[500, 502, 503, 504]
)
adapter = HTTPAdapter(
    max_retries=retries,
    pool_connections=20,
    pool_maxsize=20
)
session.mount('http://', adapter)
session.mount('https://', adapter)

# NCBI API settings
NCBI_PARAMS = {k: v for k, v in {
    "api_key": os.getenv("NCBI_API_KEY"),
    "tool": os.getenv("NCBI_TOOL_NAME", "genomics-assistant"),
    "email": os.getenv("NCBI_EMAIL")
}.items() if v is not None}

def get_weather_data(lat: float, lon: float, unit: str = "celsius") -> dict:
    """Get current weather for a specified location."""
    weather_url = "https://api.open-meteo.com/v1/forecast"
    weather_params = {
        "latitude": lat,
        "longitude": lon,
        "hourly": "temperature_2m",
        "format": "json",
        "timeformat": "unixtime"
    }
    
    response = session.get(
        weather_url,
        params=weather_params,
        timeout=REQUEST_TIMEOUT
    )
    if response.status_code != 200:
        raise HTTPException(
            status_code=response.status_code,
            detail="Weather data not available"
        )
    
    data = response.json()
    
    # Get current temperature (first value in the hourly data)
    current_temp = data["hourly"]["temperature_2m"][0]
    
    # Convert to fahrenheit if requested
    if unit == "fahrenheit":
        current_temp = (current_temp * 9/5) + 32
    
    return {
        "coordinates": {"lat": lat, "lon": lon},
        "temperature": current_temp,
        "unit": unit,
        "elevation": data["elevation"]
    }

def get_time_data(timezone: str) -> dict:
    """Get current time for a specified timezone."""
    try:
        tz = pytz.timezone(timezone)
        current_time = datetime.now(tz)
        return {
            "timezone": timezone,
            "time": current_time.isoformat()
        }
    except pytz.exceptions.UnknownTimeZoneError:
        raise HTTPException(
            status_code=400,
            detail=f"Unknown timezone: {timezone}"
        )

def google_search(query: str) -> dict:
    """Perform a Google search using Custom Search API."""
    api_key = os.getenv("GOOGLE_API_KEY")
    cx = os.getenv("GOOGLE_SEARCH_ENGINE_ID")
    
    if not api_key or not cx:
        raise HTTPException(
            status_code=500,
            detail="Google Search API not configured"
        )
    
    url = "https://www.googleapis.com/customsearch/v1"
    params = {
        "key": api_key,
        "cx": cx,
        "q": query,
        "num": 5  # Number of results to return
    }
    
    response = session.get(url, params=params, timeout=REQUEST_TIMEOUT)
    if response.status_code != 200:
        raise HTTPException(
            status_code=response.status_code,
            detail="Google search failed"
        )
    
    data = response.json()
    results = []
    
    for item in data.get("items", []):
        results.append({
            "title": item.get("title"),
            "link": item.get("link"),
            "snippet": item.get("snippet")
        })
    
    return {
        "query": query,
        "results": results
    }

def read_website(url: str) -> dict:
    """Read a website using Firecrawl."""
    api_key = os.getenv("FIRECRAWL_API_KEY")
    
    app = FirecrawlApp(api_key=api_key)
    
    try:
        scrape_status = app.scrape_url(
            url,
            params={'formats': ['markdown']}
        )
        logger.info(f"Scrape status: {scrape_status}")
        return {
            "url": scrape_status['metadata']['url'],
            "content": scrape_status['markdown'],
            "title": scrape_status['metadata'].get('title', ''),
            "description": scrape_status['metadata'].get('description', ''),
            "language": scrape_status['metadata'].get('language', ''),
            "scrape_id": scrape_status['metadata'].get('scrapeId', '')
        }
    except Exception as e:
        logger.error(f"Failed to read website: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to read website: {str(e)}"
        )

def get_pubmed_studies(query: str, max_results: int = 5) -> dict:
    """Get PubMed studies for a given query by searching for IDs and fetching study details."""
    logger.info(
        f"Starting PubMed search with query: {query}, max_results: {max_results}"
    )
    
    esearch_url = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi"
    params = {
        "db": "pubmed",
        "term": query,
        "retmax": str(max_results),
        "usehistory": "y",
        "retmode": "json",
        **NCBI_PARAMS
    }
    
    logger.info(f"PubMed search URL: {esearch_url}")
    logger.info(f"PubMed search params: {params}")
    logger.info(f"Using NCBI parameters: {NCBI_PARAMS}")
    
    try:
        logger.info("Making initial PubMed search request...")
        esearch_resp = session.get(
            esearch_url,
            params=params,
            timeout=REQUEST_TIMEOUT
        )
        logger.info(
            f"PubMed search response status: {esearch_resp.status_code}"
        )
        logger.info(
            f"PubMed search response headers: {dict(esearch_resp.headers)}"
        )
        logger.debug(f"PubMed search response body: {esearch_resp.text}")
        
        if esearch_resp.status_code != 200:
            logger.error(
                f"PubMed search failed with status {esearch_resp.status_code}"
            )
            logger.error(f"Error response: {esearch_resp.text}")
            raise HTTPException(
                status_code=esearch_resp.status_code,
                detail="PubMed esearch failed"
            )
        
        search_data = esearch_resp.json()
        logger.info(
            f"Successfully parsed PubMed search response: {search_data}"
        )
        
        ids = search_data.get("esearchresult", {}).get("idlist", [])
        logger.info(f"Found {len(ids)} PubMed IDs: {ids}")
        
        if not ids:
            logger.info("No PubMed entries found for the query")
            return {
                "studies": [],
                "total_count": 0,
                "showing": 0,
                "query": query
            }

        total_count = int(
            search_data.get("esearchresult", {}).get("count", "0")
        )
        logger.info(f"Total results available: {total_count}")
        
        efetch_url = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi"
        fetch_params = {
            "db": "pubmed",
            "id": ",".join(ids),
            "retmode": "xml",
            "rettype": "abstract",
            **NCBI_PARAMS
        }
        
        logger.info(f"PubMed fetch URL: {efetch_url}")
        logger.info(f"PubMed fetch params: {fetch_params}")
        
        logger.info("Making PubMed fetch request...")
        fetch_resp = session.get(
            efetch_url,
            params=fetch_params,
            timeout=REQUEST_TIMEOUT
        )
        logger.info(
            f"PubMed fetch response status: {fetch_resp.status_code}"
        )
        logger.info(
            f"PubMed fetch response headers: {dict(fetch_resp.headers)}"
        )
        logger.debug(f"PubMed fetch response body: {fetch_resp.text}")
        
        if fetch_resp.status_code != 200:
            logger.error(
                f"PubMed fetch failed with status {fetch_resp.status_code}"
            )
            logger.error(f"Error response: {fetch_resp.text}")
            raise HTTPException(
                status_code=fetch_resp.status_code,
                detail="PubMed efetch failed"
            )
        
        logger.info("Parsing XML response...")
        fetch_root = ElementTree.fromstring(fetch_resp.text)
        
        studies = []
        for article in fetch_root.findall(".//PubmedArticle"):
            article_node = article.find("MedlineCitation/Article")
            if article_node is None:
                logger.warning("Found PubmedArticle without Article node")
                continue
            
            pmid_node = article.find("MedlineCitation/PMID")
            pmid = pmid_node.text if pmid_node is not None else "No PMID"
            logger.info(f"Processing article PMID: {pmid}")
            
            title_node = article_node.find("ArticleTitle")
            title = title_node.text if title_node is not None else "No title"
            
            journal_node = article_node.find("Journal/Title")
            journal = (
                journal_node.text if journal_node is not None else "No journal"
            )
            
            pub_date = article_node.find("Journal/JournalIssue/PubDate/Year")
            if pub_date is None:
                pub_date = article_node.find(
                    "Journal/JournalIssue/PubDate/MedlineDate"
                )
            year = pub_date.text if pub_date is not None else "No year"
            
            abstract_node = article_node.find("Abstract/AbstractText")
            summary = (
                abstract_node.text if abstract_node is not None else "No abstract"
            )
            
            study_info = {
                "title": title,
                "journal": journal,
                "year": year,
                "summary": summary,
                "pmid": pmid
            }
            studies.append(study_info)
            logger.info(f"Successfully processed article {pmid}")
        
        result = {
            "studies": studies,
            "total_count": total_count,
            "showing": len(studies),
            "query": query
        }
        logger.info(
            f"Successfully processed {len(studies)} studies out of {total_count} total results"
        )
        return result
        
    except ElementTree.ParseError as e:
        logger.error(f"Failed to parse PubMed XML response: {str(e)}")
        logger.error(
            f"Response text (first 500 chars): {fetch_resp.text[:500] if 'fetch_resp' in locals() else 'No response'}"
        )
        raise HTTPException(
            status_code=500,
            detail="Failed to parse PubMed response"
        )
    except Exception as e:
        logger.error(f"Error processing PubMed data: {str(e)}", exc_info=True)
        logger.error(f"Error type: {type(e).__name__}")
        if hasattr(e, 'response'):
            logger.error(
                f"Response status: {e.response.status_code if e.response else 'No response'}"
            )
            logger.error(
                f"Response headers: {dict(e.response.headers) if e.response else 'No response'}"
            )
            logger.error(
                f"Response text: {e.response.text if e.response else 'No response'}"
            )
        raise HTTPException(
            status_code=500,
            detail="Error processing PubMed data"
        )

def get_genome_browser_data(gene: str) -> dict:
    """Get genomic coordinates for a gene from NCBI."""
    # First get gene info from NCBI
    esearch_url = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi"
    params = {
        "db": "gene",
        "term": f"{gene}[Gene Name] AND \"Homo sapiens\"[Organism]",
        "retmode": "json",
        **NCBI_PARAMS
    }
    
    logger.info(f"Searching NCBI Gene with params: {params}")
    response = session.get(esearch_url, params=params, timeout=REQUEST_TIMEOUT)
    if response.status_code != 200:
        logger.error(
            f"NCBI Gene search failed with status {response.status_code}: {response.text}"
        )
        raise HTTPException(
            status_code=response.status_code,
            detail="Failed to fetch gene data from NCBI"
        )
    
    data = response.json()
    gene_ids = data.get("esearchresult", {}).get("idlist", [])
    logger.info(f"Found gene IDs: {gene_ids}")
    
    if not gene_ids:
        raise HTTPException(
            status_code=404,
            detail=f"Gene {gene} not found in NCBI database"
        )
    
    # Get detailed gene info
    efetch_url = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi"
    params = {
        "db": "gene",
        "id": gene_ids[0],
        "retmode": "xml",
        **NCBI_PARAMS
    }
    
    logger.info(f"Fetching gene details with params: {params}")
    response = session.get(efetch_url, params=params, timeout=REQUEST_TIMEOUT)
    if response.status_code != 200:
        logger.error(
            f"NCBI Gene fetch failed with status {response.status_code}: {response.text}"
        )
        raise HTTPException(
            status_code=response.status_code,
            detail="Failed to fetch gene details from NCBI"
        )
    
    try:
        logger.info("Parsing XML response")
        root = ElementTree.fromstring(response.text)
        
        # Initialize variables
        chromosome = None
        start = None
        end = None
        
        # Look for Entrezgene
        entrezgene = root.find(".//Entrezgene")
        if entrezgene is not None:
            logger.info("Found Entrezgene element")
            
            # First try to find chromosome from BioSource
            biosource = entrezgene.find(".//BioSource")
            if biosource is not None:
                for subtype in biosource.findall(".//SubSource"):
                    if subtype.find("SubSource_subtype").get("value") == "chromosome":
                        chr_text = subtype.find("SubSource_name").text
                        logger.info(
                            f"Found chromosome from BioSource: {chr_text}"
                        )
                        if chr_text.isdigit() or chr_text.upper() in ["X", "Y"]:
                            chromosome = chr_text
                            break
            
            # If not found, try Gene-ref_maploc
            if chromosome is None:
                maploc = entrezgene.find(".//Gene-ref_maploc")
                if maploc is not None and maploc.text:
                    logger.info(f"Found map location: {maploc.text}")
                    # Map location is typically in format "17q21.31"
                    chr_text = maploc.text.strip()
                    chr_match = (
                        chr_text.split('q')[0]
                        .split('p')[0]
                        .split('.')[0]
                        .strip()
                    )
                    logger.info(
                        f"Extracted potential chromosome: {chr_match}"
                    )
                    if chr_match.isdigit() or chr_match.upper() in ["X", "Y"]:
                        chromosome = chr_match
                        logger.info(
                            f"Found chromosome from map location: {chromosome}"
                        )
            
            # Try to find coordinates from genomic location
            genomic_locs = entrezgene.findall(".//Gene-commentary")
            for loc in genomic_locs:
                type_node = loc.find("Gene-commentary_type")
                if type_node is not None and type_node.get("value") == "genomic":
                    coords = loc.find(".//Seq-interval")
                    if coords is not None:
                        start_node = coords.find("Seq-interval_from")
                        end_node = coords.find("Seq-interval_to")
                        if start_node is not None and end_node is not None:
                            start = start_node.text
                            end = end_node.text
                            logger.info(
                                f"Found coordinates - start: {start}, end: {end}"
                            )
                            break
        
        if chromosome is None or start is None or end is None:
            logger.error(
                f"Missing required data - chromosome: {chromosome}, start: {start}, end: {end}"
            )
            raise HTTPException(
                status_code=404,
                detail=f"Could not find complete location data for gene {gene}"
            )
        
        # Validate chromosome format
        if not (chromosome.isdigit() or chromosome.upper() in ["X", "Y"]):
            logger.error(f"Invalid chromosome format: {chromosome}")
            raise HTTPException(
                status_code=500,
                detail="Invalid chromosome format"
            )
        
        # Format coordinates with commas for thousands and ensure chromosome is numeric
        try:
            start_formatted = "{:,}".format(int(start))
            end_formatted = "{:,}".format(int(end))
            coordinates = f"chr{chromosome}:{start_formatted}-{end_formatted}"
            logger.info(f"Generated coordinates: {coordinates}")
        except ValueError as e:
            logger.error(f"Failed to format coordinates: {str(e)}")
            raise HTTPException(
                status_code=500,
                detail="Invalid coordinate values"
            )
        
        return {
            "coordinates": coordinates,
            "gene": gene
        }
        
    except ElementTree.ParseError as e:
        logger.error(f"Failed to parse NCBI response: {response.text[:200]}")
        logger.error(f"Parse error details: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="Failed to parse gene data from NCBI"
        )
    except Exception as e:
        logger.error(f"Error processing gene data: {str(e)}")
        logger.error(f"Full error details: {type(e).__name__}: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Error processing gene data: {str(e)}"
        )

def get_clinvar_data(gene: str, variant: str) -> dict:
    """Get clinical variant interpretation data from ClinVar."""
    logger.info(f"Starting ClinVar search for gene: {gene}, variant: {variant}")
    
    # First search for the variant
    esearch_url = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi"
    search_term = f"{gene}[gene] AND {variant}"
    
    search_params = {
        "db": "clinvar",
        "term": search_term,
        "retmode": "json",
        **NCBI_PARAMS
    }
    
    logger.info(f"ClinVar search URL: {esearch_url}")
    logger.info(f"ClinVar search params: {search_params}")
    
    try:
        logger.info("Making initial ClinVar search request...")
        response = session.get(
            esearch_url,
            params=search_params,
            timeout=REQUEST_TIMEOUT
        )
        logger.info(f"ClinVar search response status: {response.status_code}")
        logger.info(
            f"ClinVar search response headers: {dict(response.headers)}"
        )
        logger.debug(f"ClinVar search response body: {response.text}")
        
        if response.status_code != 200:
            logger.error(
                f"ClinVar search failed with status {response.status_code}"
            )
            logger.error(f"Error response: {response.text}")
            raise HTTPException(
                status_code=response.status_code,
                detail="ClinVar search failed"
            )
        
        search_data = response.json()
        logger.info(
            f"Successfully parsed ClinVar search response: {search_data}"
        )
        
        ids = search_data.get("esearchresult", {}).get("idlist", [])
        logger.info(f"Found {len(ids)} ClinVar IDs: {ids}")
        
        if not ids:
            logger.info(f"No ClinVar entries found for {gene} {variant}")
            return {
                "found": False,
                "message": f"No ClinVar entries found for {gene} {variant}"
            }
        
        # Get detailed variant data using esummary
        esummary_url = (
            "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esummary.fcgi"
        )
        summary_params = {
            "db": "clinvar",
            "id": ",".join(ids),
            "retmode": "json",
            **NCBI_PARAMS
        }
        
        logger.info(f"ClinVar summary URL: {esummary_url}")
        logger.info(f"ClinVar summary params: {summary_params}")
        
        logger.info("Making ClinVar summary request...")
        summary_resp = session.get(
            esummary_url,
            params=summary_params,
            timeout=REQUEST_TIMEOUT
        )
        logger.info(
            f"ClinVar summary response status: {summary_resp.status_code}"
        )
        logger.info(
            f"ClinVar summary response headers: {dict(summary_resp.headers)}"
        )
        logger.debug(f"ClinVar summary response body: {summary_resp.text}")
        
        if summary_resp.status_code != 200:
            logger.error(
                f"ClinVar summary fetch failed with status {summary_resp.status_code}"
            )
            logger.error(f"Error response: {summary_resp.text}")
            raise HTTPException(
                status_code=summary_resp.status_code,
                detail="ClinVar summary fetch failed"
            )
        
        summary_data = summary_resp.json()
        logger.info("Successfully parsed ClinVar summary response")
        
        if not summary_data.get("result"):
            logger.warning("ClinVar returned empty summary data")
            return {
                "found": False,
                "message": "No summary data available"
            }
        
        variants = []
        for variant_id in ids:
            logger.info(f"Processing variant ID: {variant_id}")
            variant_data = summary_data["result"].get(variant_id, {})
            
            # Extract germline classification
            germline = variant_data.get("germline_classification", {})
            logger.info(
                f"Germline classification for variant {variant_id}: {germline}"
            )
            
            # Extract frequency data
            freq_data = []
            for measure in variant_data.get("variation_set", []):
                for freq in measure.get("allele_freq_set", []):
                    freq_data.append({
                        "source": freq.get("source"),
                        "frequency": freq.get("value"),
                        "minor_allele": freq.get("minor_allele")
                    })
            
            # Extract genomic locations
            locations = []
            for measure in variant_data.get("variation_set", []):
                for loc in measure.get("variation_loc", []):
                    if loc.get("status") == "current":  # Only include current assembly
                        locations.append({
                            "assembly": loc.get("assembly_name"),
                            "chromosome": loc.get("chr"),
                            "position": loc.get("start"),
                            "cytogenetic": loc.get("band")
                        })
            
            variant_info = {
                "variant_id": variant_id,
                "accession": variant_data.get("accession"),
                "title": variant_data.get("title"),
                "clinical_significance": germline.get("description"),
                "last_evaluated": germline.get("last_evaluated"),
                "review_status": germline.get("review_status"),
                "is_fda_recognized": (
                    germline.get("fda_recognized_database") == "true"
                ),
                "molecular_consequences": (
                    variant_data.get("molecular_consequence_list", [])
                ),
                "allele_frequencies": freq_data,
                "genomic_locations": locations,
                "supporting_submissions": {
                    "clinical": (
                        variant_data.get("supporting_submissions", {})
                        .get("scv", [])
                    ),
                    "reference": (
                        variant_data.get("supporting_submissions", {})
                        .get("rcv", [])
                    )
                }
            }
            
            # Add associated conditions/traits
            conditions = []
            for trait_set in germline.get("trait_set", []):
                condition = {
                    "name": trait_set.get("trait_name"),
                    "identifiers": [
                        {"source": xref.get("db_source"), "id": xref.get("db_id")}
                        for xref in trait_set.get("trait_xrefs", [])
                    ]
                }
                conditions.append(condition)
            variant_info["associated_conditions"] = conditions
            
            variants.append(variant_info)
            logger.info(f"Successfully processed variant {variant_id}")
        
        logger.info(f"Successfully processed all {len(variants)} variants")
        return {
            "found": True,
            "variants": variants,
            "total_results": len(variants)
        }
        
    except Exception as e:
        logger.error(f"Error processing ClinVar data: {str(e)}", exc_info=True)
        logger.error(f"Error type: {type(e).__name__}")
        if hasattr(e, 'response'):
            logger.error(
                f"Response status: {e.response.status_code if e.response else 'No response'}"
            )
            logger.error(
                f"Response headers: {dict(e.response.headers) if e.response else 'No response'}"
            )
            logger.error(
                f"Response text: {e.response.text if e.response else 'No response'}"
            )
        raise HTTPException(
            status_code=500,
            detail=f"Error processing ClinVar data: {str(e)}"
        ) 