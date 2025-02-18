"""FastAPI router module for handling Python API endpoints."""
from datetime import datetime
import json
import pytz
import anthropic
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import requests
from firecrawl import FirecrawlApp
import logging
import xml.etree.ElementTree as ElementTree
from dotenv import load_dotenv
import os

# Load environment variables
load_dotenv()

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# NCBI API settings
NCBI_PARAMS = {k: v for k, v in {
    "api_key": os.getenv("NCBI_API_KEY"),
    "tool": os.getenv("NCBI_TOOL_NAME", "genomics-assistant"),
    "email": os.getenv("NCBI_EMAIL")
}.items() if v is not None}

# Create FastAPI instance with custom docs and openapi url
app = FastAPI(docs_url="/api/py/docs", openapi_url="/api/py/openapi.json")


class WeatherRequest(BaseModel):
    """Schema for weather request."""
    
    location: str
    unit: str = "celsius"


class TimeRequest(BaseModel):
    """Schema for time request."""
    
    timezone: str


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
    
    response = requests.get(weather_url, params=weather_params)
    if response.status_code != 200:
        raise HTTPException(status_code=response.status_code,
                          detail="Weather data not available")
    
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
        raise HTTPException(status_code=400, 
                          detail=f"Unknown timezone: {timezone}")


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
    
    response = requests.get(url, params=params)
    if response.status_code != 200:
        raise HTTPException(status_code=response.status_code,
                          detail="Google search failed")
    
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
        raise HTTPException(status_code=500, detail=f"Failed to read website: {str(e)}")


