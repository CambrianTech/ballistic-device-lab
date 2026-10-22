# Equilibrium electrical detector audit

| Design | Noise (nV/√Hz) | Weak-interval response (V/W) | Equilibrium NEP estimate (pW/√Hz) | Grid check |
| --- | ---: | ---: | ---: | --- |
| triangle-control | 8.398 | 785.9 | 10.686 | pass |
| D00 | 8.926 | 2066.3 | 4.320 | pass |
| diversity-r0-profile-g15-1 | 10.860 | 8762.3 | 1.239 | pass |

Fixed-potential 300 K electrical terminal model, 10 kΩ load, ideal voltage-clamped inputs. Response is the secant between 1 and 2 mV peak; 5 and 10 mV points are retained in JSON. Noise includes correlated device and load thermal noise. Grid check compares the saved full grid with every second energy point. This is not optical NEP or a validated finite-drive detector: excess/1/f/readout noise, bandwidth, electrostatic feedback and experimental reproduction remain absent. No search score is changed.
