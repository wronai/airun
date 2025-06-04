"""
Unit tests for script detector module.
"""
import pytest
import tempfile
import os
from pathlib import Path

from airun.core.detector import ScriptDetector, ScriptType


class TestScriptDetector:
    """Test cases for ScriptDetector class."""

    def setup_method(self):
        """Set up test fixtures."""
        self.detector = ScriptDetector()
        self.temp_dir = tempfile.mkdtemp()

    def teardown_method(self):
        """Clean up test fixtures."""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def create_test_file(self, filename: str, content: str, executable: bool = False) -> str:
        """Create a test file with given content."""
        filepath = os.path.join(self.temp_dir, filename)
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)

        if executable:
            os.chmod(filepath, 0o755)

        return filepath

    def test_detect_python_by_extension(self):
        """Test Python detection by file extension."""
        # Test various Python extensions
        test_cases = [
            ('script.py', ScriptType.PYTHON),
            ('module.pyw', ScriptType.PYTHON),
            ('script.py3', ScriptType.PYTHON),
            ('SCRIPT.PY', ScriptType.PYTHON),  # Case insensitive
        ]

        for filename, expected_type in test_cases:
            filepath = self.create_test_file(filename, "print('hello')")
            assert self.detector.detect_type(filepath) == expected_type

    def test_detect_shell_by_extension(self):
        """Test shell script detection by file extension."""
        test_cases = [
            ('script.sh', ScriptType.SHELL),
            ('script.bash', ScriptType.SHELL),
            ('script.zsh', ScriptType.SHELL),
            ('script.fish', ScriptType.SHELL),
        ]

        for filename, expected_type in test_cases:
            filepath = self.create_test_file(filename, "echo 'hello'")
            assert self.detector.detect_type(filepath) == expected_type

    def test_detect_nodejs_by_extension(self):
        """Test Node.js detection by file extension."""
        test_cases = [
            ('app.js', ScriptType.NODEJS),
            ('module.mjs', ScriptType.NODEJS),
            ('component.jsx', ScriptType.NODEJS),
            ('types.ts', ScriptType.NODEJS),
            ('app.tsx', ScriptType.NODEJS),
        ]

        for filename, expected_type in test_cases:
            filepath = self.create_test_file(filename, "console.log('hello')")
            assert self.detector.detect_type(filepath) == expected_type

    def test_detect_php_by_content(self):
        """Test PHP detection by content analysis."""
        php_content = """
<?php
function processData($data) {
    echo "Processing: " . $data;
    return $_POST['result'];
}

$input = $_GET['input'];
$result = processData($input);
echo $result;
?>
"""
        filepath = self.create_test_file('unknown_file', php_content)
        assert self.detector.detect_type(filepath) == ScriptType.PHP

    def test_extension_priority_over_content(self):
        """Test that extension detection has priority over content."""
        # Python content in a .js file should be detected as Node.js
        python_content = "print('This looks like Python')"
        filepath = self.create_test_file('script.js', python_content)
        assert self.detector.detect_type(filepath) == ScriptType.NODEJS

    def test_shebang_priority_over_extension(self):
        """Test that shebang detection has priority over extension when no extension."""
        content = "#!/usr/bin/python3\nconsole.log('mixed content')"
        filepath = self.create_test_file('script', content)
        assert self.detector.detect_type(filepath) == ScriptType.PYTHON

    def test_unknown_file_type(self):
        """Test detection of unknown file types."""
        # File with no recognizable patterns
        content = "This is just plain text with no code patterns."
        filepath = self.create_test_file('readme.txt', content)
        assert self.detector.detect_type(filepath) == ScriptType.UNKNOWN

    def test_empty_file(self):
        """Test detection of empty files."""
        filepath = self.create_test_file('empty.py', '')
        # Should detect by extension even if empty
        assert self.detector.detect_type(filepath) == ScriptType.PYTHON

        filepath = self.create_test_file('empty', '')
        assert self.detector.detect_type(filepath) == ScriptType.UNKNOWN

    def test_confidence_scores(self):
        """Test confidence scoring functionality."""
        python_content = """
import sys
def main():
    print("Hello")
if __name__ == "__main__":
    main()
"""
        filepath = self.create_test_file('script.py', python_content)
        scores = self.detector.get_confidence_scores(filepath)

        # Python should have highest score
        assert scores[ScriptType.PYTHON] > scores[ScriptType.SHELL]
        assert scores[ScriptType.PYTHON] > scores[ScriptType.NODEJS]
        assert scores[ScriptType.PYTHON] > scores[ScriptType.PHP]

    def test_confidence_threshold(self):
        """Test custom confidence threshold."""
        detector = ScriptDetector(confidence_threshold=0.8)

        # Weak content patterns should not trigger detection
        weak_content = "print"  # Only one weak pattern
        filepath = self.create_test_file('ambiguous', weak_content)
        assert detector.detect_type(filepath) == ScriptType.UNKNOWN

    def test_is_executable(self):
        """Test executable file detection."""
        # Create executable file
        filepath = self.create_test_file('script.py', 'print("hello")', executable=True)
        assert self.detector.is_executable(filepath)

        # Create non-executable file
        filepath = self.create_test_file('script2.py', 'print("hello")', executable=False)
        assert not self.detector.is_executable(filepath)

    def test_get_file_info(self):
        """Test comprehensive file information."""
        content = """#!/usr/bin/python3
import sys
print("Hello World")
"""
        filepath = self.create_test_file('info_test.py', content, executable=True)

        info = self.detector.get_file_info(filepath)

        assert info['exists'] is True
        assert info['extension'] == '.py'
        assert info['is_executable'] is True
        assert info['detected_type'] == ScriptType.PYTHON
        assert info['shebang'] == '#!/usr/bin/python3'
        assert isinstance(info['confidence_scores'], dict)
        assert info['size'] > 0

    def test_nonexistent_file(self):
        """Test handling of non-existent files."""
        nonexistent = '/path/that/does/not/exist.py'

        # Should not crash
        result = self.detector.detect_type(nonexistent)
        assert result == ScriptType.UNKNOWN

        # File info should handle gracefully
        info = self.detector.get_file_info(nonexistent)
        assert info['exists'] is False
        assert info['size'] == 0

    def test_binary_file_handling(self):
        """Test handling of binary files."""
        # Create a file with binary content
        binary_path = os.path.join(self.temp_dir, 'binary.exe')
        with open(binary_path, 'wb') as f:
            f.write(b'\x00\x01\x02\x03\xFF\xFE')

        # Should not crash on binary files
        result = self.detector.detect_type(binary_path)
        assert result == ScriptType.UNKNOWN

    def test_large_file_handling(self):
        """Test handling of large files efficiently."""
        # Create a large file with repetitive content
        large_content = "print('line')\n" * 10000
        filepath = self.create_test_file('large.py', large_content)

        # Should still detect correctly and not take too long
        import time
        start = time.time()
        result = self.detector.detect_type(filepath)
        duration = time.time() - start

        assert result == ScriptType.PYTHON
        assert duration < 1.0  # Should be fast

    def test_mixed_content_detection(self):
        """Test detection with mixed language patterns."""
        mixed_content = """#!/bin/bash
# This script has mixed patterns
echo "Starting Python script..."
python3 -c "
import sys
print('Hello from Python')
console.log('This looks like JS but is in Python string')
"
echo "Done"
"""
        filepath = self.create_test_file('mixed', mixed_content)
        # Should detect as shell due to shebang priority
        assert self.detector.detect_type(filepath) == ScriptType.SHELL

    def test_unicode_content(self):
        """Test handling of unicode content."""
        unicode_content = """#!/usr/bin/python3
# -*- coding: utf-8 -*-
print("Hello, 世界! 🌍")
def greet(name):
    return f"Привет, {name}!"
"""
        filepath = self.create_test_file('unicode.py', unicode_content)
        assert self.detector.detect_type(filepath) == ScriptType.PYTHON

    def test_case_insensitive_extensions(self):
        """Test case insensitive extension handling."""
        test_cases = [
            ('Script.PY', ScriptType.PYTHON),
            ('APP.JS', ScriptType.NODEJS),
            ('script.SH', ScriptType.SHELL),
            ('index.PHP', ScriptType.PHP),
        ]

        for filename, expected_type in test_cases:
            filepath = self.create_test_file(filename, "# content")
            assert self.detector.detect_type(filepath) == expected_type


