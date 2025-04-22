LOCALES = locales
DOMAIN = base
PYFILES = *.py sections/*.py

LANGUAGES = en it

.PHONY: translate compile clean

translate:
	@echo "🧠 Extracting translatable strings..."
	xgettext --from-code=UTF-8 -d $(DOMAIN) -o $(LOCALES)/$(DOMAIN).pot $(PYFILES)
	@echo "🔁 Updating .po files..."
	@for lang in $(LANGUAGES); do \
		msgmerge --update --backup=none --no-fuzzy-matching $(LOCALES)/$$lang/LC_MESSAGES/$(DOMAIN).po $(LOCALES)/$(DOMAIN).pot; \
	done

compile:
	@echo "⚙️ Compiling .po files to .mo..."
	@for lang in $(LANGUAGES); do \
		msgfmt --output-file=$(LOCALES)/$$lang/LC_MESSAGES/$(DOMAIN).mo $(LOCALES)/$$lang/LC_MESSAGES/$(DOMAIN).po; \
	done
	@echo "✅ Done!"

clean:
	@echo "🧹 Cleaning compiled files..."
	find $(LOCALES) -name "*.mo" -delete
	@echo "✅ Cleaned!"