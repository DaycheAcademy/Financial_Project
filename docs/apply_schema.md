# SQL Server Schema Runner 

This document explains a `PyMSSQLClient.apply_schema_file` implementation that **uses a regular expression** to split a SQL Server schema file on `GO` batch separators and execute each batch with `pymssql`.

---

## Why we need this

- SQL Server tools (SSMS, sqlcmd) treat a line containing only `GO` (case-insensitive) as a **batch separator**.
- Drivers like `pymssql` **do not** understand `GO`; they only accept one batch per `execute` call.
- We therefore need to **split** a `schema.sql` into batches wherever a `GO` line appears, **honor `GO 3` repeat counts**, and execute each batch in order.

---

## Full method

```python
import os
import re
from pathlib import Path
from typing import Optional

class PyMSSQLClient(BaseSQLServerClient):
    # ... existing code ...

    def apply_schema_file(
        self,
        file_path: str,
        *, 
        encoding: str = "utf-8",
        stop_on_error: bool = True
    ) -> None:
        """
        Read a .sql file (with optional `GO` batch separators) and execute it against the current DB.

        Args:
            file_path: Path to the SQL schema file.
            encoding: Text encoding used to read the file.
            stop_on_error: If True, rollback the whole run on first error and re-raise.
                           If False, keep going and commit what succeeded (errors are aggregated).
        """
        if not getattr(self, "conn", None) or not getattr(self, "cursor", None):
            raise RuntimeError("No active connection. Call connect_sql_auth() first.")

        path = Path(file_path)
        if not path.exists() or not path.is_file():
            raise FileNotFoundError(f"Schema file not found: {file_path}")

        sql_text = path.read_text(encoding=encoding)

        # 1) Build a pattern that matches lines containing only `GO` (case-insensitive),
        #    with optional whitespace and an optional repeat count (e.g., `GO 3`).
        batch_pattern = re.compile(
            r"(?im)^[ \t]*GO(?:[ \t]+(?P<count>\d+))?[ \t]*\r?$",
            re.MULTILINE,
        )

        # 2) Iterate matches to cut the script into batches.
        pos = 0
        batches: list[tuple[str, int]] = []
        for m in batch_pattern.finditer(sql_text):
            batch_sql = sql_text[pos:m.start()].strip()
            if batch_sql:
                repeat = int(m.group("count") or "1")
                batches.append((batch_sql, repeat))
            pos = m.end()

        # 3) Add the trailing tail (after the last GO)
        tail = sql_text[pos:].strip()
        if tail:
            batches.append((tail, 1))

        if not batches:
            return  # nothing to run

        errors: list[Exception] = []

        try:
            # 4) Execute the batches; honor repeat counts (`GO N`)
            for batch_sql, repeat in batches:
                for _ in range(repeat):
                    try:
                        self.cursor.execute(batch_sql)
                    except Exception as e:
                        if stop_on_error:
                            if not self.autocommit:
                                self.rollback()
                            raise
                        else:
                            errors.append(e)

            # 5) If we're not autocommitting, commit when done (unless we had errors)
            if not self.autocommit and (stop_on_error or not errors):
                self.commit()

        except Exception:
            # 6) On a hard failure, ensure rollback if not autocommit
            if not self.autocommit:
                self.rollback()
            raise

        if errors:
            # 7) If we continued past errors, raise a compact summary at the end
            msg_lines = [f"{len(errors)} error(s) occurred while applying {file_path}."]
            first = errors[0]
            msg_lines.append(f"First error: {first.__class__.__name__}: {first}")
            raise RuntimeError("\n".join(msg_lines))
```

---

## Explanation, line by line

### Compile the `GO` pattern

```python
batch_pattern = re.compile(
    r"(?im)^[ \t]*GO(?:[ \t]+(?P<count>\d+))?[ \t]*\r?$", re.MULTILINE
)
```
- `(?im)` enables **case-insensitive** (`i`) and **multi-line** (`m`) modes.
- `^[ \t]*` allows leading spaces/tabs.
- `GO` is the literal batch marker (case-insensitive).
- `(?:[ \t]+(?P<count>\d+))?` optionally captures a numeric **repeat count** into a named group `count` (e.g., `GO 5`).
- `[ \t]*\r?$` allows trailing spaces/tabs and an optional carriage return before the line end.
- With `re.MULTILINE`, `^` and `$` match at line boundaries, so the pattern only matches **whole lines that are `GO`** (plus optional count).

### Splitting into batches

We walk the matches and take the text **between** them as a batch. For `GO 3`, we store `(batch_sql, 3)`. The trailing text after the last match is added as the final batch.

### Executing batches

- We loop over `(sql, repeat)` and call `self.cursor.execute(sql)` `repeat` times.
- If `stop_on_error=True`, we rollback (when not autocommit) and re-raise immediately.
- If `stop_on_error=False`, we **collect** the exceptions, continue, and raise a summary at the end.

### Transactions

- If `self.autocommit` is `False`, we commit once at the end (if appropriate), or rollback on failure.
- If `self.autocommit` is `True`, each `execute` is committed by the driver as it goes.

---

## Usage example

```python
client = PyMSSQLClient(autocommit=False)
client.connect_sql_auth(server="host,1433", database="MyDb", user="sa", password="...")
client.apply_schema_file("schema.sql")
client.close()
```

> This will apply the schema in a single transaction (because `autocommit=False`), stopping on the first error by default.
