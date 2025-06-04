"""Allow airun to be executable as a module with python -m airun."""

from .cli import main

if __name__ == "__main__":
    main()