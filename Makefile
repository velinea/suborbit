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

# ----------------------------------------
# 🔼 Auto version bumping
# ----------------------------------------
# Usage:
#   make bump patch   → v1.0.1
#   make bump minor   → v1.1.0
#   make bump major   → v2.0.0
#
# Reads latest git tag, increments semver, creates & pushes new tag

bump:
	@type=$(type); \
	if [ -z "$$type" ]; then \
		echo "❌ Error: specify type (patch|minor|major), e.g. make bump type=minor"; \
		exit 1; \
	fi; \
	last=$$(git describe --tags --abbrev=0 2>/dev/null || echo "v0.0.0"); \
	echo "🔢 Last version: $$last"; \
	ver=$$(echo $$last | sed 's/^v//'); \
	major=$$(echo $$ver | cut -d. -f1); \
	minor=$$(echo $$ver | cut -d. -f2); \
	patch=$$(echo $$ver | cut -d. -f3); \
	case "$$type" in \
		major) major=$$((major+1)); minor=0; patch=0 ;; \
		minor) minor=$$((minor+1)); patch=0 ;; \
		patch) patch=$$((patch+1)) ;; \
		*) echo "❌ Invalid type: $$type"; exit 1 ;; \
	esac; \
	new="v$$major.$$minor.$$patch"; \
	echo "🏷️  Creating new tag $$new..."; \
	git tag -a $$new -m "Release $$new"; \
	git push origin main $$new; \
	echo "✅ Tagged and pushed $$new successfully!"
# ----------------------------------------
