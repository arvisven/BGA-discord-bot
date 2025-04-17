# BGA-discord-bot

Discord bot for Board Game Arena notifications

## How It Works

### User Registration:

Players can register their BGA user ID with the bot using the !add_user command. Once registered, the bot will automatically monitor all their active games.

### Game Monitoring:

The bot tracks all games a user is participating in. When it's the user's turn, the bot sends a notification to the designated Discord channel.

### User Management:

Users can remove themselves from the database using the !remove_me command.

## setup

setup .env or env vars:

```
DISCORD_TOKEN=MIi...
NOTIFY_CHANNEL_ID=3u98sjfd9in....
```

create a python venv and activate it. Install requirements and run script

```
pip install --no-cache-dir -r requirements.txt
python script.py
```

### docker (build, run, push)

Enable [Enable containerd image store on Docker Engine](https://docs.docker.com/storage/containerd/#enable-containerd-image-store-on-docker-engine)

```
docker buildx bake -f docker-bake.dev.hcl
docker run -e DISCORD_TOKEN="somevalue" -e NOTIFY_CHANNEL_ID="somevalue" -it docker.io/johrad/bga-discord-bot
docker push docker.io/johrad/bga-discord-bot
```

### kubernetes

```
# in k8s-manifests.yaml:
# modify:
---
apiVersion: v1
kind: Secret
metadata:
  name: bga-env-var-secrets
  namespace: bga-discord-bot
type: Opaque
data:
  discord_token: <base64 encoded token>          # <-- modify this
  notify_channel_id: <base64 encoded channelid>  # <-- modify this
---
# probably, also want to set PV hostPath differently:
---
apiVersion: v1
kind: PersistentVolume
metadata:
  name: bga-discord-bot-pv
  namespace: bga-discord-bot
spec:
  capacity:
    storage: 1Gi
  accessModes:
    - ReadWriteOnce
  hostPath:
    path: /mnt/path  # <-- modify this
  persistentVolumeReclaimPolicy: Retain
  storageClassName: bga-discord-botfs
---
# then execute:
kubectl apply -f k8s-manifests.yaml
```
