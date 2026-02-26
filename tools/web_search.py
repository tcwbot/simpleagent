import requests
#from duckduckgo_search import DDGS
from ddgs import DDGS
import logging

logging.getLogger("curl_cffi").setLevel(logging.ERROR)

# Updated Schema with "Anti-Hallucination" instructions in the description
SCHEMA = {
    'type': 'function',
    'function': {
        'name': 'web_search',
        'description': 'Search the internet for facts. Use ONLY if the answer is unknown. If results are empty, state that no information was found.',
        'parameters': {
            'type': 'object',
            'properties': {
                'query': {'type': 'string', 'description': 'The specific search term to verify facts.'},
            },
            'required': ['query'],
        },
    },
}

def execute(query: str):
    """
    Executes a web search with grounding logic to prevent fabrication.
    """
    results = []
    try:
        #with DDGS() as ddgs:
        with DDGS(proxy=None, timeout=20) as ddgs:
            # We use a small max_results to keep context clean and focused
            ddgs_gen = ddgs.text(query, region='wt-wt', safesearch='Off', timelimit='y')
            
            for i, r in enumerate(ddgs_gen):
                if i >= 3:  # Limit to top 3 high-relevance results
                    break
                results.append(f"SOURCE: {r['href']}\nTITLE: {r['title']}\nCONTENT: {r['body']}")

        # CRITICAL: If the list is empty, return a hard 'No Data' string
        if not results:
            return "GROUNDING_ERROR: No reliable web results found for this query. Do not improvise."

        return "\n\n---\n\n".join(results)

    except Exception as e:
        return f"SYSTEM_ERROR: Search failed. Report that you cannot verify this information currently. Error: {str(e)}"
