# Performance Testing

## Run Tests

```bash
# Test current deployment
python3 performance_test.py
```

## Analyze Results

```bash
python3 analyze_results.py results/localstack/*.json results/aws/*.json
```

## Results

- LocalStack results: `results/localstack/`
- AWS results: `results/aws/`
- Charts: `../docs/charts/`
