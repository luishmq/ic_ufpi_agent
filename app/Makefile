help:
	@echo "Local examples:"
	@echo "    make run-dev       	# Starts a uvicorn development server locally with live reloading."
	@echo "    make run-dev-workers # Starts a uvicorn server with multiple workers."
	@echo "    make install       	# Installs dependencies from requirements.txt and necessary packages."
	@echo "    make cloud-build   	# Submits a build to Google Cloud Build."
	@echo "    make clear         	# Removes Python cache and test directories."
	@echo "    make code-formatting # Formats the codebase using Black and sorts imports with isort."

install:
	pip install --upgrade pip && \
	pip install keyring==23.8.2 && \
	pip install keyrings.google-artifactregistry-auth==1.0.0 && \
	pip install --upgrade --trusted-host pypi.python.org -r requirements.txt --no-cache-dir

run-dev-workers:
	export PROJECT_ID=sample_project_id && \
	uvicorn main:app --timeout-keep-alive 60 --port 8080 --workers 10

run-dev:
	export PROJECT_ID=sample_project_id && \
	uvicorn main:app --timeout-keep-alive 60 --port 8080 --reload

cloud-build:
	gcloud builds submit --config cloudbuild.yaml 

clear:
	find . -type d -name '__pycache__' -exec rm -rf {} +
	find . -type d -name 'pytest_cache' -exec rm -rf {} +
	find . -type d -name '.ipynb_checkpoints' -exec rm -rf {} +

code-formatting:
	ruff check . --fix
	ruff check .
	ruff format .