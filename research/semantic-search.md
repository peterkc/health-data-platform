# Semantic Search — Embedding Strategy for Clinical Data

**Status**: Design — informs M3 implementation if semantic search is in scope
**Purpose**: Define what gets embedded, how search works, and how vector retrieval integrates with the Repository and PDP.
**Audience**: Engineers building the embedding pipeline; code-vs-semantic boundary review; architecture review.
**Companion to**: [database-substrate.md](database-substrate.md) (pgvector as substrate), [data-plane.md](data-plane.md) (Repository read/write integration), [decisions.md](decisions.md) (D5 embeddings table, D14 code_text, D18 agent identity)

## How to read this file

- "Search strategy" defines when code lookup is enough and when semantic search is needed
- "What gets embedded" specifies the source text per resource type
- "Hybrid search" explains the code-first-then-semantic query flow
- "Agent integration" covers RAG pipeline and PDP interaction
- "Indexing pipeline" covers when and how embeddings are computed

## 1. Search strategy matrix

Code-based search (LOINC, SNOMED, ICD-10, RxNorm) is the primary path. Semantic search handles what codes miss.

| Data type                                  | Primary search                  | Semantic search | When semantic fires                                                        |
| ------------------------------------------ | ------------------------------- | --------------- | -------------------------------------------------------------------------- |
| Observations with LOINC                    | Code lookup                     | No              | Code is the canonical identifier                                           |
| Conditions with ICD-10/SNOMED              | Code lookup                     | Fallback        | Missing code, partial code, or patient-language query                      |
| Medications with RxNorm                    | Code lookup                     | Fallback        | Brand names, misspellings, patient language ("blood pressure pill")        |
| Drug class queries ("ACE inhibitors")      | `ref_drug_classes` class lookup | Fallback        | Class hierarchy covers ~80%; semantic catches brand names + edge cases     |
| Free-text clinical notes (D14 `code_text`) | None — no code                  | **Primary**     | Always — these records exist because coding failed or wasn't attempted     |
| Unstructured documents                     | None                            | **Primary**     | PDFs, scanned records, discharge summaries                                 |
| Patient-reported symptoms                  | None                            | **Primary**     | Natural language, no standard coding                                       |
| Family history narrative                   | Code lookup for condition code  | **Fallback**    | "My dad had heart problems" — no ICD-10 code, relationship context matters |
| Immunizations with CVX                     | Code lookup                     | No              | CVX covers all US-licensed vaccines                                        |

**Rule**: if a record has a code + code_system, code lookup is authoritative. Semantic search adds value when codes are absent, incomplete, or when the query is natural language.

## 2. Embedding model selection

### Requirements

- Clinical text understanding (medical terminology, abbreviations, drug names)
- Reasonable dimension size (storage × 10k+ records × multiple models)
- D5 multi-model support: `health_record_embeddings.model_id` allows multiple models to coexist

### Candidates

| Model                         | Dimensions | Clinical training               | License  | Notes                                                |
| ----------------------------- | ---------- | ------------------------------- | -------- | ---------------------------------------------------- |
| PubMedBERT                    | 768        | Yes — PubMed + PMC corpus       | MIT      | Best clinical recall for biomedical text             |
| BioBERT                       | 768        | Yes — PubMed pre-trained        | Apache 2 | Predecessor to PubMedBERT, widely cited              |
| OpenAI text-embedding-3-small | 1536       | General (not clinical-specific) | API      | Highest general quality; requires API call per embed |
| Cohere embed-v3               | 1024       | General                         | API      | Multilingual support, good for international (P3)    |
| all-MiniLM-L6-v2              | 384        | General                         | Apache 2 | Smallest, fastest; lower clinical recall             |

### Recommendation

**PubMedBERT (768-dim) for MVP**. Clinical-specific training, open-source, self-hostable (P4 Ownership — no API dependency for embeddings). 768 dimensions is the sweet spot: 768 × 4 bytes = ~3KB per record. 100k records = ~300MB of vectors — trivial for pgvector.

OpenAI or Cohere as optional second model via D5's `model_id` column — additive, not a replacement. Useful for multilingual queries (P3 international).

### Model upgrade strategy

D5's `health_record_embeddings` has `model_id`. When a better model ships:

1. Add new model to registry
1. Batch re-embed all records with new model (background job)
1. Old and new embeddings coexist — query specifies which model
1. Remove old embeddings after validation

Zero downtime. No schema change. This is why D5 put embeddings in a separate table with `model_id`.

