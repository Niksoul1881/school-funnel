from pathlib import Path

key_file = Path("/opt/school-platform/.env.key")
key = key_file.read_text(encoding="utf-8").strip()
p = Path("/opt/school-platform/.env")
values = {
    "DEEPSEEK_API_KEY": key,
    "AGENT_MODE": "dsh",
    "DSH_HOME": "/data/dsh",
    "DSH_BIN": "dsh",
}
lines = p.read_text(encoding="utf-8").splitlines() if p.exists() else []
out, seen = [], set()
for line in lines:
    k = line.split("=", 1)[0].strip()
    if k in values:
        out.append(f"{k}={values[k]}")
        seen.add(k)
    else:
        out.append(line)
for k, v in values.items():
    if k not in seen:
        out.append(f"{k}={v}")
p.write_text("\n".join(out) + "\n", encoding="utf-8")
p.chmod(0o600)
key_file.unlink(missing_ok=True)
print("env updated")
