import os
import logging
import pickle
import json
import hashlib
from typing import List, Dict, Any, Optional
from models import Document, DocumentChunk
from app import db
from gemini_client import GeminiClient

# Simple text similarity using TF-IDF approach
class SimpleEmbedding:
    def __init__(self):
        self.vocabulary = {}
        self.idf_scores = {}
    
    def _tokenize(self, text: str) -> List[str]:
        """Simple tokenization"""
        import re
        # Convert to lowercase and split on non-alphanumeric characters
        tokens = re.findall(r'\b\w+\b', text.lower())
        return [token for token in tokens if len(token) > 2]
    
    def _compute_tf(self, tokens: List[str]) -> Dict[str, float]:
        """Compute term frequency"""
        tf = {}
        total_tokens = len(tokens)
        for token in tokens:
            tf[token] = tf.get(token, 0) + 1
        # Normalize by total tokens
        for token in tf:
            tf[token] = tf[token] / total_tokens
        return tf
    
    def encode(self, texts: List[str]) -> List[Dict[str, float]]:
        """Create simple TF-IDF-like embeddings"""
        embeddings = []
        all_tokens = []
        
        # Tokenize all texts and build vocabulary
        for text in texts:
            tokens = self._tokenize(text)
            all_tokens.append(tokens)
            for token in tokens:
                if token not in self.vocabulary:
                    self.vocabulary[token] = len(self.vocabulary)
        
        # Compute document frequency for IDF
        doc_freq = {}
        for tokens in all_tokens:
            unique_tokens = set(tokens)
            for token in unique_tokens:
                doc_freq[token] = doc_freq.get(token, 0) + 1
        
        # Compute IDF scores
        num_docs = len(texts)
        for token in doc_freq:
            self.idf_scores[token] = 1.0 + (num_docs / (1 + doc_freq[token]))
        
        # Create embeddings
        for tokens in all_tokens:
            tf = self._compute_tf(tokens)
            embedding = {}
            for token, tf_score in tf.items():
                idf_score = self.idf_scores.get(token, 1.0)
                embedding[token] = tf_score * idf_score
            embeddings.append(embedding)
        
        return embeddings
    
    def similarity(self, embedding1: Dict[str, float], embedding2: Dict[str, float]) -> float:
        """Compute cosine similarity between two embeddings"""
        # Get all unique terms
        all_terms = set(embedding1.keys()) | set(embedding2.keys())
        
        if not all_terms:
            return 0.0
        
        # Compute dot product and magnitudes
        dot_product = 0.0
        mag1 = 0.0
        mag2 = 0.0
        
        for term in all_terms:
            val1 = embedding1.get(term, 0.0)
            val2 = embedding2.get(term, 0.0)
            
            dot_product += val1 * val2
            mag1 += val1 * val1
            mag2 += val2 * val2
        
        if mag1 == 0.0 or mag2 == 0.0:
            return 0.0
        
        return dot_product / (mag1 ** 0.5 * mag2 ** 0.5)