## 3. What gets embedded

Per resource type, the embedding source text is a concatenation of specific fields. Not every column — just the fields that carry clinical meaning.

| Resource type              | Source text for embedding                                          | Example                                                                                           |
| -------------------------- | ------------------------------------------------------------------ | ------------------------------------------------------------------------------------------------- |
| Observations               | `code_display + ": " + value + " " + unit + ". " + code_text`      | "Hemoglobin A1c: 6.8 %. Slightly elevated, trending down from 7.2"                                |
| Conditions                 | `code_display + ". " + code_text + ". Status: " + clinical_status` | "Essential hypertension. Patient reports well-controlled with current medication. Status: active" |
| Medications                | `code_display + ". " + code_text`                                  | "Lisinopril 10mg. Started for blood pressure, patient tolerating well"                            |
| Allergies                  | `code_display + ". Reaction: " + code_text`                        | "Penicillin. Reaction: hives and throat swelling within 30 minutes"                               |
| Family history             | `relationship + " — " + code_display + ". " + code_text`           | "Father — Myocardial infarction. Age 52, fatal. Paternal grandfather also had MI"                 |
| Documents                  | Chunked full text (see section 4)                                  | Per-chunk embedding                                                                               |
| Clinical impressions (D13) | `summary + ". Findings: " + findings_text`                         | Agent-authored clinical reasoning                                                                 |

**Empty code_text**: if only `code` + `code_display` exist (no free text), the embedding captures the coded label. Less useful for semantic search but still enables "find similar conditions" queries.

## 4. Chunking strategy (for documents)

Documents (D3) can be multi-page PDFs or discharge summaries. Embedding the entire document as one vector loses granularity. Chunking splits the document into searchable segments.

### Approach

| Parameter          | Value                                       | Rationale                                                                |
| ------------------ | ------------------------------------------- | ------------------------------------------------------------------------ |
| Method             | Sentence-boundary splitting                 | Preserves clinical meaning better than fixed-size (no mid-sentence cuts) |
| Target chunk size  | ~500 tokens (~375 words)                    | Fits in PubMedBERT's 512-token context window                            |
| Overlap            | ~50 tokens between chunks                   | Context preservation at chunk boundaries                                 |
| Metadata per chunk | `document_id`, `chunk_index`, `page_number` | Enables "show me the page this came from"                                |

### Storage

Each chunk = one row in `health_record_embeddings` with `source_table='documents'`, `source_id=document_id`, and `chunk_index` in metadata JSON. A 10-page document might produce 15-20 chunks.

## 5. Hybrid search (code + semantic)

Most queries benefit from both search methods. The query flow:

```
User query: "ACE inhibitors"
  |
  v
1. Parse: is this a known code or code class?
   -> Yes: ref_drug_classes lookup -> RxNorm codes for ACE inhibitors
   -> Also: embed the query text
  |
  v
2. Code path: SELECT * FROM medications WHERE code IN (rxnorm_codes)
   Semantic path: SELECT * FROM health_record_embeddings
                  WHERE embedding <=> query_embedding < threshold
  |
  v
3. Merge: RRF (Reciprocal Rank Fusion)
   - Code results ranked by trust_level (D19)
   - Semantic results ranked by cosine similarity
   - RRF combines: score = 1/(k + rank_code) + 1/(k + rank_semantic)
  |
  v
4. PDP filter: BatchCheck all merged results (D25 partial-permit)
  |
  v
5. Return permitted results with search metadata:
   { match_type: 'code' | 'semantic' | 'both', similarity_score, code_match }
```

### Why RRF over re-ranking

Reciprocal Rank Fusion is simple, parameter-light (one constant k, typically 60), and doesn't require a trained re-ranker model. For MVP, RRF is sufficient. Cross-encoder re-ranking is an optimization for when search quality metrics (section 8) show RRF isn't good enough.

## 6. Agent integration (D18)

The AI agent uses semantic search as part of its RAG (Retrieval-Augmented Generation) pipeline.

### Agent read flow

```
Patient: "What medications am I on for my heart?"
  |
  v
1. Agent embeds the question
2. Semantic search: find records similar to "medications for heart"
3. Code search: medications WHERE hom_node_id = 'hom-heart' (HOM query, section 2.1 fan-out)
4. Merge results (RRF)
5. PDP: BatchCheck with agent's GrantContext (actor_kind='agent_session', purpose='care')
6. Permitted results become agent's context
7. Agent generates response grounded in retrieved records
```

