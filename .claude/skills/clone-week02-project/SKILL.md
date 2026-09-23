---
name: clone-week02-project
description: Clone the Week02Project repository (SreeKonda10/Week02Project) from GitHub. Use this whenever the user wants to clone, check out, or get a local copy of this repo — on a new machine, in a new directory, or for a teammate joining the project. Trigger on phrases like "clone the repo", "clone this project", "get a copy of Week02Project", or "set up this repo somewhere else", even if the user doesn't give the full GitHub URL.
---

# Clone Week02Project

Clone the repo at `https://github.com/SreeKonda10/Week02Project` to a local directory.

## Steps

1. Confirm the destination directory with the user if it isn't obvious from context (default: clone into a folder named `Week02Project` in the current working directory).
2. Check that `git` is available (`git --version`). If not, tell the user to install Git first.
3. Clone the repo:
   ```bash
   git clone https://github.com/SreeKonda10/Week02Project.git <destination>
   ```
4. `cd` into the cloned directory and confirm it worked (`git remote -v`, `ls`).

## Notes

- The repo requires no special auth for cloning over HTTPS if it's public. If the clone fails with a permission/auth error, the repo may be private — in that case use SSH (`git clone git@github.com:SreeKonda10/Week02Project.git`) or ensure the user is authenticated via `gh auth login` / has SSH keys set up.
- Do not overwrite an existing directory at the destination — if one exists and is non-empty, ask the user how to proceed rather than deleting it.
- After cloning, point the user to the README in the repo for setup instructions (venv, dependencies) — this skill only handles the clone step itself.
