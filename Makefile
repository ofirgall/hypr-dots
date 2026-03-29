.PHONY: chrome-profiles

chrome-profiles:
	@for d in ~/.config/google-chrome/Profile* ~/.config/google-chrome/Default; do \
		[ -d "$$d" ] && echo "$$d: $$(jq -r '.profile.name' "$$d/Preferences" 2>/dev/null)"; \
	done