### PDP still applies

Semantic search does not bypass authorization. Retrieved records go through the same PDP evaluation as any `read_many()` call (D25 partial-permit). The agent cannot see records its grant doesn't cover, regardless of vector similarity.

### Search vs Repository

Two options for where semantic search lives:

| Option                           | Where                                                                 | Trade-off                                            |
| -------------------------------- | --------------------------------------------------------------------- | ---------------------------------------------------- |
| `Repository.search()` new method | Inside Repository                                                     | PDP is automatic; consistent with read_one/read_many |
| Separate search service          | Outside Repository, calls Repository.read_one() for permitted results | Decoupled; search index can be independent           |

**Recommendation**: `Repository.search()` — keeps PDP enforcement in one place. Signature:

```python
def search(
    self,
    query: str,
    patient_id: UUID,
    grant_context: GrantContext,
    resource_types: list[ResourceType] | None = None,
    limit: int = 20,
) -> SearchResult:
    """Hybrid code + semantic search. PDP-filtered."""
```

Returns `SearchResult` with match_type per record (code, semantic, or both).

## 7. Indexing pipeline

### When embeddings are computed

| Option           | Trigger                                              | Latency             | Complexity                                                      |
| ---------------- | ---------------------------------------------------- | ------------------- | --------------------------------------------------------------- |
| Sync on write    | In Repository.write() transaction                    | Zero — always fresh | Adds embedding latency to write path (~50-100ms for PubMedBERT) |
| Async via outbox | Outbox event (section 6.2) triggers embedding worker | Seconds to minutes  | Decoupled; write path stays fast; eventual consistency          |

**Recommendation**: **Async via outbox** at MVP. Repository.write() is already fast (PDP + insert + audit triggers). Adding 50-100ms embedding computation per record in the transaction path is unnecessary coupling. The outbox worker (section 6.2) processes embedding jobs within seconds — fast enough for search.

### Batch re-indexing

For model upgrades (section 2) or backfill of existing records:

```
1. Create new model entry in registry
2. SELECT all records missing embeddings for new model_id
3. Batch embed (GPU worker, ~1000 records/minute for PubMedBERT on CPU)
4. INSERT INTO health_record_embeddings with new model_id
5. Update search to use new model_id
6. (Optional) DELETE old model embeddings after validation
```

### pgvector index maintenance

- HNSW index build: ~10 minutes for 100k vectors at 768-dim (one-time)
- Concurrent inserts during index build: supported in pgvector 0.5+
- Memory: HNSW index ~1.5x vector data size in RAM during queries
- Rebuild: rarely needed; HNSW handles incremental inserts well

## 8. Evaluation

Search quality should be measured, not assumed.

### Test set

Curate 50-100 query/expected-result pairs:

| Query                       | Expected records                           | Tests                           |
| --------------------------- | ------------------------------------------ | ------------------------------- |
| "ACE inhibitors"            | All ACE inhibitor medications              | Drug class hybrid search        |
| "heart problems"            | Cardiovascular conditions + family history | Cross-type semantic             |
| "blood sugar"               | Glucose observations + HbA1c               | Synonym handling                |
| "my dad had a heart attack" | Family history MI entries                  | Natural language + relationship |
| "penicillin allergy"        | Allergy records for penicillin class       | Code + semantic                 |

### Metrics

- **Precision@10**: of the top 10 results, how many are relevant?
- **Recall@10**: of all relevant records, how many appear in top 10?
- **MRR** (Mean Reciprocal Rank): where does the first relevant result appear?

Target: precision@10 > 0.8 and recall@10 > 0.7 before shipping semantic search to users.

### Iteration

If metrics are below target:

1. Check embedding model — switch from general to clinical-specific
1. Check source text — are we embedding the right fields?
1. Check chunking — are document chunks too large or too small?
1. Consider cross-encoder re-ranking on top of RRF

## Related

- [database-substrate.md](database-substrate.md) — pgvector as the vector search substrate
- [decisions.md](decisions.md) D5 — health_record_embeddings table design
- [decisions.md](decisions.md) D14 — code_text field (primary semantic search source)
- [decisions.md](decisions.md) D18 — agent identity (RAG pipeline consumer)
- [data-plane.md](data-plane.md) §1.1 — Repository.read() (search extends this interface)
- [data-plane.md](data-plane.md) §6.2 — transactional outbox (async embedding trigger)
