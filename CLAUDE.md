# CLAUDE

## Read Before Coding

Always read these documents before starting work:

1. docs/PRODUCT_SPEC.md
2. docs/ARCHITECTURE.md
3. docs/DATABASE.md
4. docs/ROADMAP.md

These documents are the source of truth.

---

# Development Rules

* Work only on the requested task.
* Never implement future features.
* Never rewrite the entire project.
* Modify the minimum number of files.
* Follow the existing architecture.
* Reuse existing code whenever possible.
* Do not duplicate logic.
* Keep functions small.
* Keep modules independent.

---

# Architecture Rules

* Business logic only in Services.
* Database access only in Repositories.
* AI access only through Providers.
* Telegram API only in Handlers.
* No SQL outside Repositories.
* No hardcoded values.

---

# Before Writing Code

Always:

* Read the related documentation.
* Check existing implementation.
* Reuse existing services.
* Explain architecture changes before implementing them.

---

# After Completing a Task

Always:

* Verify the code compiles.
* Verify existing functionality is preserved.
* Verify architecture is unchanged.
* Stop and wait for the next task.

Do not continue with additional features unless explicitly requested.
