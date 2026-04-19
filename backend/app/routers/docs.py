from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from typing import Optional

from ..services.document_service import document_service

router = APIRouter()


@router.post("/")
async def upload_document(file: UploadFile = File(...), category: Optional[str] = Form(None)):
    """上传文档（支持 .txt 和 .pdf）"""
    try:
        result = await document_service.upload_file(file, category)
        return {"code": 0, "message": "上传成功", "data": result}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"上传失败: {str(e)}")


@router.get("/")
async def list_documents():
    """获取文档列表"""
    docs = document_service.list_documents()
    return {"code": 0, "message": "获取成功", "data": docs}


@router.delete("/{doc_id}")
async def delete_document(doc_id: int):
    """删除文档"""
    success = document_service.delete_document(doc_id)
    if success:
        return {"code": 0, "message": "删除成功"}
    return {"code": 1, "message": "文档不存在"}


@router.post("/seed")
async def seed_test_data():
    """生成测试数据"""
    results = document_service.seed_test_data()
    return {"code": 0, "message": "测试数据生成成功", "data": results}
