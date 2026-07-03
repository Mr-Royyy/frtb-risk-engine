param(
    [string]$RepoName = "frtb-lite-risk-engine"
)

# Initialize a local Git repository and make the first commit.
# If GitHub CLI is installed and authenticated, this script can create and push
# the remote GitHub repository.

git init
git add .
git commit -m "Initial FRTB-lite market risk engine scaffold"

if (Get-Command gh -ErrorAction SilentlyContinue) {
    gh repo create $RepoName --public --source=. --remote=origin --push
}
else {
    Write-Host "GitHub CLI not found. Local Git repo created."
    Write-Host "Create an empty GitHub repo, then run:"
    Write-Host "git branch -M main"
    Write-Host "git remote add origin https://github.com/YOUR_USERNAME/$RepoName.git"
    Write-Host "git push -u origin main"
}
