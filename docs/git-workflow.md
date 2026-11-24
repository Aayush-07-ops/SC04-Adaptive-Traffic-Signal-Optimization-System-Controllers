# Git workflow and commit plan

## Rules
- One understandable improvement per commit. **Every member makes at least one meaningful commit.**
- Before every push: pull the latest version, run `python src/validate_data.py`, check `git status`, add only intended files, write a clear message, push your branch, ask another member to review.
- Never commit `.venv`, passwords, private datasets or personal information (the `.gitignore` already covers `.venv`).
- Never use messages like `update`, `changes`, `final`, `done`. Never upload everything in one last commit.
- Never overwrite another member's work without discussing it.

## Commands
```bash
git clone REPOSITORY-URL
cd REPOSITORY-NAME
git checkout -b your-name-step1
# create or edit your assigned files
git add <the files you changed>
git commit -m "Describe the real work you completed"
git push -u origin your-name-step1
# then open a Pull Request on GitHub and ask a teammate to review and merge
```
GitHub Desktop is fine too: pull first, work on a small task, write a clear commit message, push, let the team review.

## Recommended commit sequence (suggested owner)
| # | Commit message | Suggested owner |
|---|---|---|
| 1 | Create repository structure for SC04 | Repository |
| 2 | Add team roles and Step 1 project contract | Repository |
| 3 | Define input fields, units, and validation rules | Data |
| 4 | Document fixed-time traffic baseline | Baseline |
| 5 | Add five mandatory test cases | Baseline |
| 6 | Add sample-data validation script | Testing/UI |
| 7 | Add Product V1 screen sketch | Testing/UI |
| 8 | Add Step 1 evidence and run instructions | Repository |

For teams of 3: Repository and Testing/UI are combined. For teams of 4: one member per role.
**Tip:** after uploading this ready-made folder, split the work so each member makes real commits that edit
or improve their own files (for example replacing placeholder names, adding their own screenshots, adjusting
wording after review). Commits must reflect work the member genuinely did and understands.
