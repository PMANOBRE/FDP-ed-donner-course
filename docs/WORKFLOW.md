# Daily workflow

How to take Ed's latest updates each day without touching my own work.

## The remotes

- `origin`: my repo, `PMANOBRE/FDP-ed-donner-course`. I push here.
- `upstream`: Ed's repo, `ed-donner/undercover`. I only pull from here.

All my work is on `main`. A tag marks where I finished each day.

## Start of the day

```
git status
git pull --no-rebase upstream main
uv sync
npm install
```

`git status` must say "nothing to commit" before the pull. If it doesn't, commit first (see the end of the day).

## During the day

- Lab days: run the day's notebook in `labs/` on the `.venv` kernel.
- Build days: copy the brief from `labs/` into `docs/`, ask for the plan, review it, then ask for the build. The coding agent commits each phase.

## End of the day

```
git add -A
git commit -m "Week 1 Day 4 lab"
git tag -a week1day4-done -m "End of Week 1 Day 4"
git push --follow-tags
```

Name the commit and the tag for the day. The tag needs `-a`, since `--follow-tags` pushes only annotated tags.

## Why my work is safe

- A pull merges Ed's changes with mine and never replaces my committed work.
- Files only Ed changed take his version, which is usually labs, guides and `community_contributions/`.
- Files only I changed stay as they are: `backend/`, `agent/`, `dashboard/` and `docs/`.
- If we both changed the same lines, git stops with a conflict and asks me to choose. `git merge --abort` undoes the pull.
- Only uncommitted changes are at risk, so I always commit before I pull.

## Looking back

- `git tag` lists my days.
- `git checkout week1day3-done` shows my work at the end of that day. `git checkout main` comes back.
- `git log --oneline` shows every commit.
- To see one of Ed's builds without switching: `git show upstream/week1day5-end:docs/STATUS.md`.
