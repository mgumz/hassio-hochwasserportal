"""The Länderübergreifendes Hochwasser Portal API - Utility functions."""

from __future__ import annotations
import requests
import bs4


def fetch_json(url, timeout=10):
    """Fetch data via json."""
    try:
        response = requests.get(url, timeout=timeout)
        response.raise_for_status()
        json_data = response.json()
        return json_data
    except:
        # Don't care about errors because in some cases the requested page doesn't exist
        return None


def fetch_soup(url, timeout=10, remove_xml=False):
    """Fetch data via soup."""
    try:
        response = requests.get(url, timeout=timeout)
        # Override encoding by real educated guess (required for SH)
        response.encoding = response.apparent_encoding
        response.raise_for_status()
        if remove_xml and (
            (response.text.find('<?xml version="1.0" encoding="ISO-8859-15" ?>')) == 0
        ):
            text = response.text[response.text.find("<!DOCTYPE html>") :]
            soup = bs4.BeautifulSoup(text, "lxml")
        else:
            soup = bs4.BeautifulSoup(response.text, "lxml")
        return soup
    except:
        # Don't care about errors because in some cases the requested page doesn't exist
        return None


def fetch_text(url, timeout=10, forced_encoding=None):
    """Fetch data via text."""
    try:
        response = requests.get(url, timeout=timeout)
        if forced_encoding is not None:
            response.encoding = forced_encoding
        else:
            # Override encoding by real educated guess (required for BW)
            response.encoding = response.apparent_encoding
        response.raise_for_status()
        return response.text
    except:
        # Don't care about errors because in some cases the requested page doesn't exist
        return None


def calc_stage(level, stage_levels):
    """Calc stage from level and stage levels."""
    if all(sl is None for sl in stage_levels):
        return None
    if (stage_levels[3] is not None) and (level > stage_levels[3]):
        return 4
    if (stage_levels[2] is not None) and (level > stage_levels[2]):
        return 3
    if (stage_levels[1] is not None) and (level > stage_levels[1]):
        return 2
    if (stage_levels[0] is not None) and (level > stage_levels[0]):
        return 1
    return 0