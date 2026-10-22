"""Optional Kwant coherent, spinless nearest-neighbor graphene transport."""

from dataclasses import dataclass

import numpy as np

from ballistic_lab.pipeline.contracts import SquareDevice


@dataclass(frozen=True, slots=True)
class LatticeRequest:
    energies_ev: tuple[float, ...]
    lattice_constant_m: float = 0.246e-9
    hopping_ev: float = 2.7
    onsite_ev: float = 0.0
    tolerance: float = 1e-7

    def __post_init__(self):
        object.__setattr__(self, "energies_ev", tuple(self.energies_ev))
        if not self.energies_ev or not np.isfinite(self.energies_ev).all():
            raise ValueError("Specify finite probe energies in eV")
        for value in (self.lattice_constant_m, self.hopping_ev, self.tolerance):
            if not np.isfinite(value) or value <= 0:
                raise ValueError("Lattice constant, hopping and tolerance must be positive")
        if not np.isfinite(self.onsite_ev):
            raise ValueError("Onsite energy must be finite")


def build_system(device: SquareDevice, request: LatticeRequest, *, ribbon=False):
    """Square cavity or matched two-terminal ribbon; x is the zigzag axis.

    Coordinates are in lattice-constant units. Obstacles remove sites without
    passivation or edge relaxation. Leads have the same onsite energy as the
    device; no lead doping step, magnetic field, or self-consistent potential.
    """
    import kwant
    from matplotlib.path import Path

    half = device.physical_width() / request.lattice_constant_m / 2
    lat = kwant.lattice.honeycomb(norbs=1)
    system = kwant.Builder()
    system[lat.shape(lambda p: abs(p[0]) < half and abs(p[1]) < half, (0, 0))] = request.onsite_ev
    paths = [Path(poly) for poly in device.geometry()]
    if ribbon and paths:
        raise ValueError("Reference ribbon must have no obstacles")
    for site in list(system.sites()):
        if any(path.contains_point(np.array(site.pos) / half, radius=1e-10) for path in paths):
            del system[site]
    system[lat.neighbors()] = -request.hopping_ev
    translations = [(-1, 0), (1, 0)] if ribbon else [(-1, 0), (1, 0), (-1, 2), (1, -2)]
    for port, translation in enumerate(translations):
        symmetry = kwant.TranslationalSymmetry(lat.vec(translation))
        lead = kwant.Builder(symmetry)
        transverse = 1 if port < 2 else 0
        contact_half = half if ribbon else 0.3 * half
        lead[lat.shape(lambda p: abs(p[transverse]) < contact_half, (0, 0))] = request.onsite_ev
        lead[lat.neighbors()] = -request.hopping_ev
        system.attach_lead(lead)
    return system.finalized()


def solve_spectrum(system, request: LatticeRequest) -> tuple[dict, ...]:
    """T[outgoing, incoming] includes reflection on its diagonal; per spin."""
    import kwant

    h = system.hamiltonian_submatrix(sparse=True)
    difference = h - h.getH()
    if difference.nnz and np.max(abs(difference.data)) > request.tolerance:
        raise RuntimeError("Non-Hermitian Hamiltonian")
    records = []
    for energy in request.energies_ev:
        scattering = kwant.smatrix(system, energy)
        modes = np.array([scattering.num_propagating(p) for p in range(len(system.leads))])
        matrix = np.array(
            [
                [scattering.transmission(out, inc) for inc in range(len(modes))]
                for out in range(len(modes))
            ]
        )
        s = scattering.data
        if not np.isfinite(s).all() or not np.isfinite(matrix).all():
            raise RuntimeError(f"Nonfinite quantum transmission at {energy} eV")
        unitary = float(np.max(abs(s.conj().T @ s - np.eye(s.shape[1])), initial=0))
        conservation = float(np.max(abs(matrix.sum(axis=0) - modes)))
        reciprocity = float(np.max(abs(matrix - matrix.T)))
        # Equal reservoir occupations cancel at each energy, before integration.
        equilibrium = float(np.max(abs(matrix.sum(axis=1) - modes)))
        if max(unitary, conservation, reciprocity, equilibrium) > request.tolerance:
            raise RuntimeError(f"Quantum conservation gate failed at {energy} eV")
        records.append(
            dict(
                energy_ev=energy,
                modes=modes.tolist(),
                transmission=matrix.tolist(),
                unitarity_residual=unitary,
                conservation_residual=conservation,
                reciprocity_residual=reciprocity,
                equilibrium_residual=equilibrium,
            )
        )
    return tuple(records)


@dataclass(frozen=True, slots=True)
class LatticeResult:
    device_fingerprint: str
    request: LatticeRequest
    site_count: int
    kwant_version: str
    spectrum: tuple[dict, ...]
    observable: str = "Coherent zero-bias transmission per spin; not rectification"


class LatticeStage:
    def evaluate(self, device: SquareDevice, request: LatticeRequest) -> LatticeResult:
        import kwant

        system = build_system(device, request)
        return LatticeResult(
            device.fingerprint,
            request,
            len(system.sites),
            kwant.__version__,
            solve_spectrum(system, request),
        )
