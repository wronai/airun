"""
File operations utilities for AIRun.
"""
import os
import shutil
import tempfile
import time
from pathlib import Path
from typing import Optional, Union, List
import logging

logger = logging.getLogger(__name__)


def read_file_safe(filepath: Union[str, Path], encoding: str = 'utf-8') -> Optional[str]:
    """
    Safely read file content with error handling.

    Args:
        filepath: Path to file
        encoding: File encoding

    Returns:
        File content or None if failed
    """
    try:
        with open(filepath, 'r', encoding=encoding) as f:
            return f.read()
    except Exception as e:
        logger.error(f"Failed to read file {filepath}: {e}")
        return None


def write_file_safe(filepath: Union[str, Path], content: str,
                   encoding: str = 'utf-8', backup: bool = True) -> bool:
    """
    Safely write content to file with optional backup.

    Args:
        filepath: Path to file
        content: Content to write
        encoding: File encoding
        backup: Create backup before writing

    Returns:
        True if successful, False otherwise
    """
    try:
        filepath = Path(filepath)

        # Create backup if requested and file exists
        if backup and filepath.exists():
            create_backup(str(filepath))

        # Ensure directory exists
        filepath.parent.mkdir(parents=True, exist_ok=True)

        # Write content
        with open(filepath, 'w', encoding=encoding) as f:
            f.write(content)

        logger.debug(f"Successfully wrote file: {filepath}")
        return True

    except Exception as e:
        logger.error(f"Failed to write file {filepath}: {e}")
        return False


def create_backup(filepath: Union[str, Path], backup_dir: Optional[str] = None) -> Optional[str]:
    """
    Create a backup of the specified file.

    Args:
        filepath: Path to file to backup
        backup_dir: Optional backup directory (defaults to same directory)

    Returns:
        Path to backup file or None if failed
    """
    try:
        filepath = Path(filepath)

        if not filepath.exists():
            logger.warning(f"Cannot backup non-existent file: {filepath}")
            return None

        # Determine backup location
        if backup_dir:
            backup_path = Path(backup_dir) / filepath.name
            ensure_directory(backup_dir)
        else:
            backup_path = filepath.parent / f"{filepath.stem}.backup{filepath.suffix}"

        # Add timestamp if backup already exists
        if backup_path.exists():
            timestamp = int(time.time())
            backup_path = backup_path.with_suffix(f".{timestamp}{backup_path.suffix}")

        # Copy file
        shutil.copy2(filepath, backup_path)
        logger.debug(f"Created backup: {backup_path}")

        return str(backup_path)

    except Exception as e:
        logger.error(f"Failed to create backup for {filepath}: {e}")
        return None


def restore_from_backup(backup_path: Union[str, Path],
                       original_path: Union[str, Path]) -> bool:
    """
    Restore file from backup.

    Args:
        backup_path: Path to backup file
        original_path: Path where to restore the file

    Returns:
        True if successful, False otherwise
    """
    try:
        backup_path = Path(backup_path)
        original_path = Path(original_path)

        if not backup_path.exists():
            logger.error(f"Backup file does not exist: {backup_path}")
            return False

        # Ensure target directory exists
        original_path.parent.mkdir(parents=True, exist_ok=True)

        # Copy backup to original location
        shutil.copy2(backup_path, original_path)
        logger.info(f"Restored file from backup: {original_path}")

        return True

    except Exception as e:
        logger.error(f"Failed to restore from backup {backup_path}: {e}")
        return False


def ensure_directory(directory: Union[str, Path]) -> bool:
    """
    Ensure directory exists, creating it if necessary.

    Args:
        directory: Path to directory

    Returns:
        True if directory exists or was created successfully
    """
    try:
        Path(directory).mkdir(parents=True, exist_ok=True)
        return True
    except Exception as e:
        logger.error(f"Failed to create directory {directory}: {e}")
        return False


def list_backups(filepath: Union[str, Path]) -> List[str]:
    """
    List all backup files for the given file.

    Args:
        filepath: Original file path

    Returns:
        List of backup file paths
    """
    try:
        filepath = Path(filepath)
        backup_pattern = f"{filepath.stem}.backup*{filepath.suffix}"

        backups = []
        for backup_file in filepath.parent.glob(backup_pattern):
            backups.append(str(backup_file))

        # Sort by modification time (newest first)
        backups.sort(key=lambda x: os.path.getmtime(x), reverse=True)

        return backups

    except Exception as e:
        logger.error(f"Failed to list backups for {filepath}: {e}")
        return []


