"""
Chat Module

LLM-agnostic chat service that orchestrates the complete RAG pipeline.
"""

from .service import ChatService, get_chat_service

__all__ = ['ChatService', 'get_chat_service']
