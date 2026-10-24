# iCloud File Splitter

Split a ZIP, RAR, 7z, or any other large file into chunks small enough to upload on iCloud.com, then join the chunks back into the original file and verify it with a SHA-256 checksum.

iCloud.com shows this when a file is too big:

> iCloud Drive on iCloud.com currently limits uploads to a maximum of 10 GB.

Each chunk defaults to 9.5 GB, under that cap. The script uses only the Python standard library, so there is nothing to install beyond Python 3.8.

## Quick start

```bash
python file_splitter.py split large_file.zip
```

That writes:

- `large_file.zip.part001`, `large_file.zip.part002`, and so on
- `large_file.zip.metadata`, which stores the original name, size, chunk list, and SHA-256 hashes

Upload every `.part` file and the `.metadata` file. Leave the original file off iCloud.

After you download the pieces onto another machine:

```bash
python file_splitter.py combine large_file.zip.metadata
```

The combiner checks each chunk hash, rebuilds the file, then checks the final SHA-256 and file size against the metadata.

## Split a large ZIP, RAR, or other file

```bash
python file_splitter.py split archive.rar
python file_splitter.py split archive.rar --chunk-size 8
```

`--chunk-size` is in gigabytes. Use it when the limit is not iCloud's 10 GB web cap. The same command works for `.zip`, `.rar`, `.7z`, disk images, videos, and any other file.

A file that is already under the chunk size is left as-is.

## Combine split files and verify the checksum

```bash
python file_splitter.py combine archive.rar.metadata
```

If the rebuilt file already exists, the script asks before overwriting it. If a chunk is missing or its hash does not match, it stops and names the bad piece.

## List chunk files

```bash
python file_splitter.py list
python file_splitter.py list --directory D:\Downloads
```

## Upload a file larger than the iCloud limit

1. Split the file on the computer that has the original.
2. Upload all `.part` files and the `.metadata` file through iCloud.com, or into iCloud Drive.
3. On the other device, download every part plus the metadata into one folder.
4. Run `combine` on the metadata file.

Keep the metadata file with the chunks. The script needs it to rebuild the original and to verify the checksum.

iCloud Drive in the Mac and Windows apps can accept a larger individual file than the iCloud.com website. Apple's documentation has described a 50 GB per-file limit there. The 9.5 GB default targets the website upload limit, which blocks a browser upload at 10 GB.

## What the metadata file stores

`filename.metadata` is JSON with:

- the original filename and size
- the SHA-256 of the original file
- the chunk size and chunk count
- each chunk's filename, size, and SHA-256

Those hashes are how a corrupted upload gets caught before you treat the rebuilt file as good.

## Example

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

- Python 3.8 or newer (`python --version`). The script uses the standard library only.
- Free disk space about equal to the original file, because the chunks are a full copy.
- The chunks and the metadata file in the same directory when combining.

## License

[MIT](LICENSE)
