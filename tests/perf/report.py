import os


def report(title: str, rows: list[tuple[str, float | str, str]]) -> None:
    """Append a Markdown table to the GitHub job summary, or print it locally."""
    lines = [f"### {title}", "", "| case | value | unit |", "|---|---|---|"]
    for case, value, unit in rows:
        shown = f"{value:.2f}" if isinstance(value, float) else value
        lines.append(f"| {case} | {shown} | {unit} |")
    table = "\n".join(lines) + "\n"

    summary_path = os.environ.get("GITHUB_STEP_SUMMARY")
    if summary_path:
        with open(summary_path, "a", encoding="utf-8") as summary:
            summary.write(table + "\n")
    else:
        print("\n" + table)
