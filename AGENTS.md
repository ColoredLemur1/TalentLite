# Agent rules

1. Never read `.env` and never write API keys or other secrets anywhere.
2. Use only invented CVs and candidate data; never real people's data.
3. One change per branch, with the agreed commit prefixes (`feat:`, `ci:`, `chore:`, `test:`, `perf:`, `build:`, `docs:`).
4. Run `make check` before every PR; it must be green.
5. Never open or merge pull requests; the user does that.
6. Never write plan or spec files inside the repository, and never commit them.
7. Commit only low-risk (auto) tasks; every other commit is made by the user. Commit messages are in Spanish.
8. Add the Co-Authored-By AI trailer only to commits of green (auto) tasks, never to any other commit. AI use is explained in AI_LOG.md.
