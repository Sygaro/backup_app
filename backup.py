#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Fleksibel backup-CLI for prosjekter på RPi/Unix.
- SOURCE tolkes fra HOME når du gir relativ sti (f.eks. -s countdown -> ~/countdown)
- DEST tolkes fra HOME når du gir relativ sti (default: ~/backups)
- Lager ZIP (eller tar.gz) av en valgt kildekatalog
- Navngir arkivet med prosjekt, versjon (valgfritt), dato og tag (valgfritt)
- Støtter .backupignore + --exclude mønstre
- Retention: behold kun N siste arkiver for prosjektet
- Valgfri Dropbox-opplasting (DROPBOX_TOKEN)
"""

import argparse
import os
import sys
import fnmatch
import logging
from datetime import datetime
from pathlib import Path
from typing import Iterable, List, Optional, Set

try:
    from dotenv import load_dotenv  # type: ignore
except Exception:
    load_dotenv = None

def _lazy_import_dropbox():
    import uploader_dropbox  # noqa: F401
    return uploader_dropbox

LOG = logging.getLogger("backup")

DEFAULT_DEST = str(Path.home() / "backups")
IGNORE_FILE = ".backupignore"

EXCLUDE_DIRNAMES: Set[str] = {"venv", ".venv", ".git", "node_modules", "__pycache__", "dist", "build", "backups"}
EXCLUDE_FILEPATTERNS: List[str] = ["*.pyc", "*.pyo", "*.log", "*.tmp"]

def setup_logging(verbose: bool):
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(level=level, format="%(asctime)s %(levelname)s %(message)s", datefmt="%H:%M:%S")

def read_ignore_file(src: Path) -> List[str]:
    patterns: List[str] = []
    f = src / IGNORE_FILE
    if f.exists():
        for line in f.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            patterns.append(line)
    return patterns

def matched_any(path_rel: str, patterns: Iterable[str]) -> bool:
    for p in patterns:
        if fnmatch.fnmatch(path_rel, p):
            return True
    return False

def iter_files(src: Path, exclude_patterns: Iterable[str], include_hidden: bool) -> Iterable[Path]:
    for p in src.rglob("*"):
        if p.is_dir():
            continue
        rel_path = p.relative_to(src)
        rel_posix = rel_path.as_posix()
        if not include_hidden and any(part.startswith(".") for part in rel_path.parts):
            continue
        if any(part in EXCLUDE_DIRNAMES for part in rel_path.parts):
            continue
        if matched_any(rel_posix, EXCLUDE_FILEPATTERNS):
            continue
        if matched_any(rel_posix, exclude_patterns):
            continue
        yield p

def make_archive(src: Path, dest_dir: Path, project: str, version: Optional[str], tag: Optional[str],
                 fmt: str, exclude_patterns: Iterable[str], include_hidden: bool, dry_run: bool) -> Path:
    dest_dir.mkdir(parents=True, exist_ok=True)
    dt = datetime.now().strftime("%Y%m%d-%H%M")
    parts = [project]
    if version:
        parts.append(f"v{version}")
    parts.append(dt)
    if tag:
        parts.append(tag)
    base = "_".join(parts)
    if fmt == "zip":
        out = dest_dir / f"{base}.zip"
    elif fmt in ("tar.gz", "tgz"):
        out = dest_dir / f"{base}.tar.gz"
    else:
        raise SystemExit(f"Ukjent format: {fmt}")
    LOG.info("Lager arkiv: %s", out)
    if dry_run:
        return out
    if fmt == "zip":
        import zipfile
        with zipfile.ZipFile(out, "w", compression=zipfile.ZIP_DEFLATED) as zf:
            for f in iter_files(src, exclude_patterns, include_hidden):
                zf.write(f, f.relative_to(src).as_posix())
    else:
        import tarfile
        with tarfile.open(out, "w:gz") as tf:
            for f in iter_files(src, exclude_patterns, include_hidden):
                tf.add(f, f.relative_to(src).as_posix())
    return out

def verify_archive(archive_path: Path) -> None:
    if archive_path.suffix == ".zip":
        import zipfile
        with zipfile.ZipFile(archive_path, "r") as zf:
            _ = zf.namelist()
    elif archive_path.suffixes[-2:] == [".tar", ".gz"] or archive_path.suffix == ".tgz":
        import tarfile
        with tarfile.open(archive_path, "r:gz") as tf:
            _ = tf.getmembers()
    else:
        LOG.warning("Ukjent arkivtype for verifisering: %s", archive_path)

def apply_retention(dest_dir: Path, project: str, keep: int) -> None:
    if keep <= 0:
        return
    candidates: List[Path] = sorted(
        [p for p in dest_dir.glob(f"{project}_*") if p.is_file()],
        key=lambda p: p.stat().st_mtime,
        reverse=True
    )
    to_delete = candidates[keep:]
    for p in to_delete:
        try:
            LOG.info("Sletter pga retention: %s", p)
            p.unlink(missing_ok=True)
        except Exception as e:
            LOG.warning("Klarte ikke slette %s: %s", p, e)

def create_latest_symlink(dest_dir: Path, archive_path: Path, project: str) -> None:
    link = dest_dir / f"{project}_latest"
    if link.exists() or link.is_symlink():
        try:
            link.unlink()
        except Exception:
            pass
    try:
        link.symlink_to(archive_path.name)
    except Exception as e:
        LOG.debug("Kunne ikke lage symlink (OK på f.eks. FAT/Dropbox): %s", e)

def parse_args(argv: Optional[List[str]] = None) -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Fleksibel prosjekt-backup med valgfri Dropbox-opplasting.")
    p.add_argument("--project", "-p", help="Prosjektnavn (default: navn på kildemappe)")
    p.add_argument("--source", "-s", required=True, help="Kildemappe (relativ = fra HOME)")
    p.add_argument("--dest", "-d", default=os.getenv("BACKUP_DEFAULT_DEST", DEFAULT_DEST),
                   help=f"Målmappe (relativ = fra HOME) (default: {DEFAULT_DEST})")
    p.add_argument("--version", "-V", help="Versjonsnummer, f.eks. 1.06 (valgfritt)")  # <- endret til -V
    p.add_argument("--no-version", action="store_true", help="Tving uten versjon i filnavn")
    p.add_argument("--tag", "-t", help="Ekstra tag i filnavn, f.eks. Frontend_OK")
    p.add_argument("--format", choices=["zip", "tar.gz", "tgz"], default="zip", help="Arkivformat (default: zip)")
    p.add_argument("--include-hidden", action="store_true", help="Ta med skjulte filer/mapper")
    p.add_argument("--exclude", action="append", default=[], help="Glob-mønster for ekskludering (kan gjentas). Eksempel: --exclude '.env'")
    p.add_argument("--dropbox-path", help="Sti i Dropbox for opplasting (valgfritt)")
    p.add_argument("--dropbox-mode", choices=["add", "overwrite"], default="add", help="Dropbox skrivemodus (default: add)")
    p.add_argument("--keep", type=int, default=0, help="Behold kun N siste arkiver for dette prosjektet (0=av)")
    p.add_argument("--dry-run", action="store_true", help="Vis hva som ville skjedd, uten å skrive filer")
    p.add_argument("--no-verify", action="store_true", help="Ikke verifiser arkivet etter skriving")
    p.add_argument("--verbose", "-v", action="store_true", help="Mer logging")  # <- nytt kortflagg -v
    return p.parse_args(argv)

def resolve_from_home(path_arg: str) -> Path:
    p = Path(path_arg).expanduser()
    if p.is_absolute():
        return p.resolve()
    return (Path.home() / p).resolve()

def main(argv: Optional[List[str]] = None) -> int:
    if load_dotenv:
        load_dotenv()
    args = parse_args(argv)
    setup_logging(args.verbose)

    src = resolve_from_home(args.source)
    if not src.exists() or not src.is_dir():
        LOG.error("Kildemappe finnes ikke: %s", src)
        return 2

    dest_dir = resolve_from_home(args.dest)
    project = args.project or src.name

    version = args.version
    if args.no_version:
        version = None

    exclude_patterns: List[str] = read_ignore_file(src)
    exclude_patterns.extend(args.exclude or [])

    LOG.info("Prosjekt: %s", project)
    LOG.info("Kilde:    %s", src)
    LOG.info("Mål:      %s", dest_dir)
    LOG.info("Format:   %s", args.format)
    LOG.info("Versjon:  %s", version if version else "(ingen)")
    if args.tag:
        LOG.info("Tag:      %s", args.tag)
    if exclude_patterns:
        LOG.info("Exclude:  %s", ", ".join(exclude_patterns))
    LOG.info("Hidden:   %s", "med" if args.include_hidden else "uten")
    LOG.info("Dry run:  %s", "ja" if args.dry_run else "nei")

    archive_path = make_archive(
        src=src,
        dest_dir=dest_dir,
        project=project,
        version=version,
        tag=args.tag,
        fmt=args.format,
        exclude_patterns=exclude_patterns,
        include_hidden=args.include_hidden,
        dry_run=args.dry_run,
    )

    if not args.dry_run:
        if not args.no_verify:
            LOG.info("Verifiserer arkiv...")
            verify_archive(archive_path)
        create_latest_symlink(dest_dir, archive_path, project)

    if args.keep and not args.dry_run:
        apply_retention(dest_dir, project, args.keep)

    if args.dropbox_path:
        token = os.getenv("DROPBOX_TOKEN")
        if not token:
            LOG.error("DROPBOX_TOKEN mangler i miljø/.env; hopper over opplasting.")
        else:
            _ = _lazy_import_dropbox()
            try:
                LOG.info("Laster opp til Dropbox: %s -> %s", archive_path.name, args.dropbox_path)
                if not args.dry_run:
                    _ .upload_to_dropbox(
                        local_path=archive_path,
                        dest_path=str(Path(args.dropbox_path) / archive_path.name),
                        token=token,
                        mode=args.dropbox_mode
                    )
            except Exception as e:
                LOG.error("Dropbox-opplasting feilet: %s", e)
                return 3

    LOG.info("Ferdig.")
    return 0

if __name__ == "__main__":
    sys.exit(main())