def cleanup_old_backups(filepath: Union[str, Path], keep_count: int = 5) -> int:
    """
    Clean up old backup files, keeping only the most recent ones.

    Args:
        filepath: Original file path
        keep_count: Number of backups to keep

    Returns:
        Number of backups removed
    """
    try:
        backups = list_backups(filepath)

        if len(backups) <= keep_count:
            return 0

        # Remove old backups
        removed_count = 0
        for backup_path in backups[keep_count:]:
            try:
                os.remove(backup_path)
                removed_count += 1
                logger.debug(f"Removed old backup: {backup_path}")
            except Exception as e:
                logger.warning(f"Failed to remove backup {backup_path}: {e}")

        return removed_count

    except Exception as e:
        logger.error(f"Failed to cleanup backups for {filepath}: {e}")
        return 0


def get_file_info(filepath: Union[str, Path]) -> dict:
    """
    Get comprehensive file information.

    Args:
        filepath: Path to file

    Returns:
        Dictionary with file information
    """
    try:
        filepath = Path(filepath)

        if not filepath.exists():
            return {
                'exists': False,
                'path': str(filepath),
                'absolute_path': str(filepath.resolve()),
            }

        stat = filepath.stat()

        return {
            'exists': True,
            'path': str(filepath),
            'absolute_path': str(filepath.resolve()),
            'size': stat.st_size,
            'size_human': _format_file_size(stat.st_size),
            'modified_time': stat.st_mtime,
            'created_time': stat.st_ctime,
            'is_file': filepath.is_file(),
            'is_directory': filepath.is_dir(),
            'is_executable': _is_executable(filepath),
            'permissions': oct(stat.st_mode)[-3:],
            'extension': filepath.suffix,
            'stem': filepath.stem,
        }

    except Exception as e:
        logger.error(f"Failed to get file info for {filepath}: {e}")
        return {'exists': False, 'error': str(e)}


def _format_file_size(size_bytes: int) -> str:
    """Format file size in human-readable format."""
    if size_bytes == 0:
        return "0 B"

    size_names = ["B", "KB", "MB", "GB", "TB"]
    i = 0
    while size_bytes >= 1024 and i < len(size_names) - 1:
        size_bytes /= 1024.0
        i += 1

    return f"{size_bytes:.1f} {size_names[i]}"


def _is_executable(filepath: Path) -> bool:
    """Check if file is executable."""
    try:
        return os.access(filepath, os.X_OK)
    except Exception:
        return False


def create_temp_file(content: str = "", suffix: str = "", prefix: str = "airun_") -> str:
    """
    Create a temporary file with given content.

    Args:
        content: Content to write to temp file
        suffix: File suffix
        prefix: File prefix

    Returns:
        Path to temporary file
    """
    try:
        fd, temp_path = tempfile.mkstemp(suffix=suffix, prefix=prefix, text=True)

        with os.fdopen(fd, 'w') as temp_file:
            temp_file.write(content)

        logger.debug(f"Created temporary file: {temp_path}")
        return temp_path

    except Exception as e:
        logger.error(f"Failed to create temporary file: {e}")
        raise


def create_temp_directory(prefix: str = "airun_") -> str:
    """
    Create a temporary directory.

    Args:
        prefix: Directory prefix

    Returns:
        Path to temporary directory
    """
    try:
        temp_dir = tempfile.mkdtemp(prefix=prefix)
        logger.debug(f"Created temporary directory: {temp_dir}")
        return temp_dir

    except Exception as e:
        logger.error(f"Failed to create temporary directory: {e}")
        raise


def copy_file(source: Union[str, Path], destination: Union[str, Path],
              preserve_metadata: bool = True) -> bool:
    """
    Copy file from source to destination.

    Args:
        source: Source file path
        destination: Destination file path
        preserve_metadata: Whether to preserve file metadata

    Returns:
        True if successful, False otherwise
    """
    try:
        source = Path(source)
        destination = Path(destination)

        # Ensure destination directory exists
        destination.parent.mkdir(parents=True, exist_ok=True)

        if preserve_metadata:
            shutil.copy2(source, destination)
        else:
            shutil.copy(source, destination)

        logger.debug(f"Copied file: {source} -> {destination}")
        return True

    except Exception as e:
        logger.error(f"Failed to copy file {source} to {destination}: {e}")
        return False


def move_file(source: Union[str, Path], destination: Union[str, Path]) -> bool:
    """
    Move file from source to destination.

    Args:
        source: Source file path
        destination: Destination file path

    Returns:
        True if successful, False otherwise
    """
    try:
        source = Path(source)
        destination = Path(destination)

        # Ensure destination directory exists
        destination.parent.mkdir(parents=True, exist_ok=True)

        shutil.move(source, destination)
        logger.debug(f"Moved file: {source} -> {destination}")
        return True

    except Exception as e:
        logger.error(f"Failed to move file {source} to {destination}: {e}")
        return False


