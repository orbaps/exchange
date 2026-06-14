.PHONY: proto proto-lint test lint python-lint fmt clean docker-build docker-kind
.PHONY: kind-create kind-delete kind-deploy helm-lint init build-all

# ── Proto ──────────────────────────────────────────────────────────────────
proto:
	$(MAKE) -C proto python

proto-lint:
	$(MAKE) -C proto lint

# ── Tests ──────────────────────────────────────────────────────────────────
test:
	pytest -v --cov=. --cov-report=term-missing --timeout=60

test-quick:
	pytest -v --timeout=30 -x

test-coverage:
	pytest --cov=. --cov-report=html --cov-report=term

# ── Lint ───────────────────────────────────────────────────────────────────
lint: python-lint

python-lint:
	ruff check .
	ruff format --check .

fmt:
	ruff format .

mypy:
	mypy --ignore-missing-imports .

# ── Docker Build ──────────────────────────────────────────────────────────
docker-build:
	@echo "Building all 7 images..."
	docker build -f iac/docker/Dockerfile.hosting -t iicpc/hosting:latest .
	docker build -f iac/docker/Dockerfile.botfleet -t iicpc/botfleet:latest .
	docker build -f iac/docker/Dockerfile.evaluation -t iicpc/evaluation:latest .
	docker build -f iac/docker/Dockerfile.federation -t iicpc/federation:latest .
	docker build -f iac/docker/Dockerfile.governance -t iicpc/governance:latest .
	docker build -f iac/docker/Dockerfile.strategic -t iicpc/strategic:latest .
	docker build -f iac/docker/Dockerfile.dashboard -t iicpc/dashboard:latest .

# ── Helm ──────────────────────────────────────────────────────────────────
helm-lint:
	helm lint iac/helm/iicpc-platform -f iac/helm/iicpc-platform/values-kind.yaml

helm-template:
	helm template test iac/helm/iicpc-platform -f iac/helm/iicpc-platform/values-kind.yaml

# ── Kind Cluster ──────────────────────────────────────────────────────────
kind-create:
	kind create cluster --config kind-config.yaml

kind-delete:
	kind delete cluster --name iicpc-platform

kind-deploy: docker-build
	kind load docker-image iicpc/hosting:latest --name iicpc-platform
	kind load docker-image iicpc/botfleet:latest --name iicpc-platform
	kind load docker-image iicpc/evaluation:latest --name iicpc-platform
	kind load docker-image iicpc/federation:latest --name iicpc-platform
	kind load docker-image iicpc/governance:latest --name iicpc-platform
	kind load docker-image iicpc/strategic:latest --name iicpc-platform
	kind load docker-image iicpc/dashboard:latest --name iicpc-platform
	helm upgrade --install iicpc-platform iac/helm/iicpc-platform \
		-f iac/helm/iicpc-platform/values-kind.yaml --namespace iicpc --create-namespace

# ── Clean ─────────────────────────────────────────────────────────────────
clean:
	rm -rf .pytest_cache .coverage __pycache__
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name '*.pyc' -delete

# ── Init ──────────────────────────────────────────────────────────────────
init: clean
	pip install --upgrade pip setuptools wheel
	pip install -e .
	pip install -r requirements.txt
	$(MAKE) proto

# ── All ───────────────────────────────────────────────────────────────────
all: proto lint test docker-build helm-lint
