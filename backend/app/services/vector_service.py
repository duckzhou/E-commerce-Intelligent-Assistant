import os
import json
import pickle
import numpy as np
from typing import List, Optional
import faiss
from openai import OpenAI

from ..config import settings


class QwenEmbedding:
    """使用千问 text-embedding-v3 模型的 embedding 实现"""
    
    def __init__(self):
        self.client = OpenAI(
            api_key=settings.dashscope_api_key,
            base_url=settings.dashscope_base_url
        )
        self.model = settings.embedding_model
        self.dimension = 1024  # text-embedding-v3 的维度
    
    def embed(self, text: str) -> List[float]:
        """将单个文本转换为向量"""
        response = self.client.embeddings.create(
            model=self.model,
            input=text
        )
        return response.data[0].embedding
    
    def embed_batch(self, texts: List[str]) -> List[List[float]]:
        """批量转换文本为向量"""
        # 千问 API 支持批量输入
        response = self.client.embeddings.create(
            model=self.model,
            input=texts
        )
        # 按原始顺序排序（API 可能不保证顺序）
        embeddings = sorted(response.data, key=lambda x: x.index)
        return [e.embedding for e in embeddings]


class VectorService:
    """向量检索服务（使用 FAISS + 千问 embedding）"""
    
    def __init__(self):
        self.index = None
        self.documents = []  # 存储文档内容
        self.metadata = []   # 存储元数据
        self.embedding_model = QwenEmbedding()
        self.index_path = os.path.join(settings.chroma_path, "faiss_index.bin")
        self.docs_path = os.path.join(settings.chroma_path, "documents.json")
        
        os.makedirs(settings.chroma_path, exist_ok=True)
        
        # 加载已有索引
        self._load_index()
    
    def _load_index(self):
        """加载已保存的索引"""
        print(f"[VECTOR_DEBUG] _load_index called")
        print(f"[VECTOR_DEBUG] index_path exists: {os.path.exists(self.index_path)}")
        print(f"[VECTOR_DEBUG] docs_path exists: {os.path.exists(self.docs_path)}")
        
        if os.path.exists(self.index_path) and os.path.exists(self.docs_path):
            try:
                self.index = faiss.read_index(self.index_path)
                print(f"[VECTOR_DEBUG] loaded index with dimension: {self.index.d}")
                
                with open(self.docs_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.documents = data.get("documents", [])
                    self.metadata = data.get("metadata", [])
                    print(f"[VECTOR_DEBUG] loaded {len(self.documents)} documents")
                    print(f"[VECTOR_DEBUG] loaded {len(self.metadata)} metadata entries")
            except Exception as e:
                print(f"[VECTOR_DEBUG] load failed: {e}")
                import traceback
                traceback.print_exc()
                self.index = None
                self.documents = []
                self.metadata = []
        else:
            print("[VECTOR_DEBUG] index files not found, starting fresh")
    
    def _save_index(self):
        """保存索引"""
        if self.index is not None:
            faiss.write_index(self.index, self.index_path)
            with open(self.docs_path, 'w', encoding='utf-8') as f:
                json.dump({
                    "documents": self.documents,
                    "metadata": self.metadata
                }, f, ensure_ascii=False)
    
    def add_documents(self, doc_id: str, chunks: List[str], metadata: Optional[List[dict]] = None):
        """添加文档到向量数据库（累积模式）"""
        if not chunks:
            return
        
        print(f"[VECTOR_DEBUG] Adding {len(chunks)} chunks for doc_id: {doc_id}")
        
        # 获取 embedding 维度
        dim = self.embedding_model.dimension
        
        # 如果索引不存在，创建新索引
        if self.index is None:
            self.index = faiss.IndexFlatIP(dim)
        
        # 转换新文档向量
        print("[VECTOR_DEBUG] Computing embeddings for new documents...")
        vectors = self.embedding_model.embed_batch(chunks)
        vectors_np = np.array(vectors, dtype=np.float32)
        
        # 归一化向量（使内积等于余弦相似度）
        faiss.normalize_L2(vectors_np)
        
        if len(vectors_np) > 0:
            self.index.add(vectors_np)
        
        # 累积文档列表
        start_idx = len(self.documents)
        self.documents.extend(chunks)
        
        # 累积元数据
        for i, chunk in enumerate(chunks):
            if metadata and i < len(metadata):
                self.metadata.append({**metadata[i], "doc_id": doc_id})
            else:
                self.metadata.append({"doc_id": doc_id, "chunk_index": start_idx + i})
        
        self._save_index()
        print(f"[VECTOR_DEBUG] Index saved with {self.index.ntotal} vectors")
    
    # 最低相似度阈值（余弦相似度范围 0-1）
    MIN_SIMILARITY_THRESHOLD = 0.45
    
    def search(self, query: str, n_results: int = 5, doc_id: Optional[str] = None) -> List[dict]:
        """检索相关文档"""
        print(f"[VECTOR_DEBUG] search called with query: {query}")
        print(f"[VECTOR_DEBUG] index is None: {self.index is None}")
        print(f"[VECTOR_DEBUG] index.ntotal: {self.index.ntotal if self.index else 'N/A'}")
        print(f"[VECTOR_DEBUG] documents count: {len(self.documents)}")
        
        if self.index is None or self.index.ntotal == 0:
            print("[VECTOR_DEBUG] returning empty - index is None or empty")
            return []
        
        # 转换查询向量
        print("[VECTOR_DEBUG] Computing query embedding...")
        query_vec = self.embedding_model.embed(query)
        query_vec_np = np.array([query_vec], dtype=np.float32)
        
        # 归一化查询向量
        faiss.normalize_L2(query_vec_np)
        
        # 搜索
        k = min(n_results * 2, self.index.ntotal)
        print(f"[VECTOR_DEBUG] searching with k={k}")
        scores, indices = self.index.search(query_vec_np, k)
        print(f"[VECTOR_DEBUG] scores: {scores}")
        print(f"[VECTOR_DEBUG] indices: {indices}")
        
        results = []
        for i, idx in enumerate(indices[0]):
            if idx == -1:
                continue
            
            similarity = float(scores[0][i])
            print(f"[VECTOR_DEBUG] result {i}: idx={idx}, similarity={similarity:.4f}")
            
            # 过滤低于最低相似度阈值的结果
            if similarity < self.MIN_SIMILARITY_THRESHOLD:
                print(f"[VECTOR_DEBUG] filtering out result with similarity {similarity:.4f} < {self.MIN_SIMILARITY_THRESHOLD}")
                continue
            
            # 如果指定了 doc_id，过滤
            if doc_id and self.metadata[idx].get("doc_id") != doc_id:
                continue
            
            results.append({
                "content": self.documents[idx],
                "metadata": self.metadata[idx],
                "distance": similarity,
                "similarity": similarity
            })
            
            if len(results) >= n_results:
                break
        
        print(f"[VECTOR_DEBUG] returning {len(results)} results (after filtering)")
        return results
    
    def delete_documents(self, doc_id: str):
        """删除文档的向量（重建索引）"""
        to_keep = [i for i, m in enumerate(self.metadata) if m.get("doc_id") != doc_id]
        
        if len(to_keep) == len(self.metadata):
            return
        
        if self.index is not None and to_keep:
            # 重建索引
            self.index.reset()
            if to_keep:
                kept_docs = [self.documents[i] for i in to_keep]
                vectors = self.embedding_model.embed_batch(kept_docs)
                vectors_np = np.array(vectors, dtype=np.float32)
                faiss.normalize_L2(vectors_np)
                if len(vectors_np) > 0:
                    self.index.add(vectors_np)
        
        self.documents = [self.documents[i] for i in to_keep]
        self.metadata = [self.metadata[i] for i in to_keep]
        self._save_index()
    
    def get_collection_stats(self) -> dict:
        """获取集合统计信息"""
        return {
            "count": self.index.ntotal if self.index else 0
        }


# 全局实例
vector_service = VectorService()