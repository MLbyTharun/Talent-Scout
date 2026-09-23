"""
Batch runner — runs the full graph (parse_resume -> fetch_github -> evaluate)
across multiple candidates for one job description.

Two things batch processing needs that single-candidate runs don't:
  1. One candidate's failure (bad PDF, no GitHub link, API hiccup)
     shouldn't kill the whole batch.
  2. Since each candidate's steps are I/O-bound (PDF parse, GitHub API,
     LLM calls), running them concurrently is much faster than one-by-one —
     but bounded, so you don't blow through GitHub's rate limit or hit
      your LLM provider's concurrency cap.
"""

from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass, field

from agent_graph import build_graph


@dataclass
class CandidateResult:
    resume_path: str
    success: bool
    notes: dict | None = None
    resume_data: dict | None = None
    repo_profiles: list = field(default_factory=list)
    github_fetch_error: str | None = None
    error: str | None = None


def evaluate_one(resume_path: str, jd_text: str, use_crew: bool = True, username: str | None = None, _app=None) -> CandidateResult:
    """Run the full graph for a single candidate, catching any failure."""
    app = _app if _app is not None else build_graph(use_crew=use_crew)

    inputs = {"resume_path": resume_path, "jd_text": jd_text}
    if username:
        inputs["username"] = username

    try:
        result = app.invoke(inputs)
        return CandidateResult(
            resume_path=resume_path,
            success=True,
            notes=result.get("notes"),
            resume_data=result.get("resume_data"),
            repo_profiles=result.get("repo_profiles", []),
            github_fetch_error=result.get("github_fetch_error"),
        )
    except Exception as e:
        # A bad PDF, missing GitHub username, or API failure for ONE
        # candidate shouldn't stop the rest of the batch. Expose only the
        # exception message — full tracebacks stay out of the UI/results
        # so paths and internals aren't leaked to whoever runs the app.
        return CandidateResult(
            resume_path=resume_path,
            success=False,
            error=f"{type(e).__name__}: {e}",
        )


def run_batch(
    resume_paths: list[str],
    jd_text: str,
    use_crew: bool = True,
    usernames: dict[str, str] | None = None,
    max_workers: int = 3,
    progress_callback=None,
) -> list[CandidateResult]:
    """
    Evaluate multiple candidates against the same JD.

    usernames: optional {resume_path: github_username} overrides, for
               resumes that don't have a parseable GitHub link.
    max_workers: keep this modest (3-5) — each worker makes GitHub API
                 calls + 1-3 LLM calls (more if use_crew=True), and you
                 don't want to hammer either provider's rate limit.
    progress_callback: optional fn(done_count, total_count) for UI progress bars.
    """
    usernames = usernames or {}
    results: list[CandidateResult] = []
    total = len(resume_paths)

    if not resume_paths:
        return []

    # Build once and share — each invoke() gets its own state, and
    # crew_evaluate_node constructs fresh agents per call.
    app = build_graph(use_crew=use_crew)

    with ThreadPoolExecutor(max_workers=max_workers) as pool:
        futures = {
            pool.submit(evaluate_one, path, jd_text, use_crew, usernames.get(path), app): path
            for path in resume_paths
        }

        by_path: dict[str, CandidateResult] = {}
        for i, future in enumerate(as_completed(futures), start=1):
            by_path[futures[future]] = future.result()
            if progress_callback:
                progress_callback(i, total)

    # Return in input order, not completion order — UI shouldn't shuffle.
    return [by_path[p] for p in resume_paths]


if __name__ == "__main__":
    import sys

    jd = "Paste JD here..."
    paths = sys.argv[1:]
    if not paths:
        print("Usage: python batch_runner.py resume1.pdf resume2.pdf ...")
        sys.exit(1)

    def print_progress(done, total):
        print(f"  {done}/{total} done")

    results = run_batch(paths, jd, progress_callback=print_progress)
    for r in results:
        if r.success:
            print(f"OK  {r.resume_path}: {r.notes}")
        else:
            print(f"FAIL {r.resume_path}: {r.error}")