class RAGEngine:
    """Retrieval-Augmented Generation engine using simple text similarity and Gemini"""
    
    def __init__(self):
        self.embedding_model = SimpleEmbedding()
        self.document_embeddings = {}  # Maps doc_id to list of chunk embeddings
        self.document_chunks = {}  # Maps doc_id to list of chunk texts
        self.gemini_client = GeminiClient()
        self.index_file = "vector_store/simple_index.json"
        
        # Load existing index if available
        self._load_index()
    
    def _load_index(self):
        """Load existing index"""
        try:
            if os.path.exists(self.index_file):
                with open(self.index_file, 'r') as f:
                    data = json.load(f)
                    self.document_embeddings = data.get('embeddings', {})
                    self.document_chunks = data.get('chunks', {})
                    # Convert string keys back to int
                    self.document_embeddings = {int(k): v for k, v in self.document_embeddings.items()}
                    self.document_chunks = {int(k): v for k, v in self.document_chunks.items()}
                logging.info(f"Loaded existing index with {len(self.document_embeddings)} documents")
            else:
                self._create_new_index()
        except Exception as e:
            logging.error(f"Error loading index: {e}")
            self._create_new_index()
    
    def _create_new_index(self):
        """Create new index"""
        self.document_embeddings = {}
        self.document_chunks = {}
        logging.info("Created new simple index")
    
    def _save_index(self):
        """Save index to disk"""
        try:
            os.makedirs("vector_store", exist_ok=True)
            data = {
                'embeddings': self.document_embeddings,
                'chunks': self.document_chunks
            }
            with open(self.index_file, 'w') as f:
                json.dump(data, f)
            logging.info("Saved index to disk")
        except Exception as e:
            logging.error(f"Error saving index: {e}")
    
    def add_document(self, document_id: int, chunks: List[str]):
        """Add document chunks to the vector store"""
        try:
            # Create embeddings for chunks
            embeddings = self.embedding_model.encode(chunks)
            
            # Store embeddings and chunks
            self.document_embeddings[document_id] = embeddings
            self.document_chunks[document_id] = chunks
            
            # Store document chunks in database
            for i, chunk in enumerate(chunks):
                chunk_record = DocumentChunk(
                    content=chunk,
                    chunk_index=i,
                    document_id=document_id
                )
                db.session.add(chunk_record)
            
            db.session.commit()
            self._save_index()
            
            logging.info(f"Added {len(chunks)} chunks for document {document_id}")
            
        except Exception as e:
            logging.error(f"Error adding document {document_id}: {e}")
            db.session.rollback()
            raise
    
    def remove_document(self, document_id: int):
        """Remove document from vector store"""
        try:
            # Remove from embeddings and chunks
            if document_id in self.document_embeddings:
                del self.document_embeddings[document_id]
            if document_id in self.document_chunks:
                del self.document_chunks[document_id]
            
            # Remove chunks from database
            DocumentChunk.query.filter_by(document_id=document_id).delete()
            db.session.commit()
            
            # Save updated index
            self._save_index()
            
            logging.info(f"Removed document {document_id} from vector store")
            
        except Exception as e:
            logging.error(f"Error removing document {document_id}: {e}")
            db.session.rollback()
            raise
    
    def search_similar_chunks(self, query: str, user_id: int, k: int = 5) -> List[Dict[str, Any]]:
        """Search for similar chunks in user's documents"""
        try:
            if not self.document_embeddings:
                return []
            
            # Create query embedding
            query_embedding = self.embedding_model.encode([query])[0]
            
            # Find similar chunks across all user documents
            results = []
            
            for doc_id, chunk_embeddings in self.document_embeddings.items():
                # Check if document belongs to user
                document = Document.query.filter_by(id=doc_id, user_id=user_id).first()
                if not document:
                    continue
                
                chunks = self.document_chunks.get(doc_id, [])
                
                for i, chunk_embedding in enumerate(chunk_embeddings):
                    if i < len(chunks):
                        similarity = self.embedding_model.similarity(query_embedding, chunk_embedding)
                        
                        results.append({
                            'content': chunks[i],
                            'score': similarity,
                            'document_id': doc_id,
                            'document_name': document.original_filename,
                            'chunk_id': i
                        })
            
            # Sort by similarity score and return top k
            results.sort(key=lambda x: x['score'], reverse=True)
            return results[:k]
            
        except Exception as e:
            logging.error(f"Error searching chunks: {e}")
            return []
    
    def answer_question(self, question: str, user_id: int) -> Dict[str, Any]:
        """Generate answer using RAG approach"""
        try:
            # Search for relevant chunks
            relevant_chunks = self.search_similar_chunks(question, user_id, k=5)
            
            if not relevant_chunks:
                return {
                    'answer': "**Answer not in context**\n\nI couldn't find relevant information in your uploaded documents to answer this question. Please make sure you have uploaded documents that contain information related to your query.",
                    'context_documents': []
                }
            
            # Prepare context for Gemini
            context = "\n\n".join([chunk['content'] for chunk in relevant_chunks])
            context_docs = [
                {
                    'name': chunk['document_name'],
                    'score': chunk['score']
                }
                for chunk in relevant_chunks
            ]
            
            # Generate answer using Gemini
            answer = self.gemini_client.generate_answer(question, context)
            
            return {
                'answer': answer,
                'context_documents': context_docs
            }
            
        except Exception as e:
            logging.error(f"Error answering question: {e}")
            return {
                'answer': "**Error Processing Question**\n\nI encountered an error while processing your question. Please try again or contact support if the issue persists.",
                'context_documents': []
            }
    
    def get_index_stats(self) -> Dict[str, int]:
        """Get statistics about the index"""
        total_chunks = sum(len(chunks) for chunks in self.document_chunks.values())
        return {
            'total_chunks': total_chunks,
            'total_documents': len(self.document_embeddings),
            'embedding_type': 'TF-IDF'
        }
