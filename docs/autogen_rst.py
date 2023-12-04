import logging
import os
import shutil
from pathlib import Path

log = logging.getLogger(os.path.basename(__file__))


def module_template(module_qualname: str):
    module_name = module_qualname.split(".")[-1]
    title = module_name.replace("_", r"\_")
    return f"""{title}
{"=" * len(title)}

.. automodule:: {module_qualname}
   :members:
   :undoc-members:
"""


def index_template(package_name: str, doc_references: list[str] | None = None):
    doc_references = doc_references or ""
    if doc_references:
        doc_references = "\n" + "\n".join(f"* :doc:`{ref}`" for ref in doc_references) + "\n"

    dirname = package_name.split(".")[-1]
    title = dirname.replace("_", r"\_")
    if title == "tianshou":
        title = "Tianshou API Reference"
    return f"{title}\n{'=' * len(title)}" + doc_references


def write_to_file(content: str, path: str):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w") as f:
        f.write(content)
    os.chmod(path, 0o666)


def make_rst(src_root, rst_root, clean=False, overwrite=False, package_prefix=""):
    """Creates/updates documentation in form of rst files for modules and packages.
    Does not delete any existing rst files. Thus, rst files for packages or modules that have been removed or renamed
    should be deleted by hand.

    This method should be executed from the project's top-level directory

    :param src_root: path to library base directory, typically "src/<library_name>"
    :param clean: whether to completely clean the target directory beforehand, removing any existing .rst files
    :param overwrite: whether to overwrite existing rst files. This should be used with caution as it will delete
        all manual changes to documentation files
    :package_prefix: a prefix to prepend to each module (for the case where the src_root is not the base package),
        which, if not empty, should end with a "."
    :return:
    """
    rst_root = os.path.abspath(rst_root)

    if clean and os.path.isdir(rst_root):
        shutil.rmtree(rst_root)

    base_package_name = package_prefix + os.path.basename(src_root)
    write_to_file(index_template(base_package_name), os.path.join(rst_root, "index.rst"))

    for root, dirnames, filenames in os.walk(src_root):
        if os.path.basename(root).startswith("_"):
            continue
        base_package_relpath = os.path.relpath(root, start=src_root)
        base_package_qualname = package_prefix + os.path.relpath(
            root,
            start=os.path.dirname(src_root),
        ).replace(os.path.sep, ".")

        for dirname in dirnames:
            if dirname.startswith("_"):
                log.debug(f"Skipping {dirname}")
                continue
            files_in_dir = os.listdir(os.path.join(root, dirname))
            module_names = [
                f[:-3] for f in files_in_dir if f.endswith(".py") and not f.startswith("_")
            ]
            subdir_refs = [
                os.path.join(f, "index")
                for f in files_in_dir
                if os.path.isdir(os.path.join(root, dirname, f)) and not f.startswith("_")
            ]
            if not module_names:
                log.debug(f"Skipping {dirname} as it does not contain any .py files")
                continue
            package_qualname = f"{base_package_qualname}.{dirname}"
            package_index_rst_path = os.path.join(
                rst_root,
                base_package_relpath,
                dirname,
                "index.rst",
            )
            log.info(f"Writing {package_index_rst_path}")
            write_to_file(
                index_template(package_qualname, doc_references=module_names + subdir_refs),
                package_index_rst_path,
            )

        for filename in filenames:
            base_name, ext = os.path.splitext(filename)
            if ext == ".py" and not filename.startswith("_"):
                module_qualname = f"{base_package_qualname}.{filename[:-3]}"

                module_rst_path = os.path.join(rst_root, base_package_relpath, f"{base_name}.rst")
                if os.path.exists(module_rst_path) and not overwrite:
                    log.debug(f"{module_rst_path} already exists, skipping it")

                log.info(f"Writing module documentation to {module_rst_path}")
                write_to_file(module_template(module_qualname), module_rst_path)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    docs_root = Path(__file__).parent
    make_rst(
        docs_root / ".." / "tianshou",
        docs_root / "api",
        clean=True,
    )
