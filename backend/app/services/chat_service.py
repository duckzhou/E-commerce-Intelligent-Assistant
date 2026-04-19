import os
import time
import json
import asyncio
from typing import List, Optional, AsyncGenerator
from openai import OpenAI
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnablePassthrough

from ..config import settings
from ..database import SessionLocal, Message, Conversation, Log
from .vector_service import vector_service


class QueryRewriter:
    """Query 改写器 - 优化用户查询以提高检索效果"""
    
    REWRITE_PROMPT = """你是一个查询优化专家。请根据用户的问题和对话历史，优化查询语句，使其更适合检索。

要求：
1. 保持原意不变
2. 使查询更加具体和明确
3. 提取关键信息
4. 如果是多轮对话，结合上下文理解

对话历史：
{history}

用户问题：{query}

优化后的查询（只返回优化后的查询，不要解释）："""
    
    def __init__(self, llm):
        self.llm = llm
        self.prompt = ChatPromptTemplate.from_template(self.REWRITE_PROMPT)
        self.chain = self.prompt | self.llm | StrOutputParser()
    
    async def rewrite(self, query: str, history: str = "") -> str:
        """改写用户查询"""
        try:
            result = await self.chain.ainvoke({"query": query, "history": history})
            return result.strip()
        except Exception:
            return query


class HybridRetriever:
    """混合检索器 - 结合向量检索和 BM25 检索"""
    
    def __init__(self):
        self.vector_service = vector_service
    
    def search(self, query: str, n_results: int = 5) -> List[dict]:
        """混合检索相关文档"""
        # 向量检索
        vector_results = self.vector_service.search(query, n_results=n_results * 2)
        
        # 简单 rerank：根据相关性得分排序
        reranked = self._rerank_results(vector_results, query)
        
        return reranked[:n_results]
    
    def _rerank_results(self, results: List[dict], query: str) -> List[dict]:
        """简单的 rerank 策略"""
        if not results:
            return []
        
        # 计算关键词匹配度
        query_terms = set(self._tokenize(query))
        
        for result in results:
            content = result.get("content", "")
            content_terms = set(self._tokenize(content))
            
            # 关键词匹配度
            keyword_score = len(query_terms & content_terms) / max(len(query_terms), 1)
            
            # 向量相似度
            vector_score = result.get("similarity", 0)
            
            # 综合得分（向量检索权重更高）
            result["rerank_score"] = 0.7 * vector_score + 0.3 * keyword_score
        
        # 按综合得分排序
        results.sort(key=lambda x: x.get("rerank_score", 0), reverse=True)
        
        return results
    
    def _tokenize(self, text: str) -> List[str]:
        """简单分词"""
        tokens = []
        for i in range(len(text) - 1):
            tokens.append(text[i:i+2])
        return tokens


