import importlib
import sys

def verify_environment():
    packages = [
        ("xgboost", "xgboost"),
        ("lightgbm", "lightgbm"),
        ("scikit-learn", "sklearn"),
        ("geopandas", "geopandas"),
        ("rasterio", "rasterio"),
        ("pysheds", "pysheds"),
        ("networkx", "networkx"),
        ("pyswmm", "pyswmm"),
        ("fastapi", "fastapi"),
        ("uvicorn", "uvicorn"),
        ("shap", "shap"),
        ("folium", "folium"),
        ("leafmap", "leafmap"),
        ("twilio", "twilio"),
        ("pandas", "pandas"),
        ("numpy", "numpy"),
        ("matplotlib", "matplotlib"),
        ("scipy", "scipy"),
        ("psycopg2", "psycopg2"),
        ("sqlalchemy", "sqlalchemy"),
        ("redis", "redis"),
    ]

    print("=" * 65)
    print(f"Python Runtime: {sys.version.split()[0]} ({sys.platform})")
    print("=" * 65)
    print(f"| {'Package Name':<20} | {'Status':<10} | {'Version':<25} |")
    print("|" + "-"*22 + "|" + "-"*12 + "|" + "-"*27 + "|")

    passed = 0
    for display_name, import_name in packages:
        try:
            mod = importlib.import_module(import_name)
            version = getattr(mod, "__version__", "Installed")
            print(f"| {display_name:<20} | {'SUCCESS':<10} | {str(version):<25} |")
            passed += 1
        except Exception as e:
            print(f"| {display_name:<20} | {'FAILED':<10} | {str(e)[:25]:<25} |")

    print("-" * 65)
    print(f"Result: {passed}/{len(packages)} Core Data Science & Hydrology Packages Operational!")
    print("=" * 65)

if __name__ == "__main__":
    verify_environment()