class TestScriptTypeEnum:
    """Test cases for ScriptType enum."""

    def test_enum_values(self):
        """Test enum string values."""
        assert ScriptType.PYTHON.value == "python"
        assert ScriptType.SHELL.value == "shell"
        assert ScriptType.NODEJS.value == "nodejs"
        assert ScriptType.PHP.value == "php"
        assert ScriptType.UNKNOWN.value == "unknown"

    def test_enum_comparison(self):
        """Test enum comparison."""
        assert ScriptType.PYTHON == ScriptType.PYTHON
        assert ScriptType.PYTHON != ScriptType.SHELL

    def test_enum_in_collections(self):
        """Test enum usage in collections."""
        supported_types = {ScriptType.PYTHON, ScriptType.SHELL}
        assert ScriptType.PYTHON in supported_types
        assert ScriptType.UNKNOWN not in supported_types


@pytest.fixture
def sample_scripts():
    """Fixture providing sample script contents."""
    return {
        'python': """
import os
import sys
from pathlib import Path

def main():
    print("Python script example")
    path = Path(__file__).parent
    
if __name__ == "__main__":
    main()
""",
        'shell': """
#!/bin/bash
set -e

export VAR="test"
echo "Shell script example"
mkdir -p /tmp/test
cd /tmp/test
chmod +x script.sh
""",
        'nodejs': """
const fs = require('fs');
const path = require('path');

function main() {
    console.log('Node.js script example');
    let data = fs.readFileSync('file.txt', 'utf8');
}

main();
""",
        'php': """
<?php
function processRequest() {
    echo "PHP script example";
    $data = $_POST['data'];
    return $data;
}

$result = processRequest();
echo $result;
?>
"""
    }


