# community

Results people ran in the website playground and chose to publish. Each file arrives as a pull
request opened from the playground's "Propose it for the gallery" button, and appears on the website
once merged.

Rules checked by `tests/test_community.py` on every pull request:

- the file follows `schema: intent-labeler/community/1`;
- every intent points to results that exist in the file;
- nothing that looks like a secret (API keys, passwords, tokens) is inside.

Maintainers review the content itself: the query should be a real search, not spam or personal data.
