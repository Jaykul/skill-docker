# opsdroid skill random

A skill for [opsdroid](https://github.com/opsdroid/opsdroid) to run code in docker containers.

## Requirements

1. Opsdroid must have access to run docker.
2. You must have a docker volume configured which opsdroid and the scripts can use for scratch files.

### Docker

If you're running Opsdroid in a docker container, you'll have to pass the docker .sock to it in order to for this to work.

In order to use docker with opsdroid _from inside_ docker, you'll want to create an image with the docker cli in it:

1. Make a `Dockerfile` and add these lines:

```
FROM opsdroid/opsdroid:latest
RUN apk update && apk add --no-cache docker-cli
```

2. Build the image:

```
docker build -t opsdroiddocker .
```

3. Create a volume:
```
docker volume create working
```

4. Run Opsdroid with the volume mounted, and pass in the docker.sock. On linux:
```
docker run --rm -v /var/run/docker.sock:/var/run/docker.sock -v working:/code opsdroiddocker
```

## Configuration

- `volume`. The volume mount to use with the containers we create
- `path`. The path where opsdroid can save files to have them show up in that volume
- `containers`. One or more containers which must each have:
    - `language`. Strings which users can use after code fences for this language
    - `extension`. A file extension to use for scripts in this language
    - `container`. The name of the container (optionally including the repository)
    - `command`. The command to run in the docker container

```yaml
  docker:
    repo: https://github.com/Jaykul/skill-random.git
    volume: working:/code
    path: /code
    containers:
      - language: ["pwsh","powershell"]
        extension: ".ps1"
        container: "mcr.microsoft.com/powershell"
        command: ['pwsh','-NoLogo','-NonInteractive','-NoProfile','-File']
      - language: ["python","py"]
        extension: ".py"
        container: "python"
        command: ['python']
```


The docker skill will write code to a file, mount that file in the specified container, and then run the specified command ...

## Usage

### Run this:

>     user: run this:
>           ```pwsh
>           "Jim", "Bob", "Mark" | Get-Random
>           ```
>     opsdroid: Let me try that in `mcr.microsoft.com/powershell`
>     opsdroid: ```
>               Jim
>               ```
