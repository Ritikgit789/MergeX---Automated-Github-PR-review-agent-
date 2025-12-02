"""Language detector for identifying programming languages from file extensions."""
from typing import Optional
from pathlib import Path


class LanguageDetector:
    """Detects programming language from file extensions."""
    
    # Comprehensive mapping of file extensions to language names
    EXTENSION_MAP = {
        # Python
        '.py': 'python',
        '.pyw': 'python',
        '.pyi': 'python',
        
        # JavaScript/TypeScript
        '.js': 'javascript',
        '.jsx': 'javascript',
        '.mjs': 'javascript',
        '.cjs': 'javascript',
        '.ts': 'typescript',
        '.tsx': 'typescript',
        
        # Web
        '.html': 'html',
        '.htm': 'html',
        '.css': 'css',
        '.scss': 'scss',
        '.sass': 'sass',
        '.less': 'less',
        
        # Java/JVM
        '.java': 'java',
        '.kt': 'kotlin',
        '.kts': 'kotlin',
        '.scala': 'scala',
        '.groovy': 'groovy',
        
        # C/C++
        '.c': 'c',
        '.h': 'c',
        '.cpp': 'cpp',
        '.cc': 'cpp',
        '.cxx': 'cpp',
        '.hpp': 'cpp',
        '.hh': 'cpp',
        '.hxx': 'cpp',
        
        # C#
        '.cs': 'csharp',
        
        # Go
        '.go': 'go',
        
        # Rust
        '.rs': 'rust',
        
        # Ruby
        '.rb': 'ruby',
        '.rake': 'ruby',
        
        # PHP
        '.php': 'php',
        '.phtml': 'php',
        
        # Swift
        '.swift': 'swift',
        
        # Objective-C
        '.m': 'objective-c',
        '.mm': 'objective-c',
        
        # Shell
        '.sh': 'shell',
        '.bash': 'bash',
        '.zsh': 'zsh',
        
        # R
        '.r': 'r',
        '.R': 'r',
        
        # Dart
        '.dart': 'dart',
        
        # Elixir
        '.ex': 'elixir',
        '.exs': 'elixir',
        
        # Haskell
        '.hs': 'haskell',
        
        # Lua
        '.lua': 'lua',
        
        # Perl
        '.pl': 'perl',
        '.pm': 'perl',
        
        # SQL
        '.sql': 'sql',
        
        # YAML/JSON/TOML
        '.yaml': 'yaml',
        '.yml': 'yaml',
        '.json': 'json',
        '.toml': 'toml',
        
        # Markdown
        '.md': 'markdown',
        '.markdown': 'markdown',
        
        # Configuration
        '.xml': 'xml',
        '.ini': 'ini',
        '.conf': 'conf',
        '.config': 'config',
        
        # Other
        '.vim': 'vim',
        '.dockerfile': 'dockerfile',
    }
    
    # Special filenames
    FILENAME_MAP = {
        'dockerfile': 'dockerfile',
        'makefile': 'makefile',
        'rakefile': 'ruby',
        'gemfile': 'ruby',
        'vagrantfile': 'ruby',
    }
    
    def detect_language(self, file_path: str) -> str:
        """
        Detect programming language from file path.
        
        Args:
            file_path: Path to the file
            
        Returns:
            Language name (lowercase) or 'unknown'
        """
        if not file_path:
            return 'unknown'
        
        path = Path(file_path)
        
        # Check special filenames first
        filename_lower = path.name.lower()
        if filename_lower in self.FILENAME_MAP:
            return self.FILENAME_MAP[filename_lower]
        
        # Check file extension
        extension = path.suffix.lower()
        if extension in self.EXTENSION_MAP:
            return self.EXTENSION_MAP[extension]
        
        return 'unknown'
    
    def detect_primary_language(self, file_paths: list[str]) -> str:
        """
        Detect the primary language from a list of file paths.
        
        Args:
            file_paths: List of file paths
            
        Returns:
            Most common language or 'unknown'
        """
        if not file_paths:
            return 'unknown'
        
        # Count languages
        language_counts = {}
        for file_path in file_paths:
            lang = self.detect_language(file_path)
            if lang != 'unknown':
                language_counts[lang] = language_counts.get(lang, 0) + 1
        
        if not language_counts:
            return 'unknown'
        
        # Return most common language
        return max(language_counts, key=language_counts.get)


# Singleton instance
language_detector = LanguageDetector()
