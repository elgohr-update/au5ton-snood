# snood
Reddit snoo daemon

## Install
```bash
pip3 install -r requirements.txt
python3 setup.py
```

## Docker 

[![Docker Pulls](https://img.shields.io/docker/pulls/au5ton/snood)](https://hub.docker.com/r/au5ton/snood)

Pull: `docker pull au5ton/snood`

Mounts:

```
/config
├── config.ini
└── database.sqlite

/data
└── noods
    ├── ...
    └── ...
```