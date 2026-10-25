import os
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


from PyQt6.QtWidgets import QApplication
from ui.desktop_pyqt import AIAssistantPage, LIGHT, DARK
from core.ai_assistant import ExplainableAIAssistant
from core.vector_search import VectorSearchEngine

def main():
    app = QApplication(sys.argv)
    
    vec = VectorSearchEngine()
    vec.add_document_chunks(
        "doc_legal_1",
        "Master_Agreement.txt",
        "Legal",
        [{"page_number": 1, "text": "Either party may terminate this agreement upon thirty (30) days prior written notice."}]
    )
    vec.build_index()
    assistant = ExplainableAIAssistant(vec)

    # Dark mode test
    theme = DARK
    page = AIAssistantPage(assistant=assistant, theme=theme)
    page.resize(1100, 800)
    page.show()

    # 1. Test conversational greeting
    page.ask_query("hi")
    app.processEvents()

    # 2. Test document search query with evidence sources
    page.ask_query("What is the termination notice period?")
    app.processEvents()

    # Capture visual screenshot of the chat canvas
    out_dir = Path(r"C:\Users\siddh\.gemini\antigravity-ide\brain\b6d2c48b-dac1-447b-ba18-3ce7f04f23d0\.tempmediaStorage")
    out_dir.mkdir(parents=True, exist_ok=True)
    
    pix = page.grab()
    out_path = out_dir / "chatbot_readable_format_verified.png"
    pix.save(str(out_path))
    print(f"Verified Chatbot UI saved to: {out_path}")

    # Also test Light mode
    page.update_theme(LIGHT)
    app.processEvents()
    pix_light = page.grab()
    out_light_path = out_dir / "chatbot_readable_format_light.png"
    pix_light.save(str(out_light_path))
    print(f"Verified Light Chatbot UI saved to: {out_light_path}")

if __name__ == "__main__":
    main()
