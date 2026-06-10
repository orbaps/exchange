from enum import Enum

class RuntimeType(Enum):
    """Supported submission runtime environments.
    
    The challenge explicitly permits C++, Rust, and Go submissions.
    Build logic, compiler flags, and artifact paths differ per runtime.
    Never assume Python-only.
    """
    PYTHON = "python"
    CPP    = "cpp"
    GO     = "go"
    RUST   = "rust"

    @property
    def default_build_command(self) -> str:
        """Returns a canonical build command hint for this runtime."""
        return {
            RuntimeType.PYTHON: "pip install -r requirements.txt",
            RuntimeType.CPP:    "cmake --build . --config Release",
            RuntimeType.GO:     "go build -o engine .",
            RuntimeType.RUST:   "cargo build --release",
        }[self]

    @property
    def default_entrypoint(self) -> str:
        return {
            RuntimeType.PYTHON: "main.py",
            RuntimeType.CPP:    "./engine",
            RuntimeType.GO:     "./engine",
            RuntimeType.RUST:   "./target/release/engine",
        }[self]
