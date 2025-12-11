## Producer thôi mà phức tạp thế?

### How do I run?

```bash
uv run python kafka/producer.py --speedup 3600
```

### What does that script do?

It scans the parquet file and pushes (produces) data based on the `tpep_dropoff_datetime` because yeah a trip's data is only available after it ends, thank you Captain Obvious.

It supports adjustable speedup. A speedup of 3600.0 means 1s IRL = 3600s (1h) in simulation.

If a row has `store_and_fwd_flag` true, a random delay between 2m and 20m is added before push.