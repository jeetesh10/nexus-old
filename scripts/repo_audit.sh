#!/usr/bin/env bash
# Repo audit script: inventories files, flags potentially irrelevant code, runs basic linters/validation,
# and surfaces licensing signals. Safe to run offline; uses graceful fallbacks if tools are missing.
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
REPORT="$ROOT_DIR/audit-report.txt"
shopt -s globstar nullglob extglob

# Helpers
hr() { printf '\n— — — — — — — — — — — — — — — — — — — — — —\n' ; }
log() { printf '%s\n' "$*" | tee -a "$REPORT"; }
start_section() { hr | tee -a "$REPORT"; log "SECTION: $1"; hr | tee -a "$REPORT"; }

# Safe command checks
have() { command -v "$1" >/dev/null 2>&1; }
JQ() { if have jq; then jq "$@"; else cat; fi }

# Portable search helper: use ripgrep if present, otherwise grep with sane defaults.
search_all() {
  # $1: ERE pattern
  if have rg; then
    rg -n --hidden --glob '!.git' --glob '!node_modules' --glob '!vendor' -S -e "$1"
  else
    grep -RInE --exclude-dir=.git --exclude-dir=node_modules --exclude-dir=vendor "$1" .
  fi
}

: > "$REPORT" # truncate

start_section "Repository Inventory"
(
  cd "$ROOT_DIR"
  log "Root: $ROOT_DIR"
  log "Branch:"; git rev-parse --abbrev-ref HEAD 2>/dev/null | tee -a "$REPORT" || true
  log "Git status (short):"; git --no-pager status -s 2>/dev/null | tee -a "$REPORT" || true
  log ""
  log "Top-level tree (depth 2):"
  if have tree; then tree -a -L 2 | tee -a "$REPORT"; else find . -maxdepth 2 -print | sed 's|^\./||' | tee -a "$REPORT"; fi
  log ""
  log "Language fingerprints (sample):"
  if have rg; then
    rg -n --hidden --glob '!.git' --glob '!node_modules' --glob '!vendor' --glob '!*.min.*' --glob '!*audit-report.txt' \
       -e '^module ' -e '^\[tool.poetry\]' -e '"name":' -e '^package ' -e '^\[package\]' \
       -e '^go ' -e '^from ' -e '^import ' -e '^class ' 2>/dev/null | head -n 200 | tee -a "$REPORT" || true
  else
    grep -RInE --exclude-dir=.git --exclude-dir=node_modules --exclude-dir=vendor --exclude=audit-report.txt \
       '^(from |import |class |package |module |go )' . 2>/dev/null | head -n 200 | tee -a "$REPORT" || true
  fi
) 

start_section "Potentially Irrelevant or Dead Files (heuristic)"
(
  cd "$ROOT_DIR"
  log "Large/binary-like files (>1MB):"
  find . -type f -size +1M -not -path '*/.git/*' -not -path '*/node_modules/*' -not -path '*/vendor/*' -print | tee -a "$REPORT" || true

  log ""; log "Sample/placeholder indicators (names & TODOs):"
  if have rg; then
    rg -n --hidden -g '!*node_modules' -g '!*vendor' -g '!*audit-report.txt' -e '(^|/)(sample|example|template|placeholder|dummy|old|backup|bak)(/|$)' -S | tee -a "$REPORT" || true
    rg -n --hidden -g '!*node_modules' -g '!*vendor' -g '!*audit-report.txt' -e '\b(TODO|WIP|HACK|TEMP|DEPRECATED)\b' -S | tee -a "$REPORT" || true
  else
    grep -RInE --exclude-dir=.git --exclude-dir=node_modules --exclude-dir=vendor --exclude=audit-report.txt \
      '(^|/)(sample|example|template|placeholder|dummy|old|backup|bak)(/|$)' . | tee -a "$REPORT" || true
    grep -RInE --exclude-dir=.git --exclude-dir=node_modules --exclude-dir=vendor --exclude=audit-report.txt \
      '\b(TODO|WIP|HACK|TEMP|DEPRECATED)\b' . | tee -a "$REPORT" || true
  fi

  log ""; log "Executable scripts not referenced elsewhere (may be stale):"
  mapfile -t scripts < <(git ls-files | grep -E '\\.(sh|bash|zsh)$' | xargs -r -I{} bash -lc 'test -x "{}" && echo "{}"' || true)
  for s in "${scripts[@]:-}"; do
    base="$(basename "$s")"
    if have rg; then
      hits=$(rg -n --hidden --glob '!.git' --glob '!node_modules' --glob '!vendor' --glob '!*audit-report.txt' -S -e "$base" 2>/dev/null | grep -v "^$s:" | wc -l | tr -d ' ' || echo 0)
    else
      hits=$(grep -RIn --exclude-dir=.git --exclude-dir=node_modules --exclude-dir=vendor --exclude=audit-report.txt -e "$base" . 2>/dev/null | grep -v "^$s:" | wc -l | tr -d ' ' || echo 0)
    fi
    if [[ "${hits:-0}" -eq 0 ]]; then echo "Unreferenced executable: $s"; fi
  done

  log ""; log "Kubernetes YAMLs possibly orphaned (no kustomize/helm context):"
  mapfile -t yamls < <(git ls-files | grep -E '\\.ya?ml$' | grep -E '(deployment|service|ingress|statefulset|configmap|secret|kustomization|Chart\\.yaml)' -i || true)
  has_kustom_or_helm=0
  if have rg; then
    if rg -n -S -e 'kustomization\\.ya?ml|Chart\\.yaml' >/dev/null 2>&1; then has_kustom_or_helm=1; fi
  else
    if grep -RInE 'kustomization\\.ya?ml|Chart\\.yaml' . >/dev/null 2>&1; then has_kustom_or_helm=1; fi
  fi
  for y in "${yamls[@]:-}"; do
    if [[ $has_kustom_or_helm -eq 0 ]]; then echo "Possibly orphaned K8s file: $y"; fi
  done
) 

