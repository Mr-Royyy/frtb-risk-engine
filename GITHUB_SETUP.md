# GitHub setup guide

This file walks you through turning the starter folder into a GitHub repository.

## Option 1: GitHub Desktop

1. Open GitHub Desktop.
2. Click **File > Add Local Repository**.
3. Select the `frtb-lite-risk-engine` folder.
4. If it asks whether you want to initialize Git, choose yes.
5. Add a commit message such as:

```text
Initial FRTB-lite market risk engine scaffold
```

6. Click **Publish repository**.
7. Keep the repo public if you want recruiters to see it.

## Option 2: Command line with GitHub CLI

From inside the project folder:

```bash
git init
git add .
git commit -m "Initial FRTB-lite market risk engine scaffold"
gh repo create frtb-lite-risk-engine --public --source=. --remote=origin --push
```

If `gh` is not installed, install GitHub CLI first, then run:

```bash
gh auth login
```

## Option 3: Command line without GitHub CLI

Create an empty repository on GitHub called:

```text
frtb-lite-risk-engine
```

Then run:

```bash
git init
git add .
git commit -m "Initial FRTB-lite market risk engine scaffold"
git branch -M main
git remote add origin https://github.com/YOUR_USERNAME/frtb-lite-risk-engine.git
git push -u origin main
```

Replace `YOUR_USERNAME` with your GitHub username.

## Recommended first GitHub issue list

After publishing, create these issues:

1. Implement robust portfolio CSV ingestion in C++.
2. Add pybind11 build target and Python wrapper.
3. Add option Greeks and Black-Scholes pricing.
4. Add rolling VaR backtesting notebook.
5. Add dashboard screenshots to README.
6. Add benchmark comparing C++ Monte Carlo to Python baseline.