class TestDetectorWithFixtures:
    """Test detector with realistic script fixtures."""

    def setup_method(self):
        """Set up test fixtures."""
        self.detector = ScriptDetector()
        self.temp_dir = tempfile.mkdtemp()

    def teardown_method(self):
        """Clean up test fixtures."""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_realistic_scripts(self, sample_scripts):
        """Test detection with realistic script samples."""
        expected_types = {
            'python': ScriptType.PYTHON,
            'shell': ScriptType.SHELL,
            'nodejs': ScriptType.NODEJS,
            'php': ScriptType.PHP,
        }

        for script_type, content in sample_scripts.items():
            filepath = os.path.join(self.temp_dir, f'test.{script_type}')
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(content)

            detected = self.detector.detect_type(filepath)
            expected = expected_types[script_type]
            assert detected == expected, f"Failed to detect {script_type}: got {detected}, expected {expected}"

    def test_confidence_with_realistic_scripts(self, sample_scripts):
        """Test confidence scores with realistic scripts."""
        for script_type, content in sample_scripts.items():
            filepath = os.path.join(self.temp_dir, f'test_{script_type}')
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(content)

            scores = self.detector.get_confidence_scores(filepath)
            expected_type = getattr(ScriptType, script_type.upper())

            # The correct type should have the highest score
            max_score_type = max(scores, key=scores.get)
            assert max_score_type == expected_type, f"Confidence scores incorrect for {script_type}"by_extension(self):
        """Test PHP detection by file extension."""
        test_cases = [
            ('index.php', ScriptType.PHP),
            ('script.php3', ScriptType.PHP),
            ('page.phtml', ScriptType.PHP),
        ]

        for filename, expected_type in test_cases:
            filepath = self.create_test_file(filename, "<?php echo 'hello'; ?>")
            assert self.detector.detect_type(filepath) == expected_type

    def test_detect_by_shebang(self):
        """Test script detection by shebang."""
        test_cases = [
            ('#!/usr/bin/python3\nprint("hello")', ScriptType.PYTHON),
            ('#!/usr/bin/env python\nprint("hello")', ScriptType.PYTHON),
            ('#!/bin/bash\necho "hello"', ScriptType.SHELL),
            ('#!/bin/sh\necho "hello"', ScriptType.SHELL),
            ('#!/usr/bin/env bash\necho "hello"', ScriptType.SHELL),
            ('#!/usr/bin/node\nconsole.log("hello")', ScriptType.NODEJS),
            ('#!/usr/bin/env node\nconsole.log("hello")', ScriptType.NODEJS),
            ('#!/usr/bin/php\n<?php echo "hello"; ?>', ScriptType.PHP),
        ]

        for content, expected_type in test_cases:
            filepath = self.create_test_file('test_script', content)
            assert self.detector.detect_type(filepath) == expected_type

    def test_detect_python_by_content(self):
        """Test Python detection by content analysis."""
        python_content = """
import os
import sys

def main():
    print("Hello, World!")
    
if __name__ == "__main__":
    main()
"""
        filepath = self.create_test_file('unknown_file', python_content)
        assert self.detector.detect_type(filepath) == ScriptType.PYTHON

    def test_detect_shell_by_content(self):
        """Test shell script detection by content analysis."""
        shell_content = """
export PATH=/usr/local/bin:$PATH
mkdir -p /tmp/test
echo "Starting process..."
cd /tmp/test
chmod +x script.sh
"""
        filepath = self.create_test_file('unknown_file', shell_content)
        assert self.detector.detect_type(filepath) == ScriptType.SHELL

    def test_detect_nodejs_by_content(self):
        """Test Node.js detection by content analysis."""
        nodejs_content = """
const express = require('express');
const app = express();

app.get('/', (req, res) => {
    console.log('Request received');
    res.send('Hello World!');
});

let port = 3000;
app.listen(port, function() {
    console.log(`Server running on port ${port}`);
});
"""
        filepath = self.create_test_file('unknown_file', nodejs_content)
        assert self.detector.detect_type(filepath) == ScriptType.NODEJS

    def test_detect_php_