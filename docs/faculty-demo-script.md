# Three-minute faculty demonstration (in this order)

| # | Show | Say (about) |
|---|---|---|
| 1 | Repository URL and collaborator list | "Our repo; all members are collaborators." |
| 2 | `README.md` | State the one-sentence problem. |
| 3 | `docs/STEP-1.md` | Explain user, inputs, outputs, M1 (fuzzy) and M2 (GA). |
| 4 | `data/README.md` | Field meanings, units, source statement, assumptions. |
| 5 | `data/sample_input.csv` | Point to one normal (TRF-006), one boundary (TRF-012) and one difficult row (TRF-017). |
| 6 | Run `python src/validate_data.py` | Show PASS. |
| 7 | Run `python src/validate_data.py --file data/invalid_input.csv --expect-fail` | Explain the two expected errors. |
| 8 | `docs/baseline-pseudocode.md` | Explain rules and the expected result for one case, e.g. TRF-004. |
| 9 | `docs/product-v1-sketch.png` | Input, results, explanation, errors areas. |
| 10 | Git history | One meaningful commit from every member. |

## Rehearsal checklist
- [ ] Fresh clone in a new folder, new virtual environment, all commands work.
- [ ] Every member can explain three rows and the baseline in one sentence.
- [ ] Screenshots of one PASS and one EXPECTED FAIL are in `results/step1/`.
