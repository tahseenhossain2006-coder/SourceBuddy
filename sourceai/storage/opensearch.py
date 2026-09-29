from typing import List, Dict, Any, Optional
from opensearchpy import OpenSearch, RequestsHttpConnection
import os
import logging

logger = logging.getLogger(__name__)

class OpenSearchIndexer:
    def __init__(self):
        self.client: Optional[OpenSearch] = None
        self.index_name: str = "suppliers"

    def connect(self) -> None:
        self.client = OpenSearch(
            hosts=[{"host": os.getenv("OPENSEARCH_HOST", "localhost"), "port": int(os.getenv("OPENSEARCH_PORT", "9200"))}],
            http_auth=(os.getenv("OPENSEARCH_USER", "admin"), os.getenv("OPENSEARCH_PASS", "admin")),
            use_ssl=False,
            verify_certs=False,
            connection_class=RequestsHttpConnection,
        )
        self._create_index()

    def _create_index(self) -> None:
        if self.client and not self.client.indices.exists(index=self.index_name):
            self.client.indices.create(
                index=self.index_name,
                body={
                    "mappings": {
                        "properties": {
                            "name": {"type": "text"},
                            "website": {"type": "keyword"},
                            "location": {"type": "text"},
                            "moq": {"type": "integer"},
                            "price": {"type": "float"},
                            "currency": {"type": "keyword"},
                            "country": {"type": "keyword"},
                            "supplier_type": {"type": "keyword"},
                            "products": {"type": "text"},
                            "evidence": {"type": "object", "enabled": False}
                        }
                    }
                }
            )

    def index_suppliers(self, suppliers: List[Dict[str, Any]]) -> None:
        if not self.client:
            self.connect()
        for s in suppliers:
            self.client.index(index=self.index_name, body=s)