class ChatService:
    """智能问答服务 - 使用 LangChain 重构"""
    
    def __init__(self):
        # 初始化 OpenAI 客户端
        self.client = OpenAI(
            api_key=settings.dashscope_api_key,
            base_url=settings.dashscope_base_url
        )
        
        # 初始化 LangChain LLM
        self.llm = ChatOpenAI(
            model=settings.llm_model,
            api_key=settings.dashscope_api_key,
            base_url=settings.dashscope_base_url,
            streaming=True,
            temperature=0.7
        )
        
        # 初始化组件
        self.query_rewriter = QueryRewriter(self.llm)
        self.hybrid_retriever = HybridRetriever()
        
        # 对话历史管理
        self.conversation_histories = {}  # {conversation_id: [messages]}
    
    async def chat(
        self,
        query: str,
        conversation_id: Optional[str] = None,
        context_messages: Optional[List[dict]] = None
    ) -> dict:
        """处理用户查询"""
        start_time = time.time()
        
        # 获取或创建对话
        if not conversation_id:
            conversation_id = self._create_conversation(query)
        
        # Query 改写
        rewrite_start = time.time()
        history_text = self._format_history(context_messages or [])
        rewritten_query = await self.query_rewriter.rewrite(query, history_text)
        rewrite_time = (time.time() - rewrite_start) * 1000
        
        # 混合检索
        retrieval_start = time.time()
        retrieved_chunks = self.hybrid_retriever.search(rewritten_query, n_results=5)
        retrieval_time = (time.time() - retrieval_start) * 1000
        
        # 构建提示词
        system_prompt = self._build_system_prompt(retrieved_chunks)
        
        # 调用LLM
        llm_start = time.time()
        response = self._call_llm(system_prompt, query, context_messages or [])
        generation_time = (time.time() - llm_start) * 1000
        
        total_time = (time.time() - start_time) * 1000
        
        # 保存消息
        self._save_message(conversation_id, "user", query)
        self._save_message(conversation_id, "assistant", response["content"], response.get("sources"))
        
        # 更新对话历史
        self._update_conversation_history(conversation_id, query, response["content"])
        
        # 记录日志
        self._log_query(
            query, retrieved_chunks, response, 
            retrieval_time, generation_time, total_time,
            rewritten_query=rewritten_query
        )
        
        # 构建来源信息
        sources = [
            {
                "content": chunk["content"][:100] + "...",
                "similarity": chunk.get("rerank_score", chunk.get("similarity", 0))
            }
            for chunk in retrieved_chunks
        ]
        
        return {
            "conversation_id": conversation_id,
            "content": response["content"],
            "sources": sources,
            "confidence": response.get("confidence", "medium"),
            "tokens_used": response.get("tokens_used", 0),
            "retrieval_time_ms": retrieval_time,
            "generation_time_ms": generation_time,
            "total_time_ms": total_time,
            "rewritten_query": rewritten_query
        }
    
    async def chat_stream(
        self,
        query: str,
        conversation_id: Optional[str] = None,
        context_messages: Optional[List[dict]] = None
    ) -> AsyncGenerator[str, None]:
        """流式处理用户查询"""
        start_time = time.time()
        
        # 获取或创建对话
        if not conversation_id:
            conversation_id = self._create_conversation(query)
        
        # Query 改写
        rewrite_start = time.time()
        history_text = self._format_history(context_messages or [])
        rewritten_query = await self.query_rewriter.rewrite(query, history_text)
        rewrite_time = (time.time() - rewrite_start) * 1000
        
        # 混合检索
        retrieval_start = time.time()
        retrieved_chunks = self.hybrid_retriever.search(rewritten_query, n_results=5)
        retrieval_time = (time.time() - retrieval_start) * 1000
        
        print(f"[DEBUG] retrieved_chunks count: {len(retrieved_chunks)}")
        for i, chunk in enumerate(retrieved_chunks):
            print(f"[DEBUG] chunk {i}: similarity={chunk.get('similarity', 0):.4f}, rerank_score={chunk.get('rerank_score', 0):.4f}")
        
        # 如果没有检索到相关内容，直接拒绝回答
        if len(retrieved_chunks) == 0:
            full_response = "抱歉，我的知识库中没有找到与您的问题相关的内容。我专注于直播和电商领域，如果您有关于直播准备、主播话术、流量获取、选品策略等方面的问题，我很乐意为您解答！"
            
            # 保存消息
            self._save_message(conversation_id, "user", query)
            assistant_msg_id = self._save_message(conversation_id, "assistant", full_response)
            
            # 更新对话历史
            self._update_conversation_history(conversation_id, query, full_response)
            
            # 记录日志
            self._log_query(
                query, retrieved_chunks, {"content": full_response}, 
                retrieval_time, 0, (time.time() - start_time) * 1000,
                rewritten_query=rewritten_query
            )
            
            # 直接返回拒绝回答
            done_data = json.dumps({'type': 'chunk', 'content': full_response}, ensure_ascii=False)
            yield f"data: {done_data}\n\n"
            
            done_data = json.dumps({'type': 'done', 'conversation_id': conversation_id, 'message_id': assistant_msg_id, 'total_time_ms': (time.time() - start_time) * 1000, 'sources': [], 'tokens': {'prompt_tokens': 0, 'completion_tokens': len(full_response) // 4, 'total_tokens': len(full_response) // 4}, 'rewritten_query': rewritten_query}, ensure_ascii=False)
            yield f"data: {done_data}\n\n"
            return
        
        # 构建提示词
        system_prompt = self._build_system_prompt(retrieved_chunks)
        
        # 流式调用LLM
        llm_start = time.time()
        full_response = ""
        prompt_tokens = 0
        completion_tokens = 0
        
        try:
            # 使用线程池执行同步的 OpenAI 流式调用
            loop = asyncio.get_event_loop()
            
            def generate_stream():
                stream = self.client.chat.completions.create(
                    model=settings.llm_model,
                    messages=[
                        {"role": "system", "content": system_prompt},
                        *context_messages,
                        {"role": "user", "content": query}
                    ],
                    stream=True
                )
                for chunk in stream:
                    if chunk.choices and chunk.choices[0].delta.content:
                        yield chunk.choices[0].delta.content
            
            for content in generate_stream():
                full_response += content
                completion_tokens += 1  # 估算 completion tokens
                yield f"data: {json.dumps({'type': 'chunk', 'content': content}, ensure_ascii=False)}\n\n"
                # 让出控制权，确保流式输出
                await asyncio.sleep(0)
            
            # 估算 prompt tokens（系统提示词 + 用户输入 + 检索内容）
            prompt_tokens = len(system_prompt.encode('utf-8')) // 4 + len(query.encode('utf-8')) // 4
            for msg in (context_messages or []):
                prompt_tokens += len(msg.get('content', '').encode('utf-8')) // 4
            
            generation_time = (time.time() - llm_start) * 1000
            total_time = (time.time() - start_time) * 1000
            
            # 保存消息
            self._save_message(conversation_id, "user", query)
            assistant_msg_id = self._save_message(conversation_id, "assistant", full_response)
            
            # 更新对话历史
            self._update_conversation_history(conversation_id, query, full_response)
            
            # 记录日志
            self._log_query(
                query, retrieved_chunks, {"content": full_response}, 
                retrieval_time, generation_time, total_time,
                rewritten_query=rewritten_query
            )
            
            # 构建来源信息
            sources = [
                {
                    "content": c["content"][:100] + "...",
                    "similarity": c.get("rerank_score", c.get("similarity", 0))
                }
                for c in retrieved_chunks
            ]
            
            # 调试信息
            print(f"[DEBUG] retrieved_chunks: {len(retrieved_chunks)}")
            print(f"[DEBUG] sources: {sources}")
            
            done_data = json.dumps({
                'type': 'done', 
                'conversation_id': conversation_id, 
                'message_id': assistant_msg_id, 
                'total_time_ms': total_time, 
                'sources': sources, 
                'tokens': {
                    'prompt_tokens': prompt_tokens, 
                    'completion_tokens': completion_tokens, 
                    'total_tokens': prompt_tokens + completion_tokens
                },
                'rewritten_query': rewritten_query
            }, ensure_ascii=False)
            yield f"data: {done_data}\n\n"
            
        except Exception as e:
            yield f"data: {json.dumps({'type': 'error', 'message': str(e)}, ensure_ascii=False)}\n\n"
    
    def _create_conversation(self, title: str) -> str:
        """创建新对话"""
        import uuid
        db = SessionLocal()
        try:
            conv = Conversation(
                id=str(uuid.uuid4()),
                title=title[:50]
            )
            db.add(conv)
            db.commit()
            return conv.id
        finally:
            db.close()
    
    def _build_system_prompt(self, retrieved_chunks: List[dict]) -> str:
        """构建系统提示词"""
        prompt = """你是一个专业的主播智能问答助手，专注于直播和电商领域。你的职责是：
1. 根据参考信息回答用户问题
2. 提供准确、有用的信息
3. 保持友好、专业的态度

请根据以下参考信息回答问题：
"""
        if retrieved_chunks:
            for i, chunk in enumerate(retrieved_chunks, 1):
                prompt += f"\n[{i}] {chunk['content']}\n"
        else:
            prompt += "\n（暂无参考信息）\n"
        
        prompt += "\n请只根据参考信息回答问题。如果参考信息中没有相关内容，请说明你无法回答该问题。"
        return prompt
    
    def _call_llm(self, system_prompt: str, query: str, context_messages: List[dict]) -> dict:
        """调用LLM生成回答"""
        try:
            response = self.client.chat.completions.create(
                model=settings.llm_model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    *context_messages,
                    {"role": "user", "content": query}
                ]
            )
            
            content = response.choices[0].message.content
            tokens_used = response.usage.total_tokens if response.usage else 0
            
            return {
                "content": content,
                "tokens_used": tokens_used,
                "confidence": "high" if tokens_used > 0 else "low"
            }
        except Exception as e:
            return {
                "content": f"抱歉，暂时无法回答：{str(e)}",
                "tokens_used": 0,
                "confidence": "low"
            }
    
    def _save_message(self, conversation_id: str, role: str, content: str, sources: Optional[list] = None) -> int:
        """保存消息，返回消息ID"""
        db = SessionLocal()
        try:
            msg = Message(
                conversation_id=conversation_id,
                role=role,
                content=content,
                sources=sources
            )
            db.add(msg)
            db.commit()
            db.refresh(msg)
            return msg.id
        finally:
            db.close()
    
    def _log_query(self, query: str, chunks: list, response: dict, retrieval_time: float, generation_time: float, total_time: float, rewritten_query: str = None):
        """记录查询日志"""
        db = SessionLocal()
        try:
            log = Log(
                query=query,
                retrieved_chunks=[c.get("content", "") for c in chunks],
                llm_response=response.get("content", ""),
                retrieval_time_ms=retrieval_time,
                generation_time_ms=generation_time,
                total_time_ms=total_time
            )
            db.add(log)
            db.commit()
        finally:
            db.close()
    
    def _format_history(self, messages: List[dict]) -> str:
        """格式化对话历史"""
        history_parts = []
        for msg in messages[-6:]:  # 只取最近6条消息
            role = msg.get("role", "user")
            content = msg.get("content", "")
            history_parts.append(f"{role}: {content}")
        return "\n".join(history_parts)
    
    def _update_conversation_history(self, conversation_id: str, user_query: str, assistant_response: str):
        """更新对话历史缓存"""
        if conversation_id not in self.conversation_histories:
            self.conversation_histories[conversation_id] = []
        
        self.conversation_histories[conversation_id].append({
            "role": "user",
            "content": user_query
        })
        self.conversation_histories[conversation_id].append({
            "role": "assistant",
            "content": assistant_response
        })
        
        # 限制历史长度（保留最近10轮对话）
        if len(self.conversation_histories[conversation_id]) > 20:
            self.conversation_histories[conversation_id] = self.conversation_histories[conversation_id][-20:]
    
    def get_conversation_history(self, conversation_id: str) -> List[dict]:
        """获取对话历史"""
        return self.conversation_histories.get(conversation_id, [])
    
    def clear_conversation_history(self, conversation_id: str):
        """清空对话历史"""
        if conversation_id in self.conversation_histories:
            del self.conversation_histories[conversation_id]


# 全局实例
chat_service = ChatService()