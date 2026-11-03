import json
import subprocess
import sys
from pathlib import Path


SCRIPT = Path(__file__).parents[1] / "agent_dispatch.py"


def test_dispatch_runs_each_role_in_its_own_directory(tmp_path):
    packets = tmp_path / "packets"; commands = tmp_path / "commands"
    commands.write_text(json.dumps({role: [sys.executable, "-c", "open('report.md','w').write('## Contexto do revisor\\n\\n## Veredito\\npass\\n\\n## Achados\\nnone')"] for role in ("simplificador", "operador", "implementador")}), encoding="utf-8")
    subprocess.run([sys.executable, str(SCRIPT), str(packets), str(commands)], check=True)
    assert all((packets / role / "report.md").exists() for role in ("simplificador", "operador", "implementador"))
