#!/usr/bin/env bash

set -eu

declare -a ignored_branches=("debug/nv2a_debugger")


unstaged_changes=$(git status --porcelain | grep "^ M" | wc -l)
#untracked_files=$(git status --porcelain | grep "^??" | wc -l)
untracked_files=0
if [[ $unstaged_changes -gt 0 || $untracked_files -gt 0 ]]; then
  echo "Error: Unstaged changes or untracked files found."
  exit 1
fi

git checkout master
git pull upstream master
git push origin master


echo ""
echo "Rebasing debug branches..."

git branch --list "debug/*" | while IFS= read -r branch; do
  branch="${branch#* }"
  branch="${branch#"${branch%%[^[:space:]]*}"}"

  if [[ " ${ignored_branches[@]} " == *" $branch "* ]]; then
    continue
  fi
  
  echo "${branch}"

  git checkout "${branch}"
  git rebase HEAD^ --onto master
  git push -f

  echo ""
  
done