def delete_file(filepath: Union[str, Path], force: bool = False) -> bool:
    """
    Delete file with optional force flag.

    Args:
        filepath: Path to file to delete
        force: If True, ignore errors and don't prompt

    Returns:
        True if successful, False otherwise
    """
    try:
        filepath = Path(filepath)

        if not filepath.exists():
            logger.warning(f"File does not exist: {filepath}")
            return True  # Consider non-existent as successfully deleted

        if not force and not filepath.is_file():
            logger.error(f"Path is not a file: {filepath}")
            return False

        filepath.unlink()
        logger.debug(f"Deleted file: {filepath}")
        return True

    except Exception as e:
        logger.error(f"Failed to delete file {filepath}: {e}")
        return False


def find_files(directory: Union[str, Path], pattern: str = "*",
               recursive: bool = False) -> List[str]:
    """
    Find files matching pattern in directory.

    Args:
        directory: Directory to search in
        pattern: Glob pattern to match
        recursive: Whether to search recursively

    Returns:
        List of matching file paths
    """
    try:
        directory = Path(directory)

        if not directory.exists():
            logger.warning(f"Directory does not exist: {directory}")
            return []

        if recursive:
            files = directory.rglob(pattern)
        else:
            files = directory.glob(pattern)

        # Filter to only files (not directories)
        file_paths = [str(f) for f in files if f.is_file()]

        logger.debug(f"Found {len(file_paths)} files matching '{pattern}' in {directory}")
        return file_paths

    except Exception as e:
        logger.error(f"Failed to find files in {directory}: {e}")
        return []


def calculate_directory_size(directory: Union[str, Path]) -> int:
    """
    Calculate total size of directory and all its contents.

    Args:
        directory: Path to directory

    Returns:
        Total size in bytes
    """
    try:
        directory = Path(directory)
        total_size = 0

        for file_path in directory.rglob('*'):
            if file_path.is_file():
                try:
                    total_size += file_path.stat().st_size
                except (OSError, ValueError):
                    # Skip files we can't access
                    pass

        return total_size

    except Exception as e:
        logger.error(f"Failed to calculate directory size for {directory}: {e}")
        return 0


def compress_directory(directory: Union[str, Path], output_path: Union[str, Path],
                      format: str = 'zip') -> bool:
    """
    Compress directory into archive.

    Args:
        directory: Directory to compress
        output_path: Output archive path
        format: Archive format ('zip', 'tar', 'gztar', 'bztar', 'xztar')

    Returns:
        True if successful, False otherwise
    """
    try:
        directory = Path(directory)
        output_path = Path(output_path)

        if not directory.exists():
            logger.error(f"Directory does not exist: {directory}")
            return False

        # Ensure output directory exists
        output_path.parent.mkdir(parents=True, exist_ok=True)

        # Remove extension from output path for shutil.make_archive
        archive_base = str(output_path.with_suffix(''))

        shutil.make_archive(archive_base, format, directory)
        logger.info(f"Compressed directory {directory} to {output_path}")
        return True

    except Exception as e:
        logger.error(f"Failed to compress directory {directory}: {e}")
        return False


def extract_archive(archive_path: Union[str, Path], extract_to: Union[str, Path]) -> bool:
    """
    Extract archive to specified directory.

    Args:
        archive_path: Path to archive file
        extract_to: Directory to extract to

    Returns:
        True if successful, False otherwise
    """
    try:
        archive_path = Path(archive_path)
        extract_to = Path(extract_to)

        if not archive_path.exists():
            logger.error(f"Archive does not exist: {archive_path}")
            return False

        # Ensure extraction directory exists
        extract_to.mkdir(parents=True, exist_ok=True)

        shutil.unpack_archive(archive_path, extract_to)
        logger.info(f"Extracted archive {archive_path} to {extract_to}")
        return True

    except Exception as e:
        logger.error(f"Failed to extract archive {archive_path}: {e}")
        return False


