FROM golang:1.24.8-alpine AS build

ARG MINIO_VERSION=RELEASE.2025-10-15T17-29-55Z
ARG HTTP_PROXY
ARG HTTPS_PROXY

ENV CGO_ENABLED=0 \
    GOPROXY=https://proxy.golang.org,direct \
    HTTP_PROXY=${HTTP_PROXY} \
    HTTPS_PROXY=${HTTPS_PROXY} \
    http_proxy=${HTTP_PROXY} \
    https_proxy=${HTTPS_PROXY}

RUN apk add --no-cache ca-certificates git \
    && go install -v github.com/minio/minio@${MINIO_VERSION} \
    && mkdir -p /out/root/.minio /out/tmp \
    && chmod 1777 /out/tmp

FROM scratch

ENV HOME=/root

COPY --from=build /go/bin/minio /usr/bin/minio
COPY --from=build /etc/ssl/certs/ca-certificates.crt /etc/ssl/certs/ca-certificates.crt
COPY --from=build /out/root /root
COPY --from=build /out/tmp /tmp

ENTRYPOINT ["/usr/bin/minio"]
CMD ["server", "/minio_data", "--console-address", ":9001"]
