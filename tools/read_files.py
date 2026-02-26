import os

SCHEMA = {
    'type': 'function',
    'function': {
        'name': 'read_file',
        'description': 'Read the contents of a specific local file.',
        'parameters': {
            'type': 'object',
            'properties': {
                'path': {'type': 'string', 'description': 'The relative or absolute path to the file'},
            },
            'required': ['path'],
        },
    },
}

def execute(path: str):
    try:
        # Security check: you might want to restrict this to certain directories
        if not os.path.exists(path):
            return f"Error: File {path} not found."
            
        with open(path, 'r') as f:
            content = f.read()
        return f"--- CONTENTS OF {path} ---\n{content}"
    except Exception as e:
        return f"Error reading file: {e}"
