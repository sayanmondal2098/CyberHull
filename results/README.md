# Results

- `reference/`: original upstream figures, interactive HTML visualization, and vault
  mapping CSV files. These are tracked in Git.
- `runs/`: local CLI models, evaluation metrics, and predictions. These are ignored
  by Git and can be regenerated using the commands in `IMPLEMENTATION.md`.
- `generated/`: new notebook outputs, ignored by Git. Notebooks create this folder
  automatically so reruns do not overwrite the upstream reference figures.
