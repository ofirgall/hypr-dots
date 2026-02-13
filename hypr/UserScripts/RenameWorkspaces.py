#!/usr/bin/env python3
"""
Rename virtual desktops based on TMUX client titles.
Finds clients with "- TMUX" suffix and renames the vdesk to the client name without the suffix.
Vdesks without TMUX clients are renamed to the title of a window on that desk (browsers prioritized).
Vdesks with no clients at all are renamed to their ID only.
"""

import json
import os
import re
import subprocess
import sys

from emojis import EMOJI_RE
from hypr_enums import AGENT_STATUS
from icons import TMUX_ICON, BROWSER_ICON, AGENT_STATUS_ICONS


CONFIG_LOC = os.path.expanduser("~/.config/hypr/UserConfigs/VirtualDesktopsNames.conf")
MAX_NAME_LENGTH = 20

def get_tmux_session_status(session_name: str) -> str:
    """Get the cursor-cli-wrapper-status for a tmux session."""
    try:
        result = subprocess.run(
            ["tmux", "show-options", "-t", session_name, "-v", "@cursor-cli-wrapper-status"],
            capture_output=True,
            text=True,
            timeout=2,
        )
        status = result.stdout.strip()
        return AGENT_STATUS_ICONS.get(status, "")
    except (subprocess.TimeoutExpired, Exception):
        return ""


def clean_title(title: str) -> str:
    """Remove emojis, collapse whitespace, and strip leading/trailing spaces."""
    title = EMOJI_RE.sub("", title)
    title = re.sub(r"\s+", " ", title)
    return title.strip()


def run_hyprctl(args: list[str]) -> str:
    """Run hyprctl command and return output."""
    result = subprocess.run(
        ["hyprctl"] + args,
        capture_output=True,
        text=True
    )
    return result.stdout


def get_vdesks() -> list[dict]:
    """Get all virtual desktops from hyprctl printstate."""
    output = run_hyprctl(["printstate", "-j"])
    try:
        return json.loads(output)
    except json.JSONDecodeError:
        print(f"Error parsing vdesks JSON: {output}", file=sys.stderr)
        return []


def get_clients() -> list[dict]:
    """Get all clients from hyprctl clients."""
    output = run_hyprctl(["clients", "-j"])
    try:
        return json.loads(output)
    except json.JSONDecodeError:
        print(f"Error parsing clients JSON: {output}", file=sys.stderr)
        return []


def write_names(names: dict[int, str]) -> None:
    """Write vdesk names to config file if changed."""
    # Build the names string: "1:name1, 2:name2, ..."
    names_str = ", ".join(f"{id}:{name}" for id, name in sorted(names.items()))
    
    content = f"""plugin {{
    virtual-desktops {{
        names = {names_str}
    }}
}}
"""
    # Read current content and compare
    try:
        with open(CONFIG_LOC, "r") as f:
            if f.read() == content:
                return
    except FileNotFoundError:
        pass
    
    with open(CONFIG_LOC, "w") as f:
        f.write(content)
    
    # Reload workspace names
    subprocess.run(["hyprctl", "dispatch", "vdeskreset"], capture_output=True)


def main():
    vdesks = get_vdesks()
    clients = get_clients()

    if not vdesks:
        print("No virtual desktops found", file=sys.stderr)
        return

    # Build a mapping of workspace ID -> vdesk
    workspace_to_vdesk = {}
    for vdesk in vdesks:
        for ws_id in vdesk.get("workspaces", []):
            workspace_to_vdesk[ws_id] = vdesk

    # Aggregate all renames into a dict
    renames: dict[int, str] = {}
    tmux_suffix = " - TMUX"
    browser_classes = {"firefox", "firefox_firefox", "chromium", "google-chrome", "brave-browser", "vivaldi", "zen", "zen-browser"}

    # Build a mapping of vdesk ID -> list of clients on that vdesk
    vdesk_clients: dict[int, list[dict]] = {}
    for client in clients:
        workspace = client.get("workspace", {})
        ws_id = workspace.get("id")
        if ws_id is None:
            continue
        vdesk = workspace_to_vdesk.get(ws_id)
        if vdesk is None:
            continue
        vdesk_id = vdesk.get("id")
        vdesk_clients.setdefault(vdesk_id, []).append(client)

    # Collect TMUX session names per vdesk (separate viewer sessions)
    tmux_names: dict[int, list[str]] = {}
    tmux_viewer_names: dict[int, list[str]] = {}
    for client in clients:
        title = client.get("title", "")
        if not title.endswith(tmux_suffix):
            continue

        # Get the workspace this client is on
        workspace = client.get("workspace", {})
        ws_id = workspace.get("id")
        if ws_id is None:
            continue

        # Find the vdesk for this workspace
        vdesk = workspace_to_vdesk.get(ws_id)
        if vdesk is None:
            continue

        vdesk_id = vdesk.get("id")
        name = clean_title(title[:-len(tmux_suffix)])

        # Get status icon for this tmux session
        status_icon = get_tmux_session_status(name)
        display_name = f"{status_icon} {name}" if status_icon else name

        if len(display_name) > MAX_NAME_LENGTH:
            display_name = display_name[:MAX_NAME_LENGTH] + "…"

        if name.endswith("-viewer"):
            tmux_viewer_names.setdefault(vdesk_id, []).append(display_name)
        else:
            tmux_names.setdefault(vdesk_id, []).append(display_name)

    # Build renames for vdesks with TMUX clients
    all_tmux_vdesks = set(tmux_names.keys()) | set(tmux_viewer_names.keys())
    for vdesk_id in all_tmux_vdesks:
        names = tmux_names.get(vdesk_id, [])
        viewer_names = tmux_viewer_names.get(vdesk_id, [])

        if names:
            # Non-viewer sessions exist: only show those
            renames[vdesk_id] = f"{vdesk_id} {TMUX_ICON} {'|'.join(names)}"
        elif viewer_names and len(vdesk_clients.get(vdesk_id, [])) == len(viewer_names):
            # Only viewer sessions and they're the only windows on the vdesk
            renames[vdesk_id] = f"{vdesk_id} {TMUX_ICON} {'|'.join(viewer_names)}"
        # Otherwise: viewer sessions exist but there are other non-TMUX windows,
        # so skip and let the fallback logic below handle naming

    # For vdesks without TMUX clients, try to use a window title (prefer browsers)
    for vdesk in vdesks:
        vdesk_id = vdesk.get("id")
        if vdesk_id in renames:
            continue

        desk_clients = vdesk_clients.get(vdesk_id, [])
        if not desk_clients:
            renames[vdesk_id] = f"{vdesk_id}"
            continue

        # Pick best client: prioritize browsers, then fall back to first client
        chosen = None
        for c in desk_clients:
            cls = c.get("class", "").lower()
            if cls in browser_classes:
                chosen = c
                break
        if chosen is None:
            chosen = desk_clients[0]

        title = clean_title(chosen.get("title", ""))
        if not title:
            renames[vdesk_id] = f"{vdesk_id}"
            continue

        is_browser = chosen.get("class", "").lower() in browser_classes
        if len(title) > MAX_NAME_LENGTH:
            title = title[:MAX_NAME_LENGTH] + "…"
        if is_browser:
            renames[vdesk_id] = f"{vdesk_id} {BROWSER_ICON} {title}"
        else:
            renames[vdesk_id] = f"{vdesk_id} {title}"

    # Write names (only if changed)
    # print(renames)
    write_names(renames)


if __name__ == "__main__":
    main()
