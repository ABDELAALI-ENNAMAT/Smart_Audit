"""
Inline SVG icon utilities for Streamlit dashboards.

Provides Lucide-based SVG icons as inline HTML strings for use with
``st.markdown(..., unsafe_allow_html=True)``.

Functions
---------
icon(name, size, color, class_name)
    Return a complete inline ``<svg>`` element for the requested icon.
status_dot(color, label)
    Return a coloured status-indicator badge.
inline_icon(name, size, color)
    Convenience wrapper that places the SVG inside a ``<span>`` suitable
    for embedding directly in markdown text.
"""

from __future__ import annotations

# ---------------------------------------------------------------------------
# Icon path data – Lucide icon set (https://lucide.dev)
# viewBox="0 0 24 24", stroke-based, stroke-width=2,
# stroke-linecap=round, stroke-linejoin=round, fill=none
# ---------------------------------------------------------------------------

ICONS: dict[str, str] = {
    "factory": (
        '<path d="M2 20a2 2 0 0 0 2 2h16a2 2 0 0 0 2-2V8l-7 5V8l-7 5V4'
        'a2 2 0 0 0-2-2H4a2 2 0 0 0-2 2Z"/>'
        '<path d="M17 18h1"/><path d="M12 18h1"/><path d="M7 18h1"/>'
    ),
    "settings": (
        '<path d="M12.22 2h-.44a2 2 0 0 0-2 2v.18a2 2 0 0 1-1 1.73l-.43.25a2 2 0 0 1-2 0l-.15-.08'
        'a2 2 0 0 0-2.73.73l-.22.38a2 2 0 0 0 .73 2.73l.15.1a2 2 0 0 1 1 1.72v.51a2 2 0 0 1-1 1.74'
        'l-.15.09a2 2 0 0 0-.73 2.73l.22.38a2 2 0 0 0 2.73.73l.15-.08a2 2 0 0 1 2 0l.43.25a2 2 0 0 1'
        ' 1 1.73V20a2 2 0 0 0 2 2h.44a2 2 0 0 0 2-2v-.18a2 2 0 0 1 1-1.73l.43-.25a2 2 0 0 1 2 0l.15.08'
        'a2 2 0 0 0 2.73-.73l.22-.39a2 2 0 0 0-.73-2.73l-.15-.08a2 2 0 0 1-1-1.74v-.5a2 2 0 0 1 1-1.74'
        'l.15-.09a2 2 0 0 0 .73-2.73l-.22-.38a2 2 0 0 0-2.73-.73l-.15.08a2 2 0 0 1-2 0l-.43-.25'
        'a2 2 0 0 1-1-1.73V4a2 2 0 0 0-2-2z"/>'
        '<circle cx="12" cy="12" r="3"/>'
    ),
    "bar_chart_3": (
        '<path d="M3 3v18h18"/><path d="M18 17V9"/>'
        '<path d="M13 17V5"/><path d="M8 17v-3"/>'
    ),
    "coins": (
        '<circle cx="8" cy="8" r="6"/>'
        '<path d="M18.09 10.37A6 6 0 1 1 10.34 18"/>'
        '<path d="M7 6h1v4"/>'
        '<path d="m16.71 13.88.7.71-2.82 2.82"/>'
    ),
    "alert_triangle": (
        '<path d="m21.73 18-8-14a2 2 0 0 0-3.48 0l-8 14A2 2 0 0 0 4 21h16'
        'a2 2 0 0 0 1.73-3Z"/>'
        '<path d="M12 9v4"/><path d="M12 17h.01"/>'
    ),
    "check_circle": (
        '<path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"/>'
        '<path d="m9 11 3 3L22 4"/>'
    ),
    "trending_up": (
        '<polyline points="22 7 13.5 15.5 8.5 10.5 2 17"/>'
        '<polyline points="16 7 22 7 22 13"/>'
    ),
    "trending_down": (
        '<polyline points="22 17 13.5 8.5 8.5 13.5 2 7"/>'
        '<polyline points="16 17 22 17 22 11"/>'
    ),
    "calendar": (
        '<path d="M8 2v4"/><path d="M16 2v4"/>'
        '<rect width="18" height="18" x="3" y="4" rx="2"/>'
        '<path d="M3 10h18"/>'
    ),
    "clipboard_list": (
        '<rect width="8" height="4" x="8" y="2" rx="1" ry="1"/>'
        '<path d="M16 4h2a2 2 0 0 1 2 2v14a2 2 0 0 1-2 2H6a2 2 0 0 1-2-2V6'
        'a2 2 0 0 1 2-2h2"/>'
        '<path d="M12 11h4"/><path d="M12 16h4"/>'
        '<path d="M8 11h.01"/><path d="M8 16h.01"/>'
    ),
    "ruler": (
        '<path d="M21.3 15.3a2.4 2.4 0 0 1 0 3.4l-2.6 2.6a2.4 2.4 0 0 1-3.4 0'
        'L2.7 8.7a2.41 2.41 0 0 1 0-3.4l2.6-2.6a2.41 2.41 0 0 1 3.4 0Z"/>'
        '<path d="m14.5 12.5 2-2"/><path d="m11.5 9.5 2-2"/>'
        '<path d="m8.5 6.5 2-2"/><path d="m17.5 15.5 2-2"/>'
    ),
    "search": (
        '<circle cx="11" cy="11" r="8"/>'
        '<path d="m21 21-4.3-4.3"/>'
    ),
    "zap": (
        '<path d="M4 14a1 1 0 0 1-.78-1.63l9.9-10.2a.5.5 0 0 1 .86.46l-1.92 6.02'
        'A1 1 0 0 0 13 10h7a1 1 0 0 1 .78 1.63l-9.9 10.2a.5.5 0 0 1-.86-.46'
        'l1.92-6.02A1 1 0 0 0 11 14z"/>'
    ),
    "file_text": (
        '<path d="M15 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V7Z"/>'
        '<path d="M14 2v4a2 2 0 0 0 2 2h4"/>'
        '<path d="M10 9H8"/><path d="M16 13H8"/><path d="M16 17H8"/>'
    ),
    "info": (
        '<circle cx="12" cy="12" r="10"/>'
        '<path d="M12 16v-4"/><path d="M12 8h.01"/>'
    ),
    "brain": (
        '<path d="M12 5a3 3 0 1 0-5.997.125 4 4 0 0 0-2.526 5.77 4 4 0 0 0 .556 6.588'
        'A4 4 0 1 0 12 18Z"/>'
        '<path d="M12 5a3 3 0 1 1 5.997.125 4 4 0 0 1 2.526 5.77 4 4 0 0 1-.556 6.588'
        'A4 4 0 1 1 12 18Z"/>'
        '<path d="M15 13a4.5 4.5 0 0 1-3-4 4.5 4.5 0 0 1-3 4"/>'
        '<path d="M12 18v-5.5a.5.5 0 0 0-1 0v5.5a.5.5 0 0 0 1 0Z"/>'
    ),
    "wrench": (
        '<path d="M14.7 6.3a1 1 0 0 0 0 1.4l1.6 1.6a1 1 0 0 0 1.4 0l3.77-3.77'
        'a6 6 0 0 1-7.94 7.94l-6.91 6.91a2.12 2.12 0 0 1-3-3l6.91-6.91'
        'a6 6 0 0 1 7.94-7.94l-3.76 3.76z"/>'
    ),
    "play": '<polygon points="6 3 20 12 6 21 6 3"/>',
    "refresh_cw": (
        '<path d="M3 12a9 9 0 0 1 9-9 9.75 9.75 0 0 1 6.74 2.74L21 8"/>'
        '<path d="M21 3v5h-5"/>'
        '<path d="M21 12a9 9 0 0 1-9 9 9.75 9.75 0 0 1-6.74-2.74L3 16"/>'
        '<path d="M8 16H3v5"/>'
    ),
    "book_open": (
        '<path d="M2 3h6a4 4 0 0 1 4 4v14a3 3 0 0 0-3-3H2z"/>'
        '<path d="M22 3h-6a4 4 0 0 0-4 4v14a3 3 0 0 1 3-3h7z"/>'
    ),
    "target": (
        '<circle cx="12" cy="12" r="10"/>'
        '<circle cx="12" cy="12" r="6"/>'
        '<circle cx="12" cy="12" r="2"/>'
    ),
    "sliders_horizontal": (
        '<line x1="21" x2="14" y1="4" y2="4"/>'
        '<line x1="10" x2="3" y1="4" y2="4"/>'
        '<line x1="21" x2="12" y1="12" y2="12"/>'
        '<line x1="8" x2="3" y1="12" y2="12"/>'
        '<line x1="21" x2="16" y1="20" y2="20"/>'
        '<line x1="12" x2="3" y1="20" y2="20"/>'
        '<line x1="14" x2="14" y1="2" y2="6"/>'
        '<line x1="8" x2="8" y1="10" y2="14"/>'
        '<line x1="16" x2="16" y1="18" y2="22"/>'
    ),
    "bug": (
        '<path d="m8 2 1.88 1.88"/><path d="M14.12 3.88 16 2"/>'
        '<path d="M9 7.13v-1a3.003 3.003 0 1 1 6 0v1"/>'
        '<path d="M12 20c-3.3 0-6-2.7-6-6v-3a4 4 0 0 1 4-4h4a4 4 0 0 1 4 4v3'
        'c0 3.3-2.7 6-6 6"/>'
        '<path d="M12 20v-9"/>'
        '<path d="M6.53 9C4.6 8.8 3 7.1 3 5"/>'
        '<path d="M6 13H2"/>'
        '<path d="M3 21c0-2.1 1.7-3.9 3.8-4"/>'
        '<path d="M20.97 5c0 2.1-1.6 3.8-3.5 4"/>'
        '<path d="M22 13h-4"/>'
        '<path d="M17.2 17c2.1.1 3.8 1.9 3.8 4"/>'
    ),
    "clock": (
        '<circle cx="12" cy="12" r="10"/>'
        '<polyline points="12 6 12 12 16 14"/>'
    ),
    "users": (
        '<path d="M16 21v-2a4 4 0 0 0-4-4H6a4 4 0 0 0-4 4v2"/>'
        '<circle cx="9" cy="7" r="4"/>'
        '<path d="M22 21v-2a4 4 0 0 0-3-3.87"/>'
        '<path d="M16 3.13a4 4 0 0 1 0 7.75"/>'
    ),
    "calculator": (
        '<rect width="16" height="20" x="4" y="2" rx="2"/>'
        '<line x1="8" x2="16" y1="6" y2="6"/>'
        '<line x1="16" x2="16" y1="14" y2="18"/>'
        '<path d="M16 10h.01"/><path d="M12 10h.01"/><path d="M8 10h.01"/>'
        '<path d="M12 14h.01"/><path d="M8 14h.01"/>'
        '<path d="M12 18h.01"/><path d="M8 18h.01"/>'
    ),
    "user": (
        '<path d="M19 21v-2a4 4 0 0 0-4-4H9a4 4 0 0 0-4 4v2"/>'
        '<circle cx="12" cy="7" r="4"/>'
    ),
    "pin": (
        '<path d="M12 17v5"/>'
        '<path d="M9 10.76a2 2 0 0 1-1.11 1.79l-1.78.9A2 2 0 0 0 5 15.24V16'
        'a1 1 0 0 0 1 1h12a1 1 0 0 0 1-1v-.76a2 2 0 0 0-1.11-1.79l-1.78-.9'
        'A2 2 0 0 1 15 10.76V7a1 1 0 0 1 1-1 2 2 0 0 0 0-4H8a2 2 0 0 0 0 4'
        ' 1 1 0 0 1 1 1z"/>'
    ),
    "lightbulb": (
        '<path d="M15 14c.2-1 .7-1.7 1.5-2.5 1-.9 1.5-2.2 1.5-3.5A6 6 0 0 0 6 8'
        'c0 1 .2 2.2 1.5 3.5.7.7 1.3 1.5 1.5 2.5"/>'
        '<path d="M9 18h6"/><path d="M10 22h4"/>'
    ),
    "microscope": (
        '<path d="M6 18h8"/><path d="M3 22h18"/>'
        '<path d="M14 22a7 7 0 1 0 0-14h-1"/>'
        '<path d="M9 14h2"/>'
        '<path d="M9 12a2 2 0 0 1-2-2V6h6v4a2 2 0 0 1-2 2Z"/>'
        '<path d="M12 6V3a1 1 0 0 0-1-1H9a1 1 0 0 0-1 1v3"/>'
    ),
    "download": (
        '<path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/>'
        '<polyline points="7 10 12 15 17 10"/>'
        '<line x1="12" x2="12" y1="15" y2="3"/>'
    ),
    "activity": (
        '<path d="M22 12h-2.48a2 2 0 0 0-1.93 1.46l-2.35 8.36a.25.25 0 0 1-.48 0'
        'L9.24 2.18a.25.25 0 0 0-.48 0l-2.35 8.36A2 2 0 0 1 4.49 12H2"/>'
    ),
    "gauge": (
        '<path d="m12 14 4-4"/>'
        '<path d="M3.34 19a10 10 0 1 1 17.32 0"/>'
    ),
    "layout_dashboard": (
        '<rect width="7" height="9" x="3" y="3" rx="1"/>'
        '<rect width="7" height="5" x="14" y="3" rx="1"/>'
        '<rect width="7" height="9" x="14" y="12" rx="1"/>'
        '<rect width="7" height="5" x="3" y="16" rx="1"/>'
    ),
    "shield": (
        '<path d="M20 13c0 5-3.5 7.5-7.66 8.95a1 1 0 0 1-.67-.01C7.5 20.5 4 18 4 13V6'
        'a1 1 0 0 1 1-1c2 0 4.5-1.2 6.24-2.72a1.17 1.17 0 0 1 1.52 0'
        'C14.51 3.81 17 5 19 5a1 1 0 0 1 1 1z"/>'
    ),
    "circle_dot": (
        '<circle cx="12" cy="12" r="10"/>'
        '<circle cx="12" cy="12" r="1"/>'
    ),
}


