#!/bin/sh

/src/indexer.py && /src/ripper.py && fdupes -r --delete --noprompt /data/noods