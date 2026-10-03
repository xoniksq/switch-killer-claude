import sys

def main():
    if "--cli" in sys.argv:
        from app_cli import run_cli
        run_cli()
    else:
        try:
            from app_gui import run_gui
            run_gui()
        except ImportError as e:
            print(f"GUI dependencies not found ({e}), falling back to CLI mode...")
            from app_cli import run_cli
            run_cli()

if __name__ == "__main__":
    main()
