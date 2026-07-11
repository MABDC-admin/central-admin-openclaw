# VPS Deployment

Deploy path:

```bash
/DATA/docker/command-center
```

Initial deployment:

```bash
mkdir -p /DATA/docker/command-center
cp -r deploy src pyproject.toml README.md /DATA/docker/command-center/
cd /DATA/docker/command-center/deploy
cp command-center.env.example command-center.env
```

Edit `command-center.env` with real private values, then:

```bash
docker compose up -d --build
curl -fsS http://127.0.0.1:18088/api/health
```

Expected response:

```json
{"ok":true}
```
