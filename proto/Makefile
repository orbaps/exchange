# Makefile for Protobuf Generation
# Generates Python gRPC stubs from .proto files

PROTO_DIR := iicpc
OUT_DIR := ../generated
PYTHON_OUT := $(OUT_DIR)/python
GO_OUT := $(OUT_DIR)/go

# Find all .proto files
PROTO_FILES := $(shell find $(PROTO_DIR) -name "*.proto")

# Python generation flags
PYTHON_FLAGS := --python_out=$(PYTHON_OUT) \
                --grpc_python_out=$(PYTHON_OUT) \
                --proto_path=.

# Go generation flags
GO_FLAGS := --go_out=$(GO_OUT) \
            --go-grpc_out=$(GO_OUT) \
            --proto_path=.

.PHONY: all python go clean install-tools

all: python go

# Generate Python gRPC stubs
python: $(PYTHON_OUT)
	python -m grpc_tools.protoc $(PYTHON_FLAGS) $(PROTO_FILES)
	@echo "Python stubs generated in $(PYTHON_OUT)"

# Generate Go gRPC stubs
go: $(GO_OUT)
	protoc $(GO_FLAGS) $(PROTO_FILES)
	@echo "Go stubs generated in $(GO_OUT)"

# Create output directories
$(PYTHON_OUT):
	mkdir -p $(PYTHON_OUT)

$(GO_OUT):
	mkdir -p $(GO_OUT)

# Install required tools
install-tools:
	pip install grpcio-tools protobuf
	# For Go: go install google.golang.org/protobuf/cmd/protoc-gen-go@latest
	# go install google.golang.org/grpc/cmd/protoc-gen-go-grpc@latest

# Clean generated files
clean:
	rm -rf $(OUT_DIR)
	@echo "Cleaned generated files"

# Lint proto files with buf
lint:
	buf lint

# Check for breaking changes
breaking:
	buf breaking --against '.git#branch=main'

# Format proto files
format:
	buf format -w

# Generate all and verify
generate: clean python go
	@echo "Generation complete"

# Verify generated Python imports work
verify-python: python
	python -c "
import sys
sys.path.insert(0, '$(PYTHON_OUT)')
import iicpc.common.health_pb2
import iicpc.common.metrics_pb2
import iicpc.hosting.deployment_pb2
import iicpc.hosting.container_pb2
import iicpc.botfleet.orchestrator_pb2
import iicpc.botfleet.worker_pb2
import iicpc.evaluation.benchmark_pb2
import iicpc.evaluation.telemetry_pb2
import iicpc.federation.consensus_pb2
import iicpc.federation.replication_pb2
print('All Python imports successful')
"

# Generate requirements for generated code
gen-requirements:
	@echo "grpcio>=1.62.0" > $(PYTHON_OUT)/requirements.txt
	@echo "protobuf>=4.25.0" >> $(PYTHON_OUT)/requirements.txt

help:
	@echo "Available targets:"
	@echo "  all           - Generate Python and Go stubs"
	@echo "  python        - Generate Python gRPC stubs"
	@echo "  go            - Generate Go gRPC stubs"
	@echo "  clean         - Remove generated files"
	@echo "  lint          - Lint proto files with buf"
	@echo "  breaking      - Check for breaking changes"
	@echo "  format        - Format proto files"
	@echo "  generate      - Clean and regenerate all"
	@echo "  verify-python - Verify Python imports work"
	@echo "  install-tools - Install required tools"
	@echo "  gen-requirements - Generate requirements.txt for generated code"
	@echo "  help          - Show this help"