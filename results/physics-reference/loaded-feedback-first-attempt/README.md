# First loaded-feedback attempt: unresolved

The 10 mV, 10 kohm coupled pilot stopped after 36.48 seconds on its first
charge evaluation. No loaded solution was produced. The equilibrium Matsubara
sum reached its 32768-pole ceiling before two consecutive refinements satisfied
the requested tolerance. Last estimated change: 3.87796e-10 electrons/site.
The feedback target 1e-6 requests charge tolerance 1e-8 and an equilibrium
sub-budget of 2.5e-9; a last change below that threshold alone is insufficient
because two consecutive successful refinements are required.

[Failure receipt and source hashes](status.json). The attempt lock and local
logs are preserved. BiasChargeDevice now accepts an explicit max_poles budget
(default unchanged); a higher-budget retry is pending. This changes available
work, not the accuracy criterion, and does not establish physical validation.
