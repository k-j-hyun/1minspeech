def simple_text_splitter(text, chunk_size=500, chunk_overlap=100):
    """메모리 효율적인 텍스트 분할"""
    if not text or len(text.strip()) < 10:
        return []
    
    # 찭크 크기를 줄여 메모리 사용량 감소
    chunks = []
    start = 0
    text_length = len(text)
    
    # 최대 찭크 수 제한 (메모리 보호)
    max_chunks = 20
    
    while start < text_length and len(chunks) < max_chunks:
        end = start + chunk_size
        if end > text_length:
            end = text_length
        
        chunk = text[start:end].strip()
        if chunk and len(chunk) > 10:  # 너무 짧은 찭크 제외
            chunks.append(chunk)
        
        start = end - chunk_overlap
        if start < 0:
            start = 0
    
    print(f"텍스트 분할 완료: {len(chunks)}개 찭크 (최대 {max_chunks}개)")
    return chunks