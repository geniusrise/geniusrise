.PHONY: test vet fmt build clean e2e install

test:
	go test ./... -count=1 -timeout 600s

vet:
	go vet ./...

fmt:
	gofmt -w .

build:
	go build -o bin/geniusrise ./cmd/geniusrise

install:
	go install ./cmd/geniusrise

e2e:
	@echo "set PROVIDER=<aws|ssh> to run real-cloud contract tests"
	@test -n "$(PROVIDER)" || (echo "PROVIDER is empty"; exit 1)
	go test ./internal/provider/... -count=1 -tags e2e -run "TestE2E_$(PROVIDER)" -v

clean:
	rm -rf bin/
