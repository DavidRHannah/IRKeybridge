import re
import statistics

def parse_tte_from_log(log_text: str):
    """
    Extracts all TTE values from the given log text.
    Returns a list of floats (seconds).
    """
    tte_pattern = re.compile(r"TTE:\s*([\d.eE+-]+)")
    return [float(match) for match in tte_pattern.findall(log_text)]

def profile_tte(tte_values, f):
    """
    Profiles the given list of TTE values and prints statistics.
    """
    if not tte_values:
        print("No TTE values found.", file=f)
        return
    
    stats = {
        "count": len(tte_values),
        "min": min(tte_values),
        "max": max(tte_values),
        "mean": statistics.mean(tte_values),
        "median": statistics.median(tte_values),
        "stdev": statistics.stdev(tte_values) if len(tte_values) > 1 else 0.0,
        "25th_percentile": statistics.quantiles(tte_values, n=4)[0],
        "75th_percentile": statistics.quantiles(tte_values, n=4)[-1],
    }

    print("\n=== TTE Profiling Report ===", file=f)
    for k, v in stats.items():
        print(f"{k:20}: {v:.6f} seconds", file=f)

if __name__ == "__main__":
    with open("raw_logs/tte6", "r") as input_file:
        log_text = input_file.read()
    
    with open("reports/tte6", "w") as output_file:
        tte_values = parse_tte_from_log(log_text)
        profile_tte(tte_values, output_file)
