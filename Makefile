# === Tailwind Build Automation ===

TAILWIND_INPUT = suborbit/static/src/input.css
TAILWIND_OUTPUT = suborbit/static/css/tailwind.css

all: css

css:
	@echo "🚀 Building Tailwind CSS..."
	npx tailwindcss -i $(TAILWIND_INPUT) -o $(TAILWIND_OUTPUT) --minify
	@echo "✅ Built: $(TAILWIND_OUTPUT)"

watch:
	@echo "👀 Watching for changes..."
	npx tailwindcss -i $(TAILWIND_INPUT) -o $(TAILWIND_OUTPUT) --watch

clean:
	rm -f $(TAILWIND_OUTPUT)

# ----------------------------------------
# 🏷️ Version tagging and release
# ----------------------------------------
# Usage:
#   make release v=1.2.3   → tags and pushes v1.2.3
#   make release v=latest     → tags and pushes latest (no version)
# ----------------------------------------

release:
	@if [ "$(v)" = "latest" ]; then \
		echo "🏷️  Tagging 'latest' release..."; \
		git tag -f latest -m "Rolling latest release"; \
		git push origin latest --force; \
		echo "✅ 'latest' tag pushed successfully!"; \
	elif [ -n "$(v)" ]; then \
		if git rev-parse "v$(v)" >/dev/null 2>&1; then \
        	echo "❌ Tag v$(v) already exists!"; \
        	exit 1; \
    	fi; \
		echo "🏷️  Creating version tag v$(v)..."; \
		git tag -a v$(v) -m "Release v$(v)"; \
		git push origin v$(v); \
		echo "✅ Tag v$(v) created and pushed successfully!"; \
	else \
		echo "❌ Error: please specify a version, e.g. 'make release v=1.0.0' or 'make release v=latest'"; \
		exit 1; \
	fi
