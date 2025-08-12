"""
간단한 문법 검사 스크립트
"""
import ast
import os

def check_syntax(file_path):
    """파이썬 파일의 문법을 검사합니다."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            source = f.read()
        
        # AST 파싱으로 문법 검사
        ast.parse(source)
        return True, "✅ 문법 오류 없음"
    
    except SyntaxError as e:
        return False, f"❌ 문법 오류: {e.msg} (라인 {e.lineno})"
    except Exception as e:
        return False, f"❌ 파일 읽기 오류: {e}"

def main():
    """주요 파이썬 파일들의 문법을 검사합니다."""
    print("=== FlowMate 문법 검사 ===\n")
    
    base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
    
    files_to_check = [
        'app.py',
        'run_app.py',
        'config/settings.py',
        'core/embeddings.py',
        'core/vector_store.py',
        'core/llm_handler.py',
        'core/memory.py',
        'utils/file_parser.py',
        'utils/chunking.py',
        'utils/docx_generator.py',
        'utils/txt_generator.py'
    ]
    
    all_passed = True
    
    for file_path in files_to_check:
        full_path = os.path.join(base_dir, file_path)
        if os.path.exists(full_path):
            success, message = check_syntax(full_path)
            print(f"{file_path}: {message}")
            if not success:
                all_passed = False
        else:
            print(f"{file_path}: ❌ 파일 없음")
            all_passed = False
    
    print(f"\n=== 검사 결과 ===")
    if all_passed:
        print("✅ 모든 파일의 문법이 정상입니다!")
    else:
        print("❌ 일부 파일에 문제가 있습니다.")
    
    return all_passed

if __name__ == "__main__":
    main()