def get_pubmed_studies(query: str, max_results: int = 5) -> dict:
    """Get PubMed studies for a given query by searching for IDs and fetching study details.
    
    Supports advanced PubMed search syntax including field tags and boolean operators.
    Example queries:
    - science[journal] AND breast cancer AND 2023[pdat]
    - Smith[au] AND (BRCA1 OR BRCA2)
    - Lynch syndrome[tiab] AND review[pt]
    """
    esearch_url = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi"
    params = {
        "db": "pubmed",
        "term": query,
        "retmax": str(max_results),
        "usehistory": "y",
        "retmode": "json",
        **NCBI_PARAMS
    }
    
    esearch_resp = requests.get(esearch_url, params=params)
    if esearch_resp.status_code != 200:
        raise HTTPException(
            status_code=esearch_resp.status_code,
            detail="PubMed esearch failed"
        )
    
    try:
        search_data = esearch_resp.json()
        ids = search_data.get("esearchresult", {}).get("idlist", [])
        if not ids:
            return {"studies": [], "total_count": 0}

        # Get the total count of results (even if we're only fetching a subset)
        total_count = int(search_data.get("esearchresult", {}).get("count", "0"))
        
        efetch_url = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi"
        fetch_params = {
            "db": "pubmed",
            "id": ",".join(ids),
            "retmode": "xml",
            "rettype": "abstract",
            **NCBI_PARAMS
        }
        
        fetch_resp = requests.get(efetch_url, params=fetch_params)
        if fetch_resp.status_code != 200:
            raise HTTPException(
                status_code=fetch_resp.status_code,
                detail="PubMed efetch failed"
            )
        
        fetch_root = ElementTree.fromstring(fetch_resp.text)
        
        studies = []
        for article in fetch_root.findall(".//PubmedArticle"):
            article_node = article.find("MedlineCitation/Article")
            if article_node is None:
                continue
                
            pmid_node = article.find("MedlineCitation/PMID")
            pmid = pmid_node.text if pmid_node is not None else "No PMID"
            
            title_node = article_node.find("ArticleTitle")
            title = title_node.text if title_node is not None else "No title"
            
            journal_node = article_node.find("Journal/Title")
            journal = journal_node.text if journal_node is not None else "No journal"
            
            pub_date = article_node.find("Journal/JournalIssue/PubDate/Year")
            if pub_date is None:
                pub_date = article_node.find(
                    "Journal/JournalIssue/PubDate/MedlineDate"
                )
            year = pub_date.text if pub_date is not None else "No year"
            
            abstract_node = article_node.find("Abstract/AbstractText")
            summary = abstract_node.text if abstract_node is not None else "No abstract"
            
            studies.append({
                "title": title,
                "journal": journal,
                "year": year,
                "summary": summary,
                "pmid": pmid
            })
            
        return {
            "studies": studies,
            "total_count": total_count,
            "showing": len(studies)
        }
        
    except ElementTree.ParseError as e:
        logger.error(f"Failed to parse PubMed response: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="Failed to parse PubMed response"
        )
    except Exception as e:
        logger.error(f"Error processing PubMed data: {str(e)}")
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
    response = requests.get(esearch_url, params=params)
    if response.status_code != 200:
        logger.error(f"NCBI Gene search failed with status {response.status_code}: {response.text}")
        raise HTTPException(
            status_code=response.status_code,
            detail="Failed to fetch gene data from NCBI"
        )
    
    data = response.json()
    gene_ids = data.get("esearchresult", {}).get("idlist", [])
    logger.info(f"Found gene IDs: {gene_ids}")
    
    if not gene_ids:
        raise HTTPException(status_code=404, detail=f"Gene {gene} not found in NCBI database")
    
    # Get detailed gene info
    efetch_url = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi"
    params = {
        "db": "gene",
        "id": gene_ids[0],
        "retmode": "xml",
        **NCBI_PARAMS
    }
    
    logger.info(f"Fetching gene details with params: {params}")
    response = requests.get(efetch_url, params=params)
    if response.status_code != 200:
        logger.error(f"NCBI Gene fetch failed with status {response.status_code}: {response.text}")
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
                        logger.info(f"Found chromosome from BioSource: {chr_text}")
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
                    chr_match = chr_text.split('q')[0].split('p')[0].split('.')[0].strip()
                    logger.info(f"Extracted potential chromosome: {chr_match}")
                    if chr_match.isdigit() or chr_match.upper() in ["X", "Y"]:
                        chromosome = chr_match
                        logger.info(f"Found chromosome from map location: {chromosome}")
            
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
                            logger.info(f"Found coordinates - start: {start}, end: {end}")
                            break
        
        if chromosome is None or start is None or end is None:
            logger.error(f"Missing required data - chromosome: {chromosome}, start: {start}, end: {end}")
            raise HTTPException(status_code=404, detail=f"Could not find complete location data for gene {gene}")
        
        # Validate chromosome format
        if not (chromosome.isdigit() or chromosome.upper() in ["X", "Y"]):
            logger.error(f"Invalid chromosome format: {chromosome}")
            raise HTTPException(status_code=500, detail="Invalid chromosome format")
        
        # Format coordinates with commas for thousands and ensure chromosome is numeric
        try:
            start_formatted = "{:,}".format(int(start))
            end_formatted = "{:,}".format(int(end))
            coordinates = f"chr{chromosome}:{start_formatted}-{end_formatted}"
            logger.info(f"Generated coordinates: {coordinates}")
        except ValueError as e:
            logger.error(f"Failed to format coordinates: {str(e)}")
            raise HTTPException(status_code=500, detail="Invalid coordinate values")
        
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
    """Get clinical variant interpretation data from ClinVar.
    
    Args:
        gene: Gene symbol (e.g., CDH1, BRCA1)
        variant: HGVS variant notation (e.g., c.1137G>A)
    
    Returns:
        Dictionary containing ClinVar interpretation data including:
        - Clinical significance
        - Review status
        - Last evaluation date
        - Supporting evidence
        - FDA recognition status
        - Molecular consequences
    """
    # First search for the variant
    esearch_url = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi"
    search_params = {
        "db": "clinvar",
        "term": f"{gene}[gene] AND {variant}",
        "retmode": "json",
        **NCBI_PARAMS
    }
    
    response = requests.get(esearch_url, params=search_params)
    if response.status_code != 200:
        raise HTTPException(
            status_code=response.status_code,
            detail="ClinVar search failed"
        )
    
    try:
        search_data = response.json()
        ids = search_data.get("esearchresult", {}).get("idlist", [])
        if not ids:
            return {
                "found": False,
                "message": f"No ClinVar entries found for {gene} {variant}"
            }
        
        # Get detailed variant data using esummary
        esummary_url = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esummary.fcgi"
        summary_params = {
            "db": "clinvar",
            "id": ",".join(ids),
            "retmode": "json",
            **NCBI_PARAMS
        }
        
        summary_resp = requests.get(esummary_url, params=summary_params)
        if summary_resp.status_code != 200:
            raise HTTPException(
                status_code=summary_resp.status_code,
                detail="ClinVar summary fetch failed"
            )
        
        summary_data = summary_resp.json()
        if not summary_data.get("result"):
            return {
                "found": False,
                "message": "No summary data available"
            }
        
        variants = []
        for variant_id in ids:
            variant_data = summary_data["result"].get(variant_id, {})
            
            # Extract germline classification
            germline = variant_data.get("germline_classification", {})
            
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
                "is_fda_recognized": germline.get("fda_recognized_database") == "true",
                "molecular_consequences": variant_data.get("molecular_consequence_list", []),
                "allele_frequencies": freq_data,
                "genomic_locations": locations,
                "supporting_submissions": {
                    "clinical": variant_data.get("supporting_submissions", {}).get("scv", []),
                    "reference": variant_data.get("supporting_submissions", {}).get("rcv", [])
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
        
        return {
            "found": True,
            "variants": variants,
            "total_results": len(variants)
        }
        
    except Exception as e:
        logger.error(f"Error processing ClinVar data: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Error processing ClinVar data: {str(e)}"
        )


@app.get('/api/py/chat')
def chat(message: str):
    """Handle chat requests with tool usage."""
    logger.info(f"Received chat message: {message}")
    
    client = anthropic.Anthropic(
        api_key=os.getenv("ANTHROPIC_API_KEY")
    )
    
    tools = [
        {
            "name": "get_weather",
            "description": "Get the current weather in a given location",
            "input_schema": {
                "type": "object",
                "properties": {
                    "lat": {
                        "type": "number",
                        "description": "Latitude of the location"
                    },
                    "lon": {
                        "type": "number",
                        "description": "Longitude of the location"
                    },
                    "unit": {
                        "type": "string",
                        "enum": ["celsius", "fahrenheit"],
                        "description": "The unit of temperature"
                    }
                },
                "required": ["lat", "lon"]
            }
        },
        {
            "name": "get_time",
            "description": "Get the current time in a given time zone",
            "input_schema": {
                "type": "object",
                "properties": {
                    "timezone": {
                        "type": "string",
                        "description": "The IANA time zone name"
                    }
                },
                "required": ["timezone"]
            }
        },
        {
            "name": "google_search",
            "description": "Search Google for information. Returns a list of results that include the url of the website",
            "input_schema": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "The search query"
                    }
                },
                "required": ["query"]
            }
        },
        {
            "name": "get_pubmed_studies",
            "description": "Get studies from PubMed using advanced search syntax. For variant queries, try multiple searches from specific to broad if initial searches yield no results.",
            "input_schema": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "The search query for PubMed. Supports advanced syntax:\n- Field tags in square brackets (e.g., author[au], journal[jour], year[pdat])\n- Boolean operators (AND, OR, NOT)\n- For variant searches, try multiple approaches if initial search yields no results:\n  1. Exact variant: 'CDH1[gene] AND \"c.1137G>A\"[tiab]'\n  2. Broader gene context: 'CDH1[gene] AND (pathogenic[tiab] OR \"clinical significance\"[tiab]) AND 2020:2024[pdat]'\n  3. Gene reviews/guidelines: 'CDH1[gene] AND (\"review\"[pt] OR \"guideline\"[pt]) AND 2020:2024[pdat]'\n  4. Gene + phenotype: 'CDH1[gene] AND (gastric[tiab] OR breast[tiab]) AND mutation[tiab]'\n  5. Gene + region: 'CDH1[gene] AND 1137[tiab]'"
                    },
                    "max_results": {
                        "type": "integer",
                        "description": "Maximum number of results to return (default: 5)",
                        "default": 5
                    }
                },
                "required": ["query"]
            }
        },
        {
            "name": "get_clinvar_data",
            "description": "Get clinical variant interpretation data from ClinVar database",
            "input_schema": {
                "type": "object",
                "properties": {
                    "gene": {
                        "type": "string",
                        "description": "Gene symbol (e.g., CDH1, BRCA1)"
                    },
                    "variant": {
                        "type": "string",
                        "description": "HGVS variant notation (e.g., c.1137G>A)"
                    }
                },
                "required": ["gene", "variant"]
            }
        },
        # {
        #     "name": "read_website",
        #     "description": "Read and extract content from a website URL, consider using this if a search result could be relevant to the user's query",
        #     "input_schema": {
        #         "type": "object",
        #         "properties": {
        #             "url": {
        #                 "type": "string",
        #                 "description": "The full URL of the website to read"
        #             }
        #         },
        #         "required": ["url"]
        #     }
        # },
        {
            "name": "genome_browser",
            "description": "Get genomic coordinates for a gene to display in the UCSC Genome Browser",
            "input_schema": {
                "type": "object",
                "properties": {
                    "gene": {
                        "type": "string",
                        "description": "The gene symbol (e.g., BRCA1, BRCA2)"
                    }
                },
                "required": ["gene"]
            }
        }
    ]

    conversation = [{"role": "user", "type": "message", "content": message}]
    messages = [{"role": "user", "content": message}]
    
    while True:
        logger.info("Making request to Claude...")
        response = client.messages.create(
            model="claude-3-sonnet-20240229",
            max_tokens=1024,
            temperature=0,
            messages=messages,
            tools=tools
        )
        
        # Log Claude's initial response
        logger.info(f"Claude response type: {response.content[0].type}")
        if response.content[0].type == "text":
            logger.info(f"Claude response: {response.content[0].text[:200]}...")
        elif response.content[0].type == "tool_use":
            logger.info(f"Claude tool use: {response.content[0].name} with args {response.content[0].input}")
        
        # If no tool calls, add final message and return conversation
        if not any(content.type == "tool_use" for content in response.content):
            logger.info("No tool calls, returning final response")
            conversation.append({
                "role": "assistant",
                "type": "message",
                "content": response.content[0].text
            })
            return {"conversation": conversation}
            
        # Handle tool calls
        for content in response.content:
            if content.type == "tool_use":
                tool_name = content.name
                tool_id = content.id
                arguments = content.input
                
                logger.info(f"Tool call requested: {tool_name}")
                logger.info(f"Tool arguments: {arguments}")
                
                result = None
                try:
                    if tool_name == "get_weather":
                        result = get_weather_data(
                            lat=arguments["lat"],
                            lon=arguments["lon"],
                            unit=arguments.get("unit", "celsius")
                        )
                    elif tool_name == "get_time":
                        result = get_time_data(timezone=arguments["timezone"])
                    elif tool_name == "google_search":
                        result = google_search(query=arguments["query"])
                    elif tool_name == "get_pubmed_studies":
                        result = get_pubmed_studies(
                            query=arguments["query"],
                            max_results=arguments.get("max_results", 5)
                        )
                    elif tool_name == "read_website":
                        result = read_website(url=arguments["url"])
                    elif tool_name == "genome_browser":
                        result = get_genome_browser_data(gene=arguments["gene"])
                    elif tool_name == "get_clinvar_data":
                        result = get_clinvar_data(gene=arguments["gene"], variant=arguments["variant"])
                        
                    logger.info(f"Tool result: {str(result)[:200]}...")
                except Exception as e:
                    logger.error(f"Tool execution failed: {str(e)}")
                    raise
                
                # Add tool call and result to conversation
                conversation.append({
                    "role": "assistant",
                    "type": "tool_use",
                    "tool": tool_name,
                    "id": tool_id,
                    "arguments": arguments
                })
                
                conversation.append({
                    "role": "system",
                    "type": "tool_result",
                    "tool": tool_name,
                    "id": tool_id,
                    "result": result
                })
                
                logger.info("Adding tool results to message history")
                # Add to messages for Claude
                messages.append({
                    "role": "assistant",
                    "content": [
                        {
                            "type": "tool_use",
                            "id": tool_id,
                            "name": tool_name,
                            "input": arguments
                        }
                    ]
                })
                
                messages.append({
                    "role": "user",
                    "content": [
                        {
                            "type": "tool_result",
                            "tool_use_id": tool_id,
                            "content": json.dumps(result)
                        }
                    ]
                })


@app.get("/api/py/helloFastApi")
def hello_fast_api():
    """Return a hello message from the FastAPI endpoint."""
    return {"message": "Hello from FastAPI"}