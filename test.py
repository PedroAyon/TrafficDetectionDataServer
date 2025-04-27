from datetime import datetime
from repository import get_peak_hours

def main():
    # parse your exact start/end timestamps
    start = datetime.strptime("2025-03-29 00:25:33", "%Y-%m-%d %H:%M:%S")
    end   = datetime.strptime("2025-04-24 19:43:00", "%Y-%m-%d %H:%M:%S")

    peaks = get_peak_hours(start, end, cam_id=1)

    print(f"Peak hour(s) between {start} and {end}:")
    if not peaks:
        print("  → No records found in that range.")
    else:
        for entry in peaks:
            print(f"  • {entry['hour']} → {entry['vehicle_count']} vehicles")

if __name__ == "__main__":
    main()
