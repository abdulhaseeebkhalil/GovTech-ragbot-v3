from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct
from typing import List, Dict, Any, Optional
import numpy as np
import uuid
import re
from .hybrid_search import (
    HybridSearchEngine,
    load_sentence_transformer,
    encode_with_fallback,
) 
import os


class EnhancedQdrantVectorStore:
    def __init__(self, url: str, api_key: str, collection_name: str):
        self.client = QdrantClient(url=url, api_key=api_key)
        self.collection_name = collection_name

        self.embedding_variant_weights = [0.6, 0.3, 0.1]
        self.embedding_backends = self._load_embedding_backends()
        self.embedding_dim = max(backend['dimension'] for backend in self.embedding_backends)
        self.primary_backend = self.embedding_backends[0]

        print("Initializing hybrid search engine...")
        self.hybrid_search = HybridSearchEngine(
            embedding_model_name=self.primary_backend['name'],
            embedding_model=self.primary_backend['model']
        )
        self.documents_cache: List[Dict[str, Any]] = []

        # Create collection if it doesn't exist
        self._create_collection_if_not_exists()

    def _load_embedding_backends(self) -> List[Dict[str, Any]]:
        """Load sentence-transformers embedding models with graceful fallback."""
        model_name = os.getenv('EMBEDDING_MODEL_NAME', 'sentence-transformers/all-MiniLM-L6-v2')
        preferred_models = [
            (model_name, 1.0),
            ('sentence-transformers/all-MiniLM-L6-v2', 1.0)
        ]

        backends: List[Dict[str, Any]] = []
        for model_name, weight in preferred_models:
            try:
                print(f"Loading embedding model '{model_name}' ...")
                model = load_sentence_transformer(model_name)
                dimension = model.get_sentence_embedding_dimension()
                backends.append({
                    'name': model_name,
                    'model': model,
                    'weight': weight,
                    'dimension': dimension
                })
                print(f"✅ Loaded '{model_name}' ({dimension}d, weight={weight})")
            except Exception as exc:
                print(f"⚠️  Could not load '{model_name}': {exc}")

        if not backends:
            raise RuntimeError("No embedding models could be initialized. Please ensure sentence-transformers models are available.")

        return backends
    
    def _create_collection_if_not_exists(self):
        """Create collection with appropriate vector configuration"""
        collections = self.client.get_collections().collections
        collection_names = [col.name for col in collections]
        
        if self.collection_name in collection_names:
            # Check if existing collection has correct dimensions
            try:
                collection_info = self.client.get_collection(self.collection_name)
                existing_dim = collection_info.config.params.vectors.size
                
                if existing_dim != self.embedding_dim:
                    print(f"⚠️  Collection exists with wrong dimensions ({existing_dim} vs {self.embedding_dim})")
                    print("🗑️  Deleting existing collection...")
                    self.client.delete_collection(self.collection_name)
                    print("✅ Old collection deleted")
                else:
                    print(f"✅ Collection exists with correct dimensions ({self.embedding_dim})")
                    return
            except Exception as e:
                print(f"Error checking collection: {e}, recreating...")
                try:
                    self.client.delete_collection(self.collection_name)
                except:
                    pass  # Collection might not exist
        
        print(f"🔨 Creating new collection with {self.embedding_dim} dimensions...")
        self.client.create_collection(
            collection_name=self.collection_name,
            vectors_config=VectorParams(
                size=self.embedding_dim,  # Dynamic embedding dimension
                distance=Distance.COSINE
            )
        )
        print("✅ Collection created successfully")
    
    def get_embeddings(self, texts: List[str], metadatas: Optional[List[Dict[str, Any]]] = None) -> List[List[float]]:
        """Generate blended embeddings emphasising legal structure and terminology.

        Optimised to batch-encode across all texts per backend and per variant to
        avoid long stalls when indexing many chunks.
        """
        if metadatas is None:
            metadatas = [{} for _ in texts]

        n = len(texts)
        if n == 0:
            return []

        # Prepare variant inputs per text once
        try:
            inputs_per_text: List[List[str]] = [
                self._prepare_embedding_inputs(t, m) for t, m in zip(texts, metadatas)
            ]
        except Exception as exc:
            print(f"Error preparing embedding inputs: {exc}")
            inputs_per_text = [[t] for t in texts]

        # Determine how many variants to use (bounded by configured weights)
        variant_count = min(
            max((len(v) for v in inputs_per_text), default=1),
            len(self.embedding_variant_weights)
        )

        # Ensure each text has exactly variant_count inputs
        for i in range(n):
            cur = inputs_per_text[i]
            if not cur:
                cur = [texts[i]]
            while len(cur) < variant_count:
                cur.append(cur[-1])
            inputs_per_text[i] = cur[:variant_count]

        print(
            f"🧮 Generating embeddings for {n} texts | "
            f"models={len(self.embedding_backends)} | variants={variant_count}"
        )

        # Accumulate blended vectors
        combined = np.zeros((n, self.embedding_dim), dtype=float)
        total_weights = np.zeros((n,), dtype=float)

        # Allow overriding batch size via env var
        import os
        try:
            batch_size = int(os.getenv('RAGBOT_EMBED_BATCH', '64'))
        except Exception:
            batch_size = 64

        for b_idx, backend in enumerate(self.embedding_backends):
            model = backend['model']
            b_dim = backend['dimension']
            b_weight = backend['weight']
            print(f"➡️  Backend {b_idx+1}/{len(self.embedding_backends)}: '{backend['name']}' ({b_dim}d, weight={b_weight})")

            for v_idx in range(variant_count):
                # Gather v-th variant across all texts
                variant_inputs = [inputs_per_text[i][v_idx] for i in range(n)]

                # Encode in batches
                parts: List[np.ndarray] = []
                for start in range(0, n, batch_size):
                    end = min(start + batch_size, n)
                    try:
                        emb = encode_with_fallback(
                            model,
                            variant_inputs[start:end],
                            batch_size=min(batch_size, end - start),
                            show_progress_bar=False,
                        )
                        if isinstance(emb, list):
                            emb = np.asarray(emb)
                    except Exception as exc:
                        print(f"⚠️  Encode failed for backend '{backend['name']}' variant {v_idx+1}: {exc}")
                        emb = np.zeros((end - start, b_dim), dtype=float)
                    parts.append(emb)
                backend_variant_emb = np.vstack(parts)  # (n, b_dim)

                # Resize to target dim once for the whole matrix
                if b_dim == self.embedding_dim:
                    resized = backend_variant_emb
                elif b_dim > self.embedding_dim:
                    resized = backend_variant_emb[:, : self.embedding_dim]
                else:
                    pad = np.zeros((n, self.embedding_dim - b_dim), dtype=float)
                    resized = np.concatenate([backend_variant_emb, pad], axis=1)

                weight = b_weight * self.embedding_variant_weights[v_idx]
                combined += resized * weight
                total_weights += weight
                print(f"   ✓ Variant {v_idx+1}/{variant_count} encoded and accumulated")

        # Avoid division by zero
        total_weights_safe = np.where(total_weights == 0.0, 1.0, total_weights)[:, None]
        final_vectors = combined / total_weights_safe

        print(f"✅ Successfully generated {n} blended embeddings")
        return [row.tolist() for row in final_vectors]

    def _encode_with_backends(self, text: str, metadata: Dict[str, Any]) -> np.ndarray:
        inputs = self._prepare_embedding_inputs(text, metadata)
        combined_vector = np.zeros(self.embedding_dim, dtype=float)
        total_weight = 0.0

        for backend in self.embedding_backends:
            try:
                embeddings = encode_with_fallback(backend['model'], inputs)
            except Exception as exc:
                print(f"⚠️  Encoding failed for model '{backend['name']}': {exc}")
                continue

            if embeddings.ndim == 1:
                embeddings = np.expand_dims(embeddings, axis=0)

            for idx, variant_vector in enumerate(embeddings):
                resized_vector = self._resize_vector(variant_vector, backend['dimension'])
                weight = backend['weight'] * self.embedding_variant_weights[min(idx, len(self.embedding_variant_weights) - 1)]
                combined_vector += resized_vector * weight
                total_weight += weight

        if total_weight == 0:
            return np.zeros(self.embedding_dim, dtype=float)

        return combined_vector / total_weight

    def _prepare_embedding_inputs(self, text: str, metadata: Dict[str, Any]) -> List[str]:
        """Create multiple legal-aware views of the text for richer embeddings."""
        inputs = [text]

        context_bits = []
        for field in ['chapter_number', 'section_number', 'article_number', 'rule_number', 'schedule_number']:
            if metadata.get(field):
                context_bits.append(f"{field.replace('_number', '').title()} {metadata[field]}")

        if context_bits:
            context_line = ' | '.join(context_bits)
            inputs.append(f"Context: {context_line}\n{text}")
        else:
            inputs.append(text)

        key_terms = metadata.get('key_terms') or []
        if key_terms:
            inputs.append(' '.join(sorted(set(key_terms))))
        else:
            inputs.append(text)

        unique_inputs: List[str] = []
        seen_inputs = set()
        for candidate in inputs:
            normalised = candidate.strip()
            if not normalised:
                continue
            if normalised in seen_inputs:
                continue
            unique_inputs.append(normalised)
            seen_inputs.add(normalised)

        if not unique_inputs:
            unique_inputs = [text]

        while len(unique_inputs) < len(self.embedding_variant_weights):
            unique_inputs.append(unique_inputs[-1])

        return unique_inputs[:len(self.embedding_variant_weights)]

    def _resize_vector(self, vector: np.ndarray, source_dim: int) -> np.ndarray:
        if source_dim == self.embedding_dim:
            return vector
        if source_dim > self.embedding_dim:
            return vector[:self.embedding_dim]
        padding = np.zeros(self.embedding_dim - source_dim, dtype=float)
        return np.concatenate([vector, padding])
    
    def add_documents(self, texts: List[str], metadatas: List[Dict[str, Any]] = None):
        """Add documents to the vector store"""
        if metadatas is None:
            metadatas = [{"text": text, "chunk_id": i} for i, text in enumerate(texts)]
        
        # Generate embeddings
        embeddings = self.get_embeddings(texts, metadatas)
        
        # Create points for Qdrant
        points = []
        documents_for_hybrid = []
        
        for i, (text, embedding, metadata) in enumerate(zip(texts, embeddings, metadatas)):
            point = PointStruct(
                id=str(uuid.uuid4()),
                vector=embedding,
                payload={
                    "text": text,
                    "metadata": metadata
                }
            )
            points.append(point)
            
            # Prepare documents for hybrid search
            documents_for_hybrid.append({
                "text": text,
                "metadata": metadata
            })
        
        # Upsert points to collection in batches to prevent long blocking calls
        batch_size = 256
        total = len(points)
        for start in range(0, total, batch_size):
            end = min(start + batch_size, total)
            try:
                self.client.upsert(
                    collection_name=self.collection_name,
                    points=points[start:end]
                )
                print(f"🆙 Upserted {end}/{total} points")
            except Exception as exc:
                print(f"❌ Upsert failed for batch {start}:{end} - {exc}")
                # Continue with remaining batches
        
        # Update documents cache and hybrid search index
        self.documents_cache.extend(documents_for_hybrid)
        print("🔍 Indexing documents for hybrid search...")
        self.hybrid_search.index_documents(self.documents_cache)
    
    def add_documents_with_metadata(self, documents_with_metadata: List[Dict[str, Any]]):
        """Add documents with rich metadata to the vector store"""
        texts = []
        metadatas = []
        
        for doc in documents_with_metadata:
            texts.append(doc['text'])
            metadatas.append(doc['metadata'])
        
        self.add_documents(texts, metadatas)
    
    def search(self, query: str, limit: int = 5) -> List[Dict[str, Any]]:
        """Search for similar documents using semantic search only"""
        # Generate query embedding
        query_embedding = self.get_embeddings([query])[0]
        
        # Search in Qdrant
        search_results = self.client.search(
            collection_name=self.collection_name,
            query_vector=query_embedding,
            limit=limit
        )
        # Format results to common structure
        raw: List[Dict[str, Any]] = []
        for result in search_results:
            raw.append({
                "text": result.payload.get("text", ""),
                "score": float(result.score),
                "metadata": result.payload.get("metadata", {})
            })

        # Apply precision filtering for surgical grounding
        try:
            max_cites = int(os.getenv('RAGBOT_MAX_CITATIONS', '4'))
        except Exception:
            max_cites = 4
        refined = self.hybrid_search.apply_precision_filters(
            query=query,
            results=raw,
            top_k=limit,
            max_results=max_cites,
        )

        # Return formatted results with provenance
        formatted: List[Dict[str, Any]] = []
        for r in refined:
            payload = {
                "text": r.get('text', ''),
                "score": float(r.get('score', 0.0)),
                "metadata": r.get('metadata', {}),
                "score_breakdown": r.get('score_breakdown', {}),
                "search_type": "semantic"
            }
            if 'sliced_text' in r:
                payload['sliced_text'] = r['sliced_text']
            if 'pinpoint_labels' in r:
                payload['pinpoint_labels'] = r['pinpoint_labels']
            formatted.append(payload)

        return formatted
    
    def hybrid_search_method(self, query: str, limit: int = 5, search_weights: Dict[str, float] = None) -> List[Dict[str, Any]]:
        """Advanced hybrid search combining multiple search strategies"""
        if not self.documents_cache:
            print("⚠️  No documents indexed for hybrid search, falling back to semantic search")
            return self.search(query, limit)
        
        # Use hybrid search engine
        hybrid_results = self.hybrid_search.hybrid_search(
            query=query,
            top_k=limit,
            weights=search_weights
        )

        # Apply precision filters (enforce surgical citations and drop loose matches)
        try:
            max_cites = int(os.getenv('RAGBOT_MAX_CITATIONS', '4'))
        except Exception:
            max_cites = 4
        refined = self.hybrid_search.apply_precision_filters(
            query=query,
            results=hybrid_results,
            top_k=limit,
            max_results=max_cites,
        )

        # Format results for consistency
        formatted_results: List[Dict[str, Any]] = []
        for result in refined:
            payload = {
                "text": result['text'],
                "score": float(result.get('score', 0.0)),
                "metadata": result.get('metadata', {}),
                "score_breakdown": result.get('score_breakdown', {}),
                "search_type": "hybrid"
            }
            if 'sliced_text' in result:
                payload['sliced_text'] = result['sliced_text']
            if 'pinpoint_labels' in result:
                payload['pinpoint_labels'] = result['pinpoint_labels']
            formatted_results.append(payload)

        return formatted_results
    
    def smart_search(self, query: str, limit: int = 5) -> List[Dict[str, Any]]:
        """Intelligent search that chooses the best strategy based on query"""
        # Analyze query to determine best search strategy
        query_lower = query.lower()

        # Check for schedule-specific queries
        schedule_patterns = [
            r'(first|second|third|fourth|fifth|sixth|seventh|eighth|ninth|tenth|eleventh|twelfth)\s+schedule',
            r'schedule\s+([ivxlcdm]+|\d+)',
            r'(\d+)(?:st|nd|rd|th)\s+schedule',
            r'what\s+(?:does|is)\s+.*?schedule'
        ]
        is_schedule_query = any(re.search(pattern, query_lower) for pattern in schedule_patterns)

        # Check if query contains specific references
        has_references = any(ref in query_lower for ref in [
            'section', 'article', 'chapter', 'part', 'clause', 'subclause', 'rule', 'schedule'
        ])

        # Check if query is asking for specific information
        is_specific_query = any(word in query_lower for word in [
            'what is', 'define', 'definition', 'meaning', 'purpose'
        ])

        # Check if query is about procedures or processes
        is_process_query = any(word in query_lower for word in [
            'how to', 'process', 'procedure', 'steps', 'method'
        ])

        # Determine search weights based on query type
        if is_schedule_query:
            # Strongly emphasize entity-based search for schedule queries
            # Schedules need exact matching more than semantic similarity
            weights = {'semantic': 0.2, 'keyword': 0.3, 'tfidf': 0.1, 'entity': 0.4}
            query_type = 'schedule'
        elif has_references:
            # Emphasize entity-based search for reference queries
            weights = {'semantic': 0.3, 'keyword': 0.2, 'tfidf': 0.2, 'entity': 0.3}
            query_type = 'reference'
        elif is_specific_query:
            # Emphasize semantic search for definition queries
            weights = {'semantic': 0.5, 'keyword': 0.2, 'tfidf': 0.2, 'entity': 0.1}
            query_type = 'definition'
        elif is_process_query:
            # Balanced approach for process queries
            weights = {'semantic': 0.4, 'keyword': 0.3, 'tfidf': 0.2, 'entity': 0.1}
            query_type = 'process'
        else:
            # Default balanced weights
            weights = {'semantic': 0.4, 'keyword': 0.3, 'tfidf': 0.2, 'entity': 0.1}
            query_type = 'general'

        # Perform hybrid search with optimized weights
        results = self.hybrid_search_method(query, limit, weights)

        # Add search strategy info to metadata
        for result in results:
            result['search_strategy'] = {
                'weights_used': weights,
                'query_type': query_type,
                'is_schedule_query': is_schedule_query
            }

        return results
    
    def get_collection_info(self):
        """Get information about the collection"""
        try:
            info = self.client.get_collection(self.collection_name)
            return {
                "status": info.status,
                "vectors_count": info.vectors_count,
                "points_count": info.points_count
            }
        except Exception as e:
            return {"error": str(e)}
    
    def delete_collection(self):
        """Delete the collection (useful for resetting)"""
        try:
            self.client.delete_collection(self.collection_name)
            print(f"✅ Collection '{self.collection_name}' deleted successfully")
            return True
        except Exception as e:
            print(f"❌ Error deleting collection: {e}")
            return False

    def recreate_collection(self):
        """Delete and recreate the collection with current dimensions"""
        try:
            # Delete if exists
            collections = self.client.get_collections().collections
            collection_names = [col.name for col in collections]

            if self.collection_name in collection_names:
                self.client.delete_collection(self.collection_name)
                print(f"🗑️  Deleted existing collection '{self.collection_name}'")

            # Create new
            self._create_collection_if_not_exists()
            return True
        except Exception as e:
            print(f"❌ Error recreating collection: {e}")
            return False

    def get_embedding_overview(self) -> Dict[str, Any]:
        """Summarise the embedding ensemble used for indexing."""
        return {
            'dimension': self.embedding_dim,
            'variant_weights': self.embedding_variant_weights,
            'models': [
                {
                    'name': backend['name'],
                    'weight': backend['weight'],
                    'dimension': backend['dimension']
                }
                for backend in self.embedding_backends
            ]
        }
