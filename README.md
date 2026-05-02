# comfyui-file-uploader

Tiny custom node that adds drag & drop file upload to any hosted ComfyUI where you don't have shell access.

## What it does

Adds a node `File Uploader` (category `utils/io`) with:

- **`subfolder`** input (STRING, default `fonts`): subdirectory inside ComfyUI's `input/` directory.
- **`file`** dropdown: lists files currently in `input/<subfolder>/`.
- **Upload button**: opens browser file picker, uploads the selected file to `input/<subfolder>/`, refreshes the dropdown.

Outputs:

- `file_path`: absolute path to the chosen file (e.g. for nodes that take a file path)
- `folder_path`: absolute path to the subfolder (e.g. for `CR Font File List` which wants a folder)
- `filename`: just the filename

## Install

Drop the whole folder into your ComfyUI `custom_nodes/` directory:

```
ComfyUI/custom_nodes/comfyui-file-uploader/
    __init__.py
    nodes.py
    web/js/upload-widget.js
```

Restart ComfyUI. Refresh the browser.

## Usage for the Scania font case

1. Add `File Uploader` node.
2. Set `subfolder` to `fonts` (or whatever you want).
3. Click "📁 Upload file", pick `ScaniaOfficeHeadline-Bold.ttf`.
4. Wire `folder_path` output into `CR Font File List`'s folder path input. Or wire `file_path` into a node that takes a direct font file path (S4Tool-Text etc.).

## Endpoints

- `POST /file_uploader/upload` — multipart `file` + `subfolder`
- `GET  /file_uploader/list?subfolder=...` — returns `{files: [...]}`

## Notes

- Files land inside `ComfyUI/input/`. Path traversal (`../`) is blocked.
- On RunPod / hosted setups: `input/` is usually under `/workspace/` or wherever ComfyUI's working dir is. Survives across pod restarts only if that path is on persistent storage.
- No file size limit enforced here. Your hosting's reverse proxy may have one (typically 100MB+).
