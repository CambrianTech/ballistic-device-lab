"""One-command fresh audit, wide search, refinement and README publication."""


def main():
    from datetime import datetime, timezone
    from pathlib import Path

    from ballistic_lab.experiments.dc_audit import main as audit
    from ballistic_lab.experiments.dc_wide import main as search
    from ballistic_lab.pipeline.dc_publish import main as publish

    audit()
    search()
    publish(Path("results") / datetime.now(timezone.utc).strftime("dc-wide-%Y%m%d-%H%M%S"))


if __name__ == "__main__":
    main()
