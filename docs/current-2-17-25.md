Here's a concise summary of the core functionality:

1. Hybrid Next.js + FastAPI Architecture
   Shown in next.config.js (lines 3-27) and package.json (lines 6-12)
   Next.js handles frontend while FastAPI serves backend APIs under /api/py/
2. AI Assistant with Tool Orchestration
   Core logic in api/index.py (lines 202-388)
   Features:
   PubMed study lookup (get_pubmed_studies)
   Web search (google_search)
   Website content extraction (read_website)
   Weather/time data APIs
   Multi-turn conversations with Claude-3 Sonnet
3. Conversational UI
   Implemented in app/page.tsx (lines 1-458)
   Key components:
   Message threading with avatars
   Rich result displays for different tool outputs
   Markdown rendering with remarkGfm
   Loading states and error handling
4. Genetic Research Focus
   Demonstrated in docs/genetics-prd.md (lines 1-269)
   Specialized PubMed integration for:
   Variant analysis
   Clinical significance lookup
   Study aggregation
5. Developer Tooling
   Concurrent dev servers (package.json scripts)
   Shared API endpoints:
   Next.js: /api/helloNextJs
   FastAPI: /api/py/helloFastApi
   Component library with shadcn/ui
   The system demonstrates tight integration between Next.js frontend and Python backend, with a focus on biomedical research use cases through its PubMed integration and genetics-focused PRD.
