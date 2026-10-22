"""Remove explicit obstacle-edge sites while preserving the original leads."""

import kwant
import numpy as np
from scipy.sparse.csgraph import connected_components


def edge_sites(system, polygons, half_width):
    """Under-coordinated sites within one lattice constant of etched edges.

    Outer boundaries and contact buffers are excluded. This selects atomic
    vacancies, not a model of chemical passivation or relaxed edge bonding.
    """
    positions = np.array([s.pos for s in system.sites])
    distance = np.full(len(positions), np.inf)
    for polygon in polygons:
        vertices = np.asarray(polygon) * half_width
        for a, b in zip(vertices, np.roll(vertices, -1, axis=0)):
            vector = b - a
            fraction = np.clip((positions - a) @ vector / (vector @ vector), 0, 1)
            distance = np.minimum(
                distance, np.linalg.norm(positions - a - fraction[:, None] * vector, axis=1)
            )
    degree = np.array([len(system.graph.out_neighbors(i)) for i in range(len(positions))])
    interior = np.max(abs(positions), axis=1) < half_width - 2
    return np.flatnonzero((degree < 3) & (distance < 1) & interior)


class VacancySystem(kwant.system.FiniteSystem):
    """Exact induced subgraph; surviving onsite/hopping terms are unchanged."""

    def __init__(self, original, removed):
        removed = frozenset(map(int, removed))
        if any(i < 0 or i >= len(original.sites) for i in removed):
            raise ValueError("Invalid removed site")
        contacts = set(np.concatenate(original.lead_interfaces).tolist())
        if removed & contacts:
            raise ValueError("Cannot remove a contact interface site")
        self.original = original
        self.indices = tuple(i for i in range(len(original.sites)) if i not in removed)
        inverse = {old: new for new, old in enumerate(self.indices)}
        graph = kwant.graph.Graph()
        graph.num_nodes = len(self.indices)
        for old in self.indices:
            for neighbor in original.graph.out_neighbors(old):
                if neighbor in inverse:
                    graph.add_edge(inverse[old], inverse[neighbor])
        self.graph = graph.compressed()
        self.sites = tuple(original.sites[i] for i in self.indices)
        self.leads = original.leads
        self.lead_interfaces = [
            np.array([inverse[int(i)] for i in port]) for port in original.lead_interfaces
        ]
        self.parameters = original.parameters
        self.site_ranges = [(0, 1, 0), (len(self.indices), 0, len(self.indices))]

    def hamiltonian(self, i, j, *args, params=None):
        return self.original.hamiltonian(self.indices[i], self.indices[j], *args, params=params)

    def components(self):
        graph = self.hamiltonian_submatrix(sparse=True).tocsr()
        graph.setdiag(0)
        graph.eliminate_zeros()
        return int(connected_components(graph, directed=False, return_labels=False))
