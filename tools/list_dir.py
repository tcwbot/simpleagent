import subprocess

SCHEMA = {
    'type': 'function',
    'function': {
        'name': 'list_dir',
        'description': 'List all files with details (permissions, size). Executables are marked with x in permissions.',
        'parameters': {
            'type': 'object',
            'properties': {
                'path': {
                    'type': 'string', 
                    'description': 'The directory path to list.',
                    'default': '.'
                }
            },
            'required': ['path']
        }
    }
}

def execute(path="."):
    """Provides a detailed directory listing similar to ll or ls -lah."""
    target_path = path if path and path.strip() else "."
    
    try:
        # -l: long format (shows permissions like -rwxr-xr-x)
        # -a: show hidden files
        # -h: human-readable sizes
        result = subprocess.check_output(['ls', '-lah', target_path], text=True)
        return f"DETAILED FILESYSTEM OUTPUT for {target_path}:\n{result}"
    except Exception as e:
        return f"Error listing directory '{target_path}': {e}"
