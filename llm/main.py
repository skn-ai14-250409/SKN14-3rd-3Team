from llm_model import enhanced_chain

# 사용자 인터페이스 - 대화형 챗봇
def run_chatbot():
    print("="*60)
    print("🤖 삼성 BESPOKE AI 콤보 도우미에 오신 것을 환영합니다!")
    print("="*60)
    print("질문을 입력하시면 답변해드립니다.")
    print("종료하시려면 '종료'를 입력하세요.")
    print("="*60)
    
    while True:
        try:
            query = input("\n💬 질문을 입력하세요: ").strip()
            
            # 종료 조건 확인
            if query.lower() in ['종료']:
                print("\n" + "="*60)
                print("👋 도우미를 종료합니다. 이용해 주셔서 감사합니다!")
                print("="*60)
                break
            
            # 빈 입력 처리
            if not query:
                print("❌ 질문을 입력해주세요.")
                continue
            
            print("\n🤔 답변을 생성하고 있습니다...")
            
            # 답변 생성
            result = enhanced_chain(query)
            
            print("\n" + "="*60)
            print("📝 답변:")
            print("="*60)
            print(result.content)
            print("="*60)
            
        except KeyboardInterrupt:
            print("\n\n👋 프로그램이 중단되었습니다. 이용해 주셔서 감사합니다!")
            break
        except Exception as e:
            print(f"\n❌ 오류가 발생했습니다: {str(e)}")
            print("다시 시도해주세요.")

# 챗봇 실행
if __name__ == "__main__":
    run_chatbot()
