# Contributing to SceneReady

SceneReady is a hackathon project with a small team. Keep changes reviewable, tested, and easy to
demonstrate.

## Team workflow

1. Accept the GitHub collaborator invitation.
2. Clone the repository and create a branch from the latest `main`.
3. Keep each branch focused on one feature or fix.
4. Run the checks before opening a pull request.
5. Request one teammate review; merge only after the deployed workflow remains reproducible.

```bash
git switch main
git pull --ff-only
git switch -c feature/short-description

bash scripts/setup.sh

git add <changed-files>
git commit -m "Describe the user-visible change"
git push -u origin feature/short-description
```

## Boundaries

- Never commit API keys, access codes, `.env` files, private scripts, or confidential PDFs.
- Only Gemini/Google Cloud AI and built-in Parallel AI capabilities may be used in the project.
- Do not add another agent framework or AI API without first checking the official rules.
- Preserve the fixed breakdown → research → planning → validation order.
- Do not convert warnings or unknowns into confident legal claims.
- Keep the live/offline distinction visible.
- Update tests and documentation with behavior changes.

## Pull-request checklist

- [ ] Python, JavaScript, and shell syntax checks pass.
- [ ] Complete unit test suite passes in Cloud Shell.
- [ ] No secrets or personal data appear in the diff.
- [ ] UI changes work with keyboard navigation and narrow screens.
- [ ] Provider changes are tested with one real live run before deployment.
- [ ] README, validation notes, and demo claims remain accurate.
