# File Splitter for iCloud Upload

A Python script to split large .rar, .zip, and other files into chunks under 10GB for iCloud upload, then recombine them with integrity verification.

## Features

- ✅ Splits files into 9.5GB chunks (safely under 10GB limit)
- ✅ Creates metadata file with checksums for integrity verification
- ✅ Progress bars for large file operations
- ✅ Automatic file integrity verification
- ✅ Cross-platform compatibility (Windows, Mac, Linux)
- ✅ Works with any file type (.rar, .zip, .7z, etc.)

## Usage

### Split a large file
```bash
python file_splitter.py split large_file.zip
```

This creates:
- `large_file.zip.part001`, `large_file.zip.part002`, etc.
- `large_file.zip.metadata` (contains reconstruction info)

### Combine chunks back into original file
```bash
python file_splitter.py combine large_file.zip.metadata
```

### List chunks in current directory
```bash
python file_splitter.py list
```

### Custom chunk size (in GB)
```bash
python file_splitter.py split large_file.zip --chunk-size 8.0
```

## Workflow for iCloud Upload

1. **Before uploading:**
   ```bash
   python file_splitter.py split my_large_archive.rar
   ```

2. **Upload to iCloud:**
   - Upload ALL `.part` files
   - Upload the `.metadata` file
   - Don't upload the original file

3. **After downloading from iCloud:**
   ```bash
   python file_splitter.py combine my_large_archive.rar.metadata
   ```

4. **Verify the file is identical to original**
   - The script automatically verifies file integrity using SHA256 checksums

## Example Output

```
Splitting file: huge_archive.zip
File size: 25.67 GB
Will create 3 chunks of max 9.50 GB each
Calculating original file hash...

Creating chunk 1/3: huge_archive.zip.part001
Chunk 1: |████████████████████████████████████████████████████| 100.0% Complete - Created: 9.50 GB

Creating chunk 2/3: huge_archive.zip.part002
Chunk 2: |████████████████████████████████████████████████████| 100.0% Complete - Created: 9.50 GB

Creating chunk 3/3: huge_archive.zip.part003
Chunk 3: |████████████████████████████████████████████████████| 100.0% Complete - Created: 6.67 GB

✓ File split successfully!
✓ Created 3 chunks and metadata file: huge_archive.zip.metadata
✓ Upload all .part files and the .metadata file to iCloud
```

## Requirements

- Python 3.6 or higher (uses built-in libraries only)
- Enough disk space for chunks (same as original file size)

## Safety Features

- **Integrity verification**: SHA256 checksums ensure no corruption
- **Overwrite protection**: Asks before overwriting existing files
- **Missing chunk detection**: Warns if chunks are missing before combining
- **Size verification**: Confirms final file size matches original

## Tips

- Keep the `.metadata` file safe - you need it to recombine chunks
- All chunks must be present in the same directory as the metadata file
- The script works with any file type, not just archives
- Use `list` command to see what chunks are available in a directory 