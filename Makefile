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
