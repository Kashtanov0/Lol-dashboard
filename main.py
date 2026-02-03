from extract import run_extraction
from analysis import run_analysis
from export import run_export


def main():
    print()
    print("=" * 50)
    print("ETL PIPELINE")
    print("=" * 50)
    print()

    print("Step 1: Extract data from Riot API")
    print("-" * 50)
    run_extraction()
    print()

    print("Step 2: Analyze data and detect anomalies")
    print("-" * 50)
    run_analysis()
    print()

    print("Step 3: Export to CSV for Tableau")
    print("-" * 50)
    run_export()
    print()

    print("=" * 50)
    print("PIPELINE COMPLETE!")
    print("=" * 50)
    print()


if __name__ == "__main__":
    main()
