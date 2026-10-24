#!/usr/bin/env python3
"""
File Splitter/Combiner for iCloud Upload
Splits large files into chunks under 10GB and recombines them with integrity verification.
"""

import os
import sys
import json
import hashlib
import argparse
from pathlib import Path
from typing import List, Dict, Any

# Configuration
CHUNK_SIZE = int(9.5 * 1024 * 1024 * 1024)  # 9.5GB in bytes
BUFFER_SIZE = 64 * 1024 * 1024  # 64MB buffer for reading/writing


def calculate_file_hash(filepath: str, chunk_size: int = BUFFER_SIZE) -> str:
    """Calculate SHA256 hash of a file."""
    hash_sha256 = hashlib.sha256()
    try:
        with open(filepath, 'rb') as f:
            while chunk := f.read(chunk_size):
                hash_sha256.update(chunk)
        return hash_sha256.hexdigest()
    except IOError as e:
        print(f"Error calculating hash for {filepath}: {e}")
        return ""


def format_size(size_bytes: int) -> str:
    """Format bytes to human readable format."""
    size = float(size_bytes)
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if size < 1024.0:
            return f"{size:.2f} {unit}"
        size /= 1024.0
    return f"{size:.2f} PB"


def show_progress(current: int, total: int, prefix: str = "Progress"):
    """Show progress bar."""
    percent = (current / total) * 100
    bar_length = 50
    filled_length = int(bar_length * current // total)
    bar = '█' * filled_length + '-' * (bar_length - filled_length)
    print(f'\r{prefix}: |{bar}| {percent:.1f}% Complete', end='', flush=True)


def split_file(filepath: str, chunk_size: int = CHUNK_SIZE) -> bool:
    """
    Split a file into chunks.
    
    Args:
        filepath: Path to the file to split
        chunk_size: Size of each chunk in bytes
        
    Returns:
        True if successful, False otherwise
    """
    try:
        file_path = Path(filepath)
        if not file_path.exists():
            print(f"Error: File '{filepath}' not found.")
            return False
        
        file_size = file_path.stat().st_size
        print(f"Splitting file: {file_path.name}")
        print(f"File size: {format_size(file_size)}")
        
        if file_size <= chunk_size:
            print("File is already under the chunk size limit. No splitting needed.")
            return True
        
        # Calculate number of chunks needed
        num_chunks = (file_size + chunk_size - 1) // chunk_size
        print(f"Will create {num_chunks} chunks of max {format_size(chunk_size)} each")
        
        # Calculate original file hash
        print("Calculating original file hash...")
        original_hash = calculate_file_hash(filepath)
        if not original_hash:
            return False
        
        # Prepare metadata
        metadata = {
            "original_filename": file_path.name,
            "original_size": file_size,
            "original_hash": original_hash,
            "chunk_size": chunk_size,
            "num_chunks": num_chunks,
            "chunks": []
        }
        
        # Split the file
        with open(filepath, 'rb') as source_file:
            for chunk_num in range(num_chunks):
                chunk_filename = f"{file_path.name}.part{chunk_num + 1:03d}"
                chunk_path = file_path.parent / chunk_filename
                
                print(f"\nCreating chunk {chunk_num + 1}/{num_chunks}: {chunk_filename}")
                
                bytes_to_read = min(chunk_size, file_size - (chunk_num * chunk_size))
                bytes_written = 0
                
                with open(chunk_path, 'wb') as chunk_file:
                    while bytes_written < bytes_to_read:
                        buffer_size = min(BUFFER_SIZE, bytes_to_read - bytes_written)
                        data = source_file.read(buffer_size)
                        if not data:
                            break
                        chunk_file.write(data)
                        bytes_written += len(data)
                        show_progress(bytes_written, bytes_to_read, f"Chunk {chunk_num + 1}")
                
                # Calculate chunk hash
                chunk_hash = calculate_file_hash(str(chunk_path))
                chunk_size_actual = chunk_path.stat().st_size
                
                metadata["chunks"].append({
                    "filename": chunk_filename,
                    "size": chunk_size_actual,
                    "hash": chunk_hash
                })
                
                print(f" - Created: {format_size(chunk_size_actual)}")
        
        # Save metadata
        metadata_filename = f"{file_path.name}.metadata"
        metadata_path = file_path.parent / metadata_filename
        
        with open(metadata_path, 'w') as meta_file:
            json.dump(metadata, meta_file, indent=2)
        
        print(f"\n✓ File split successfully!")
        print(f"✓ Created {num_chunks} chunks and metadata file: {metadata_filename}")
        print(f"✓ Upload all .part files and the .metadata file to iCloud")
        
        return True
        
    except Exception as e:
        print(f"Error splitting file: {e}")
        return False


def combine_files(metadata_filepath: str) -> bool:
    """
    Combine chunks back into original file.
    
    Args:
        metadata_filepath: Path to the metadata file
        
    Returns:
        True if successful, False otherwise
    """
    try:
        metadata_path = Path(metadata_filepath)
        if not metadata_path.exists():
            print(f"Error: Metadata file '{metadata_filepath}' not found.")
            return False
        
        # Load metadata
        with open(metadata_path, 'r') as meta_file:
            metadata = json.load(meta_file)
        
        original_filename = metadata["original_filename"]
        original_size = metadata["original_size"]
        original_hash = metadata["original_hash"]
        chunks_info = metadata["chunks"]
        
        print(f"Combining chunks to recreate: {original_filename}")
        print(f"Expected size: {format_size(original_size)}")
        print(f"Number of chunks: {len(chunks_info)}")
        
        # Check if all chunks exist
        missing_chunks = []
        for chunk_info in chunks_info:
            chunk_path = metadata_path.parent / chunk_info["filename"]
            if not chunk_path.exists():
                missing_chunks.append(chunk_info["filename"])
        
        if missing_chunks:
            print(f"Error: Missing chunks: {', '.join(missing_chunks)}")
            return False
        
        # Verify chunk integrity
        print("Verifying chunk integrity...")
        for i, chunk_info in enumerate(chunks_info):
            chunk_path = metadata_path.parent / chunk_info["filename"]
            chunk_hash = calculate_file_hash(str(chunk_path))
            
            if chunk_hash != chunk_info["hash"]:
                print(f"Error: Chunk {chunk_info['filename']} has been corrupted!")
                return False
            
            show_progress(i + 1, len(chunks_info), "Verifying")
        
        print("\n✓ All chunks verified successfully")
        
        # Combine chunks
        output_path = metadata_path.parent / original_filename
        
        # Check if output file already exists
        if output_path.exists():
            response = input(f"Output file '{original_filename}' already exists. Overwrite? (y/n): ")
            if response.lower() != 'y':
                print("Operation cancelled.")
                return False
        
        print(f"Combining chunks into: {original_filename}")
        
        with open(output_path, 'wb') as output_file:
            total_written = 0
            
            for i, chunk_info in enumerate(chunks_info):
                chunk_path = metadata_path.parent / chunk_info["filename"]
                
                with open(chunk_path, 'rb') as chunk_file:
                    while True:
                        data = chunk_file.read(BUFFER_SIZE)
                        if not data:
                            break
                        output_file.write(data)
                        total_written += len(data)
                        show_progress(total_written, original_size, f"Combining")
        
        print(f"\n✓ File combined successfully!")
        
        # Verify final file integrity
        print("Verifying final file integrity...")
        final_hash = calculate_file_hash(str(output_path))
        
        if final_hash != original_hash:
            print("Error: Final file hash doesn't match original! File may be corrupted.")
            return False
        
        final_size = output_path.stat().st_size
        if final_size != original_size:
            print(f"Error: Final file size ({format_size(final_size)}) doesn't match original ({format_size(original_size)})!")
            return False
        
        print("✓ File integrity verified successfully!")
        print(f"✓ Recreated: {original_filename} ({format_size(final_size)})")
        
        return True
        
    except Exception as e:
        print(f"Error combining files: {e}")
        return False


def list_chunks(directory: str = ".") -> None:
    """List all chunk files and metadata files in directory."""
    dir_path = Path(directory)
    
    # Find metadata files
    metadata_files = list(dir_path.glob("*.metadata"))
    chunk_files = list(dir_path.glob("*.part*"))
    
    if metadata_files:
        print("Found metadata files:")
        for meta_file in metadata_files:
            with open(meta_file, 'r') as f:
                metadata = json.load(f)
            print(f"  {meta_file.name} -> {metadata['original_filename']} ({metadata['num_chunks']} chunks)")
    
    if chunk_files:
        print(f"\nFound {len(chunk_files)} chunk files:")
        for chunk_file in sorted(chunk_files):
            size = format_size(chunk_file.stat().st_size)
            print(f"  {chunk_file.name} ({size})")
    
    if not metadata_files and not chunk_files:
        print("No chunk files or metadata files found in current directory.")


def main():
    """Main function to handle command line arguments."""
    parser = argparse.ArgumentParser(
        description="Split large files into chunks for iCloud upload and recombine them",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python file_splitter.py split large_file.zip
  python file_splitter.py combine large_file.zip.metadata
  python file_splitter.py list
        """
    )
    
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # Split command
    split_parser = subparsers.add_parser('split', help='Split a file into chunks')
    split_parser.add_argument('filepath', help='Path to the file to split')
    split_parser.add_argument('--chunk-size', type=float, default=9.5, 
                             help='Chunk size in GB (default: 9.5)')
    
    # Combine command
    combine_parser = subparsers.add_parser('combine', help='Combine chunks back into original file')
    combine_parser.add_argument('metadata_file', help='Path to the metadata file')
    
    # List command
    list_parser = subparsers.add_parser('list', help='List chunk files in directory')
    list_parser.add_argument('--directory', default='.', help='Directory to search (default: current)')
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return
    
    if args.command == 'split':
        chunk_size = int(args.chunk_size * 1024 * 1024 * 1024)  # Convert GB to bytes
        success = split_file(args.filepath, chunk_size)
        sys.exit(0 if success else 1)
    
    elif args.command == 'combine':
        success = combine_files(args.metadata_file)
        sys.exit(0 if success else 1)
    
    elif args.command == 'list':
        list_chunks(args.directory)


if __name__ == "__main__":
    main() 