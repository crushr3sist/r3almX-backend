import toml
from semantic_version import Version


def get_current_version(file_path="pyproject.toml"):
    with open(file_path, "r") as f:
        data = toml.load(f)
    return data["tool"]["semantic-version"]["current_version"]


def update_version(new_version, file_path="pyproject.toml"):
    with open(file_path, "r") as f:
        data = toml.load(f)

    data["tool"]["semantic-version"]["current_version"] = str(new_version)

    with open(file_path, "w") as f:
        toml.dump(data, f)


def bump_version(bump_type="patch"):
    current_version = Version(get_current_version())

    if bump_type == "major":
        new_version = current_version.next_major()
    elif bump_type == "minor":
        new_version = current_version.next_minor()
    elif bump_type == "patch":
        new_version = current_version.next_patch()
    else:
        raise ValueError("Invalid bump type. Use 'major', 'minor', or 'patch'.")

    update_version(new_version)
    print(f"Version bumped to {new_version}")


# Example usage
bump_version("minor")
