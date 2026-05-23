# Graphnetes

## Comments

Only two comment styles are permitted:

**Inline and block comments** — use `#`:
```python
# The kubernetes client must configure authentication and authorization parameters
# in accordance with the API server security policy.
```

**Docstrings** — use `"""..."""`:
```python
def fetch(self, namespace: Optional[str] = None) -> Generator[RawResource, None, None]:
    """Yield raw resource dicts for all resources in a single namespace.

    Scopes to namespace if given, otherwise fetches the full cluster.
    """
```

No other comment formats (`//`, `/* */`, `--`, etc.).

Comments must always appear on the line above the code they describe, never inline to the right of it:

```python
# Good
# Directly derived from resource spec
EXTRACTED = "EXTRACTED"

# Bad
EXTRACTED = "EXTRACTED"  # directly derived from resource spec
```
