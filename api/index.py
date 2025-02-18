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
NCBI_PARAMS = {
    "api_key": os.getenv("NCBI_API_KEY"),
    "tool": os.getenv("NCBI_TOOL_NAME", "genomics-assistant"),
    "email": os.getenv("NCBI_EMAIL")
}

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


def get_pubmed_studies(query: str) -> dict:
    """Get PubMed studies for a given query by searching for IDs and fetching study details."""
    esearch_url = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi"
    params = {
        "db": "pubmed",
        "term": query,
        "retmax": "5",
        **NCBI_PARAMS
    }
    esearch_resp = requests.get(esearch_url, params=params)
    if esearch_resp.status_code != 200:
        raise HTTPException(
            status_code=esearch_resp.status_code,
            detail="PubMed esearch failed"
        )
    try:
        root = ElementTree.fromstring(esearch_resp.text)
    except ElementTree.ParseError:
        raise HTTPException(
            status_code=500,
            detail="Failed to parse PubMed esearch XML"
        )
    ids = [elem.text for elem in root.findall(".//Id") if elem.text]
    if not ids:
        return {"studies": []}

    efetch_url = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi"
    fetch_params = {
        "db": "pubmed",
        "id": ",".join(ids),
        "retmode": "xml",
        "rettype": "abstract"
    }
    fetch_resp = requests.get(efetch_url, params=fetch_params)
    if fetch_resp.status_code != 200:
        raise HTTPException(status_code=fetch_resp.status_code, detail="PubMed efetch failed")
    try:
        fetch_root = ElementTree.fromstring(fetch_resp.text)
    except ElementTree.ParseError:
        raise HTTPException(status_code=500, detail="Failed to parse PubMed efetch XML")

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
            pub_date = article_node.find("Journal/JournalIssue/PubDate/MedlineDate")
        year = pub_date.text if pub_date is not None else "No year"
        abstract_node = article_node.find("Abstract/AbstractText")
        summary = abstract_node.text if abstract_node is not None else "No abstract"
        studies.append({"title": title, "journal": journal, "year": year, "summary": summary, "pmid": pmid})
    return {"studies": studies}


def get_genome_browser_data(gene: str, variant: str = None) -> dict:
    """Get genomic coordinates and variant information for a gene from NCBI and ClinVar."""
    # First get gene info from NCBI
    esearch_url = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi"
    params = {
        "db": "gene",
        "term": f"{gene}[Gene Name] AND human[Organism]",
        "retmode": "json",
        **NCBI_PARAMS
    }
    
    response = requests.get(esearch_url, params=params)
    if response.status_code != 200:
        raise HTTPException(
            status_code=response.status_code,
            detail="Failed to fetch gene data from NCBI"
        )
    
    data = response.json()
    gene_ids = data.get("esearchresult", {}).get("idlist", [])
    
    if not gene_ids:
        raise HTTPException(status_code=404, detail=f"Gene {gene} not found in NCBI database")
    
    # Get detailed gene info
    efetch_url = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi"
    params = {
        "db": "gene",
        "id": gene_ids[0],
        "retmode": "xml"
    }
    
    response = requests.get(efetch_url, params=params)
    if response.status_code != 200:
        raise HTTPException(
            status_code=response.status_code,
            detail="Failed to fetch gene details from NCBI"
        )
    
    try:
        root = ElementTree.fromstring(response.text)
        gene_loc = root.find(".//Entrezgene_location")
        if gene_loc is None:
            raise HTTPException(status_code=404, detail=f"No location data found for gene {gene}")
        
        # Extract chromosome
        chr_node = gene_loc.find(".//Gene-commentary_label")
        chromosome = chr_node.text if chr_node is not None else None
        
        # Extract coordinates
        seq_locs = gene_loc.findall(".//Seq-interval")
        if seq_locs:
            seq_loc = seq_locs[0]  # Use first interval
            start = seq_loc.find(".//Seq-interval_from").text
            end = seq_loc.find(".//Seq-interval_to").text
            coordinates = f"chr{chromosome}:{start}-{end}"
        else:
            raise HTTPException(status_code=404, detail=f"No coordinate data found for gene {gene}")
        
        # If variant is provided, fetch from ClinVar
        variants = []
        if variant:
            # Search ClinVar for the variant
            clinvar_search_url = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi"
            clinvar_params = {
                "db": "clinvar",
                "term": f"{gene}[Gene] AND {variant}[Variant]",
                "retmode": "json"
            }
            
            clinvar_response = requests.get(clinvar_search_url, params=clinvar_params)
            if clinvar_response.status_code == 200:
                clinvar_data = clinvar_response.json()
                clinvar_ids = clinvar_data.get("esearchresult", {}).get("idlist", [])
                
                if clinvar_ids:
                    # Get variant details
                    clinvar_fetch_url = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi"
                    clinvar_fetch_params = {
                        "db": "clinvar",
                        "id": clinvar_ids[0],
                        "rettype": "variation",
                        "retmode": "xml"
                    }
                    
                    clinvar_fetch_response = requests.get(clinvar_fetch_url, params=clinvar_fetch_params)
                    if clinvar_fetch_response.status_code == 200:
                        clinvar_root = ElementTree.fromstring(clinvar_fetch_response.text)
                        # Extract variant position and allele
                        var_loc = clinvar_root.find(".//SequenceLocation[@Assembly='GRCh38']")
                        if var_loc is not None:
                            position = var_loc.get("start")
                            ref_allele = var_loc.get("referenceAllele", "")
                            alt_allele = var_loc.get("alternateAllele", "")
                            variants.append({
                                "position": int(position),
                                "allele": f"{ref_allele}>{alt_allele}" if ref_allele and alt_allele else variant
                            })
        
        return {
            "coordinates": coordinates,
            "gene": gene,
            "variants": variants
        }
        
    except ElementTree.ParseError:
        raise HTTPException(
            status_code=500,
            detail="Failed to parse gene data from NCBI"
        )
    except Exception as e:
        logger.error(f"Error processing gene data: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Error processing gene data: {str(e)}"
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
            "description": "Get studies from PubMed by searching with a query",
            "input_schema": {
                "type": "object",
                "properties": {
                    "query": { "type": "string", "description": "The search query for PubMed" }
                },
                "required": ["query"]
            }
        },
        {
            "name": "read_website",
            "description": "Read and extract content from a website URL, consider using this if a search result could be relevant to the user's query",
            "input_schema": {
                "type": "object",
                "properties": {
                    "url": {
                        "type": "string",
                        "description": "The full URL of the website to read"
                    }
                },
                "required": ["url"]
            }
        },
        {
            "name": "genome_browser",
            "description": "Get genomic coordinates and variant information for a gene to display in the UCSC Genome Browser",
            "input_schema": {
                "type": "object",
                "properties": {
                    "gene": {
                        "type": "string",
                        "description": "The gene symbol (e.g., BRCA1, BRCA2)"
                    },
                    "variant": {
                        "type": "string",
                        "description": "Optional variant in HGVS notation (e.g., c.68_69delAG)"
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
        logger.info(f"Claude response: {response.content[0].text[:200]}...")
        
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
                        result = get_pubmed_studies(query=arguments["query"])
                    elif tool_name == "read_website":
                        result = read_website(url=arguments["url"])
                    elif tool_name == "genome_browser":
                        result = get_genome_browser_data(
                            gene=arguments["gene"],
                            variant=arguments.get("variant")
                        )
                        
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