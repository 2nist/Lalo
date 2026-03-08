# Inbox

## Pending requests (machine-c diagnostics)

- Need final payload confirm: Where can I find the Harmonix `data/raw/harmonix` annotations (or should I run `scripts/datasets/fetch_harmonix.py` locally) so the benchmark can execute and write `results/sections-machine-c.json`?
- The payload references `third_party/BTC-ISMIR19/test/example.mp3`; there is no `third_party/` tree in this checkout. Should I update the payload to point to another audio path/dataset, or will that folder be added before the diagnostic run?
- The instruction file mentions `python tmp/validate_pipeline.py` but the `tmp/validate_pipeline.py` script is absent. Can you confirm whether there is an alternative validation command or where the missing script lives?
- Machine C instructions also expect me to commit/push the artifact. Should I wait for the missing data/script before rerunning those commands, or do you want to coordinate another action first?
