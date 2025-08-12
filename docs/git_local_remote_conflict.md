# Git Local vs Remote History Conflict Resolution 

When your local and remote branches have **different commit histories**, Git requires you to reconcile them before pushing or pulling.  
This document provides safe, step-by-step approaches.

---

## 1. Inspect the Situation

Before taking action, see what’s different between local and remote:

```bash
git fetch origin
git log --oneline --graph --decorate --all
```

- **Local branch**: `main`
- **Remote branch**: `origin/main`

---

## 2. Common Scenarios and Solutions

### **A. Merge (Preserve Both Histories)**

Use when you want to keep both sets of commits:

```bash
git pull origin main
# Resolve conflicts if prompted, then:
git add <conflicted-files>
git commit
```

- ✅ Pros: No commit loss.
- ⚠️ Cons: Creates merge commits.

---

### **B. Rebase (Clean, Linear History)**

Use when you want your local changes replayed on top of the remote:

```bash
git fetch origin
git rebase origin/main
# Resolve conflicts if prompted, then:
git rebase --continue
```

- ✅ Pros: Cleaner commit history.
- ⚠️ Cons: Don’t rebase shared/public branches without coordination.

---

### **C. Force Push (Overwrite Remote)**

Use when you want **local** to replace **remote** entirely:

```bash
git push origin main --force
```

- ⚠️ **Danger**: Deletes commits from remote not in your local history.
- ✅ Good if remote is disposable or you’re the only contributor.

---

### **D. Reset Local to Match Remote**

Use when you want **remote** to replace **local** entirely:

```bash
git fetch origin
git reset --hard origin/main
```

- ⚠️ **Danger**: Deletes local commits not in remote.
- ✅ Useful when remote has the desired state.

---

## 3. Safety Tips

- Always **create a backup branch** before destructive operations:
```bash
git branch backup-branch
```

- Communicate with your team before using `--force`.
- Use `git status` often to avoid surprises.

---

## 4. Quick Decision Table

| Goal                                   | Command                                      |
|----------------------------------------|-----------------------------------------------|
| Keep both histories                    | `git pull origin main`                        |
| Reapply local commits on remote branch | `git fetch origin && git rebase origin/main`  |
| Make remote match local exactly        | `git push origin main --force`                |
| Make local match remote exactly        | `git fetch origin && git reset --hard origin/main` |

---

## 5. Visual Aid

```
LOCAL   A---B---C
REMOTE  A---X---Y

Merge   A---B---C---M (merge commit) ---Y
Rebase  A---X---Y---B'---C'
Force   A---B---C
Reset   A---X---Y
```

---