start_section "Static Checks and Linters"
(
  cd "$ROOT_DIR"
  if have shellcheck; then
    log "ShellCheck:"; sh_files=( $(git ls-files '*.sh' '*.bash' 2>/dev/null || true) )
    if (( ${#sh_files[@]} > 0 )); then shellcheck -x "${sh_files[@]}" | tee -a "$REPORT" || true; else log "No shell scripts found."; fi
  else
    log "ShellCheck not installed. Optional: sudo apt-get update && sudo apt-get install -y shellcheck"
  fi

  log ""; if [[ -f package.json ]]; then
    log "Node/JS detected."; if have npx && npx -y eslint -v >/dev/null 2>&1; then
      log "Running ESLint:"; npx -y eslint . | tee -a "$REPORT" || true
    else log "ESLint unavailable. Optional: npx -y eslint ."; fi
  fi

  log ""; if [[ -f pyproject.toml || -f requirements.txt ]]; then
    log "Python detected."; if have ruff; then log "Ruff:"; ruff check . | tee -a "$REPORT" || true; else log "Ruff not installed. Optional: pip install ruff"; fi
    if have mypy; then
      if have rg; then
        if rg -n -g '!tests/**' -e '^(from|import) ' >/dev/null 2>&1; then log "mypy:"; mypy . | tee -a "$REPORT" || true; fi
      else
        if grep -RInE '^(from|import) ' --exclude-dir=tests . >/dev/null 2>&1; then log "mypy:"; mypy . | tee -a "$REPORT" || true; fi
      fi
    fi
  fi

  log ""; if [[ -f go.mod ]]; then
    log "Go detected."; if have go; then go vet ./... || true; go test ./... -run TestNonExistent -count=0 || true; else log "Go not installed."; fi
  fi

  log ""; if compgen -G "**/*.y?(a)ml" > /dev/null; then
    log "Kubernetes client dry-run validation:";
    if have kubectl; then
      while IFS= read -r y; do
        grep -q 'apiVersion:' "$y" || continue
        kubectl apply --dry-run=client -f "$y" >/dev/null 2>&1 && echo "OK: $y" || echo "Invalid: $y"
      done < <(git ls-files '*.yaml' '*.yml' 2>/dev/null || true) | tee -a "$REPORT"
    else
      log "kubectl not installed. Skipping dry-run validation."
    fi
  fi
) 

start_section "Dependency and Build Sanity"
(
  cd "$ROOT_DIR"
  if [[ -f package.json ]]; then
    log "package.json summary:"; JQ '.name, .license, .scripts' < package.json 2>/dev/null | tee -a "$REPORT" || cat package.json | tee -a "$REPORT"
  fi
  if [[ -f pyproject.toml ]]; then log "pyproject.toml snapshot:"; sed -n '1,200p' pyproject.toml | tee -a "$REPORT"; fi
  if [[ -f requirements.txt ]]; then log "requirements.txt:"; sed -n '1,200p' requirements.txt | tee -a "$REPORT"; fi
  if [[ -f go.mod ]]; then log "go.mod:"; sed -n '1,200p' go.mod | tee -a "$REPORT"; fi
) 

start_section "Licensing and Copyright"
(
  cd "$ROOT_DIR"
  log "Top-level LICENSE/NOTICE:"; ls -1 LICENSE* COPYING* NOTICE* 2>/dev/null | tee -a "$REPORT" || true
  log ""; log "SPDX and copyright markers:";
  if have rg; then
    rg -n --hidden --glob '!.git' --glob '!node_modules' --glob '!vendor' --glob '!*audit-report.txt' -S \
       -e 'SPDX-License-Identifier:' -e 'Copyright \\(c\\)' -e 'Licensed under the ' | tee -a "$REPORT"
  else
    grep -RInE --exclude-dir=.git --exclude-dir=node_modules --exclude-dir=vendor --exclude=audit-report.txt \
       'SPDX-License-Identifier:|Copyright \(c\)|Licensed under the ' . | tee -a "$REPORT" || true
  fi
  log ""; log "Third-party license files:"; find . -type f -iname 'license*' -not -path '*/.git/*' -print | sed 's|^\./||' | tee -a "$REPORT"
) 

start_section "Next Steps"
log "Review audit-report.txt for:"
log "- Candidates for removal (irrelevant/stale)"
log "- Linter and K8s validation errors (potential bugs)"
log "- Licensing files and headers"
hr
printf 'Wrote report: %s\n' "$REPORT"
