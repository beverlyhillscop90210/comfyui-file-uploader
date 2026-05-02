import { app } from "/scripts/app.js";
import { api } from "/scripts/api.js";

console.log("[FileUploader] extension loading");

app.registerExtension({
    name: "FileUploader.UploadWidget",

    async beforeRegisterNodeDef(nodeType, nodeData) {
        if (nodeData.name !== "FileUploader") return;
        console.log("[FileUploader] patching node", nodeData.name);

        const onNodeCreated = nodeType.prototype.onNodeCreated;
        nodeType.prototype.onNodeCreated = function () {
            const r = onNodeCreated?.apply(this, arguments);

            const fileWidget = this.widgets.find((w) => w.name === "file");
            const subfolderWidget = this.widgets.find((w) => w.name === "subfolder");

            const refreshList = async () => {
                const sub = (subfolderWidget?.value ?? "").trim();
                try {
                    const resp = await api.fetchApi(
                        `/file_uploader/list?subfolder=${encodeURIComponent(sub)}`
                    );
                    const data = await resp.json();
                    const files = data.files ?? [];
                    fileWidget.options.values =
                        files.length > 0 ? files : ["(no files yet, click upload)"];
                    if (files.length > 0 && !files.includes(fileWidget.value)) {
                        fileWidget.value = files[0];
                    }
                    app.graph.setDirtyCanvas(true, true);
                } catch (err) {
                    console.warn("[FileUploader] list failed", err);
                }
            };

            if (subfolderWidget) {
                const orig = subfolderWidget.callback;
                subfolderWidget.callback = function () {
                    const ret = orig?.apply(this, arguments);
                    refreshList();
                    return ret;
                };
            }

            this.addWidget("button", "📁 Upload file", null, () => {
                const input = document.createElement("input");
                input.type = "file";
                input.accept = "*/*";
                input.style.display = "none";
                document.body.appendChild(input);

                input.onchange = async () => {
                    const file = input.files?.[0];
                    document.body.removeChild(input);
                    if (!file) return;

                    const sub = (subfolderWidget?.value ?? "").trim();
                    const formData = new FormData();
                    formData.append("file", file, file.name);
                    formData.append("subfolder", sub);

                    try {
                        const resp = await api.fetchApi("/file_uploader/upload", {
                            method: "POST",
                            body: formData,
                        });
                        const data = await resp.json();
                        if (!resp.ok) {
                            alert("Upload failed: " + (data.error ?? resp.status));
                            return;
                        }
                        await refreshList();
                        if (data.name) fileWidget.value = data.name;
                        app.graph.setDirtyCanvas(true, true);
                    } catch (err) {
                        alert("Upload error: " + err.message);
                    }
                };

                input.click();
            });

            return r;
        };
    },
});
