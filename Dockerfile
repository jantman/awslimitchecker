FROM python:3-alpine

ARG git_version

COPY . /awslimitchecker
RUN cd /awslimitchecker && pip install -e .

ENTRYPOINT ["/usr/local/bin/awslimitchecker"]
LABEL org.opencontainers.image.revision=$git_version \
      org.opencontainers.image.source="https://github.com/jantman/awslimitchecker.git" \
      org.opencontainers.image.url="https://github.com/jantman/awslimitchecker" \
      org.opencontainers.image.authors="jason@jasonantman.com"
