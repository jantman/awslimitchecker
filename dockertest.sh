#!/bin/bash -x

set -x
set -e

if [ -z "$1" ]; then
    >&2 echo "USAGE: dockertest.sh repo/image:tag"
    exit 1
fi

docker run -it --rm -e AWS_DEFAULT_REGION=us-east-1 "$1" --version