# ---------------------------------------------------------------------------
# Public helpers
# ---------------------------------------------------------------------------

def icon(
    name: str,
    size: int = 20,
    color: str = "currentColor",
    class_name: str = "",
) -> str:
    """Return an inline ``<svg>`` HTML string for the requested Lucide icon.

    Parameters
    ----------
    name:
        Key in :data:`ICONS`.  Returns an empty string when *name* is not
        found.
    size:
        Width **and** height of the rendered SVG (pixels).
    color:
        Stroke colour applied to every path inside the icon.
    class_name:
        Optional CSS class(es) added to the ``<svg>`` element.

    Returns
    -------
    str
        A self-contained ``<svg>`` element ready for
        ``st.markdown(..., unsafe_allow_html=True)``.
    """
    path_data = ICONS.get(name)
    if path_data is None:
        return ""

    cls_attr = f' class="{class_name}"' if class_name else ""
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" '
        f'width="{size}" height="{size}" '
        f'viewBox="0 0 24 24" '
        f'fill="none" stroke="{color}" '
        f'stroke-width="2" stroke-linecap="round" stroke-linejoin="round"'
        f'{cls_attr} '
        f'style="display:inline-block; vertical-align:middle;">'
        f"{path_data}</svg>"
    )


def status_dot(color: str, label: str) -> str:
    """Return a coloured status-indicator badge as an HTML snippet.

    Renders as a small pill with a filled circle and a text label, tinted
    to match *color*.

    Parameters
    ----------
    color:
        Any valid CSS colour value (hex, rgb, named, etc.).
    label:
        Short text displayed next to the dot.
    """
    return (
        f'<span style="display:inline-flex; align-items:center; gap:6px; '
        f"padding:3px 10px; border-radius:20px; font-size:11px; font-weight:600; "
        f'background:{color}15; color:{color};">'
        f'<span style="width:6px; height:6px; border-radius:50%; '
        f'background:{color};"></span>'
        f"{label}</span>"
    )


def inline_icon(
    name: str,
    size: int = 16,
    color: str = "currentColor",
) -> str:
    """Wrap an icon in a ``<span>`` for seamless use inside markdown text.

    This is a thin convenience wrapper around :func:`icon` that produces a
    ``<span>`` element with sensible inline styling so the icon sits
    naturally alongside text rendered via ``st.markdown``.

    Parameters
    ----------
    name:
        Key in :data:`ICONS`.
    size:
        Icon size in pixels (default ``16`` – slightly smaller than body
        text to blend nicely).
    color:
        Stroke colour.

    Returns
    -------
    str
        An HTML ``<span>`` containing the SVG, or an empty string when
        *name* is not found in :data:`ICONS`.
    """
    svg = icon(name, size=size, color=color)
    if not svg:
        return ""
    return (
        f'<span style="display:inline-flex; align-items:center; '
        f'vertical-align:middle; margin:0 2px;">{svg}</span>'
    )
