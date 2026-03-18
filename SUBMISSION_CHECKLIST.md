# Submission Checklist

## Before Push

- Verify `uv run ruff check` passes.
- Verify `uv run pytest` passes.
- Verify `docker build .` passes.
- Confirm `OPENAI_API_KEY` is not committed.
- Confirm `.venv`, cache directories, and local artifacts are ignored.

## Before Sending

- Push repository to a public Git hosting provider.
- Add a short project description to the repository page.
- Include the repository link in the recruitment submission.
- Mention that the app works with and without `OPENAI_API_KEY`.
- Mention that seeded demo images have a deterministic local fallback.

## Demo Flow

- Start backend: `make api`
- Start frontend: `make ui`
- Ask: `co ma Kowalski?`
- Ask: `pokaz mi auta powyzej 100k`
- Check API docs: `http://localhost:8000/docs`

## Suggested First Commit Message

`feat: deliver vehicle ai agent recruitment task end-to-end`
