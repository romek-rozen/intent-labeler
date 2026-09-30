# community

Results contributed as pull requests. The playground itself now sends public results to an n8n
collection instead (see `site/README.md`) and no longer shows a GitHub button, so files arrive here only
when someone opens a pull request by hand.

They are **collected, not published**: the website does not show them until there is moderation
(a query can contain offensive or personal text, and checking that with a model on the fly is not
done yet). `SHOW_COMMUNITY` in `scripts/build_site.py` switches the gallery on.

Rules checked by `tests/test_community.py` on every pull request:

- the file follows `schema: intent-labeler/community/1`;
- every intent points to results that exist in the file;
- nothing that looks like a secret (API keys, passwords, tokens) is inside.

Maintainers review the content itself: the query should be a real search, not spam or personal data.
