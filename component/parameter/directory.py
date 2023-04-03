from pathlib import Path

module_dir = Path.home() / "module_results"
module_dir.mkdir(exist_ok=True)

result_dir = module_dir / "clip_time_series"
result_dir.mkdir(exist_ok=True)

tmp_dir = result_dir / "tmp"
tmp_dir.mkdir(exist_ok=True)

sepal_down_dir = Path.home() / "downloads"

test_dataset = Path(__file__).parents[2] / "utils" / "clip_test_points.csv"
