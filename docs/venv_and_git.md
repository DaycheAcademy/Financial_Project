# Python Virtual Environment

Documentation, Links and Helpful Hints on VENV.

---

## Helpful Links

1. https://docs.python.org/3/library/venv.html
2. https://virtualenvwrapper.readthedocs.io/en/latest/
3. https://www.freecodecamp.org/news/virtualenv-with-virtualenvwrapper-on-ubuntu-18-04/


---

## Connecting Your Local Project to GitHub Repository

Follow these steps to link your local project folder to project repository and push your code.

---

## 1. Prerequisites

Before starting, ensure you have:

- [Git](https://git-scm.com/downloads) installed (`git --version` should work in your terminal).
- A GitHub account.
- This repository already created on GitHub (empty, with no README or `.gitignore` if possible).
- Your project files ready in a local folder.

---

## 2. Navigate to Your Project Folder

Open a terminal and go to your local project directory:

```bash
cd /path/to/your/project
```

---

## 3. Initialize Git (if not already initialized)

If your project is **not** yet under Git version control:

```bash
git init
```

If it’s already a Git repo (`.git` folder exists), you can skip this step.

---

## 4. Add Project's GitHub Repository as a Remote

Replace `<USERNAME>` with your GitHub username and `<REPO>` with the name of this repository:

```bash
git remote add origin https://github.com/<USERNAME>/<REPO>.git
```

You can check that it’s added correctly:

```bash
git remote -v
```

---

## 5. Add and Commit Your Files

```bash
git add .
git commit -m "Initial commit"
```

---

## 6. Push to GitHub

If this is the **first push** and your GitHub repo is empty:

```bash
git branch -M main
git push -u origin main
```

> `-M` renames your local branch to `main` (GitHub default).  
> `-u` sets `origin/main` as the default remote branch.

---

## 7. Verify on GitHub

Go to your repository’s GitHub page in the browser — you should now see your project files.

---

## 8. Common Issues

### ❌ Authentication failed
- Make sure you’re logged in to GitHub.
- If using HTTPS, you may need a [Personal Access Token](https://docs.github.com/en/github/authenticating-to-github/creating-a-personal-access-token) instead of your password.

### ❌ Remote origin already exists
If you already have a remote named `origin`, update it instead:

```bash
git remote set-url origin https://github.com/<USERNAME>/<REPO>.git
```

---

## 9. Next Steps

- Continue making changes in your local project.
- Use `git add`, `git commit`, and `git push` to update GitHub.
- Pull updates with `git pull` if collaborating.

---
