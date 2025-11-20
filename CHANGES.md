```text
# CHANGES

- 2025-11-13: Replaced deprecated Streamlit keyword argument `use_container_width` with `width` in application code.
  - True -> width='stretch'
  - False -> width='content'
  - non-literals -> width=('stretch' if expr else 'content')

Note: This change is to address Streamlit deprecation "Please replace `use_container_width` with `width`" and ensure compatibility once the argument is removed (after 2025-12-31).
```
- 2025-11-13: Replaced deprecated Streamlit keyword argument `use_container_width` with `width` in application code.
  - True -> width='stretch'
  - False -> width='content'
  - non-literals -> width=('stretch' if expr else 'content')
