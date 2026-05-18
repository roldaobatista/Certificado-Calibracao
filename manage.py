#!/usr/bin/env python
"""Utilitario de linha de comando do Django."""

import os
import sys


def main() -> None:
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.dev")
    try:
        from django.core.management import execute_from_command_line
    except ImportError as exc:
        raise ImportError(
            "Django nao foi encontrado. Voce ativou o ambiente virtual? "
            "Rode 'poetry install' primeiro."
        ) from exc
    execute_from_command_line(sys.argv)


if __name__ == "__main__":
    main()
