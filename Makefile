.PHONY: build-copilot check-copilot

# Regenerate the GitHub Copilot CLI layer (.github/agents + .github/skills)
# from the canonical Claude Code sources (agents/, commands/, skills/).
build-copilot:
	python3 scripts/build-copilot.py

# Fail if the Copilot CLI layer is out of sync with its sources. Run in CI.
check-copilot:
	python3 scripts/build-copilot.py --check
