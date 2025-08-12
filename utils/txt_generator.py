def generate_txt_report(content, output_path):
    """텍스트를 TXT 형식으로 저장"""
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write("=== AI 생성 보고서 ===\n\n")
        f.write(content)