def sync_directories(source: Union[str, Path], destination: Union[str, Path],
                    delete_extra: bool = False) -> bool:
    """
    Synchronize source directory to destination.

    Args:
        source: Source directory
        destination: Destination directory
        delete_extra: Whether to delete files in destination not in source

    Returns:
        True if successful, False otherwise
    """
    try:
        source = Path(source)
        destination = Path(destination)

        if not source.exists():
            logger.error(f"Source directory does not exist: {source}")
            return False

        # Ensure destination exists
        destination.mkdir(parents=True, exist_ok=True)

        # Copy/update files
        for source_file in source.rglob('*'):
            if source_file.is_file():
                relative_path = source_file.relative_to(source)
                dest_file = destination / relative_path

                # Ensure destination directory exists
                dest_file.parent.mkdir(parents=True, exist_ok=True)

                # Copy if destination doesn't exist or source is newer
                if (not dest_file.exists() or
                    source_file.stat().st_mtime > dest_file.stat().st_mtime):
                    shutil.copy2(source_file, dest_file)

        # Delete extra files if requested
        if delete_extra:
            for dest_file in destination.rglob('*'):
                if dest_file.is_file():
                    relative_path = dest_file.relative_to(destination)
                    source_file = source / relative_path

                    if not source_file.exists():
                        dest_file.unlink()

        logger.info(f"Synchronized directory {source} to {destination}")
        return True

    except Exception as e:
        logger.error(f"Failed to sync directories {source} -> {destination}: {e}")
        return False


def create_file_from_template(template_path: Union[str, Path],
                             output_path: Union[str, Path],
                             variables: dict = None) -> bool:
    """
    Create file from template with variable substitution.

    Args:
        template_path: Path to template file
        output_path: Path for output file
        variables: Dictionary of variables for substitution

    Returns:
        True if successful, False otherwise
    """
    try:
        template_content = read_file_safe(template_path)
        if template_content is None:
            return False

        # Perform variable substitution
        if variables:
            for key, value in variables.items():
                template_content = template_content.replace(f"{{{key}}}", str(value))
                template_content = template_content.replace(f"{{{{ {key} }}}}", str(value))

        return write_file_safe(output_path, template_content, backup=False)

    except Exception as e:
        logger.error(f"Failed to create file from template {template_path}: {e}")
        return False


def watch_file_changes(filepath: Union[str, Path], callback, interval: float = 1.0):
    """
    Watch file for changes and call callback when modified.

    Args:
        filepath: Path to file to watch
        callback: Function to call when file changes
        interval: Check interval in seconds

    Note:
        This is a simple polling-based implementation.
        For production use, consider using a proper file watching library.
    """
    import time

    filepath = Path(filepath)
    last_mtime = 0

    if filepath.exists():
        last_mtime = filepath.stat().st_mtime

    logger.info(f"Watching file for changes: {filepath}")

    try:
        while True:
            time.sleep(interval)

            if filepath.exists():
                current_mtime = filepath.stat().st_mtime
                if current_mtime > last_mtime:
                    logger.debug(f"File changed: {filepath}")
                    callback(str(filepath))
                    last_mtime = current_mtime
            elif last_mtime > 0:
                # File was deleted
                logger.debug(f"File deleted: {filepath}")
                callback(str(filepath))
                last_mtime = 0

    except KeyboardInterrupt:
        logger.info("File watching stopped")
    except Exception as e:
        logger.error(f"Error watching file {filepath}: {e}")


class FileManager:
    """High-level file management utility class."""

    def __init__(self, base_directory: Union[str, Path] = None):
        """
        Initialize file manager.

        Args:
            base_directory: Base directory for operations
        """
        self.base_directory = Path(base_directory) if base_directory else Path.cwd()
        ensure_directory(self.base_directory)

    def get_path(self, relative_path: str) -> Path:
        """Get absolute path relative to base directory."""
        return self.base_directory / relative_path

    def read(self, relative_path: str) -> Optional[str]:
        """Read file content."""
        return read_file_safe(self.get_path(relative_path))

    def write(self, relative_path: str, content: str, backup: bool = True) -> bool:
        """Write content to file."""
        return write_file_safe(self.get_path(relative_path), content, backup=backup)

    def backup(self, relative_path: str) -> Optional[str]:
        """Create backup of file."""
        return create_backup(self.get_path(relative_path))

    def restore(self, relative_path: str, backup_path: str) -> bool:
        """Restore file from backup."""
        return restore_from_backup(backup_path, self.get_path(relative_path))

    def delete(self, relative_path: str, force: bool = False) -> bool:
        """Delete file."""
        return delete_file(self.get_path(relative_path), force=force)

    def exists(self, relative_path: str) -> bool:
        """Check if file exists."""
        return self.get_path(relative_path).exists()

    def list_files(self, pattern: str = "*", recursive: bool = False) -> List[str]:
        """List files matching pattern."""
        files = find_files(self.base_directory, pattern, recursive)
        # Return relative paths
        return [str(Path(f).relative_to(self.base_directory)) for f in files]

    def get_info(self, relative_path: str) -> dict:
        """Get file information."""
        return get_file_info(self.get_path(relative_path))

    def cleanup_old_backups(self, relative_path: str, keep_count: int = 5) -> int:
        """Clean up old backup files."""
        return cleanup_old_backups(self.get_path(relative_path), keep_count)