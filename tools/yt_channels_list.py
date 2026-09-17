#!/usr/bin/env python3
"""Lista configurada de canales de competencia e inspiración."""
from lib import base  # noqa: F401
from lib import yt_data
from lib.contrato import SOURCE_CONFIG, emitir, main, parser, sobre

TOOL = "yt_channels_list"


def run():
    p = parser(__doc__)
    p.add_argument("--list", dest="lista",
                   help="nombre de una lista de config/channels_lists.json "
                        "(competencia, inspiracion, vecindario...)")
    args = p.parse_args()

    datos = yt_data.cargar_canales(args.lista)
    env = sobre(TOOL, SOURCE_CONFIG, datos, {"list": args.lista or "todas"})
    emitir(env, args, lambda e: base.cabecera_md(e) + "\n" + base.tabla_md(
        e["data"], ["list_type", "name", "channel_id", "notes"]))


if __name__ == "__main__":
    main(TOOL, run)
