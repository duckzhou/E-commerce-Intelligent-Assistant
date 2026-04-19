import os
import uuid
import time
from typing import List, Optional
from datetime import datetime
from fastapi import UploadFile
import pdfplumber

from ..database import SessionLocal, Document
from ..config import settings
from .vector_service import vector_service, QwenEmbedding


class DocumentService:
    """文档处理服务"""
    
    UPLOAD_DIR = "./data/uploads"
    
    def __init__(self):
        os.makedirs(self.UPLOAD_DIR, exist_ok=True)
    
    async def upload_file(self, file: UploadFile, category: Optional[str] = None) -> dict:
        """上传并处理文档"""
        print(f"[UPLOAD_DEBUG] filename: {file.filename}")
        print(f"[UPLOAD_DEBUG] content_type: {file.content_type}")
        print(f"[UPLOAD_DEBUG] size attr: {file.size}")
        
        # 验证文件类型
        file_ext = os.path.splitext(file.filename)[1].lower()
        if file_ext not in ['.txt', '.pdf']:
            raise ValueError(f"不支持的文件类型: {file_ext}，仅支持 .txt 和 .pdf")
        
        # 生成唯一文件名
        unique_filename = f"{uuid.uuid4().hex}{file_ext}"
        file_path = os.path.join(self.UPLOAD_DIR, unique_filename)
        
        # 保存文件
        content = await file.read()
        print(f"[UPLOAD_DEBUG] content length: {len(content)} bytes")
        with open(file_path, "wb") as f:
            f.write(content)
        
        # 解析文档内容
        if file_ext == '.pdf':
            text_content = self._parse_pdf(file_path)
        else:
            text_content = content.decode('utf-8')
        
        # 切分文本
        chunks = self._split_text(text_content)
        
        # 保存文档记录
        db = SessionLocal()
        try:
            doc = Document(
                filename=file.filename,
                category=category,
                file_type=file_ext[1:],
                chunks_count=len(chunks)
            )
            db.add(doc)
            db.commit()
            db.refresh(doc)
            
            # 添加到向量数据库
            if chunks:
                vector_service.add_documents(str(doc.id), chunks)
            
            return {
                "id": doc.id,
                "filename": doc.filename,
                "category": doc.category,
                "file_type": doc.file_type,
                "chunks_count": doc.chunks_count,
                "created_at": doc.created_at.isoformat()
            }
        finally:
            db.close()
    
    def _parse_pdf(self, file_path: str) -> str:
        """解析PDF文件内容"""
        text = ""
        with pdfplumber.open(file_path) as pdf:
            for page in pdf.pages:
                page_text = page.extract_text()
                if page_text:
                    text += page_text + "\n"
        return text
    
    def _split_text(self, text: str) -> List[str]:
        """将文本切分为块"""
        chunks = []
        # 简单按段落切分
        paragraphs = text.split('\n\n')
        current_chunk = ""
        
        for para in paragraphs:
            para = para.strip()
            if not para:
                continue
            
            if len(current_chunk) + len(para) > settings.chunk_size:
                if current_chunk:
                    chunks.append(current_chunk.strip())
                current_chunk = para
            else:
                if current_chunk:
                    current_chunk += "\n\n" + para
                else:
                    current_chunk = para
        
        if current_chunk:
            chunks.append(current_chunk.strip())
        
        return chunks
    
    def list_documents(self) -> List[dict]:
        """获取文档列表"""
        db = SessionLocal()
        try:
            docs = db.query(Document).order_by(Document.created_at.desc()).all()
            return [doc.to_dict() for doc in docs]
        finally:
            db.close()
    
    def delete_document(self, doc_id: int) -> bool:
        """删除文档"""
        db = SessionLocal()
        try:
            doc = db.query(Document).filter(Document.id == doc_id).first()
            if doc:
                # 删除向量数据库中的内容
                vector_service.delete_documents(str(doc_id))
                db.delete(doc)
                db.commit()
                return True
            return False
        finally:
            db.close()
    
    def seed_test_data(self) -> List[dict]:
        """生成测试数据"""
        test_docs = [
            {
                "filename": "直播技巧指南.txt",
                "category": "直播技巧",
                "content": """直播前的准备工作非常重要。首先，你需要准备好直播设备，包括摄像头、麦克风、灯光等。确保设备质量良好，画面清晰。

其次，选择合适的直播背景。背景应该干净整洁，符合你的直播风格。可以使用虚拟背景或者实景布置。

直播内容的策划也很关键。提前准备好话题大纲，准备好互动环节，比如抽奖、问答等，增加观众参与感。

最后，测试网络连接。确保网络稳定，避免直播过程中出现卡顿。建议使用有线网络而非WiFi。""",
            },
            {
                "filename": "电商产品运营策略.txt",
                "category": "电商运营",
                "content": """电商产品选品是运营的核心环节。选品需要考虑市场需求、竞争情况、利润空间等多个因素。

首先，分析目标用户的需求。通过数据分析了解用户的购买偏好、消费能力等，选择符合用户需求的产品。

其次，研究竞争对手。分析同类产品的销量、评价、价格等，找出差异化竞争点。

定价策略也很重要。可以采用成本加成法、市场定价法、价值定价法等多种方式。同时要考虑促销活动的空间。

产品上架后，需要持续优化产品详情页。包括标题优化、主图优化、详情页设计等，提高转化率。""",
            },
            {
                "filename": "主播话术技巧.txt",
                "category": "直播技巧",
                "content": """主播的话术直接影响观众的购买决策。好的话术应该自然流畅，有感染力。

开场白要吸引注意力。可以用问候、自我介绍、今日亮点等方式开场，让观众感受到你的热情。

产品介绍要有条理。先说产品的核心卖点，再详细介绍功能、材质、使用方法等。用场景化的描述让观众产生代入感。

互动话术很重要。多使用"宝宝们"、"家人们"等亲切称呼，拉近距离。及时回复弹幕问题，让观众感受到被重视。

促单话术要制造紧迫感。比如"限量抢购"、"最后100件"、"错过就没有了"等，促使观众快速下单。""",
            },
            {
                "filename": "直播间流量获取.txt",
                "category": "流量运营",
                "content": """直播间流量获取是直播成功的关键。流量来源主要包括自然流量、付费流量和私域流量。

自然流量主要依靠平台推荐算法。提高直播间互动率、停留时长、转化率等指标，可以获得更多推荐流量。

付费流量主要通过投放广告获取。可以选择信息流广告、搜索广告等方式，精准定向目标用户。

私域流量是最稳定的流量来源。包括粉丝群、微信公众号、朋友圈等。平时要做好粉丝维护和社群运营。

直播时间的选择也影响流量。选择目标用户活跃的时间段直播，可以获得更好的观看效果。一般晚上8-10点是黄金时段。""",
            },
            {
                "filename": "售后服务管理.txt",
                "category": "电商运营",
                "content": """售后服务是电商运营的重要环节，直接影响用户满意度和复购率。

首先，建立完善的售后流程。包括退换货处理、投诉处理、维修服务等，确保每个环节都有明确的标准。

客服团队的培训也很关键。客服人员需要熟悉产品知识、售后政策，具备良好的沟通能力和问题解决能力。

建立用户反馈机制。通过评价、问卷、客服记录等方式收集用户反馈，持续改进产品和服务。

售后数据分析也很重要。分析退换货率、投诉率、满意度等指标，找出问题所在，优化运营策略。""",
            }
        ]
        
        results = []
        db = SessionLocal()
        try:
            # 清空向量库
            vector_service.index = None
            vector_service.documents = []
            vector_service.metadata = []
            vector_service.embedding_model = QwenEmbedding()
            
            for doc_data in test_docs:
                # 检查是否已存在
                existing = db.query(Document).filter(Document.filename == doc_data["filename"]).first()
                if existing:
                    # 删除旧记录
                    vector_service.delete_documents(str(existing.id))
                    db.delete(existing)
                    db.commit()
                
                # 切分文本
                chunks = self._split_text(doc_data["content"])
                
                # 保存文档
                doc = Document(
                    filename=doc_data["filename"],
                    category=doc_data["category"],
                    file_type="txt",
                    chunks_count=len(chunks)
                )
                db.add(doc)
                db.commit()
                db.refresh(doc)
                
                # 添加到向量数据库
                if chunks:
                    vector_service.add_documents(str(doc.id), chunks)
                
                results.append({
                    "id": doc.id,
                    "filename": doc.filename,
                    "category": doc.category,
                    "chunks_count": len(chunks)
                })
            
            return results
        finally:
            db.close()


# 全局实例
document_service = DocumentService()