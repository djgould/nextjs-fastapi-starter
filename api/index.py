"""FastAPI router module for handling Python API endpoints."""
import json
import anthropic
from fastapi import FastAPI
from pydantic import BaseModel
import logging
from dotenv import load_dotenv
import os
from fastapi.responses import StreamingResponse
from .utils.tools import (
    get_weather_data,
    get_time_data,
    get_pubmed_studies,
    get_genome_browser_data,
    get_clinvar_data
)


# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Log environment information
logger.info("Environment Information:")
logger.info(f"VERCEL_ENV: {os.getenv('VERCEL_ENV', 'not set')}")
logger.info(f"VERCEL_REGION: {os.getenv('VERCEL_REGION', 'not set')}")
logger.info(f"Running in Vercel: {'VERCEL' in os.environ}")

# Load environment variables
logger.info("Loading environment variables...")
load_dotenv()

# Define available tools for Claude
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
        "name": "get_pubmed_studies",
        "description": "Get studies from PubMed using advanced search syntax",
        "input_schema": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "The search query for PubMed"
                },
                "max_results": {
                    "type": "integer",
                    "description": "Maximum number of results to return",
                    "default": 5
                }
            },
            "required": ["query"]
        }
    },
    {
        "name": "get_clinvar_data",
        "description": (
            "Get clinical variant interpretation data from ClinVar database"
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "gene": {
                    "type": "string",
                    "description": "Gene symbol (e.g., CDH1, BRCA1)"
                },
                "variant": {
                    "type": "string",
                    "description": (
                        "HGVS variant notation (e.g., c.1137G>A)"
                    )
                }
            },
            "required": ["gene", "variant"]
        }
    },
    {
        "name": "genome_browser",
        "description": (
            "Get genomic coordinates for a gene to display in the "
            "UCSC Genome Browser"
        ),
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

# Map of available tools to their functions
available_tools = {
    "get_weather": get_weather_data,
    "get_time": get_time_data,
    "get_pubmed_studies": get_pubmed_studies,
    "get_clinvar_data": get_clinvar_data,
    "genome_browser": get_genome_browser_data
}

# Create FastAPI instance with custom docs and openapi url
app = FastAPI(
    docs_url="/api/py/docs", 
    openapi_url="/api/py/openapi.json"
)


class WeatherRequest(BaseModel):
    """Schema for weather request."""

    location: str
    unit: str = "celsius"


class TimeRequest(BaseModel):
    """Schema for time request."""

    timezone: str


class ChatRequest(BaseModel):
    """Schema for chat request."""

    messages: list
    functions: list | None = None
    function_call: str | None = None


@app.post('/api/py/chat')
async def chat(request: ChatRequest):
    """Handle chat requests with tool usage."""
    logger.info(
        f"Received chat request with {len(request.messages)} messages"
    )
    return await stream_chat_response(request.messages)


@app.get("/api/py/helloFastApi")
def hello_fast_api():
    """Return a hello message from the FastAPI endpoint."""
    return {"message": "Hello from FastAPI"}


async def stream_chat_response(messages: list):
    """Stream chat responses following Vercel AI SDK protocol."""
    client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

    # Format messages for Claude API
    formatted_messages = []
    for msg in messages:
        if isinstance(msg.get("content"), list):
            # Handle messages with tool results
            content_parts = []
            for part in msg["content"]:
                if part.get("type") == "text":
                    content_parts.append(part["text"])
                elif part.get("type") == "tool_result":
                    content_parts.append(
                        f"Tool result: {part['content']}"
                    )
            content = " ".join(content_parts)
        else:
            content = msg.get("content", "")
        
        formatted_messages.append({
            "role": msg["role"],
            "content": content
        })

    logger.info(f"Formatted messages for Claude: {json.dumps(formatted_messages, indent=2)}")

    async def generate():
        try:
            draft_tool_calls = []
            draft_tool_calls_index = -1
            iteration_count = 0
            
            while True:  # Continue until we get a final text response
                iteration_count += 1
                logger.info(f"Starting iteration {iteration_count}")
                
                response = client.messages.create(
                    model="claude-3-sonnet-20240229",
                    max_tokens=1024,
                    temperature=0,
                    messages=formatted_messages,
                    tools=tools
                )
                
                logger.info(f"Claude response in iteration {iteration_count}: {json.dumps(response.model_dump(), indent=2)}")
                
                has_tool_call = False
                for content in response.content:
                    if content.type == "tool_use":
                        has_tool_call = True
                        draft_tool_calls_index += 1
                        
                        logger.info(f"Processing tool call: {content.name} with input: {json.dumps(content.input)}")
                        
                        # Tool call start
                        tool_call = {
                            "id": content.id,
                            "name": content.name,
                            "arguments": json.dumps(content.input)
                        }
                        draft_tool_calls.append(tool_call)
                        
                        # Send tool call announcement
                        tool_call_msg = f'9:{{"toolCallId":"{content.id}","toolName":"{content.name}","args":{json.dumps(content.input)}}}\n'
                        logger.info(f"Sending tool call announcement: {tool_call_msg.strip()}")
                        yield tool_call_msg
                        
                        # Execute tool and send result
                        try:
                            result = None
                            tool_input = content.input
                            
                            if content.name in available_tools:
                                logger.info(f"Executing tool {content.name}")
                                result = available_tools[content.name](**tool_input)
                                logger.info(f"Tool result: {json.dumps(result, indent=2)}")
                            
                            # Send tool result
                            tool_result_msg = f'a:{{"toolCallId":"{content.id}","toolName":"{content.name}","args":{json.dumps(tool_input)},"result":{json.dumps(result)}}}\n'
                            logger.info(f"Sending tool result: {tool_result_msg.strip()}")
                            yield tool_result_msg
                            
                            # Update formatted messages for next iteration
                            tool_messages = [
                                {
                                    "role": "assistant",
                                    "content": f"Using {content.name} tool with parameters: {json.dumps(tool_input)}"
                                },
                                {
                                    "role": "user",
                                    "content": f"Tool result: {json.dumps(result)}"
                                }
                            ]
                            logger.info(f"Adding tool messages to conversation: {json.dumps(tool_messages, indent=2)}")
                            formatted_messages.extend(tool_messages)
                            
                        except Exception as e:
                            logger.error(f"Tool execution error: {str(e)}", exc_info=True)
                            error_result = {"error": str(e)}
                            error_msg = f'a:{{"toolCallId":"{content.id}","toolName":"{content.name}","args":{json.dumps(tool_input)},"result":{json.dumps(error_result)}}}\n'
                            logger.info(f"Sending error result: {error_msg.strip()}")
                            yield error_msg
                    
                    elif content.type == "text":
                        # Stream text response
                        text_msg = f'0:{json.dumps(content.text)}\n'
                        logger.info(f"Sending text response: {text_msg.strip()}")
                        yield text_msg
                
                # Send completion message
                if not has_tool_call:
                    completion_msg = f'e:{{"finishReason":"stop","usage":{{"promptTokens":0,"completionTokens":0}},"isContinued":false}}\n'
                    logger.info(f"Sending completion (stop): {completion_msg.strip()}")
                    yield completion_msg
                    break
                else:
                    tool_completion_msg = f'e:{{"finishReason":"tool-calls","usage":{{"promptTokens":0,"completionTokens":0}},"isContinued":false}}\n'
                    logger.info(f"Sending completion (tool-calls): {tool_completion_msg.strip()}")
                    yield tool_completion_msg
                    if iteration_count >= 5:  # Add safety limit
                        logger.warning("Reached maximum iteration limit (5)")
                        break

        except Exception as e:
            logger.error("Chat error", exc_info=True)
            error_msg = f'e:{{"finishReason":"error","error":{json.dumps(str(e))},"usage":{{"promptTokens":0,"completionTokens":0}},"isContinued":false}}\n'
            logger.info(f"Sending error completion: {error_msg.strip()}")
            yield error_msg

    return StreamingResponse(
        generate(),
        media_type="text/event-stream",
        headers={
            "content-type": "text/event-stream",
            "cache-control": "no-cache",
            "connection": "keep-alive",
            "x-accel-buffering": "no",
            "x-vercel-ai-data-stream": "v1"
        }
    )