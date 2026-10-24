"""Bounded geometry-to-current adapter for self-consistent candidate evaluation.

Uses the same cold-start physics as the loaded fixture pilot. This is an
integration boundary, not a qualified search score or calibrated device model.
"""
import time
import numpy as np
from .geometry_feedback_fixture import geometry_fixture
from .equilibrium_charge import EquilibriumChargeDevice
from .bias_charge import BiasChargeDevice
from .site_acceleration import solve_accelerated
from .feedback_current import FeedbackCurrentModel


class GeometryFeedbackModel:
    def __init__(self, device, *, max_poles=131072, max_evaluations=24,
                 max_charge_calls=240, max_seconds=5400, record=None):
        for name, value in [('max_poles',max_poles),('max_evaluations',max_evaluations),
                            ('max_charge_calls',max_charge_calls),('max_seconds',max_seconds)]:
            if type(value) is not int or value <= 0:
                raise ValueError(name+' must be a positive integer')
        self.device=device
        self.max_poles=max_poles
        self.max_evaluations=max_evaluations
        self.max_charge_calls=max_charge_calls
        self.deadline=time.monotonic()+max_seconds
        self.evaluations=0
        self.charge_calls=0
        self.neutral=None
        self.record=record
        self.bridge=FeedbackCurrentModel(self.evaluate,lead_order=(0,1,2,3))

    def _budget(self):
        if time.monotonic() >= self.deadline:
            raise RuntimeError('Geometry feedback time budget exhausted')

    def evaluate(self, voltage):
        voltage=np.asarray(voltage,dtype=float)
        if voltage.shape != (4,) or not np.isfinite(voltage).all():
            raise ValueError('Four finite reservoir voltages required')
        self._budget()
        if self.evaluations >= self.max_evaluations:
            raise RuntimeError('Geometry feedback evaluation budget exhausted')
        self.evaluations += 1
        if self.neutral is None:
            reference,_,_=geometry_fixture(self.device,np.zeros(4))
            self.neutral=EquilibriumChargeDevice(reference,max_poles=self.max_poles).solve(
                np.zeros(len(reference.sites)),[.9]*4,300,tolerance=1e-7).electrons_per_site.copy()
        self._budget()
        system,mesh,mapping=geometry_fixture(self.device,voltage)
        if len(system.sites) != len(self.neutral):
            raise ValueError('Geometry site count changed during evaluation')
        provider=BiasChargeDevice(system,reference_mu_ev=.9,lead_shifts_ev=voltage,max_poles=self.max_poles)
        owner=self
        class Counted:
            def solve(self,*args,**kwargs):
                owner._budget()
                if owner.charge_calls >= owner.max_charge_calls:
                    raise RuntimeError('Geometry feedback charge budget exhausted')
                owner.charge_calls += 1
                return provider.solve(*args,**kwargs)
        result=solve_accelerated(mesh,mapping,Counted(),self.neutral,.9+voltage,300,
                                 tolerance=1e-6,method='broyden1')
        if self.record is not None:
            self.record(voltage.copy(),result)
        return result

    def currents(self, voltage):
        return self.bridge.currents(voltage)
