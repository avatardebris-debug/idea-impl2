class ParserPlugin:
    PLUGIN_TYPE = "parser"
    
    def parse(self, content: str) -> list[dict]:
        raise NotImplementedError
        
class CveSourcePlugin:
    PLUGIN_TYPE = "cve_source"
    
    def fetch_by_package(self, package: str, version: str) -> list[dict]:
        raise NotImplementedError

class ReportTemplatePlugin:
    PLUGIN_TYPE = "report"
    
    def generate(self, findings: list[dict]) -> str:
        raise NotImplementedError
