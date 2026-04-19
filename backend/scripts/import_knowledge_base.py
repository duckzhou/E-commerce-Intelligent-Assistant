"""
导入知识库文档到向量数据库
"""
import os
import sys

# 添加项目根目录到 Python 路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from app.services.vector_service import vector_service

KNOWLEDGE_BASE_PATH = os.path.join(
    os.path.dirname(os.path.dirname(__file__)),
    'data',
    'knowledge_base'
)


def chunk_text(text: str, chunk_size: int = 500, overlap: int = 50) -> list:
    """将文本分块"""
    chunks = []
    start = 0
    while start < len(text):
        end = start + chunk_size
        chunk = text[start:end]
        chunks.append(chunk)
        start = end - overlap
    return chunks


def import_documents():
    """导入知识库文档"""
    if not os.path.exists(KNOWLEDGE_BASE_PATH):
        print(f"知识库目录不存在: {KNOWLEDGE_BASE_PATH}")
        return
    
    files = [f for f in os.listdir(KNOWLEDGE_BASE_PATH) if f.endswith('.txt')]
    
    if not files:
        print("知识库目录中没有找到任何文档")
        return
    
    print(f"找到 {len(files)} 个文档")
    
    for filename in files:
        filepath = os.path.join(KNOWLEDGE_BASE_PATH, filename)
        print(f"\n正在处理: {filename}")
        
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 分块
        chunks = chunk_text(content)
        print(f"  - 文本长度: {len(content)} 字符")
        print(f"  - 分块数量: {len(chunks)}")
        
        # 创建元数据
        metadata = [
            {"source": filename, "chunk_index": i}
            for i in range(len(chunks))
        ]
        
        # 添加到向量数据库
        doc_id = filename.replace('.txt', '')
        vector_service.add_documents(doc_id, chunks, metadata)
        print(f"  - 已添加到向量数据库")
    
    # 打印统计信息
    stats = vector_service.get_collection_stats()
    print(f"\n导入完成!")
    print(f"向量数据库中文档总数: {stats['count']}")


if __name__ == '__main__':
    import_documents()