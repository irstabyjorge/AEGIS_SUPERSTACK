"""Read-only Gradio view for the PETS–AEGIS historical device registry."""

import json
from pathlib import Path

import gradio as gr

REGISTRY = Path(__file__).with_name("historical_devices.json")


def show_registry():
    data = json.loads(REGISTRY.read_text(encoding="utf-8"))
    devices = data.get("devices", [])
    rows = [
        [d["record_id"], d["model"], d.get("platform", ""), d["classification"], "Unverified"]
        for d in devices
    ]
    return rows, (
        f"Project: {data.get('project', 'PETS–AEGIS')} | "
        f"Records: {len(devices)} | "
        "Source: prior conversation mentions; no independent ownership verification."
    )


with gr.Blocks(title="PETS–AEGIS Device Registry") as demo:
    gr.Markdown("# PETS–AEGIS Historical Device Registry")
    gr.Markdown(
        "Read-only inventory. Historical mentions are not proof of ownership or "
        "evidence of impersonation. This demo does not scan devices or collect identifiers."
    )
    table = gr.Dataframe(
        headers=["Record ID", "Device model", "Platform", "Classification", "Verification"],
        datatype=["str", "str", "str", "str", "str"],
        interactive=False,
        label="Historical records",
    )
    summary = gr.Textbox(label="Registry status", interactive=False)
    refresh = gr.Button("Refresh")
    demo.load(show_registry, outputs=[table, summary])
    refresh.click(show_registry, outputs=[table, summary])


if __name__ == "__main__":
    demo.launch()
