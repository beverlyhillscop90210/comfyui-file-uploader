"""
File Uploader for ComfyUI.

Adds a node with a drag & drop upload button that writes any file (fonts, audio,
data, whatever) into the ComfyUI input directory and outputs both the full file
path and the containing folder path for downstream nodes.
"""

import os
from pathlib import Path

import folder_paths
from aiohttp import web
from server import PromptServer


def _input_dir() -> Path:
    return Path(folder_paths.get_input_directory()).resolve()


def _resolve_safe(subfolder: str) -> Path:
    """Resolve input_dir/subfolder, refusing path traversal."""
    base = _input_dir()
    target = (base / (subfolder or "")).resolve()
    if base != target and base not in target.parents:
        raise ValueError(f"subfolder escapes input dir: {subfolder!r}")
    return target


def _list_files(subfolder: str) -> list[str]:
    target = _input_dir() / (subfolder or "")
    if not target.exists() or not target.is_dir():
        return []
    return sorted(f.name for f in target.iterdir() if f.is_file())


@PromptServer.instance.routes.post("/file_uploader/upload")
async def _upload(request):
    try:
        post = await request.post()
        file_field = post.get("file")
        subfolder = (post.get("subfolder") or "").strip().strip("/")

        if file_field is None or not hasattr(file_field, "file"):
            return web.json_response({"error": "no file"}, status=400)

        try:
            target_dir = _resolve_safe(subfolder)
        except ValueError as exc:
            return web.json_response({"error": str(exc)}, status=400)

        target_dir.mkdir(parents=True, exist_ok=True)

        filename = os.path.basename(file_field.filename or "upload.bin")
        target_path = target_dir / filename

        with open(target_path, "wb") as out:
            while True:
                chunk = file_field.file.read(1024 * 1024)
                if not chunk:
                    break
                out.write(chunk)

        return web.json_response(
            {
                "name": filename,
                "subfolder": subfolder,
                "size": target_path.stat().st_size,
            }
        )
    except Exception as exc:
        return web.json_response({"error": repr(exc)}, status=500)


@PromptServer.instance.routes.get("/file_uploader/list")
async def _list(request):
    subfolder = (request.query.get("subfolder") or "").strip().strip("/")
    try:
        _resolve_safe(subfolder)
    except ValueError as exc:
        return web.json_response({"error": str(exc)}, status=400)
    return web.json_response({"files": _list_files(subfolder)})


class FileUploader:
    @classmethod
    def INPUT_TYPES(cls):
        files = _list_files("fonts") or ["(no files yet, click upload)"]
        return {
            "required": {
                "file": (files,),
                "subfolder": ("STRING", {"default": "fonts"}),
            }
        }

    RETURN_TYPES = ("STRING", "STRING", "STRING")
    RETURN_NAMES = ("file_path", "folder_path", "filename")
    FUNCTION = "resolve"
    CATEGORY = "utils/io"
    OUTPUT_NODE = False

    def resolve(self, file: str, subfolder: str):
        subfolder = (subfolder or "").strip().strip("/")
        folder = _resolve_safe(subfolder)
        file_path = folder / file
        if not file_path.exists():
            raise FileNotFoundError(
                f"file not found: {file_path}. Upload it via the node's button first."
            )
        return (str(file_path), str(folder), file)

    @classmethod
    def IS_CHANGED(cls, file, subfolder):
        try:
            p = _resolve_safe((subfolder or "").strip().strip("/")) / file
            if p.exists():
                return str(p.stat().st_mtime)
        except Exception:
            pass
        return float("nan")


NODE_CLASS_MAPPINGS = {"FileUploader": FileUploader}
NODE_DISPLAY_NAME_MAPPINGS = {"FileUploader": "File Uploader"}
