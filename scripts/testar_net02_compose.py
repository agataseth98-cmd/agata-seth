"""Confere o isolamento de dados do LibreChat sem subir containers."""
import json
import os
import subprocess
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
COMPOSE = ROOT / "redesign/librechat/docker-compose.yml"


def main() -> int:
    with tempfile.TemporaryDirectory(prefix="agata-net02-") as tmp:
        temp_dir = Path(tmp)
        (temp_dir / ".config/agata").mkdir(parents=True, mode=0o700)
        key_file = temp_dir / ".config/agata/approval-capability-private.pem"
        key_file.write_text("test-private-key-fixture", encoding="ascii")
        key_file.chmod(0o600)
        (temp_dir / ".cache/agata/approval-capabilities").mkdir(parents=True, mode=0o700)
        compose_copy = temp_dir / "docker-compose.yml"
        compose_copy.write_text(COMPOSE.read_text(encoding="utf-8"), encoding="utf-8")
        (temp_dir / ".env").write_text("MEILI_MASTER_KEY=placeholder\n", encoding="utf-8")
        env = {**os.environ, "HOME": tmp, "MEILI_MASTER_KEY": "placeholder"}
        result = subprocess.run(
            ["docker", "compose", "-f", str(compose_copy), "config", "--format", "json"],
            capture_output=True, text=True, env=env,
        )
    if result.returncode:
        print(result.stderr.strip() or "docker compose config falhou")
        return 1
    config = json.loads(result.stdout)
    services, networks = config["services"], config["networks"]
    assert set(services["librechat-mongodb"]["networks"]) == {"librechat-data"}
    assert set(services["librechat-meilisearch"]["networks"]) == {"librechat-data"}
    assert set(services["librechat"]["networks"]) == {"librechat", "librechat-data"}
    assert services["librechat"]["image"] == "agata-librechat:capabilities-20261020"
    assert services["librechat"]["build"]["dockerfile"] == "Dockerfile"
    assert (ROOT / "redesign/librechat/Dockerfile").is_file()
    assert (ROOT / "redesign/librechat/fork/agata-capabilities.patch").is_file()
    assert services["librechat"]["user"] == "1000:59999"
    mounts = services["librechat"]["volumes"]
    assert not any("approval-capabilities" in mount.get("source", "") for mount in mounts)
    assert any("approval-capability-private.pem" in mount.get("source", "") for mount in mounts)
    assert networks["librechat-data"]["internal"] is True
    assert services["librechat-ponte-host"]["network_mode"] == "host"
    print("NET-02 compose topology PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
