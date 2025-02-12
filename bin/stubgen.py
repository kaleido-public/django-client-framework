#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import os
import re
import sys
from pathlib import Path

import django
from mypy.stubgen import main

if __name__ == "__main__":
    sys.path.append(str(Path("./dcf_dummy_proj").absolute()))
    sys.path.append(str(Path(".").absolute()))
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "dcf_dummy_proj.settings")
    django.setup()
    sys.argv[0] = re.sub(r"(-script\.pyw|\.exe)?$", "", sys.argv[0])
    sys.exit(main())
