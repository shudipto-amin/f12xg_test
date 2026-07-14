from pathlib import Path
import subprocess

workflow_dir = Path("./")

theme = (workflow_dir / "theme.mmd").read_text().strip()
classes = (workflow_dir / "classes.mmd").read_text().strip()

body_files = sorted(workflow_dir.glob("*.body.mmd"))

for body_file in body_files:
    body = body_file.read_text().strip()

    out_file = Path(str(body_file).replace(".body.mmd", ".mmd"))
    svg_file = out_file.with_suffix(".svg")

    final_text = f"{theme}\n\nflowchart TD\n\n{classes}\n\n{body}\n"
    print(out_file)
    out_file.write_text(final_text)

    subprocess.run(
        [
            "mmdc",
            "-i", str(out_file),
            "-o", str(svg_file),
        ],
        check=True,
    )

    print(f"Wrote {out_file}")
    print(f"Rendered {svg_file}")
