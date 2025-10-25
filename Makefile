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
#   make release v=1.2.3
# Creates an annotated tag and pushes it to origin.

release:
	@if [ -z "$(v)" ]; then \
		echo "❌ Error: please specify version, e.g. make release v=1.0.0"; \
		exit 1; \
	fi
	@echo "🏷️  Creating git tag v$(v)..."
	git tag -a v$(v) -m "Release v$(v)"
	@echo "⬆️  Pushing tag v$(v) to origin..."
	git push origin v$(v)
	@echo "✅ Tag v$(v) created and pushed successfully!"
