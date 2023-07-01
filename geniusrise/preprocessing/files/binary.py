import os
from os.path import getmtime
from time import ctime
from typing import Any, Dict

from elftools.elf.elffile import ELFFile

from geniusrise.data_sources.files.base import TextExtractor


class ELFExtractor(TextExtractor):
    """Text extractor for ELF binaries."""

    def process(self, file_path: str, **kwargs) -> Dict[str, Any]:
        """Extract headers and section headers from an ELF binary."""
        with open(file_path, "rb") as file:
            elffile = ELFFile(file)

            headers = {
                "e_type": elffile.header.e_type,
                "e_entry": elffile.header.e_entry,
                "e_phoff": elffile.header.e_phoff,
                "e_shoff": elffile.header.e_shoff,
                "e_flags": elffile.header.e_flags,
                "e_ehsize": elffile.header.e_ehsize,
                "e_phentsize": elffile.header.e_phentsize,
                "e_phnum": elffile.header.e_phnum,
                "e_shentsize": elffile.header.e_shentsize,
                "e_shnum": elffile.header.e_shnum,
                "e_shstrndx": elffile.header.e_shstrndx,
            }

            section_headers = [
                {
                    "sh_name": section_header.sh_name,
                    "sh_type": section_header.sh_type,
                    "sh_flags": section_header.sh_flags,
                    "sh_addr": section_header.sh_addr,
                    "sh_offset": section_header.sh_offset,
                    "sh_size": section_header.sh_size,
                    "sh_link": section_header.sh_link,
                    "sh_info": section_header.sh_info,
                    "sh_addralign": section_header.sh_addralign,
                    "sh_entsize": section_header.sh_entsize,
                }
                for section_header in elffile.iter_sections()
            ]

            return {
                "binary_name": os.path.basename(file_path),
                "headers": headers,
                "section_headers": section_headers,
                "created_at": ctime(getmtime(file_path)),
            }
