"""The Länderübergreifendes Hochwasser Portal API - Functions for Baden-Württemberg."""

from __future__ import annotations

from json import loads

from .api_utils import (
    DynamicData,
    LHPError,
    StaticData,
    calc_stage,
    convert_to_datetime,
    convert_to_float,
    fetch_text,
)


def init_BW(ident: str) -> StaticData:  # pylint: disable=invalid-name
    """Init data for Baden-Württemberg."""
    try:
        # Get data
        page = fetch_text("https://www.hvz.baden-wuerttemberg.de/js/hvz_peg_stmn.js")
        lines = page.split("\r\n")[6:-4]
        # Parse data
        for line in lines:
            # Building a valid json string
            content = line[line.find("[") : (line.find("]") + 1)]
            content = content.replace("'", '"')
            content = '{ "data":' + content + "}"
            data = loads(content)["data"]
            if data[0] == ident[3:]:
                name = data[1] + " / " + data[2]
                url = "https://hvz.baden-wuerttemberg.de/pegel.html?id=" + ident[3:]
                stage_levels = [None] * 4
                hmo_level = convert_to_float(data[24])
                if (hmo_level is not None) and (hmo_level > 0.0):
                    stage_levels[0] = round(hmo_level * 100.0, 0)
                stage_level = convert_to_float(data[30])
                if (stage_level is not None) and (stage_level > 0.0):
                    if (stage_levels[0] is None) or (stage_level < stage_levels[0]):
                        stage_levels[0] = stage_level
                stage_level = convert_to_float(data[31])
                if (stage_level is not None) and (stage_level > 0.0):
                    stage_levels[1] = stage_level
                stage_level = convert_to_float(data[32])
                if (stage_level is not None) and (stage_level > 0.0):
                    stage_levels[2] = stage_level
                stage_level = convert_to_float(data[33])
                if (stage_level is not None) and (stage_level > 0.0):
                    stage_levels[3] = stage_level
                return StaticData(
                    ident=ident, name=name, url=url, stage_levels=stage_levels
                )
        return StaticData(ident=ident)
    except Exception as err:
        raise LHPError(err, "bw_api.py: init_BW()") from err


def update_BW(static_data: StaticData) -> DynamicData:  # pylint: disable=invalid-name
    """Update data for Baden-Württemberg."""
    try:
        # Get data
        page = fetch_text("https://www.hvz.baden-wuerttemberg.de/js/hvz_peg_stmn.js")
        lines = page.split("\r\n")[6:-4]
        # Parse data
        level = None
        stage = None
        flow = None
        last_update = None
        for line in lines:
            # Building a valid json string
            content = line[line.find("[") : (line.find("]") + 1)]
            content = content.replace("'", '"')
            content = '{ "data":' + content + "}"
            data = loads(content)["data"]
            if data[0] == static_data.ident[3:]:
                if data[5] == "cm":
                    level = convert_to_float(data[4])
                    stage = calc_stage(level, static_data.stage_levels)
                    parts = data[6].split()
                    last_update = convert_to_datetime(
                        parts[0] + parts[1], "%d.%m.%Y%H:%M"
                    )
                if data[8] == "m³/s":
                    flow = convert_to_float(data[7])
                    if last_update is None:
                        parts = data[9].split()
                        last_update = convert_to_datetime(
                            parts[0] + parts[1], "%d.%m.%Y%H:%M"
                        )
                break
        return DynamicData(level=level, stage=stage, flow=flow, last_update=last_update)
    except Exception as err:
        raise LHPError(err, "bw_api.py: update_BW()") from err
