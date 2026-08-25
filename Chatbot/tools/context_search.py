import re

class ContextSearchTool:
    name = "context_search"
    
    def execute(self, query: str, context: str) -> str:
        if not context or not context.strip():
            return "No active context available to search."

        lines = [line.strip() for line in context.split("\n") if line.strip()]
        keywords = set(re.findall(r'\w+', query.lower())) - {"what", "is", "the", "are", "how", "many", "of", "in", "does"}
        
        matches = []
        for line in lines:
            intersection = keywords.intersection(set(re.findall(r'\w+', line.lower())))
            if intersection:
                matches.append((len(intersection), line))

        if matches:
            matches.sort(key=lambda x: x[0], reverse=True)
            return "\n".join([item[1] for item in matches[:3]])
        
        return "Context content:\n" + "\n".join(lines)