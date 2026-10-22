"""Compatibility entry point for the original classical experiment."""

from ballistic_lab.experiments.classical import main
from ballistic_lab.geometry.basic import (
    cross as cross,
)
from ballistic_lab.geometry.basic import (
    segments as segments,
)
from ballistic_lab.geometry.basic import (
    shapes as shapes,
)
from ballistic_lab.transport.cpu import trace as trace

if __name__ == "__main__":
    main()
