from ..interfaces import IParser
from ..models import Document
import uuid

class TxtParser(IParser):
    def parse(self, content: bytes, filename: str) -> Document:
        # 工业级严格解码与异常处理
        try:
            text = content.decode('utf-8')
        except UnicodeDecodeError:
            text = content.decode('gbk', errors='ignore')
        return Document(doc_id=str(uuid.uuid4()), text=text, metadata={"source": filename})
