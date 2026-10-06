FROM golang:1.26 AS build
WORKDIR /src
COPY go.mod go.sum ./
RUN go mod download
COPY . .
RUN CGO_ENABLED=0 go build -trimpath -ldflags="-s -w" -o /out/geniusrise ./cmd/geniusrise

FROM alpine:3.20
RUN adduser -D -u 10001 gr
COPY --from=build /out/geniusrise /usr/local/bin/geniusrise
USER gr
ENV GR_DATA_DIR=/data
VOLUME /data
EXPOSE 443
ENTRYPOINT ["geniusrise"]
CMD ["gateway"]
